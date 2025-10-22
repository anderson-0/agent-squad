"""
Seed Routing Templates

Creates default routing templates for common hierarchical agent interaction patterns.

These templates can be applied to squads to quickly set up routing rules
without manually configuring each rule.
"""
from uuid import uuid4
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import DefaultRoutingTemplate
from backend.core.database import get_async_session_context


# Default routing template definitions
DEFAULT_TEMPLATES = [
    {
        "name": "Standard Software Development Squad",
        "description": (
            "Standard routing for a software development squad with developers, "
            "tech leads, solution architects, and project managers. "
            "Developers ask tech leads, tech leads ask solution architects, "
            "solution architects ask project managers."
        ),
        "routing_rules_template": [
            # Developer questions
            # Level 0: Developer -> Tech Lead
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "backend_developer",
                "question_type": "implementation",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "backend_developer",
                "question_type": "code_review",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "implementation",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },

            # Level 1: Developer -> Solution Architect (escalated)
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "backend_developer",
                "question_type": "architecture",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "architecture",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },

            # Level 2: Developer -> Project Manager (final escalation)
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 2,
                "responder_role": "project_manager",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 2,
                "responder_role": "project_manager",
                "priority": 10
            },

            # Tech Lead questions
            # Level 0: Tech Lead -> Solution Architect
            {
                "asker_role": "tech_lead",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "tech_lead",
                "question_type": "architecture",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "tech_lead",
                "question_type": "design_decision",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },

            # Level 1: Tech Lead -> Project Manager (escalated)
            {
                "asker_role": "tech_lead",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "project_manager",
                "priority": 10
            },

            # Solution Architect questions
            # Level 0: Solution Architect -> Project Manager
            {
                "asker_role": "solution_architect",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "project_manager",
                "priority": 10
            },
            {
                "asker_role": "solution_architect",
                "question_type": "business_requirement",
                "escalation_level": 0,
                "responder_role": "project_manager",
                "priority": 10
            },
            {
                "asker_role": "solution_architect",
                "question_type": "resource_allocation",
                "escalation_level": 0,
                "responder_role": "project_manager",
                "priority": 10
            },

            # QA Tester questions
            # Level 0: Tester -> Tech Lead
            {
                "asker_role": "tester",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "tester",
                "question_type": "bug_verification",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "tester",
                "question_type": "test_strategy",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },

            # Level 1: Tester -> Solution Architect (escalated)
            {
                "asker_role": "tester",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 10
            },
        ]
    },
    {
        "name": "Peer Review Squad",
        "description": (
            "Flat structure where developers ask each other for peer reviews. "
            "Escalates to tech lead if no peer available."
        ),
        "routing_rules_template": [
            # Level 0: Developer -> Another Developer (peer review)
            {
                "asker_role": "backend_developer",
                "question_type": "code_review",
                "escalation_level": 0,
                "responder_role": "backend_developer",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "code_review",
                "escalation_level": 0,
                "responder_role": "frontend_developer",
                "priority": 10
            },

            # Level 1: Developer -> Tech Lead (escalated peer review)
            {
                "asker_role": "backend_developer",
                "question_type": "code_review",
                "escalation_level": 1,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "code_review",
                "escalation_level": 1,
                "responder_role": "tech_lead",
                "priority": 10
            },
        ]
    },
    {
        "name": "AI/ML Squad",
        "description": (
            "Routing for AI/ML development squads. AI engineers ask senior AI engineers, "
            "who escalate to solution architects for infrastructure questions."
        ),
        "routing_rules_template": [
            # Level 0: AI Engineer -> Senior AI Engineer
            {
                "asker_role": "ai_engineer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",  # Tech lead acts as senior in this context
                "priority": 10
            },
            {
                "asker_role": "ai_engineer",
                "question_type": "model_training",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "ai_engineer",
                "question_type": "model_deployment",
                "escalation_level": 0,
                "responder_role": "devops_engineer",
                "priority": 10
            },

            # Level 1: AI Engineer -> Solution Architect
            {
                "asker_role": "ai_engineer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "ai_engineer",
                "question_type": "infrastructure",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
        ]
    },
    {
        "name": "DevOps Squad",
        "description": (
            "Routing for DevOps-focused squads. Developers ask DevOps engineers "
            "for deployment and infrastructure questions."
        ),
        "routing_rules_template": [
            # Level 0: Developer -> DevOps Engineer
            {
                "asker_role": "backend_developer",
                "question_type": "deployment",
                "escalation_level": 0,
                "responder_role": "devops_engineer",
                "priority": 10
            },
            {
                "asker_role": "backend_developer",
                "question_type": "infrastructure",
                "escalation_level": 0,
                "responder_role": "devops_engineer",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "deployment",
                "escalation_level": 0,
                "responder_role": "devops_engineer",
                "priority": 10
            },

            # Level 1: DevOps questions -> Solution Architect
            {
                "asker_role": "devops_engineer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
            {
                "asker_role": "devops_engineer",
                "question_type": "architecture",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 10
            },
        ]
    },
    {
        "name": "Full Stack Squad",
        "description": (
            "Small squad where full-stack developers help each other, "
            "escalating to a tech lead/architect hybrid role."
        ),
        "routing_rules_template": [
            # Level 0: Developer -> Tech Lead
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },

            # Level 1: All questions -> Project Manager (final authority)
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "project_manager",
                "priority": 10
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "project_manager",
                "priority": 10
            },
            {
                "asker_role": "tech_lead",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "project_manager",
                "priority": 10
            },
        ]
    }
]


async def create_default_templates(db: AsyncSession) -> List[DefaultRoutingTemplate]:
    """
    Create default routing templates in the database

    Args:
        db: Database session

    Returns:
        List of created templates
    """
    templates = []

    for template_def in DEFAULT_TEMPLATES:
        template = DefaultRoutingTemplate(
            id=uuid4(),
            name=template_def["name"],
            description=template_def["description"],
            routing_rules_template=template_def["routing_rules_template"],
            is_active=True
        )
        db.add(template)
        templates.append(template)

    await db.commit()

    for template in templates:
        await db.refresh(template)

    return templates


async def seed_routing_templates() -> dict:
    """
    Main function to seed routing templates

    Returns:
        Dictionary with seeding results
    """
    async with get_async_session_context() as db:
        templates = await create_default_templates(db)

        return {
            "success": True,
            "templates_created": len(templates),
            "template_names": [t.name for t in templates],
            "template_ids": [str(t.id) for t in templates]
        }


async def get_template_by_name(name: str) -> DefaultRoutingTemplate:
    """
    Get a template by name

    Args:
        name: Template name

    Returns:
        Template object or None
    """
    from sqlalchemy import select

    async with get_async_session_context() as db:
        stmt = select(DefaultRoutingTemplate).where(
            DefaultRoutingTemplate.name == name
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


if __name__ == "__main__":
    """
    Run this script to seed the database with default routing templates

    Usage:
        python -m backend.agents.interaction.seed_routing_templates
    """
    import asyncio

    result = asyncio.run(seed_routing_templates())
    print(f"\n✓ Seeding complete!")
    print(f"  Created {result['templates_created']} templates:")
    for name in result['template_names']:
        print(f"    - {name}")
