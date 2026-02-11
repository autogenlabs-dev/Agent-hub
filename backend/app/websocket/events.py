from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import manager
import json
import logging

logger = logging.getLogger(__name__)


async def handle_agent_websocket(websocket: WebSocket, agent_id: str):
    """Handle WebSocket connection for an agent"""
    try:
        # Accept connection
        await manager.connect(websocket, agent_id)
        
        # Send welcome message
        await websocket.send_json({
            "event": "connected",
            "data": {
                "agent_id": agent_id,
                "message": "Successfully connected to Agent Communication Channel"
            }
        })
        
        # Notify other agents
        await manager.broadcast({
            "event": "agent:joined",
            "data": {
                "agent_id": agent_id
            }
        }, exclude_agent_id=agent_id)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            await process_agent_event(agent_id, data, websocket)
            
    except WebSocketDisconnect:
        logger.info(f"Agent {agent_id} disconnected")
        manager.disconnect(agent_id)
        try:
            await manager.broadcast({
                "event": "agent:left",
                "data": {
                    "agent_id": agent_id
                }
            })
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in agent websocket connection: {e}")
        manager.disconnect(agent_id)
        try:
            await manager.broadcast({
                "event": "agent:left",
                "data": {
                    "agent_id": agent_id
                }
            })
        except Exception:
            pass


async def process_agent_event(agent_id: str, data: dict, websocket: WebSocket):
    """Process incoming events from an agent"""
    event_type = data.get("event")
    event_data = data.get("data", {})
    
    logger.info(f"Received event from agent {agent_id}: {event_type}")
    
    # Route events to appropriate handlers
    if event_type == "agent:register":
        logger.info(f"Agent {agent_id} registered: {event_data}")
    elif event_type == "agent:heartbeat":
        await handle_heartbeat(agent_id, event_data)
    elif event_type == "message:send":
        await handle_message_send(agent_id, event_data)
    elif event_type == "task:create":
        await handle_task_create(agent_id, event_data)
    elif event_type == "task:assign":
        await handle_task_assign(agent_id, event_data)
    elif event_type == "task:update":
        await handle_task_update(agent_id, event_data)
    elif event_type == "memory:set":
        await handle_memory_set(agent_id, event_data)
    elif event_type == "memory:get":
        await handle_memory_get(agent_id, event_data, websocket)
    else:
        logger.warning(f"Unknown event type: {event_type}")


async def handle_heartbeat(agent_id: str, data: dict):
    """Handle heartbeat from agent"""
    # Update agent last_seen timestamp in database
    from app.services.agent_service import AgentService
    from app.core.database import get_db
    
    async for db in get_db():
        service = AgentService(db)
        await service.update_last_seen(agent_id)
        break
    
    # Send heartbeat response
    await manager.send_personal_message({
        "event": "agent:heartbeat_ack",
        "data": {
            "timestamp": data.get("timestamp")
        }
    }, agent_id)


async def handle_message_send(agent_id: str, data: dict):
    """Handle message sending from agent"""
    from app.services.message_service import MessageService
    from app.core.database import get_db
    from app.schemas.message import MessageCreate
    
    async for db in get_db():
        service = MessageService(db)
        
        # Create message
        message_data = MessageCreate(
            sender_id=agent_id,
            content=data.get("content"),
            message_type=data.get("message_type", "text"),
            task_id=data.get("task_id"),
            recipients=data.get("recipients", []),
            metadata=data.get("metadata", {})
        )
        
        message = await service.create_message(message_data)
        
        # Send to recipients
        recipients = data.get("recipients", [])
        if recipients:
            await manager.send_to_agents({
                "event": "message:received",
                "data": {
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "task_id": message.task_id,
                    "created_at": message.created_at.isoformat()
                }
            }, recipients)
        
        # Send confirmation to sender
        await manager.send_personal_message({
            "event": "message:sent",
            "data": {
                "id": message.id
            }
        }, agent_id)
        
        break


async def handle_task_create(agent_id: str, data: dict):
    """Handle task creation from agent"""
    from app.services.task_service import TaskService
    from app.core.database import get_db
    from app.schemas.task import TaskCreate
    
    async for db in get_db():
        service = TaskService(db)
        
        task_data = TaskCreate(
            creator_id=agent_id,
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority", 1),
            due_date=data.get("due_date"),
            requirements=data.get("requirements", {})
        )
        
        task = await service.create_task(task_data)
        
        # Broadcast task creation
        await manager.broadcast({
            "event": "task:created",
            "data": {
                "id": task.id,
                "creator_id": task.creator_id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat()
            }
        })
        
        break


async def handle_task_assign(agent_id: str, data: dict):
    """Handle task assignment from agent"""
    from app.services.task_service import TaskService
    from app.core.database import get_db
    
    async for db in get_db():
        service = TaskService(db)
        
        assignment = await service.assign_task(
            data.get("task_id"),
            data.get("agent_id")
        )
        
        # Notify assigned agent
        await manager.send_personal_message({
            "event": "task:assigned",
            "data": {
                "task_id": assignment.task_id,
                "assignment_id": assignment.id,
                "assigned_at": assignment.assigned_at.isoformat()
            }
        }, data.get("agent_id"))
        
        # Notify creator
        await manager.send_personal_message({
            "event": "task:assignment_created",
            "data": {
                "task_id": assignment.task_id,
                "agent_id": assignment.agent_id
            }
        }, agent_id)
        
        break


async def handle_task_update(agent_id: str, data: dict):
    """Handle task status update from agent"""
    from app.services.task_service import TaskService
    from app.core.database import get_db
    from app.schemas.task import TaskUpdate
    
    async for db in get_db():
        service = TaskService(db)
        
        update_data = TaskUpdate(**data)
        task = await service.update_task(data.get("task_id"), update_data)
        
        # Broadcast task update
        await manager.broadcast({
            "event": "task:updated",
            "data": {
                "id": task.id,
                "status": task.status,
                "updated_at": task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
            }
        })
        
        break


async def handle_memory_set(agent_id: str, data: dict):
    """Handle memory setting from agent"""
    from app.services.memory_service import MemoryService
    from app.core.database import get_db
    from app.schemas.memory import MemoryCreate, MemoryUpdate
    
    async for db in get_db():
        service = MemoryService(db)
        
        # Check if memory exists
        existing = await service.get_memory_by_key(data.get("key"))
        
        if existing:
            # Update existing memory
            update_data = MemoryUpdate(
                value=data.get("value"),
                access_control=data.get("access_control")
            )
            memory = await service.update_memory(existing.id, update_data)
        else:
            # Create new memory
            memory_data = MemoryCreate(
                key=data.get("key"),
                value=data.get("value"),
                created_by=agent_id,
                access_control=data.get("access_control")
            )
            memory = await service.create_memory(memory_data)
        
        # Broadcast memory update
        await manager.broadcast({
            "event": "memory:updated",
            "data": {
                "key": memory.key,
                "updated_at": memory.updated_at.isoformat()
            }
        })
        
        break


async def handle_memory_get(agent_id: str, data: dict, websocket: WebSocket):
    """Handle memory retrieval from agent"""
    from app.services.memory_service import MemoryService
    from app.core.database import get_db
    
    async for db in get_db():
        service = MemoryService(db)
        
        memory = await service.get_memory_by_key(data.get("key"))
        
        if memory:
            await websocket.send_json({
                "event": "memory:response",
                "data": {
                    "key": memory.key,
                    "value": memory.value,
                    "created_by": memory.created_by,
                    "updated_at": memory.updated_at.isoformat()
                }
            })
        else:
            await websocket.send_json({
                "event": "memory:response",
                "data": {
                    "key": data.get("key"),
                    "error": "Memory not found"
                }
            })
        
        break