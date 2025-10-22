"""
Conversation Manager

Manages the lifecycle of agent-to-agent conversations including:
- Initiating questions with routing
- Handling acknowledgments
- Monitoring timeouts
- Managing escalations
- Resolving conversations
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    Conversation,
    ConversationState,
    ConversationEvent,
    SquadMember,
    AgentMessage
)
from backend.agents.interaction.routing_engine import RoutingEngine
from backend.agents.configuration.interaction_config import InteractionConfig, get_interaction_config
from backend.agents.communication.message_bus import get_message_bus


class ConversationManager:
    """
    Manager for agent-to-agent conversation lifecycle

    This class handles the complete lifecycle of hierarchical conversations:
    1. Route initial questions to appropriate responders
    2. Send automatic acknowledgments
    3. Monitor timeouts and send follow-ups
    4. Escalate to next level when needed
    5. Track conversation state and events
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[InteractionConfig] = None
    ):
        """
        Initialize conversation manager

        Args:
            db: Database session
            config: Interaction configuration (uses default if not provided)
        """
        self.db = db
        self.config = config or get_interaction_config()
        self.routing_engine = RoutingEngine(db)
        self.message_bus = get_message_bus()

    async def initiate_question(
        self,
        asker_id: UUID,
        question_content: str,
        question_type: str = "default",
        task_execution_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> Conversation:
        """
        Initiate a new question conversation

        Steps:
        1. Get asker's squad and role
        2. Query routing engine for appropriate responder
        3. Send question message via message bus
        4. Create conversation record
        5. Create conversation event
        6. Set timeout

        Args:
            asker_id: ID of the agent asking the question
            question_content: Content of the question
            question_type: Type of question (implementation, architecture, etc.)
            task_execution_id: Optional task execution ID
            metadata: Optional additional metadata

        Returns:
            Created Conversation object

        Raises:
            ValueError: If asker not found or no responder available
        """
        # Get asker
        stmt = select(SquadMember).where(SquadMember.id == asker_id)
        result = await self.db.execute(stmt)
        asker = result.scalar_one_or_none()

        if asker is None:
            raise ValueError(f"Asker not found: {asker_id}")

        # Get appropriate responder using routing engine
        responder = await self.routing_engine.get_responder(
            squad_id=asker.squad_id,
            asker_role=asker.role,
            question_type=question_type,
            escalation_level=0
        )

        if responder is None:
            raise ValueError(
                f"No responder found for {asker.role} asking {question_type} questions"
            )

        # Send question message via message bus
        message = await self.message_bus.send_message(
            sender_id=asker_id,
            recipient_id=responder.id,
            content=question_content,
            message_type="question",
            task_execution_id=task_execution_id,
            db=self.db
        )

        # Create conversation record
        timeout_at = datetime.utcnow() + timedelta(
            seconds=self.config.timeouts.initial_timeout_seconds
        )

        conversation = Conversation(
            id=uuid4(),
            initial_message_id=message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=asker_id,
            current_responder_id=responder.id,
            escalation_level=0,
            question_type=question_type,
            task_execution_id=task_execution_id,
            timeout_at=timeout_at,
            conv_metadata=metadata or {}
        )

        self.db.add(conversation)

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="initiated",
            from_state=None,
            to_state=ConversationState.INITIATED.value,
            message_id=message.id,
            triggered_by_agent_id=asker_id,
            event_data={
                "question_type": question_type,
                "responder_role": responder.role
            }
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def acknowledge_conversation(
        self,
        conversation_id: UUID,
        responder_id: UUID,
        custom_message: Optional[str] = None
    ) -> None:
        """
        Acknowledge a conversation (responder confirms they received the question)

        Steps:
        1. Update conversation state to WAITING
        2. Set acknowledged_at timestamp
        3. Reset timeout
        4. Send acknowledgment message
        5. Create conversation event

        Args:
            conversation_id: ID of the conversation
            responder_id: ID of the responder acknowledging
            custom_message: Optional custom acknowledgment message

        Raises:
            ValueError: If conversation not found or in wrong state
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        if conversation.current_state != ConversationState.INITIATED.value:
            raise ValueError(
                f"Cannot acknowledge conversation in state: {conversation.current_state}"
            )

        # Update conversation
        conversation.current_state = ConversationState.WAITING.value
        conversation.acknowledged_at = datetime.utcnow()
        conversation.timeout_at = datetime.utcnow() + timedelta(
            seconds=self.config.timeouts.initial_timeout_seconds
        )

        # Send acknowledgment message
        ack_message = custom_message or self.config.get_message_template("acknowledgment")

        message = await self.message_bus.send_message(
            sender_id=responder_id,
            recipient_id=conversation.asker_id,
            content=ack_message,
            message_type="acknowledgment",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation_id,
            event_type="acknowledged",
            from_state=ConversationState.INITIATED.value,
            to_state=ConversationState.WAITING.value,
            message_id=message.id,
            triggered_by_agent_id=responder_id
        )

        self.db.add(event)
        await self.db.commit()

    async def answer_conversation(
        self,
        conversation_id: UUID,
        responder_id: UUID,
        answer_content: str
    ) -> None:
        """
        Answer a conversation (provide the final answer)

        Steps:
        1. Update conversation state to ANSWERED
        2. Set resolved_at timestamp
        3. Clear timeout
        4. Send answer message
        5. Create conversation event

        Args:
            conversation_id: ID of the conversation
            responder_id: ID of the responder providing the answer
            answer_content: Content of the answer

        Raises:
            ValueError: If conversation not found
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Update conversation
        old_state = conversation.current_state
        conversation.current_state = ConversationState.ANSWERED.value
        conversation.resolved_at = datetime.utcnow()
        conversation.timeout_at = None

        # Send answer message
        message = await self.message_bus.send_message(
            sender_id=responder_id,
            recipient_id=conversation.asker_id,
            content=answer_content,
            message_type="answer",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation_id,
            event_type="answered",
            from_state=old_state,
            to_state=ConversationState.ANSWERED.value,
            message_id=message.id,
            triggered_by_agent_id=responder_id
        )

        self.db.add(event)
        await self.db.commit()

    async def cancel_conversation(
        self,
        conversation_id: UUID,
        cancelled_by_id: UUID,
        reason: Optional[str] = None
    ) -> None:
        """
        Cancel a conversation

        Args:
            conversation_id: ID of the conversation
            cancelled_by_id: ID of the agent cancelling
            reason: Optional cancellation reason
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Update conversation
        old_state = conversation.current_state
        conversation.current_state = ConversationState.CANCELLED.value
        conversation.timeout_at = None

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation_id,
            event_type="cancelled",
            from_state=old_state,
            to_state=ConversationState.CANCELLED.value,
            message_id=None,
            triggered_by_agent_id=cancelled_by_id,
            event_data={"reason": reason} if reason else {}
        )

        self.db.add(event)
        await self.db.commit()

    async def get_conversation_timeline(self, conversation_id: UUID) -> dict:
        """
        Get complete timeline of a conversation with all events

        Args:
            conversation_id: ID of the conversation

        Returns:
            Dictionary with conversation details and event timeline
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Get all events
        stmt = select(ConversationEvent).where(
            ConversationEvent.conversation_id == conversation_id
        ).order_by(ConversationEvent.created_at)

        result = await self.db.execute(stmt)
        events = result.scalars().all()

        # Build timeline
        return {
            "conversation_id": str(conversation.id),
            "asker_id": str(conversation.asker_id),
            "current_responder_id": str(conversation.current_responder_id),
            "current_state": conversation.current_state,
            "escalation_level": conversation.escalation_level,
            "question_type": conversation.question_type,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "acknowledged_at": conversation.acknowledged_at.isoformat() if conversation.acknowledged_at else None,
            "resolved_at": conversation.resolved_at.isoformat() if conversation.resolved_at else None,
            "timeout_at": conversation.timeout_at.isoformat() if conversation.timeout_at else None,
            "events": [
                {
                    "event_type": e.event_type,
                    "from_state": e.from_state,
                    "to_state": e.to_state,
                    "triggered_by_agent_id": str(e.triggered_by_agent_id) if e.triggered_by_agent_id else None,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "event_data": e.event_data
                }
                for e in events
            ]
        }
