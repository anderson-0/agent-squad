"""
Full Workflow Integration Tests

Tests complete workflows from squad creation to task execution.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_squad_setup_workflow(client: AsyncClient, test_user_data):
    """
    Test complete workflow: Register → Create Squad → Add Agents → Ready
    """
    # Step 1: Register user
    register_response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Create Squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={
            "name": "Development Squad",
            "description": "Full-stack development team"
        },
        headers=headers
    )
    assert squad_response.status_code == 201
    squad = squad_response.json()
    squad_id = squad["id"]

    # Step 4: Add PM
    pm_response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "project_manager",
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        },
        headers=headers
    )
    assert pm_response.status_code == 201
    pm = pm_response.json()

    # Step 5: Add Backend Developer
    dev_response = await client.post(
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
    assert dev_response.status_code == 201

    # Step 6: Add QA Tester
    qa_response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "qa_tester",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo"
        },
        headers=headers
    )
    assert qa_response.status_code == 201

    # Step 7: Get Squad with All Agents
    squad_details_response = await client.get(
        f"/api/v1/squads/{squad_id}/details",
        headers=headers
    )
    assert squad_details_response.status_code == 200
    squad_details = squad_details_response.json()

    # Verify squad has all 3 members
    assert "members" in squad_details
    assert len(squad_details["members"]) == 3
    assert squad_details["member_count"] == 3
    assert squad_details["active_member_count"] == 3

    # Verify roles
    roles = {member["role"] for member in squad_details["members"]}
    assert "project_manager" in roles
    assert "backend_developer" in roles
    assert "qa_tester" in roles

    # Step 8: Get Squad Composition
    composition_response = await client.get(
        f"/api/v1/squad-members/squad/{squad_id}/composition",
        headers=headers
    )
    assert composition_response.status_code == 200
    composition = composition_response.json()

    assert composition["total_members"] == 3
    assert composition["active_members"] == 3
    assert "roles" in composition
    assert "llm_providers" in composition

    # Step 9: Get Cost Estimate
    cost_response = await client.get(
        f"/api/v1/squads/{squad_id}/cost",
        headers=headers
    )
    assert cost_response.status_code == 200
    cost = cost_response.json()

    assert cost["member_count"] == 3
    assert cost["total_monthly_cost"] > 0
    assert "cost_by_model" in cost


@pytest.mark.asyncio
async def test_squad_member_lifecycle(client: AsyncClient, test_user_data):
    """
    Test squad member lifecycle: Create → Update → Deactivate → Reactivate → Delete
    """
    # Setup: Register, login, create squad
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers=headers
    )
    squad_id = squad_response.json()["id"]

    # Step 1: Create Member
    create_response = await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "backend_developer",
            "specialization": "Python",
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        },
        headers=headers
    )
    assert create_response.status_code == 201
    member = create_response.json()
    member_id = member["id"]

    assert member["role"] == "backend_developer"
    assert member["specialization"] == "Python"
    assert member["is_active"] is True

    # Step 2: Update Member
    update_response = await client.put(
        f"/api/v1/squad-members/{member_id}",
        json={
            "specialization": "Python/FastAPI/PostgreSQL",
            "llm_model": "gpt-4-turbo"
        },
        headers=headers
    )
    assert update_response.status_code == 200
    updated = update_response.json()

    assert updated["specialization"] == "Python/FastAPI/PostgreSQL"
    assert updated["llm_model"] == "gpt-4-turbo"

    # Step 3: Deactivate Member
    deactivate_response = await client.patch(
        f"/api/v1/squad-members/{member_id}/deactivate",
        headers=headers
    )
    assert deactivate_response.status_code == 200
    deactivated = deactivate_response.json()

    assert deactivated["is_active"] is False

    # Step 4: Reactivate Member
    reactivate_response = await client.patch(
        f"/api/v1/squad-members/{member_id}/reactivate",
        headers=headers
    )
    assert reactivate_response.status_code == 200
    reactivated = reactivate_response.json()

    assert reactivated["is_active"] is True

    # Step 5: Delete Member
    delete_response = await client.delete(
        f"/api/v1/squad-members/{member_id}",
        headers=headers
    )
    assert delete_response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/squad-members/{member_id}",
        headers=headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_multi_squad_management(client: AsyncClient, test_user_data):
    """
    Test managing multiple squads with different purposes
    """
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple squads
    squads_data = [
        {"name": "Backend Team", "description": "API development"},
        {"name": "Frontend Team", "description": "UI development"},
        {"name": "QA Team", "description": "Testing and quality"},
    ]

    squad_ids = []
    for squad_data in squads_data:
        response = await client.post(
            "/api/v1/squads",
            json=squad_data,
            headers=headers
        )
        assert response.status_code == 201
        squad_ids.append(response.json()["id"])

    # Add specific members to each squad
    # Backend Team: PM + 2 Backend Devs
    for role in ["project_manager", "backend_developer", "backend_developer"]:
        await client.post(
            "/api/v1/squad-members",
            json={
                "squad_id": squad_ids[0],
                "role": role,
                "llm_provider": "openai",
                "llm_model": "gpt-4"
            },
            headers=headers
        )

    # Frontend Team: PM + 2 Frontend Devs
    for role in ["project_manager", "frontend_developer", "frontend_developer"]:
        await client.post(
            "/api/v1/squad-members",
            json={
                "squad_id": squad_ids[1],
                "role": role,
                "llm_provider": "openai",
                "llm_model": "gpt-4"
            },
            headers=headers
        )

    # QA Team: PM + QA Testers
    for role in ["project_manager", "qa_tester", "qa_tester"]:
        await client.post(
            "/api/v1/squad-members",
            json={
                "squad_id": squad_ids[2],
                "role": role,
                "llm_provider": "openai",
                "llm_model": "gpt-3.5-turbo"
            },
            headers=headers
        )

    # List all squads
    list_response = await client.get("/api/v1/squads", headers=headers)
    assert list_response.status_code == 200
    all_squads = list_response.json()

    assert len(all_squads) == 3

    # Verify each squad has the right number of members
    for i, squad_id in enumerate(squad_ids):
        details_response = await client.get(
            f"/api/v1/squads/{squad_id}/details",
            headers=headers
        )
        details = details_response.json()
        assert details["member_count"] == 3
        assert details["squad"]["name"] == squads_data[i]["name"]


@pytest.mark.asyncio
async def test_squad_filtering_and_status(client: AsyncClient, test_user_data):
    """
    Test squad filtering by status and organization
    """
    # Setup
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple squads
    squad1_response = await client.post(
        "/api/v1/squads",
        json={"name": "Active Squad 1"},
        headers=headers
    )
    squad1_id = squad1_response.json()["id"]

    squad2_response = await client.post(
        "/api/v1/squads",
        json={"name": "Active Squad 2"},
        headers=headers
    )
    squad2_id = squad2_response.json()["id"]

    squad3_response = await client.post(
        "/api/v1/squads",
        json={"name": "To Deactivate"},
        headers=headers
    )
    squad3_id = squad3_response.json()["id"]

    # Deactivate one squad
    await client.patch(
        f"/api/v1/squads/{squad3_id}/status?new_status=paused",
        headers=headers
    )

    # List all squads
    all_response = await client.get("/api/v1/squads", headers=headers)
    assert len(all_response.json()) == 3

    # Filter by active status
    active_response = await client.get(
        "/api/v1/squads?status_filter=active",
        headers=headers
    )
    active_squads = active_response.json()
    assert len(active_squads) == 2

    # Filter by paused status
    paused_response = await client.get(
        "/api/v1/squads?status_filter=paused",
        headers=headers
    )
    paused_squads = paused_response.json()
    assert len(paused_squads) == 1
    assert paused_squads[0]["status"] == "paused"
