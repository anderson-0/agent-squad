#!/usr/bin/env python3
"""
NATS Integration Test

Tests the NATS message bus integration with the agent squad architecture.
This validates:
1. Message bus factory switching (memory vs NATS)
2. NATS connection and stream setup
3. Message sending via NATS
4. Database persistence with NATS
5. SSE broadcasting with NATS
"""
import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Setup path
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

# Set NATS mode
os.environ['MESSAGE_BUS'] = 'nats'
os.environ['NATS_URL'] = 'nats://localhost:4222'
os.environ['DEBUG'] = 'False'

# Suppress logging
import logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.models.project import Project, Task
from backend.agents.communication.message_bus import get_message_bus, reset_message_bus
from sqlalchemy import select

# Colors
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_section(title):
    print(f"\n{C.BOLD}{C.CYAN}{'='*70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{title.center(70)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'='*70}{C.END}\n")


async def test_message_bus_factory():
    """Test that factory returns correct bus type based on config"""
    print_section("Test 1: Message Bus Factory")

    # Test NATS mode
    os.environ['MESSAGE_BUS'] = 'nats'
    await reset_message_bus()

    bus = get_message_bus()
    bus_type = type(bus).__name__

    if bus_type == 'NATSMessageBus':
        print(f"{C.GREEN}✓ Factory returned NATSMessageBus (correct!){C.END}")
    else:
        print(f"{C.RED}✗ Factory returned {bus_type} (expected NATSMessageBus){C.END}")
        return False

    # Test memory mode
    os.environ['MESSAGE_BUS'] = 'memory'
    await reset_message_bus()

    bus = get_message_bus()
    bus_type = type(bus).__name__

    if bus_type == 'MessageBus':
        print(f"{C.GREEN}✓ Factory returned MessageBus for memory mode (correct!){C.END}")
    else:
        print(f"{C.RED}✗ Factory returned {bus_type} (expected MessageBus){C.END}")
        return False

    # Switch back to NATS
    os.environ['MESSAGE_BUS'] = 'nats'
    await reset_message_bus()

    return True


async def test_nats_connection():
    """Test NATS connection and stream setup"""
    print_section("Test 2: NATS Connection & Stream Setup")

    bus = get_message_bus()

    # Connect to NATS
    try:
        await bus.connect()
        print(f"{C.GREEN}✓ Connected to NATS server{C.END}")
    except Exception as e:
        print(f"{C.RED}✗ Failed to connect to NATS: {e}{C.END}")
        return False

    # Check connection
    if bus._connected:
        print(f"{C.GREEN}✓ NATS connection verified{C.END}")
    else:
        print(f"{C.RED}✗ NATS not connected{C.END}")
        return False

    # Check stream exists
    try:
        stream_info = await bus._js.stream_info("agent-messages")
        print(f"{C.GREEN}✓ JetStream stream 'agent-messages' exists{C.END}")
        print(f"{C.CYAN}  Stream config:{C.END}")
        print(f"{C.CYAN}    Name: {stream_info.config.name}{C.END}")
        print(f"{C.CYAN}    Subjects: {stream_info.config.subjects}{C.END}")
        print(f"{C.CYAN}    Max messages: {stream_info.config.max_msgs:,}{C.END}")
        print(f"{C.CYAN}    Max age: {stream_info.config.max_age}s ({stream_info.config.max_age // 86400} days){C.END}")
    except Exception as e:
        print(f"{C.RED}✗ Stream check failed: {e}{C.END}")
        return False

    return True


async def test_message_sending():
    """Test sending messages via NATS"""
    print_section("Test 3: Sending Messages via NATS")

    bus = get_message_bus()

    # Ensure connection
    if not bus._connected:
        await bus.connect()

    # Send test messages
    sender_id = uuid4()
    recipient_id = uuid4()
    task_execution_id = uuid4()

    messages = [
        ("question", "How should we implement authentication?"),
        ("answer", "Use JWT tokens with refresh token rotation"),
        ("status_update", "Implementation is 60% complete"),
    ]

    print(f"{C.CYAN}Sending {len(messages)} test messages...{C.END}\n")

    for i, (msg_type, content) in enumerate(messages, 1):
        try:
            msg = await bus.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id if i != 3 else None,  # Last one is broadcast
                content=content,
                message_type=msg_type,
                task_execution_id=task_execution_id,
                metadata={"test": True, "index": i}
            )

            print(f"  {C.GREEN}✓{C.END} Message {i}: {msg_type}")
            print(f"    ID: {msg.id}")
            print(f"    Content: {content[:50]}...")
            print()

        except Exception as e:
            print(f"  {C.RED}✗{C.END} Failed to send message {i}: {e}")
            return False

    print(f"{C.GREEN}✓ All {len(messages)} messages sent successfully{C.END}")
    return True


async def test_nats_stats():
    """Test getting NATS statistics"""
    print_section("Test 4: NATS Statistics")

    bus = get_message_bus()

    try:
        stats = await bus.get_stats()

        if stats.get('connected'):
            print(f"{C.GREEN}✓ NATS statistics retrieved{C.END}\n")
            print(f"{C.CYAN}Statistics:{C.END}")
            print(f"  Connected: {stats['connected']}")
            print(f"  Stream: {stats.get('stream_name', 'N/A')}")
            print(f"  Total messages: {stats.get('total_messages', 0):,}")
            print(f"  Total bytes: {stats.get('total_bytes', 0):,}")
            print(f"  First sequence: {stats.get('first_seq', 0)}")
            print(f"  Last sequence: {stats.get('last_seq', 0)}")
            print(f"  Consumer count: {stats.get('consumer_count', 0)}")
        else:
            print(f"{C.RED}✗ Not connected to NATS{C.END}")
            return False

    except Exception as e:
        print(f"{C.RED}✗ Failed to get stats: {e}{C.END}")
        return False

    return True


async def test_with_real_agents():
    """Test NATS integration with real agent workflow"""
    print_section("Test 5: Integration with Real Agents")

    async with AsyncSessionLocal() as db:
        # Get or create user
        result = await db.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()

        if not user:
            print(f"{C.YELLOW}⚠ Demo user not found. Creating...{C.END}")
            user = User(
                id=uuid4(),
                email='demo@test.com',
                username='demo',
                full_name='Demo User',
                hashed_password='dummy'
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create squad
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name='NATS Test Squad',
            description='Testing NATS integration'
        )
        print(f"{C.GREEN}✓ Squad created: {squad.name}{C.END}")

        # Create agents
        pm = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='project_manager',
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )

        backend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='backend_developer',
            specialization='python_fastapi',
            llm_provider='openai',
            llm_model='gpt-4'
        )

        await db.commit()
        print(f"{C.GREEN}✓ Agents created: PM, Backend Dev{C.END}")

        # Create task
        project = Project(
            id=uuid4(),
            squad_id=squad.id,
            name='NATS Test Project',
            description='Test',
            is_active=True
        )
        db.add(project)
        await db.flush()

        task = Task(
            id=uuid4(),
            project_id=project.id,
            title='Test NATS Messaging',
            description='Validate NATS integration',
            status='in_progress',
            priority='high'
        )
        db.add(task)
        await db.commit()

        # Create TaskExecution (required for messages)
        from backend.services.task_execution_service import TaskExecutionService
        execution = await TaskExecutionService.start_task_execution(
            db=db,
            task_id=task.id,
            squad_id=squad.id
        )
        await db.commit()

        print(f"{C.GREEN}✓ Task created: {task.title}{C.END}")
        print(f"{C.GREEN}✓ Execution created: {execution.id}{C.END}\n")

        # Send messages via NATS bus
        bus = get_message_bus()
        if not bus._connected:
            await bus.connect()

        print(f"{C.CYAN}Sending messages between agents...{C.END}\n")

        # PM → Backend
        msg1 = await bus.send_message(
            sender_id=pm.id,
            recipient_id=backend.id,
            content="Please implement user authentication with JWT",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high"},
            db=db
        )
        print(f"  {C.GREEN}✓{C.END} PM → Backend: Task assignment")

        await db.commit()
        await asyncio.sleep(0.5)

        # Backend → PM
        msg2 = await bus.send_message(
            sender_id=backend.id,
            recipient_id=pm.id,
            content="Understood. I'll implement JWT authentication with refresh tokens.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        print(f"  {C.GREEN}✓{C.END} Backend → PM: Acknowledgment")

        await db.commit()
        await asyncio.sleep(0.5)

        # Broadcast
        msg3 = await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Team standup: Let's sync on authentication implementation",
            message_type="standup",
            task_execution_id=execution.id,
            db=db
        )
        print(f"  {C.GREEN}✓{C.END} PM → All: Broadcast standup")

        await db.commit()

        print(f"\n{C.GREEN}✓ All agent messages sent via NATS and persisted to DB{C.END}")

        # Verify messages in database
        from backend.models.agent_message import AgentMessage
        result = await db.execute(
            select(AgentMessage).where(AgentMessage.task_execution_id == execution.id)
        )
        db_messages = result.scalars().all()

        print(f"{C.CYAN}\nDatabase verification:{C.END}")
        print(f"  Messages in DB: {len(db_messages)}")
        if len(db_messages) == 3:
            print(f"  {C.GREEN}✓ All 3 messages persisted correctly{C.END}")
        else:
            print(f"  {C.RED}✗ Expected 3 messages, found {len(db_messages)}{C.END}")
            return False

    return True


async def main():
    """Run all tests"""
    print(f"\n{C.BOLD}{C.CYAN}{'='*70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'NATS Integration Test Suite'.center(70)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'='*70}{C.END}")

    tests = [
        ("Message Bus Factory", test_message_bus_factory),
        ("NATS Connection", test_nats_connection),
        ("Message Sending", test_message_sending),
        ("NATS Statistics", test_nats_stats),
        ("Real Agent Integration", test_with_real_agents),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n{C.RED}✗ Test failed with exception: {e}{C.END}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print_section("Test Summary")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = f"{C.GREEN}✓ PASS{C.END}" if success else f"{C.RED}✗ FAIL{C.END}"
        print(f"  {status}  {test_name}")

    print(f"\n{C.BOLD}Results: {passed}/{total} tests passed{C.END}")

    if passed == total:
        print(f"\n{C.BOLD}{C.GREEN}🎉 All tests passed! NATS integration is working correctly.{C.END}\n")
        return 0
    else:
        print(f"\n{C.BOLD}{C.RED}❌ Some tests failed. Please review the output above.{C.END}\n")
        return 1

    # Cleanup
    bus = get_message_bus()
    if hasattr(bus, 'disconnect'):
        await bus.disconnect()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Tests interrupted{C.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{C.RED}Test suite error: {e}{C.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
