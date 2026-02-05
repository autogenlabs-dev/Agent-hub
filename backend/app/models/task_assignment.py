from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    status = Column(String, default="assigned")  # assigned, accepted, rejected, completed, failed
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="assignments")
    agent = relationship("Agent", back_populates="task_assignments")
    
    def __repr__(self):
        return f"<TaskAssignment(id={self.id}, task_id={self.task_id}, agent_id={self.agent_id}, status={self.status})>"