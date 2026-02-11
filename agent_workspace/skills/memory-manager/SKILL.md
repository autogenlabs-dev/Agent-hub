# Memory Manager Skill

## Description
Manage agent's persistent memory, notes, and context within the dedicated workspace.

## Storage Location
All memory files go to `/workspace/memory/`:
```
/workspace/memory/
├── context.json       # Current context and state
├── notes.md           # General notes and observations
├── tasks.json         # Task history and learnings
├── preferences.json   # User preferences learned over time
└── sessions/          # Per-session transcripts
```

## Capabilities
- Store and retrieve key-value pairs
- Maintain conversation context across sessions
- Log learnings from completed tasks
- Track user preferences

## Usage Examples

### Store a Note
```python
def store_note(content: str, category: str = "general"):
    with open("/workspace/memory/notes.md", "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"\n## [{category}] {timestamp}\n{content}\n")
```

### Store Context
```python
import json

def store_context(key: str, value: any):
    context_file = "/workspace/memory/context.json"
    try:
        with open(context_file, "r") as f:
            context = json.load(f)
    except FileNotFoundError:
        context = {}
    
    context[key] = {
        "value": value,
        "updated_at": datetime.now().isoformat()
    }
    
    with open(context_file, "w") as f:
        json.dump(context, f, indent=2)
```

### Retrieve Context
```python
def get_context(key: str) -> any:
    try:
        with open("/workspace/memory/context.json", "r") as f:
            context = json.load(f)
        return context.get(key, {}).get("value")
    except FileNotFoundError:
        return None
```

### Log Task Learning
```python
def log_task_learning(task_id: str, learning: str):
    tasks_file = "/workspace/memory/tasks.json"
    try:
        with open(tasks_file, "r") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        tasks = {"completed": [], "learnings": []}
    
    tasks["learnings"].append({
        "task_id": task_id,
        "learning": learning,
        "timestamp": datetime.now().isoformat()
    })
    
    with open(tasks_file, "w") as f:
        json.dump(tasks, f, indent=2)
```

## Memory Types
| Type | File | Purpose |
|------|------|---------|
| Context | `context.json` | Current working state |
| Notes | `notes.md` | Free-form observations |
| Tasks | `tasks.json` | Task outcomes and learnings |
| Preferences | `preferences.json` | User preferences |
| Sessions | `sessions/*.json` | Session transcripts |

## Best Practices
- Regularly clean old context that's no longer relevant
- Summarize long notes periodically
- Index learnings for quick retrieval
