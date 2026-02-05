from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, assigned, in_progress, completed, failed
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=urgent
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    requirements = Column(JSON, default={})
    
    # Relationships
    creator = relationship("Agent", back_populates="created_tasks")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="task")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status}, priority={self.priority})>"