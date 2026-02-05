"""Seed database with test data for E2E testing."""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models import Agent, Message, Task, SharedMemory
from app.core.database import Base

# Database URL from environment
DATABASE_URL = "sqlite+aiosqlite:///./agent_communication.db"

async def seed_database():
    """Create test data in database."""
    # Create engine
    engine = create_async_engine(DATABASE_URL)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Check if data already exists
        result = await session.execute(select(Agent).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping...")
            return
        
        print("Seeding database with test data...")
        
        # Create agents
        agents = [
            Agent(
                name="Alpha Agent",
                type="llm",
                status="online",
                last_seen=datetime.now(),
                meta_data={"model": "gpt-4", "version": "1.0"}
            ),
            Agent(
                name="Beta Agent",
                type="worker",
                status="online",
                last_seen=datetime.now() - timedelta(minutes=5),
                meta_data={"capabilities": ["processing", "analysis"]}
            ),
            Agent(
                name="Gamma Agent",
                type="llm",
                status="offline",
                last_seen=datetime.now() - timedelta(hours=2),
                meta_data={"model": "claude-3", "version": "2.0"}
            ),
            Agent(
                name="Delta Agent",
                type="worker",
                status="online",
                last_seen=datetime.now() - timedelta(minutes=15),
                meta_data={"capabilities": ["data_ingestion", "parsing"]}
            ),
            Agent(
                name="Epsilon Agent",
                type="llm",
                status="offline",
                last_seen=datetime.now() - timedelta(days=1),
                meta_data={"model": "gpt-3.5", "version": "1.5"}
            ),
        ]
        
        for agent in agents:
            session.add(agent)
        await session.flush()  # Get IDs
        
        # Create messages
        messages = [
            Message(
                sender_id=agents[0].id,
                content="Hello from Alpha Agent! Starting new task processing.",
                message_type="text",
                created_at=datetime.now() - timedelta(minutes=30),
                meta_data={"priority": "normal"}
            ),
            Message(
                sender_id=agents[1].id,
                content="Task received. Beginning analysis phase.",
                message_type="text",
                created_at=datetime.now() - timedelta(minutes=25),
                meta_data={"priority": "normal"}
            ),
            Message(
                sender_id=agents[3].id,
                content="Data ingestion complete. 500 records processed.",
                message_type="info",
                created_at=datetime.now() - timedelta(minutes=20),
                meta_data={"records_processed": 500}
            ),
            Message(
                sender_id=agents[0].id,
                content="Analysis complete. Results are ready for review.",
                message_type="text",
                created_at=datetime.now() - timedelta(minutes=15),
                meta_data={"priority": "high"}
            ),
            Message(
                sender_id=agents[1].id,
                content="Reviewing results. Quality checks passed.",
                message_type="text",
                created_at=datetime.now() - timedelta(minutes=10),
                meta_data={"quality": "passed"}
            ),
        ]
        
        for message in messages:
            session.add(message)
        await session.flush()
        
        # Create tasks
        tasks = [
            Task(
                creator_id=agents[0].id,
                title="Process daily data batch",
                description="Process and analyze daily data batch from ingestion pipeline",
                status="completed",
                priority=2,
                created_at=datetime.now() - timedelta(hours=2),
                due_date=datetime.now() - timedelta(hours=1),
                completed_at=datetime.now() - timedelta(minutes=30),
                requirements={"skills": ["processing", "analysis"], "data_size": "large"}
            ),
            Task(
                creator_id=agents[1].id,
                title="Generate weekly report",
                description="Generate comprehensive weekly report from processed data",
                status="in_progress",
                priority=3,
                created_at=datetime.now() - timedelta(hours=1),
                due_date=datetime.now() + timedelta(hours=2),
                requirements={"format": "pdf", "sections": ["summary", "metrics", "trends"]}
            ),
            Task(
                creator_id=agents[0].id,
                title="Optimize database queries",
                description="Identify and optimize slow database queries",
                status="pending",
                priority=1,
                created_at=datetime.now() - timedelta(minutes=30),
                due_date=datetime.now() + timedelta(days=1),
                requirements={"target_db": "postgres", "max_latency_ms": 100}
            ),
            Task(
                creator_id=agents[3].id,
                title="Implement caching layer",
                description="Add Redis caching for frequently accessed data",
                status="pending",
                priority=2,
                created_at=datetime.now() - timedelta(minutes=15),
                due_date=datetime.now() + timedelta(days=2),
                requirements={"cache_type": "redis", "ttl_seconds": 3600}
            ),
        ]
        
        for task in tasks:
            session.add(task)
        await session.flush()
        
        # Create memory entries
        memories = [
            SharedMemory(
                key="system_config",
                value={"max_workers": 10, "timeout": 300, "retry_count": 3},
                created_by=agents[0].id,
                created_at=datetime.now() - timedelta(hours=3),
                updated_at=datetime.now() - timedelta(hours=1),
                access_control={"read": ["all"], "write": ["admin"]}
            ),
            SharedMemory(
                key="user_preferences",
                value={"theme": "dark", "language": "en", "notifications": True},
                created_by=agents[1].id,
                created_at=datetime.now() - timedelta(hours=2),
                updated_at=datetime.now() - timedelta(minutes=30),
                access_control={"read": ["all"], "write": ["admin", "user"]}
            ),
            SharedMemory(
                key="api_keys",
                value={"openai": "sk-***", "anthropic": "sk-ant-***"},
                created_by=agents[0].id,
                created_at=datetime.now() - timedelta(hours=4),
                updated_at=datetime.now() - timedelta(hours=2),
                access_control={"read": ["admin"], "write": ["admin"]}
            ),
            SharedMemory(
                key="task_queue",
                value={"pending": 5, "in_progress": 2, "completed": 150},
                created_by=agents[3].id,
                created_at=datetime.now() - timedelta(minutes=45),
                updated_at=datetime.now() - timedelta(minutes=10),
                access_control={"read": ["all"], "write": ["all"]}
            ),
        ]
        
        for memory in memories:
            session.add(memory)
        
        # Commit all changes
        await session.commit()
        
        print(f"[OK] Created {len(agents)} agents")
        print(f"[OK] Created {len(messages)} messages")
        print(f"[OK] Created {len(tasks)} tasks")
        print(f"[OK] Created {len(memories)} memory entries")
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())