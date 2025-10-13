"""
Tests for SquadService
"""
import pytest
from uuid import uuid4
from fastapi import HTTPException

from backend.services.squad_service import SquadService
from backend.models.user import User
from backend.models.squad import Squad


@pytest.mark.asyncio
async def test_create_squad(test_db):
    """Test creating a squad"""
    # Create a user first
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
        plan_tier="pro"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Create squad
    squad = await SquadService.create_squad(
        db=test_db,
        name="Test Squad",
        user_id=user.id,
        description="A test squad"
    )

    assert squad.name == "Test Squad"
    assert squad.user_id == user.id
    assert squad.status == "active"
    assert squad.description == "A test squad"


@pytest.mark.asyncio
async def test_get_squad(test_db):
    """Test retrieving a squad by ID"""
    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")

    # Get squad
    retrieved = await SquadService.get_squad(test_db, squad.id)

    assert retrieved is not None
    assert retrieved.id == squad.id
    assert retrieved.name == "Squad"


@pytest.mark.asyncio
async def test_get_user_squads(test_db):
    """Test retrieving all squads for a user"""
    # Create user
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Create multiple squads
    await SquadService.create_squad(test_db, user_id=user.id, name="Squad 1")
    await SquadService.create_squad(test_db, user_id=user.id, name="Squad 2")
    await SquadService.create_squad(test_db, user_id=user.id, name="Squad 3")

    # Get all squads
    squads = await SquadService.get_user_squads(test_db, user.id)

    assert len(squads) == 3
    assert all(s.user_id == user.id for s in squads)


@pytest.mark.asyncio
async def test_update_squad(test_db):
    """Test updating a squad"""
    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Original Name")

    # Update squad
    updated = await SquadService.update_squad(
        db=test_db,
        squad_id=squad.id,
        name="New Name",
        description="New description"
    )

    assert updated.name == "New Name"
    assert updated.description == "New description"


@pytest.mark.asyncio
async def test_update_squad_status(test_db):
    """Test updating squad status"""
    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")
    assert squad.status == "active"

    # Pause
    updated = await SquadService.update_squad_status(test_db, squad.id, "paused")
    assert updated.status == "paused"

    # Reactivate
    updated = await SquadService.update_squad_status(test_db, squad.id, "active")
    assert updated.status == "active"


@pytest.mark.asyncio
async def test_delete_squad(test_db):
    """Test deleting a squad"""
    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")
    squad_id = squad.id

    # Delete
    await SquadService.delete_squad(test_db, squad_id)

    # Verify deleted
    deleted_squad = await SquadService.get_squad(test_db, squad_id)
    assert deleted_squad is None


@pytest.mark.asyncio
async def test_validate_squad_size_starter(test_db):
    """Test squad size validation for starter plan"""
    # Create user with starter plan
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="starter")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")

    # Should allow up to 3 members
    await SquadService.validate_squad_size(test_db, squad.id, user.id, new_member_count=3)

    # Should fail for 4 members
    with pytest.raises(HTTPException) as exc_info:
        await SquadService.validate_squad_size(test_db, squad.id, user.id, new_member_count=4)

    assert exc_info.value.status_code == 400
    assert "limit" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_validate_squad_size_pro(test_db):
    """Test squad size validation for pro plan"""
    # Create user with pro plan
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")

    # Should allow up to 10 members
    await SquadService.validate_squad_size(test_db, squad.id, user.id, new_member_count=10)

    # Should fail for 11 members
    with pytest.raises(HTTPException) as exc_info:
        await SquadService.validate_squad_size(test_db, squad.id, user.id, new_member_count=11)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_calculate_squad_cost(test_db):
    """Test calculating squad cost estimation"""
    from backend.services.agent_service import AgentService

    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")

    # Add agents with different models
    await AgentService.create_squad_member(
        test_db, squad.id, "project_manager", llm_model="gpt-4"
    )
    await AgentService.create_squad_member(
        test_db, squad.id, "backend_developer", llm_model="gpt-3.5-turbo"
    )

    # Calculate cost
    cost_estimate = await SquadService.calculate_squad_cost(test_db, squad.id)

    assert "total_monthly_cost" in cost_estimate
    assert "cost_by_model" in cost_estimate
    assert cost_estimate["member_count"] == 2
    assert cost_estimate["total_monthly_cost"] > 0


@pytest.mark.asyncio
async def test_verify_squad_ownership(test_db):
    """Test squad ownership verification"""
    # Create two users
    user1 = User(email="user1@example.com", name="User 1", password_hash="hash", plan_tier="pro")
    user2 = User(email="user2@example.com", name="User 2", password_hash="hash", plan_tier="pro")
    test_db.add_all([user1, user2])
    await test_db.commit()
    await test_db.refresh(user1)
    await test_db.refresh(user2)

    # Create squad for user1
    squad = await SquadService.create_squad(test_db, user_id=user1.id, name="Squad")

    # User1 should have access
    await SquadService.verify_squad_ownership(test_db, squad.id, user1.id)

    # User2 should not have access
    with pytest.raises(HTTPException) as exc_info:
        await SquadService.verify_squad_ownership(test_db, squad.id, user2.id)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_squad_with_agents(test_db):
    """Test getting squad with all agents"""
    from backend.services.agent_service import AgentService

    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = await SquadService.create_squad(test_db, user_id=user.id, name="Squad")

    # Add agents
    await AgentService.create_squad_member(test_db, squad.id, "project_manager")
    await AgentService.create_squad_member(test_db, squad.id, "backend_developer")
    await AgentService.create_squad_member(test_db, squad.id, "qa_tester")

    # Get squad with agents
    squad_details = await SquadService.get_squad_with_agents(test_db, squad.id)

    assert squad_details is not None
    assert "squad" in squad_details
    assert "name" in squad_details["squad"]
    assert "members" in squad_details
    assert len(squad_details["members"]) == 3
    assert squad_details["member_count"] == 3
    assert squad_details["active_member_count"] == 3
