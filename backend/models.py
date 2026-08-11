from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Supervisor(Base):
    __tablename__ = "supervisors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    base_instruction = Column(Text, nullable=False)
    available_actions = Column(JSON, nullable=False) # list of action names
    wake_config = Column(JSON, nullable=True)
    llm_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    runs = relationship("Run", back_populates="supervisor")

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, unique=True, nullable=False)
    order_id = Column(String, index=True, nullable=False)
    supervisor_id = Column(Integer, ForeignKey("supervisors.id"))
    
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, TERMINATED
    order_context = Column(JSON, nullable=True)
    memory_summary = Column(JSON, nullable=True)
    next_wake_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    final_summary = Column(Text, nullable=True)
    final_learnings = Column(Text, nullable=True)
    final_feedback = Column(Text, nullable=True)

    supervisor = relationship("Supervisor", back_populates="runs")
    activities = relationship("Activity", back_populates="run")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    type = Column(String, nullable=False) # e.g. "event", "action", "wake", "sleep", "instruction"
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    run = relationship("Run", back_populates="activities")
