"""
Tests for Squad Members API Endpoints
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from backend.models.user import User
from backend.models.squad import Squad
from backend.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_create_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test creating a squad member via API"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad", "description": "Test"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    # Create squad member
    response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "backend_developer",
            "specialization": "Python/FastAPI",
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        },
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "backend_developer"
    assert data["specialization"] == "Python/FastAPI"
    assert data["llm_provider"] == "openai"
    assert data["llm_model"] == "gpt-4"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_squad_member_invalid_role(client: AsyncClient, test_user_data, test_db):
    """Test creating squad member with invalid role"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    # Try to create member with invalid role
    response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "invalid_role"
        },
        headers=headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_squad_members(client: AsyncClient, test_user_data, test_db):
    """Test listing squad members"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    # Create multiple members
    await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "project_manager"},
        headers=headers
    )
    await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )

    # List members
    response = await client.get(
        f"/api/v1/squad-members?squad_id={squad_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    roles = {m["role"] for m in data}
    assert "project_manager" in roles
    assert "backend_developer" in roles


@pytest.mark.asyncio
async def test_list_squad_members_active_only(client: AsyncClient, test_user_data, test_db):
    """Test listing only active squad members"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    # Create members
    member1_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "project_manager"},
        headers=headers
    )
    member2_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )

    member2_id = member2_response.json()["id"]

    # Deactivate one member
    await client.patch(
        f"/api/v1/squad-members/{member2_id}/deactivate",
        headers=headers
    )

    # List active members only
    response = await client.get(
        f"/api/v1/squad-members?squad_id={squad_id}&active_only=true",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "project_manager"


@pytest.mark.asyncio
async def test_get_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test getting a specific squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "project_manager"},
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Get member
    response = await client.get(
        f"/api/v1/squad-members/{member_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == member_id
    assert data["role"] == "project_manager"


@pytest.mark.asyncio
async def test_get_squad_member_not_found(client: AsyncClient, test_user_data, test_db):
    """Test getting non-existent squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_id = str(uuid4())

    response = await client.get(
        f"/api/v1/squad-members/{invalid_id}",
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_squad_member_with_config(client: AsyncClient, test_user_data, test_db):
    """Test getting squad member with config"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "project_manager",
            "config": {"temperature": 0.7}
        },
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Get member with config
    response = await client.get(
        f"/api/v1/squad-members/{member_id}/config",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert data["config"]["temperature"] == 0.7


@pytest.mark.asyncio
async def test_get_squad_composition(client: AsyncClient, test_user_data, test_db):
    """Test getting squad composition"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and members
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "project_manager", "llm_provider": "openai", "llm_model": "gpt-4"},
        headers=headers
    )
    await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer", "llm_provider": "openai", "llm_model": "gpt-4"},
        headers=headers
    )
    await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "qa_tester", "llm_provider": "anthropic", "llm_model": "claude-3-opus"},
        headers=headers
    )

    # Get composition
    response = await client.get(
        f"/api/v1/squad-members/squad/{squad_id}/composition",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_members"] == 3
    assert data["active_members"] == 3
    assert data["roles"]["project_manager"] == 1
    assert data["roles"]["backend_developer"] == 1
    assert data["roles"]["qa_tester"] == 1
    assert data["llm_providers"]["openai"] == 2
    assert data["llm_providers"]["anthropic"] == 1


@pytest.mark.asyncio
async def test_update_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test updating a squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Update member
    response = await client.put(
        f"/api/v1/squad-members/{member_id}",
        json={
            "specialization": "Python/Django",
            "llm_model": "gpt-4-turbo"
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["specialization"] == "Python/Django"
    assert data["llm_model"] == "gpt-4-turbo"


@pytest.mark.asyncio
async def test_update_squad_member_not_found(client: AsyncClient, test_user_data, test_db):
    """Test updating non-existent squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_id = str(uuid4())

    response = await client.put(
        f"/api/v1/squad-members/{invalid_id}",
        json={"specialization": "Python"},
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test deactivating a squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Deactivate
    response = await client.patch(
        f"/api/v1/squad-members/{member_id}/deactivate",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_reactivate_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test reactivating a squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Deactivate then reactivate
    await client.patch(
        f"/api/v1/squad-members/{member_id}/deactivate",
        headers=headers
    )

    response = await client.patch(
        f"/api/v1/squad-members/{member_id}/reactivate",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_delete_squad_member(client: AsyncClient, test_user_data, test_db):
    """Test deleting a squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create squad and member
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    create_response = await client.post(
        "/api/v1/squad-members",
        json={"squad_id": squad_id, "role": "backend_developer"},
        headers=headers
    )
    member_id = create_response.json()["id"]

    # Delete
    response = await client.delete(
        f"/api/v1/squad-members/{member_id}",
        headers=headers
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/squad-members/{member_id}",
        headers=headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_squad_member_not_found(client: AsyncClient, test_user_data, test_db):
    """Test deleting non-existent squad member"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_id = str(uuid4())

    response = await client.delete(
        f"/api/v1/squad-members/{invalid_id}",
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_squad_member_without_auth(client: AsyncClient):
    """Test that squad member endpoints require authentication"""
    response = await client.get("/api/v1/squad-members")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_squad_member_squad_not_found(client: AsyncClient, test_user_data):
    """Test creating squad member with non-existent squad"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_squad_id = str(uuid4())

    response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": invalid_squad_id,
            "role": "backend_developer"
        },
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_squad_members_squad_not_found(client: AsyncClient, test_user_data):
    """Test listing members of non-existent squad"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_squad_id = str(uuid4())

    response = await client.get(
        f"/api/v1/squad-members?squad_id={invalid_squad_id}",
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_squad_composition_squad_not_found(client: AsyncClient, test_user_data):
    """Test getting composition of non-existent squad"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_squad_id = str(uuid4())

    response = await client.get(
        f"/api/v1/squad-members/squad/{invalid_squad_id}/composition",
        headers=headers
    )

    assert response.status_code == 404
