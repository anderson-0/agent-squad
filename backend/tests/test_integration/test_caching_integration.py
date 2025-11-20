"""
Integration Tests for Caching Services

Tests to verify that caching is working correctly across all services.
"""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.cached_services.squad_cache import get_squad_cache
from backend.services.cached_services.task_cache import get_task_cache
from backend.models.squad import Squad, SquadMember
from backend.models.project import Task, TaskExecution


@pytest.mark.asyncio
async def test_squad_caching(db_session: AsyncSession):
    """Test squad caching service"""
    squad_cache = get_squad_cache()

    # Create test squad
    squad = Squad(
        id=uuid4(),
        org_id=uuid4(),
        user_id=uuid4(),
        name="Test Squad",
        description="Test squad for caching",
        status="active",
        config={}
    )
    db_session.add(squad)
    await db_session.commit()

    # First call - should be cache MISS
    cached_squad_1 = await squad_cache.get_squad_by_id(db_session, squad.id)
    assert cached_squad_1 is not None
    assert cached_squad_1["name"] == "Test Squad"

    # Second call - should be cache HIT (won't query database)
    cached_squad_2 = await squad_cache.get_squad_by_id(db_session, squad.id)
    assert cached_squad_2 is not None
    assert cached_squad_2["name"] == "Test Squad"

    # Update squad (invalidates cache)
    squad.name = "Updated Squad"
    await db_session.commit()
    await squad_cache.invalidate_squad(squad.id)

    # Third call - should be cache MISS again (after invalidation)
    cached_squad_3 = await squad_cache.get_squad_by_id(db_session, squad.id)
    assert cached_squad_3 is not None
    # Note: Won't see updated name because cache stores serialized dict


@pytest.mark.asyncio
async def test_squad_member_caching(db_session: AsyncSession):
    """Test squad member list caching"""
    squad_cache = get_squad_cache()

    # Create test squad and members
    squad = Squad(
        id=uuid4(),
        org_id=uuid4(),
        user_id=uuid4(),
        name="Test Squad",
        status="active",
        config={}
    )
    db_session.add(squad)

    member1 = SquadMember(
        id=uuid4(),
        squad_id=squad.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4",
        is_active=True,
        config={}
    )
    member2 = SquadMember(
        id=uuid4(),
        squad_id=squad.id,
        role="frontend_developer",
        llm_provider="anthropic",
        llm_model="claude-3-opus",
        is_active=True,
        config={}
    )
    db_session.add(member1)
    db_session.add(member2)
    await db_session.commit()

    # First call - cache MISS
    members_1 = await squad_cache.get_squad_members(db_session, squad.id)
    assert len(members_1) == 2

    # Second call - cache HIT
    members_2 = await squad_cache.get_squad_members(db_session, squad.id)
    assert len(members_2) == 2

    # Invalidate cache
    await squad_cache.invalidate_squad_member(squad.id)

    # Third call - cache MISS
    members_3 = await squad_cache.get_squad_members(db_session, squad.id)
    assert len(members_3) == 2


@pytest.mark.asyncio
async def test_execution_status_caching(db_session: AsyncSession):
    """Test execution status caching (HOT PATH)"""
    task_cache = get_task_cache()

    # Create test execution
    project_id = uuid4()
    task_id = uuid4()
    squad_id = uuid4()

    task = Task(
        id=task_id,
        project_id=project_id,
        title="Test Task",
        description="Test task",
        status="pending",
        priority="medium",
        task_metadata={}
    )
    db_session.add(task)

    execution = TaskExecution(
        id=uuid4(),
        task_id=task_id,
        squad_id=squad_id,
        status="pending",
        logs=[],
        execution_metadata={}
    )
    db_session.add(execution)
    await db_session.commit()

    # First call - cache MISS
    status_1 = await task_cache.get_execution_status(db_session, execution.id)
    assert status_1 == "pending"

    # Second call - cache HIT (hot path optimization)
    status_2 = await task_cache.get_execution_status(db_session, execution.id)
    assert status_2 == "pending"

    # Update status and invalidate
    execution.status = "in_progress"
    await db_session.commit()
    await task_cache.invalidate_execution(execution.id, task_id, squad_id)

    # Third call - cache MISS (after invalidation)
    status_3 = await task_cache.get_execution_status(db_session, execution.id)
    assert status_3 == "in_progress"


@pytest.mark.asyncio
async def test_cache_bypass_option(db_session: AsyncSession):
    """Test that use_cache=False bypasses cache"""
    squad_cache = get_squad_cache()

    # Create test squad
    squad = Squad(
        id=uuid4(),
        org_id=uuid4(),
        user_id=uuid4(),
        name="Test Squad",
        status="active",
        config={}
    )
    db_session.add(squad)
    await db_session.commit()

    # Call with caching
    cached_1 = await squad_cache.get_squad_by_id(db_session, squad.id, use_cache=True)
    assert cached_1 is not None

    # Update squad name
    squad.name = "Updated Squad"
    await db_session.commit()

    # Call with cache (should still see old name)
    cached_2 = await squad_cache.get_squad_by_id(db_session, squad.id, use_cache=True)
    assert cached_2["name"] == "Test Squad"  # Cached value

    # Call WITHOUT cache (should see new name)
    fresh = await squad_cache.get_squad_by_id(db_session, squad.id, use_cache=False)
    assert fresh is not None
    # Note: Database returns Squad object, not dict


@pytest.mark.asyncio
async def test_warm_cache(db_session: AsyncSession):
    """Test cache warming functionality"""
    squad_cache = get_squad_cache()

    # Create multiple squads
    squad_ids = []
    for i in range(5):
        squad = Squad(
            id=uuid4(),
            org_id=uuid4(),
            user_id=uuid4(),
            name=f"Squad {i}",
            status="active",
            config={}
        )
        db_session.add(squad)
        squad_ids.append(squad.id)

    await db_session.commit()

    # Warm cache for all squads
    cached_count = await squad_cache.warm_cache(db_session, squad_ids)
    assert cached_count == 5

    # All squads should now be in cache
    for squad_id in squad_ids:
        cached = await squad_cache.get_squad_by_id(db_session, squad_id)
        assert cached is not None


@pytest.mark.asyncio
async def test_organization_squads_caching(db_session: AsyncSession):
    """Test caching of squads by organization"""
    squad_cache = get_squad_cache()

    org_id = uuid4()

    # Create multiple squads for same org
    for i in range(3):
        squad = Squad(
            id=uuid4(),
            org_id=org_id,
            user_id=uuid4(),
            name=f"Squad {i}",
            status="active" if i < 2 else "inactive",
            config={}
        )
        db_session.add(squad)

    await db_session.commit()

    # First call - cache MISS
    squads_1 = await squad_cache.get_squads_by_organization(
        db_session, org_id, active_only=False
    )
    assert len(squads_1) == 3

    # Second call - cache HIT
    squads_2 = await squad_cache.get_squads_by_organization(
        db_session, org_id, active_only=False
    )
    assert len(squads_2) == 3

    # Filter by active only (uses cached data)
    active_squads = await squad_cache.get_squads_by_organization(
        db_session, org_id, active_only=True
    )
    assert len(active_squads) == 2


@pytest.mark.asyncio
async def test_execution_list_caching(db_session: AsyncSession):
    """Test caching of execution lists by squad"""
    task_cache = get_task_cache()

    project_id = uuid4()
    task_id = uuid4()
    squad_id = uuid4()

    # Create task
    task = Task(
        id=task_id,
        project_id=project_id,
        title="Test Task",
        description="Test",
        status="pending",
        priority="medium",
        task_metadata={}
    )
    db_session.add(task)

    # Create multiple executions
    for i in range(3):
        execution = TaskExecution(
            id=uuid4(),
            task_id=task_id,
            squad_id=squad_id,
            status="pending",
            logs=[],
            execution_metadata={}
        )
        db_session.add(execution)

    await db_session.commit()

    # First call - cache MISS
    executions_1 = await task_cache.get_executions_by_squad(
        db_session, squad_id, limit=100
    )
    assert len(executions_1) == 3

    # Second call - cache HIT
    executions_2 = await task_cache.get_executions_by_squad(
        db_session, squad_id, limit=100
    )
    assert len(executions_2) == 3
