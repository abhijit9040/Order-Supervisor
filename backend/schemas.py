from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SupervisorBase(BaseModel):
    name: str
    base_instruction: str
    available_actions: List[str]
    wake_config: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorResponse(SupervisorBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RunCreate(BaseModel):
    order_id: str
    order_context: Optional[Dict[str, Any]] = None

class RunResponse(BaseModel):
    id: int
    workflow_id: str
    order_id: str
    supervisor_id: int
    status: str
    order_context: Optional[Dict[str, Any]] = None
    memory_summary: Optional[Dict[str, Any]] = None
    next_wake_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    final_summary: Optional[str] = None
    final_learnings: Optional[str] = None
    final_feedback: Optional[str] = None
    class Config:
        from_attributes = True

class ActivityResponse(BaseModel):
    id: int
    run_id: int
    type: str
    data: Dict[str, Any]
    created_at: datetime
    class Config:
        from_attributes = True

class EventPayload(BaseModel):
    event_type: str
    message: str
    timestamp: Optional[str] = None

class InstructionPayload(BaseModel):
    instruction: str

# AI output schema
class ActionRequest(BaseModel):
    name: str
    reason: str

class AgentDecision(BaseModel):
    decision: str = Field(description="ACT, SLEEP, or NO_ACTION")
    reason: str = Field(description="Reason for the decision")
    actions: List[ActionRequest] = Field(default_factory=list, description="List of actions to take")
    memory_update: str = Field(description="Summary of what happened to store in memory")
    next_wake_seconds: int = Field(default=30, description="Seconds until next check")
