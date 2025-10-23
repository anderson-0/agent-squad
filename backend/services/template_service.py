"""
Template Service

Handles application of complete squad templates including:
- Agent creation
- Routing rule setup
- System prompt assignment
- Template management
"""
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.squad_template import SquadTemplate
from backend.models import Squad, SquadMember
from backend.models.routing_rule import RoutingRule
from backend.services.agent_service import AgentService


class TemplateService:
    """Service for managing and applying squad templates"""

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        category: Optional[str] = None,
        featured_only: bool = False
    ) -> List[SquadTemplate]:
        """
        List available squad templates

        Args:
            db: Database session
            category: Filter by category (e.g., 'development', 'support')
            featured_only: Only show featured templates

        Returns:
            List of templates ordered by popularity
        """
        stmt = select(SquadTemplate).where(SquadTemplate.is_active == True)

        if category:
            stmt = stmt.where(SquadTemplate.category == category)

        if featured_only:
            stmt = stmt.where(SquadTemplate.is_featured == True)

        # Order by usage count (most popular first)
        stmt = stmt.order_by(SquadTemplate.usage_count.desc())

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: UUID
    ) -> Optional[SquadTemplate]:
        """
        Get template by ID

        Args:
            db: Database session
            template_id: UUID of template

        Returns:
            Template if found, None otherwise
        """
        stmt = select(SquadTemplate).where(SquadTemplate.id == template_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_template_by_slug(
        db: AsyncSession,
        slug: str
    ) -> Optional[SquadTemplate]:
        """
        Get template by slug

        Args:
            db: Database session
            slug: Template slug (e.g., 'software-dev-squad')

        Returns:
            Template if found, None otherwise
        """
        stmt = select(SquadTemplate).where(SquadTemplate.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def apply_template(
        db: AsyncSession,
        template_id: UUID,
        squad_id: UUID,
        user_id: UUID,
        customization: Optional[Dict] = None
    ) -> Dict:
        """
        Apply a complete template to a squad

        Args:
            db: Database session
            template_id: Template to apply
            squad_id: Target squad
            user_id: User applying template
            customization: Optional overrides for template
                - agents: List of agent customizations
                - routing_rules: List of routing rule customizations

        Returns:
            Dictionary with created agents and rules

        Raises:
            ValueError: If template not found
        """
        # Get template
        template = await TemplateService.get_template(db, template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        template_def = template.template_definition.copy()

        # Apply customizations
        if customization:
            if 'agents' in customization:
                template_def['agents'] = customization['agents']
            if 'routing_rules' in customization:
                template_def['routing_rules'] = customization['routing_rules']

        # Verify squad exists
        stmt = select(Squad).where(Squad.id == squad_id)
        result = await db.execute(stmt)
        squad = result.scalar_one_or_none()
        if not squad:
            raise ValueError(f"Squad not found: {squad_id}")

        # Create agents
        created_agents = []
        for agent_def in template_def.get('agents', []):
            agent = await AgentService.create_squad_member(
                db=db,
                squad_id=squad_id,
                role=agent_def['role'],
                specialization=agent_def.get('specialization'),
                llm_provider=agent_def.get('llm_provider', 'openai'),
                llm_model=agent_def.get('llm_model', 'gpt-4'),
                custom_system_prompt=None  # Will load from roles/ directory
            )
            created_agents.append(agent)

        await db.flush()

        # Create routing rules
        created_rules = []
        for rule_def in template_def.get('routing_rules', []):
            rule = RoutingRule(
                id=uuid4(),
                squad_id=squad_id,
                asker_role=rule_def['asker_role'],
                question_type=rule_def['question_type'],
                escalation_level=rule_def['escalation_level'],
                responder_role=rule_def['responder_role'],
                is_active=True,
                priority=rule_def.get('priority', 10),
                rule_metadata={}
            )
            db.add(rule)
            created_rules.append(rule)

        await db.commit()

        # Update template usage
        template.usage_count += 1
        await db.commit()

        return {
            "success": True,
            "template_name": template.name,
            "template_slug": template.slug,
            "agents_created": len(created_agents),
            "rules_created": len(created_rules),
            "agents": [
                {
                    "id": str(a.id),
                    "role": a.role,
                    "specialization": a.specialization,
                    "llm_provider": a.llm_provider,
                    "llm_model": a.llm_model
                }
                for a in created_agents
            ],
            "routing_rules": [
                {
                    "asker_role": r.asker_role,
                    "responder_role": r.responder_role,
                    "question_type": r.question_type,
                    "escalation_level": r.escalation_level
                }
                for r in created_rules
            ]
        }

    @staticmethod
    async def create_template(
        db: AsyncSession,
        name: str,
        slug: str,
        description: str,
        category: str,
        template_definition: Dict,
        is_featured: bool = False
    ) -> SquadTemplate:
        """
        Create a new squad template

        Args:
            db: Database session
            name: Template name
            slug: URL-friendly slug
            description: Template description
            category: Template category
            template_definition: Complete template definition
            is_featured: Whether to feature this template

        Returns:
            Created template

        Raises:
            ValueError: If slug already exists
        """
        # Check if slug exists
        existing = await TemplateService.get_template_by_slug(db, slug)
        if existing:
            raise ValueError(f"Template with slug '{slug}' already exists")

        template = SquadTemplate(
            id=uuid4(),
            name=name,
            slug=slug,
            description=description,
            category=category,
            is_active=True,
            is_featured=is_featured,
            template_definition=template_definition,
            usage_count=0,
            avg_rating=0.0
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return template

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: UUID,
        updates: Dict
    ) -> Optional[SquadTemplate]:
        """
        Update a template

        Args:
            db: Database session
            template_id: Template to update
            updates: Fields to update

        Returns:
            Updated template if found, None otherwise
        """
        template = await TemplateService.get_template(db, template_id)
        if not template:
            return None

        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'category', 'is_active',
            'is_featured', 'template_definition'
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(template, field, value)

        await db.commit()
        await db.refresh(template)

        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: UUID
    ) -> bool:
        """
        Delete a template (soft delete - mark as inactive)

        Args:
            db: Database session
            template_id: Template to delete

        Returns:
            True if deleted, False if not found
        """
        template = await TemplateService.get_template(db, template_id)
        if not template:
            return False

        template.is_active = False
        await db.commit()

        return True
