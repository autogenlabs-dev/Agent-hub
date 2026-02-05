from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime
from app.models.task import Task
from app.models.task_assignment import TaskAssignment
from app.models.agent import Agent
from app.schemas.task import TaskCreate, TaskUpdate, TaskAssignmentCreate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task"""
        db_task = Task(**task_data.model_dump())
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return db_task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        creator_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> List[Task]:
        """List tasks with optional filters"""
        query = select(Task)
        
        conditions = []
        if creator_id:
            conditions.append(Task.creator_id == creator_id)
        if status:
            conditions.append(Task.status == status)
        if priority:
            conditions.append(Task.priority == priority)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """Update task"""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        # Set completed_at if status is completed
        if task.status == "completed" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await self.db.delete(task)
        await self.db.commit()
        return True
    
    async def assign_task(self, task_id: str, agent_id: str) -> TaskAssignment:
        """Assign task to an agent"""
        # Check if task exists
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Check if agent exists
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Check if assignment already exists
        existing = await self.db.execute(
            select(TaskAssignment).where(
                and_(TaskAssignment.task_id == task_id, TaskAssignment.agent_id == agent_id)
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Task already assigned to agent {agent_id}")
        
        # Create assignment
        assignment = TaskAssignment(
            task_id=task_id,
            agent_id=agent_id,
            status="assigned"
        )
        self.db.add(assignment)
        
        # Update task status
        task.status = "assigned"
        
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment
    
    async def complete_task(self, task_id: str, agent_id: str, result: Optional[dict] = None) -> Optional[Task]:
        """Mark task as completed by an agent"""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        # Update task status
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        if result:
            task.requirements = {**task.requirements, "result": result}
        
        # Update assignment status
        result = await self.db.execute(
            select(TaskAssignment).where(
                and_(TaskAssignment.task_id == task_id, TaskAssignment.agent_id == agent_id)
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment:
            assignment.status = "completed"
            assignment.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_task_assignments(self, task_id: str) -> List[TaskAssignment]:
        """Get all assignments for a task"""
        result = await self.db.execute(
            select(TaskAssignment)
            .where(TaskAssignment.task_id == task_id)
            .order_by(TaskAssignment.assigned_at.desc())
        )
        return result.scalars().all()
    
    async def get_agent_tasks(self, agent_id: str, status: Optional[str] = None) -> List[Task]:
        """Get tasks assigned to an agent"""
        query = (
            select(Task)
            .join(TaskAssignment)
            .where(TaskAssignment.agent_id == agent_id)
        )
        
        if status:
            query = query.where(Task.status == status)
        
        query = query.order_by(Task.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        result = await self.db.execute(
            select(Task)
            .where(Task.status == "pending")
            .order_by(Task.priority.desc(), Task.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks"""
        result = await self.db.execute(
            select(Task)
            .where(
                and_(
                    Task.due_date < datetime.utcnow(),
                    Task.status.in_(["pending", "assigned", "in_progress"])
                )
            )
            .order_by(Task.due_date.asc())
        )
        return result.scalars().all()