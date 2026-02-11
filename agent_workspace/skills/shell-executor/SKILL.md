# Shell Executor Skill (Workspace Restricted)

## Description
Execute shell commands safely within the agent's dedicated workspace.

## CRITICAL SECURITY RULES
⚠️ **ALL COMMANDS MUST RUN INSIDE /workspace ONLY**
- ✅ Allowed: `cd /workspace && npm install`
- ✅ Allowed: `ls /workspace/projects`
- ❌ FORBIDDEN: `rm -rf /` 
- ❌ FORBIDDEN: `cat /etc/passwd`
- ❌ FORBIDDEN: Any command outside /workspace

## Allowed Directories
```
/workspace/           # Root workspace
/workspace/projects/  # Project files
/workspace/builds/    # Build outputs
/workspace/memory/    # Agent memory/notes
/workspace/logs/      # Execution logs
/workspace/skills/    # Custom skills
```

## Usage Examples

### Safe Commands
```bash
# Navigate to workspace
cd /workspace/projects

# Create project files
echo "console.log('hello')" > /workspace/projects/app.js

# Run builds
cd /workspace/projects/myapp && npm run build

# Check logs
cat /workspace/logs/build.log
```

### FORBIDDEN Commands (Will Be Rejected)
```bash
# Accessing system files
cat /etc/passwd           # ❌ BLOCKED
rm -rf /                  # ❌ BLOCKED
ls /home                  # ❌ BLOCKED

# Accessing host directories
cat /configs/clawdbot-1.json5  # ❌ BLOCKED
```

## Implementation
When executing commands:
1. Always prefix with `cd /workspace &&`
2. Use absolute paths starting with `/workspace/`
3. Log all executions to `/workspace/logs/exec.log`
4. Never use `sudo` or elevated privileges

## Script Template
```python
import subprocess
import os

WORKSPACE = "/workspace"

def safe_exec(command: str) -> str:
    # Validate command doesn't escape workspace
    forbidden = ["/etc", "/home", "/root", "/var", "sudo", "su "]
    for f in forbidden:
        if f in command:
            return f"BLOCKED: Command contains forbidden path/keyword: {f}"
    
    # Execute in workspace context
    full_cmd = f"cd {WORKSPACE} && {command}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    # Log execution
    with open(f"{WORKSPACE}/logs/exec.log", "a") as log:
        log.write(f"CMD: {command}\nOUT: {result.stdout}\nERR: {result.stderr}\n---\n")
    
    return result.stdout or result.stderr
```
