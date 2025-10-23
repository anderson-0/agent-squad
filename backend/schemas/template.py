"""
Template Schemas

Pydantic schemas for template API requests/responses
"""
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TemplateListResponse(BaseModel):
    """Response for listing templates"""
    id: UUID
    name: str
    slug: str
    description: str
    category: str
    is_featured: bool
    usage_count: int
    avg_rating: Optional[float] = None

    class Config:
        from_attributes = True


class AgentDefinition(BaseModel):
    """Agent definition in template"""
    role: str
    specialization: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    description: Optional[str] = None


class RoutingRuleDefinition(BaseModel):
    """Routing rule definition in template"""
    asker_role: str
    question_type: str
    escalation_level: int
    responder_role: str
    priority: int = 10
    description: Optional[str] = None


class SuccessMetric(BaseModel):
    """Success metric for template"""
    name: str
    target: float
    unit: str
    description: Optional[str] = None


class ExampleConversation(BaseModel):
    """Example conversation for template"""
    title: str
    description: Optional[str] = None
    participants: List[str]
    messages: List[Dict[str, Any]]


class TemplateDefinition(BaseModel):
    """Complete template definition"""
    agents: List[AgentDefinition]
    routing_rules: List[RoutingRuleDefinition]
    success_metrics: Optional[List[SuccessMetric]] = None
    example_conversations: Optional[List[ExampleConversation]] = None
    use_cases: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class TemplateDetailResponse(BaseModel):
    """Detailed template response"""
    id: UUID
    name: str
    slug: str
    description: str
    category: str
    is_featured: bool
    template_definition: Dict[str, Any]
    usage_count: int
    avg_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplyTemplateRequest(BaseModel):
    """Request to apply template to squad"""
    squad_id: UUID
    user_id: UUID
    customization: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional customizations to template (agents, routing_rules)"
    )


class CreatedAgent(BaseModel):
    """Agent created from template"""
    id: str
    role: str
    specialization: Optional[str]
    llm_provider: str
    llm_model: str


class CreatedRoutingRule(BaseModel):
    """Routing rule created from template"""
    asker_role: str
    responder_role: str
    question_type: str
    escalation_level: int


class ApplyTemplateResponse(BaseModel):
    """Response from applying template"""
    success: bool
    template_name: str
    template_slug: str
    agents_created: int
    rules_created: int
    agents: List[CreatedAgent]
    routing_rules: List[CreatedRoutingRule]


class CreateTemplateRequest(BaseModel):
    """Request to create new template"""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: str = Field(..., min_length=1, max_length=1000)
    category: str = Field(..., min_length=1, max_length=50)
    is_featured: bool = False
    template_definition: TemplateDefinition


class UpdateTemplateRequest(BaseModel):
    """Request to update template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    template_definition: Optional[Dict[str, Any]] = None
