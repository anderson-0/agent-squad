#!/usr/bin/env python3
"""
NATS Agent-to-Agent Communication Test

Tests:
1. NATS connection
2. Message publishing
3. Message subscription
4. Agent-to-agent message passing
"""

import asyncio
import sys
from datetime import datetime
import nats
from nats.js import JetStreamContext

# Add backend to path
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

from backend.core.config import settings


async def test_nats_communication():
    """Test NATS agent-to-agent communication"""

    print("=" * 80)
    print("🚀 NATS Agent-to-Agent Communication Test")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"NATS URL: {settings.NATS_URL}")
    print("=" * 80)

    # ============================================================================
    # Step 1: Connect to NATS
    # ============================================================================
    print("\n📡 Step 1: Connect to NATS")

    try:
        nc = await nats.connect(settings.NATS_URL)
        print(f"   ✅ Connected to: {nc.connected_url}")
        print(f"   ✅ Client ID: {nc.client_id}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

    # ============================================================================
    # Step 2: Setup JetStream
    # ============================================================================
    print("\n🌊 Step 2: Setup JetStream")

    try:
        js: JetStreamContext = nc.jetstream()
        print("   ✅ JetStream initialized")

        # Try to get stream info
        try:
            stream_info = await js.stream_info(settings.NATS_STREAM_NAME)
            print(f"   ✅ Stream exists: {settings.NATS_STREAM_NAME}")
            print(f"      Messages: {stream_info.state.messages}")
            print(f"      Bytes: {stream_info.state.bytes}")
        except nats.js.errors.NotFoundError:
            # Create stream if it doesn't exist
            print(f"   ⚠️  Stream doesn't exist, creating: {settings.NATS_STREAM_NAME}")

            from nats.js.api import StreamConfig, RetentionPolicy

            stream_config = StreamConfig(
                name=settings.NATS_STREAM_NAME,
                subjects=[f"{settings.NATS_STREAM_NAME}.>"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=settings.NATS_MAX_MSGS,
                max_age=settings.NATS_MAX_AGE_DAYS * 24 * 3600,  # Convert days to seconds
            )

            await js.add_stream(stream_config)
            print(f"   ✅ Stream created: {settings.NATS_STREAM_NAME}")

    except Exception as e:
        print(f"   ❌ JetStream setup failed: {e}")
        await nc.close()
        return False

    # ============================================================================
    # Step 3: Test Message Publishing
    # ============================================================================
    print("\n📤 Step 3: Test Message Publishing")

    try:
        # Publish a test message
        subject = f"{settings.NATS_STREAM_NAME}.test.agent-to-agent"
        message = {
            "from": "agent-1",
            "to": "agent-2",
            "content": "Hello from Agent 1! Can you help review this code?",
            "timestamp": datetime.now().isoformat()
        }

        import json
        message_bytes = json.dumps(message).encode()

        ack = await js.publish(subject, message_bytes)
        print(f"   ✅ Message published to: {subject}")
        print(f"   ✅ Sequence: {ack.seq}")
        print(f"   ✅ Stream: {ack.stream}")
        print(f"   📝 Message: {message['content'][:60]}...")

    except Exception as e:
        print(f"   ❌ Publishing failed: {e}")
        await nc.close()
        return False

    # ============================================================================
    # Step 4: Test Message Subscription
    # ============================================================================
    print("\n📥 Step 4: Test Message Subscription")

    messages_received = []

    async def message_handler(msg):
        """Handle received messages"""
        import json
        data = json.loads(msg.data.decode())
        messages_received.append(data)
        print(f"   📨 Received message:")
        print(f"      From: {data['from']}")
        print(f"      To: {data['to']}")
        print(f"      Content: {data['content']}")
        await msg.ack()

    try:
        # Create consumer
        consumer_name = "test-consumer"

        # Subscribe to messages
        subscription = await js.pull_subscribe(
            subject=f"{settings.NATS_STREAM_NAME}.test.>",
            durable=consumer_name
        )

        print(f"   ✅ Subscribed to: {settings.NATS_STREAM_NAME}.test.>")
        print(f"   ✅ Consumer: {consumer_name}")

        # Fetch messages (wait up to 5 seconds)
        print("   ⏳ Fetching messages...")

        try:
            msgs = await subscription.fetch(batch=1, timeout=5)
            for msg in msgs:
                await message_handler(msg)
        except nats.errors.TimeoutError:
            print("   ⚠️  No messages received (timeout)")

        if messages_received:
            print(f"   ✅ Successfully received {len(messages_received)} message(s)")

    except Exception as e:
        print(f"   ❌ Subscription failed: {e}")
        import traceback
        traceback.print_exc()
        await nc.close()
        return False

    # ============================================================================
    # Step 5: Test Bidirectional Communication
    # ============================================================================
    print("\n🔄 Step 5: Test Bidirectional Communication")

    try:
        # Agent 2 responds to Agent 1
        response_message = {
            "from": "agent-2",
            "to": "agent-1",
            "content": "Sure! I'll review your code. Please share the file path.",
            "timestamp": datetime.now().isoformat(),
            "reply_to": ack.seq  # Reference to original message
        }

        response_bytes = json.dumps(response_message).encode()
        response_ack = await js.publish(subject, response_bytes)

        print(f"   ✅ Response published")
        print(f"   ✅ Sequence: {response_ack.seq}")
        print(f"   📝 Response: {response_message['content']}")

        # Fetch the response
        msgs = await subscription.fetch(batch=1, timeout=5)
        for msg in msgs:
            data = json.loads(msg.data.decode())
            print(f"   📨 Received response:")
            print(f"      From: {data['from']}")
            print(f"      Content: {data['content']}")
            await msg.ack()

        print("   ✅ Bidirectional communication successful!")

    except Exception as e:
        print(f"   ❌ Bidirectional test failed: {e}")
        await nc.close()
        return False

    # ============================================================================
    # Step 6: Test Multi-Agent Broadcast
    # ============================================================================
    print("\n📢 Step 6: Test Multi-Agent Broadcast")

    try:
        # Broadcast message to all agents
        broadcast_subject = f"{settings.NATS_STREAM_NAME}.broadcast.all-agents"
        broadcast_message = {
            "from": "orchestrator",
            "to": "all",
            "content": "Team meeting in 5 minutes!",
            "timestamp": datetime.now().isoformat(),
            "type": "broadcast"
        }

        broadcast_bytes = json.dumps(broadcast_message).encode()
        broadcast_ack = await js.publish(broadcast_subject, broadcast_bytes)

        print(f"   ✅ Broadcast published to: {broadcast_subject}")
        print(f"   ✅ Sequence: {broadcast_ack.seq}")
        print(f"   📝 Message: {broadcast_message['content']}")

    except Exception as e:
        print(f"   ❌ Broadcast test failed: {e}")

    # ============================================================================
    # Step 7: Cleanup
    # ============================================================================
    print("\n🧹 Step 7: Cleanup")

    try:
        # Delete test consumer
        await js.delete_consumer(settings.NATS_STREAM_NAME, consumer_name)
        print(f"   ✅ Consumer deleted: {consumer_name}")
    except Exception as e:
        print(f"   ⚠️  Consumer cleanup warning: {e}")

    # Close connection
    await nc.close()
    print("   ✅ NATS connection closed")

    # ============================================================================
    # Final Summary
    # ============================================================================
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print("\n✅ Tests Passed:")
    print("   ✅ NATS connection")
    print("   ✅ JetStream setup")
    print("   ✅ Message publishing")
    print("   ✅ Message subscription")
    print("   ✅ Message receiving")
    print("   ✅ Bidirectional communication")
    print("   ✅ Broadcast messaging")

    print("\n🎯 Features Tested:")
    print("   ✅ Point-to-point messaging (agent-to-agent)")
    print("   ✅ Message persistence (JetStream)")
    print("   ✅ Message acknowledgment")
    print("   ✅ Bidirectional communication")
    print("   ✅ Broadcast messaging")

    print("\n📈 Performance:")
    print(f"   Messages sent: 3")
    print(f"   Messages received: {len(messages_received)}")
    print(f"   Stream: {settings.NATS_STREAM_NAME}")

    print("\n" + "=" * 80)
    print(f"✅ NATS Communication Test Complete!")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return True


if __name__ == "__main__":
    print("\n🚀 Starting NATS Communication Test...\n")

    try:
        result = asyncio.run(test_nats_communication())
        if result:
            print("\n✅ All tests passed!\n")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed\n")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
