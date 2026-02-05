from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class MemoryBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=200)
    value: Dict[str, Any] = Field(..., description="JSON value to store")
    access_control: Optional[Dict[str, List[str]]] = None


class MemoryCreate(MemoryBase):
    created_by: str


class MemoryUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    access_control: Optional[Dict[str, List[str]]] = None


class MemoryResponse(MemoryBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True