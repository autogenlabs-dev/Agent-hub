from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class SharedMemory(Base):
    __tablename__ = "shared_memory"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=False)
    created_by = Column(String, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_control = Column(JSON, default={})  # e.g., {"read": ["agent1"], "write": ["agent1"]}
    
    # Relationships
    creator = relationship("Agent", back_populates="memory_accesses")
    
    def __repr__(self):
        return f"<SharedMemory(id={self.id}, key={self.key}, created_by={self.created_by})>"