# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

### Web Servers & Deployments

**QuantumTech Dashboard:**
- Location: `/home/node/.openclaw/workspace/quantumtech-dashboard/`
- Server: Python HTTP Server
- Port: 8081
- URL: http://localhost:8081/index.html
- Process ID: 46 (check with `ps aux | grep "python3 -m http.server 8081"`)
- Log file: `/home/node/.openclaw/workspace/quantumtech-dashboard/server.log`
- Start command: `cd /home/node/.openclaw/workspace/quantumtech-dashboard && python3 -m http.server 8081`
- Stop command: `kill $(ps aux | grep "python3 -m http.server 8081" | grep -v grep | awk '{print $2}')`

**React Counter App:**
- Location: `/home/node/.openclaw/workspace/react-counter/`
- Server: Python HTTP Server
- Port: 8080
- URL: http://localhost:8080/demo.html
- Process ID: 552 (check with `ps aux | grep "python3 -m http.server 8080"`)
- Log file: `/home/node/.openclaw/workspace/react-counter/server.log`
- Start command: `cd /home/node/.openclaw/workspace/react-counter && python3 -m http.server 8080`
- Stop command: `kill $(ps aux | grep "python3 -m http.server 8080" | grep -v grep | awk '{print $2}')`

**Quick Check Server Status:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/index.html
# Should return: 200

curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/demo.html
# Should return: 200
```
