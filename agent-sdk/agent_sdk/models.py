from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class AgentInfo(BaseModel):
    """Agent information"""
    id: str
    name: str
    type: str
    status: str
    created_at: datetime
    last_seen: datetime
    metadata: Dict[str, Any] = {}


class Message(BaseModel):
    """Message model"""
    id: str
    sender_id: str
    content: str
    message_type: str
    task_id: Optional[str] = None
    created_at: datetime
    metadata: Dict[str, Any] = {}


class Task(BaseModel):
    """Task model"""
    id: str
    creator_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    created_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    requirements: Dict[str, Any] = {}


class TaskAssignment(BaseModel):
    """Task assignment model"""
    id: str
    task_id: str
    agent_id: str
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None


class SharedMemory(BaseModel):
    """Shared memory model"""
    id: str
    key: str
    value: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime
    access_control: Optional[Dict[str, List[str]]] = None