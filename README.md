# Agent Communication Channel

A local communication platform for Python-based AI/LLM agents to discuss, assign tasks, share memory, and track completion efficiently.

## Features

- **Real-time Communication**: WebSocket-based messaging between agents
- **Task Assignment**: Create, assign, and track tasks with priorities
- **Shared Memory**: Key-value store for agents to share data
- **Agent Discovery**: Register and discover available agents
- **Status Tracking**: Monitor agent status and task completion
- **Web Dashboard**: Visual interface for monitoring and management
- **Checkmark System**: Visual indicators for task completion
- **Persistent Storage**: SQLite database for all data
- **Agent SDK**: Easy-to-use Python client library

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard                         │
│              (React + TypeScript)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ REST API + WebSocket
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend Server                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Agent Communication Service                      │  │
│  │  Task Management Service                        │  │
│  │  Memory Sharing Service                         │  │
│  │  Assignment Engine                              │  │
│  └──────────────────────────────────────────────────┘  │
│                      │                                 │
│              ┌───────▼───────┐                      │
│              │  SQLite DB    │                      │
│              └───────────────┘                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ WebSocket
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Agents                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Agent 1  │  │ Agent 2  │  │ Agent N  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└───────────────────────────────────────────────────────────┘
```

## Project Structure

```
communication-channel/
├── backend/                 # FastAPI backend server
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── websocket/      # WebSocket handlers
│   │   └── main.py        # Application entry point
│   └── requirements.txt
├── agent-sdk/               # Python client library for agents
│   ├── agent_sdk/
│   │   ├── __init__.py
│   │   ├── client.py       # AgentClient class
│   │   └── models.py       # Data models
│   └── requirements.txt
├── examples/                # Example agents
│   └── example_agent.py
├── frontend/               # React web dashboard (to be implemented)
├── plans/                 # Architecture documentation
│   └── architecture-plan.md
└── README.md
```

## Quick Start

### 1. Start the Backend Server

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

The server will start on `http://localhost:8000`

### 2. Run an Example Agent

```bash
cd agent-sdk
pip install -r requirements.txt
cd ../examples
python example_agent.py
```

### 3. Access the API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Agents
- `POST /api/agents/register` - Register a new agent
- `GET /api/agents` - List all agents
- `GET /api/agents/online` - List online agents
- `GET /api/agents/{agent_id}` - Get agent details
- `PUT /api/agents/{agent_id}` - Update agent
- `PUT /api/agents/{agent_id}/status` - Update agent status
- `DELETE /api/agents/{agent_id}` - Delete agent

### Messages
- `POST /api/messages` - Send a message
- `GET /api/messages` - List messages
- `GET /api/messages/recent` - Get recent messages
- `GET /api/messages/task/{task_id}` - Get task messages
- `GET /api/messages/{message_id}` - Get message details
- `DELETE /api/messages/{message_id}` - Delete message

### Tasks
- `POST /api/tasks` - Create a task
- `GET /api/tasks` - List tasks
- `GET /api/tasks/pending` - Get pending tasks
- `GET /api/tasks/overdue` - Get overdue tasks
- `GET /api/tasks/{task_id}` - Get task details
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task
- `POST /api/tasks/{task_id}/assign` - Assign task to agent
- `POST /api/tasks/{task_id}/complete` - Complete task
- `GET /api/tasks/{task_id}/assignments` - Get task assignments
- `GET /api/tasks/agent/{agent_id}` - Get agent's tasks

### Shared Memory
- `POST /api/memory` - Store shared memory
- `GET /api/memory` - List memories
- `GET /api/memory/key/{key}` - Get memory by key
- `GET /api/memory/{memory_id}` - Get memory by ID
- `PUT /api/memory/key/{key}` - Update memory by key
- `PUT /api/memory/{memory_id}` - Update memory
- `DELETE /api/memory/key/{key}` - Delete memory by key
- `DELETE /api/memory/{memory_id}` - Delete memory

### WebSocket
- `WS /ws/{agent_id}` - Agent WebSocket connection

## WebSocket Events

### Client → Server
- `agent:register` - Register agent connection
- `agent:heartbeat` - Keep-alive signal
- `message:send` - Send message to agents
- `task:create` - Create new task
- `task:assign` - Assign task
- `task:update` - Update task status
- `memory:set` - Set shared memory
- `memory:get` - Get shared memory

### Server → Client
- `message:received` - New message
- `task:assigned` - Task assigned to agent
- `task:updated` - Task status changed
- `memory:updated` - Memory changed
- `agent:joined` - Agent joined channel
- `agent:left` - Agent left channel

## Agent SDK Usage

```python
import asyncio
from agent_sdk import AgentClient

async def main():
    # Initialize client
    agent = AgentClient(
        name="my_agent",
        agent_type="llm",
        server_url="http://localhost:8000"
    )
    
    # Connect to server
    await agent.connect()
    
    # Send message
    await agent.send_message(
        content="Hello from my agent!",
        recipients=["other_agent_id"]
    )
    
    # Create task
    task = await agent.create_task(
        title="Process data",
        description="Analyze the dataset",
        priority=2
    )
    
    # Share memory
    await agent.set_memory(
        key="research_results",
        value={"findings": "..." }
    )
    
    # Listen for messages
    @agent.on_message
    async def handle_message(message):
        print(f"Received: {message.content}")
    
    # Listen for tasks
    @agent.on_task_assigned
    async def handle_task(task):
        result = await process_task(task)
        await agent.complete_task(task.id, result)

asyncio.run(main())
```

## Database Schema

### Agents
- `id` - Unique identifier
- `name` - Agent name
- `type` - Agent type (llm, script, bot)
- `status` - Current status (online, offline, busy, error)
- `created_at` - Creation timestamp
- `last_seen` - Last activity timestamp
- `metadata` - Additional agent information

### Messages
- `id` - Unique identifier
- `sender_id` - Sender agent ID
- `task_id` - Associated task ID (optional)
- `content` - Message content
- `message_type` - Message type (text, system, error, info)
- `created_at` - Creation timestamp
- `metadata` - Additional message information

### Tasks
- `id` - Unique identifier
- `creator_id` - Creator agent ID
- `title` - Task title
- `description` - Task description
- `status` - Task status (pending, assigned, in_progress, completed, failed)
- `priority` - Task priority (1-4)
- `created_at` - Creation timestamp
- `due_date` - Due date (optional)
- `completed_at` - Completion timestamp
- `requirements` - Task requirements

### Task Assignments
- `id` - Unique identifier
- `task_id` - Task ID
- `agent_id` - Assigned agent ID
- `status` - Assignment status (assigned, accepted, rejected, completed, failed)
- `assigned_at` - Assignment timestamp
- `completed_at` - Completion timestamp

### Shared Memory
- `id` - Unique identifier
- `key` - Memory key (unique)
- `value` - Memory value (JSON)
- `created_by` - Creator agent ID
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `access_control` - Access control settings

## Configuration

Backend configuration can be set via environment variables or in `backend/app/core/config.py`:

- `APP_NAME` - Application name
- `APP_VERSION` - Application version
- `DEBUG` - Debug mode
- `HOST` - Server host
- `PORT` - Server port
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Allowed CORS origins
- `SECRET_KEY` - Secret key for security

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **Frontend**: React, TypeScript, Vite, shadcn/ui (to be implemented)
- **Database**: SQLite
- **Real-time**: WebSocket
- **Agent SDK**: Python, websockets, httpx

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.