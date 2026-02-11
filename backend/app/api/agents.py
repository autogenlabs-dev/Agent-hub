from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentStatusUpdate

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/health")
async def health_check():
    """System health check - monitors agent WebSocket connections."""
    from app.websocket.connection_manager import manager
    
    expected_agents = ["memu-bot", "clawdbot-1", "clawdbot-2", "clawdbot-3"]
    agent_status = {}
    
    for agent_id in expected_agents:
        agent_status[agent_id] = "connected" if agent_id in manager.active_connections else "disconnected"
    
    connected_count = sum(1 for s in agent_status.values() if s == "connected")
    
    return {
        "status": "healthy" if connected_count >= 3 else "degraded" if connected_count >= 1 else "unhealthy",
        "backend": "running",
        "agents": agent_status,
        "connected_count": connected_count,
        "total_expected": len(expected_agents)
    }



@router.post("/register", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new agent"""
    service = AgentService(db)
    
    # Check if agent with same name already exists
    existing = await service.get_agent_by_name(agent_data.name)
    if existing:
        # Idempotent registration: verify type matches and return existing
        if existing.type != agent_data.type:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent exists with different type"
             )
        # Update status to online since they are registering
        await service.update_status(existing.id, "online")
        return existing
    
    agent = await service.create_agent(agent_data)
    return agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all agents"""
    service = AgentService(db)
    agents = await service.list_agents(skip=skip, limit=limit)
    return agents


@router.get("/online", response_model=List[AgentResponse])
async def list_online_agents(db: AsyncSession = Depends(get_db)):
    """List all online agents"""
    service = AgentService(db)
    agents = await service.get_online_agents()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent by ID"""
    service = AgentService(db)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update agent"""
    service = AgentService(db)
    agent = await service.update_agent(agent_id, agent_data)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update agent status"""
    service = AgentService(db)
    agent = await service.update_status(agent_id, status_data.status)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete agent"""
    service = AgentService(db)
    success = await service.delete_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return None


@router.get("/{agent_id}/next-task")
async def get_next_task(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the next priority task for this agent to work on"""
    from app.services.task_service import TaskService
    from app.schemas.task import TaskResponse
    
    task_service = TaskService(db)
    task = await task_service.get_next_task(agent_id)
    if not task:
        return {"status": "idle", "message": "No tasks assigned. Awaiting delegation."}
    return {"status": "has_task", "task": TaskResponse.model_validate(task)}


@router.get("/{agent_id}/what-next")
async def get_what_next(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get full work queue and recommendations for autonomous agents"""
    from app.services.task_service import TaskService
    from app.services.message_service import MessageService
    
    task_service = TaskService(db)
    message_service = MessageService(db)
    
    # Get work queue
    work_queue = await task_service.get_agent_work_queue(agent_id)
    
    # Get recent messages for this agent
    recent_messages = await message_service.list_messages(limit=5, sender_id=agent_id)
    
    return {
        "agent_id": agent_id,
        "work_queue": {
            "assigned_count": len(work_queue["assigned_tasks"]),
            "in_progress_count": len(work_queue["in_progress_tasks"]),
            "available_count": len(work_queue["available_tasks"]),
        },
        "next_action": work_queue["recommendations"][0] if work_queue["recommendations"] else "Process assigned tasks",
        "recent_messages": len(recent_messages)
    }


@router.post("/{agent_id}/claim/{task_id}")
async def claim_task(
    agent_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Worker claims a task and starts working on it"""
    from app.services.task_service import TaskService
    from app.schemas.task import TaskResponse
    
    task_service = TaskService(db)
    task = await task_service.claim_task(task_id, agent_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or cannot be claimed"
        )
    return {"status": "claimed", "task": TaskResponse.model_validate(task)}


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Worker reports alive status - updates last_seen timestamp"""
    service = AgentService(db)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    # Update last_seen
    agent = await service.update_status(agent_id, agent.status)
    return {"status": "ok", "agent_id": agent_id, "last_seen": agent.last_seen}