from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskAssignmentCreate, TaskAssignmentResponse, TaskComplete

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    service = TaskService(db)
    task = await service.create_task(task_data)
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    creator_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List tasks with optional filters"""
    service = TaskService(db)
    tasks = await service.list_tasks(
        skip=skip,
        limit=limit,
        creator_id=creator_id,
        status=status,
        priority=priority
    )
    return tasks


@router.get("/pending", response_model=List[TaskResponse])
async def get_pending_tasks(db: AsyncSession = Depends(get_db)):
    """Get all pending tasks"""
    service = TaskService(db)
    tasks = await service.get_pending_tasks()
    return tasks


@router.get("/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(db: AsyncSession = Depends(get_db)):
    """Get all overdue tasks"""
    service = TaskService(db)
    tasks = await service.get_overdue_tasks()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get task by ID"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update task"""
    service = TaskService(db)
    task = await service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete task"""
    service = TaskService(db)
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None


@router.post("/{task_id}/assign", response_model=TaskAssignmentResponse)
async def assign_task(
    task_id: str,
    assignment_data: TaskAssignmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Assign task to an agent"""
    service = TaskService(db)
    try:
        assignment = await service.assign_task(task_id, assignment_data.agent_id)
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    complete_data: TaskComplete,
    agent_id: str = Query(..., description="Agent ID completing the task"),
    db: AsyncSession = Depends(get_db)
):
    """Mark task as completed by an agent"""
    service = TaskService(db)
    task = await service.complete_task(task_id, agent_id, complete_data.result)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.get("/{task_id}/assignments", response_model=List[TaskAssignmentResponse])
async def get_task_assignments(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all assignments for a task"""
    service = TaskService(db)
    assignments = await service.get_task_assignments(task_id)
    return assignments


@router.get("/agent/{agent_id}", response_model=List[TaskResponse])
async def get_agent_tasks(
    agent_id: str,
    task_status: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db)
):
    """Get tasks assigned to an agent"""
    service = TaskService(db)
    tasks = await service.get_agent_tasks(agent_id, task_status)
    return tasks