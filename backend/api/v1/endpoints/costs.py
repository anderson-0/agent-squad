"""
Cost Tracking API Endpoints

Provides endpoints for querying LLM cost data and analytics.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.models import LLMCostEntry, LLMCostSummary, Squad, User, Organization
from pydantic import BaseModel, Field

router = APIRouter(prefix="/costs", tags=["costs"])


# ============================================================================
# Schemas
# ============================================================================

class CostEntryResponse(BaseModel):
    """Response schema for a single cost entry"""
    id: UUID
    provider: str
    model: str
    squad_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    task_execution_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float
    prompt_price_per_1m: Optional[float] = None
    completion_price_per_1m: Optional[float] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    response_time_ms: Optional[int] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CostStatsResponse(BaseModel):
    """Response schema for cost statistics"""
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_cost_per_request: float
    avg_tokens_per_request: float
    avg_response_time_ms: Optional[float] = None
    by_provider: dict[str, dict]
    by_model: dict[str, dict]
    date_range: dict[str, datetime]


class CostSummaryResponse(BaseModel):
    """Response schema for a cost summary"""
    id: UUID
    summary_type: str
    summary_date: datetime
    organization_id: Optional[UUID] = None
    squad_id: Optional[UUID] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    total_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float
    avg_tokens_per_request: Optional[float] = None
    avg_cost_per_request: Optional[float] = None
    avg_response_time_ms: Optional[float] = None
    last_updated: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/entries", response_model=List[CostEntryResponse])
async def get_cost_entries(
    squad_id: Optional[UUID] = Query(None, description="Filter by squad ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    task_execution_id: Optional[UUID] = Query(None, description="Filter by task execution ID"),
    provider: Optional[str] = Query(None, description="Filter by LLM provider"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get LLM cost entries with optional filters.

    Supports filtering by:
    - Squad, user, organization
    - Task execution
    - Provider and model
    - Date range

    Returns up to `limit` entries with pagination support.
    """
    # Build query
    query = select(LLMCostEntry).order_by(LLMCostEntry.created_at.desc())

    # Apply filters
    filters = []
    if squad_id:
        filters.append(LLMCostEntry.squad_id == squad_id)
    if user_id:
        filters.append(LLMCostEntry.user_id == user_id)
    if organization_id:
        filters.append(LLMCostEntry.organization_id == organization_id)
    if task_execution_id:
        filters.append(LLMCostEntry.task_execution_id == task_execution_id)
    if provider:
        filters.append(LLMCostEntry.provider == provider)
    if model:
        filters.append(LLMCostEntry.model == model)
    if start_date:
        filters.append(LLMCostEntry.created_at >= start_date)
    if end_date:
        filters.append(LLMCostEntry.created_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    entries = result.scalars().all()

    return entries


@router.get("/stats", response_model=CostStatsResponse)
async def get_cost_stats(
    squad_id: Optional[UUID] = Query(None, description="Filter by squad ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter to this date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated cost statistics.

    Returns:
    - Total requests, tokens, and cost
    - Average cost and tokens per request
    - Breakdown by provider and model
    - Date range of data
    """
    # Build base query
    query = select(LLMCostEntry)

    # Apply filters
    filters = []
    if squad_id:
        filters.append(LLMCostEntry.squad_id == squad_id)
    if user_id:
        filters.append(LLMCostEntry.user_id == user_id)
    if organization_id:
        filters.append(LLMCostEntry.organization_id == organization_id)
    if start_date:
        filters.append(LLMCostEntry.created_at >= start_date)
    if end_date:
        filters.append(LLMCostEntry.created_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Execute query
    result = await db.execute(query)
    entries = result.scalars().all()

    if not entries:
        return CostStatsResponse(
            total_requests=0,
            total_tokens=0,
            total_cost_usd=0.0,
            avg_cost_per_request=0.0,
            avg_tokens_per_request=0.0,
            avg_response_time_ms=None,
            by_provider={},
            by_model={},
            date_range={}
        )

    # Calculate aggregates
    total_requests = len(entries)
    total_tokens = sum(e.total_tokens for e in entries)
    total_cost = sum(e.total_cost_usd for e in entries)

    # Calculate averages
    avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
    avg_tokens = total_tokens / total_requests if total_requests > 0 else 0.0

    response_times = [e.response_time_ms for e in entries if e.response_time_ms is not None]
    avg_response_time = sum(response_times) / len(response_times) if response_times else None

    # Group by provider
    by_provider = {}
    for entry in entries:
        if entry.provider not in by_provider:
            by_provider[entry.provider] = {
                "requests": 0,
                "tokens": 0,
                "cost_usd": 0.0
            }
        by_provider[entry.provider]["requests"] += 1
        by_provider[entry.provider]["tokens"] += entry.total_tokens
        by_provider[entry.provider]["cost_usd"] += entry.total_cost_usd

    # Group by model
    by_model = {}
    for entry in entries:
        model_key = f"{entry.provider}/{entry.model}"
        if model_key not in by_model:
            by_model[model_key] = {
                "requests": 0,
                "tokens": 0,
                "cost_usd": 0.0
            }
        by_model[model_key]["requests"] += 1
        by_model[model_key]["tokens"] += entry.total_tokens
        by_model[model_key]["cost_usd"] += entry.total_cost_usd

    # Date range
    min_date = min(e.created_at for e in entries)
    max_date = max(e.created_at for e in entries)

    return CostStatsResponse(
        total_requests=total_requests,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 6),
        avg_cost_per_request=round(avg_cost, 6),
        avg_tokens_per_request=round(avg_tokens, 2),
        avg_response_time_ms=round(avg_response_time, 2) if avg_response_time else None,
        by_provider=by_provider,
        by_model=by_model,
        date_range={
            "start": min_date,
            "end": max_date
        }
    )


@router.get("/squad/{squad_id}", response_model=CostStatsResponse)
async def get_squad_costs(
    squad_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost statistics for a specific squad.

    Args:
        squad_id: Squad UUID
        days: Number of days to look back (default: 30)

    Returns:
        Cost statistics for the squad
    """
    # Check if squad exists
    result = await db.execute(
        select(Squad).where(Squad.id == squad_id)
    )
    squad = result.scalar_one_or_none()

    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad {squad_id} not found"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get stats
    return await get_cost_stats(
        squad_id=squad_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )


@router.get("/user/{user_id}", response_model=CostStatsResponse)
async def get_user_costs(
    user_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost statistics for a specific user.

    Args:
        user_id: User UUID
        days: Number of days to look back (default: 30)

    Returns:
        Cost statistics for the user
    """
    # Check if user exists
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get stats
    return await get_cost_stats(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )


@router.get("/organization/{organization_id}", response_model=CostStatsResponse)
async def get_organization_costs(
    organization_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost statistics for a specific organization.

    Args:
        organization_id: Organization UUID
        days: Number of days to look back (default: 30)

    Returns:
        Cost statistics for the organization
    """
    # Check if organization exists
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get stats
    return await get_cost_stats(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )


@router.get("/summaries", response_model=List[CostSummaryResponse])
async def get_cost_summaries(
    summary_type: Optional[str] = Query(None, description="Filter by summary type (daily, weekly, monthly)"),
    squad_id: Optional[UUID] = Query(None, description="Filter by squad ID"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    provider: Optional[str] = Query(None, description="Filter by LLM provider"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum summaries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pre-aggregated cost summaries.

    Summaries are periodically generated for fast dashboard queries.
    Types: daily, weekly, monthly
    """
    # Build query
    query = select(LLMCostSummary).order_by(LLMCostSummary.summary_date.desc())

    # Apply filters
    filters = []
    if summary_type:
        filters.append(LLMCostSummary.summary_type == summary_type)
    if squad_id:
        filters.append(LLMCostSummary.squad_id == squad_id)
    if organization_id:
        filters.append(LLMCostSummary.organization_id == organization_id)
    if provider:
        filters.append(LLMCostSummary.provider == provider)
    if start_date:
        filters.append(LLMCostSummary.summary_date >= start_date)
    if end_date:
        filters.append(LLMCostSummary.summary_date <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    summaries = result.scalars().all()

    return summaries
