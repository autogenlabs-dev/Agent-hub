from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time agent communication"""
    
    def __init__(self):
        # Store active connections: {agent_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata: {agent_id: metadata}
        self.connection_metadata: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str, metadata: Optional[dict] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.connection_metadata[agent_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        logger.info(f"Agent {agent_id} connected")
    
    def disconnect(self, agent_id: str):
        """Remove a WebSocket connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            del self.connection_metadata[agent_id]
            logger.info(f"Agent {agent_id} disconnected")
    
    async def send_personal_message(self, message: dict, agent_id: str):
        """Send a message to a specific agent"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to agent {agent_id}: {e}")
                self.disconnect(agent_id)
                return False
        return False
    
    async def broadcast(self, message: dict, exclude_agent_id: Optional[str] = None):
        """Broadcast a message to all connected agents"""
        disconnected_agents = []
        # Copy items to avoid "dictionary changed size during iteration"
        connections_snapshot = list(self.active_connections.items())
        for agent_id, connection in connections_snapshot:
            if exclude_agent_id and agent_id == exclude_agent_id:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to agent {agent_id}: {e}")
                disconnected_agents.append(agent_id)

        # Clean up disconnected agents
        for agent_id in disconnected_agents:
            self.disconnect(agent_id)
    
    async def send_to_agents(self, message: dict, agent_ids: list):
        """Send a message to specific agents"""
        for agent_id in agent_ids:
            await self.send_personal_message(message, agent_id)
    
    def get_connected_agents(self) -> Set[str]:
        """Get set of all connected agent IDs"""
        return set(self.active_connections.keys())
    
    def is_connected(self, agent_id: str) -> bool:
        """Check if an agent is connected"""
        return agent_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_agent_metadata(self, agent_id: str) -> Optional[dict]:
        """Get metadata for a connected agent"""
        return self.connection_metadata.get(agent_id)


# Global connection manager instance
manager = ConnectionManager()