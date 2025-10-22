"""
Escalation Service

Handles escalating conversations to the next level in the hierarchy when:
- Initial responder times out
- Responder explicitly requests escalation ("can't help")
- Maximum retries exceeded
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
    SquadMember
)
from backend.agents.interaction.routing_engine import RoutingEngine
from backend.agents.configuration.interaction_config import InteractionConfig, get_interaction_config
from backend.agents.communication.message_bus import get_message_bus


class EscalationService:
    """
    Service for escalating conversations to next level

    Handles:
    - Automatic escalation after timeouts
    - Manual escalation ("can't help" requests)
    - Notification to asker and new responder
    - Updating conversation state and escalation level
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[InteractionConfig] = None
    ):
        """
        Initialize escalation service

        Args:
            db: Database session
            config: Interaction configuration
        """
        self.db = db
        self.config = config or get_interaction_config()
        self.routing_engine = RoutingEngine(db)
        self.message_bus = get_message_bus()

    async def escalate_conversation(
        self,
        conversation_id: UUID,
        reason: str = "timeout",
        triggered_by_agent_id: Optional[UUID] = None
    ) -> bool:
        """
        Escalate a conversation to the next level

        Steps:
        1. Get current conversation state
        2. Query routing engine for next level responder
        3. If no next level exists, mark as unresolvable
        4. Update conversation (responder, escalation level, timeout)
        5. Send notification to asker about escalation
        6. Send context to new responder
        7. Create conversation events

        Args:
            conversation_id: ID of conversation to escalate
            reason: Reason for escalation (timeout, cant_help, etc.)
            triggered_by_agent_id: ID of agent triggering escalation (None for system)

        Returns:
            True if escalated successfully, False if no next level available

        Raises:
            ValueError: If conversation not found
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Get asker to determine squad
        stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
        result = await self.db.execute(stmt)
        asker = result.scalar_one_or_none()

        if asker is None:
            raise ValueError(f"Asker not found: {conversation.asker_id}")

        # Get current responder for notifications
        stmt = select(SquadMember).where(
            SquadMember.id == conversation.current_responder_id
        )
        result = await self.db.execute(stmt)
        current_responder = result.scalar_one_or_none()

        # Query routing engine for next level responder
        next_level = conversation.escalation_level + 1
        next_responder = await self.routing_engine.get_responder(
            squad_id=asker.squad_id,
            asker_role=asker.role,
            question_type=conversation.question_type,
            escalation_level=next_level
        )

        if next_responder is None:
            # No next level available - mark as unresolvable
            await self._mark_unresolvable(conversation, reason)
            return False

        # Update conversation state
        old_state = conversation.current_state
        conversation.current_state = ConversationState.ESCALATED.value
        conversation.current_responder_id = next_responder.id
        conversation.escalation_level = next_level
        conversation.timeout_at = datetime.utcnow() + timedelta(
            seconds=self.config.timeouts.initial_timeout_seconds
        )

        # Send escalation notification to asker
        escalation_msg = self.config.get_message_template(
            "escalation_notification",
            previous_responder=current_responder.role if current_responder else "previous agent",
            new_responder=next_responder.role
        )

        await self.message_bus.send_message(
            sender_id=None,  # System message
            recipient_id=conversation.asker_id,
            content=escalation_msg,
            message_type="escalation_notification",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Get original question content
        stmt = select(AgentMessage).where(
            AgentMessage.id == conversation.initial_message_id
        )
        from backend.models import AgentMessage
        result = await self.db.execute(stmt)
        original_message = result.scalar_one_or_none()

        # Send context to new responder
        escalation_context = self.config.get_message_template(
            "escalation_context",
            previous_responder=current_responder.role if current_responder else "previous agent",
            original_question=original_message.content if original_message else "N/A"
        )

        message = await self.message_bus.send_message(
            sender_id=conversation.asker_id,
            recipient_id=next_responder.id,
            content=escalation_context,
            message_type="escalated_question",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation_id,
            event_type="escalated",
            from_state=old_state,
            to_state=ConversationState.ESCALATED.value,
            message_id=message.id,
            triggered_by_agent_id=triggered_by_agent_id,
            event_data={
                "reason": reason,
                "from_agent_id": str(conversation.current_responder_id) if current_responder else None,
                "to_agent_id": str(next_responder.id),
                "escalation_level": next_level,
                "previous_responder_role": current_responder.role if current_responder else None,
                "new_responder_role": next_responder.role
            }
        )

        self.db.add(event)
        await self.db.commit()

        return True

    async def _mark_unresolvable(
        self,
        conversation: Conversation,
        reason: str
    ) -> None:
        """
        Mark a conversation as unresolvable (no next level available)

        Args:
            conversation: Conversation object
            reason: Reason for being unresolvable
        """
        old_state = conversation.current_state
        conversation.current_state = "unresolvable"  # Special state
        conversation.timeout_at = None

        # Send notification to asker
        unresolvable_msg = (
            f"I'm sorry, but I couldn't find anyone to help with your question. "
            f"The escalation chain has been exhausted. Reason: {reason}"
        )

        message = await self.message_bus.send_message(
            sender_id=None,  # System message
            recipient_id=conversation.asker_id,
            content=unresolvable_msg,
            message_type="unresolvable_notification",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create conversation event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="unresolvable",
            from_state=old_state,
            to_state="unresolvable",
            message_id=message.id,
            triggered_by_agent_id=None,  # System triggered
            event_data={
                "reason": reason,
                "escalation_level_reached": conversation.escalation_level
            }
        )

        self.db.add(event)
        await self.db.commit()

    async def handle_cant_help(
        self,
        conversation_id: UUID,
        current_responder_id: UUID,
        target_role: Optional[str] = None
    ) -> bool:
        """
        Handle "can't help" request from current responder

        When an agent explicitly says they can't help, we can either:
        1. Route to a specific role (if target_role provided)
        2. Escalate to next level in hierarchy

        Args:
            conversation_id: ID of conversation
            current_responder_id: ID of responder who can't help
            target_role: Optional specific role to route to

        Returns:
            True if successfully routed/escalated, False otherwise
        """
        # Get conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        if conversation.current_responder_id != current_responder_id:
            raise ValueError(
                "Only the current responder can request routing"
            )

        # Create "cant_help" event
        old_state = conversation.current_state

        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation_id,
            event_type="cant_help",
            from_state=old_state,
            to_state=old_state,  # State doesn't change yet
            message_id=None,
            triggered_by_agent_id=current_responder_id,
            event_data={
                "target_role": target_role,
                "action": "routing" if target_role else "escalating"
            }
        )

        self.db.add(event)

        if target_role:
            # Try to route to specific role
            success = await self._route_to_role(
                conversation=conversation,
                target_role=target_role,
                triggered_by_agent_id=current_responder_id
            )
            await self.db.commit()
            return success
        else:
            # Escalate to next level
            await self.db.commit()  # Commit cant_help event first
            return await self.escalate_conversation(
                conversation_id=conversation_id,
                reason="cant_help",
                triggered_by_agent_id=current_responder_id
            )

    async def _route_to_role(
        self,
        conversation: Conversation,
        target_role: str,
        triggered_by_agent_id: UUID
    ) -> bool:
        """
        Route conversation to a specific role

        Args:
            conversation: Conversation object
            target_role: Role to route to
            triggered_by_agent_id: ID of agent triggering the route

        Returns:
            True if successfully routed, False if role not found
        """
        # Find agent with target role in the same squad
        stmt = select(SquadMember).where(
            SquadMember.id == conversation.asker_id
        )
        result = await self.db.execute(stmt)
        asker = result.scalar_one_or_none()

        if asker is None:
            return False

        # Find target agent
        stmt = select(SquadMember).where(
            SquadMember.squad_id == asker.squad_id,
            SquadMember.role == target_role,
            SquadMember.is_active == True
        ).limit(1)

        result = await self.db.execute(stmt)
        target_agent = result.scalar_one_or_none()

        if target_agent is None:
            return False

        # Get current responder for notification
        stmt = select(SquadMember).where(
            SquadMember.id == conversation.current_responder_id
        )
        result = await self.db.execute(stmt)
        current_responder = result.scalar_one()

        # Update conversation
        conversation.current_responder_id = target_agent.id
        conversation.timeout_at = datetime.utcnow() + timedelta(
            seconds=self.config.timeouts.initial_timeout_seconds
        )

        # Send routing message
        routing_msg = self.config.get_message_template(
            "cant_help_routing",
            expert_role=target_role
        )

        # Get original question
        stmt = select(AgentMessage).where(
            AgentMessage.id == conversation.initial_message_id
        )
        from backend.models import AgentMessage
        result = await self.db.execute(stmt)
        original_message = result.scalar_one_or_none()

        # Send to new responder
        message = await self.message_bus.send_message(
            sender_id=conversation.asker_id,
            recipient_id=target_agent.id,
            content=f"{routing_msg}\n\nOriginal question: {original_message.content if original_message else 'N/A'}",
            message_type="routed_question",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="routed",
            from_state=conversation.current_state,
            to_state=conversation.current_state,
            message_id=message.id,
            triggered_by_agent_id=triggered_by_agent_id,
            event_data={
                "from_role": current_responder.role,
                "to_role": target_role,
                "reason": "cant_help"
            }
        )

        self.db.add(event)

        return True
