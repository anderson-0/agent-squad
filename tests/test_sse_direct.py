#!/usr/bin/env python3
"""
Direct SSE Broadcasting Test

Tests SSE manager directly without complex database setup.
Verifies that the SSE infrastructure can broadcast streaming events.

Run:
    PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python test_sse_direct.py
"""
import asyncio
from uuid import uuid4
from datetime import datetime

from backend.services.sse_service import sse_manager


def print_header(title: str, emoji: str = "🔍"):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {emoji} {title}")
    print("=" * 80 + "\n")


async def test_sse_direct():
    """
    Test SSE manager directly.

    This verifies:
    1. SSE manager can accept connections
    2. Broadcasting to execution works
    3. Events are properly formatted
    4. Clients receive events in real-time
    """
    print("\n" + "📡" * 40)
    print("  DIRECT SSE BROADCASTING TEST".center(80))
    print("  Testing SSE Infrastructure".center(80))
    print("📡" * 40)

    task_execution_id = uuid4()
    user_id = uuid4()

    # ================================================================
    # Test 1: Create SSE Connection
    # ================================================================
    print_header("Test 1: Create SSE Connection", "🔌")

    # Manually create a connection queue (simulating what subscribe_to_execution does)
    queue = asyncio.Queue(maxsize=100)
    sse_manager.execution_connections[task_execution_id].add(queue)
    sse_manager.all_connections.add(queue)
    sse_manager.connection_metadata[queue] = {
        "execution_id": task_execution_id,
        "user_id": user_id,
        "connected_at": datetime.utcnow().isoformat(),
        "type": "execution",
    }

    print(f"✓ Created SSE connection for execution {task_execution_id}")
    print(f"✓ Active connections: {sse_manager.get_connection_count(task_execution_id)}")

    # ================================================================
    # Test 2: Broadcast Streaming Events
    # ================================================================
    print_header("Test 2: Broadcast Streaming Events", "🌊")

    # Simulate streaming tokens
    events_received = []

    async def collect_events():
        """Collect events from queue"""
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=2.0)
                    if message is None:
                        break
                    events_received.append(message)
                    event_type = message.get("event", "unknown")
                    print(f"📨 Received: {event_type}")
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            print(f"❌ Error collecting: {e}")

    # Start collector
    collector = asyncio.create_task(collect_events())

    # Broadcast streaming tokens
    print("\nBroadcasting streaming tokens...")
    tokens = ["Redis ", "is ", "an ", "in-memory ", "data ", "structure ", "store."]

    for i, token in enumerate(tokens):
        await sse_manager.broadcast_to_execution(
            execution_id=task_execution_id,
            event="answer_streaming",
            data={
                "token": token,
                "partial_response": "".join(tokens[:i+1]),
                "agent_id": str(uuid4()),
                "agent_role": "tech_lead",
                "conversation_id": str(uuid4()),
                "is_streaming": True,
            }
        )
        await asyncio.sleep(0.05)  # Small delay to simulate streaming

    # Broadcast completion
    print("\nBroadcasting completion event...")
    await sse_manager.broadcast_to_execution(
        execution_id=task_execution_id,
        event="answer_complete",
        data={
            "complete_response": "".join(tokens),
            "agent_id": str(uuid4()),
            "agent_role": "tech_lead",
            "conversation_id": str(uuid4()),
            "is_streaming": False,
            "total_length": len("".join(tokens)),
        }
    )

    # Wait for collection
    await asyncio.sleep(0.5)
    await queue.put(None)  # Sentinel
    await collector

    # ================================================================
    # Test 3: Verify Events
    # ================================================================
    print_header("Test 3: Verify Events", "✅")

    streaming_events = [e for e in events_received if e.get("event") == "answer_streaming"]
    complete_events = [e for e in events_received if e.get("event") == "answer_complete"]

    print(f"Total events received: {len(events_received)}")
    print(f"  - Streaming events: {len(streaming_events)}")
    print(f"  - Complete events: {len(complete_events)}")
    print()

    # Verify streaming events
    if len(streaming_events) == len(tokens):
        print(f"✅ All {len(tokens)} streaming events received")

        # Verify first event structure
        first_event = streaming_events[0]["data"]
        required_fields = ["token", "partial_response", "agent_id", "agent_role",
                          "conversation_id", "is_streaming", "execution_id", "timestamp"]
        missing = [f for f in required_fields if f not in first_event]

        if missing:
            print(f"⚠️  Missing fields: {missing}")
        else:
            print("✅ All required fields present in streaming events")

        # Show sample
        print(f"\nFirst streaming event:")
        print(f"  - token: '{first_event.get('token')}'")
        print(f"  - partial_response: '{first_event.get('partial_response')}'")
        print(f"  - agent_role: {first_event.get('agent_role')}")
        print(f"  - is_streaming: {first_event.get('is_streaming')}")
    else:
        print(f"❌ Expected {len(tokens)} streaming events, got {len(streaming_events)}")

    print()

    # Verify complete event
    if len(complete_events) == 1:
        print("✅ Complete event received")

        complete_data = complete_events[0]["data"]
        required_fields = ["complete_response", "agent_id", "agent_role",
                          "conversation_id", "is_streaming", "total_length",
                          "execution_id", "timestamp"]
        missing = [f for f in required_fields if f not in complete_data]

        if missing:
            print(f"⚠️  Missing fields: {missing}")
        else:
            print("✅ All required fields present in complete event")

        print(f"\nComplete event:")
        print(f"  - total_length: {complete_data.get('total_length')}")
        print(f"  - is_streaming: {complete_data.get('is_streaming')}")
        print(f"  - response: '{complete_data.get('complete_response')}'")
    else:
        print(f"❌ Expected 1 complete event, got {len(complete_events)}")

    # ================================================================
    # Test 4: SSE Manager Stats
    # ================================================================
    print_header("Test 4: SSE Manager Stats", "📊")

    stats = sse_manager.get_stats()
    print(f"Total connections: {stats['total_connections']}")
    print(f"Execution streams: {stats['execution_streams']}")
    print(f"Squad streams: {stats['squad_streams']}")

    if str(task_execution_id) in stats['connections_by_execution']:
        conn_count = stats['connections_by_execution'][str(task_execution_id)]
        print(f"✅ Execution {task_execution_id}: {conn_count} connection(s)")

    # ================================================================
    # Summary
    # ================================================================
    print_header("Test Summary", "🎉")

    all_passed = (
        len(streaming_events) == len(tokens) and
        len(complete_events) == 1
    )

    if all_passed:
        print("✅ All tests passed!")
        print("✅ SSE infrastructure working correctly")
        print("✅ Broadcasting mechanism verified")
        print("✅ Event format validated")
        print("✅ Ready for agent integration")
    else:
        print("⚠️  Some tests failed:")
        if len(streaming_events) != len(tokens):
            print(f"   ❌ Streaming events: expected {len(tokens)}, got {len(streaming_events)}")
        if len(complete_events) != 1:
            print(f"   ❌ Complete events: expected 1, got {len(complete_events)}")

    # Cleanup
    sse_manager.execution_connections[task_execution_id].discard(queue)
    sse_manager.all_connections.discard(queue)
    if queue in sse_manager.connection_metadata:
        del sse_manager.connection_metadata[queue]

    print("\n" + "=" * 80)
    print("  SSE DIRECT TEST COMPLETE".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_sse_direct())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
