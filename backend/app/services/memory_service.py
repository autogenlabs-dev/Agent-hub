from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.memory import SharedMemory
from app.schemas.memory import MemoryCreate, MemoryUpdate


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_memory(self, memory_data: MemoryCreate) -> SharedMemory:
        """Create a new shared memory entry"""
        db_memory = SharedMemory(**memory_data.model_dump())
        self.db.add(db_memory)
        await self.db.commit()
        await self.db.refresh(db_memory)
        return db_memory
    
    async def get_memory(self, memory_id: str) -> Optional[SharedMemory]:
        """Get memory by ID"""
        result = await self.db.execute(select(SharedMemory).where(SharedMemory.id == memory_id))
        return result.scalar_one_or_none()
    
    async def get_memory_by_key(self, key: str) -> Optional[SharedMemory]:
        """Get memory by key"""
        result = await self.db.execute(select(SharedMemory).where(SharedMemory.key == key))
        return result.scalar_one_or_none()
    
    async def list_memories(
        self,
        skip: int = 0,
        limit: int = 100,
        created_by: Optional[str] = None
    ) -> List[SharedMemory]:
        """List memories with optional filters"""
        query = select(SharedMemory)
        
        if created_by:
            query = query.where(SharedMemory.created_by == created_by)
        
        query = query.order_by(SharedMemory.updated_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_memory(self, memory_id: str, memory_data: MemoryUpdate) -> Optional[SharedMemory]:
        """Update memory"""
        memory = await self.get_memory(memory_id)
        if not memory:
            return None
        
        update_data = memory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(memory, field, value)
        
        await self.db.commit()
        await self.db.refresh(memory)
        return memory
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        memory = await self.get_memory(memory_id)
        if not memory:
            return False
        
        await self.db.delete(memory)
        await self.db.commit()
        return True
    
    async def check_access(self, memory: SharedMemory, agent_id: str, access_type: str = "read") -> bool:
        """Check if agent has access to memory"""
        access_control = memory.access_control or {}
        
        # If no access control, allow all
        if not access_control:
            return True
        
        # Check specific access
        allowed_agents = access_control.get(access_type, [])
        
        # If no agents specified for this access type, allow all
        if not allowed_agents:
            return True
        
        # Check if agent is in allowed list
        return agent_id in allowed_agents
    
    async def get_accessible_memories(self, agent_id: str, access_type: str = "read") -> List[SharedMemory]:
        """Get memories accessible to an agent"""
        result = await self.db.execute(select(SharedMemory))
        all_memories = result.scalars().all()
        
        accessible = []
        for memory in all_memories:
            if await self.check_access(memory, agent_id, access_type):
                accessible.append(memory)
        
        return accessible