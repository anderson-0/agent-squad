"""
Tests for Conversation Manager
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.agents.interaction.conversation_manager import ConversationManager
from backend.models import Conversation, ConversationState, ConversationEvent, RoutingRule


@pytest.mark.asyncio
async def test_initiate_question_basic(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test initiating a basic question"""
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

    # Initiate question
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="How do I implement authentication?",
        question_type="default"
    )

    assert conversation is not None
    assert conversation.asker_id == test_squad_member_backend.id
    assert conversation.current_responder_id == test_squad_member_tech_lead.id
    assert conversation.current_state == ConversationState.INITIATED.value
    assert conversation.escalation_level == 0
    assert conversation.timeout_at is not None


@pytest.mark.asyncio
async def test_initiate_question_with_metadata(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test initiating question with custom metadata"""
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

    # Initiate question with metadata
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question content",
        question_type="default",
        metadata={"urgency": "high", "context": "feature-x"}
    )

    assert conversation.conv_metadata is not None
    assert conversation.conv_metadata["urgency"] == "high"
    assert conversation.conv_metadata["context"] == "feature-x"


@pytest.mark.asyncio
async def test_initiate_question_no_responder(
    test_db,
    test_squad,
    test_squad_member_backend
):
    """Test initiating question when no responder available"""
    # No routing rules exist

    manager = ConversationManager(test_db)

    with pytest.raises(ValueError, match="No responder found"):
        await manager.initiate_question(
            asker_id=test_squad_member_backend.id,
            question_content="Question",
            question_type="default"
        )


@pytest.mark.asyncio
async def test_acknowledge_conversation(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test acknowledging a conversation"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Acknowledge
    await manager.acknowledge_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id
    )

    # Verify state changed
    await test_db.refresh(conversation)
    assert conversation.current_state == ConversationState.WAITING.value
    assert conversation.acknowledged_at is not None


@pytest.mark.asyncio
async def test_acknowledge_conversation_custom_message(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test acknowledging with custom message"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Acknowledge with custom message
    await manager.acknowledge_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id,
        custom_message="I'll get back to you in 10 minutes"
    )

    await test_db.refresh(conversation)
    assert conversation.current_state == ConversationState.WAITING.value


@pytest.mark.asyncio
async def test_acknowledge_conversation_wrong_state(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test acknowledging conversation in wrong state"""
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

    # Initiate and acknowledge
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )
    await manager.acknowledge_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id
    )

    # Try to acknowledge again (wrong state)
    with pytest.raises(ValueError, match="Cannot acknowledge"):
        await manager.acknowledge_conversation(
            conversation_id=conversation.id,
            responder_id=test_squad_member_tech_lead.id
        )


@pytest.mark.asyncio
async def test_answer_conversation(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test answering a conversation"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Answer
    await manager.answer_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id,
        answer_content="Here's the answer to your question..."
    )

    # Verify state changed
    await test_db.refresh(conversation)
    assert conversation.current_state == ConversationState.ANSWERED.value
    assert conversation.resolved_at is not None
    assert conversation.timeout_at is None  # Timeout cleared


@pytest.mark.asyncio
async def test_cancel_conversation(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test cancelling a conversation"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Cancel
    await manager.cancel_conversation(
        conversation_id=conversation.id,
        cancelled_by_id=test_squad_member_backend.id,
        reason="No longer needed"
    )

    # Verify state changed
    await test_db.refresh(conversation)
    assert conversation.current_state == ConversationState.CANCELLED.value
    assert conversation.timeout_at is None


@pytest.mark.asyncio
async def test_get_conversation_timeline(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test getting conversation timeline with all events"""
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

    # Create conversation with multiple events
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    await manager.acknowledge_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id
    )

    await manager.answer_conversation(
        conversation_id=conversation.id,
        responder_id=test_squad_member_tech_lead.id,
        answer_content="Answer"
    )

    # Get timeline
    timeline = await manager.get_conversation_timeline(conversation.id)

    assert timeline["conversation_id"] == str(conversation.id)
    assert len(timeline["events"]) == 3  # initiated, acknowledged, answered
    assert timeline["events"][0]["event_type"] == "initiated"
    assert timeline["events"][1]["event_type"] == "acknowledged"
    assert timeline["events"][2]["event_type"] == "answered"


@pytest.mark.asyncio
async def test_conversation_creates_events(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test that conversation actions create proper events"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Verify event was created
    from sqlalchemy import select
    stmt = select(ConversationEvent).where(
        ConversationEvent.conversation_id == conversation.id
    )
    result = await test_db.execute(stmt)
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].event_type == "initiated"
    assert events[0].triggered_by_agent_id == test_squad_member_backend.id


@pytest.mark.asyncio
async def test_conversation_timeout_set_correctly(
    test_db,
    test_squad,
    test_squad_member_backend,
    test_squad_member_tech_lead
):
    """Test that conversation timeout is set correctly"""
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

    # Initiate conversation
    manager = ConversationManager(test_db)
    conversation = await manager.initiate_question(
        asker_id=test_squad_member_backend.id,
        question_content="Question",
        question_type="default"
    )

    # Verify timeout is set in the future
    assert conversation.timeout_at is not None
    assert conversation.timeout_at > datetime.utcnow()

    # Verify timeout is roughly 5 minutes from now (default)
    time_diff = conversation.timeout_at - datetime.utcnow()
    assert 4 * 60 < time_diff.total_seconds() < 6 * 60  # Between 4 and 6 minutes
