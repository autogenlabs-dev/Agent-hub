from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    meta_data: Optional[Dict[str, Any]] = {}


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class AgentResponse(AgentBase):
    id: str
    status: str
    created_at: datetime
    last_seen: datetime
    
    class Config:
        from_attributes = True


class AgentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(online|offline|busy|error)$")