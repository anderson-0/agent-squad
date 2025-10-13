"""
Squad Management API Endpoints

Endpoints for creating, managing, and viewing AI agent squads.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.squad import Squad
from backend.services.squad_service import SquadService
from backend.schemas.squad import (
    SquadCreate,
    SquadUpdate,
    SquadResponse,
    SquadWithAgents,
    SquadCostEstimate,
)


router = APIRouter(prefix="/squads", tags=["squads"])


@router.post(
    "",
    response_model=SquadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new squad",
    description="Create a new AI agent squad for your organization or personal use"
)
async def create_squad(
    squad_data: SquadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Squad:
    """
    Create a new squad.

    - **name**: Squad name (required)
    - **description**: Squad description (optional)
    - **organization_id**: Organization ID (optional, defaults to personal squad)
    - **config**: Squad configuration (optional)

    Returns the created squad object.
    """
    # Create squad for current user
    squad = await SquadService.create_squad(
        db=db,
        user_id=current_user.id,
        name=squad_data.name,
        description=squad_data.description,
        org_id=squad_data.org_id,
        config=squad_data.config or {},
    )

    return squad


@router.get(
    "",
    response_model=List[SquadResponse],
    summary="List user's squads",
    description="Get all squads owned by the current user"
)
async def list_squads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_id: UUID | None = Query(None, description="Filter by organization"),
    status_filter: str | None = Query(None, description="Filter by status (active/inactive)"),
    skip: int = Query(0, ge=0, description="Number of squads to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of squads to return"),
) -> List[Squad]:
    """
    List all squads for current user.

    Supports filtering by:
    - **organization_id**: Filter by organization
    - **status**: Filter by status (active/inactive)

    Supports pagination with skip and limit.
    """
    squads = await SquadService.get_user_squads(
        db=db,
        user_id=current_user.id,
        status=status_filter,
    )

    # Apply pagination
    return squads[skip: skip + limit]


@router.get(
    "/{squad_id}",
    response_model=SquadResponse,
    summary="Get squad details",
    description="Get details of a specific squad"
)
async def get_squad(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Squad:
    """
    Get squad by ID.

    - **squad_id**: UUID of the squad

    Returns squad details if user has access.
    """
    # Get squad
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    return squad


@router.get(
    "/{squad_id}/details",
    response_model=SquadWithAgents,
    summary="Get squad with all agents",
    description="Get complete squad details including all agent members"
)
async def get_squad_details(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete squad details including all agents.

    - **squad_id**: UUID of the squad

    Returns squad with full agent details.
    """
    # Check if squad exists first
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Then verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get squad with agents
    squad_details = await SquadService.get_squad_with_agents(db, squad_id)

    return squad_details


@router.get(
    "/{squad_id}/cost",
    response_model=SquadCostEstimate,
    summary="Get squad cost estimate",
    description="Calculate estimated monthly cost for squad based on LLM usage"
)
async def get_squad_cost(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get estimated monthly cost for squad.

    - **squad_id**: UUID of the squad

    Returns cost breakdown by LLM model.
    """
    # Check if squad exists first
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Then verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Calculate cost
    cost_estimate = await SquadService.calculate_squad_cost(db, squad_id)

    return cost_estimate


@router.put(
    "/{squad_id}",
    response_model=SquadResponse,
    summary="Update squad",
    description="Update squad details"
)
async def update_squad(
    squad_id: UUID,
    squad_update: SquadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Squad:
    """
    Update squad details.

    - **squad_id**: UUID of the squad
    - **name**: New name (optional)
    - **description**: New description (optional)
    - **status**: New status (optional)
    - **config**: New config (optional)

    Returns updated squad.
    """
    # Check if squad exists first
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Then verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Update squad
    updated_squad = await SquadService.update_squad(
        db=db,
        squad_id=squad_id,
        name=squad_update.name,
        description=squad_update.description,
        status=squad_update.status,
        config=squad_update.config,
    )

    return updated_squad


@router.patch(
    "/{squad_id}/status",
    response_model=SquadResponse,
    summary="Update squad status",
    description="Activate or deactivate a squad"
)
async def update_squad_status(
    squad_id: UUID,
    new_status: str = Query(..., regex="^(active|paused|archived)$", description="New status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Squad:
    """
    Update squad status (activate/deactivate).

    - **squad_id**: UUID of the squad
    - **new_status**: New status (active/inactive)

    Returns updated squad.
    """
    # Check if squad exists first
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Then verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Update status
    updated_squad = await SquadService.update_squad_status(
        db=db,
        squad_id=squad_id,
        status=new_status,
    )

    return updated_squad


@router.delete(
    "/{squad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete squad",
    description="Permanently delete a squad and all its agents"
)
async def delete_squad(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete squad permanently.

    - **squad_id**: UUID of the squad

    This will also delete:
    - All squad members (agents)
    - All task executions
    - All messages

    This action cannot be undone.
    """
    # Check if squad exists first
    squad = await SquadService.get_squad(db, squad_id)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Then verify ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Delete squad
    await SquadService.delete_squad(db, squad_id)
