# Architecture Note

## High-Level Flow

```
[ Next.js UI ] 
      │ 
      ▼ (REST API)
[ FastAPI Backend ] 
      │ 
      ▼ (Starts Workflow / Sends Signals)
[ Temporal Server ] 
      │ 
      ▼ (Executes Workflow / Activities)
[ Temporal Worker (Python) ] 
      │ 
      ├──► Agent Runtime (LLM) 
      └──► PostgreSQL DB (State & Timeline)
```

## Core Principles

1. **Workflow-Owned Lifecycle**: There is exactly one `OrderSupervisorWorkflow` per order. The workflow loops continuously until a terminal condition is met. It does not poll. It uses `workflow.wait_condition` to sleep and wait for external Temporal signals or timeouts.
2. **Event-Driven Wakeup**: Events (e.g., `payment_failed`) are sent to the `/events` endpoint, which translates them into Temporal Signals. 
3. **Deterministic Pre-Filtering**: The workflow itself implements a lightweight deterministic filter. If an event is "low-priority" (like `payment_confirmed`), the workflow simply records it and remains asleep. If it is "high-priority" (like `shipment_delayed`), it flips the `wake_signal`, unblocking the `wait_condition` and invoking the LLM agent.
4. **Event Deduplication**: The workflow tracks a `processed_events_count` state variable to ensure that the LLM agent is strictly presented with *unprocessed* events on each wake cycle, preventing duplicate execution of business actions.
5. **Structured Agent Output**: The LLM is provided with recent events, the current order context, and rolling memory. It outputs a strictly validated JSON structure determining whether to `ACT`, `SLEEP`, or take `NO_ACTION`, along with specific business actions to execute.
6. **Mock Actions**: The business actions are implemented as Temporal Activities. They record a database entry in the `activities` table which is immediately visible in the Next.js UI timeline.
7. **Graceful Completion**: The workflow recognizes terminal events like `delivered`. The LLM does not kill the workflow; the workflow kills itself and generates a final summary activity before completing.
