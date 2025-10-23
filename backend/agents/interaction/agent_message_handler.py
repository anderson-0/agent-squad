"""
Agent Message Handler

Processes incoming messages and triggers agent responses.

This is the glue between the message bus and the agent processing logic.
When an agent receives a message, this handler:
1. Retrieves the agent's configuration
2. Creates/retrieves the BaseAgent instance
3. Calls process_message() to get LLM response
4. Sends the response back via message bus
5. Updates conversation state

Created: October 22, 2025
"""
from typing import Optional
from uuid import UUID
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import SquadMember, AgentMessage
from backend.models.conversation import Conversation
from backend.agents.factory import AgentFactory
from backend.agents.communication.message_bus import get_message_bus
from backend.agents.interaction.conversation_manager import ConversationManager


logger = logging.getLogger(__name__)


class AgentMessageHandler:
    """
    Handles incoming messages and triggers agent processing.

    This is the core service that makes agents actually "think" and respond.
    It bridges the gap between message routing and AI processing.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize agent message handler.

        Args:
            db: Database session
        """
        self.db = db
        self.message_bus = get_message_bus()
        self.conversation_manager = ConversationManager(db)
        self._processing_lock = asyncio.Lock()

    async def process_incoming_message(
        self,
        message_id: UUID,
        recipient_id: UUID,
        sender_id: UUID,
        content: str,
        message_type: str,
        conversation_id: Optional[UUID] = None
    ) -> None:
        """
        Process an incoming message and generate agent response.

        This is the main entry point. When called, it:
        1. Loads the recipient agent's configuration
        2. Creates a BaseAgent instance
        3. Builds conversation context
        4. Calls the agent's LLM to generate a response
        5. Sends the response back via message bus
        6. Updates the conversation state

        Args:
            message_id: ID of the message to process
            recipient_id: Agent who should respond (SquadMember ID)
            sender_id: Agent who sent the message (SquadMember ID)
            content: Message content (the question/request)
            message_type: Type of message (question, task_assignment, etc.)
            conversation_id: Optional conversation ID for context

        Raises:
            ValueError: If agent not found
            Exception: If LLM processing fails
        """

        # Only process certain message types
        if message_type not in ['question', 'task_assignment', 'code_review_request']:
            logger.debug(f"Skipping message type: {message_type}")
            return

        logger.info(
            f"Processing message {message_id} for agent {recipient_id} "
            f"(type: {message_type})"
        )

        try:
            # Get recipient agent configuration
            stmt = select(SquadMember).where(SquadMember.id == recipient_id)
            result = await self.db.execute(stmt)
            agent_member = result.scalar_one_or_none()

            if not agent_member:
                logger.error(f"Agent not found: {recipient_id}")
                raise ValueError(f"Agent not found: {recipient_id}")

            logger.info(
                f"Agent loaded: {agent_member.role} "
                f"({agent_member.llm_provider}/{agent_member.llm_model})"
            )

            # Create or retrieve agent instance
            agent = AgentFactory.create_agent(
                agent_id=recipient_id,
                role=agent_member.role,
                llm_provider=agent_member.llm_provider or "openai",
                llm_model=agent_member.llm_model or "gpt-4",
                specialization=agent_member.specialization,
                temperature=0.7
            )

            # Build conversation context
            context = await self._build_conversation_context(
                conversation_id=conversation_id,
                agent_id=recipient_id
            )

            logger.info(f"Context built for conversation {conversation_id}")
            logger.debug(f"Context: {context}")

            # Process message with agent's LLM (using streaming)
            logger.info(f"🤖 {agent_member.role} is thinking...")
            print(f"🤖 {agent_member.role} is processing message...")

            # Track streaming response
            streamed_response = ""
            from datetime import datetime
            from uuid import uuid4

            # Get SSE manager for broadcasting
            try:
                from backend.services.sse_service import sse_manager
                has_sse = True
            except ImportError:
                logger.warning("SSE service not available, streaming will work but not broadcast to frontend")
                has_sse = False

            # Get task_execution_id from conversation metadata if available
            task_execution_id = None
            if conversation_id:
                try:
                    stmt = select(Conversation).where(Conversation.id == conversation_id)
                    result = await self.db.execute(stmt)
                    conv = result.scalar_one_or_none()
                    if conv and conv.task_execution_id:
                        task_execution_id = conv.task_execution_id
                except Exception as e:
                    logger.debug(f"Could not get task_execution_id: {e}")

            # Define token callback for streaming
            async def on_token(token: str):
                """Callback for each token - broadcast via SSE if available"""
                nonlocal streamed_response
                streamed_response += token

                # Broadcast streaming update via SSE
                if has_sse and task_execution_id:
                    try:
                        await sse_manager.broadcast_to_execution(
                            execution_id=task_execution_id,
                            event="answer_streaming",
                            data={
                                "token": token,
                                "partial_response": streamed_response,
                                "agent_id": str(recipient_id),
                                "agent_role": agent_member.role,
                                "conversation_id": str(conversation_id) if conversation_id else None,
                                "is_streaming": True,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    except Exception as e:
                        logger.debug(f"SSE broadcast failed (non-critical): {e}")

                logger.debug(f"Streaming token: {token[:20]}...")

            # Use streaming for real-time responses
            response = await agent.process_message_streaming(
                message=content,
                context=context,
                on_token=on_token
            )

            logger.info(
                f"Agent {agent_member.role} generated response "
                f"({len(response.content)} chars)"
            )

            # Send final streaming complete event via SSE
            if has_sse and task_execution_id:
                try:
                    await sse_manager.broadcast_to_execution(
                        execution_id=task_execution_id,
                        event="answer_complete",
                        data={
                            "complete_response": response.content,
                            "agent_id": str(recipient_id),
                            "agent_role": agent_member.role,
                            "conversation_id": str(conversation_id) if conversation_id else None,
                            "is_streaming": False,
                            "total_length": len(response.content),
                            "timestamp": datetime.utcnow().isoformat(),
                            "metadata": response.metadata
                        }
                    )
                except Exception as e:
                    logger.debug(f"Final SSE broadcast failed (non-critical): {e}")

            # Send response back via message bus
            await self.message_bus.send_message(
                sender_id=recipient_id,
                recipient_id=sender_id,
                content=response.content,
                message_type="answer",
                metadata={
                    "thinking": response.thinking if hasattr(response, 'thinking') else None,
                    "confidence": response.metadata.get("confidence") if hasattr(response, 'metadata') else None,
                    "original_question": content[:100],  # First 100 chars of question
                },
                task_execution_id=None,
                conversation_id=conversation_id,
                db=self.db
            )

            logger.info("Response sent via message bus")

            # Update conversation state to answered
            if conversation_id:
                await self.conversation_manager.answer_conversation(
                    conversation_id=conversation_id,
                    responder_id=recipient_id,
                    answer_content=response.content
                )
                logger.info(f"Conversation {conversation_id} marked as answered")

            print(f"✅ {agent_member.role} responded successfully")
            logger.info(
                f"Successfully processed message {message_id} - "
                f"conversation {conversation_id} is now answered"
            )

        except Exception as e:
            logger.error(
                f"Error processing message {message_id}: {e}",
                exc_info=True
            )
            print(f"❌ Error processing message: {e}")

            # If we have a conversation, mark it as failed
            if conversation_id:
                try:
                    # We could add a "failed" state or leave it in waiting
                    # For now, just log the error
                    logger.error(f"Conversation {conversation_id} failed to get response")
                except Exception as inner_e:
                    logger.error(f"Error updating failed conversation: {inner_e}")

            raise

    async def _build_conversation_context(
        self,
        conversation_id: Optional[UUID],
        agent_id: UUID
    ) -> dict:
        """
        Build context from conversation history.

        This enriches the agent's prompt with relevant context:
        - Agent's role
        - Question type
        - Escalation level
        - Previous conversation events

        Args:
            conversation_id: Conversation ID to get history from
            agent_id: Agent ID for role-specific context

        Returns:
            Context dictionary with conversation history and metadata
        """
        if not conversation_id:
            logger.debug("No conversation_id provided, returning empty context")
            return {}

        try:
            # Get conversation
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await self.db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {}

            # Get agent's role for context
            stmt = select(SquadMember).where(SquadMember.id == agent_id)
            result = await self.db.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                logger.warning(f"Agent not found: {agent_id}")
                return {}

            # Get conversation timeline for events
            timeline = await self.conversation_manager.get_conversation_timeline(
                conversation_id
            )

            context = {
                "conversation_id": str(conversation_id),
                "agent_role": agent.role,
                "agent_specialization": agent.specialization,
                "conversation_state": conversation.current_state,
                "question_type": conversation.question_type,
                "escalation_level": conversation.escalation_level,
                "conversation_events": timeline.get("events", []),
                "conversation_metadata": conversation.conv_metadata or {}
            }

            logger.debug(
                f"Built context for conversation {conversation_id}: "
                f"role={agent.role}, type={conversation.question_type}, "
                f"escalation={conversation.escalation_level}"
            )

            return context

        except Exception as e:
            logger.error(
                f"Error building conversation context for {conversation_id}: {e}",
                exc_info=True
            )
            # Return minimal context on error
            return {
                "conversation_id": str(conversation_id),
                "error": f"Failed to build full context: {str(e)}"
            }

    async def process_message_async(
        self,
        message_id: UUID,
        recipient_id: UUID,
        sender_id: UUID,
        content: str,
        message_type: str,
        conversation_id: Optional[UUID] = None
    ) -> None:
        """
        Process message asynchronously without blocking.

        This is a convenience wrapper that creates a background task.
        Useful when you want to trigger processing but not wait for it.

        Args:
            message_id: Message ID
            recipient_id: Recipient agent ID
            sender_id: Sender agent ID
            content: Message content
            message_type: Message type
            conversation_id: Optional conversation ID
        """
        asyncio.create_task(
            self.process_incoming_message(
                message_id=message_id,
                recipient_id=recipient_id,
                sender_id=sender_id,
                content=content,
                message_type=message_type,
                conversation_id=conversation_id
            )
        )
        logger.info(f"Created background task to process message {message_id}")
