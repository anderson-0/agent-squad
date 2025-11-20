"""
Tests for Agent Pool Service

Phase 2 Optimization - Tests for agent instance pooling and caching
"""
import pytest
import asyncio
from uuid import uuid4

from backend.services.agent_pool import (
    AgentPoolService,
    AgentPoolConfig,
    AgentPoolStats,
    get_agent_pool,
    reset_agent_pool,
)
from backend.models.user import User
from backend.models.squad import Squad, SquadMember


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def user(test_db):
    """Create test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hash",
        plan_tier="pro"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def squad(test_db, user):
    """Create test squad"""
    squad = Squad(
        user_id=user.id,
        name="Test Squad",
        status="active",
        config={}
    )
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)
    return squad


@pytest.fixture
async def squad_member(test_db, squad):
    """Create test squad member"""
    member = SquadMember(
        squad_id=squad.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a backend developer",
        config={"temperature": 0.7},
        is_active=True
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member


@pytest.fixture
async def pool():
    """Create fresh agent pool for testing"""
    config = AgentPoolConfig(
        max_pool_size=10,  # Smaller for testing
        enable_stats=True,
        log_cache_hits=False
    )
    pool = AgentPoolService(config)
    yield pool
    # Cleanup
    await pool.clear_pool()


# ============================================================================
# Test Agent Caching
# ============================================================================

@pytest.mark.asyncio
async def test_cache_miss_on_first_request(pool, squad_member):
    """Test cache MISS on first request (agent created)"""
    stats_before = await pool.get_stats()
    assert stats_before.cache_misses == 0

    # First request - cache miss
    agent = await pool.get_or_create_agent(squad_member)

    assert agent is not None
    assert agent.agent_id == squad_member.id
    assert agent.config.role == "backend_developer"

    stats_after = await pool.get_stats()
    assert stats_after.cache_misses == 1
    assert stats_after.cache_hits == 0
    assert stats_after.pool_size == 1


@pytest.mark.asyncio
async def test_cache_hit_on_second_request(pool, squad_member):
    """Test cache HIT on second request (agent reused)"""
    # First request - cache miss
    agent1 = await pool.get_or_create_agent(squad_member)

    # Second request - cache hit
    agent2 = await pool.get_or_create_agent(squad_member)

    # Same agent instance returned
    assert agent1 is agent2
    assert id(agent1) == id(agent2)

    stats = await pool.get_stats()
    assert stats.cache_hits == 1
    assert stats.cache_misses == 1
    assert stats.pool_size == 1


@pytest.mark.asyncio
async def test_correct_key_generation(pool, squad, test_db):
    """Test correct key generation (squad_id, role)"""
    # Create two members with same role, different squads
    member1 = SquadMember(
        squad_id=squad.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="Dev 1",
        config={},
        is_active=True
    )
    test_db.add(member1)
    await test_db.commit()
    await test_db.refresh(member1)

    # Create second squad
    user = User(
        email="test2@example.com",
        name="Test User 2",
        password_hash="hash",
        plan_tier="pro"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad2 = Squad(
        user_id=user.id,
        name="Test Squad 2",
        status="active",
        config={}
    )
    test_db.add(squad2)
    await test_db.commit()
    await test_db.refresh(squad2)

    member2 = SquadMember(
        squad_id=squad2.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="Dev 2",
        config={},
        is_active=True
    )
    test_db.add(member2)
    await test_db.commit()
    await test_db.refresh(member2)

    # Get agents
    agent1 = await pool.get_or_create_agent(member1)
    agent2 = await pool.get_or_create_agent(member2)

    # Different agents (different keys)
    assert agent1 is not agent2
    assert agent1.agent_id == member1.id
    assert agent2.agent_id == member2.id

    stats = await pool.get_stats()
    assert stats.pool_size == 2


@pytest.mark.asyncio
async def test_agent_instance_same_object_not_recreated(pool, squad_member):
    """Test agent instance is same object (not recreated)"""
    agent1 = await pool.get_or_create_agent(squad_member)
    agent2 = await pool.get_or_create_agent(squad_member)
    agent3 = await pool.get_or_create_agent(squad_member)

    # All three are the exact same object
    assert agent1 is agent2 is agent3
    assert id(agent1) == id(agent2) == id(agent3)

    stats = await pool.get_stats()
    assert stats.cache_hits == 2  # Second and third requests
    assert stats.cache_misses == 1  # Only first request
    assert stats.pool_size == 1


# ============================================================================
# Test FIFO Eviction
# ============================================================================

@pytest.mark.asyncio
async def test_pool_respects_max_pool_size(pool, test_db, user):
    """Test pool respects max_pool_size"""
    # Pool max size is 10 (from fixture)
    members = []

    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead", "solution_architect", "devops_engineer",
        "ai_engineer", "designer"
    ]

    # Create 15 squads + members (exceeds max)
    # Each member has unique (squad_id, role) key
    for i in range(15):
        # Create unique squad for each member
        squad = Squad(
            user_id=user.id,
            name=f"Test Squad {i}",
            status="active",
            config={}
        )
        test_db.add(squad)
        await test_db.commit()
        await test_db.refresh(squad)

        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i % len(valid_roles)],  # Cycle through valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        members.append(member)

    await test_db.commit()

    # Add all to pool
    for member in members:
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    stats = await pool.get_stats()
    # Pool size capped at max
    assert stats.pool_size == 10
    assert stats.evictions == 5  # 15 - 10 = 5 evictions


@pytest.mark.asyncio
async def test_oldest_agent_evicted_when_pool_full(pool, test_db, user):
    """Test oldest agent evicted when pool full"""
    members = []

    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead", "solution_architect", "devops_engineer",
        "ai_engineer", "designer"
    ]

    # Create 12 squads + members (exceeds max of 10)
    # Each member has unique (squad_id, role) key
    for i in range(12):
        squad = Squad(
            user_id=user.id,
            name=f"Test Squad {i}",
            status="active",
            config={}
        )
        test_db.add(squad)
        await test_db.commit()
        await test_db.refresh(squad)

        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i % len(valid_roles)],  # Cycle through valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        members.append(member)

    await test_db.commit()

    # Add first 10 (fills pool)
    for member in members[:10]:
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    # Add 11th (evicts oldest = member 0)
    await test_db.refresh(members[10])
    await pool.get_or_create_agent(members[10])

    # Add 12th (evicts second oldest = member 1)
    await test_db.refresh(members[11])
    await pool.get_or_create_agent(members[11])

    # Try to get member 0 again - should be cache miss (evicted)
    # This will cause another eviction since pool is still full
    await test_db.refresh(members[0])
    await pool.get_or_create_agent(members[0])

    stats = await pool.get_stats()
    # Evictions: member 0 (when adding 10), member 1 (when adding 11), member 2 (when re-adding 0)
    assert stats.evictions == 3
    assert stats.cache_misses == 13  # 12 initial + 1 re-add of member 0


@pytest.mark.asyncio
async def test_eviction_counter_increments(pool, test_db, user):
    """Test eviction counter increments"""
    stats_before = await pool.get_stats()
    assert stats_before.evictions == 0

    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead", "solution_architect", "devops_engineer",
        "ai_engineer", "designer"
    ]

    # Fill pool beyond capacity
    for i in range(12):
        squad = Squad(
            user_id=user.id,
            name=f"Test Squad {i}",
            status="active",
            config={}
        )
        test_db.add(squad)
        await test_db.commit()
        await test_db.refresh(squad)

        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i % len(valid_roles)],  # Cycle through valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    stats_after = await pool.get_stats()
    assert stats_after.evictions == 2  # 12 - 10 = 2 evictions


@pytest.mark.asyncio
async def test_evicted_agent_removed_from_pool(pool, test_db, user):
    """Test evicted agent removed from pool"""
    members = []

    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead", "solution_architect", "devops_engineer",
        "ai_engineer", "designer"
    ]

    # Create 12 squads + members
    for i in range(12):
        squad = Squad(
            user_id=user.id,
            name=f"Test Squad {i}",
            status="active",
            config={}
        )
        test_db.add(squad)
        await test_db.commit()
        await test_db.refresh(squad)

        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i % len(valid_roles)],  # Cycle through valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        members.append(member)

    await test_db.commit()

    # Add all to pool (evicts first 2)
    for member in members:
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    # Get pool info
    info = await pool.get_pool_info()

    # Pool should have 10 agents (max size)
    assert len(info["agents"]) == 10

    # First two members should NOT be in pool (evicted)
    # Check by (squad_id, role) pairs
    pool_keys = {(agent["squad_id"], agent["role"]) for agent in info["agents"]}
    assert (str(members[0].squad_id), members[0].role) not in pool_keys
    assert (str(members[1].squad_id), members[1].role) not in pool_keys

    # Last two should be in pool
    assert (str(members[10].squad_id), members[10].role) in pool_keys
    assert (str(members[11].squad_id), members[11].role) in pool_keys

    stats = await pool.get_stats()
    assert stats.pool_size == 10
    assert stats.evictions == 2


# ============================================================================
# Test Statistics Tracking
# ============================================================================

@pytest.mark.asyncio
async def test_cache_hits_counter_increments_on_hit(pool, squad_member):
    """Test cache_hits counter increments on hit"""
    await pool.get_or_create_agent(squad_member)  # Cache miss
    await pool.get_or_create_agent(squad_member)  # Cache hit
    await pool.get_or_create_agent(squad_member)  # Cache hit

    stats = await pool.get_stats()
    assert stats.cache_hits == 2


@pytest.mark.asyncio
async def test_cache_misses_counter_increments_on_miss(pool, squad, test_db):
    """Test cache_misses counter increments on miss"""
    # Valid roles that AgentFactory supports
    valid_roles = ["project_manager", "backend_developer", "frontend_developer"]

    # Create 3 different members with different roles
    for i in range(3):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)  # Each is a cache miss

    stats = await pool.get_stats()
    assert stats.cache_misses == 3


@pytest.mark.asyncio
async def test_evictions_counter_increments_on_eviction(pool, test_db, user):
    """Test evictions counter increments on eviction"""
    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead", "solution_architect", "devops_engineer",
        "ai_engineer", "designer"
    ]

    # Add 12 members (2 evictions)
    for i in range(12):
        squad = Squad(
            user_id=user.id,
            name=f"Test Squad {i}",
            status="active",
            config={}
        )
        test_db.add(squad)
        await test_db.commit()
        await test_db.refresh(squad)

        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i % len(valid_roles)],  # Cycle through valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    stats = await pool.get_stats()
    assert stats.evictions == 2


@pytest.mark.asyncio
async def test_hit_rate_calculation(pool, squad_member):
    """Test hit_rate calculation (hits / total * 100)"""
    # Create pattern: miss, hit, hit, miss, hit
    await pool.get_or_create_agent(squad_member)  # Miss
    await pool.get_or_create_agent(squad_member)  # Hit
    await pool.get_or_create_agent(squad_member)  # Hit

    # Clear and re-add (miss)
    await pool.clear_pool()
    await pool.get_or_create_agent(squad_member)  # Miss
    await pool.get_or_create_agent(squad_member)  # Hit

    stats = await pool.get_stats()
    # Total: 5 requests
    # Hits: 3
    # Misses: 2
    # Hit rate: 3/5 * 100 = 60%
    assert stats.total_requests == 5
    assert stats.cache_hits == 3
    assert stats.cache_misses == 2
    assert stats.hit_rate == 60.0


@pytest.mark.asyncio
async def test_total_requests_calculation(pool, squad_member):
    """Test total_requests (hits + misses)"""
    # 1 miss + 4 hits
    for _ in range(5):
        await pool.get_or_create_agent(squad_member)

    stats = await pool.get_stats()
    assert stats.total_requests == 5
    assert stats.cache_hits == 4
    assert stats.cache_misses == 1


@pytest.mark.asyncio
async def test_stats_to_dict_returns_correct_format(pool, squad_member):
    """Test stats.to_dict() returns correct format"""
    await pool.get_or_create_agent(squad_member)

    stats = await pool.get_stats()
    stats_dict = stats.to_dict()

    # Check all required keys
    assert "pool_size" in stats_dict
    assert "cache_hits" in stats_dict
    assert "cache_misses" in stats_dict
    assert "evictions" in stats_dict
    assert "total_requests" in stats_dict
    assert "hit_rate" in stats_dict
    assert "created_at" in stats_dict
    assert "last_access" in stats_dict

    # Check types
    assert isinstance(stats_dict["pool_size"], int)
    assert isinstance(stats_dict["hit_rate"], float)


# ============================================================================
# Test Pool Management
# ============================================================================

@pytest.mark.asyncio
async def test_clear_pool_removes_all_agents(pool, squad, test_db):
    """Test clear_pool() removes all agents"""
    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead"
    ]

    # Add 5 agents
    for i in range(5):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    stats_before = await pool.get_stats()
    assert stats_before.pool_size == 5

    # Clear pool
    count = await pool.clear_pool()

    assert count == 5
    stats_after = await pool.get_stats()
    assert stats_after.pool_size == 0


@pytest.mark.asyncio
async def test_clear_pool_returns_correct_count(pool, squad, test_db):
    """Test clear_pool() returns correct count"""
    # Valid roles that AgentFactory supports
    valid_roles = ["project_manager", "backend_developer", "frontend_developer"]

    # Add 3 agents
    for i in range(3):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    count = await pool.clear_pool()
    assert count == 3


@pytest.mark.asyncio
async def test_remove_agent_removes_specific_agent(pool, squad_member):
    """Test remove_agent() removes specific agent"""
    await pool.get_or_create_agent(squad_member)

    stats_before = await pool.get_stats()
    assert stats_before.pool_size == 1

    # Remove agent
    removed = await pool.remove_agent(squad_member.squad_id, squad_member.role)

    assert removed is True
    stats_after = await pool.get_stats()
    assert stats_after.pool_size == 0


@pytest.mark.asyncio
async def test_remove_agent_returns_true_when_found(pool, squad_member):
    """Test remove_agent() returns True when found"""
    await pool.get_or_create_agent(squad_member)

    removed = await pool.remove_agent(squad_member.squad_id, squad_member.role)
    assert removed is True


@pytest.mark.asyncio
async def test_remove_agent_returns_false_when_not_found(pool, squad_member):
    """Test remove_agent() returns False when not found"""
    # Don't add agent to pool
    removed = await pool.remove_agent(squad_member.squad_id, "nonexistent_role")
    assert removed is False


@pytest.mark.asyncio
async def test_pool_size_updates_after_operations(pool, squad, test_db):
    """Test pool_size updates after operations"""
    # Valid roles that AgentFactory supports
    valid_roles = ["project_manager", "backend_developer", "frontend_developer"]

    # Initial size
    stats = await pool.get_stats()
    assert stats.pool_size == 0

    # Add 3 agents
    members = []
    for i in range(3):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        members.append(member)

    await test_db.commit()

    for member in members:
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    stats = await pool.get_stats()
    assert stats.pool_size == 3

    # Remove one (backend_developer)
    await pool.remove_agent(squad.id, "backend_developer")
    stats = await pool.get_stats()
    assert stats.pool_size == 2

    # Clear all
    await pool.clear_pool()
    stats = await pool.get_stats()
    assert stats.pool_size == 0


# ============================================================================
# Test Thread Safety
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_get_or_create_agent_calls(pool, squad_member):
    """Test concurrent get_or_create_agent() calls"""
    # Simulate 10 concurrent requests for same agent
    tasks = [
        pool.get_or_create_agent(squad_member)
        for _ in range(10)
    ]

    agents = await asyncio.gather(*tasks)

    # All should be same agent instance
    first_agent = agents[0]
    assert all(agent is first_agent for agent in agents)

    stats = await pool.get_stats()
    # Should have 1 miss (first) and 9 hits (rest)
    assert stats.cache_misses == 1
    assert stats.cache_hits == 9


@pytest.mark.asyncio
async def test_no_duplicate_agent_creation_under_contention(pool, squad_member):
    """Test no duplicate agent creation under contention"""
    # Many concurrent requests
    tasks = [
        pool.get_or_create_agent(squad_member)
        for _ in range(50)
    ]

    agents = await asyncio.gather(*tasks)

    # All should be identical
    assert all(id(agent) == id(agents[0]) for agent in agents)

    # Only one agent created
    stats = await pool.get_stats()
    assert stats.cache_misses == 1
    assert stats.pool_size == 1


@pytest.mark.asyncio
async def test_async_locks_prevent_race_conditions(pool, squad, test_db):
    """Test async locks prevent race conditions"""
    # Valid roles that AgentFactory supports
    valid_roles = [
        "project_manager", "backend_developer", "frontend_developer",
        "tester", "tech_lead"
    ]

    # Create multiple members
    members = []
    for i in range(5):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        members.append(member)

    await test_db.commit()
    for member in members:
        await test_db.refresh(member)

    # Concurrent requests for different agents
    tasks = []
    for member in members:
        # 10 concurrent requests per member
        for _ in range(10):
            tasks.append(pool.get_or_create_agent(member))

    await asyncio.gather(*tasks)

    stats = await pool.get_stats()
    # Should have exactly 5 cache misses (one per unique member)
    assert stats.cache_misses == 5
    # Should have 45 cache hits (50 total - 5 misses)
    assert stats.cache_hits == 45
    assert stats.pool_size == 5


# ============================================================================
# Test Singleton Pattern
# ============================================================================

@pytest.mark.asyncio
async def test_get_agent_pool_returns_same_instance():
    """Test get_agent_pool() returns same instance"""
    pool1 = await get_agent_pool()
    pool2 = await get_agent_pool()

    assert pool1 is pool2
    assert id(pool1) == id(pool2)


@pytest.mark.asyncio
async def test_reset_agent_pool_clears_singleton():
    """Test reset_agent_pool() clears singleton"""
    pool1 = await get_agent_pool()

    # Reset
    reset_agent_pool()

    pool2 = await get_agent_pool()

    # Should be different instance
    assert pool1 is not pool2
    assert id(pool1) != id(pool2)


@pytest.mark.asyncio
async def test_reset_agent_pool_allows_new_instance():
    """Test reset_agent_pool() allows new instance"""
    pool1 = await get_agent_pool()
    original_id = id(pool1)

    reset_agent_pool()

    pool2 = await get_agent_pool()
    new_id = id(pool2)

    assert original_id != new_id


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.mark.asyncio
async def test_custom_max_pool_size_respected():
    """Test custom max_pool_size respected"""
    config = AgentPoolConfig(max_pool_size=5)
    pool = AgentPoolService(config)

    assert pool.config.max_pool_size == 5

    # Cleanup
    await pool.clear_pool()


@pytest.mark.asyncio
async def test_enable_stats_flag_works():
    """Test enable_stats flag works"""
    config = AgentPoolConfig(enable_stats=False)
    pool = AgentPoolService(config)

    assert pool.config.enable_stats is False

    # Cleanup
    await pool.clear_pool()


@pytest.mark.asyncio
async def test_log_cache_hits_flag_works():
    """Test log_cache_hits flag works"""
    config = AgentPoolConfig(log_cache_hits=True)
    pool = AgentPoolService(config)

    assert pool.config.log_cache_hits is True

    # Cleanup
    await pool.clear_pool()


# ============================================================================
# Test Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_empty_pool_stats():
    """Test stats on empty pool"""
    config = AgentPoolConfig()
    pool = AgentPoolService(config)

    stats = await pool.get_stats()

    assert stats.pool_size == 0
    assert stats.cache_hits == 0
    assert stats.cache_misses == 0
    assert stats.evictions == 0
    assert stats.hit_rate == 0.0
    assert stats.total_requests == 0

    # Cleanup
    await pool.clear_pool()


@pytest.mark.asyncio
async def test_clear_empty_pool():
    """Test clearing already empty pool"""
    config = AgentPoolConfig()
    pool = AgentPoolService(config)

    count = await pool.clear_pool()

    assert count == 0

    # Cleanup
    await pool.clear_pool()


@pytest.mark.asyncio
async def test_remove_from_empty_pool():
    """Test removing from empty pool"""
    config = AgentPoolConfig()
    pool = AgentPoolService(config)

    removed = await pool.remove_agent(uuid4(), "some_role")

    assert removed is False

    # Cleanup
    await pool.clear_pool()


@pytest.mark.asyncio
async def test_get_pool_info_comprehensive(pool, squad, test_db):
    """Test get_pool_info() returns comprehensive information"""
    # Valid roles that AgentFactory supports
    valid_roles = ["project_manager", "backend_developer", "frontend_developer"]

    # Add 3 agents
    for i in range(3):
        member = SquadMember(
            squad_id=squad.id,
            role=valid_roles[i],  # Use valid roles
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt=f"Agent {i}",
            config={},
            is_active=True
        )
        test_db.add(member)
        await test_db.commit()
        await test_db.refresh(member)
        await pool.get_or_create_agent(member)

    info = await pool.get_pool_info()

    # Check structure
    assert "config" in info
    assert "stats" in info
    assert "agents" in info

    # Check config
    assert info["config"]["max_pool_size"] == 10
    assert info["config"]["enable_stats"] is True

    # Check agents list
    assert len(info["agents"]) == 3
    assert all("squad_id" in agent for agent in info["agents"])
    assert all("role" in agent for agent in info["agents"])
    assert all("position" in agent for agent in info["agents"])
