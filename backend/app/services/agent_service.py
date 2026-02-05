from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """Create a new agent"""
        db_agent = Agent(**agent_data.model_dump())
        self.db.add(db_agent)
        await self.db.commit()
        await self.db.refresh(db_agent)
        return db_agent
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()
    
    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        result = await self.db.execute(select(Agent).where(Agent.name == name))
        return result.scalar_one_or_none()
    
    async def list_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List all agents"""
        result = await self.db.execute(
            select(Agent)
            .order_by(Agent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_agent(self, agent_id: str, agent_data: AgentUpdate) -> Optional[Agent]:
        """Update agent"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        
        update_data = agent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        await self.db.commit()
        await self.db.refresh(agent)
        return agent
    
    async def update_status(self, agent_id: str, status: str) -> Optional[Agent]:
        """Update agent status"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        
        agent.status = status
        agent.last_seen = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(agent)
        return agent
    
    async def update_last_seen(self, agent_id: str) -> Optional[Agent]:
        """Update agent last_seen timestamp"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        
        agent.last_seen = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(agent)
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        await self.db.delete(agent)
        await self.db.commit()
        return True
    
    async def get_online_agents(self) -> List[Agent]:
        """Get all online agents"""
        result = await self.db.execute(
            select(Agent).where(Agent.status == "online")
        )
        return result.scalars().all()
    
    async def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type"""
        result = await self.db.execute(
            select(Agent).where(Agent.type == agent_type)
        )
        return result.scalars().all()