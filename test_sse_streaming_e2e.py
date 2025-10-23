#!/usr/bin/env python3
"""
End-to-End Test for SSE Streaming Integration

Tests that:
1. AgentMessageHandler broadcasts streaming tokens via SSE
2. SSE manager receives and queues messages
3. Events are properly formatted (answer_streaming, answer_complete)
4. Integration works with real agent processing

Run:
    DEBUG=False PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python test_sse_streaming_e2e.py
"""
import asyncio
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.models import User, Squad, SquadMember, Conversation
from backend.services.squad_service import SquadService
from backend.services.sse_service import sse_manager
from backend.agents.interaction.agent_message_handler import AgentMessageHandler
from backend.agents.factory import AgentFactory


def print_header(title: str, emoji: str = "🔍"):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {emoji} {title}")
    print("=" * 80 + "\n")


async def test_sse_streaming():
    """
    Test SSE streaming end-to-end.

    This test verifies:
    1. AgentMessageHandler streams tokens
    2. SSE manager receives broadcasts
    3. Events are properly formatted
    4. Real-time updates work
    """
    print("\n" + "🌊" * 40)
    print("  SSE STREAMING END-TO-END TEST".center(80))
    print("  Verifying Real-Time Agent Streaming".center(80))
    print("🌊" * 40)

    async with AsyncSessionLocal() as db:
        # ================================================================
        # Setup: Create test data
        # ================================================================
        print_header("Setup - Create Test Data")

        # Get or create user
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("❌ No users found")
            return

        print(f"✓ User: {user.email}")

        # Create squad and agents
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name="SSE Test Squad",
            description="Testing SSE streaming"
        )

        # Create a user agent (represents user asking questions)
        user_agent = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="user_proxy",
            specialization="default",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="User proxy agent",
            is_active=True
        )
        db.add(user_agent)

        tech_lead = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="tech_lead",
            specialization="default",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="You are a helpful tech lead. Keep responses brief (2-3 sentences).",
            is_active=True
        )
        db.add(tech_lead)
        await db.commit()
        await db.refresh(user_agent)
        await db.refresh(tech_lead)

        print(f"✓ Created User proxy agent")
        print(f"✓ Created Tech Lead agent ({tech_lead.llm_provider}/{tech_lead.llm_model})")

        # Create a minimal TaskExecution for SSE to work
        from backend.models import TaskExecution
        task_execution_id = uuid4()
        task_execution = TaskExecution(
            id=task_execution_id,
            squad_id=squad.id,
            title="SSE Test Task",
            status="in_progress",
            user_input="What is Redis used for?"
        )
        db.add(task_execution)
        await db.commit()
        await db.refresh(task_execution)

        print(f"✓ Created TaskExecution: {task_execution_id}")

        # First create an initial message (required by Conversation)
        from backend.models import AgentMessage
        initial_msg = AgentMessage(
            id=uuid4(),
            task_execution_id=task_execution_id,  # Now we have a valid FK
            sender_id=user_agent.id,  # User agent asking question
            recipient_id=tech_lead.id,
            content="Test question",
            message_type="question"
        )
        db.add(initial_msg)
        await db.commit()
        await db.refresh(initial_msg)

        # Now create conversation referencing the message
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=initial_msg.id,
            task_execution_id=task_execution_id,  # Valid FK now
            asker_id=user_agent.id,  # User agent (not user.id)
            current_responder_id=tech_lead.id,
            question_type="implementation",
            current_state="waiting",
            escalation_level=0
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        print(f"✓ Created conversation (task_execution_id: {task_execution_id})")

        # ================================================================
        # Test 1: Subscribe to SSE and capture events
        # ================================================================
        print_header("Test 1: SSE Event Capture", "📡")

        # Track events received
        events_received = []
        tokens_received = []

        # Create a mock SSE subscription by listening to the queue directly
        queue = asyncio.Queue(maxsize=100)
        sse_manager.execution_connections[task_execution_id].add(queue)
        sse_manager.all_connections.add(queue)
        sse_manager.connection_metadata[queue] = {
            "execution_id": task_execution_id,
            "user_id": user.id,
            "connected_at": datetime.utcnow().isoformat(),
            "type": "execution",
        }

        print(f"✓ Subscribed to SSE for execution {task_execution_id}")
        print(f"✓ Active connections: {sse_manager.get_connection_count(task_execution_id)}")

        # ================================================================
        # Test 2: Process message with streaming
        # ================================================================
        print_header("Test 2: Process Streaming Message", "🤖")

        # Create message handler
        handler = AgentMessageHandler(db)

        # Start background task to collect SSE events
        async def collect_sse_events():
            """Collect events from SSE queue"""
            try:
                while True:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)

                        if message is None:
                            break

                        event_type = message.get("event", "unknown")
                        event_data = message.get("data", {})

                        events_received.append({
                            "event": event_type,
                            "data": event_data,
                            "timestamp": datetime.utcnow().isoformat()
                        })

                        # Track streaming tokens
                        if event_type == "answer_streaming":
                            token = event_data.get("token", "")
                            tokens_received.append(token)
                            print(f"📨 SSE Event: {event_type} (token: '{token[:20]}...')")
                        elif event_type == "answer_complete":
                            print(f"✅ SSE Event: {event_type} (length: {event_data.get('total_length', 0)})")
                        else:
                            print(f"📨 SSE Event: {event_type}")

                    except asyncio.TimeoutError:
                        print("⏱️  SSE event collection timeout")
                        break
            except Exception as e:
                print(f"❌ Error collecting SSE events: {e}")

        # Start SSE collector
        collector_task = asyncio.create_task(collect_sse_events())

        # Process message (will trigger streaming)
        question = "What is Redis used for?"

        print(f"Question: '{question}'")
        print("\nAgent streaming (this will take 5-10 seconds)...")
        print("─" * 80)

        try:
            await handler.process_incoming_message(
                message_id=uuid4(),
                recipient_id=tech_lead.id,
                sender_id=user_agent.id,  # User agent sending the question
                content=question,
                message_type="question",
                conversation_id=conversation.id
            )

            print("─" * 80)
            print("✓ Agent processing complete")

        except Exception as e:
            print(f"❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()

        # Wait a bit for final events to be queued
        await asyncio.sleep(1)

        # Stop SSE collector
        await queue.put(None)  # Sentinel to stop collector
        await collector_task

        # ================================================================
        # Test 3: Verify SSE Events
        # ================================================================
        print_header("Test 3: Verify SSE Events", "✅")

        # Check events received
        streaming_events = [e for e in events_received if e["event"] == "answer_streaming"]
        complete_events = [e for e in events_received if e["event"] == "answer_complete"]

        print(f"Total Events Received: {len(events_received)}")
        print(f"  - answer_streaming: {len(streaming_events)}")
        print(f"  - answer_complete: {len(complete_events)}")
        print(f"  - other: {len(events_received) - len(streaming_events) - len(complete_events)}")
        print()

        # Verify streaming events
        if len(streaming_events) > 0:
            print(f"✅ Streaming events received: {len(streaming_events)}")

            # Check first streaming event structure
            first_streaming = streaming_events[0]["data"]
            required_fields = [
                "token", "partial_response", "agent_id", "agent_role",
                "conversation_id", "is_streaming", "timestamp"
            ]

            missing_fields = [f for f in required_fields if f not in first_streaming]
            if missing_fields:
                print(f"⚠️  Missing fields in streaming event: {missing_fields}")
            else:
                print("✅ All required fields present in streaming events")

            # Show sample event
            print("\nSample streaming event:")
            print(f"  - token: '{first_streaming.get('token', '')[:30]}...'")
            print(f"  - agent_role: {first_streaming.get('agent_role')}")
            print(f"  - is_streaming: {first_streaming.get('is_streaming')}")
            print(f"  - conversation_id: {first_streaming.get('conversation_id')}")
        else:
            print("❌ No streaming events received")

        print()

        # Verify complete event
        if len(complete_events) > 0:
            print(f"✅ Complete event received")

            # Check complete event structure
            complete_data = complete_events[0]["data"]
            required_fields = [
                "complete_response", "agent_id", "agent_role",
                "conversation_id", "is_streaming", "total_length", "timestamp"
            ]

            missing_fields = [f for f in required_fields if f not in complete_data]
            if missing_fields:
                print(f"⚠️  Missing fields in complete event: {missing_fields}")
            else:
                print("✅ All required fields present in complete event")

            # Show complete event details
            print("\nComplete event details:")
            print(f"  - total_length: {complete_data.get('total_length', 0)}")
            print(f"  - agent_role: {complete_data.get('agent_role')}")
            print(f"  - is_streaming: {complete_data.get('is_streaming')}")
            print(f"  - response preview: '{complete_data.get('complete_response', '')[:100]}...'")
        else:
            print("❌ No complete event received")

        print()

        # Verify tokens
        if len(tokens_received) > 0:
            print(f"✅ Tokens streamed: {len(tokens_received)}")
            full_streamed_response = "".join(tokens_received)
            print(f"  - Total characters: {len(full_streamed_response)}")
            print(f"  - Preview: '{full_streamed_response[:100]}...'")
        else:
            print("❌ No tokens received")

        # ================================================================
        # Test 4: Verify SSE Manager Stats
        # ================================================================
        print_header("Test 4: SSE Manager Stats", "📊")

        stats = sse_manager.get_stats()
        print(f"Total Connections: {stats['total_connections']}")
        print(f"Execution Streams: {stats['execution_streams']}")
        print(f"Squad Streams: {stats['squad_streams']}")

        if str(task_execution_id) in stats['connections_by_execution']:
            print(f"✅ Execution {task_execution_id} tracked in SSE manager")
        else:
            print(f"⚠️  Execution {task_execution_id} not found in SSE manager")

        # ================================================================
        # Summary
        # ================================================================
        print_header("Test Summary", "🎉")

        all_checks_passed = (
            len(streaming_events) > 0 and
            len(complete_events) > 0 and
            len(tokens_received) > 0
        )

        if all_checks_passed:
            print("✅ All checks passed!")
            print("✅ SSE streaming is working correctly")
            print("✅ AgentMessageHandler → SSE Manager integration verified")
            print("✅ Ready for frontend integration")
        else:
            print("⚠️  Some checks failed:")
            if len(streaming_events) == 0:
                print("   ❌ No streaming events received")
            if len(complete_events) == 0:
                print("   ❌ No complete event received")
            if len(tokens_received) == 0:
                print("   ❌ No tokens received")

        print("\n" + "=" * 80)
        print("  SSE STREAMING TEST COMPLETE".center(80))
        print("=" * 80 + "\n")

        # Cleanup
        sse_manager.execution_connections[task_execution_id].discard(queue)
        sse_manager.all_connections.discard(queue)
        if queue in sse_manager.connection_metadata:
            del sse_manager.connection_metadata[queue]


if __name__ == "__main__":
    try:
        asyncio.run(test_sse_streaming())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
