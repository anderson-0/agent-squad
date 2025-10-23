#!/usr/bin/env python3
"""
Test Script for Agent Message Streaming

Simulates real agent communication to test the CLI streaming functionality.

This script will:
1. Create a test task execution
2. Create 2 test agents (Backend Developer and Tech Lead)
3. Send realistic messages between them
4. Messages will be broadcast via SSE and visible in the CLI

Usage:
    # Terminal 1: Run this script
    python test_agent_streaming.py

    # Terminal 2: Run the CLI
    python -m backend.cli.stream_agent_messages --execution-id <execution-id>
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.session import get_async_session
from backend.models.squad import Squad, SquadMember
from backend.models.task_execution import TaskExecution
from backend.agents.communication.message_bus import get_message_bus
from backend.agents.communication.protocol import A2AProtocol
from sqlalchemy.ext.asyncio import AsyncSession


async def create_test_data(db: AsyncSession):
    """Create test squad, agents, and task execution"""
    print("🔧 Creating test data...")

    # Create test squad
    squad = Squad(
        id=uuid4(),
        name="Test Squad",
        description="Test squad for streaming demo",
        created_by_id=uuid4(),  # Mock user
        is_active=True
    )
    db.add(squad)
    await db.flush()

    # Create Backend Developer agent
    backend_dev = SquadMember(
        id=uuid4(),
        squad_id=squad.id,
        role="backend_developer",
        specialization="python_fastapi",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="I am a backend developer",
        is_active=True
    )

    # Create Tech Lead agent
    tech_lead = SquadMember(
        id=uuid4(),
        squad_id=squad.id,
        role="tech_lead",
        specialization=None,
        llm_provider="anthropic",
        llm_model="claude-3-sonnet",
        system_prompt="I am a tech lead",
        is_active=True
    )

    db.add_all([backend_dev, tech_lead])
    await db.flush()

    # Create task execution
    task_execution = TaskExecution(
        id=uuid4(),
        squad_id=squad.id,
        task_id=uuid4(),  # Mock task
        status="in_progress",
        created_at=datetime.utcnow()
    )
    db.add(task_execution)
    await db.commit()

    print(f"✅ Created squad: {squad.id}")
    print(f"✅ Created Backend Developer: {backend_dev.id}")
    print(f"✅ Created Tech Lead: {tech_lead.id}")
    print(f"✅ Created task execution: {task_execution.id}")
    print()

    return squad, backend_dev, tech_lead, task_execution


async def simulate_conversation(
    db: AsyncSession,
    backend_dev: SquadMember,
    tech_lead: SquadMember,
    task_execution: TaskExecution
):
    """Simulate a realistic conversation between agents"""
    message_bus = get_message_bus()

    print("💬 Starting agent conversation simulation...")
    print("=" * 70)
    print()

    # Conversation flow
    conversations = [
        {
            "sender": backend_dev,
            "recipient": tech_lead,
            "message_type": "question",
            "content": "How should I implement caching for the user API? We're seeing response times of 2-3 seconds.",
            "delay": 1
        },
        {
            "sender": tech_lead,
            "recipient": backend_dev,
            "message_type": "answer",
            "content": "Use Redis for caching. Here's why:\n- Fast in-memory storage\n- TTL support for automatic expiration\n- Industry standard for API caching\n\nCache user data with 5-minute TTL. Invalidate on updates.",
            "delay": 2
        },
        {
            "sender": backend_dev,
            "recipient": tech_lead,
            "message_type": "status_update",
            "content": "Progress: 25% | Status: In Progress\nImplemented Redis caching layer with 5-minute TTL.\nNext: Testing cache invalidation logic.",
            "delay": 3
        },
        {
            "sender": tech_lead,
            "recipient": backend_dev,
            "message_type": "question",
            "content": "Did you add cache invalidation on user updates? That's critical for data consistency.",
            "delay": 1.5
        },
        {
            "sender": backend_dev,
            "recipient": tech_lead,
            "message_type": "answer",
            "content": "Yes! Added cache invalidation in the update_user() endpoint. Also added tests to verify cache is cleared on updates.",
            "delay": 2
        },
        {
            "sender": backend_dev,
            "recipient": tech_lead,
            "message_type": "code_review_request",
            "content": "Code review needed!\n\nPR: https://github.com/org/repo/pull/123\nChanges: Added Redis caching for user API\n\nImplemented:\n✓ Redis cache layer\n✓ 5-minute TTL\n✓ Cache invalidation on updates\n✓ Unit tests (95% coverage)\n✓ Integration tests\n\nResponse times improved from 2.5s → 150ms!",
            "delay": 2
        },
        {
            "sender": tech_lead,
            "recipient": backend_dev,
            "message_type": "code_review_response",
            "content": "Code Review: APPROVED ✅\n\nGreat work! A few observations:\n\n✅ Excellent cache implementation\n✅ Good test coverage\n✅ Proper error handling\n\n💡 Minor suggestion: Consider adding cache warming for frequently accessed users.\n\nReady to merge!",
            "delay": 2.5
        },
        {
            "sender": backend_dev,
            "recipient": None,  # Broadcast
            "message_type": "task_completion",
            "content": "🎉 Task completed!\n\nImplemented Redis caching for user API:\n- Response times: 2.5s → 150ms (94% improvement)\n- Cache hit rate: ~85%\n- Zero data consistency issues\n- Full test coverage\n\nPR merged to main. Ready for deployment!",
            "delay": 1.5
        }
    ]

    for i, conv in enumerate(conversations, 1):
        sender = conv["sender"]
        recipient = conv["recipient"]

        # Display what we're sending
        sender_name = f"Backend Dev (FastAPI)" if sender.role == "backend_developer" else "Tech Lead"
        recipient_name = "Tech Lead" if recipient and recipient.role == "tech_lead" else "Backend Dev (FastAPI)" if recipient else "All Agents"

        print(f"📨 Message {i}/{len(conversations)}")
        print(f"   From: {sender_name}")
        print(f"   To: {recipient_name}")
        print(f"   Type: {conv['message_type']}")
        print(f"   Preview: {conv['content'][:60]}...")

        # Send the message
        if recipient is None:
            # Broadcast message
            await message_bus.broadcast_message(
                sender_id=sender.id,
                content=conv["content"],
                message_type=conv["message_type"],
                task_execution_id=task_execution.id,
                db=db
            )
        else:
            # Point-to-point message
            await message_bus.send_message(
                sender_id=sender.id,
                recipient_id=recipient.id,
                content=conv["content"],
                message_type=conv["message_type"],
                task_execution_id=task_execution.id,
                metadata={"thread_id": f"thread-{task_execution.id}"},
                db=db
            )

        print(f"   ✅ Sent!\n")

        # Wait before next message (simulate realistic timing)
        await asyncio.sleep(conv["delay"])

    print("=" * 70)
    print("✅ Conversation simulation complete!")
    print()


async def main():
    """Main test function"""
    print("\n" + "=" * 70)
    print("  AGENT MESSAGE STREAMING - TEST SCRIPT")
    print("=" * 70)
    print()

    # Get database session
    async for db in get_async_session():
        try:
            # Create test data
            squad, backend_dev, tech_lead, task_execution = await create_test_data(db)

            # Show CLI command
            print("🎯 TO VIEW THE STREAM IN REAL-TIME:")
            print("   Open another terminal and run:")
            print()
            print(f"   python -m backend.cli.stream_agent_messages \\")
            print(f"     --execution-id {task_execution.id} \\")
            print(f"     --base-url http://localhost:8000")
            print()
            print("   (You'll need a JWT token - set AGENT_SQUAD_TOKEN env var)")
            print()
            input("   Press ENTER when CLI is ready to start the conversation...")
            print()

            # Simulate conversation
            await simulate_conversation(db, backend_dev, tech_lead, task_execution)

            print("🎉 Done! You should have seen all messages in the CLI.")
            print()
            print("📊 Summary:")
            print(f"   - Squad ID: {squad.id}")
            print(f"   - Execution ID: {task_execution.id}")
            print(f"   - Messages sent: 8")
            print(f"   - Agent roles: backend_developer, tech_lead")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(main())
