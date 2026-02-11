# Bot-to-Bot Communication System — Full Implementation Plan

## The Problem

Telegram bots **cannot see messages from other bots** (platform limitation). Our 4 agents (CTO, Developer, DevOps, Alex) can't talk to each other through Telegram. We need a **bridge** that routes messages through the backend instead.

## Current Architecture

```
[User] <--Telegram--> [CTO Bot (OpenClaw)]        ← clawdbot-1, port 18790
[User] <--Telegram--> [Developer Bot (OpenClaw)]   ← clawdbot-2, port 18790
[User] <--Telegram--> [DevOps Bot (OpenClaw)]      ← clawdbot-3, port 18790
[User] <--Telegram--> [Alex (memU Bot)]            ← memu-bot, Python
                            |
                            v
                    [Backend API + WebSocket]
```

**Problem:** Only Alex connects to the backend. OpenClaw bots are isolated — they only talk to Telegram.

## Target Architecture

```
[User] <--Telegram--> [CTO Bot]      <--WS (0.0.0.0:18790)--> [Bridge Service]
[User] <--Telegram--> [Developer Bot] <--WS (0.0.0.0:18791)--> [Bridge Service]
[User] <--Telegram--> [DevOps Bot]    <--WS (0.0.0.0:18792)--> [Bridge Service]
[User] <--Telegram--> [Alex]          <--WS--> [Backend]
                                                    ^
                                                    |
                                            [Bridge Service]
                                        (connects both sides)
```

The **Bridge Service** is the key new component. It connects to:
1. The **backend WebSocket** (to receive messages from Alex and other agents)
2. Each **OpenClaw bot's internal WebSocket** (to forward messages and get responses)

---

## Phase 1: Enable OpenClaw Gateway Access (Config Changes)

### 1.1 Expose OpenClaw Gateway Ports

Each OpenClaw bot runs an internal WebSocket gateway on port 18790. Currently it binds to `127.0.0.1` (localhost only). We need to:

**Change bind to LAN mode** in each OpenClaw config:

`config/clawdbot-1.json5` — Add:
```json5
{
  gateway: {
    bind: "lan",  // Changes from 127.0.0.1 to 0.0.0.0
    auth: {
      token: "${OPENCLAW_GATEWAY_TOKEN}"
    }
  },
  // ... existing config
}
```

`config/clawdbot-2.json5` — Same change
`config/clawdbot-3.json5` — Same change

### 1.2 Expose Ports in Docker Compose

```yaml
clawdbot-1:
  # ... existing config
  ports:
    - "18790:18790"  # Gateway WebSocket (optional, for debugging)

clawdbot-2:
  # ... existing config
  ports:
    - "18791:18790"  # Map to different host port

clawdbot-3:
  # ... existing config
  ports:
    - "18792:18790"
```

**Note:** Within Docker's internal network, the bridge can access each bot as `clawdbot-1:18790`, `clawdbot-2:18790`, `clawdbot-3:18790` — no port mapping needed if the bridge is in the same Docker network.

---

## Phase 2: Bridge Service (New Container)

### 2.1 Architecture

```
agent-bridge/
  ├── Dockerfile
  ├── requirements.txt
  ├── bridge.py          # Main bridge service
  ├── openclaw_client.py # OpenClaw WebSocket client
  └── config.py          # Configuration
```

### 2.2 Bridge Service Flow

```
1. Bridge starts → connects to Backend WebSocket as "bridge-agent"
2. Bridge connects to each OpenClaw bot's WebSocket gateway
3. Bridge registers as message router in the backend

INCOMING (Agent → OpenClaw Bot):
  Alex sends /ask CTO "How are you?"
  → Alex posts to Backend: message:send {recipients: ["cto-agent-id"], content: "How are you?"}
  → Backend routes to Bridge (bridge subscribed to all agent messages)
  → Bridge receives message:received event
  → Bridge identifies target = CTO = clawdbot-1:18790
  → Bridge sends chat.send to CTO's gateway WebSocket
  → CTO processes message via LLM
  → CTO responds via gateway WebSocket events (chat.tick, chat.done)
  → Bridge collects response
  → Bridge sends response back to Backend: message:send {recipients: ["alex-agent-id"]}
  → Alex receives response via Backend WebSocket
  → Alex forwards to user on Telegram

OUTGOING (OpenClaw Bot → Other Agents):
  CTO wants to delegate task to Developer
  → CTO can use a new tool "send_agent_message" (added to OpenClaw config)
  → Tool calls Bridge's HTTP endpoint
  → Bridge routes to the target agent via Backend
```

### 2.3 OpenClaw Gateway Protocol

The OpenClaw gateway uses a JSON WebSocket protocol:

**Connection:**
```json
// Client sends after WebSocket connects:
{
  "type": "req",
  "id": "connect-1",
  "method": "connect",
  "params": {
    "token": "clawd_gateway_secret_123",
    "clientName": "bridge",
    "clientDisplayName": "Agent Bridge",
    "clientVersion": "1.0",
    "mode": "cli",
    "protocol": 3
  }
}

// Server responds:
{
  "type": "res",
  "id": "connect-1",
  "result": { "ok": true, "sessions": [...] }
}
```

**Sending a message:**
```json
{
  "type": "req",
  "id": "msg-123",
  "method": "chat.send",
  "params": {
    "sessionKey": "bridge-session",
    "message": "How are you?",
    "idempotencyKey": "unique-key-abc123"
  }
}
```

**Receiving response (streamed):**
```json
// Token-by-token streaming:
{"type": "evt", "event": "chat.tick", "data": {"text": "I'm", "sessionKey": "bridge-session"}}
{"type": "evt", "event": "chat.tick", "data": {"text": " doing", "sessionKey": "bridge-session"}}
{"type": "evt", "event": "chat.tick", "data": {"text": " great!", "sessionKey": "bridge-session"}}

// Final response:
{"type": "res", "id": "msg-123", "result": {"ok": true, "runId": "run-xyz"}}
```

### 2.4 Bridge Code (bridge.py)

```python
"""Agent Bridge — Routes messages between Backend and OpenClaw bots."""

import asyncio
import json
import logging
import os
from uuid import uuid4

import httpx
import websockets

logger = logging.getLogger("agent-bridge")

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")

# Map agent names to their OpenClaw gateway WebSocket URLs
AGENT_GATEWAYS = {
    "CTO": {
        "ws_url": "ws://clawdbot-1:18790",
        "agent_name": "CTO",
        "backend_agent_id": None,  # Resolved at startup
    },
    "Developer": {
        "ws_url": "ws://clawdbot-2:18790",
        "agent_name": "Developer",
        "backend_agent_id": None,
    },
    "DevOps": {
        "ws_url": "ws://clawdbot-3:18790",
        "agent_name": "DevOps (ClawdBot 3)",
        "backend_agent_id": None,
    },
}

# Active gateway connections
gateway_connections = {}


class OpenClawGatewayClient:
    """Client for OpenClaw's internal WebSocket gateway."""

    def __init__(self, name: str, ws_url: str, token: str):
        self.name = name
        self.ws_url = ws_url
        self.token = token
        self.ws = None
        self.pending_requests = {}  # id -> Future
        self.response_buffers = {}  # id -> accumulated text
        self.connected = False

    async def connect(self):
        """Connect to OpenClaw gateway and authenticate."""
        self.ws = await websockets.connect(self.ws_url)

        # Send connect request
        connect_id = f"connect-{uuid4().hex[:8]}"
        await self.ws.send(json.dumps({
            "type": "req",
            "id": connect_id,
            "method": "connect",
            "params": {
                "token": self.token,
                "clientName": "bridge",
                "clientDisplayName": "Agent Bridge",
                "clientVersion": "1.0",
                "mode": "cli",
                "protocol": 3,
            }
        }))

        # Wait for connect response
        raw = await asyncio.wait_for(self.ws.recv(), timeout=10)
        data = json.loads(raw)
        if data.get("type") == "res" and data.get("id") == connect_id:
            self.connected = True
            logger.info("Connected to %s gateway at %s", self.name, self.ws_url)
        else:
            raise Exception(f"Unexpected connect response: {data}")

    async def send_message(self, message: str, session_key: str = "bridge") -> str:
        """Send a message to the OpenClaw bot and wait for the full response."""
        if not self.connected or not self.ws:
            raise Exception(f"Not connected to {self.name}")

        req_id = f"msg-{uuid4().hex[:8]}"
        idempotency_key = uuid4().hex

        # Send chat.send request
        await self.ws.send(json.dumps({
            "type": "req",
            "id": req_id,
            "method": "chat.send",
            "params": {
                "sessionKey": session_key,
                "message": message,
                "idempotencyKey": idempotency_key,
            }
        }))

        # Collect response tokens
        full_response = ""
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=120)
            data = json.loads(raw)

            if data.get("type") == "evt" and data.get("event") == "chat.tick":
                text = data.get("data", {}).get("text", "")
                full_response += text

            elif data.get("type") == "res" and data.get("id") == req_id:
                # Final response
                break

            elif data.get("type") == "evt" and data.get("event") == "chat.done":
                break

        return full_response.strip() or "(No response)"

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.connected = False


class AgentBridge:
    """Main bridge service — routes messages between Backend and OpenClaw bots."""

    def __init__(self):
        self.backend_ws = None
        self.bridge_agent_id = None
        self.gateways = {}  # name -> OpenClawGatewayClient
        self.agent_id_map = {}  # backend_agent_id -> gateway_name

    async def start(self):
        """Start the bridge service."""
        # 1. Register with backend
        await self.register_with_backend()

        # 2. Resolve agent IDs
        await self.resolve_agent_ids()

        # 3. Connect to OpenClaw gateways
        await self.connect_gateways()

        # 4. Connect to backend WebSocket
        await self.connect_backend_ws()

    async def register_with_backend(self):
        """Register bridge as an agent."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{BACKEND_URL}/api/agents/register", json={
                "name": "Agent Bridge",
                "type": "bridge",
                "meta_data": {"capabilities": ["message_routing"]}
            })
            if resp.status_code in (200, 201):
                self.bridge_agent_id = resp.json().get("id")
                logger.info("Registered as bridge agent: %s", self.bridge_agent_id)
            else:
                logger.warning("Bridge registration: %s", resp.status_code)

    async def resolve_agent_ids(self):
        """Map backend agent IDs to gateway names."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BACKEND_URL}/api/agents")
            if resp.status_code == 200:
                for agent in resp.json():
                    name = agent.get("name", "")
                    aid = agent.get("id", "")
                    for gw_name, gw_info in AGENT_GATEWAYS.items():
                        if gw_name.lower() in name.lower():
                            gw_info["backend_agent_id"] = aid
                            self.agent_id_map[aid] = gw_name
                            logger.info("Mapped %s -> %s (%s)", name, gw_name, aid)

    async def connect_gateways(self):
        """Connect to each OpenClaw bot's gateway."""
        for name, info in AGENT_GATEWAYS.items():
            try:
                client = OpenClawGatewayClient(name, info["ws_url"], GATEWAY_TOKEN)
                await client.connect()
                self.gateways[name] = client
            except Exception as e:
                logger.error("Failed to connect to %s: %s", name, e)

    async def connect_backend_ws(self):
        """Connect to backend WebSocket and listen for messages."""
        ws_url = BACKEND_URL.replace("http://", "ws://") + f"/ws/{self.bridge_agent_id}"

        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    self.backend_ws = ws
                    logger.info("Connected to backend WebSocket")
                    async for raw in ws:
                        data = json.loads(raw)
                        await self.handle_backend_event(data)
            except Exception as e:
                logger.warning("Backend WS disconnected: %s. Reconnecting...", e)
                await asyncio.sleep(5)

    async def handle_backend_event(self, data: dict):
        """Handle events from backend WebSocket."""
        event = data.get("event")
        event_data = data.get("data", {})

        if event == "message:received":
            sender_id = event_data.get("sender_id", "")
            content = event_data.get("content", "")

            # Check if any of the recipients are OpenClaw bots
            # The bridge receives ALL messages (it's subscribed to the bus)
            # We need to check if we should handle this

            # Find which gateway this is for
            for agent_id, gw_name in self.agent_id_map.items():
                if gw_name in self.gateways:
                    # Forward to OpenClaw bot
                    logger.info("Routing message to %s: %s", gw_name, content[:100])
                    response = await self.route_to_gateway(gw_name, content)

                    # Send response back via backend
                    await self.send_backend_message(
                        content=f"[{gw_name}] {response}",
                        recipients=[sender_id],
                    )
                    break

        elif event == "task:assigned":
            task_id = event_data.get("task_id")
            logger.info("Task assigned via bridge: %s", task_id)

    async def route_to_gateway(self, gateway_name: str, message: str) -> str:
        """Send a message to an OpenClaw bot and get the response."""
        gw = self.gateways.get(gateway_name)
        if not gw:
            return f"Gateway {gateway_name} not connected"

        try:
            response = await gw.send_message(message)
            logger.info("Got response from %s: %s", gateway_name, response[:100])
            return response
        except Exception as e:
            logger.error("Gateway %s error: %s", gateway_name, e)
            return f"Error from {gateway_name}: {e}"

    async def send_backend_message(self, content: str, recipients: list):
        """Send a message through the backend WebSocket."""
        if not self.backend_ws:
            return
        await self.backend_ws.send(json.dumps({
            "event": "message:send",
            "data": {
                "content": content,
                "message_type": "text",
                "recipients": recipients,
            }
        }))


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    bridge = AgentBridge()
    await bridge.start()


if __name__ == "__main__":
    asyncio.run(main())
```

### 2.5 Docker Setup

**`agent-bridge/Dockerfile`:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bridge.py"]
```

**`agent-bridge/requirements.txt`:**
```
websockets>=13.0
httpx>=0.28.1
```

**Add to `docker-compose.yml`:**
```yaml
agent-bridge:
  build:
    context: ./agent-bridge
    dockerfile: Dockerfile
  depends_on:
    - backend
    - clawdbot-1
    - clawdbot-2
    - clawdbot-3
  environment:
    - BACKEND_URL=http://backend:8000
    - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
    - PYTHONUNBUFFERED=1
  restart: unless-stopped
```

---

## Phase 3: Update Alex's /ask Command

Once the bridge is running, update Alex's `/ask` command to use the backend properly:

```python
async def ask_command(update, context):
    target_name = args[0]  # e.g., "CTO"
    message = " ".join(args[1:])

    # Send to backend — bridge will route to the OpenClaw bot
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{BACKEND_URL}/api/messages", json={
            "sender_id": agent_id,
            "content": message,
            "message_type": "text",
            "recipients": [target_agent_id],
        })

    # Alex will receive the response via WebSocket (handle_ws_event)
    await update.message.reply_text(f"Asked {target_name}: '{message}'\nWaiting for response...")
```

When the response comes back via WebSocket:
```python
async def handle_ws_event(data):
    if data["event"] == "message:received":
        content = data["data"]["content"]
        # Forward to Telegram user
        await telegram_app.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Reply: {content}"
        )
```

---

## Phase 4: OpenClaw Config Changes

### 4.1 Add Gateway LAN Binding

Each clawdbot config needs the gateway section:

**`config/clawdbot-1.json5`:**
```json5
{
  gateway: {
    bind: "lan",  // 0.0.0.0 — accessible from other containers
    auth: {
      token: "${OPENCLAW_GATEWAY_TOKEN}"
    }
  },
  agents: { /* existing */ },
  tools: { /* existing */ },
  channels: { /* existing */ },
  // ...
}
```

Same for `clawdbot-2.json5` and `clawdbot-3.json5`.

---

## Phase 5: Full Message Flow (End-to-End)

```
USER: /ask CTO How are you?
  |
  v
ALEX (Telegram bot):
  1. Parses command: target="CTO", message="How are you?"
  2. Looks up CTO's backend agent_id
  3. POST /api/messages {sender: alex_id, content: "How are you?", recipients: [cto_id]}
  4. Replies to user: "Asked CTO, waiting..."
  |
  v
BACKEND:
  5. Stores message in DB
  6. Routes via WebSocket to Bridge (bridge is subscribed)
  |
  v
BRIDGE:
  7. Receives message:received event
  8. Maps cto_id → "CTO" → clawdbot-1:18790
  9. Connects (or reuses connection) to CTO's OpenClaw gateway
  10. Sends: {"type":"req", "method":"chat.send", "params":{"message":"How are you?", ...}}
  |
  v
CTO (OpenClaw Bot):
  11. Receives chat.send via gateway WebSocket
  12. Processes through LLM (GLM-4.7)
  13. Streams response via chat.tick events
  14. Sends final response
  |
  v
BRIDGE:
  15. Collects full response from chat.tick events
  16. Sends back to backend: message:send {content: "[CTO] I'm doing great!", recipients: [alex_id]}
  |
  v
BACKEND:
  17. Routes to Alex via WebSocket
  |
  v
ALEX:
  18. Receives message:received in handle_ws_event
  19. Forwards to user on Telegram: "CTO says: I'm doing great!"
  |
  v
USER sees: "CTO says: I'm doing great!"
```

**Total latency:** ~5-15 seconds (mostly LLM processing time)

---

## Phase 6: SaaS Roadmap — "Hire Agents Per Hour"

### Vision
Users pay to "hire" AI agents that collaborate as a team. User submits a task, the CTO agent breaks it down, delegates to Developer and DevOps agents, they implement and deploy.

### Features Needed (Priority Order)

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| 1 | **User Auth** | Login/signup, JWT tokens, multi-tenant isolation | Medium |
| 2 | **Task Submission API** | Users submit tasks via web UI or API | Small |
| 3 | **Agent Orchestrator** | CTO auto-delegates sub-tasks to Developer/DevOps | Large |
| 4 | **Real-Time Dashboard** | WebSocket streaming of agent conversations | Medium |
| 5 | **Conversation Rooms** | Agents discuss in topic-based rooms | Medium |
| 6 | **Billing & Metering** | Track agent-hours, charge per usage | Medium |
| 7 | **Agent Marketplace** | List agents with capabilities, ratings | Medium |
| 8 | **NATS JetStream** | Replace in-memory WebSocket with proper message broker | Large |
| 9 | **Task Leasing** | Atomic task claiming, prevent duplicates | Medium |
| 10 | **Failure Recovery** | Dead agent detection, task reassignment | Medium |
| 11 | **Event Sourcing** | Full conversation replay and audit trail | Large |
| 12 | **Security** | Rate limiting, message signing, API keys | Medium |

### SaaS Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Web Dashboard (React)          │
                    │  - Submit tasks    - Watch agents work   │
                    │  - View history    - Manage billing      │
                    └──────────────┬──────────────────────────┘
                                   │ WebSocket + REST
                    ┌──────────────┴──────────────────────────┐
                    │         API Gateway (FastAPI)             │
                    │  - Auth (JWT)      - Rate limiting        │
                    │  - Task routing    - Billing metering     │
                    └──────────────┬──────────────────────────┘
                                   │
                    ┌──────────────┴──────────────────────────┐
                    │       Message Broker (NATS JetStream)     │
                    │  - Ordered streams  - Deduplication       │
                    │  - Replay           - Work queues         │
                    └──┬─────────┬─────────┬─────────┬────────┘
                       │         │         │         │
                    ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐
                    │ CTO │  │ Dev │  │ Ops │  │Alex │
                    │Agent│  │Agent│  │Agent│  │(Mem)│
                    └─────┘  └─────┘  └─────┘  └─────┘

                    ┌─────────────────────────────────────────┐
                    │          PostgreSQL + Redis               │
                    │  - Tasks, messages, users, billing        │
                    │  - Session cache, rate limiting           │
                    └─────────────────────────────────────────┘
```

### User Flow

```
1. User signs up → gets API key
2. User creates a task: "Build me a landing page for my SaaS"
3. CTO agent receives task → breaks into sub-tasks:
   - "Design the HTML/CSS layout" → assigns to Developer
   - "Set up hosting on Vercel" → assigns to DevOps
   - "Write compelling copy" → assigns to Developer
4. Developer and DevOps work on sub-tasks
5. Agents communicate in a conversation room
6. User watches progress in real-time dashboard
7. Agents complete work → CTO reviews → marks task done
8. User gets billed for agent-hours used
```

### Pricing Model Ideas

| Plan | Price | Includes |
|------|-------|----------|
| Free | $0 | 5 tasks/month, 1 agent-hour |
| Pro | $29/mo | 50 tasks/month, 20 agent-hours |
| Team | $99/mo | Unlimited tasks, 100 agent-hours |
| Enterprise | Custom | Dedicated agents, SLA, priority |

---

## Implementation Order

### Week 1: Bot-to-Bot Bridge (THIS WEEK)
- [ ] Add `gateway.bind: "lan"` to OpenClaw configs
- [ ] Create `agent-bridge/` service
- [ ] Implement `OpenClawGatewayClient` (connect, chat.send, collect response)
- [ ] Implement `AgentBridge` (backend WS + gateway routing)
- [ ] Add to docker-compose.yml
- [ ] Update Alex's `/ask` command to use backend routing
- [ ] Test: `/ask CTO How are you?` → CTO responds → Alex shows response
- [ ] Test: `/ask Developer Write hello world` → Developer responds

### Week 2: Conversation Rooms + Orchestrator
- [ ] Add conversation/session model to backend
- [ ] Agents can join rooms and discuss
- [ ] CTO auto-delegates when receiving complex tasks
- [ ] Task dependency tracking

### Week 3: Real-Time Dashboard
- [ ] React web UI
- [ ] WebSocket streaming of agent conversations
- [ ] Task progress visualization

### Week 4: Auth + Multi-Tenancy
- [ ] User signup/login (JWT)
- [ ] Tenant isolation (each user gets own workspace)
- [ ] API key generation

### Week 5-6: NATS JetStream + Billing
- [ ] Replace WebSocket routing with NATS JetStream
- [ ] Message ordering, deduplication, replay
- [ ] Usage metering and billing integration (Stripe)

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `agent-bridge/bridge.py` | **Create** | Main bridge service |
| `agent-bridge/openclaw_client.py` | **Create** | OpenClaw gateway WebSocket client |
| `agent-bridge/config.py` | **Create** | Configuration |
| `agent-bridge/Dockerfile` | **Create** | Docker image |
| `agent-bridge/requirements.txt` | **Create** | Python dependencies |
| `docker-compose.yml` | **Edit** | Add bridge service |
| `config/clawdbot-1.json5` | **Edit** | Add `gateway.bind: "lan"` |
| `config/clawdbot-2.json5` | **Edit** | Add `gateway.bind: "lan"` |
| `config/clawdbot-3.json5` | **Edit** | Add `gateway.bind: "lan"` |
| `memu-bot/bot.py` | **Edit** | Update `/ask` to use backend routing |

---

## Testing Plan

1. **Unit test:** OpenClawGatewayClient connects and sends chat.send
2. **Integration test:** Bridge routes message from backend to CTO and back
3. **E2E test:** User sends `/ask CTO How are you?` on Telegram → gets CTO's response
4. **Load test:** Multiple concurrent messages to different agents
5. **Failure test:** What happens when an OpenClaw bot is down? (graceful error message)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenClaw gateway protocol changes | High | Pin OpenClaw version, add protocol version check |
| Gateway auth issues | Medium | Use same token as existing config |
| Message ordering in concurrent requests | Medium | Use idempotency keys, queue per-agent |
| OpenClaw bot takes too long to respond | Medium | 120s timeout, stream partial responses |
| Docker network issues | Low | All on same compose network |
