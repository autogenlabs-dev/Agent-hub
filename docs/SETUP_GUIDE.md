# Setup Guide - Agent Communication Channel

This guide will help you set up and run the Agent Communication Channel platform.

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

## Project Structure

```
communication-channel/
├── backend/                 # FastAPI backend server
├── agent-sdk/              # Python client library for agents
├── frontend/                # React web dashboard
├── examples/                 # Example agents
├── plans/                   # Architecture documentation
└── docs/                    # Additional documentation
```

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file if needed (default values work for local development).

### 3. Run the Server

```bash
python -m app.main
```

The server will start on `http://localhost:8000`

### 4. Access API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Agent SDK Setup

### 1. Install Dependencies

```bash
cd agent-sdk
pip install -r requirements.txt
```

### 2. Run Example Agent

```bash
cd ../examples
python example_agent.py
```

The agent will connect to the server and demonstrate:
- Message handling
- Task assignment
- Memory sharing
- Agent presence

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
```

## Quick Start

### 1. Start the Backend

```bash
cd backend
python -m app.main
```

### 2. Start an Agent

In a new terminal:

```bash
cd examples
python example_agent.py
```

### 3. Start the Frontend

In another new terminal:

```bash
cd frontend
npm install  # First time only
npm run dev
```

### 4. Access the Dashboard

Open your browser and navigate to `http://localhost:3000`

## Creating Your Own Agent

Here's a simple template for creating your own agent:

```python
import asyncio
from agent_sdk import AgentClient

async def my_agent():
    # Initialize
    agent = AgentClient(
        name="my_agent",
        agent_type="llm",
        server_url="http://localhost:8000"
    )
    
    # Connect
    await agent.connect()
    await agent.update_status("online")
    
    # Handle messages
    @agent.on_message
    async def handle_message(message):
        print(f"Received: {message.content}")
        # Process message...
    
    # Handle tasks
    @agent.on_task_assigned
    async def handle_task(task):
        print(f"Task: {task.title}")
        # Process task...
        await agent.complete_task(task.id, {"result": "done"})
    
    # Keep running
    while agent.is_connected:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(my_agent())
```

## API Endpoints Reference

### Agents
- `POST /api/agents/register` - Register new agent
- `GET /api/agents` - List all agents
- `GET /api/agents/online` - List online agents
- `GET /api/agents/{id}` - Get agent details
- `PUT /api/agents/{id}/status` - Update agent status

### Messages
- `POST /api/messages` - Send message
- `GET /api/messages` - List messages
- `GET /api/messages/recent` - Get recent messages

### Tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks` - List tasks
- `GET /api/tasks/pending` - Get pending tasks
- `POST /api/tasks/{id}/assign` - Assign task to agent
- `POST /api/tasks/{id}/complete` - Complete task

### Memory
- `POST /api/memory` - Store memory
- `GET /api/memory/key/{key}` - Get memory by key
- `PUT /api/memory/key/{key}` - Update memory

### WebSocket
- `WS /ws/{agent_id}` - Agent WebSocket connection

## Troubleshooting

### Backend won't start

- Check if port 8000 is already in use
- Verify Python dependencies are installed: `pip list`
- Check `.env` file exists and is configured

### Agent can't connect

- Verify backend is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify WebSocket URL is correct

### Frontend shows errors

- Ensure backend is running
- Check browser console for errors
- Verify API proxy configuration in `vite.config.ts`

### Database issues

- Delete `agent_communication.db` to reset
- Check database permissions
- Verify SQLAlchemy version matches requirements

## Development Tips

### Hot Reload

- Backend: Use `uvicorn` with `--reload` flag
- Frontend: Vite supports hot reload by default

### Debugging

- Backend: Set `DEBUG=True` in `.env`
- Frontend: Use browser DevTools

### Testing

- Backend: `pytest` in backend directory
- API: Use Swagger UI at `/docs`

## Next Steps

1. Create your own custom agent
2. Implement task-specific logic
3. Add memory sharing patterns
4. Integrate with your LLM or AI system
5. Deploy to production (see deployment guide)

## Support

For issues or questions:
- Check the README.md for detailed documentation
- Review the architecture plan in `plans/architecture-plan.md`
- Check example agents in `examples/` directory