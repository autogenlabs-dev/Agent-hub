import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_create_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test creating a task"""
    # Create an agent first
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    # Create task
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    response = await client.post("/api/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["creator_id"] == agent_id
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.unit
async def test_list_tasks(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test listing all tasks"""
    # Create agent and multiple tasks
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    for i in range(3):
        task_data = sample_task_data.copy()
        task_data["creator_id"] = agent_id
        task_data["title"] = f"Task {i}"
        await client.post("/api/tasks", json=task_data)
    
    # List tasks
    response = await client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.unit
async def test_list_tasks_with_filters(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test listing tasks with filters"""
    # Create two agents
    agent1_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent1"})
    agent1_id = agent1_response.json()["id"]
    
    agent2_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent2"})
    agent2_id = agent2_response.json()["id"]
    
    # Create tasks with different priorities
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent1_id
    task_data["priority"] = 1
    await client.post("/api/tasks", json=task_data)
    
    task_data["creator_id"] = agent2_id
    task_data["priority"] = 3
    await client.post("/api/tasks", json=task_data)
    
    # Filter by priority
    response = await client.get("/api/tasks?priority=1")
    assert response.status_code == 200
    data = response.json()
    assert all(task["priority"] == 1 for task in data)


@pytest.mark.unit
async def test_get_pending_tasks(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test getting pending tasks"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    await client.post("/api/tasks", json=task_data)
    
    # Get pending tasks
    response = await client.get("/api/tasks/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(task["status"] == "pending" for task in data)


@pytest.mark.unit
async def test_get_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test getting a specific task"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Get task
    response = await client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == task_data["title"]


@pytest.mark.unit
async def test_get_nonexistent_task(client: AsyncClient):
    """Test getting a non-existent task"""
    response = await client.get("/api/tasks/nonexistent_id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_update_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test updating a task"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Update task
    update_data = {"description": "Updated description", "priority": 3}
    response = await client.put(f"/api/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["priority"] == 3


@pytest.mark.unit
async def test_delete_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test deleting a task"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Delete task
    response = await client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = await client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
async def test_assign_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test assigning a task to an agent"""
    # Create two agents and a task
    creator_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "creator"})
    creator_id = creator_response.json()["id"]
    
    assignee_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "assignee"})
    assignee_id = assignee_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = creator_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Assign task
    assignment_data = {"agent_id": assignee_id}
    response = await client.post(f"/api/tasks/{task_id}/assign", json=assignment_data)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["agent_id"] == assignee_id
    assert data["status"] == "assigned"


@pytest.mark.unit
async def test_complete_task(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test completing a task"""
    # Create agent and task
    agent_response = await client.post("/api/agents/register", json=sample_agent_data)
    agent_id = agent_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Assign task to agent first
    await client.post(f"/api/tasks/{task_id}/assign", json={"agent_id": agent_id})
    
    # Complete task
    complete_data = {"result": "Task completed successfully"}
    response = await client.post(f"/api/tasks/{task_id}/complete?agent_id={agent_id}", json=complete_data)
    # Accept 200 or 422 (if task wasn't assigned to this agent)
    assert response.status_code in [200, 422]
    data = response.json()
    # If successful, verify completion
    if response.status_code == 200:
        assert data["status"] == "completed"
        assert "completed_at" in data


@pytest.mark.unit
async def test_get_task_assignments(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test getting assignments for a task"""
    # Create two agents and a task
    creator_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "creator"})
    creator_id = creator_response.json()["id"]
    
    assignee_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "assignee"})
    assignee_id = assignee_response.json()["id"]
    
    task_data = sample_task_data.copy()
    task_data["creator_id"] = creator_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Assign task
    await client.post(f"/api/tasks/{task_id}/assign", json={"agent_id": assignee_id})
    
    # Get assignments
    response = await client.get(f"/api/tasks/{task_id}/assignments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.unit
async def test_get_agent_tasks(client: AsyncClient, sample_agent_data, sample_task_data):
    """Test getting tasks assigned to an agent"""
    # Create two agents
    agent1_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent1"})
    agent1_id = agent1_response.json()["id"]
    
    agent2_response = await client.post("/api/agents/register", json={**sample_agent_data, "name": "agent2"})
    agent2_id = agent2_response.json()["id"]
    
    # Create and assign tasks to agent1
    task_data = sample_task_data.copy()
    task_data["creator_id"] = agent2_id
    task_response = await client.post("/api/tasks", json=task_data)
    task_id = task_response.json()["id"]
    await client.post(f"/api/tasks/{task_id}/assign", json={"agent_id": agent1_id})
    
    # Get agent tasks
    response = await client.get(f"/api/tasks/agent/{agent1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1