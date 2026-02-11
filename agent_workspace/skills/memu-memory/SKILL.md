# Skill: memU Proactive Memory

## Description
**"The Memory Engine"** - Gives the agent 24/7 proactive memory via [memU](https://github.com/NevaMind-AI/memU).
memU continuously captures and understands user intent, stores structured memories, and surfaces relevant context automatically.

## Requirements
1. **Python 3.13+** installed in the container or accessible via sandbox
2. **memU** installed: `pip install memu-py`
3. **OpenAI API key** (or compatible provider) for LLM + embeddings
4. **Project location**: `/workspace/projects/memU`

## Core Operations

### 1. Memorize (Store Knowledge)
Process conversations, documents, or any text into structured memory:
```bash
cd /workspace/projects/memU
python -c "
import asyncio
from memu.app import MemoryService

async def memorize():
    service = MemoryService(
        llm_profiles={
            'default': {
                'base_url': 'https://api.z.ai/api/coding/paas/v4',
                'api_key': '$ZAI_API_KEY',
                'chat_model': 'glm-4.5',
                'client_backend': 'httpx'
            }
        },
        database_config={'metadata_store': {'provider': 'sqlite', 'dsn': 'sqlite:///workspace/memory/memu.db'}}
    )
    result = await service.memorize(
        resource_url='path/to/conversation.json',
        modality='conversation'
    )
    print(result)

asyncio.run(memorize())
"
```

### 2. Retrieve (Query Memory)
Search memory for relevant context:
```bash
cd /workspace/projects/memU
python -c "
import asyncio
from memu.app import MemoryService

async def retrieve():
    service = MemoryService(...)
    result = await service.retrieve(
        queries=[{'role': 'user', 'content': {'text': 'What does the user prefer?'}}],
        method='rag'
    )
    print(result)

asyncio.run(retrieve())
"
```

### 3. Proactive Context Loading
Run memU in the background to monitor and memorize interactions:
```bash
bash background:true command:"cd /workspace/projects/memU && python examples/proactive/proactive.py"
```

## Memory Types
| Type | Description |
|------|-------------|
| `profile` | User preferences, traits, personal info |
| `event` | Things that happened, timeline facts |
| `knowledge` | Domain expertise, learned facts |
| `behavior` | Patterns, habits, routines |
| `skill` | Capabilities, tools, techniques |
| `tool` | Tool usage patterns and preferences |

## Retrieval Methods
| Method | Speed | Cost | Best For |
|--------|-------|------|----------|
| `rag` | Milliseconds | Low (embeddings only) | Real-time context surfacing |
| `llm` | Seconds | Higher (LLM inference) | Deep reasoning, intent prediction |

## Storage Backends
- **In-memory**: Fast, no persistence (testing only)
- **SQLite**: File-based, good for single-agent (`sqlite:///workspace/memory/memu.db`)
- **PostgreSQL + pgvector**: Scalable, multi-agent shared memory

## Usage Rules
- **When to use**: When the agent needs to remember context across sessions, surface relevant info proactively, or build long-term user understanding
- **Background mode**: Run memorization async so it doesn't block the main conversation
- **Cost**: Uses LLM tokens for memorization and LLM-based retrieval; RAG retrieval is cheap (embedding only)
- **Scope**: Use `where` filters (`user_id`, `agent_id`) to isolate memories per user/agent

## Security
- Memory data stored locally in `/workspace/memory/`
- No data leaves the system unless using external LLM APIs
- Supports access control via `where` filters
