# File Manager Skill (Workspace Restricted)

## Description
Create, read, edit, delete, and organize files within the agent workspace only.

## SECURITY: Workspace Only
⚠️ **ALL FILE OPERATIONS RESTRICTED TO /workspace**

### Allowed Paths
```
✅ /workspace/projects/
✅ /workspace/memory/
✅ /workspace/builds/
✅ /workspace/logs/
✅ /workspace/skills/
✅ /workspace/credentials/  # Read-only for env files
```

### Forbidden Paths
```
❌ /configs/             # Host configuration
❌ /etc/                 # System files
❌ /home/                # Home directories
❌ /root/                # Root directory
❌ ../                   # Path traversal
```

## Capabilities
- Create files and directories
- Read file contents
- Edit/update files
- Delete files (with confirmation)
- Search files by name or content
- List directory contents

## Usage Examples

### Create File
```python
def create_file(path: str, content: str) -> str:
    if not path.startswith("/workspace"):
        return "ERROR: Path must be within /workspace"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w") as f:
        f.write(content)
    
    return f"Created: {path}"
```

### Read File
```python
def read_file(path: str) -> str:
    if not path.startswith("/workspace"):
        return "ERROR: Can only read files in /workspace"
    
    with open(path, "r") as f:
        return f.read()
```

### Search Files
```bash
# Find all Python files in workspace
find /workspace -name "*.py" -type f

# Search for content
grep -r "TODO" /workspace/projects/
```

### List Directory
```python
def list_dir(path: str = "/workspace") -> list:
    if not path.startswith("/workspace"):
        return ["ERROR: Can only list /workspace directories"]
    
    return os.listdir(path)
```

### Delete with Confirmation
```python
def delete_file(path: str, confirm: bool = False) -> str:
    if not path.startswith("/workspace"):
        return "ERROR: Can only delete in /workspace"
    
    if not confirm:
        return f"CONFIRM: Delete {path}? Call with confirm=True"
    
    os.remove(path)
    return f"Deleted: {path}"
```

## Path Validation
Always validate paths before any operation:
```python
def validate_path(path: str) -> bool:
    # Resolve absolute path
    abs_path = os.path.abspath(path)
    
    # Check it starts with workspace
    if not abs_path.startswith("/workspace"):
        return False
    
    # Check for path traversal attempts
    if ".." in path:
        return False
    
    return True
```
