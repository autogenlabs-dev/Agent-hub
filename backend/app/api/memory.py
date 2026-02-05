from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def set_memory(
    memory_data: MemoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Store shared memory"""
    service = MemoryService(db)
    
    # Check if memory with same key already exists
    existing = await service.get_memory_by_key(memory_data.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory with this key already exists. Use PUT to update."
        )
    
    memory = await service.create_memory(memory_data)
    return memory


@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List memories with optional filters"""
    service = MemoryService(db)
    memories = await service.list_memories(
        skip=skip,
        limit=limit,
        created_by=created_by
    )
    return memories


@router.get("/key/{key}", response_model=MemoryResponse)
async def get_memory_by_key(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get memory by key"""
    service = MemoryService(db)
    memory = await service.get_memory_by_key(key)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get memory by ID"""
    service = MemoryService(db)
    memory = await service.get_memory(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.put("/key/{key}", response_model=MemoryResponse)
async def update_memory_by_key(
    key: str,
    memory_data: MemoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update memory by key"""
    service = MemoryService(db)
    
    # Get existing memory
    existing = await service.get_memory_by_key(key)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    memory = await service.update_memory(existing.id, memory_data)
    return memory


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    memory_data: MemoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update memory"""
    service = MemoryService(db)
    memory = await service.update_memory(memory_id, memory_data)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.delete("/key/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_by_key(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete memory by key"""
    service = MemoryService(db)
    
    # Get existing memory
    existing = await service.get_memory_by_key(key)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    success = await service.delete_memory(existing.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return None


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete memory"""
    service = MemoryService(db)
    success = await service.delete_memory(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return None