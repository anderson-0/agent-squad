"""
Conversation Service - Business Logic for Multi-Turn Conversations

Handles:
- Creating and managing conversations (user-agent, agent-agent, multi-party)
- Sending messages and getting responses
- Managing conversation context
- Participant management
- Conversation lifecycle (active, archived, closed)
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import (
    MultiTurnConversation,
    ConversationMessage,
    ConversationParticipant,
    User,
    SquadMember
)
from backend.core.logging import logger


class ConversationService:
    """Service for managing multi-turn conversations"""

    # ============================================================================
    # CONVERSATION CREATION
    # ============================================================================

    @staticmethod
    async def create_user_agent_conversation(
        db: AsyncSession,
        user_id: uuid.UUID,
        agent_id: uuid.UUID,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MultiTurnConversation:
        """
        Create a new user-agent conversation.

        Args:
            db: Database session
            user_id: UUID of the user
            agent_id: UUID of the squad member (agent)
            title: Optional conversation title
            tags: Optional list of tags
            metadata: Optional metadata dict

        Returns:
            Created MultiTurnConversation
        """
        # Verify user and agent exist
        user = await db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        agent = await db.get(SquadMember, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Create conversation
        conversation = MultiTurnConversation(
            id=uuid.uuid4(),
            conversation_type="user_agent",
            initiator_id=user_id,
            initiator_type="user",
            primary_responder_id=agent_id,
            user_id=user_id,
            title=title or f"Conversation with {agent.role}",
            status="active",
            tags=tags or [],
            conv_metadata=metadata or {}
        )

        db.add(conversation)

        # Add participants
        user_participant = ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=user_id,
            participant_type="user",
            role="initiator",
            is_active=True
        )
        agent_participant = ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=agent_id,
            participant_type="agent",
            role="responder",
            is_active=True
        )

        db.add_all([user_participant, agent_participant])
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created user-agent conversation {conversation.id}: user={user_id}, agent={agent_id}")
        return conversation

    @staticmethod
    async def create_agent_agent_conversation(
        db: AsyncSession,
        initiator_agent_id: uuid.UUID,
        responder_agent_id: uuid.UUID,
        title: Optional[str] = None,
        agent_conversation_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MultiTurnConversation:
        """
        Create a new agent-agent conversation.

        Args:
            db: Database session
            initiator_agent_id: UUID of the initiating agent
            responder_agent_id: UUID of the responding agent
            title: Optional conversation title
            agent_conversation_id: Optional link to hierarchical routing conversation
            tags: Optional list of tags
            metadata: Optional metadata dict

        Returns:
            Created MultiTurnConversation
        """
        # Verify both agents exist
        initiator = await db.get(SquadMember, initiator_agent_id)
        if not initiator:
            raise ValueError(f"Initiator agent {initiator_agent_id} not found")

        responder = await db.get(SquadMember, responder_agent_id)
        if not responder:
            raise ValueError(f"Responder agent {responder_agent_id} not found")

        # Create conversation
        conversation = MultiTurnConversation(
            id=uuid.uuid4(),
            conversation_type="agent_agent",
            initiator_id=initiator_agent_id,
            initiator_type="agent",
            primary_responder_id=responder_agent_id,
            user_id=None,  # No user for agent-agent conversations
            agent_conversation_id=agent_conversation_id,
            title=title or f"{initiator.role} → {responder.role}",
            status="active",
            tags=tags or [],
            conv_metadata=metadata or {}
        )

        db.add(conversation)

        # Add participants
        initiator_participant = ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=initiator_agent_id,
            participant_type="agent",
            role="initiator",
            is_active=True
        )
        responder_participant = ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            participant_id=responder_agent_id,
            participant_type="agent",
            role="responder",
            is_active=True
        )

        db.add_all([initiator_participant, responder_participant])
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created agent-agent conversation {conversation.id}: {initiator_agent_id} → {responder_agent_id}")
        return conversation

    # ============================================================================
    # MESSAGE SENDING
    # ============================================================================

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        sender_type: str,  # 'user' or 'agent'
        content: str,
        role: str = "user",  # 'user', 'assistant', 'system'
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        model_used: Optional[str] = None,
        temperature: Optional[float] = None,
        llm_provider: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        agent_message_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Send a message in a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            sender_id: UUID of the sender (user or agent)
            sender_type: 'user' or 'agent'
            content: Message content
            role: Message role for LLM context ('user', 'assistant', 'system')
            input_tokens: Optional input token count
            output_tokens: Optional output token count
            model_used: Optional model identifier
            temperature: Optional temperature parameter
            llm_provider: Optional LLM provider name
            response_time_ms: Optional response time in milliseconds
            agent_message_id: Optional link to hierarchical routing message
            metadata: Optional metadata dict

        Returns:
            Created ConversationMessage
        """
        # Verify conversation exists
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.status != "active":
            raise ValueError(f"Conversation {conversation_id} is not active (status: {conversation.status})")

        # Calculate total tokens
        total_tokens = None
        if input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens

        # Create message
        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model_used=model_used,
            temperature=temperature,
            llm_provider=llm_provider,
            response_time_ms=response_time_ms,
            agent_message_id=agent_message_id,
            conv_metadata=metadata or {}
        )

        db.add(message)

        # Update conversation stats
        conversation.total_messages += 1
        if total_tokens:
            conversation.total_tokens_used += total_tokens
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(message)

        logger.debug(f"Message sent in conversation {conversation_id}: {sender_type} {sender_id}")
        return message

    # ============================================================================
    # CONVERSATION RETRIEVAL
    # ============================================================================

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        include_messages: bool = False,
        include_participants: bool = False
    ) -> Optional[MultiTurnConversation]:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            include_messages: Whether to eagerly load messages
            include_participants: Whether to eagerly load participants

        Returns:
            MultiTurnConversation or None if not found
        """
        query = select(MultiTurnConversation).where(MultiTurnConversation.id == conversation_id)

        if include_messages:
            query = query.options(selectinload(MultiTurnConversation.messages))
        if include_participants:
            query = query.options(selectinload(MultiTurnConversation.participants))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
        max_tokens: Optional[int] = None
    ) -> Tuple[List[ConversationMessage], int]:
        """
        Get message history for a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            limit: Maximum number of messages to return
            offset: Offset for pagination
            max_tokens: Optional maximum total tokens to include (for context window management)

        Returns:
            Tuple of (messages list, total_count)
        """
        # Count total messages
        count_query = select(func.count(ConversationMessage.id)).where(
            ConversationMessage.conversation_id == conversation_id
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Get messages (ordered by creation time, oldest first)
        query = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        messages = list(result.scalars().all())

        # If max_tokens specified, trim from the beginning
        if max_tokens and messages:
            token_sum = 0
            trimmed_messages = []
            for msg in reversed(messages):  # Start from most recent
                msg_tokens = msg.total_tokens or 0
                if token_sum + msg_tokens <= max_tokens:
                    trimmed_messages.insert(0, msg)
                    token_sum += msg_tokens
                else:
                    break
            messages = trimmed_messages

        return messages, total_count

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[MultiTurnConversation], int]:
        """
        Get all conversations for a user.

        Args:
            db: Database session
            user_id: UUID of the user
            status: Optional status filter ('active', 'archived', 'closed')
            limit: Maximum number of conversations to return
            offset: Offset for pagination

        Returns:
            Tuple of (conversations list, total_count)
        """
        # Build filters
        filters = [MultiTurnConversation.user_id == user_id]
        if status:
            filters.append(MultiTurnConversation.status == status)

        # Count total
        count_query = select(func.count(MultiTurnConversation.id)).where(and_(*filters))
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Get conversations (ordered by last message time, most recent first)
        query = (
            select(MultiTurnConversation)
            .where(and_(*filters))
            .order_by(desc(MultiTurnConversation.last_message_at))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        conversations = list(result.scalars().all())

        return conversations, total_count

    @staticmethod
    async def get_agent_conversations(
        db: AsyncSession,
        agent_id: uuid.UUID,
        conversation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[MultiTurnConversation], int]:
        """
        Get all conversations for an agent.

        Args:
            db: Database session
            agent_id: UUID of the agent
            conversation_type: Optional type filter ('user_agent', 'agent_agent', 'multi_party')
            status: Optional status filter ('active', 'archived', 'closed')
            limit: Maximum number of conversations to return
            offset: Offset for pagination

        Returns:
            Tuple of (conversations list, total_count)
        """
        # Build filters - agent is either primary responder or initiator
        agent_filter = or_(
            MultiTurnConversation.primary_responder_id == agent_id,
            and_(
                MultiTurnConversation.initiator_id == agent_id,
                MultiTurnConversation.initiator_type == "agent"
            )
        )

        filters = [agent_filter]
        if conversation_type:
            filters.append(MultiTurnConversation.conversation_type == conversation_type)
        if status:
            filters.append(MultiTurnConversation.status == status)

        # Count total
        count_query = select(func.count(MultiTurnConversation.id)).where(and_(*filters))
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Get conversations
        query = (
            select(MultiTurnConversation)
            .where(and_(*filters))
            .order_by(desc(MultiTurnConversation.last_message_at))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        conversations = list(result.scalars().all())

        return conversations, total_count

    # ============================================================================
    # CONVERSATION MANAGEMENT
    # ============================================================================

    @staticmethod
    async def archive_conversation(
        db: AsyncSession,
        conversation_id: uuid.UUID
    ) -> MultiTurnConversation:
        """
        Archive a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation

        Returns:
            Updated conversation
        """
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.status = "archived"
        conversation.archived_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Archived conversation {conversation_id}")
        return conversation

    @staticmethod
    async def close_conversation(
        db: AsyncSession,
        conversation_id: uuid.UUID
    ) -> MultiTurnConversation:
        """
        Close a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation

        Returns:
            Updated conversation
        """
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.status = "closed"
        conversation.updated_at = datetime.utcnow()

        # Deactivate all participants
        result = await db.execute(
            select(ConversationParticipant)
            .where(ConversationParticipant.conversation_id == conversation_id)
        )
        participants = result.scalars().all()
        for participant in participants:
            participant.is_active = False
            participant.left_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Closed conversation {conversation_id}")
        return conversation

    @staticmethod
    async def update_conversation_title(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        title: str
    ) -> MultiTurnConversation:
        """
        Update conversation title.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            title: New title

        Returns:
            Updated conversation
        """
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.title = title
        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        return conversation

    @staticmethod
    async def update_conversation_summary(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        summary: str
    ) -> MultiTurnConversation:
        """
        Update conversation summary.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            summary: Conversation summary

        Returns:
            Updated conversation
        """
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.summary = summary
        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        return conversation

    # ============================================================================
    # PARTICIPANT MANAGEMENT
    # ============================================================================

    @staticmethod
    async def add_participant(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        participant_id: uuid.UUID,
        participant_type: str,  # 'user' or 'agent'
        role: str = "observer",  # 'observer', 'responder', 'moderator'
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationParticipant:
        """
        Add a participant to a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            participant_id: UUID of the participant
            participant_type: 'user' or 'agent'
            role: Participant role
            metadata: Optional metadata dict

        Returns:
            Created ConversationParticipant
        """
        conversation = await db.get(MultiTurnConversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Check if participant already exists
        existing = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id == participant_id,
                    ConversationParticipant.participant_type == participant_type,
                    ConversationParticipant.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Participant {participant_id} already active in conversation {conversation_id}")

        participant = ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            participant_id=participant_id,
            participant_type=participant_type,
            role=role,
            is_active=True,
            conv_metadata=metadata or {}
        )

        db.add(participant)

        # Update conversation to multi_party if needed
        if conversation.conversation_type != "multi_party":
            conversation.conversation_type = "multi_party"
            conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(participant)

        logger.info(f"Added participant {participant_type} {participant_id} to conversation {conversation_id}")
        return participant

    @staticmethod
    async def remove_participant(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        participant_id: uuid.UUID,
        participant_type: str
    ) -> ConversationParticipant:
        """
        Remove (deactivate) a participant from a conversation.

        Args:
            db: Database session
            conversation_id: UUID of the conversation
            participant_id: UUID of the participant
            participant_type: 'user' or 'agent'

        Returns:
            Updated ConversationParticipant
        """
        result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id == participant_id,
                    ConversationParticipant.participant_type == participant_type,
                    ConversationParticipant.is_active == True
                )
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            raise ValueError(
                f"Active participant {participant_type} {participant_id} not found in conversation {conversation_id}"
            )

        participant.is_active = False
        participant.left_at = datetime.utcnow()

        await db.commit()
        await db.refresh(participant)

        logger.info(f"Removed participant {participant_type} {participant_id} from conversation {conversation_id}")
        return participant
