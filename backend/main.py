from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid

import models, schemas
from database import engine, get_db

from temporalio.client import Client
from workflows import OrderSupervisorWorkflow

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order Supervisor API")

import os

async def get_temporal_client():
    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    return await Client.connect(temporal_host)

@app.get("/api/supervisors", response_model=List[schemas.SupervisorResponse])
def get_supervisors(db: Session = Depends(get_db)):
    return db.query(models.Supervisor).all()

@app.post("/api/supervisors", response_model=schemas.SupervisorResponse)
def create_supervisor(supervisor: schemas.SupervisorCreate, db: Session = Depends(get_db)):
    db_supervisor = models.Supervisor(**supervisor.model_dump())
    db.add(db_supervisor)
    db.commit()
    db.refresh(db_supervisor)
    return db_supervisor

@app.get("/api/supervisors/{id}", response_model=schemas.SupervisorResponse)
def get_supervisor(id: int, db: Session = Depends(get_db)):
    supervisor = db.query(models.Supervisor).filter(models.Supervisor.id == id).first()
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    return supervisor

@app.post("/api/runs", response_model=schemas.RunResponse)
async def create_run(run: schemas.RunCreate, db: Session = Depends(get_db)):
    # Pick first supervisor for now
    supervisor = db.query(models.Supervisor).first()
    if not supervisor:
        raise HTTPException(status_code=400, detail="No supervisor created yet")
        
    workflow_id = f"order-supervisor-{uuid.uuid4()}"
    
    db_run = models.Run(
        workflow_id=workflow_id,
        order_id=run.order_id,
        supervisor_id=supervisor.id,
        order_context=run.order_context,
        status="STARTING"
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    
    # Start Temporal workflow
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            OrderSupervisorWorkflow.run,
            {"order_id": run.order_id, "order_context": run.order_context},
            id=workflow_id,
            task_queue="order-supervisor-task-queue"
        )
    except Exception as e:
        # Rollback the DB run if workflow failed to start
        db.delete(db_run)
        db.commit()
        raise HTTPException(status_code=503, detail=f"Failed to connect to Temporal Server: {str(e)}")
    
    return db_run

@app.get("/api/runs", response_model=List[schemas.RunResponse])
def get_runs(db: Session = Depends(get_db)):
    runs = db.query(models.Run).all()
    return runs

@app.get("/api/runs/{run_id}", response_model=schemas.RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    # run_id could be the int ID or the workflow string ID
    if run_id.isdigit():
        run = db.query(models.Run).filter(models.Run.id == int(run_id)).first()
    else:
        run = db.query(models.Run).filter(models.Run.workflow_id == run_id).first()
        
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.post("/api/runs/{run_id}/events")
async def send_event(run_id: str, event: schemas.EventPayload, db: Session = Depends(get_db)):
    run = db.query(models.Run).filter(models.Run.workflow_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    # Store event in db
    new_activity = models.Activity(
        run_id=run.id,
        type="event",
        data=event.model_dump()
    )
    db.add(new_activity)
    db.commit()
    
    # Signal Temporal workflow
    client = await get_temporal_client()
    handle = client.get_workflow_handle(run_id)
    await handle.signal(OrderSupervisorWorkflow.order_event, event.model_dump())
    
    return {"status": "event sent"}

@app.post("/api/runs/{run_id}/instructions")
async def send_instruction(run_id: str, payload: schemas.InstructionPayload, db: Session = Depends(get_db)):
    run = db.query(models.Run).filter(models.Run.workflow_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    new_activity = models.Activity(
        run_id=run.id,
        type="instruction",
        data=payload.model_dump()
    )
    db.add(new_activity)
    db.commit()
    
    client = await get_temporal_client()
    handle = client.get_workflow_handle(run_id)
    await handle.signal(OrderSupervisorWorkflow.add_instruction, payload.instruction)
    return {"status": "instruction sent"}

@app.post("/api/runs/{run_id}/interrupt")
async def interrupt_run(run_id: str):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(run_id)
    await handle.signal(OrderSupervisorWorkflow.interrupt)
    return {"status": "interrupted"}

@app.post("/api/runs/{run_id}/resume")
async def resume_run(run_id: str):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(run_id)
    await handle.signal(OrderSupervisorWorkflow.resume)
    return {"status": "resumed"}

@app.post("/api/runs/{run_id}/terminate")
async def terminate_run(run_id: str):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(run_id)
    await handle.signal(OrderSupervisorWorkflow.terminate)
    return {"status": "terminated"}

@app.get("/api/runs/{run_id}/activities", response_model=List[schemas.ActivityResponse])
def get_activities(run_id: str, db: Session = Depends(get_db)):
    run = db.query(models.Run).filter(models.Run.workflow_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    activities = db.query(models.Activity).filter(models.Activity.run_id == run.id).order_by(models.Activity.created_at.desc()).all()
    return activities
