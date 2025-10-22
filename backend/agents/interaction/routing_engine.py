"""
Routing Engine

Determines which agent should respond to a question based on:
- Routing rules stored in the database
- Priority-based conflict resolution
- Fallback to default templates
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import RoutingRule, SquadMember, DefaultRoutingTemplate


class RoutingEngine:
    """
    Engine for routing questions to appropriate agents

    The routing engine queries the database for routing rules and determines
    the best agent to handle a question based on:
    - Asker role
    - Question type
    - Escalation level
    - Squad-specific vs organization-level rules
    - Priority-based conflict resolution
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the routing engine

        Args:
            db: Database session
        """
        self.db = db

    async def get_responder(
        self,
        squad_id: UUID,
        asker_role: str,
        question_type: str = "default",
        escalation_level: int = 0,
        organization_id: Optional[UUID] = None
    ) -> Optional[SquadMember]:
        """
        Get the appropriate responder for a question

        Args:
            squad_id: Squad ID
            asker_role: Role of the agent asking the question
            question_type: Type of question (implementation, architecture, etc.)
            escalation_level: Current escalation level (0 = first contact)
            organization_id: Organization ID (for org-level rules)

        Returns:
            SquadMember who should respond, or None if no rule found
        """
        # First, try to find a matching routing rule
        rule = await self._find_best_routing_rule(
            squad_id=squad_id,
            asker_role=asker_role,
            question_type=question_type,
            escalation_level=escalation_level,
            organization_id=organization_id
        )

        if rule is None:
            # No rule found - try with default question type
            if question_type != "default":
                rule = await self._find_best_routing_rule(
                    squad_id=squad_id,
                    asker_role=asker_role,
                    question_type="default",
                    escalation_level=escalation_level,
                    organization_id=organization_id
                )

        if rule is None:
            return None

        # If rule specifies a specific responder, use that
        if rule.specific_responder_id:
            stmt = select(SquadMember).where(
                SquadMember.id == rule.specific_responder_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        # Otherwise, find any available agent with the responder role
        stmt = select(SquadMember).where(
            and_(
                SquadMember.squad_id == squad_id,
                SquadMember.role == rule.responder_role,
                SquadMember.is_active == True
            )
        ).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_best_routing_rule(
        self,
        squad_id: UUID,
        asker_role: str,
        question_type: str,
        escalation_level: int,
        organization_id: Optional[UUID] = None
    ) -> Optional[RoutingRule]:
        """
        Find the best matching routing rule

        Rules are prioritized as follows:
        1. Squad-specific rules
        2. Organization-level rules
        3. Higher priority values
        4. Most recently created

        Args:
            squad_id: Squad ID
            asker_role: Role of asker
            question_type: Type of question
            escalation_level: Escalation level
            organization_id: Organization ID

        Returns:
            Best matching RoutingRule, or None
        """
        # Build query conditions
        conditions = [
            RoutingRule.asker_role == asker_role,
            RoutingRule.question_type == question_type,
            RoutingRule.escalation_level == escalation_level,
            RoutingRule.is_active == True
        ]

        # Add squad/org conditions
        if organization_id:
            conditions.append(
                or_(
                    RoutingRule.squad_id == squad_id,
                    RoutingRule.organization_id == organization_id
                )
            )
        else:
            conditions.append(RoutingRule.squad_id == squad_id)

        # Query for matching rules
        stmt = select(RoutingRule).where(
            and_(*conditions)
        ).order_by(
            # Prioritize squad-specific over org-level
            RoutingRule.squad_id.is_not(None).desc(),
            # Then by priority
            RoutingRule.priority.desc(),
            # Then by creation date (newer rules first)
            RoutingRule.created_at.desc()
        ).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_escalation_chain(
        self,
        squad_id: UUID,
        asker_role: str,
        question_type: str = "default",
        max_levels: int = 5,
        organization_id: Optional[UUID] = None
    ) -> List[dict]:
        """
        Get the complete escalation chain for a question

        Args:
            squad_id: Squad ID
            asker_role: Role of asker
            question_type: Type of question
            max_levels: Maximum escalation levels to retrieve
            organization_id: Organization ID

        Returns:
            List of escalation levels with responder roles
        """
        chain = []

        for level in range(max_levels):
            rule = await self._find_best_routing_rule(
                squad_id=squad_id,
                asker_role=asker_role,
                question_type=question_type,
                escalation_level=level,
                organization_id=organization_id
            )

            if rule is None:
                break

            chain.append({
                "escalation_level": level,
                "responder_role": rule.responder_role,
                "specific_responder_id": str(rule.specific_responder_id) if rule.specific_responder_id else None,
                "rule_id": str(rule.id),
                "priority": rule.priority
            })

        return chain

    async def apply_template_to_squad(
        self,
        template_id: UUID,
        squad_id: UUID,
        overwrite_existing: bool = False
    ) -> int:
        """
        Apply a routing template to a squad

        Args:
            template_id: ID of the template to apply
            squad_id: Squad to apply template to
            overwrite_existing: Whether to overwrite existing rules

        Returns:
            Number of rules created

        Raises:
            ValueError: If template not found
        """
        # Get template
        stmt = select(DefaultRoutingTemplate).where(
            DefaultRoutingTemplate.id == template_id
        )
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        # If overwrite, delete existing rules for this squad
        if overwrite_existing:
            from sqlalchemy import delete
            stmt = delete(RoutingRule).where(RoutingRule.squad_id == squad_id)
            await self.db.execute(stmt)

        # Create rules from template
        rules_created = 0

        for rule_def in template.routing_rules_template:
            rule = RoutingRule(
                squad_id=squad_id,
                asker_role=rule_def["asker_role"],
                question_type=rule_def["question_type"],
                escalation_level=rule_def["escalation_level"],
                responder_role=rule_def["responder_role"],
                is_active=True,
                priority=rule_def.get("priority", 0)
            )
            self.db.add(rule)
            rules_created += 1

        await self.db.commit()

        return rules_created

    async def validate_routing_config(
        self,
        squad_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> dict:
        """
        Validate routing configuration for a squad

        Checks for:
        - Missing escalation levels
        - Circular routing (same role at multiple levels)
        - Inactive responder roles

        Args:
            squad_id: Squad ID
            organization_id: Organization ID

        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []

        # Get all routing rules for this squad
        conditions = [RoutingRule.is_active == True]
        if organization_id:
            conditions.append(
                or_(
                    RoutingRule.squad_id == squad_id,
                    RoutingRule.organization_id == organization_id
                )
            )
        else:
            conditions.append(RoutingRule.squad_id == squad_id)

        stmt = select(RoutingRule).where(and_(*conditions))
        result = await self.db.execute(stmt)
        rules = result.scalars().all()

        if not rules:
            issues.append("No routing rules configured for this squad")
            return {
                "valid": False,
                "issues": issues,
                "warnings": warnings
            }

        # Group rules by asker_role and question_type
        rule_groups = {}
        for rule in rules:
            key = (rule.asker_role, rule.question_type)
            if key not in rule_groups:
                rule_groups[key] = []
            rule_groups[key].append(rule)

        # Check each group for escalation chain completeness
        for (asker_role, question_type), group_rules in rule_groups.items():
            escalation_levels = sorted([r.escalation_level for r in group_rules])

            # Check for gaps in escalation levels
            if escalation_levels[0] != 0:
                issues.append(
                    f"Missing level 0 routing rule for {asker_role} asking {question_type} questions"
                )

            for i in range(len(escalation_levels) - 1):
                if escalation_levels[i + 1] != escalation_levels[i] + 1:
                    warnings.append(
                        f"Gap in escalation chain for {asker_role} asking {question_type}: "
                        f"jumps from level {escalation_levels[i]} to {escalation_levels[i + 1]}"
                    )

            # Check for circular routing (same role at multiple levels)
            responder_roles = [r.responder_role for r in group_rules]
            if len(responder_roles) != len(set(responder_roles)):
                warnings.append(
                    f"Same responder role appears at multiple escalation levels for {asker_role} asking {question_type}"
                )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_rules": len(rules)
        }


def get_routing_engine(db: AsyncSession) -> RoutingEngine:
    """
    Factory function to create a RoutingEngine instance

    Args:
        db: Database session

    Returns:
        RoutingEngine instance
    """
    return RoutingEngine(db)
