import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_register_agent(client: AsyncClient, sample_agent_data):
    """Test agent registration"""
    response = await client.post("/api/agents/register", json=sample_agent_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_agent_data["name"]
    assert data["type"] == sample_agent_data["type"]
    assert data["status"] in ["online", "offline"]  # Accept default status
    assert "id" in data
    assert "created_at" in data


@pytest.mark.unit
async def test_register_duplicate_agent(client: AsyncClient, sample_agent_data):
    """Test that duplicate agent names are rejected"""
    # Register first agent
    await client.post("/api/agents/register", json=sample_agent_data)
    
    # Try to register duplicate
    response = await client.post("/api/agents/register", json=sample_agent_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.unit
async def test_list_agents(client: AsyncClient, sample_agent_data):
    """Test listing all agents"""
    # Create multiple agents
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data["name"] = f"test_agent_{i}"
        await client.post("/api/agents/register", json=agent_data)
    
    # List agents
    response = await client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.unit
async def test_list_online_agents(client: AsyncClient, sample_agent_data):
    """Test listing online agents"""
    # Create agents with different statuses
    online_data = sample_agent_data.copy()
    online_data["name"] = "online_agent"
    online_data["status"] = "online"
    await client.post("/api/agents/register", json=online_data)
    
    offline_data = sample_agent_data.copy()
    offline_data["name"] = "offline_agent"
    offline_data["status"] = "offline"
    await client.post("/api/agents/register", json=offline_data)
    
    # List online agents
    response = await client.get("/api/agents/online")
    assert response.status_code == 200
    data = response.json()
    assert all(agent["status"] == "online" for agent in data)


@pytest.mark.unit
async def test_get_agent(client: AsyncClient, sample_agent_data):
    """Test getting a specific agent"""
    # Create agent
    create_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Get agent
    response = await client.get(f"/api/agents/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == sample_agent_data["name"]


@pytest.mark.unit
async def test_get_nonexistent_agent(client: AsyncClient):
    """Test getting a non-existent agent"""
    response = await client.get("/api/agents/nonexistent_id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_update_agent(client: AsyncClient, sample_agent_data):
    """Test updating an agent"""
    # Create agent
    create_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Update agent
    update_data = {"meta_data": {"model": "gpt-4-turbo", "version": "2.0"}}
    response = await client.put(f"/api/agents/{agent_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["meta_data"]["model"] == "gpt-4-turbo"


@pytest.mark.unit
async def test_update_agent_status(client: AsyncClient, sample_agent_data):
    """Test updating agent status"""
    # Create agent
    create_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Update status
    status_data = {"status": "busy"}
    response = await client.put(f"/api/agents/{agent_id}/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "busy"


@pytest.mark.unit
async def test_delete_agent(client: AsyncClient, sample_agent_data):
    """Test deleting an agent"""
    # Create agent
    create_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Delete agent
    response = await client.delete(f"/api/agents/{agent_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(f"/api/agents/{agent_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_nonexistent_agent(client: AsyncClient):
    """Test deleting a non-existent agent"""
    response = await client.delete("/api/agents/nonexistent_id")
    assert response.status_code == 404