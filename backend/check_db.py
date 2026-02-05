"""Check database contents."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models import Agent, Message, Task, SharedMemory

DATABASE_URL = "sqlite+aiosqlite:///./agent_communication.db"

async def check_database():
    """Check database contents."""
    engine = create_async_engine(DATABASE_URL)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with maker() as s:
        result = await s.execute(select(Agent))
        agents = result.scalars().all()
        print(f'Agents count: {len(agents)}')
        for a in agents:
            print(f'  - {a.name} ({a.status})')
        
        result = await s.execute(select(Message))
        messages = result.scalars().all()
        print(f'\nMessages count: {len(messages)}')
        
        result = await s.execute(select(Task))
        tasks = result.scalars().all()
        print(f'\nTasks count: {len(tasks)}')
        
        result = await s.execute(select(SharedMemory))
        memories = result.scalars().all()
        print(f'\nMemories count: {len(memories)}')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_database())