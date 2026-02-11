# Docker Mount Setup for Claude Driver

## Why This Is Needed

The Anthropic Claude CLI stores authentication tokens and session data in `~/.claude`. When running OpenClaw in a container, this directory must be accessible from inside the container.

## Quick Setup

### Method 1: Docker CLI

```bash
docker run -d \
  -v ~/.claude:/root/.claude \
  ...other OpenClaw options...
```

### Method 2: Docker Compose

Add this volume to your `docker-compose.yml`:

```yaml
services:
  openclaw:
    volumes:
      - ~/.claude:/root/.claude
```

### Method 3: WSL2 (Windows)

If you're running OpenClaw in WSL2:

1. In WSL, mount Windows home directory:
   ```bash
   # In /etc/wsl.conf (create if needed)
   [automount]
   enabled = true
   root = /mnt/
   options = "metadata"
   ```

2. Then in your Docker setup:
   ```bash
   docker run -v /mnt/c/Users/YOURUSERNAME/.claude:/root/.claude ...
   ```

## Verification

After mounting, verify inside the container:

```bash
# Check if directory is accessible
ls -la /root/.claude

# Should see auth_credentials.json if you've run claude login
```

## Troubleshooting

### "Directory not found" after mount

**Cause:** `~/.claude` doesn't exist on host yet.

**Fix:** Run `claude login` on host first to create the directory and auth credentials.

### Permission denied errors

**Cause:** Wrong ownership or permissions on mounted directory.

**Fix:**
```bash
# On host
chmod 700 ~/.claude
chmod 600 ~/.claude/*
```

### Auth not working in container

**Cause:** Container can't read auth credentials.

**Fix:** Ensure mount path is exactly `/root/.claude` (not `/root/.claude/...`)

### Using Docker Desktop (Mac/Windows)

1. Open Docker Desktop settings
2. Go to "Resources" → "File sharing"
3. Add `~/.claude` (or full path like `/Users/username/.claude`)
4. Restart Docker Desktop
5. Update container with mount as shown in Method 1/2 above

## Alternative: Container-Only Auth

If mounting isn't possible, you can authenticate inside the container:

```bash
# Inside the container
claude login
```

**⚠️ Warning:** You'll need to re-authenticate every time the container is recreated. Not recommended for production use.

## Recommended: First-Time Setup Script

```bash
#!/bin/bash
# run-once-setup.sh

# 1. Create Claude auth on host (if needed)
if [ ! -d ~/.claude ]; then
    echo "Please run 'claude login' on your host machine first"
    exit 1
fi

# 2. Verify auth credentials exist
if [ ! -f ~/.claude/auth_credentials.json ]; then
    echo "No auth credentials found. Run 'claude login' on host."
    exit 1
fi

# 3. Start OpenClaw with proper mount
docker run -d \
  --name openclaw \
  -v ~/.claude:/root/.claude \
  ...other options...
```
