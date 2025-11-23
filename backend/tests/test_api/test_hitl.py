"""
Test HITL (Human-in-the-Loop) API endpoints
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.squad import Squad
from backend.models.approval_request import ApprovalRequest, ApprovalStatus


@pytest.mark.asyncio
async def test_pause_squad(client: AsyncClient, test_test_db: AsyncSession):
    """Test pausing a squad"""
    # Create a test squad
    squad = Squad(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Squad",
        description="Test description",
        status="active",
        is_paused=False,
        config={}
    )
    test_db.add(squad)
    await test_db.commit()
    
    # Pause the squad
    response = await client.post(f"/api/v1/squads/{squad.id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["is_paused"] is True
    
    # Verify in database
    await test_db.refresh(squad)
    assert squad.is_paused is True


@pytest.mark.asyncio
async def test_resume_squad(client: AsyncClient, test_db: AsyncSession):
    """Test resuming a paused squad"""
    # Create a paused squad
    squad = Squad(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Squad",
        description="Test description",
        status="active",
        is_paused=True,
        config={}
    )
    test_db.add(squad)
    await test_db.commit()
    
    # Resume the squad
    response = await client.post(f"/api/v1/squads/{squad.id}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["is_paused"] is False
    
    # Verify in database
    await test_db.refresh(squad)
    assert squad.is_paused is False


@pytest.mark.asyncio
async def test_get_pending_approvals(client: AsyncClient, test_db: AsyncSession):
    """Test getting pending approval requests"""
    squad_id = uuid4()
    agent_id = uuid4()
    
    # Create a squad
    squad = Squad(
        id=squad_id,
        user_id=uuid4(),
        name="Test Squad",
        config={}
    )
    test_db.add(squad)
    
    # Create approval requests
    approval1 = ApprovalRequest(
        id=uuid4(),
        squad_id=squad_id,
        agent_id=agent_id,
        action_type="deploy",
        payload={"service": "backend", "environment": "production"},
        status=ApprovalStatus.PENDING
    )
    approval2 = ApprovalRequest(
        id=uuid4(),
        squad_id=squad_id,
        agent_id=agent_id,
        action_type="delete_resource",
        payload={"resource": "database"},
        status=ApprovalStatus.APPROVED  # This one should not appear
    )
    test_db.add_all([approval1, approval2])
    await test_db.commit()
    
    # Get pending approvals
    response = await client.get(f"/api/v1/squads/{squad_id}/approvals")
    assert response.status_code == 200
    data = response.json()
    
    # Should only return pending approval
    assert len(data) == 1
    assert data[0]["action_type"] == "deploy"
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_approve_request(client: AsyncClient, test_db: AsyncSession):
    """Test approving a pending request"""
    approval = ApprovalRequest(
        id=uuid4(),
        squad_id=uuid4(),
        agent_id=uuid4(),
        action_type="deploy",
        payload={"service": "backend"},
        status=ApprovalStatus.PENDING
    )
    test_db.add(approval)
    await test_db.commit()
    
    # Approve the request
    response = await client.post(f"/api/v1/approvals/{approval.id}/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    
    # Verify in database
    await test_db.refresh(approval)
    assert approval.status == ApprovalStatus.APPROVED


@pytest.mark.asyncio
async def test_reject_request(client: AsyncClient, test_db: AsyncSession):
    """Test rejecting a pending request"""
    approval = ApprovalRequest(
        id=uuid4(),
        squad_id=uuid4(),
        agent_id=uuid4(),
        action_type="delete_resource",
        payload={"resource": "database"},
        status=ApprovalStatus.PENDING
    )
    test_db.add(approval)
    await test_db.commit()
    
    # Reject the request
    response = await client.post(f"/api/v1/approvals/{approval.id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    
    # Verify in database
    await test_db.refresh(approval)
    assert approval.status == ApprovalStatus.REJECTED
