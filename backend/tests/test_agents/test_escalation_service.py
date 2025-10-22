"""
Tests for Escalation Service
"""
import pytest
from uuid import uuid4

from backend.agents.interaction.escalation_service import EscalationService
from backend.agents.interaction.conversation_manager import ConversationManager
from backend.models import Conversation, ConversationState, RoutingRule


@pytest.mark.asyncio
async def test_escalate_conversation_basic(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test basic conversation escalation"""
    # Create routing rules for levels 0 and 1
    rule0 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )
    test_db.add(rule0)
    test_db.add(rule1)
    await test_db.commit()

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Escalate
    escalation_service = EscalationService(test_db)
    success = await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )

    assert success is True

    # Verify escalation
    await test_db.refresh(conversation)
    assert conversation.current_state == ConversationState.ESCALATED.value
    assert conversation.escalation_level == 1
    assert conversation.current_responder_id == test_squad_member_architect.id


@pytest.mark.asyncio
async def test_escalate_conversation_no_next_level(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test escalation when no next level exists"""
    # Only level 0 rule (no level 1)
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

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Try to escalate
    escalation_service = EscalationService(test_db)
    success = await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )

    assert success is False

    # Verify marked as unresolvable
    await test_db.refresh(conversation)
    assert conversation.current_state == "unresolvable"
    assert conversation.timeout_at is None


@pytest.mark.asyncio
async def test_escalate_conversation_multi_level(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect,
    test_squad_member_pm
):
    """Test multiple escalations through hierarchy"""
    # Create 3 levels
    rule0 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )
    rule2 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=2,
        responder_role="project_manager",
        is_active=True,
        priority=10
    )
    test_db.add(rule0)
    test_db.add(rule1)
    test_db.add(rule2)
    await test_db.commit()

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    escalation_service = EscalationService(test_db)

    # First escalation
    success1 = await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )
    assert success1 is True
    await test_db.refresh(conversation)
    assert conversation.escalation_level == 1
    assert conversation.current_responder_id == test_squad_member_architect.id

    # Second escalation
    success2 = await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )
    assert success2 is True
    await test_db.refresh(conversation)
    assert conversation.escalation_level == 2
    assert conversation.current_responder_id == test_squad_member_pm.id

    # Third escalation (no level 3 exists)
    success3 = await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )
    assert success3 is False
    await test_db.refresh(conversation)
    assert conversation.current_state == "unresolvable"


@pytest.mark.asyncio
async def test_handle_cant_help_escalate(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test 'can't help' escalation"""
    # Create routing rules
    rule0 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )
    test_db.add(rule0)
    test_db.add(rule1)
    await test_db.commit()

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Tech lead says "can't help" (no target role = escalate)
    escalation_service = EscalationService(test_db)
    success = await escalation_service.handle_cant_help(
        conversation_id=conversation.id,
        current_responder_id=test_squad_member_tech_lead.id,
        target_role=None  # No specific target = escalate
    )

    assert success is True

    # Verify escalation occurred
    await test_db.refresh(conversation)
    assert conversation.escalation_level == 1
    assert conversation.current_responder_id == test_squad_member_architect.id


@pytest.mark.asyncio
async def test_handle_cant_help_route_to_role(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test 'can't help' with specific role routing"""
    # Create routing rules
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

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Tech lead routes to solution architect
    escalation_service = EscalationService(test_db)
    success = await escalation_service.handle_cant_help(
        conversation_id=conversation.id,
        current_responder_id=test_squad_member_tech_lead.id,
        target_role="solution_architect"
    )

    assert success is True

    # Verify routing (escalation level stays 0, just responder changes)
    await test_db.refresh(conversation)
    assert conversation.escalation_level == 0  # Level doesn't change
    assert conversation.current_responder_id == test_squad_member_architect.id


@pytest.mark.asyncio
async def test_handle_cant_help_wrong_responder(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test that only current responder can request routing"""
    # Create routing rule
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

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Different agent tries to request routing
    escalation_service = EscalationService(test_db)

    with pytest.raises(ValueError, match="Only the current responder"):
        await escalation_service.handle_cant_help(
            conversation_id=conversation.id,
            current_responder_id=test_squad_member_architect.id,  # Wrong responder
            target_role=None
        )


@pytest.mark.asyncio
async def test_handle_cant_help_target_role_not_found(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test 'can't help' when target role doesn't exist"""
    # Create routing rule
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

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Try to route to non-existent role
    escalation_service = EscalationService(test_db)
    success = await escalation_service.handle_cant_help(
        conversation_id=conversation.id,
        current_responder_id=test_squad_member_tech_lead.id,
        target_role="nonexistent_role"
    )

    assert success is False


@pytest.mark.asyncio
async def test_escalation_creates_events(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test that escalation creates proper events"""
    # Create routing rules
    rule0 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )
    test_db.add(rule0)
    test_db.add(rule1)
    await test_db.commit()

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Escalate
    escalation_service = EscalationService(test_db)
    await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )

    # Verify escalation event was created
    from sqlalchemy import select
    from backend.models import ConversationEvent
    stmt = select(ConversationEvent).where(
        ConversationEvent.conversation_id == conversation.id,
        ConversationEvent.event_type == "escalated"
    )
    result = await test_db.execute(stmt)
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].event_data["escalation_level"] == 1
    assert events[0].event_data["reason"] == "timeout"


@pytest.mark.asyncio
async def test_escalation_sends_notifications(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead,
    test_squad_member_architect
):
    """Test that escalation sends notifications to all parties"""
    # Create routing rules
    rule0 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=0,
        responder_role="tech_lead",
        is_active=True,
        priority=10
    )
    rule1 = RoutingRule(
        id=uuid4(),
        squad_id=test_squad.id,
        asker_role="backend_developer",
        question_type="default",
        escalation_level=1,
        responder_role="solution_architect",
        is_active=True,
        priority=10
    )
    test_db.add(rule0)
    test_db.add(rule1)
    await test_db.commit()

    # Create conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Escalate
    escalation_service = EscalationService(test_db)
    await escalation_service.escalate_conversation(
        conversation_id=conversation.id,
        reason="timeout"
    )

    # Verify messages were sent (check AgentMessage table)
    from sqlalchemy import select
    from backend.models import AgentMessage
    stmt = select(AgentMessage).where(
        AgentMessage.task_execution_id == conversation.task_execution_id
    )
    result = await test_db.execute(stmt)
    messages = result.scalars().all()

    # Should have: original question + escalation notification + escalation context
    assert len(messages) >= 2
