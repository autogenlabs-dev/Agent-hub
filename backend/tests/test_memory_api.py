import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_set_memory(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test setting shared memory"""
    # Create an agent first
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    # Set memory
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    response = await client.post("/api/memory", json=memory_data)
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == memory_data["key"]
    assert data["created_by"] == agent_id
    assert "id" in data


@pytest.mark.unit
async def test_set_duplicate_memory(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test that duplicate memory keys are rejected"""
    # Create agent
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    # Set memory
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    await client.post("/api/memory", json=memory_data)
    
    # Try to set duplicate
    response = await client.post("/api/memory", json=memory_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.unit
async def test_list_memories(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test listing all memories"""
    # Create agent and multiple memories
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    for i in range(3):
        memory_data = sample_memory_data.copy()
        memory_data["created_by"] = agent_id
        memory_data["key"] = f"test_key_{i}"
        await client.post("/api/memory", json=memory_data)
    
    # List memories
    response = await client.get("/api/memory")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.unit
async def test_list_memories_with_filters(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test listing memories with filters"""
    # Create two agents
    agent1_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent1"})
    agent1_id = agent1_response.json()["id"]
    
    agent2_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent2"})
    agent2_id = agent2_response.json()["id"]
    
    # Create memories from both agents
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent1_id
    memory_data["key"] = "key1"
    await client.post("/api/memory", json=memory_data)
    
    memory_data["created_by"] = agent2_id
    memory_data["key"] = "key2"
    await client.post("/api/memory", json=memory_data)
    
    # Filter by creator
    response = await client.get(f"/api/memory?created_by={agent1_id}")
    assert response.status_code == 200
    data = response.json()
    assert all(mem["created_by"] == agent1_id for mem in data)


@pytest.mark.unit
async def test_get_memory_by_key(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test getting memory by key"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    await client.post("/api/memory", json=memory_data)
    
    # Get memory by key
    response = await client.get(f"/api/memory/key/{memory_data['key']}")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == memory_data["key"]
    assert data["value"] == memory_data["value"]


@pytest.mark.unit
async def test_get_memory(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test getting memory by ID"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    memory_response = await client.post("/api/memory", json=memory_data)
    memory_id = memory_response.json()["id"]
    
    # Get memory by ID
    response = await client.get(f"/api/memory/{memory_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memory_id
    assert data["key"] == memory_data["key"]


@pytest.mark.unit
async def test_get_nonexistent_memory(client: AsyncClient):
    """Test getting a non-existent memory"""
    response = await client.get("/api/memory/nonexistent_key")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_update_memory_by_key(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test updating memory by key"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    await client.post("/api/memory", json=memory_data)
    
    # Update memory
    update_data = {"value": {"data": "updated_value"}}
    response = await client.put(f"/api/memory/key/{memory_data['key']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["value"]["data"] == "updated_value"


@pytest.mark.unit
async def test_update_memory(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test updating memory by ID"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    memory_response = await client.post("/api/memory", json=memory_data)
    memory_id = memory_response.json()["id"]
    
    # Update memory
    update_data = {"value": {"data": "updated_value"}}
    response = await client.put(f"/api/memory/{memory_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["value"]["data"] == "updated_value"


@pytest.mark.unit
async def test_delete_memory_by_key(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test deleting memory by key"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    await client.post("/api/memory", json=memory_data)
    
    # Delete memory
    response = await client.delete(f"/api/memory/key/{memory_data['key']}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(f"/api/memory/key/{memory_data['key']}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_memory(client: AsyncClient, sample_agent_data, sample_memory_data):
    """Test deleting memory by ID"""
    # Create agent and set memory
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    memory_data = sample_memory_data.copy()
    memory_data["created_by"] = agent_id
    memory_response = await client.post("/api/memory", json=memory_data)
    memory_id = memory_response.json()["id"]
    
    # Delete memory
    response = await client.delete(f"/api/memory/{memory_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(f"/api/memory/{memory_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_delete_nonexistent_memory(client: AsyncClient):
    """Test deleting a non-existent memory"""
    response = await client.delete("/api/memory/nonexistent_key")
    assert response.status_code == 404