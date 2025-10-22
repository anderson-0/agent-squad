"""
Routing Rule Schemas

Pydantic schemas for customizable agent routing hierarchies.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# Routing Rule Schemas

class RoutingRuleBase(BaseModel):
    """Base routing rule schema"""
    asker_role: str = Field(..., description="Role of the agent asking the question")
    question_type: str = Field(..., description="Type of question (implementation, architecture, default, etc.)")
    escalation_level: int = Field(default=0, ge=0, description="0 = first contact, 1 = second contact, etc.")
    responder_role: str = Field(..., description="Role of the agent who should respond")
    specific_responder_id: Optional[UUID] = Field(None, description="Specific agent ID (optional, otherwise any agent with the role)")
    is_active: bool = Field(default=True, description="Whether this rule is active")
    priority: int = Field(default=0, description="Priority for conflict resolution (higher = higher priority)")
    rule_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class RoutingRuleCreate(RoutingRuleBase):
    """Schema for creating a routing rule"""
    squad_id: Optional[UUID] = Field(None, description="Squad-specific rule (takes precedence over org-level)")
    organization_id: Optional[UUID] = Field(None, description="Organization-level rule")

    @field_validator('squad_id', 'organization_id')
    @classmethod
    def check_scope(cls, v, info):
        """At least one of squad_id or organization_id must be set"""
        values = info.data
        if not values.get('squad_id') and not values.get('organization_id'):
            raise ValueError('Either squad_id or organization_id must be provided')
        return v


class RoutingRuleUpdate(BaseModel):
    """Schema for updating a routing rule"""
    asker_role: Optional[str] = None
    question_type: Optional[str] = None
    escalation_level: Optional[int] = None
    responder_role: Optional[str] = None
    specific_responder_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    rule_metadata: Optional[Dict[str, Any]] = None


class RoutingRuleResponse(RoutingRuleBase):
    """Schema for routing rule responses"""
    id: UUID
    squad_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoutingRuleWithDetails(RoutingRuleResponse):
    """Routing rule with additional details"""
    squad_name: Optional[str] = None
    organization_name: Optional[str] = None
    specific_responder_name: Optional[str] = None


# Routing Template Schemas

class RoutingRuleDefinition(BaseModel):
    """Single routing rule definition for templates"""
    asker_role: str
    question_type: str
    escalation_level: int
    responder_role: str


class DefaultRoutingTemplateBase(BaseModel):
    """Base default routing template schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    template_type: str = Field(..., description="Type of template (software, devops, ml, etc.)")
    routing_rules_template: List[RoutingRuleDefinition] = Field(..., description="List of routing rules")
    is_public: bool = Field(default=True, description="Whether other orgs can use this template")
    is_default: bool = Field(default=False, description="Whether this is the default template for new squads")


class DefaultRoutingTemplateCreate(DefaultRoutingTemplateBase):
    """Schema for creating a default routing template"""
    created_by_org_id: Optional[UUID] = Field(None, description="Organization that created this template")


class DefaultRoutingTemplateUpdate(BaseModel):
    """Schema for updating a default routing template"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    routing_rules_template: Optional[List[RoutingRuleDefinition]] = None
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None


class DefaultRoutingTemplateResponse(DefaultRoutingTemplateBase):
    """Schema for default routing template responses"""
    id: UUID
    created_by_org_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API Request/Response Schemas

class ApplyTemplateRequest(BaseModel):
    """Request to apply a routing template to a squad"""
    squad_id: UUID = Field(..., description="Squad to apply the template to")
    template_id: UUID = Field(..., description="Template to apply")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing rules")


class ApplyTemplateResponse(BaseModel):
    """Response after applying a template"""
    squad_id: UUID
    template_id: UUID
    rules_created: int
    rules_updated: int
    rules_deactivated: int


class RoutingChainRequest(BaseModel):
    """Request to get the routing chain for a specific scenario"""
    asker_role: str
    question_type: str
    squad_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None


class RoutingChainStep(BaseModel):
    """Single step in a routing chain"""
    escalation_level: int
    responder_role: str
    specific_responder_id: Optional[UUID] = None
    rule_id: Optional[UUID] = None


class RoutingChainResponse(BaseModel):
    """Response with the full routing chain"""
    asker_role: str
    question_type: str
    chain: List[RoutingChainStep] = Field(..., description="Ordered list of escalation steps")
    total_levels: int


class BulkCreateRoutingRulesRequest(BaseModel):
    """Request to create multiple routing rules at once"""
    squad_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    rules: List[RoutingRuleBase] = Field(..., min_length=1, description="List of rules to create")


class BulkCreateRoutingRulesResponse(BaseModel):
    """Response after bulk creating routing rules"""
    created_count: int
    rules: List[RoutingRuleResponse]


class RoutingRuleStats(BaseModel):
    """Statistics about routing rules"""
    total_rules: int
    rules_by_question_type: Dict[str, int]
    rules_by_asker_role: Dict[str, int]
    rules_by_responder_role: Dict[str, int]
    active_rules: int
    inactive_rules: int
    squad_specific_rules: int
    org_level_rules: int


class ValidateRoutingConfigRequest(BaseModel):
    """Request to validate a routing configuration"""
    squad_id: UUID
    check_completeness: bool = Field(default=True, description="Check if all roles have routing rules")
    check_cycles: bool = Field(default=True, description="Check for circular routing")


class RoutingConfigIssue(BaseModel):
    """Single issue in routing configuration"""
    severity: str = Field(..., description="error, warning, or info")
    issue_type: str = Field(..., description="Type of issue (missing_rule, circular_routing, etc.)")
    description: str
    affected_roles: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None


class ValidateRoutingConfigResponse(BaseModel):
    """Response after validating routing configuration"""
    squad_id: UUID
    is_valid: bool
    issues: List[RoutingConfigIssue] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
