import os
import json
from typing import Dict, Any
from schemas import AgentDecision
from dotenv import load_dotenv

import google.generativeai as genai

load_dotenv()

# Setup Gemini API key
api_key = os.environ.get("LLM_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def deterministic_fallback(context: str, instruction: str) -> AgentDecision:
    """Fallback if API is missing or fails."""
    # Simple deterministic logic based on the *latest* event
    latest_event_type = ""
    try:
        events = json.loads(context)
        if events and isinstance(events, list):
            latest_event_type = events[-1].get("event_type", "")
    except:
        pass
    
    if latest_event_type == "shipment_delayed":
        return AgentDecision(
            decision="ACT",
            reason="Shipment is delayed.",
            actions=[{"name": "message_logistics_team", "reason": "Escalate shipment delay."}, {"name": "create_internal_note", "reason": "Noted shipment delay."}],
            memory_update="Shipment delayed; logistics team notified.",
            next_wake_seconds=30
        )
    elif latest_event_type == "payment_failed":
        return AgentDecision(
            decision="ACT",
            reason="Payment failed.",
            actions=[{"name": "message_payments_team", "reason": "Escalate payment failure."}, {"name": "create_internal_note", "reason": "Noted payment failure."}],
            memory_update="Payment failed; payments team notified.",
            next_wake_seconds=30
        )
    elif latest_event_type == "refund_requested":
        return AgentDecision(
            decision="ACT",
            reason="Customer requested a refund.",
            actions=[{"name": "message_customer", "reason": "Acknowledge refund request."}, {"name": "create_internal_note", "reason": "Refund requested."}],
            memory_update="Refund requested by customer; acknowledged.",
            next_wake_seconds=30
        )
    elif latest_event_type == "customer_message_received":
        return AgentDecision(
            decision="ACT",
            reason="Customer sent a message.",
            actions=[{"name": "message_customer", "reason": "Acknowledge customer message."}, {"name": "create_internal_note", "reason": "Customer message received."}],
            memory_update="Customer message received; acknowledged.",
            next_wake_seconds=30
        )
    elif latest_event_type == "payment_confirmed":
        return AgentDecision(
            decision="NO_ACTION",
            reason="Payment confirmed.",
            actions=[],
            memory_update="Payment confirmed.",
            next_wake_seconds=30
        )
    elif latest_event_type == "shipment_created":
        return AgentDecision(
            decision="NO_ACTION",
            reason="Shipment label created.",
            actions=[],
            memory_update="Shipment created.",
            next_wake_seconds=30
        )
    elif latest_event_type == "order_created":
        return AgentDecision(
            decision="NO_ACTION",
            reason="Order created.",
            actions=[],
            memory_update="Order created successfully.",
            next_wake_seconds=30
        )
    elif latest_event_type == "delivered":
        return AgentDecision(
            decision="NO_ACTION",
            reason="Order delivered.",
            actions=[],
            memory_update="Order delivered successfully.",
            next_wake_seconds=30
        )
    else:
        return AgentDecision(
            decision="SLEEP",
            reason="No critical action required at this time.",
            actions=[],
            memory_update="Checked status, no anomalies.",
            next_wake_seconds=30
        )

def run_agent_decision(order_context: Dict[str, Any], memory: Dict[str, Any], events: list, instruction: str) -> AgentDecision:
    prompt = f"""
    You are an Order Supervisor AI Agent.
    
    Order Context:
    {json.dumps(order_context, indent=2)}
    
    Memory:
    {json.dumps(memory, indent=2)}
    
    Recent Events:
    {json.dumps(events, indent=2)}
    
    Latest Instruction:
    {instruction}
    
    Based on the events and context, make a decision on what to do next.
    If the shipment is delayed, escalate to logistics.
    If payment failed, escalate to payments.
    If nothing is wrong, SLEEP.
    If a terminal state like delivered occurs, return NO_ACTION (the workflow will handle termination).
    
    Return your response strictly in the following JSON format:
    {{
      "decision": "ACT" | "SLEEP" | "NO_ACTION",
      "reason": "Why you made this decision",
      "actions": [
        {{
          "name": "message_logistics_team",
          "reason": "..."
        }}
      ],
      "memory_update": "Summary of the situation",
      "next_wake_seconds": 30
    }}
    
    Allowed actions: message_fulfillment_team, message_payments_team, message_logistics_team, message_customer, create_internal_note.
    """

    if not api_key:
        print("No API key found. Using deterministic fallback.")
        return deterministic_fallback(json.dumps(events), instruction)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        data = json.loads(response.text)
        return AgentDecision(**data)
    except Exception as e:
        print(f"LLM call failed: {e}. Using deterministic fallback.")
        return deterministic_fallback(json.dumps(events), instruction)
