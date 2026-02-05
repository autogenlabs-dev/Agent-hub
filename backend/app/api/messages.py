from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a message"""
    service = MessageService(db)
    message = await service.create_message(message_data)
    return message


@router.get("", response_model=List[MessageResponse])
async def list_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sender_id: Optional[str] = None,
    task_id: Optional[str] = None,
    message_type: Optional[str] = None,
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """List messages with optional filters"""
    service = MessageService(db)
    messages = await service.list_messages(
        skip=skip,
        limit=limit,
        sender_id=sender_id,
        task_id=task_id,
        message_type=message_type,
        since=since
    )
    return messages


@router.get("/recent", response_model=List[MessageResponse])
async def get_recent_messages(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get messages from the last N hours"""
    service = MessageService(db)
    messages = await service.get_recent_messages(hours=hours)
    return messages


@router.get("/task/{task_id}", response_model=List[MessageResponse])
async def get_task_messages(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a task"""
    service = MessageService(db)
    messages = await service.get_messages_by_task(task_id)
    return messages


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get message by ID"""
    service = MessageService(db)
    message = await service.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a message"""
    service = MessageService(db)
    success = await service.delete_message(message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return None