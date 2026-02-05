from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    content = Column(String, nullable=False)
    message_type = Column(String, default="text")  # text, system, error, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_data = Column(JSON, default={})
    
    # Relationships
    sender = relationship("Agent", back_populates="sent_messages", foreign_keys=[sender_id])
    task = relationship("Task", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, content={self.content[:50]}...)>"