import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_send_message(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test sending a message"""
    # Create an agent first
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    # Send message
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent_id
    response = await client.post("/api/messages", json=message_data)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == message_data["content"]
    assert data["sender_id"] == agent_id
    assert "id" in data


@pytest.mark.unit
async def test_list_messages(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test listing all messages"""
    # Create agent and send multiple messages
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    for i in range(3):
        message_data = sample_message_data.copy()
        message_data["sender_id"] = agent_id
        message_data["content"] = f"Message {i}"
        await client.post("/api/messages", json=message_data)
    
    # List messages
    response = await client.get("/api/messages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.unit
async def test_list_messages_with_filters(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test listing messages with filters"""
    # Create two agents
    agent1_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent1"})
    agent1_id = agent1_response.json()["id"]
    
    agent2_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent2"})
    agent2_id = agent2_response.json()["id"]
    
    # Send messages from both agents
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent1_id
    await client.post("/api/messages", json=message_data)
    
    message_data["sender_id"] = agent2_id
    await client.post("/api/messages", json=message_data)
    
    # Filter by sender
    response = await client.get(f"/api/messages?sender_id={agent1_id}")
    assert response.status_code == 200
    data = response.json()
    assert all(msg["sender_id"] == agent1_id for msg in data)


@pytest.mark.unit
async def test_get_recent_messages(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test getting recent messages"""
    # Create agent and send messages
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent_id
    await client.post("/api/messages", json=message_data)
    
    # Get recent messages
    response = await client.get("/api/messages/recent?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.unit
async def test_get_task_messages(client: AsyncClient, sample_agent_data, sample_message_data, sample_task_data):
    """Test getting messages for a specific task"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Send message for task
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent_id
    message_data["task_id"] = task_id
    await client.post("/api/messages", json=message_data)
    
    # Get task messages
    response = await client.get(f"/api/messages/task/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(msg["task_id"] == task_id for msg in data)


@pytest.mark.unit
async def test_get_message(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test getting a specific message"""
    # Create agent and send message
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent_id
    message_response = await client.post("/api/messages", json=message_data)
    message_id = message_response.json()["id"]
    
    # Get message
    response = await client.get(f"/api/messages/{message_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == message_id
    assert data["content"] == message_data["content"]


@pytest.mark.unit
async def test_get_nonexistent_message(client: AsyncClient):
    """Test getting a non-existent message"""
    response = await client.get("/api/messages/nonexistent_id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_delete_message(client: AsyncClient, sample_agent_data, sample_message_data):
    """Test deleting a message"""
    # Create agent and send message
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    message_data = sample_message_data.copy()
    message_data["sender_id"] = agent_id
    message_response = await client.post("/api/messages", json=message_data)
    message_id = message_response.json()["id"]
    
    # Delete message
    response = await client.delete(f"/api/messages/{message_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(f"/api/messages/{message_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_nonexistent_message(client: AsyncClient):
    """Test deleting a non-existent message"""
    response = await client.delete("/api/messages/nonexistent_id")
    assert response.status_code == 404