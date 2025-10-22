"""
Tests for Enhanced Message Bus

Tests for message broadcasting with enriched metadata (agent names, roles, threading).
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.communication.message_bus import MessageBus
from backend.models.squad import SquadMember


@pytest.mark.asyncio
class TestMessageBusWithEnhancedMetadata:
    """Tests for message bus with enhanced metadata"""

    async def test_send_message_with_db_enrichment(self, db_session, sample_squad):
        """Test sending message with database enrichment"""
        # Create squad members
        sender = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        recipient = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="tech_lead",
            specialization=None,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add_all([sender, recipient])
        await db_session.commit()

        # Create message bus
        message_bus = MessageBus()

        # Mock SSE manager
        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Send message with db
            execution_id = uuid4()
            message = await message_bus.send_message(
                sender_id=sender.id,
                recipient_id=recipient.id,
                content="How should I implement caching?",
                message_type="question",
                metadata={"priority": "high"},
                task_execution_id=execution_id,
                db=db_session,
            )

            # Verify message created
            assert message is not None
            assert message.content == "How should I implement caching?"

            # Verify SSE broadcast was called
            mock_sse_instance.broadcast_to_execution.assert_called_once()
            call_args = mock_sse_instance.broadcast_to_execution.call_args

            # Check that enriched data was sent
            data = call_args.kwargs['data']
            assert 'sender_role' in data
            assert data['sender_role'] == "backend_developer"
            assert data['sender_name'] == "Backend Dev (FastAPI)"
            assert data['sender_specialization'] == "python_fastapi"

            assert 'recipient_role' in data
            assert data['recipient_role'] == "tech_lead"
            assert data['recipient_name'] == "Tech Lead"

            assert 'timestamp' in data
            assert data['message_type'] == "question"

    async def test_send_message_without_db(self):
        """Test sending message without database (backward compatibility)"""
        message_bus = MessageBus()
        sender_id = uuid4()
        recipient_id = uuid4()

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Send message without db
            execution_id = uuid4()
            message = await message_bus.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content="Test message",
                message_type="status_update",
                task_execution_id=execution_id,
                # No db parameter
            )

            # Should still work
            assert message is not None

            # SSE should be called but without enriched data
            mock_sse_instance.broadcast_to_execution.assert_called_once()
            call_args = mock_sse_instance.broadcast_to_execution.call_args
            data = call_args.kwargs['data']

            # Should have basic fields
            assert 'message_id' in data
            assert 'sender_id' in data
            assert 'recipient_id' in data
            assert 'content' in data
            assert 'message_type' in data
            assert 'timestamp' in data

            # Should NOT have enriched fields
            assert 'sender_role' not in data
            assert 'sender_name' not in data

    async def test_broadcast_message_with_enrichment(self, db_session, sample_squad):
        """Test broadcast message with enrichment"""
        # Create sender
        sender = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add(sender)
        await db_session.commit()

        message_bus = MessageBus()

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Broadcast message
            execution_id = uuid4()
            message = await message_bus.broadcast_message(
                sender_id=sender.id,
                content="Daily standup starting",
                message_type="standup",
                task_execution_id=execution_id,
                db=db_session,
            )

            # Verify
            assert message is not None

            # Check SSE data
            call_args = mock_sse_instance.broadcast_to_execution.call_args
            data = call_args.kwargs['data']

            assert data['sender_role'] == "project_manager"
            assert data['sender_name'] == "Project Manager"
            assert data['recipient_id'] is None
            assert data['recipient_role'] == "broadcast"
            assert data['recipient_name'] == "All Agents"

    async def test_conversation_threading(self, db_session, sample_squad):
        """Test conversation threading support"""
        # Create members
        sender = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add(sender)
        await db_session.commit()

        message_bus = MessageBus()

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Send message with thread_id in metadata
            execution_id = uuid4()
            message = await message_bus.send_message(
                sender_id=sender.id,
                recipient_id=uuid4(),
                content="Follow-up question",
                message_type="question",
                metadata={"thread_id": "thread-123"},
                task_execution_id=execution_id,
                db=db_session,
            )

            # Check thread ID is included
            call_args = mock_sse_instance.broadcast_to_execution.call_args
            data = call_args.kwargs['data']

            assert 'conversation_thread_id' in data
            assert data['conversation_thread_id'] == "thread-123"

    async def test_sse_enrichment_error_handling(self, db_session, sample_squad):
        """Test that SSE enrichment errors don't break message sending"""
        message_bus = MessageBus()
        sender_id = uuid4()  # Non-existent agent

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Send message with db but non-existent agent
            execution_id = uuid4()
            message = await message_bus.send_message(
                sender_id=sender_id,
                recipient_id=uuid4(),
                content="Test",
                message_type="test",
                task_execution_id=execution_id,
                db=db_session,  # Agent won't be found
            )

            # Should still create message
            assert message is not None

            # SSE should still be called (with basic data)
            mock_sse_instance.broadcast_to_execution.assert_called_once()

    async def test_message_bus_stats_remain_accurate(self):
        """Test that stats are accurate with new changes"""
        message_bus = MessageBus()

        sender_id = uuid4()
        recipient_id = uuid4()

        with patch('backend.agents.communication.message_bus.get_sse_manager'):
            # Send messages
            await message_bus.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content="Message 1",
                message_type="test",
            )

            await message_bus.broadcast_message(
                sender_id=sender_id,
                content="Broadcast",
                message_type="test",
            )

            # Check stats
            stats = message_bus.get_stats()
            assert stats['total_messages'] == 2
            assert stats['broadcast_messages'] == 1


@pytest.mark.asyncio
class TestSSEBroadcastMethod:
    """Tests specifically for _broadcast_to_sse method"""

    async def test_broadcast_to_sse_full_enrichment(self, db_session, sample_squad):
        """Test full SSE broadcast with all enrichments"""
        # Create members
        sender = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        recipient = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="tech_lead",
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add_all([sender, recipient])
        await db_session.commit()

        message_bus = MessageBus()

        # Create mock message
        from backend.schemas.agent_message import AgentMessageResponse
        from datetime import datetime

        mock_message = AgentMessageResponse(
            id=uuid4(),
            task_execution_id=uuid4(),
            sender_id=sender.id,
            recipient_id=recipient.id,
            content="Test content",
            message_type="question",
            message_metadata={},
            created_at=datetime.utcnow()
        )

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            # Call _broadcast_to_sse directly
            await message_bus._broadcast_to_sse(
                execution_id=uuid4(),
                message=mock_message,
                sender_id=sender.id,
                recipient_id=recipient.id,
                content="Test content",
                message_type="question",
                metadata={"thread_id": "thread-123"},
                db=db_session,
            )

            # Verify SSE manager was called
            mock_sse_instance.broadcast_to_execution.assert_called_once()
            call_args = mock_sse_instance.broadcast_to_execution.call_args

            # Verify all expected fields are present
            data = call_args.kwargs['data']
            expected_fields = [
                'message_id', 'sender_id', 'recipient_id', 'content',
                'message_type', 'metadata', 'timestamp',
                'sender_role', 'sender_name', 'sender_specialization',
                'recipient_role', 'recipient_name',
                'conversation_thread_id'
            ]

            for field in expected_fields:
                assert field in data, f"Missing field: {field}"

            # Verify values
            assert data['sender_role'] == "backend_developer"
            assert data['sender_name'] == "Backend Dev (FastAPI)"
            assert data['recipient_role'] == "tech_lead"
            assert data['conversation_thread_id'] == "thread-123"

    async def test_broadcast_to_sse_broadcast_message(self, db_session, sample_squad):
        """Test SSE broadcast for broadcast messages (no specific recipient)"""
        sender = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add(sender)
        await db_session.commit()

        message_bus = MessageBus()

        from backend.schemas.agent_message import AgentMessageResponse
        from datetime import datetime

        mock_message = AgentMessageResponse(
            id=uuid4(),
            task_execution_id=uuid4(),
            sender_id=sender.id,
            recipient_id=None,  # Broadcast
            content="Team announcement",
            message_type="standup",
            message_metadata={},
            created_at=datetime.utcnow()
        )

        with patch('backend.agents.communication.message_bus.get_sse_manager') as mock_sse:
            mock_sse_instance = AsyncMock()
            mock_sse.return_value = mock_sse_instance

            await message_bus._broadcast_to_sse(
                execution_id=uuid4(),
                message=mock_message,
                sender_id=sender.id,
                recipient_id=None,  # Broadcast
                content="Team announcement",
                message_type="standup",
                metadata={},
                db=db_session,
            )

            # Verify broadcast fields
            call_args = mock_sse_instance.broadcast_to_execution.call_args
            data = call_args.kwargs['data']

            assert data['recipient_id'] is None
            assert data['recipient_role'] == "broadcast"
            assert data['recipient_name'] == "All Agents"
