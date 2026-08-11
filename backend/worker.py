import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import OrderSupervisorWorkflow
from activities import execute_agent, execute_business_action, record_workflow_state, record_final_summary

import os

async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)
    
    worker = Worker(
        client,
        task_queue="order-supervisor-task-queue",
        workflows=[OrderSupervisorWorkflow],
        activities=[execute_agent, execute_business_action, record_workflow_state, record_final_summary]
    )
    print("Starting worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
