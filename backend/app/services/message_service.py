from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.message import Message
from app.schemas.message import MessageCreate


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_message(self, message_data: MessageCreate) -> Message:
        """Create a new message"""
        db_message = Message(**message_data.model_dump(exclude={"recipients"}))
        self.db.add(db_message)
        await self.db.commit()
        await self.db.refresh(db_message)
        return db_message
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        result = await self.db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()
    
    async def list_messages(
        self,
        skip: int = 0,
        limit: int = 100,
        sender_id: Optional[str] = None,
        task_id: Optional[str] = None,
        message_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """List messages with optional filters"""
        query = select(Message)
        
        conditions = []
        if sender_id:
            conditions.append(Message.sender_id == sender_id)
        if task_id:
            conditions.append(Message.task_id == task_id)
        if message_type:
            conditions.append(Message.message_type == message_type)
        if since:
            conditions.append(Message.created_at >= since)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_messages_by_task(self, task_id: str) -> List[Message]:
        """Get all messages for a task"""
        result = await self.db.execute(
            select(Message)
            .where(Message.task_id == task_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_recent_messages(self, hours: int = 24) -> List[Message]:
        """Get messages from the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.db.execute(
            select(Message)
            .where(Message.created_at >= since)
            .order_by(Message.created_at.desc())
        )
        return result.scalars().all()
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        message = await self.get_message(message_id)
        if not message:
            return False
        
        await self.db.delete(message)
        await self.db.commit()
        return True
    
    async def count_messages(
        self,
        sender_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> int:
        """Count messages with optional filters"""
        from sqlalchemy import func
        
        query = select(func.count(Message.id))
        
        if sender_id:
            query = query.where(Message.sender_id == sender_id)
        if task_id:
            query = query.where(Message.task_id == task_id)
        
        result = await self.db.execute(query)
        return result.scalar()