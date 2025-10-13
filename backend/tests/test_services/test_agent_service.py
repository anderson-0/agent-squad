"""
Tests for Agent Service
"""
import pytest
from uuid import uuid4
from fastapi import HTTPException

from backend.services.agent_service import AgentService
from backend.models.user import User
from backend.models.squad import Squad, SquadMember


@pytest.mark.asyncio
async def test_create_squad_member(test_db):
    """Test creating a squad member"""
    # Create user and squad
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    # Create squad member
    member = await AgentService.create_squad_member(
        db=test_db,
        squad_id=squad.id,
        role="backend_developer",
        specialization="Python/FastAPI",
        llm_provider="openai",
        llm_model="gpt-4"
    )

    assert member.squad_id == squad.id
    assert member.role == "backend_developer"
    assert member.specialization == "Python/FastAPI"
    assert member.llm_provider == "openai"
    assert member.llm_model == "gpt-4"
    assert member.is_active is True
    assert member.system_prompt is not None


@pytest.mark.asyncio
async def test_create_squad_member_invalid_squad(test_db):
    """Test creating member with invalid squad ID"""
    invalid_squad_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.create_squad_member(
            db=test_db,
            squad_id=invalid_squad_id,
            role="backend_developer"
        )

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_squad_member_invalid_role(test_db):
    """Test creating member with invalid role"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.create_squad_member(
            db=test_db,
            squad_id=squad.id,
            role="invalid_role"
        )

    assert exc_info.value.status_code == 400
    assert "invalid role" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_squad_member(test_db):
    """Test retrieving a squad member"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    member = await AgentService.create_squad_member(
        db=test_db,
        squad_id=squad.id,
        role="project_manager"
    )

    # Get member
    retrieved = await AgentService.get_squad_member(test_db, member.id)

    assert retrieved is not None
    assert retrieved.id == member.id
    assert retrieved.role == "project_manager"


@pytest.mark.asyncio
async def test_get_squad_member_not_found(test_db):
    """Test getting non-existent squad member"""
    invalid_id = uuid4()
    member = await AgentService.get_squad_member(test_db, invalid_id)
    assert member is None


@pytest.mark.asyncio
async def test_get_squad_members(test_db):
    """Test getting all members of a squad"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    # Create multiple members
    await AgentService.create_squad_member(test_db, squad.id, "project_manager")
    await AgentService.create_squad_member(test_db, squad.id, "backend_developer")
    await AgentService.create_squad_member(test_db, squad.id, "qa_tester")

    # Get all members
    members = await AgentService.get_squad_members(test_db, squad.id, active_only=True)

    assert len(members) == 3
    roles = {m.role for m in members}
    assert "project_manager" in roles
    assert "backend_developer" in roles
    assert "qa_tester" in roles


@pytest.mark.asyncio
async def test_get_squad_members_active_only(test_db):
    """Test filtering active members only"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    # Create members
    member1 = await AgentService.create_squad_member(test_db, squad.id, "project_manager")
    member2 = await AgentService.create_squad_member(test_db, squad.id, "backend_developer")

    # Deactivate one
    await AgentService.deactivate_squad_member(test_db, member2.id)

    # Get active only
    active_members = await AgentService.get_squad_members(test_db, squad.id, active_only=True)
    assert len(active_members) == 1
    assert active_members[0].role == "project_manager"

    # Get all members
    all_members = await AgentService.get_squad_members(test_db, squad.id, active_only=False)
    assert len(all_members) == 2


@pytest.mark.asyncio
async def test_get_squad_member_by_role(test_db):
    """Test getting member by role"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    await AgentService.create_squad_member(test_db, squad.id, "project_manager")
    await AgentService.create_squad_member(test_db, squad.id, "backend_developer")

    # Get by role
    pm = await AgentService.get_squad_member_by_role(test_db, squad.id, "project_manager")

    assert pm is not None
    assert pm.role == "project_manager"


@pytest.mark.asyncio
async def test_update_squad_member(test_db):
    """Test updating squad member"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    member = await AgentService.create_squad_member(test_db, squad.id, "backend_developer")

    # Update member
    updated = await AgentService.update_squad_member(
        db=test_db,
        member_id=member.id,
        specialization="Python/Django",
        llm_model="gpt-4-turbo",
        config={"temperature": 0.8}
    )

    assert updated.specialization == "Python/Django"
    assert updated.llm_model == "gpt-4-turbo"
    assert updated.config["temperature"] == 0.8


@pytest.mark.asyncio
async def test_update_squad_member_not_found(test_db):
    """Test updating non-existent member"""
    invalid_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.update_squad_member(
            db=test_db,
            member_id=invalid_id,
            specialization="Python"
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_squad_member(test_db):
    """Test deactivating squad member"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    member = await AgentService.create_squad_member(test_db, squad.id, "backend_developer")
    assert member.is_active is True

    # Deactivate
    deactivated = await AgentService.deactivate_squad_member(test_db, member.id)
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_deactivate_squad_member_not_found(test_db):
    """Test deactivating non-existent member"""
    invalid_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.deactivate_squad_member(test_db, invalid_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_reactivate_squad_member(test_db):
    """Test reactivating squad member"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    member = await AgentService.create_squad_member(test_db, squad.id, "backend_developer")

    # Deactivate then reactivate
    await AgentService.deactivate_squad_member(test_db, member.id)
    reactivated = await AgentService.reactivate_squad_member(test_db, member.id)

    assert reactivated.is_active is True


@pytest.mark.asyncio
async def test_reactivate_squad_member_not_found(test_db):
    """Test reactivating non-existent member"""
    invalid_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.reactivate_squad_member(test_db, invalid_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_squad_member(test_db):
    """Test deleting squad member"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    member = await AgentService.create_squad_member(test_db, squad.id, "backend_developer")
    member_id = member.id

    # Delete
    success = await AgentService.delete_squad_member(test_db, member_id)
    assert success is True

    # Verify deleted
    deleted_member = await AgentService.get_squad_member(test_db, member_id)
    assert deleted_member is None


@pytest.mark.asyncio
async def test_delete_squad_member_not_found(test_db):
    """Test deleting non-existent member"""
    invalid_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await AgentService.delete_squad_member(test_db, invalid_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_squad_composition(test_db):
    """Test getting squad composition"""
    user = User(email="test@example.com", name="Test", password_hash="hash", plan_tier="pro")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    squad = Squad(user_id=user.id, name="Test Squad", status="active", config={})
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)

    # Create diverse members
    await AgentService.create_squad_member(test_db, squad.id, "project_manager", llm_provider="openai", llm_model="gpt-4")
    await AgentService.create_squad_member(test_db, squad.id, "backend_developer", llm_provider="openai", llm_model="gpt-4")
    await AgentService.create_squad_member(test_db, squad.id, "backend_developer", llm_provider="anthropic", llm_model="claude-3-opus")
    await AgentService.create_squad_member(test_db, squad.id, "qa_tester", llm_provider="openai", llm_model="gpt-3.5-turbo")

    # Get composition
    composition = await AgentService.get_squad_composition(test_db, squad.id)

    assert composition["squad_id"] == str(squad.id)
    assert composition["total_members"] == 4
    assert composition["active_members"] == 4
    assert composition["roles"]["project_manager"] == 1
    assert composition["roles"]["backend_developer"] == 2
    assert composition["roles"]["qa_tester"] == 1
    assert composition["llm_providers"]["openai"] == 3
    assert composition["llm_providers"]["anthropic"] == 1
    assert len(composition["members"]) == 4
