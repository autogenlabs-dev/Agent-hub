"""
Example agent demonstrating the Agent SDK usage.
This agent can receive messages, handle tasks, and share memory.
"""

import asyncio
import logging
from agent_sdk import AgentClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Create agent instance
    agent = AgentClient(
        name="research_agent",
        agent_type="llm",
        server_url="http://localhost:8000",
        metadata={"capabilities": ["research", "analysis"]}
    )
    
    # Register message handler
    @agent.on_message
    async def handle_message(message):
        logger.info(f"Received message from {message.sender_id}: {message.content}")
        
        # Send a response
        if message.content.lower().startswith("hello"):
            await agent.send_message(
                content=f"Hello! I'm {agent.name}. How can I help you?",
                recipients=[message.sender_id]
            )
    
    # Register task assignment handler
    @agent.on_task_assigned
    async def handle_task_assigned(task):
        logger.info(f"Task assigned: {task.title}")
        
        # Update status to show we're working
        await agent.update_status("busy")
        
        # Process the task (simulated)
        await asyncio.sleep(2)
        
        # Complete the task
        await agent.complete_task(
            task.id,
            result={"status": "completed", "output": "Task processed successfully"},
            notes="Task completed without issues"
        )
        
        # Update status back to online
        await agent.update_status("online")
    
    # Register memory update handler
    @agent.on_memory_updated
    async def handle_memory_updated(memory):
        logger.info(f"Memory updated: {memory.key}")
    
    # Register agent join handler
    @agent.on_agent_joined
    async def handle_agent_joined(agent_id):
        logger.info(f"Agent joined: {agent_id}")
        
        # Welcome new agents
        agents = await agent.list_agents()
        for a in agents:
            if a.id == agent_id:
                await agent.send_message(
                    content=f"Welcome {a.name}! I'm {agent.name}.",
                    recipients=[agent_id]
                )
                break
    
    # Connect to server
    await agent.connect()
    
    # Update status to online
    await agent.update_status("online")
    
    logger.info("Agent started successfully!")
    
    # Send heartbeat periodically
    async def heartbeat_loop():
        while agent.is_connected:
            await agent.send_heartbeat()
            await asyncio.sleep(30)
    
    asyncio.create_task(heartbeat_loop())
    
    # Keep agent running
    try:
        while agent.is_connected:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.disconnect()


if __name__ == "__main__":
    asyncio.run(main())