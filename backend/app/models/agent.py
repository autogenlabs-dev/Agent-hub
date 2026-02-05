from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # e.g., "llm", "script", "bot"
    status = Column(String, default="offline")  # online, offline, busy, error
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default={})
    
    # Relationships
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    created_tasks = relationship("Task", back_populates="creator")
    task_assignments = relationship("TaskAssignment", back_populates="agent")
    memory_accesses = relationship("SharedMemory", back_populates="creator")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"