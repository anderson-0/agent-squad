"""
Unit tests for RoutingRule and DefaultRoutingTemplate models
"""
import pytest
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    RoutingRule,
    DefaultRoutingTemplate,
    SquadMember
)


class TestRoutingRuleModel:
    """Tests for RoutingRule model"""

    @pytest.mark.asyncio
    async def test_create_squad_routing_rule(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test creating a squad-specific routing rule"""
        # Create routing rule
        rule = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="tech_lead",
            is_active=True,
            priority=0
        )

        test_db.add(rule)
        await test_db.commit()
        await test_db.refresh(rule)

        # Verify
        assert rule.id is not None
        assert rule.squad_id == test_squad.id
        assert rule.organization_id is None
        assert rule.asker_role == "backend_developer"
        assert rule.question_type == "implementation"
        assert rule.escalation_level == 0
        assert rule.responder_role == "tech_lead"
        assert rule.specific_responder_id is None
        assert rule.is_active is True
        assert rule.priority == 0
        assert rule.created_at is not None
        assert rule.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_org_routing_rule(
        self,
        test_db: AsyncSession,
        test_organization
    ):
        """Test creating an organization-level routing rule"""
        # Create org-level rule (applies to all squads in org)
        rule = RoutingRule(
            id=uuid4(),
            organization_id=test_organization.id,
            asker_role="frontend_developer",
            question_type="design",
            escalation_level=0,
            responder_role="designer",
            is_active=True,
            priority=0
        )

        test_db.add(rule)
        await test_db.commit()
        await test_db.refresh(rule)

        # Verify
        assert rule.organization_id == test_organization.id
        assert rule.squad_id is None

    @pytest.mark.asyncio
    async def test_routing_rule_with_specific_responder(
        self,
        test_db: AsyncSession,
        test_squad,
        test_squad_member_tech_lead
    ):
        """Test routing to a specific agent instead of any agent with a role"""
        # Create rule targeting specific agent
        rule = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="critical_bug",
            escalation_level=0,
            responder_role="tech_lead",
            specific_responder_id=test_squad_member_tech_lead.id,  # Route to this specific tech lead
            is_active=True,
            priority=10  # Higher priority
        )

        test_db.add(rule)
        await test_db.commit()
        await test_db.refresh(rule)

        # Verify
        assert rule.specific_responder_id == test_squad_member_tech_lead.id
        assert rule.priority == 10

    @pytest.mark.asyncio
    async def test_routing_rule_priority_system(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test priority-based conflict resolution when multiple rules match"""
        # Create multiple rules that could match the same query
        # Lower priority (default) rule
        rule1 = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="tech_lead",
            is_active=True,
            priority=0
        )

        # Higher priority (specific) rule
        rule2 = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="solution_architect",  # Different responder
            is_active=True,
            priority=10  # Higher priority wins
        )

        test_db.add_all([rule1, rule2])
        await test_db.commit()

        # Query for matching rules, ordered by priority
        stmt = select(RoutingRule).where(
            and_(
                RoutingRule.squad_id == test_squad.id,
                RoutingRule.asker_role == "backend_developer",
                RoutingRule.question_type == "implementation",
                RoutingRule.escalation_level == 0,
                RoutingRule.is_active == True
            )
        ).order_by(RoutingRule.priority.desc())

        result = await test_db.execute(stmt)
        matching_rules = result.scalars().all()

        # Verify highest priority rule is first
        assert len(matching_rules) == 2
        assert matching_rules[0].id == rule2.id  # Higher priority
        assert matching_rules[0].responder_role == "solution_architect"
        assert matching_rules[1].id == rule1.id

    @pytest.mark.asyncio
    async def test_routing_rule_escalation_chain(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test creating a complete escalation chain"""
        # Level 0: Backend Dev → Tech Lead
        rule_level0 = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="tech_lead",
            is_active=True,
            priority=0
        )

        # Level 1: Backend Dev → Solution Architect (escalated)
        rule_level1 = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=1,
            responder_role="solution_architect",
            is_active=True,
            priority=0
        )

        # Level 2: Backend Dev → Project Manager (escalated again)
        rule_level2 = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=2,
            responder_role="project_manager",
            is_active=True,
            priority=0
        )

        test_db.add_all([rule_level0, rule_level1, rule_level2])
        await test_db.commit()

        # Query escalation chain
        for level in range(3):
            stmt = select(RoutingRule).where(
                and_(
                    RoutingRule.squad_id == test_squad.id,
                    RoutingRule.asker_role == "backend_developer",
                    RoutingRule.question_type == "implementation",
                    RoutingRule.escalation_level == level,
                    RoutingRule.is_active == True
                )
            )
            result = await test_db.execute(stmt)
            rule = result.scalar_one()

            if level == 0:
                assert rule.responder_role == "tech_lead"
            elif level == 1:
                assert rule.responder_role == "solution_architect"
            elif level == 2:
                assert rule.responder_role == "project_manager"

    @pytest.mark.asyncio
    async def test_routing_rule_active_inactive_toggle(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test enabling/disabling routing rules"""
        # Create rule
        rule = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="tech_lead",
            is_active=True,
            priority=0
        )

        test_db.add(rule)
        await test_db.commit()

        assert rule.is_active is True

        # Deactivate rule
        rule.is_active = False
        await test_db.commit()
        await test_db.refresh(rule)

        assert rule.is_active is False

        # Query should not return inactive rules
        stmt = select(RoutingRule).where(
            and_(
                RoutingRule.squad_id == test_squad.id,
                RoutingRule.is_active == True
            )
        )
        result = await test_db.execute(stmt)
        active_rules = result.scalars().all()

        assert len(active_rules) == 0

    @pytest.mark.asyncio
    async def test_routing_rule_with_metadata(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test storing additional configuration in rule_metadata"""
        # Create rule with metadata
        metadata = {
            "timeout_override_minutes": 10,
            "max_escalations": 3,
            "notification_channels": ["slack", "email"],
            "business_hours_only": True
        }

        rule = RoutingRule(
            id=uuid4(),
            squad_id=test_squad.id,
            asker_role="backend_developer",
            question_type="implementation",
            escalation_level=0,
            responder_role="tech_lead",
            is_active=True,
            priority=0,
            rule_metadata=metadata
        )

        test_db.add(rule)
        await test_db.commit()
        await test_db.refresh(rule)

        # Verify metadata
        assert rule.rule_metadata == metadata
        assert rule.rule_metadata["timeout_override_minutes"] == 10
        assert "slack" in rule.rule_metadata["notification_channels"]

    @pytest.mark.asyncio
    async def test_routing_rule_question_types(
        self,
        test_db: AsyncSession,
        test_squad
    ):
        """Test different question types"""
        # Different question types route to different responders
        question_types = [
            ("implementation", "tech_lead"),
            ("architecture", "solution_architect"),
            ("deployment", "devops_engineer"),
            ("requirements", "project_manager"),
            ("design", "designer"),
            ("testing", "tester"),
            ("default", "tech_lead")  # Catch-all
        ]

        for question_type, responder_role in question_types:
            rule = RoutingRule(
                id=uuid4(),
                squad_id=test_squad.id,
                asker_role="backend_developer",
                question_type=question_type,
                escalation_level=0,
                responder_role=responder_role,
                is_active=True,
                priority=0
            )
            test_db.add(rule)

        await test_db.commit()

        # Query each question type
        for question_type, expected_responder in question_types:
            stmt = select(RoutingRule).where(
                and_(
                    RoutingRule.squad_id == test_squad.id,
                    RoutingRule.question_type == question_type
                )
            )
            result = await test_db.execute(stmt)
            rule = result.scalar_one()

            assert rule.responder_role == expected_responder


class TestDefaultRoutingTemplateModel:
    """Tests for DefaultRoutingTemplate model"""

    @pytest.mark.asyncio
    async def test_create_routing_template(
        self,
        test_db: AsyncSession,
        test_organization
    ):
        """Test creating a default routing template"""
        # Create template
        template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Standard Software Team",
            description="Standard routing hierarchy for software development teams",
            template_type="software",
            routing_rules_template=[
                {
                    "asker_role": "backend_developer",
                    "question_type": "implementation",
                    "escalation_level": 0,
                    "responder_role": "tech_lead"
                },
                {
                    "asker_role": "backend_developer",
                    "question_type": "implementation",
                    "escalation_level": 1,
                    "responder_role": "solution_architect"
                }
            ],
            is_public=True,
            is_default=True,
            created_by_org_id=test_organization.id
        )

        test_db.add(template)
        await test_db.commit()
        await test_db.refresh(template)

        # Verify
        assert template.id is not None
        assert template.name == "Standard Software Team"
        assert template.template_type == "software"
        assert len(template.routing_rules_template) == 2
        assert template.is_public is True
        assert template.is_default is True
        assert template.created_at is not None

    @pytest.mark.asyncio
    async def test_template_types(
        self,
        test_db: AsyncSession,
        test_organization
    ):
        """Test different template types"""
        # Software Team Template
        software_template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Standard Software Team",
            description="For general software development",
            template_type="software",
            routing_rules_template=[],
            is_public=True,
            is_default=False,
            created_by_org_id=test_organization.id
        )

        # DevOps Team Template
        devops_template = DefaultRoutingTemplate(
            id=uuid4(),
            name="DevOps Team",
            description="For infrastructure and deployment teams",
            template_type="devops",
            routing_rules_template=[],
            is_public=True,
            is_default=False,
            created_by_org_id=test_organization.id
        )

        # AI/ML Team Template
        ml_template = DefaultRoutingTemplate(
            id=uuid4(),
            name="AI/ML Team",
            description="For machine learning and data science teams",
            template_type="ml",
            routing_rules_template=[],
            is_public=True,
            is_default=False,
            created_by_org_id=test_organization.id
        )

        test_db.add_all([software_template, devops_template, ml_template])
        await test_db.commit()

        # Query by template type
        stmt = select(DefaultRoutingTemplate).where(
            DefaultRoutingTemplate.template_type == "devops"
        )
        result = await test_db.execute(stmt)
        template = result.scalar_one()

        assert template.name == "DevOps Team"

    @pytest.mark.asyncio
    async def test_public_vs_private_templates(
        self,
        test_db: AsyncSession,
        test_user
    ):
        """Test public and private template visibility"""
        # Need two organizations
        from backend.models import Organization

        org1 = Organization(id=uuid4(), name="Org 1", owner_id=test_user.id)
        org2 = Organization(id=uuid4(), name="Org 2", owner_id=test_user.id)
        test_db.add_all([org1, org2])
        await test_db.commit()

        # Public template (shareable across orgs)
        public_template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Public Template",
            description="Available to all organizations",
            template_type="software",
            routing_rules_template=[],
            is_public=True,
            is_default=False,
            created_by_org_id=org1.id
        )

        # Private template (org-specific)
        private_template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Private Template",
            description="Only for Org 1",
            template_type="custom",
            routing_rules_template=[],
            is_public=False,
            is_default=False,
            created_by_org_id=org1.id
        )

        test_db.add_all([public_template, private_template])
        await test_db.commit()

        # Org 2 should see public templates
        stmt = select(DefaultRoutingTemplate).where(
            DefaultRoutingTemplate.is_public == True
        )
        result = await test_db.execute(stmt)
        public_templates = result.scalars().all()

        assert len(public_templates) == 1
        assert public_templates[0].name == "Public Template"

        # Org 1 should see both public and their private templates
        stmt = select(DefaultRoutingTemplate).where(
            (DefaultRoutingTemplate.is_public == True) |
            (DefaultRoutingTemplate.created_by_org_id == org1.id)
        )
        result = await test_db.execute(stmt)
        org1_templates = result.scalars().all()

        assert len(org1_templates) == 2

    @pytest.mark.asyncio
    async def test_default_template_flag(
        self,
        test_db: AsyncSession,
        test_organization
    ):
        """Test marking a template as default for new squads"""
        # Create multiple templates, mark one as default
        template1 = DefaultRoutingTemplate(
            id=uuid4(),
            name="Template 1",
            description="Not default",
            template_type="software",
            routing_rules_template=[],
            is_public=True,
            is_default=False,
            created_by_org_id=test_organization.id
        )

        template2 = DefaultRoutingTemplate(
            id=uuid4(),
            name="Template 2",
            description="Default template for new squads",
            template_type="software",
            routing_rules_template=[],
            is_public=True,
            is_default=True,  # This is the default
            created_by_org_id=test_organization.id
        )

        test_db.add_all([template1, template2])
        await test_db.commit()

        # Query default template
        stmt = select(DefaultRoutingTemplate).where(
            DefaultRoutingTemplate.is_default == True
        )
        result = await test_db.execute(stmt)
        default_template = result.scalar_one()

        assert default_template.name == "Template 2"

    @pytest.mark.asyncio
    async def test_complex_routing_rules_template(
        self,
        test_db: AsyncSession,
        test_organization
    ):
        """Test template with complex routing rules configuration"""
        # Create template with complete escalation chain
        routing_rules = [
            # Backend Developer routing
            {
                "asker_role": "backend_developer",
                "question_type": "implementation",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 0
            },
            {
                "asker_role": "backend_developer",
                "question_type": "implementation",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 0
            },
            {
                "asker_role": "backend_developer",
                "question_type": "implementation",
                "escalation_level": 2,
                "responder_role": "project_manager",
                "priority": 0
            },
            # Frontend Developer routing
            {
                "asker_role": "frontend_developer",
                "question_type": "design",
                "escalation_level": 0,
                "responder_role": "designer",
                "priority": 0
            },
            {
                "asker_role": "frontend_developer",
                "question_type": "implementation",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 0
            },
            # DevOps Engineer routing
            {
                "asker_role": "devops_engineer",
                "question_type": "deployment",
                "escalation_level": 0,
                "responder_role": "solution_architect",
                "priority": 0
            },
        ]

        template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Complete Software Team",
            description="Full routing configuration for software team",
            template_type="software",
            routing_rules_template=routing_rules,
            is_public=True,
            is_default=True,
            created_by_org_id=test_organization.id
        )

        test_db.add(template)
        await test_db.commit()
        await test_db.refresh(template)

        # Verify template structure
        assert len(template.routing_rules_template) == 6

        # Verify backend developer rules
        backend_rules = [r for r in template.routing_rules_template if r["asker_role"] == "backend_developer"]
        assert len(backend_rules) == 3
        assert backend_rules[0]["escalation_level"] == 0
        assert backend_rules[1]["escalation_level"] == 1
        assert backend_rules[2]["escalation_level"] == 2

        # Verify frontend developer rules
        frontend_rules = [r for r in template.routing_rules_template if r["asker_role"] == "frontend_developer"]
        assert len(frontend_rules) == 2

    @pytest.mark.asyncio
    async def test_apply_template_simulation(
        self,
        test_db: AsyncSession,
        test_squad,
        test_organization
    ):
        """Test simulating applying a template to create routing rules"""
        # Create template
        template = DefaultRoutingTemplate(
            id=uuid4(),
            name="Standard Template",
            description="Standard routing",
            template_type="software",
            routing_rules_template=[
                {
                    "asker_role": "backend_developer",
                    "question_type": "implementation",
                    "escalation_level": 0,
                    "responder_role": "tech_lead"
                },
                {
                    "asker_role": "backend_developer",
                    "question_type": "implementation",
                    "escalation_level": 1,
                    "responder_role": "solution_architect"
                }
            ],
            is_public=True,
            is_default=True,
            created_by_org_id=test_organization.id
        )

        test_db.add(template)
        await test_db.commit()

        # Simulate applying template: Create routing rules from template
        for rule_def in template.routing_rules_template:
            routing_rule = RoutingRule(
                id=uuid4(),
                squad_id=test_squad.id,
                asker_role=rule_def["asker_role"],
                question_type=rule_def["question_type"],
                escalation_level=rule_def["escalation_level"],
                responder_role=rule_def["responder_role"],
                is_active=True,
                priority=0
            )
            test_db.add(routing_rule)

        await test_db.commit()

        # Verify rules were created
        stmt = select(RoutingRule).where(RoutingRule.squad_id == test_squad.id)
        result = await test_db.execute(stmt)
        created_rules = result.scalars().all()

        assert len(created_rules) == 2
        assert created_rules[0].asker_role == "backend_developer"
        assert created_rules[1].escalation_level == 1
