"""
End-to-End Test for Squad Analytics System

Tests all analytics features:
1. Token usage tracking
2. Message counting
3. Communication matrix
4. Conversation filtering
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db_context
from backend.models import Squad, SquadMember, AgentMessage, SquadMemberStats, User
from backend.services.squad_analytics_service import SquadAnalyticsService
from backend.core.logging import logger


async def cleanup_test_data(db: AsyncSession, squad_id, user_id):
    """Clean up test data"""
    try:
        # Get squad member IDs
        result = await db.execute(
            select(SquadMember.id).where(SquadMember.squad_id == squad_id)
        )
        member_ids = [row[0] for row in result.all()]

        if member_ids:
            # Delete in proper order due to foreign key constraints
            from sqlalchemy import delete

            # Delete messages
            await db.execute(
                delete(AgentMessage).where(AgentMessage.sender_id.in_(member_ids))
            )

            # Delete stats
            await db.execute(
                delete(SquadMemberStats).where(SquadMemberStats.squad_member_id.in_(member_ids))
            )

            # Delete members
            await db.execute(
                delete(SquadMember).where(SquadMember.squad_id == squad_id)
            )

        # Delete squad
        from sqlalchemy import delete
        await db.execute(delete(Squad).where(Squad.id == squad_id))

        # Delete test user
        await db.execute(delete(User).where(User.id == user_id))

        await db.commit()
    except Exception as e:
        logger.warning(f"Cleanup error (non-critical): {e}")
        await db.rollback()


async def test_analytics_system():
    """Test the complete analytics system"""

    print("=" * 80)
    print("SQUAD ANALYTICS E2E TEST")
    print("=" * 80)

    async with get_db_context() as db:
        # Setup: Create test user and squad with members
        print("\n📦 Setting up test data...")

        # Create test user
        user_id = uuid4()
        test_user = User(
            id=user_id,
            email=f"test_analytics_{user_id}@example.com",
            name="Test Analytics User",
            password_hash="fake_hash_for_testing",
            is_active=True
        )
        db.add(test_user)

        squad_id = uuid4()
        squad = Squad(
            id=squad_id,
            name="Test Analytics Squad",
            description="Testing analytics features",
            user_id=user_id,
            status="active"
        )
        db.add(squad)

        # Create 3 squad members
        member1_id = uuid4()
        member2_id = uuid4()
        member3_id = uuid4()

        member1 = SquadMember(
            id=member1_id,
            squad_id=squad_id,
            role="backend_developer",
            specialization="python",
            system_prompt="You are a backend developer.",
            is_active=True
        )
        member2 = SquadMember(
            id=member2_id,
            squad_id=squad_id,
            role="frontend_developer",
            specialization="react",
            system_prompt="You are a frontend developer.",
            is_active=True
        )
        member3 = SquadMember(
            id=member3_id,
            squad_id=squad_id,
            role="tech_lead",
            specialization="architecture",
            system_prompt="You are a tech lead.",
            is_active=True
        )

        db.add_all([member1, member2, member3])
        await db.commit()

        print(f"✅ Created squad: {squad_id}")
        print(f"✅ Created 3 squad members")

        # Test 1: Token Usage Tracking
        print("\n" + "=" * 80)
        print("TEST 1: Token Usage Tracking")
        print("=" * 80)

        print("\n📊 Updating token usage for member 1...")
        stats1 = await SquadAnalyticsService.update_token_usage(
            db=db,
            squad_member_id=member1_id,
            input_tokens=1000,
            output_tokens=500
        )

        assert stats1.total_input_tokens == 1000, "Input tokens mismatch"
        assert stats1.total_output_tokens == 500, "Output tokens mismatch"
        assert stats1.total_tokens == 1500, "Total tokens mismatch"
        assert stats1.last_llm_call_at is not None, "Last LLM call timestamp not set"
        print(f"✅ Member 1 tokens: {stats1.total_tokens} (1000 in, 500 out)")

        # Update again to test accumulation
        stats1 = await SquadAnalyticsService.update_token_usage(
            db=db,
            squad_member_id=member1_id,
            input_tokens=2000,
            output_tokens=1000
        )

        assert stats1.total_input_tokens == 3000, "Accumulated input tokens mismatch"
        assert stats1.total_output_tokens == 1500, "Accumulated output tokens mismatch"
        assert stats1.total_tokens == 4500, "Accumulated total tokens mismatch"
        print(f"✅ After second update: {stats1.total_tokens} total (accumulated)")

        # Test 2: Message Counting
        print("\n" + "=" * 80)
        print("TEST 2: Message Counting")
        print("=" * 80)

        print("\n📨 Recording messages sent/received...")

        # Member 1 sends 3 messages
        for _ in range(3):
            await SquadAnalyticsService.update_message_sent(db, member1_id)

        # Member 1 receives 2 messages
        for _ in range(2):
            await SquadAnalyticsService.update_message_received(db, member1_id)

        # Member 2 sends 5 messages
        for _ in range(5):
            await SquadAnalyticsService.update_message_sent(db, member2_id)

        # Verify counts
        stats1 = await SquadAnalyticsService.get_or_create_stats(db, member1_id)
        stats2 = await SquadAnalyticsService.get_or_create_stats(db, member2_id)

        assert stats1.total_messages_sent == 3, "Member 1 sent count mismatch"
        assert stats1.total_messages_received == 2, "Member 1 received count mismatch"
        assert stats2.total_messages_sent == 5, "Member 2 sent count mismatch"

        print(f"✅ Member 1: {stats1.total_messages_sent} sent, {stats1.total_messages_received} received")
        print(f"✅ Member 2: {stats2.total_messages_sent} sent")

        # Test 3: Get Member Stats
        print("\n" + "=" * 80)
        print("TEST 3: Get Member Statistics")
        print("=" * 80)

        print(f"\n📈 Fetching stats for member 1...")
        member_stats = await SquadAnalyticsService.get_member_stats(db, member1_id)

        assert member_stats["squad_member_id"] == str(member1_id)
        assert member_stats["role"] == "backend_developer"
        assert member_stats["token_usage"]["total_tokens"] == 4500
        assert member_stats["message_counts"]["total_sent"] == 3
        assert member_stats["message_counts"]["total_received"] == 2

        print(f"✅ Role: {member_stats['role']}")
        print(f"✅ Total tokens: {member_stats['token_usage']['total_tokens']}")
        print(f"✅ Messages: {member_stats['message_counts']['total_sent']} sent, {member_stats['message_counts']['total_received']} received")

        # Test 4: Get Squad Stats
        print("\n" + "=" * 80)
        print("TEST 4: Get Squad Statistics")
        print("=" * 80)

        print(f"\n📊 Fetching aggregated squad stats...")

        # Add some tokens to member 2
        await SquadAnalyticsService.update_token_usage(db, member2_id, 500, 250)

        squad_stats = await SquadAnalyticsService.get_squad_stats(db, squad_id)

        assert squad_stats["squad_id"] == str(squad_id)
        assert squad_stats["total_members"] == 3
        assert squad_stats["aggregate_stats"]["total_tokens"] == 5250  # 4500 + 750
        assert squad_stats["aggregate_stats"]["total_messages"] == 8  # 3 + 5

        print(f"✅ Squad: {squad_stats['squad_name']}")
        print(f"✅ Total members: {squad_stats['total_members']}")
        print(f"✅ Total tokens: {squad_stats['aggregate_stats']['total_tokens']}")
        print(f"✅ Total messages: {squad_stats['aggregate_stats']['total_messages']}")

        # Test 5: Communication Matrix
        print("\n" + "=" * 80)
        print("TEST 5: Communication Matrix")
        print("=" * 80)

        print("\n💬 Creating test messages between members...")

        # Member 1 -> Member 2 (3 messages)
        for i in range(3):
            msg = AgentMessage(
                id=uuid4(),
                sender_id=member1_id,
                recipient_id=member2_id,
                content=f"Message {i+1} from member 1 to member 2",
                message_type="question"
            )
            db.add(msg)

        # Member 2 -> Member 1 (2 messages)
        for i in range(2):
            msg = AgentMessage(
                id=uuid4(),
                sender_id=member2_id,
                recipient_id=member1_id,
                content=f"Message {i+1} from member 2 to member 1",
                message_type="response"
            )
            db.add(msg)

        # Member 3 -> Member 1 (1 message)
        msg = AgentMessage(
            id=uuid4(),
            sender_id=member3_id,
            recipient_id=member1_id,
            content="Message from member 3 to member 1",
            message_type="question"
        )
        db.add(msg)

        # Member 1 -> Broadcast (1 message)
        msg = AgentMessage(
            id=uuid4(),
            sender_id=member1_id,
            recipient_id=None,
            content="Broadcast message from member 1",
            message_type="announcement"
        )
        db.add(msg)

        await db.commit()

        print("✅ Created 7 test messages")

        print("\n📊 Fetching communication matrix...")
        matrix = await SquadAnalyticsService.get_communication_matrix(db, squad_id)

        assert str(member1_id) in matrix["communication_matrix"]
        assert str(member2_id) in matrix["communication_matrix"][str(member1_id)]
        assert matrix["communication_matrix"][str(member1_id)][str(member2_id)] == 3
        assert matrix["communication_matrix"][str(member2_id)][str(member1_id)] == 2
        assert matrix["communication_matrix"][str(member3_id)][str(member1_id)] == 1
        assert matrix["communication_matrix"][str(member1_id)]["broadcast"] == 1

        print(f"✅ Matrix contains {len(matrix['members'])} members")
        print(f"✅ Member 1 -> Member 2: {matrix['communication_matrix'][str(member1_id)][str(member2_id)]} messages")
        print(f"✅ Member 2 -> Member 1: {matrix['communication_matrix'][str(member2_id)][str(member1_id)]} messages")
        print(f"✅ Member 3 -> Member 1: {matrix['communication_matrix'][str(member3_id)][str(member1_id)]} messages")
        print(f"✅ Member 1 broadcasts: {matrix['communication_matrix'][str(member1_id)]['broadcast']} messages")

        # Test 6: Conversations Between Members
        print("\n" + "=" * 80)
        print("TEST 6: Conversations Between Members")
        print("=" * 80)

        print(f"\n💬 Fetching conversation between member 1 and member 2...")
        conversations = await SquadAnalyticsService.get_conversations_between_members(
            db=db,
            member_a_id=member1_id,
            member_b_id=member2_id,
            limit=100,
            offset=0
        )

        assert conversations["total_messages"] == 5  # 3 from m1->m2 + 2 from m2->m1
        assert conversations["returned_messages"] == 5
        assert len(conversations["messages"]) == 5

        print(f"✅ Total messages between members: {conversations['total_messages']}")
        print(f"✅ Messages returned: {conversations['returned_messages']}")

        # Verify messages are bidirectional
        sender_ids = {msg["sender_id"] for msg in conversations["messages"]}
        assert str(member1_id) in sender_ids
        assert str(member2_id) in sender_ids
        print(f"✅ Bidirectional conversation verified")

        # Test 7: Time-filtered Communication Matrix
        print("\n" + "=" * 80)
        print("TEST 7: Time-Filtered Communication Matrix")
        print("=" * 80)

        print("\n⏰ Testing communication matrix with time filter...")

        # Get matrix for last 1 day (should include all messages)
        since = datetime.utcnow() - timedelta(days=1)
        matrix_recent = await SquadAnalyticsService.get_communication_matrix(
            db, squad_id, since=since
        )

        total_messages = sum(
            sum(recipients.values())
            for recipients in matrix_recent["communication_matrix"].values()
        )

        assert total_messages == 7  # All 7 messages we created
        print(f"✅ Messages in last day: {total_messages}")

        # Get matrix for last 0 days (future filter - should have 0 messages)
        future = datetime.utcnow() + timedelta(days=1)
        matrix_future = await SquadAnalyticsService.get_communication_matrix(
            db, squad_id, since=future
        )

        total_future = sum(
            sum(recipients.values())
            for recipients in matrix_future["communication_matrix"].values()
        ) if matrix_future["communication_matrix"] else 0

        assert total_future == 0
        print(f"✅ Messages in future filter: {total_future}")

        # Cleanup
        print("\n🧹 Cleaning up test data...")
        await cleanup_test_data(db, squad_id, user_id)
        print("✅ Cleanup complete")

        # Final Summary
        print("\n" + "=" * 80)
        print("✅ ALL ANALYTICS TESTS PASSED!")
        print("=" * 80)
        print("\nFeatures Verified:")
        print("  ✅ Token usage tracking and accumulation")
        print("  ✅ Message sent/received counting")
        print("  ✅ Individual member statistics")
        print("  ✅ Squad-level aggregated statistics")
        print("  ✅ Communication matrix (who talks to whom)")
        print("  ✅ Bidirectional conversation filtering")
        print("  ✅ Time-based filtering")
        print("\n🎉 Analytics system is fully operational!")


if __name__ == "__main__":
    asyncio.run(test_analytics_system())
