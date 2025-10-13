"""
Squad Member (Agent) API Endpoints

Endpoints for managing AI agents within squads.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.squad import SquadMember
from backend.services.agent_service import AgentService
from backend.services.squad_service import SquadService
from backend.schemas.squad_member import (
    SquadMemberCreate,
    SquadMemberUpdate,
    SquadMemberResponse,
    SquadMemberWithConfig,
    SquadComposition,
)


router = APIRouter(prefix="/squad-members", tags=["squad-members"])


@router.post(
    "",
    response_model=SquadMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add agent to squad",
    description="Create a new AI agent and add it to a squad"
)
async def create_squad_member(
    member_data: SquadMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Create a new agent (squad member).

    - **squad_id**: Squad to add agent to
    - **role**: Agent role (project_manager, tech_lead, backend_developer, etc.)
    - **specialization**: Agent specialization (optional)
    - **llm_provider**: LLM provider (openai, anthropic, groq)
    - **llm_model**: LLM model (gpt-4, claude-3-opus, etc.)
    - **config**: Agent configuration (optional)

    Returns the created agent.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member_data.squad_id, current_user.id)

    # Validate squad size before adding
    await SquadService.validate_squad_size(
        db=db,
        squad_id=member_data.squad_id,
        user_id=current_user.id,
        new_member_count=1,
    )

    # Create squad member
    member = await AgentService.create_squad_member(
        db=db,
        squad_id=member_data.squad_id,
        role=member_data.role,
        specialization=member_data.specialization,
        llm_provider=member_data.llm_provider,
        llm_model=member_data.llm_model,
        config=member_data.config or {},
    )

    return member


@router.get(
    "",
    response_model=List[SquadMemberResponse],
    summary="List squad members",
    description="Get all agents in a squad"
)
async def list_squad_members(
    squad_id: UUID = Query(..., description="Squad ID to get members for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Only return active members"),
    role: str | None = Query(None, description="Filter by role"),
) -> List[SquadMember]:
    """
    List all members of a squad.

    - **squad_id**: Squad ID (required)
    - **active_only**: Only return active members (default: true)
    - **role**: Filter by specific role (optional)

    Returns list of agents in the squad.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get squad members
    members = await AgentService.get_squad_members(
        db=db,
        squad_id=squad_id,
        active_only=active_only,
    )

    # Filter by role if specified
    if role:
        members = [m for m in members if m.role == role]

    return members


@router.get(
    "/{member_id}",
    response_model=SquadMemberResponse,
    summary="Get squad member details",
    description="Get details of a specific agent"
)
async def get_squad_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Get squad member by ID.

    - **member_id**: UUID of the squad member

    Returns agent details if user has access.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    return member


@router.get(
    "/{member_id}/config",
    response_model=SquadMemberWithConfig,
    summary="Get squad member with full config",
    description="Get agent details with complete configuration"
)
async def get_squad_member_config(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Get squad member with full configuration.

    - **member_id**: UUID of the squad member

    Returns agent with complete config including system prompt.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    return member


@router.get(
    "/by-role/{role}",
    response_model=List[SquadMemberResponse],
    summary="Get squad members by role",
    description="Get all agents with a specific role in a squad"
)
async def get_members_by_role(
    role: str,
    squad_id: UUID = Query(..., description="Squad ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[SquadMember]:
    """
    Get all members with a specific role.

    - **role**: Agent role to filter by
    - **squad_id**: Squad ID

    Returns list of agents with that role.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get members by role
    members = await AgentService.get_squad_member_by_role(
        db=db,
        squad_id=squad_id,
        role=role,
    )

    return members


@router.get(
    "/squad/{squad_id}/composition",
    response_model=SquadComposition,
    summary="Get squad composition",
    description="Get summary of squad composition (roles, providers, models)"
)
async def get_squad_composition(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get squad composition summary.

    - **squad_id**: Squad ID

    Returns breakdown of roles, LLM providers, and models in use.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get composition
    composition = await AgentService.get_squad_composition(db, squad_id)

    return composition


@router.put(
    "/{member_id}",
    response_model=SquadMemberResponse,
    summary="Update squad member",
    description="Update agent configuration"
)
async def update_squad_member(
    member_id: UUID,
    member_update: SquadMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Update squad member details.

    - **member_id**: UUID of the squad member
    - **specialization**: New specialization (optional)
    - **llm_provider**: New LLM provider (optional)
    - **llm_model**: New LLM model (optional)
    - **config**: New configuration (optional)

    Returns updated agent.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    # Update member
    updated_member = await AgentService.update_squad_member(
        db=db,
        member_id=member_id,
        specialization=member_update.specialization,
        llm_provider=member_update.llm_provider,
        llm_model=member_update.llm_model,
        config=member_update.config,
    )

    if not updated_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    return updated_member


@router.patch(
    "/{member_id}/deactivate",
    response_model=SquadMemberResponse,
    summary="Deactivate squad member",
    description="Temporarily deactivate an agent"
)
async def deactivate_squad_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Deactivate squad member.

    - **member_id**: UUID of the squad member

    Deactivated agents won't be assigned tasks but remain in the squad.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    # Deactivate
    updated_member = await AgentService.deactivate_squad_member(db, member_id)

    if not updated_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    return updated_member


@router.patch(
    "/{member_id}/reactivate",
    response_model=SquadMemberResponse,
    summary="Reactivate squad member",
    description="Reactivate a deactivated agent"
)
async def reactivate_squad_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SquadMember:
    """
    Reactivate squad member.

    - **member_id**: UUID of the squad member

    Reactivated agents can be assigned tasks again.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    # Reactivate
    updated_member = await AgentService.reactivate_squad_member(db, member_id)

    if not updated_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    return updated_member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete squad member",
    description="Permanently remove an agent from squad"
)
async def delete_squad_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete squad member permanently.

    - **member_id**: UUID of the squad member

    This action cannot be undone.
    """
    # Get member
    member = await AgentService.get_squad_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, member.squad_id, current_user.id)

    # Delete
    success = await AgentService.delete_squad_member(db, member_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad member {member_id} not found"
        )
