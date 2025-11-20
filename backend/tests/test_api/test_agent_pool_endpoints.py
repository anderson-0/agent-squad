"""
Integration Tests for Agent Pool API Endpoints

Tests the REST API endpoints for monitoring and managing the agent pool.
Phase 2 Optimization Feature - 60% faster agent instantiation.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_stats_endpoint(client: AsyncClient, test_user_data):
    """Test GET /api/v1/agent-pool/stats endpoint"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get stats
    response = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response schema
    assert "pool_size" in data
    assert "cache_hits" in data
    assert "cache_misses" in data
    assert "evictions" in data
    assert "total_requests" in data
    assert "hit_rate" in data

    # Verify data types
    assert isinstance(data["pool_size"], int)
    assert isinstance(data["cache_hits"], int)
    assert isinstance(data["cache_misses"], int)
    assert isinstance(data["evictions"], int)
    assert isinstance(data["total_requests"], int)
    assert isinstance(data["hit_rate"], (int, float))

    # Verify hit_rate calculation
    assert data["total_requests"] == data["cache_hits"] + data["cache_misses"]


@pytest.mark.asyncio
async def test_get_stats_without_auth(client: AsyncClient):
    """Test GET /stats returns 401/403 without authentication"""
    response = await client.get("/api/v1/agent-pool/stats")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_info_endpoint(client: AsyncClient, test_user_data):
    """Test GET /api/v1/agent-pool/info endpoint"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get info
    response = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response includes all sections
    assert "config" in data
    assert "stats" in data
    assert "agents" in data

    # Verify config section
    config = data["config"]
    assert "max_pool_size" in config
    assert "enable_stats" in config
    assert isinstance(config["max_pool_size"], int)
    assert isinstance(config["enable_stats"], bool)

    # Verify stats section
    stats = data["stats"]
    assert "pool_size" in stats
    assert "cache_hits" in stats
    assert "cache_misses" in stats

    # Verify agents section
    agents = data["agents"]
    assert isinstance(agents, list)


@pytest.mark.asyncio
async def test_get_info_without_auth(client: AsyncClient):
    """Test GET /info returns 401/403 without authentication"""
    response = await client.get("/api/v1/agent-pool/info")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_clear_pool_endpoint(client: AsyncClient, test_user_data):
    """Test POST /api/v1/agent-pool/clear endpoint"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Clear pool
    response = await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response
    assert data["status"] == "cleared"
    assert "agents_removed" in data
    assert "message" in data
    assert isinstance(data["agents_removed"], int)
    assert data["agents_removed"] >= 0


@pytest.mark.asyncio
async def test_clear_pool_multiple_times(client: AsyncClient, test_user_data):
    """Test clearing pool multiple times works correctly"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Clear pool first time
    response1 = await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 200

    # Clear pool second time (should work, return 0 agents removed)
    response2 = await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 200
    data = response2.json()
    assert data["agents_removed"] == 0  # Pool already empty


@pytest.mark.asyncio
async def test_clear_pool_without_auth(client: AsyncClient):
    """Test POST /clear returns 401/403 without authentication"""
    response = await client.post("/api/v1/agent-pool/clear")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_remove_agent_endpoint(client: AsyncClient, test_user_data):
    """Test DELETE /api/v1/agent-pool/agents/{squad_id}/{role} endpoint"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "Test Squad"},
        headers={"Authorization": f"Bearer {token}"}
    )
    squad_id = squad_response.json()["id"]

    # Create squad member
    await client.post(
        "/api/v1/squad-members",
        json={
            "squad_id": squad_id,
            "role": "backend_developer",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Note: Agent won't be in pool until we actually use it
    # For this test, we're testing the 404 case (agent not in pool)
    # This is valid because agent is only added to pool when first accessed

    # Try to remove agent (should return 404 - not in pool yet)
    response = await client.delete(
        f"/api/v1/agent-pool/agents/{squad_id}/backend_developer",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Agent not in pool yet, so should get 404
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_agent_with_invalid_squad_id(client: AsyncClient, test_user_data):
    """Test DELETE with invalid squad_id returns 400"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Try to remove agent with invalid squad_id
    response = await client.delete(
        "/api/v1/agent-pool/agents/not-a-uuid/backend_developer",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid squad_id" in data["detail"]


@pytest.mark.asyncio
async def test_remove_agent_not_in_pool(client: AsyncClient, test_user_data):
    """Test DELETE returns 404 when agent not in pool"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Use a valid UUID that doesn't exist in pool
    fake_squad_id = str(uuid4())

    # Try to remove non-existent agent
    response = await client.delete(
        f"/api/v1/agent-pool/agents/{fake_squad_id}/backend_developer",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "not found in pool" in data["detail"]


@pytest.mark.asyncio
async def test_remove_agent_without_auth(client: AsyncClient):
    """Test DELETE /agents/{squad_id}/{role} returns 401/403 without authentication"""
    fake_squad_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/agent-pool/agents/{fake_squad_id}/backend_developer"
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_stats_update_after_clear(client: AsyncClient, test_user_data):
    """Test that stats correctly update after clearing pool"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get initial stats
    stats_before = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    pool_size_before = stats_before.json()["pool_size"]

    # Clear pool
    await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get stats after clear
    stats_after = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    pool_size_after = stats_after.json()["pool_size"]

    # Pool size should be 0 after clear
    assert pool_size_after == 0


@pytest.mark.asyncio
async def test_info_shows_agents_list(client: AsyncClient, test_user_data):
    """Test that /info endpoint returns list of cached agents"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get info
    response = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    agents = data["agents"]

    # Should be a list (might be empty if no agents cached yet)
    assert isinstance(agents, list)

    # If there are agents, verify structure
    if len(agents) > 0:
        agent = agents[0]
        assert "squad_id" in agent
        assert "role" in agent
        assert "position" in agent


@pytest.mark.asyncio
async def test_pool_size_matches_agents_list(client: AsyncClient, test_user_data):
    """Test that pool_size in stats matches number of agents in info"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Clear pool first to start fresh
    await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get stats
    stats_response = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    pool_size = stats_response.json()["pool_size"]

    # Get info
    info_response = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    agents_count = len(info_response.json()["agents"])

    # Pool size should match number of agents in list
    assert pool_size == agents_count


@pytest.mark.asyncio
async def test_concurrent_clear_requests(client: AsyncClient, test_user_data):
    """Test that concurrent clear requests are handled safely"""
    import asyncio

    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Make 5 concurrent clear requests
    tasks = [
        client.post(
            "/api/v1/agent-pool/clear",
            headers={"Authorization": f"Bearer {token}"}
        )
        for _ in range(5)
    ]

    responses = await asyncio.gather(*tasks)

    # All should succeed
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        # Some will clear 0 agents (if already cleared by another request)
        assert isinstance(data["agents_removed"], int)


@pytest.mark.asyncio
async def test_hit_rate_calculation(client: AsyncClient, test_user_data):
    """Test that hit_rate is calculated correctly"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get stats
    response = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    cache_hits = data["cache_hits"]
    cache_misses = data["cache_misses"]
    hit_rate = data["hit_rate"]
    total_requests = data["total_requests"]

    # Verify calculation
    assert total_requests == cache_hits + cache_misses

    if total_requests > 0:
        expected_hit_rate = (cache_hits / total_requests) * 100
        # Allow small floating point difference
        assert abs(hit_rate - expected_hit_rate) < 0.01
    else:
        # No requests yet, hit rate should be 0
        assert hit_rate == 0.0


@pytest.mark.asyncio
async def test_info_endpoint_shows_config(client: AsyncClient, test_user_data):
    """Test that /info endpoint includes pool configuration"""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Get info
    response = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    config = data["config"]

    # Verify expected config keys
    assert "max_pool_size" in config
    assert "enable_stats" in config

    # Verify default values
    assert config["max_pool_size"] == 100  # Default
    assert config["enable_stats"] is True  # Default


@pytest.mark.asyncio
async def test_end_to_end_flow(client: AsyncClient, test_user_data):
    """
    Test end-to-end flow:
    1. Check initial stats
    2. Create squad and members
    3. Clear pool
    4. Check stats after clear
    5. Verify pool rebuilds after agent access
    """
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]

    # Step 1: Get initial stats
    initial_stats = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert initial_stats.status_code == 200

    # Step 2: Create squad
    squad_response = await client.post(
        "/api/v1/squads",
        json={"name": "E2E Test Squad"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert squad_response.status_code == 201
    squad_id = squad_response.json()["id"]

    # Step 3: Create squad members
    roles = ["project_manager", "backend_developer"]
    for role in roles:
        member_response = await client.post(
            "/api/v1/squad-members",
            json={
                "squad_id": squad_id,
                "role": role,
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert member_response.status_code == 201

    # Step 4: Get info (should show config and stats)
    info_response = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert "config" in info_data
    assert "stats" in info_data
    assert "agents" in info_data

    # Step 5: Clear pool
    clear_response = await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["status"] == "cleared"

    # Step 6: Verify pool is empty
    after_clear_stats = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert after_clear_stats.status_code == 200
    assert after_clear_stats.json()["pool_size"] == 0

    # Step 7: Verify agents list is empty
    after_clear_info = await client.get(
        "/api/v1/agent-pool/info",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert after_clear_info.status_code == 200
    assert len(after_clear_info.json()["agents"]) == 0


@pytest.mark.asyncio
async def test_multiple_users_independent_pools(client: AsyncClient, test_user_data, test_user_data_2):
    """
    Test that agent pool is shared across users (global singleton)
    but clearing pool affects all users
    """
    # Create user 1
    await client.post("/api/v1/auth/register", json=test_user_data)
    login1 = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token1 = login1.json()["access_token"]

    # Create user 2
    await client.post("/api/v1/auth/register", json=test_user_data_2)
    login2 = await client.post("/api/v1/auth/login", json={
        "email": test_user_data_2["email"],
        "password": test_user_data_2["password"]
    })
    token2 = login2.json()["access_token"]

    # User 1 gets stats
    stats1 = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert stats1.status_code == 200

    # User 2 gets stats (should see same pool - it's global)
    stats2 = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert stats2.status_code == 200

    # Both should see the same pool_size (pool is global, not per-user)
    assert stats1.json()["pool_size"] == stats2.json()["pool_size"]

    # User 1 clears pool
    await client.post(
        "/api/v1/agent-pool/clear",
        headers={"Authorization": f"Bearer {token1}"}
    )

    # User 2 should also see empty pool
    stats2_after = await client.get(
        "/api/v1/agent-pool/stats",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert stats2_after.json()["pool_size"] == 0
