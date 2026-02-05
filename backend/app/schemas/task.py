from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=4)
    due_date: Optional[datetime] = None
    requirements: Optional[Dict[str, Any]] = {}


class TaskCreate(TaskBase):
    creator_id: str


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|assigned|in_progress|completed|failed)$")
    priority: Optional[int] = Field(None, ge=1, le=4)
    due_date: Optional[datetime] = None
    requirements: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    id: str
    creator_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskAssignmentCreate(BaseModel):
    agent_id: str


class TaskAssignmentResponse(BaseModel):
    id: str
    task_id: str
    agent_id: str
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskComplete(BaseModel):
    result: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None