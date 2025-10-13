"""
Tests for Squad API Endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_squad(client: AsyncClient, test_user_data):
    """Test creating a squad via API"""
    # Register user
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201

    # Login
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create squad
    squad_data = {
        "name": "Test Squad",
        "description": "A test squad for agents"
    }

    response = await client.post(
        "/api/v1/squads",
        json=squad_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Squad"
    assert data["description"] == "A test squad for agents"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_squads(client: AsyncClient, test_user_data):
    """Test listing user's squads"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create multiple squads
    for i in range(3):
        await client.post(
            "/api/v1/squads",
            json={"name": f"Squad {i+1}"},
            headers={"Authorization": f"Bearer {token}"}
        )

    # List squads
    response = await client.get(
        "/api/v1/squads",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(squad["status"] == "active" for squad in data)


@pytest.mark.asyncio
async def test_get_squad(client: AsyncClient, test_user_data):
    """Test getting a specific squad"""
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create squad
    create_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers={"Authorization": f"Bearer {token}"}
    )
    squad_id = create_response.json()["id"]

    # Get squad
    response = await client.get(
        f"/api/v1/squads/{squad_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == squad_id
    assert data["name"] == "Test Squad"


@pytest.mark.asyncio
async def test_update_squad(client: AsyncClient, test_user_data):
    """Test updating a squad"""
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create squad
    create_response = await client.post(
        "/api/v1/squads",
        json={"name": "Original Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    squad_id = create_response.json()["id"]

    # Update squad
    response = await client.put(
        f"/api/v1/squads/{squad_id}",
        json={
            "name": "Updated Name",
            "description": "Updated description"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_squad(client: AsyncClient, test_user_data):
    """Test deleting a squad"""
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create squad
    create_response = await client.post(
        "/api/v1/squads",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"}
    )
    squad_id = create_response.json()["id"]

    # Delete squad
    response = await client.delete(
        f"/api/v1/squads/{squad_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/squads/{squad_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_squad_cost(client: AsyncClient, test_user_data):
    """Test getting squad cost estimate"""
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create squad
    create_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers={"Authorization": f"Bearer {token}"}
    )
    squad_id = create_response.json()["id"]

    # Add squad member
    await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "project_manager",
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get cost
    response = await client.get(
        f"/api/v1/squads/{squad_id}/cost",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_monthly_cost" in data
    assert "cost_by_model" in data
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_squad_access_control(client: AsyncClient, test_user_data, test_user_data_2):
    """Test that users can only access their own squads"""
    # Create user 1
    await client.post("/api/v1/auth/register", json=test_user_data)
    login1 = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token1 = login1.json()["access_token"]

    # Create squad for user 1
    create_response = await client.post(
        "/api/v1/squads",
        json={"name": "User 1 Squad"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    squad_id = create_response.json()["id"]

    # Create user 2
    await client.post("/api/v1/auth/register", json=test_user_data_2)
    login2 = await client.post("/api/v1/auth/login", json={
        "email": test_user_data_2["email"],
        "password": test_user_data_2["password"]
    })
    token2 = login2.json()["access_token"]

    # User 2 tries to access user 1's squad
    response = await client.get(
        f"/api/v1/squads/{squad_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_squad_without_auth(client: AsyncClient):
    """Test that squad endpoints require authentication"""
    response = await client.get("/api/v1/squads")
    # FastAPI dependency system returns 403 when token is missing
    assert response.status_code in [401, 403]

    response = await client.post("/api/v1/squads", json={"name": "Test"})
    assert response.status_code in [401, 403]
