# Order Supervisor POC

This project is a Proof of Concept (POC) for an **Order Supervisor AI Agent**. It uses Temporal to manage the long-running lifecycle of an order and an LLM to make intelligent decisions when important events (like a shipment delay) occur.

## Architecture

Please see [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed breakdown of the system design.

## Prerequisites

- Docker and Docker Compose (for Temporal and PostgreSQL)
- Python 3.10+
- Node.js 18+

## Quickstart

### 1. Start Infrastructure

Start Temporal, the Temporal UI, and PostgreSQL:

```bash
docker-compose up -d
```

*Note: The Temporal UI will be available at http://localhost:8080*

### 2. Setup Backend

In a new terminal:

```bash
cd backend
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate
# Activate venv (Mac/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

Start the FastAPI Server:

```bash
# In the backend directory with venv activated
export LLM_API_KEY="your_gemini_api_key_here" # Optional: Uses deterministic fallback if omitted
uvicorn main:app --reload --port 8000
```

Start the Temporal Worker:

```bash
# In a new terminal, in the backend directory with venv activated
export LLM_API_KEY="your_gemini_api_key_here" # Same key as above
python worker.py
```

### 3. Setup Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000.

## Demo Scenario

1. Open http://localhost:3000.
2. Click **+ Create Run**. A new order workflow will start and enter the `SLEEPING` state.
3. Click the Order ID to view the Run Details.
4. **Agent Sleep**: Inject `Order Created`. The workflow records it but the agent goes to sleep because no action is required.
5. **Agent Wake**: Inject `Shipment Delayed`. The Temporal workflow wakes up and invokes the agent.
6. **Agent Decision**: The agent decides to `ACT`. It executes `message_logistics_team` and `create_internal_note`. These appear in the timeline.
7. **Live Instruction**: Add an instruction like "If shipment is delayed, prioritize immediate escalation."
8. **Completion**: Inject `Delivered`. This is a terminal state. The workflow completes gracefully and generates a Final Summary.

## Features Implemented

- **Single Workflow per Order**: Uses Temporal to manage long-running state. No naive polling.
- **Signal-driven Wake/Sleep**: Wakes up immediately for high-priority events, sleeps otherwise using Temporal timers.
- **Agent Integration**: Uses Gemini 1.5 Flash (with a built-in deterministic fallback if no API key is provided).
- **Rolling Memory & History**: Activities and agent decisions are persisted in PostgreSQL.
- **Next.js Dashboard**: A fully functional simulator to inject events, manage runs, and observe the timeline in real-time.
