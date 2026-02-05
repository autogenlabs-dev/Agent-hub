from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = Field(default="text", pattern="^(text|system|error|info)$")
    task_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}


class MessageCreate(MessageBase):
    sender_id: str
    recipients: Optional[List[str]] = []  # List of agent IDs to send to


class MessageResponse(MessageBase):
    id: str
    sender_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True