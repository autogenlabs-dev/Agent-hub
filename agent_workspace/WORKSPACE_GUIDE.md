# Agent Workspace Guide

## Overview
This is your dedicated, isolated workspace. You can do ANYTHING here without affecting the main repository.

## Directory Structure
```
/workspace/
├── projects/        # Clone and build projects here
├── memory/          # Your persistent memory and notes
├── builds/          # Build outputs and artifacts
├── logs/            # Execution logs
├── skills/          # Your skill definitions
└── credentials/     # Dedicated agent credentials
    └── .env.agent   # API keys and tokens
```

## Security Rules
|✅ ALLOWED | ❌ FORBIDDEN |
|----------|-------------|
| `/workspace/*` | `/configs/*` |
| Read `.env.agent` | Host system files |
| Create any files | Path traversal (`../`) |
| Run any builds | Access outside workspace |

## Quick Start Commands

### Navigate
```bash
cd /workspace/projects
ls /workspace/
```

### Create Files
```bash
echo "Hello World" > /workspace/test.txt
```

### Clone Projects
```bash
cd /workspace/projects
git clone https://github.com/owner/repo.git
```

### Build Projects
```bash
cd /workspace/projects/myapp
npm install && npm run build
```

### Store Memory
```bash
echo "Learned: X works better than Y" >> /workspace/memory/notes.md
```

### Check Logs
```bash
cat /workspace/logs/exec.log
```

## Loading Credentials
```bash
source /workspace/credentials/.env.agent
# Now $AGENT_GITHUB_TOKEN etc. are available
```

## Available Skills
See `/workspace/skills/` for all available skill documentation.
