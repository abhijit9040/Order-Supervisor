from datetime import timedelta
import asyncio
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import execute_agent, execute_business_action, record_workflow_state, record_final_summary

@workflow.defn
class OrderSupervisorWorkflow:
    def __init__(self) -> None:
        self.state = "AWAKE"
        self.events = []
        self.instructions = []
        self.memory = {}
        self.is_completed = False
        self.is_terminated = False
        self.is_paused = False
        self.wake_signal = False
        self.order_id = ""
        self.workflow_id = ""

    @workflow.signal
    def order_event(self, event: dict) -> None:
        self.events.append(event)
        
        # Check priority to wake up immediately
        high_priority = ["payment_failed", "shipment_delayed", "refund_requested", "customer_message_received"]
        terminal = ["delivered"]
        
        if event.get("event_type") in high_priority:
            self.wake_signal = True
            
        if event.get("event_type") in terminal:
            self.is_completed = True
            self.wake_signal = True

    @workflow.signal
    def add_instruction(self, instruction: str) -> None:
        self.instructions.append(instruction)
        self.wake_signal = True

    @workflow.signal
    def interrupt(self) -> None:
        self.is_paused = True
        self.state = "PAUSED"
        self.wake_signal = True

    @workflow.signal
    def resume(self) -> None:
        self.is_paused = False
        self.state = "AWAKE"
        self.wake_signal = True

    @workflow.signal
    def terminate(self) -> None:
        self.is_terminated = True
        self.wake_signal = True

    @workflow.run
    async def run(self, args: dict) -> str:
        self.order_context = args.get("order_context", {})
        self.order_id = args.get("order_id", "unknown")
        self.workflow_id = workflow.info().workflow_id
        
        self.state = "AWAKE"
        
        while not self.is_completed and not self.is_terminated:
            if self.is_paused:
                await workflow.execute_activity(
                    record_workflow_state,
                    {"run_id": self.workflow_id, "state": "PAUSED"},
                    start_to_close_timeout=timedelta(seconds=10)
                )
                await workflow.wait_condition(lambda: not self.is_paused or self.is_terminated)
                if self.is_terminated:
                    break
            
            # Record Awake state
            self.state = "AWAKE"
            await workflow.execute_activity(
                record_workflow_state,
                {"run_id": self.workflow_id, "state": "AWAKE"},
                start_to_close_timeout=timedelta(seconds=10)
            )

            # Check if terminal based on events before agent
            if self.is_completed:
                break
                
            # Run Agent
            latest_instruction = self.instructions[-1] if self.instructions else ""
            agent_decision_dict = await workflow.execute_activity(
                execute_agent,
                {
                    "order_context": self.order_context,
                    "memory": self.memory,
                    "events": self.events[-5:], # only pass recent events
                    "instruction": latest_instruction
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            decision = agent_decision_dict.get("decision", "SLEEP")
            actions = agent_decision_dict.get("actions", [])
            memory_update = agent_decision_dict.get("memory_update", "")
            next_wake_seconds = agent_decision_dict.get("next_wake_seconds", 30)
            
            # Update memory
            if memory_update:
                self.memory["latest_update"] = memory_update
            
            if decision == "ACT":
                for action in actions:
                    await workflow.execute_activity(
                        execute_business_action,
                        {
                            "run_id": self.workflow_id,
                            "action_name": action.get("name"),
                            "reason": action.get("reason")
                        },
                        start_to_close_timeout=timedelta(seconds=10)
                    )
            
            # Sleep phase
            self.state = "SLEEPING"
            self.wake_signal = False
            
            # Record state
            await workflow.execute_activity(
                record_workflow_state,
                {
                    "run_id": self.workflow_id, 
                    "state": "SLEEPING",
                    "data": {
                        "memory_summary": self.memory
                    }
                },
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            # Sleep until timeout OR wake_signal
            try:
                await workflow.wait_condition(
                    lambda: self.wake_signal, 
                    timeout=timedelta(seconds=next_wake_seconds)
                )
            except asyncio.TimeoutError:
                pass
            
        if self.is_terminated:
            self.state = "TERMINATED"
            await workflow.execute_activity(
                record_workflow_state,
                {"run_id": self.workflow_id, "state": "TERMINATED"},
                start_to_close_timeout=timedelta(seconds=10)
            )
            return "Terminated manually"
            
        if self.is_completed:
            self.state = "COMPLETED"
            await workflow.execute_activity(
                record_workflow_state,
                {"run_id": self.workflow_id, "state": "COMPLETED"},
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            # Generate final summary
            summary_text = f"Order {self.order_id} reached terminal state. Final memory: {self.memory.get('latest_update', '')}"
            learnings_text = "Shipment delay required immediate intervention. Verified by supervisor."
            feedback_text = "Monitor delayed shipments more aggressively."
            
            await workflow.execute_activity(
                record_final_summary,
                {
                    "run_id": self.workflow_id, 
                    "summary": summary_text,
                    "learnings": learnings_text,
                    "feedback": feedback_text
                },
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            return summary_text

        return "Finished"
