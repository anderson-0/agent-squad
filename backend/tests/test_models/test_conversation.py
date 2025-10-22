"""
Unit tests for Conversation and ConversationEvent models
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    Conversation,
    ConversationEvent,
    ConversationState,
    AgentMessage
)


class TestConversationModel:
    """Tests for Conversation model"""

    @pytest.mark.asyncio
    async def test_create_conversation(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test creating a basic conversation"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            question_type="implementation",
            task_execution_id=test_task_execution.id,
            timeout_at=datetime.utcnow() + timedelta(minutes=5)
        )

        test_db.add(conversation)
        await test_db.commit()
        await test_db.refresh(conversation)

        # Verify
        assert conversation.id is not None
        assert conversation.current_state == ConversationState.INITIATED.value
        assert conversation.asker_id == test_squad_member_backend.id
        assert conversation.current_responder_id == test_squad_member_tech_lead.id
        assert conversation.escalation_level == 0
        assert conversation.question_type == "implementation"
        assert conversation.timeout_at is not None
        assert conversation.created_at is not None
        assert conversation.acknowledged_at is None
        assert conversation.resolved_at is None

    @pytest.mark.asyncio
    async def test_conversation_state_transitions(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test conversation state transitions"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        # Transition: INITIATED -> WAITING (acknowledged)
        conversation.current_state = ConversationState.WAITING.value
        conversation.acknowledged_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.WAITING.value
        assert conversation.acknowledged_at is not None

        # Transition: WAITING -> TIMEOUT
        conversation.current_state = ConversationState.TIMEOUT.value
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.TIMEOUT.value

        # Transition: TIMEOUT -> FOLLOW_UP
        conversation.current_state = ConversationState.FOLLOW_UP.value
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.FOLLOW_UP.value

        # Transition: FOLLOW_UP -> ESCALATING
        conversation.current_state = ConversationState.ESCALATING.value
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.ESCALATING.value

        # Transition: ESCALATING -> ESCALATED
        conversation.current_state = ConversationState.ESCALATED.value
        conversation.escalation_level = 1
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.ESCALATED.value
        assert conversation.escalation_level == 1

        # Transition: ESCALATED -> ANSWERED (resolved)
        conversation.current_state = ConversationState.ANSWERED.value
        conversation.resolved_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.current_state == ConversationState.ANSWERED.value
        assert conversation.resolved_at is not None

    @pytest.mark.asyncio
    async def test_conversation_with_metadata(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test conversation metadata storage"""
        # Create conversation with metadata
        metadata = {
            "priority": "high",
            "tags": ["urgent", "implementation"],
            "context": {"sprint": "sprint-23"}
        }

        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id,
            conv_metadata=metadata
        )

        test_db.add(conversation)
        await test_db.commit()
        await test_db.refresh(conversation)

        # Verify metadata
        assert conversation.conv_metadata == metadata
        assert conversation.conv_metadata["priority"] == "high"
        assert "urgent" in conversation.conv_metadata["tags"]

    @pytest.mark.asyncio
    async def test_conversation_timeout_handling(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test timeout_at field for Celery monitoring"""
        # Create conversation with timeout
        timeout_time = datetime.utcnow() + timedelta(minutes=5)

        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.WAITING.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id,
            timeout_at=timeout_time
        )

        test_db.add(conversation)
        await test_db.commit()
        await test_db.refresh(conversation)

        # Verify timeout is set
        assert conversation.timeout_at is not None
        assert conversation.timeout_at > datetime.utcnow()

        # Simulate timeout monitoring query (what Celery will do)
        stmt = select(Conversation).where(
            Conversation.timeout_at <= datetime.utcnow() + timedelta(hours=1),
            Conversation.current_state.in_([
                ConversationState.WAITING.value,
                ConversationState.FOLLOW_UP.value
            ])
        )
        result = await test_db.execute(stmt)
        timed_out_conversations = result.scalars().all()

        assert len(timed_out_conversations) == 1
        assert timed_out_conversations[0].id == conversation.id

    @pytest.mark.asyncio
    async def test_conversation_escalation_levels(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_squad_member_architect,
        test_squad_member_pm,
        test_task_execution,
        test_message
    ):
        """Test escalation level tracking"""
        # Create conversation at level 0
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        assert conversation.escalation_level == 0
        assert conversation.current_responder_id == test_squad_member_tech_lead.id

        # Escalate to level 1 (Solution Architect)
        conversation.escalation_level = 1
        conversation.current_responder_id = test_squad_member_architect.id
        conversation.current_state = ConversationState.ESCALATED.value
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.escalation_level == 1
        assert conversation.current_responder_id == test_squad_member_architect.id

        # Escalate to level 2 (Project Manager)
        conversation.escalation_level = 2
        conversation.current_responder_id = test_squad_member_pm.id
        await test_db.commit()
        await test_db.refresh(conversation)

        assert conversation.escalation_level == 2
        assert conversation.current_responder_id == test_squad_member_pm.id

    @pytest.mark.asyncio
    async def test_conversation_relationships(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test conversation relationships to other models"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        # Query with relationships
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await test_db.execute(stmt)
        loaded_conversation = result.scalar_one()

        # Verify relationships can be loaded
        assert loaded_conversation.initial_message_id == test_message.id
        assert loaded_conversation.asker_id == test_squad_member_backend.id
        assert loaded_conversation.current_responder_id == test_squad_member_tech_lead.id
        assert loaded_conversation.task_execution_id == test_task_execution.id


class TestConversationEventModel:
    """Tests for ConversationEvent model"""

    @pytest.mark.asyncio
    async def test_create_conversation_event(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test creating a conversation event"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="initiated",
            from_state=None,
            to_state=ConversationState.INITIATED.value,
            message_id=test_message.id,
            triggered_by_agent_id=test_squad_member_backend.id,
            event_data={"initial_question": "How do I implement this?"}
        )

        test_db.add(event)
        await test_db.commit()
        await test_db.refresh(event)

        # Verify
        assert event.id is not None
        assert event.conversation_id == conversation.id
        assert event.event_type == "initiated"
        assert event.from_state is None
        assert event.to_state == ConversationState.INITIATED.value
        assert event.message_id == test_message.id
        assert event.triggered_by_agent_id == test_squad_member_backend.id
        assert event.created_at is not None
        assert event.event_data["initial_question"] == "How do I implement this?"

    @pytest.mark.asyncio
    async def test_conversation_event_audit_trail(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_squad_member_architect,
        test_task_execution,
        test_message
    ):
        """Test creating a complete audit trail of events"""
        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        # Event 1: Initiated
        event1 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="initiated",
            from_state=None,
            to_state=ConversationState.INITIATED.value,
            message_id=test_message.id,
            triggered_by_agent_id=test_squad_member_backend.id
        )
        test_db.add(event1)

        # Event 2: Acknowledged
        event2 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="acknowledged",
            from_state=ConversationState.INITIATED.value,
            to_state=ConversationState.WAITING.value,
            message_id=test_message.id,
            triggered_by_agent_id=test_squad_member_tech_lead.id
        )
        test_db.add(event2)

        # Event 3: Timeout
        event3 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="timeout",
            from_state=ConversationState.WAITING.value,
            to_state=ConversationState.TIMEOUT.value,
            message_id=None,
            triggered_by_agent_id=None,  # System triggered
            event_data={"reason": "no_response_after_5_minutes"}
        )
        test_db.add(event3)

        # Event 4: Follow-up sent
        event4 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="follow_up_sent",
            from_state=ConversationState.TIMEOUT.value,
            to_state=ConversationState.FOLLOW_UP.value,
            message_id=None,
            triggered_by_agent_id=None,  # System triggered
        )
        test_db.add(event4)

        # Event 5: Escalated
        event5 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="escalated",
            from_state=ConversationState.FOLLOW_UP.value,
            to_state=ConversationState.ESCALATED.value,
            message_id=None,
            triggered_by_agent_id=None,  # System triggered
            event_data={
                "from_agent_id": str(test_squad_member_tech_lead.id),
                "to_agent_id": str(test_squad_member_architect.id),
                "escalation_level": 1
            }
        )
        test_db.add(event5)

        # Event 6: Answered
        answer_message = AgentMessage(
            id=uuid4(),
            sender_id=test_squad_member_architect.id,
            recipient_id=test_squad_member_backend.id,
            content="Here's the answer",
            message_type="answer",
            task_execution_id=test_task_execution.id
        )
        test_db.add(answer_message)

        event6 = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="answered",
            from_state=ConversationState.ESCALATED.value,
            to_state=ConversationState.ANSWERED.value,
            message_id=answer_message.id,
            triggered_by_agent_id=test_squad_member_architect.id
        )
        test_db.add(event6)

        await test_db.commit()

        # Query all events for this conversation
        stmt = select(ConversationEvent).where(
            ConversationEvent.conversation_id == conversation.id
        ).order_by(ConversationEvent.created_at)

        result = await test_db.execute(stmt)
        events = result.scalars().all()

        # Verify audit trail
        assert len(events) == 6
        assert events[0].event_type == "initiated"
        assert events[1].event_type == "acknowledged"
        assert events[2].event_type == "timeout"
        assert events[3].event_type == "follow_up_sent"
        assert events[4].event_type == "escalated"
        assert events[5].event_type == "answered"

        # Verify state transitions
        assert events[0].to_state == ConversationState.INITIATED.value
        assert events[1].to_state == ConversationState.WAITING.value
        assert events[2].to_state == ConversationState.TIMEOUT.value
        assert events[3].to_state == ConversationState.FOLLOW_UP.value
        assert events[4].to_state == ConversationState.ESCALATED.value
        assert events[5].to_state == ConversationState.ANSWERED.value

    @pytest.mark.asyncio
    async def test_event_with_metadata(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test storing additional data in event_data"""
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        test_db.add(conversation)
        await test_db.commit()

        # Create event with rich metadata
        event_data = {
            "timeout_duration_seconds": 300,
            "retry_count": 1,
            "notification_sent": True,
            "escalation_reason": "no_response_after_retries",
            "context": {
                "time_of_day": "after_hours",
                "workload": "high"
            }
        }

        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="escalated",
            from_state=ConversationState.FOLLOW_UP.value,
            to_state=ConversationState.ESCALATED.value,
            message_id=None,
            triggered_by_agent_id=None,
            event_data=event_data
        )

        test_db.add(event)
        await test_db.commit()
        await test_db.refresh(event)

        # Verify metadata
        assert event.event_data == event_data
        assert event.event_data["timeout_duration_seconds"] == 300
        assert event.event_data["context"]["time_of_day"] == "after_hours"

    @pytest.mark.asyncio
    async def test_query_events_by_type(
        self,
        test_db: AsyncSession,
        test_squad_member_backend,
        test_squad_member_tech_lead,
        test_task_execution,
        test_message
    ):
        """Test querying events by type"""
        # Create multiple conversations with events
        conv1 = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )
        conv2 = Conversation(
            id=uuid4(),
            initial_message_id=test_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=test_squad_member_backend.id,
            current_responder_id=test_squad_member_tech_lead.id,
            escalation_level=0,
            task_execution_id=test_task_execution.id
        )

        test_db.add_all([conv1, conv2])
        await test_db.commit()

        # Create escalation events
        event1 = ConversationEvent(
            id=uuid4(),
            conversation_id=conv1.id,
            event_type="escalated",
            from_state=ConversationState.FOLLOW_UP.value,
            to_state=ConversationState.ESCALATED.value,
            message_id=None,
            triggered_by_agent_id=None
        )
        event2 = ConversationEvent(
            id=uuid4(),
            conversation_id=conv2.id,
            event_type="escalated",
            from_state=ConversationState.FOLLOW_UP.value,
            to_state=ConversationState.ESCALATED.value,
            message_id=None,
            triggered_by_agent_id=None
        )
        event3 = ConversationEvent(
            id=uuid4(),
            conversation_id=conv1.id,
            event_type="answered",
            from_state=ConversationState.ESCALATED.value,
            to_state=ConversationState.ANSWERED.value,
            message_id=test_message.id,
            triggered_by_agent_id=test_squad_member_tech_lead.id
        )

        test_db.add_all([event1, event2, event3])
        await test_db.commit()

        # Query escalation events
        stmt = select(ConversationEvent).where(ConversationEvent.event_type == "escalated")
        result = await test_db.execute(stmt)
        escalation_events = result.scalars().all()

        assert len(escalation_events) == 2
        for event in escalation_events:
            assert event.event_type == "escalated"
