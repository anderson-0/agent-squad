"""
Squad Member Pydantic Schemas

Request/response schemas for Squad Member (Agent) API endpoints.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SquadMemberBase(BaseModel):
    """Base squad member schema"""
    role: str = Field(
        ...,
        description="Agent role (project_manager, tech_lead, backend_developer, etc.)"
    )
    specialization: Optional[str] = Field(
        None,
        max_length=200,
        description="Agent specialization"
    )
    llm_provider: str = Field(
        default="openai",
        pattern="^(openai|anthropic|groq)$",
        description="LLM provider"
    )
    llm_model: str = Field(
        default="gpt-4",
        description="LLM model to use"
    )


class SquadMemberCreate(SquadMemberBase):
    """Schema for creating a squad member"""
    squad_id: UUID = Field(..., description="Squad to add member to")
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent configuration"
    )


class SquadMemberUpdate(BaseModel):
    """Schema for updating a squad member"""
    specialization: Optional[str] = Field(None, max_length=200)
    llm_provider: Optional[str] = Field(None, pattern="^(openai|anthropic|groq)$")
    llm_model: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SquadMemberResponse(SquadMemberBase):
    """Schema for squad member response"""
    id: UUID
    squad_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SquadMemberWithConfig(SquadMemberResponse):
    """Squad member response with full configuration"""
    config: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: Optional[str] = Field(None, description="Agent system prompt")


class SquadMemberSummary(BaseModel):
    """Summary of a squad member in composition"""
    id: UUID
    role: str
    specialization: Optional[str]
    llm_provider: str
    llm_model: str


class SquadComposition(BaseModel):
    """Squad composition summary"""
    squad_id: UUID
    total_members: int
    active_members: int
    roles: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of members by role"
    )
    llm_providers: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of members by LLM provider"
    )
    members: List[SquadMemberSummary] = Field(
        default_factory=list,
        description="List of members"
    )
