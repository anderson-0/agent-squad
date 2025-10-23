"""
End-to-End Test for Multi-Turn Conversation System

Tests:
1. User-Agent conversations
2. Agent-Agent conversations
3. Message sending and retrieval
4. Conversation history with context
5. Participant management
6. Conversation lifecycle (archive, close)
"""

import asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_context
from backend.models import User, Squad, SquadMember, MultiTurnConversation, ConversationMessage, ConversationParticipant
from backend.services.conversation_service import ConversationService
from backend.core.logging import logger


async def cleanup_test_data(db: AsyncSession, user_id, squad_id):
    """Clean up test data"""
    try:
        from sqlalchemy import delete

        # Delete conversations (cascade will handle messages and participants)
        await db.execute(
            delete(MultiTurnConversation).where(MultiTurnConversation.user_id == user_id)
        )

        # Delete squad members
        await db.execute(
            delete(SquadMember).where(SquadMember.squad_id == squad_id)
        )

        # Delete squad
        await db.execute(delete(Squad).where(Squad.id == squad_id))

        # Delete test user
        await db.execute(delete(User).where(User.id == user_id))

        await db.commit()
    except Exception as e:
        logger.warning(f"Cleanup error (non-critical): {e}")
        await db.rollback()


async def test_multi_turn_conversations():
    """Test the complete multi-turn conversation system"""

    print("=" * 80)
    print("MULTI-TURN CONVERSATION E2E TEST")
    print("=" * 80)

    async with get_db_context() as db:
        # ====================================================================
        # SETUP: Create test user, squad, and agents
        # ====================================================================
        print("\n📦 Setting up test data...")

        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=f"test_conversations_{user_id}@example.com",
            name="Test Conversation User",
            password_hash="fake_hash_for_testing",
            is_active=True
        )
        db.add(test_user)

        squad_id = uuid4()
        squad = Squad(
            id=squad_id,
            name="Test Conversation Squad",
            description="Testing multi-turn conversations",
            user_id=user_id,
            status="active"
        )
        db.add(squad)

        # Create 3 agents
        agent1_id = uuid4()
        agent2_id = uuid4()
        agent3_id = uuid4()

        agent1 = SquadMember(
            id=agent1_id,
            squad_id=squad_id,
            role="frontend_developer",
            specialization="react",
            system_prompt="You are a frontend developer.",
            is_active=True
        )
        agent2 = SquadMember(
            id=agent2_id,
            squad_id=squad_id,
            role="backend_developer",
            specialization="python",
            system_prompt="You are a backend developer.",
            is_active=True
        )
        agent3 = SquadMember(
            id=agent3_id,
            squad_id=squad_id,
            role="tech_lead",
            specialization="architecture",
            system_prompt="You are a tech lead.",
            is_active=True
        )

        db.add_all([agent1, agent2, agent3])
        await db.commit()

        print(f"✅ Created user: {user_id}")
        print(f"✅ Created squad: {squad_id}")
        print(f"✅ Created 3 agents")

        # ====================================================================
        # TEST 1: Create User-Agent Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 1: Create User-Agent Conversation")
        print("=" * 80)

        print("\n📝 Creating user-agent conversation...")
        user_agent_conv = await ConversationService.create_user_agent_conversation(
            db=db,
            user_id=user_id,
            agent_id=agent1_id,
            title="React Component Help",
            tags=["react", "frontend", "help"]
        )

        assert user_agent_conv.conversation_type == "user_agent"
        assert user_agent_conv.initiator_id == user_id
        assert user_agent_conv.initiator_type == "user"
        assert user_agent_conv.primary_responder_id == agent1_id
        assert user_agent_conv.user_id == user_id
        assert user_agent_conv.status == "active"
        print(f"✅ Created user-agent conversation: {user_agent_conv.id}")
        print(f"   Type: {user_agent_conv.conversation_type}")
        print(f"   Title: {user_agent_conv.title}")

        # ====================================================================
        # TEST 2: Send Messages in User-Agent Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 2: Send Messages in User-Agent Conversation")
        print("=" * 80)

        print("\n💬 User sends first message...")
        user_msg1 = await ConversationService.send_message(
            db=db,
            conversation_id=user_agent_conv.id,
            sender_id=user_id,
            sender_type="user",
            content="How do I create a reusable button component in React?",
            role="user"
        )
        assert user_msg1.sender_type == "user"
        assert user_msg1.role == "user"
        print(f"✅ User message sent: {user_msg1.id}")
        print(f"   Content: {user_msg1.content[:50]}...")

        print("\n💬 Agent sends response...")
        agent_msg1 = await ConversationService.send_message(
            db=db,
            conversation_id=user_agent_conv.id,
            sender_id=agent1_id,
            sender_type="agent",
            content="Here's how to create a reusable Button component: ...",
            role="assistant",
            input_tokens=50,
            output_tokens=150,
            model_used="gpt-4",
            llm_provider="openai"
        )
        assert agent_msg1.sender_type == "agent"
        assert agent_msg1.role == "assistant"
        assert agent_msg1.total_tokens == 200
        print(f"✅ Agent message sent: {agent_msg1.id}")
        print(f"   Tokens: {agent_msg1.total_tokens} (in: {agent_msg1.input_tokens}, out: {agent_msg1.output_tokens})")

        print("\n💬 User sends follow-up...")
        user_msg2 = await ConversationService.send_message(
            db=db,
            conversation_id=user_agent_conv.id,
            sender_id=user_id,
            sender_type="user",
            content="Thanks! How do I add TypeScript types?",
            role="user"
        )
        print(f"✅ Follow-up message sent: {user_msg2.id}")

        # ====================================================================
        # TEST 3: Get Conversation History
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 3: Get Conversation History")
        print("=" * 80)

        print("\n📚 Retrieving conversation history...")
        messages, total_count = await ConversationService.get_conversation_history(
            db=db,
            conversation_id=user_agent_conv.id,
            limit=100
        )

        assert total_count == 3
        assert len(messages) == 3
        assert messages[0].id == user_msg1.id
        assert messages[1].id == agent_msg1.id
        assert messages[2].id == user_msg2.id
        print(f"✅ Retrieved {len(messages)} messages (total: {total_count})")
        for i, msg in enumerate(messages, 1):
            print(f"   {i}. {msg.sender_type}: {msg.content[:40]}...")

        # ====================================================================
        # TEST 4: Create Agent-Agent Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 4: Create Agent-Agent Conversation")
        print("=" * 80)

        print("\n📝 Creating agent-agent conversation...")
        agent_agent_conv = await ConversationService.create_agent_agent_conversation(
            db=db,
            initiator_agent_id=agent1_id,
            responder_agent_id=agent2_id,
            title="API Integration Discussion",
            tags=["api", "collaboration"]
        )

        assert agent_agent_conv.conversation_type == "agent_agent"
        assert agent_agent_conv.initiator_id == agent1_id
        assert agent_agent_conv.initiator_type == "agent"
        assert agent_agent_conv.primary_responder_id == agent2_id
        assert agent_agent_conv.user_id is None  # No user for agent-agent
        print(f"✅ Created agent-agent conversation: {agent_agent_conv.id}")
        print(f"   From: {agent1.role} → To: {agent2.role}")

        # ====================================================================
        # TEST 5: Send Messages in Agent-Agent Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 5: Send Messages in Agent-Agent Conversation")
        print("=" * 80)

        print("\n💬 Agent 1 asks Agent 2...")
        agent_q = await ConversationService.send_message(
            db=db,
            conversation_id=agent_agent_conv.id,
            sender_id=agent1_id,
            sender_type="agent",
            content="What's the best way to structure the user authentication API?",
            role="user",
            input_tokens=30,
            output_tokens=0
        )
        print(f"✅ Agent 1 message: {agent_q.id}")

        print("\n💬 Agent 2 responds...")
        agent_a = await ConversationService.send_message(
            db=db,
            conversation_id=agent_agent_conv.id,
            sender_id=agent2_id,
            sender_type="agent",
            content="I recommend using JWT tokens with refresh token rotation...",
            role="assistant",
            input_tokens=45,
            output_tokens=120
        )
        print(f"✅ Agent 2 response: {agent_a.id}")
        print(f"   Tokens: {agent_a.total_tokens}")

        # ====================================================================
        # TEST 6: Get User Conversations
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 6: Get User Conversations")
        print("=" * 80)

        print(f"\n📋 Getting all conversations for user {user_id}...")
        user_convs, total = await ConversationService.get_user_conversations(
            db=db,
            user_id=user_id,
            status="active",
            limit=50,
            offset=0
        )

        assert total == 1  # Only 1 user-agent conversation
        assert user_convs[0].id == user_agent_conv.id
        print(f"✅ Found {total} conversation(s) for user")
        for conv in user_convs:
            print(f"   - {conv.title} ({conv.total_messages} messages)")

        # ====================================================================
        # TEST 7: Get Agent Conversations
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 7: Get Agent Conversations")
        print("=" * 80)

        print(f"\n📋 Getting all conversations for agent 1...")
        agent1_convs, total = await ConversationService.get_agent_conversations(
            db=db,
            agent_id=agent1_id,
            limit=50,
            offset=0
        )

        assert total == 2  # 1 user-agent + 1 agent-agent
        print(f"✅ Found {total} conversation(s) for agent 1")
        for conv in agent1_convs:
            print(f"   - [{conv.conversation_type}] {conv.title}")

        # ====================================================================
        # TEST 8: Add Participant (Multi-Party)
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 8: Add Participant (Multi-Party)")
        print("=" * 80)

        print(f"\n👥 Adding agent 3 to user-agent conversation...")
        participant = await ConversationService.add_participant(
            db=db,
            conversation_id=user_agent_conv.id,
            participant_id=agent3_id,
            participant_type="agent",
            role="observer"
        )

        # Refresh conversation
        await db.refresh(user_agent_conv)
        assert user_agent_conv.conversation_type == "multi_party"
        print(f"✅ Added participant: {participant.participant_type} {participant.participant_id}")
        print(f"   Conversation type changed to: {user_agent_conv.conversation_type}")

        # ====================================================================
        # TEST 9: Archive Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 9: Archive Conversation")
        print("=" * 80)

        print(f"\n📦 Archiving agent-agent conversation...")
        archived = await ConversationService.archive_conversation(
            db=db,
            conversation_id=agent_agent_conv.id
        )

        assert archived.status == "archived"
        assert archived.archived_at is not None
        print(f"✅ Conversation archived")
        print(f"   Status: {archived.status}")
        print(f"   Archived at: {archived.archived_at}")

        # ====================================================================
        # TEST 10: Close Conversation
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 10: Close Conversation")
        print("=" * 80)

        print(f"\n🔒 Closing user-agent conversation...")
        closed = await ConversationService.close_conversation(
            db=db,
            conversation_id=user_agent_conv.id
        )

        assert closed.status == "closed"
        # Check participants were deactivated by querying them
        from sqlalchemy import select
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == user_agent_conv.id
            )
        )
        participants = list(result.scalars().all())
        for p in participants:
            assert p.is_active is False
            assert p.left_at is not None
        print(f"✅ Conversation closed")
        print(f"   Status: {closed.status}")
        print(f"   All {len(participants)} participants deactivated")

        # ====================================================================
        # TEST 11: Update Conversation Metadata
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 11: Update Conversation Metadata")
        print("=" * 80)

        print(f"\n✏️ Updating conversation title...")
        updated = await ConversationService.update_conversation_title(
            db=db,
            conversation_id=user_agent_conv.id,
            title="React Components - RESOLVED"
        )
        assert updated.title == "React Components - RESOLVED"
        print(f"✅ Title updated: {updated.title}")

        print(f"\n📝 Adding conversation summary...")
        updated = await ConversationService.update_conversation_summary(
            db=db,
            conversation_id=user_agent_conv.id,
            summary="User learned how to create reusable React components with TypeScript"
        )
        assert updated.summary is not None
        print(f"✅ Summary added: {updated.summary}")

        # ====================================================================
        # TEST 12: Token Tracking
        # ====================================================================
        print("\n" + "=" * 80)
        print("TEST 12: Token Tracking")
        print("=" * 80)

        print(f"\n📊 Checking token usage...")
        await db.refresh(user_agent_conv)
        print(f"✅ User-agent conversation tokens: {user_agent_conv.total_tokens_used}")

        await db.refresh(agent_agent_conv)
        print(f"✅ Agent-agent conversation tokens: {agent_agent_conv.total_tokens_used}")

        # Total should be sum of all message tokens
        expected_user_agent_tokens = 200  # From agent_msg1 (50 input + 150 output)
        assert user_agent_conv.total_tokens_used == expected_user_agent_tokens

        expected_agent_agent_tokens = 195  # (30+0=30) + (45+120=165) = 195
        assert agent_agent_conv.total_tokens_used == expected_agent_agent_tokens

        # ====================================================================
        # CLEANUP
        # ====================================================================
        print("\n🧹 Cleaning up test data...")
        await cleanup_test_data(db, user_id, squad_id)
        print("✅ Cleanup complete")

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 80)
        print("✅ ALL MULTI-TURN CONVERSATION TESTS PASSED!")
        print("=" * 80)
        print("\nFeatures Verified:")
        print("  ✅ User-Agent conversation creation")
        print("  ✅ Agent-Agent conversation creation")
        print("  ✅ Message sending (user and agent)")
        print("  ✅ Conversation history retrieval")
        print("  ✅ Token tracking and accumulation")
        print("  ✅ User conversation listing")
        print("  ✅ Agent conversation listing")
        print("  ✅ Participant management (add)")
        print("  ✅ Multi-party conversation support")
        print("  ✅ Conversation archiving")
        print("  ✅ Conversation closing")
        print("  ✅ Metadata updates (title, summary)")
        print("\n🎉 Multi-turn conversation system is fully operational!")


if __name__ == "__main__":
    asyncio.run(test_multi_turn_conversations())
