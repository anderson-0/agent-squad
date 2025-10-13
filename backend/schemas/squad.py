"""
Squad Pydantic Schemas

Request/response schemas for Squad API endpoints.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SquadBase(BaseModel):
    """Base squad schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Squad name")
    description: Optional[str] = Field(None, max_length=500, description="Squad description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Squad configuration")


class SquadCreate(SquadBase):
    """Schema for creating a squad"""
    org_id: Optional[UUID] = Field(None, description="Organization ID (optional)", alias="organization_id")


class SquadUpdate(BaseModel):
    """Schema for updating a squad"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(active|paused|archived)$")
    config: Optional[Dict[str, Any]] = None


class SquadResponse(SquadBase):
    """Schema for squad response"""
    id: UUID
    user_id: UUID
    org_id: Optional[UUID] = Field(None, alias="organization_id")
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SquadMemberSummary(BaseModel):
    """Summary of a squad member"""
    id: UUID
    role: str
    specialization: Optional[str]
    llm_provider: str
    llm_model: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SquadWithAgents(BaseModel):
    """Squad response with all agents"""
    member_count: int = Field(0, description="Total number of members")
    active_member_count: int = Field(0, description="Number of active members")
    squad: SquadResponse
    members: List[SquadMemberSummary] = Field(default_factory=list)


class SquadCostEstimate(BaseModel):
    """Squad cost estimate"""
    squad_id: UUID
    total_monthly_cost: float = Field(..., description="Total estimated monthly cost in USD")
    cost_by_model: List[Dict[str, Any]] = Field(default_factory=list, description="Cost breakdown by LLM model")
    member_count: int = Field(..., description="Number of agents")
    note: str = Field(..., description="Cost calculation note")
