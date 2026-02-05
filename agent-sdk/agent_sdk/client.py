import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import websockets
import httpx
from agent_sdk.models import AgentInfo, Message, Task, TaskAssignment, SharedMemory

logger = logging.getLogger(__name__)


class AgentClient:
    """Client for agents to connect to the communication channel"""
    
    def __init__(
        self,
        name: str,
        agent_type: str,
        server_url: str = "http://localhost:8000",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.agent_type = agent_type
        self.server_url = server_url
        self.metadata = metadata or {}
        
        # Agent info (set after registration)
        self.agent_id: Optional[str] = None
        self.agent_info: Optional[AgentInfo] = None
        
        # WebSocket connection
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._running = False
        
        # Event handlers
        self._message_handlers: List[Callable[[Message], None]] = []
        self._task_assigned_handlers: List[Callable[[Task], None]] = []
        self._task_updated_handlers: List[Callable[[Task], None]] = []
        self._memory_updated_handlers: List[Callable[[SharedMemory], None]] = []
        self._agent_joined_handlers: List[Callable[[str], None]] = []
        self._agent_left_handlers: List[Callable[[str], None]] = []
        
        # HTTP client
        self._http = httpx.AsyncClient(base_url=server_url)
    
    async def connect(self) -> None:
        """Connect to the server"""
        # Register agent
        await self._register()
        
        # Connect WebSocket
        ws_url = self.server_url.replace("http", "ws") + f"/ws/{self.agent_id}"
        self._ws = await websockets.connect(ws_url)
        self._connected = True
        self._running = True
        
        logger.info(f"Agent {self.name} connected as {self.agent_id}")
        
        # Start message handler
        asyncio.create_task(self._message_loop())
    
    async def disconnect(self) -> None:
        """Disconnect from the server"""
        self._running = False
        if self._ws:
            await self._ws.close()
        self._connected = False
        await self._http.aclose()
        logger.info(f"Agent {self.name} disconnected")
    
    async def _register(self) -> None:
        """Register the agent with the server"""
        response = await self._http.post(
            "/api/agents/register",
            json={
                "name": self.name,
                "type": self.agent_type,
                "metadata": self.metadata
            }
        )
        response.raise_for_status()
        data = response.json()
        self.agent_id = data["id"]
        self.agent_info = AgentInfo(**data)
        logger.info(f"Agent {self.name} registered with ID: {self.agent_id}")
    
    async def _message_loop(self) -> None:
        """Handle incoming WebSocket messages"""
        try:
            while self._running and self._ws:
                message = await self._ws.recv()
                await self._handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self._connected = False
        except Exception as e:
            logger.error(f"Error in message loop: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming message from server"""
        event = data.get("event")
        event_data = data.get("data", {})
        
        logger.info(f"Received event: {event}")
        
        if event == "message:received":
            message = Message(**event_data)
            for handler in self._message_handlers:
                await self._call_handler(handler, message)
        
        elif event == "task:assigned":
            task_data = event_data.copy()
            # Get full task details
            task = await self.get_task(task_data["task_id"])
            if task:
                for handler in self._task_assigned_handlers:
                    await self._call_handler(handler, task)
        
        elif event == "task:updated":
            task = Task(**event_data)
            for handler in self._task_updated_handlers:
                await self._call_handler(handler, task)
        
        elif event == "memory:updated":
            # Get full memory details
            memory = await self.get_memory_by_key(event_data["key"])
            if memory:
                for handler in self._memory_updated_handlers:
                    await self._call_handler(handler, memory)
        
        elif event == "agent:joined":
            for handler in self._agent_joined_handlers:
                await self._call_handler(handler, event_data["agent_id"])
        
        elif event == "agent:left":
            for handler in self._agent_left_handlers:
                await self._call_handler(handler, event_data["agent_id"])
    
    async def _call_handler(self, handler: Callable, *args) -> None:
        """Call an event handler safely"""
        try:
            result = handler(*args)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Error in handler: {e}")
    
    async def _send_ws_event(self, event: str, data: Dict[str, Any]) -> None:
        """Send an event via WebSocket"""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected to server")
        
        await self._ws.send_json({"event": event, "data": data})
    
    # Decorators for event handlers
    
    def on_message(self, handler: Callable[[Message], Any]) -> Callable:
        """Register a handler for incoming messages"""
        self._message_handlers.append(handler)
        return handler
    
    def on_task_assigned(self, handler: Callable[[Task], Any]) -> Callable:
        """Register a handler for task assignments"""
        self._task_assigned_handlers.append(handler)
        return handler
    
    def on_task_updated(self, handler: Callable[[Task], Any]) -> Callable:
        """Register a handler for task updates"""
        self._task_updated_handlers.append(handler)
        return handler
    
    def on_memory_updated(self, handler: Callable[[SharedMemory], Any]) -> Callable:
        """Register a handler for memory updates"""
        self._memory_updated_handlers.append(handler)
        return handler
    
    def on_agent_joined(self, handler: Callable[[str], Any]) -> Callable:
        """Register a handler for agent joins"""
        self._agent_joined_handlers.append(handler)
        return handler
    
    def on_agent_left(self, handler: Callable[[str], Any]) -> Callable:
        """Register a handler for agent leaves"""
        self._agent_left_handlers.append(handler)
        return handler
    
    # Message methods
    
    async def send_message(
        self,
        content: str,
        recipients: Optional[List[str]] = None,
        message_type: str = "text",
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a message to other agents"""
        await self._send_ws_event("message:send", {
            "content": content,
            "recipients": recipients or [],
            "message_type": message_type,
            "task_id": task_id,
            "metadata": metadata or {}
        })
        
        # Wait for confirmation
        # In production, you'd want to wait for the message:sent event
        return Message(
            id="pending",
            sender_id=self.agent_id,
            content=content,
            message_type=message_type,
            task_id=task_id,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    # Task methods
    
    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 1,
        due_date: Optional[datetime] = None,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task"""
        await self._send_ws_event("task:create", {
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date.isoformat() if due_date else None,
            "requirements": requirements or {}
        })
        
        return Task(
            id="pending",
            creator_id=self.agent_id,
            title=title,
            description=description,
            status="pending",
            priority=priority,
            created_at=datetime.utcnow(),
            due_date=due_date,
            requirements=requirements or {}
        )
    
    async def assign_task(self, task_id: str, agent_id: str) -> TaskAssignment:
        """Assign a task to an agent"""
        await self._send_ws_event("task:assign", {
            "task_id": task_id,
            "agent_id": agent_id
        })
        
        return TaskAssignment(
            id="pending",
            task_id=task_id,
            agent_id=agent_id,
            status="assigned",
            assigned_at=datetime.utcnow()
        )
    
    async def update_task_status(
        self,
        task_id: str,
        status: str
    ) -> None:
        """Update task status"""
        await self._send_ws_event("task:update", {
            "task_id": task_id,
            "status": status
        })
    
    async def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> None:
        """Complete a task"""
        await self._send_ws_event("task:update", {
            "task_id": task_id,
            "status": "completed"
        })
        
        # Also send completion via API
        await self._http.post(
            f"/api/tasks/{task_id}/complete",
            params={"agent_id": self.agent_id},
            json={"result": result, "notes": notes}
        )
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task details"""
        response = await self._http.get(f"/api/tasks/{task_id}")
        if response.status_code == 200:
            return Task(**response.json())
        return None
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> List[Task]:
        """List tasks"""
        params = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        
        response = await self._http.get("/api/tasks", params=params)
        return [Task(**task) for task in response.json()]
    
    # Memory methods
    
    async def set_memory(
        self,
        key: str,
        value: Dict[str, Any],
        access_control: Optional[Dict[str, List[str]]] = None
    ) -> None:
        """Store shared memory"""
        await self._send_ws_event("memory:set", {
            "key": key,
            "value": value,
            "access_control": access_control
        })
    
    async def get_memory(self, key: str) -> Optional[SharedMemory]:
        """Get shared memory"""
        await self._send_ws_event("memory:get", {"key": key})
        
        # Wait for response (in production, use proper async waiting)
        response = await self._http.get(f"/api/memory/key/{key}")
        if response.status_code == 200:
            return SharedMemory(**response.json())
        return None
    
    async def get_memory_by_key(self, key: str) -> Optional[SharedMemory]:
        """Get memory by key (HTTP)"""
        response = await self._http.get(f"/api/memory/key/{key}")
        if response.status_code == 200:
            return SharedMemory(**response.json())
        return None
    
    async def update_memory(
        self,
        key: str,
        value: Dict[str, Any]
    ) -> None:
        """Update shared memory"""
        await self._http.put(
            f"/api/memory/key/{key}",
            json={"value": value}
        )
    
    # Agent methods
    
    async def update_status(self, status: str) -> None:
        """Update agent status"""
        await self._http.put(
            f"/api/agents/{self.agent_id}/status",
            json={"status": status}
        )
    
    async def list_agents(self) -> List[AgentInfo]:
        """List all agents"""
        response = await self._http.get("/api/agents")
        return [AgentInfo(**agent) for agent in response.json()]
    
    async def get_online_agents(self) -> List[AgentInfo]:
        """Get online agents"""
        response = await self._http.get("/api/agents/online")
        return [AgentInfo(**agent) for agent in response.json()]
    
    # Utility methods
    
    async def send_heartbeat(self) -> None:
        """Send heartbeat to keep connection alive"""
        await self._send_ws_event("agent:heartbeat", {
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self._connected