from temporalio import activity
from typing import Dict, Any, List
import json
from schemas import AgentDecision
from agent import run_agent_decision
from database import SessionLocal
from models import Activity, Run

@activity.defn
async def execute_agent(args: Dict[str, Any]) -> dict:
    order_context = args.get("order_context", {})
    memory = args.get("memory", {})
    events = args.get("events", [])
    instruction = args.get("instruction", "")
    
    decision: AgentDecision = run_agent_decision(order_context, memory, events, instruction)
    return decision.model_dump()

@activity.defn
async def execute_business_action(args: Dict[str, Any]) -> str:
    run_id_str = args.get("run_id")
    action_name = args.get("action_name")
    reason = args.get("reason")
    
    # Store action in DB
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.workflow_id == run_id_str).first()
        if run:
            new_activity = Activity(
                run_id=run.id,
                type="action",
                data={
                    "action": action_name,
                    "reason": reason
                }
            )
            db.add(new_activity)
            db.commit()
    finally:
        db.close()
        
    return f"Executed {action_name}: {reason}"

@activity.defn
async def record_workflow_state(args: Dict[str, Any]) -> str:
    run_id_str = args.get("run_id")
    state = args.get("state")
    data = args.get("data", {})
    
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.workflow_id == run_id_str).first()
        if run:
            run.status = state
            
            # Update memory if provided
            if "memory_summary" in data:
                run.memory_summary = data["memory_summary"]
            
            if "next_wake_at" in data:
                run.next_wake_at = data["next_wake_at"]
                
            db.commit()
    finally:
        db.close()
    return state

@activity.defn
async def record_final_summary(args: Dict[str, Any]) -> str:
    run_id_str = args.get("run_id")
    summary = args.get("summary", "")
    learnings = args.get("learnings", "")
    feedback = args.get("feedback", "")
    
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.workflow_id == run_id_str).first()
        if run:
            run.final_summary = summary
            run.final_learnings = learnings
            run.final_feedback = feedback
            db.commit()
    finally:
        db.close()
    return "Summary recorded"
