"""
Tests for Routing Engine
"""
import pytest
from uuid import uuid4

from backend.agents.interaction.routing_engine import RoutingEngine
from backend.models import RoutingRule, DefaultRoutingTemplate


@pytest.mark.asyncio
async def test_get_responder_basic(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test getting responder for a basic question"""
    # Create routing rule: backend -> tech lead
    rule = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    test_db.add(rule)
    await test_db.commit()

    # Get responder
    routing_engine = RoutingEngine(test_db)
    responder = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )

    assert responder is not None
    assert responder.role == "tech_lead"
    assert responder.id == test_squad_member_tech_lead.id


@pytest.mark.asyncio
async def test_get_responder_escalation_level(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test getting responder at different escalation levels"""
    # Level 0: backend -> tech lead
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )

    # Level 1: backend -> solution architect
    rule2 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )

    test_db.add(rule1)
    test_db.add(rule2)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)

    # Test level 0
    responder0 = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )
    assert responder0.role == "tech_lead"

    # Test level 1
    responder1 = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1
    )
    assert responder1.role == "solution_architect"


@pytest.mark.asyncio
async def test_get_responder_question_type(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test routing by question type"""
    # Default questions -> tech lead
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )

    # Architecture questions -> solution architect
    rule2 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="architecture",
        escalation_level=0,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )

    test_db.add(rule1)
    test_db.add(rule2)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)

    # Test default
    responder_default = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )
    assert responder_default.role == "tech_lead"

    # Test architecture
    responder_arch = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="architecture",
        escalation_level=0
    )
    assert responder_arch.role == "solution_architect"


@pytest.mark.asyncio
async def test_get_responder_priority(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test that higher priority rules take precedence"""
    # Low priority rule
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=5
    )

    # High priority rule
    rule2 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="solution_architect",
        is_active=True,
        priority=20
    )

    test_db.add(rule1)
    test_db.add(rule2)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)

    # Should get high priority responder
    responder = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )

    assert responder.role == "solution_architect"


@pytest.mark.asyncio
async def test_get_responder_specific_responder_id(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test routing to a specific responder by ID"""
    # Rule with specific responder
    rule = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        specific_responder_id=test_squad_member_tech_lead.id,
        is_active=True,
        priority=10
    )
    test_db.add(rule)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    responder = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )

    assert responder.id == test_squad_member_tech_lead.id


@pytest.mark.asyncio
async def test_get_responder_no_rule(test_db, test_squad):
    """Test when no routing rule exists"""
    routing_engine = RoutingEngine(test_db)
    responder = await routing_engine.get_responder(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0
    )

    assert responder is None


@pytest.mark.asyncio
async def test_get_escalation_chain(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect,
    test_squad_member_pm
):
    """Test getting complete escalation chain"""
    # Level 0: backend -> tech lead
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )

    # Level 1: backend -> solution architect
    rule2 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )

    # Level 2: backend -> project manager
    rule3 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=2,
        responder_role="project_manager",
        is_active=True,
        priority=10
    )

    test_db.add(rule1)
    test_db.add(rule2)
    test_db.add(rule3)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    chain = await routing_engine.get_escalation_chain(
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default"
    )

    assert len(chain) == 3
    assert chain[0]["escalation_level"] == 0
    assert chain[0]["responder_role"] == "tech_lead"
    assert chain[1]["escalation_level"] == 1
    assert chain[1]["responder_role"] == "solution_architect"
    assert chain[2]["escalation_level"] == 2
    assert chain[2]["responder_role"] == "project_manager"


@pytest.mark.asyncio
async def test_validate_routing_config_valid(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test validating a valid routing configuration"""
    # Complete level 0 routing
    rule = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    test_db.add(rule)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    result = await routing_engine.validate_routing_config(squad_id=test_squad.id)

    assert result["valid"] is True
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
async def test_validate_routing_config_missing_level_zero(test_db, test_squad):
    """Test validating config with missing level 0"""
    # Only level 1 rule (missing level 0)
    rule = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    test_db.add(rule)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    result = await routing_engine.validate_routing_config(squad_id=test_squad.id)

    assert result["valid"] is False
    assert len(result["issues"]) > 0
    assert "Missing level 0" in result["issues"][0]


@pytest.mark.asyncio
async def test_validate_routing_config_no_rules(test_db, test_squad):
    """Test validating config with no rules"""
    routing_engine = RoutingEngine(test_db)
    result = await routing_engine.validate_routing_config(squad_id=test_squad.id)

    assert result["valid"] is False
    assert "No routing rules" in result["issues"][0]


@pytest.mark.asyncio
async def test_apply_template_to_squad(test_db, test_squad):
    """Test applying a routing template to a squad"""
    # Create template
    template = DefaultRoutingTemplate(
        id=uuid4(),
        name="Test Template",
        description="Test template description",
        routing_rules_template=[
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            {
                "asker_role": "backend_developer",
                "question_type": "default",
                "escalation_level": 1,
                "responder_role": "solution_architect",
                "priority": 10
            }
        ],
        is_active=True
    )
    test_db.add(template)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    rules_created = await routing_engine.apply_template_to_squad(
        template_id=template.id,
        squad_id=test_squad.id,
        overwrite_existing=False
    )

    assert rules_created == 2

    # Verify rules were created
    from sqlalchemy import select
    stmt = select(RoutingRule).where(RoutingRule.squad_id == test_squad.id)
    result = await test_db.execute(stmt)
    rules = result.scalars().all()

    assert len(rules) == 2


@pytest.mark.asyncio
async def test_apply_template_overwrite(test_db, test_squad):
    """Test applying template with overwrite=True"""
    # Create existing rule
    existing_rule = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=5
    )
    test_db.add(existing_rule)
    await test_db.commit()

    # Create template
    template = DefaultRoutingTemplate(
        id=uuid4(),
        name="Test Template",
        description="Test template",
        routing_rules_template=[
            {
                "asker_role": "frontend_developer",
                "question_type": "default",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            }
        ],
        is_active=True
    )
    test_db.add(template)
    await test_db.commit()

    routing_engine = RoutingEngine(test_db)
    await routing_engine.apply_template_to_squad(
        template_id=template.id,
        squad_id=test_squad.id,
        overwrite_existing=True
    )

    # Verify old rules deleted and new rules created
    from sqlalchemy import select
    stmt = select(RoutingRule).where(RoutingRule.squad_id == test_squad.id)
    result = await test_db.execute(stmt)
    rules = result.scalars().all()

    assert len(rules) == 1
    assert rules[0].asker_role == "frontend_developer"
