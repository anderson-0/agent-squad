"""
Routing Rules API Endpoints

Endpoints for managing agent interaction routing rules, templates,
and escalation chains.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models import RoutingRule, DefaultRoutingTemplate
from backend.agents.interaction.routing_engine import RoutingEngine
from backend.agents.interaction.seed_routing_templates import (
    create_default_templates,
    get_template_by_name
)
from backend.services.squad_service import SquadService


router = APIRouter(prefix="/routing-rules", tags=["routing-rules"])


@router.post(
    "/squads/{squad_id}/rules",
    status_code=status.HTTP_201_CREATED,
    summary="Create routing rule",
    description="Create a new routing rule for a squad"
)
async def create_routing_rule(
    squad_id: UUID,
    asker_role: str,
    question_type: str,
    escalation_level: int,
    responder_role: str,
    priority: int = 0,
    specific_responder_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new routing rule for a squad.

    - **squad_id**: UUID of the squad
    - **asker_role**: Role of the agent asking questions
    - **question_type**: Type of question (implementation, architecture, etc.)
    - **escalation_level**: Escalation level (0 = first contact, 1+ = escalated)
    - **responder_role**: Role of the agent who should respond
    - **priority**: Rule priority (higher = takes precedence)
    - **specific_responder_id**: Optional specific agent to route to

    Returns the created routing rule.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Create routing rule
    from uuid import uuid4
    rule = RoutingRule(
        id=uuid4(),
        squad_id=squad_id,
        asker_role=asker_role,
        question_type=question_type,
        escalation_level=escalation_level,
        responder_role=responder_role,
        specific_responder_id=specific_responder_id,
        priority=priority,
        is_active=True
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {
        "id": str(rule.id),
        "squad_id": str(rule.squad_id),
        "asker_role": rule.asker_role,
        "question_type": rule.question_type,
        "escalation_level": rule.escalation_level,
        "responder_role": rule.responder_role,
        "specific_responder_id": str(rule.specific_responder_id) if rule.specific_responder_id else None,
        "priority": rule.priority,
        "is_active": rule.is_active
    }


@router.get(
    "/squads/{squad_id}/rules",
    summary="List routing rules",
    description="Get all routing rules for a squad"
)
async def list_routing_rules(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    asker_role: str | None = Query(None, description="Filter by asker role"),
    question_type: str | None = Query(None, description="Filter by question type"),
    escalation_level: int | None = Query(None, description="Filter by escalation level"),
) -> List[Dict[str, Any]]:
    """
    List all routing rules for a squad.

    Supports filtering by:
    - **asker_role**: Filter by asker role
    - **question_type**: Filter by question type
    - **escalation_level**: Filter by escalation level
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Build query
    from sqlalchemy import and_
    conditions = [RoutingRule.squad_id == squad_id]

    if asker_role:
        conditions.append(RoutingRule.asker_role == asker_role)
    if question_type:
        conditions.append(RoutingRule.question_type == question_type)
    if escalation_level is not None:
        conditions.append(RoutingRule.escalation_level == escalation_level)

    stmt = select(RoutingRule).where(and_(*conditions)).order_by(
        RoutingRule.priority.desc(),
        RoutingRule.escalation_level
    )

    result = await db.execute(stmt)
    rules = result.scalars().all()

    return [
        {
            "id": str(rule.id),
            "squad_id": str(rule.squad_id),
            "asker_role": rule.asker_role,
            "question_type": rule.question_type,
            "escalation_level": rule.escalation_level,
            "responder_role": rule.responder_role,
            "specific_responder_id": str(rule.specific_responder_id) if rule.specific_responder_id else None,
            "priority": rule.priority,
            "is_active": rule.is_active
        }
        for rule in rules
    ]


@router.get(
    "/squads/{squad_id}/escalation-chain",
    summary="Get escalation chain",
    description="Get the complete escalation chain for a question type"
)
async def get_escalation_chain(
    squad_id: UUID,
    asker_role: str,
    question_type: str = "default",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get the complete escalation chain for a question.

    - **squad_id**: UUID of the squad
    - **asker_role**: Role of the agent asking
    - **question_type**: Type of question

    Returns list of escalation levels with responder roles.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get escalation chain
    routing_engine = RoutingEngine(db)
    chain = await routing_engine.get_escalation_chain(
        squad_id=squad_id,
        asker_role=asker_role,
        question_type=question_type
    )

    return chain


@router.post(
    "/squads/{squad_id}/validate",
    summary="Validate routing configuration",
    description="Validate the routing configuration for a squad"
)
async def validate_routing_config(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate routing configuration for a squad.

    Checks for:
    - Missing escalation levels
    - Circular routing
    - Inactive responder roles

    Returns validation results with issues and warnings.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Validate configuration
    routing_engine = RoutingEngine(db)
    validation_result = await routing_engine.validate_routing_config(squad_id=squad_id)

    return validation_result


@router.post(
    "/squads/{squad_id}/apply-template/{template_id}",
    summary="Apply routing template",
    description="Apply a routing template to create rules for a squad"
)
async def apply_template_to_squad(
    squad_id: UUID,
    template_id: UUID,
    overwrite_existing: bool = Query(False, description="Overwrite existing rules"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Apply a routing template to a squad.

    - **squad_id**: UUID of the squad
    - **template_id**: UUID of the template to apply
    - **overwrite_existing**: Whether to overwrite existing rules (default: False)

    Returns number of rules created.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Apply template
    routing_engine = RoutingEngine(db)
    rules_created = await routing_engine.apply_template_to_squad(
        template_id=template_id,
        squad_id=squad_id,
        overwrite_existing=overwrite_existing
    )

    return {
        "squad_id": str(squad_id),
        "template_id": str(template_id),
        "rules_created": rules_created,
        "overwrite_existing": overwrite_existing
    }


@router.get(
    "/templates",
    summary="List routing templates",
    description="Get all available routing templates"
)
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all available routing templates.

    Returns all templates with their descriptions and rule counts.
    """
    stmt = select(DefaultRoutingTemplate).where(
        DefaultRoutingTemplate.is_active == True
    )
    result = await db.execute(stmt)
    templates = result.scalars().all()

    return [
        {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "rule_count": len(template.routing_rules_template),
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat() if template.created_at else None
        }
        for template in templates
    ]


@router.get(
    "/templates/{template_id}",
    summary="Get template details",
    description="Get detailed information about a routing template"
)
async def get_template_details(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed information about a routing template.

    - **template_id**: UUID of the template

    Returns template with full rule definitions.
    """
    stmt = select(DefaultRoutingTemplate).where(
        DefaultRoutingTemplate.id == template_id
    )
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "routing_rules_template": template.routing_rules_template,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat() if template.created_at else None
    }


@router.post(
    "/templates/seed",
    summary="Seed default templates",
    description="Create default routing templates (admin only)"
)
async def seed_default_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Seed the database with default routing templates.

    This endpoint creates the standard routing templates if they don't exist.
    Useful for initial setup or resetting templates.

    Returns list of created templates.
    """
    # Create default templates
    templates = await create_default_templates(db)

    return {
        "success": True,
        "templates_created": len(templates),
        "template_names": [t.name for t in templates],
        "template_ids": [str(t.id) for t in templates]
    }


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete routing rule",
    description="Delete a routing rule"
)
async def delete_routing_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a routing rule.

    - **rule_id**: UUID of the rule to delete

    Verifies squad ownership before deletion.
    """
    # Get rule
    stmt = select(RoutingRule).where(RoutingRule.id == rule_id)
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing rule {rule_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, rule.squad_id, current_user.id)

    # Delete rule
    await db.delete(rule)
    await db.commit()


@router.patch(
    "/rules/{rule_id}/toggle",
    summary="Toggle routing rule active status",
    description="Activate or deactivate a routing rule"
)
async def toggle_routing_rule(
    rule_id: UUID,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Toggle a routing rule's active status.

    - **rule_id**: UUID of the rule
    - **is_active**: New active status

    Returns updated rule.
    """
    # Get rule
    stmt = select(RoutingRule).where(RoutingRule.id == rule_id)
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing rule {rule_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, rule.squad_id, current_user.id)

    # Update rule
    rule.is_active = is_active
    await db.commit()
    await db.refresh(rule)

    return {
        "id": str(rule.id),
        "is_active": rule.is_active,
        "squad_id": str(rule.squad_id),
        "asker_role": rule.asker_role,
        "responder_role": rule.responder_role
    }
