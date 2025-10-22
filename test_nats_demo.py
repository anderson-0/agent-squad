#!/usr/bin/env python3
"""
Quick NATS Demo - Test agent messaging with NATS JetStream

This shows how fast and simple NATS is compared to Kafka/Redis.
"""
import asyncio
import sys
import os
from datetime import datetime
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

# Disable logging noise
os.environ['DEBUG'] = 'False'
import logging
logging.basicConfig(level=logging.ERROR)

from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig

# Colors for terminal output
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


async def main():
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'🚀 NATS JetStream Demo - Agent Messaging'.center(70)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 70}{C.END}\n")

    # Connect to NATS
    print(f"{C.YELLOW}Step 1: Connecting to NATS server...{C.END}")
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    print(f"{C.GREEN}✓ Connected to NATS!{C.END}\n")

    # Get JetStream context
    js = nc.jetstream()

    # Create a stream for agent messages
    print(f"{C.YELLOW}Step 2: Creating JetStream stream 'agent-messages'...{C.END}")
    try:
        await js.add_stream(
            name="agent-messages",
            subjects=["agent.>"],  # All subjects starting with "agent."
            retention="limits",     # Keep messages based on limits
            max_msgs=10000,        # Max 10k messages
            max_age=7 * 24 * 60 * 60,  # 7 days retention
        )
        print(f"{C.GREEN}✓ Stream created!{C.END}")
    except Exception as e:
        if "stream name already in use" in str(e).lower():
            print(f"{C.GREEN}✓ Stream already exists!{C.END}")
        else:
            raise

    print(f"{C.CYAN}   Subjects: agent.>{C.END}")
    print(f"{C.CYAN}   Max messages: 10,000{C.END}")
    print(f"{C.CYAN}   Retention: 7 days{C.END}\n")

    # Publish some agent messages
    print(f"{C.YELLOW}Step 3: Publishing agent messages...{C.END}\n")

    messages = [
        ("agent.message.pm", "Good morning team! Daily standup starting."),
        ("agent.message.backend", "I'll implement the authentication API with JWT."),
        ("agent.message.frontend", "Working on the login UI components."),
        ("agent.message.qa", "Running integration tests for the new feature."),
        ("agent.message.devops", "Deploying to staging environment."),
    ]

    for subject, content in messages:
        timestamp = datetime.now().strftime("%H:%M:%S")
        ack = await js.publish(subject, content.encode())
        agent_type = subject.split('.')[-1].upper()
        print(f"  {C.CYAN}[{timestamp}]{C.END} {C.GREEN}✓{C.END} {agent_type}: {content}")
        print(f"    {C.CYAN}→ Sequence: {ack.seq}, Stream: {ack.stream}{C.END}")
        await asyncio.sleep(0.3)

    print(f"\n{C.GREEN}✓ Published {len(messages)} messages!{C.END}\n")

    # Subscribe and consume messages
    print(f"{C.YELLOW}Step 4: Consuming messages from stream...{C.END}\n")

    # Create a durable consumer
    psub = await js.pull_subscribe(
        subject="agent.>",
        durable="demo-consumer"
    )

    # Fetch messages
    print(f"{C.CYAN}Fetching messages (this proves they're persisted!):{C.END}\n")
    msgs = await psub.fetch(batch=len(messages), timeout=2)

    for msg in msgs:
        timestamp = datetime.now().strftime("%H:%M:%S")
        agent_type = msg.subject.split('.')[-1].upper()
        content = msg.data.decode()
        print(f"  {C.CYAN}[{timestamp}]{C.END} {C.GREEN}◀{C.END} {agent_type}: {content}")
        await msg.ack()

    print(f"\n{C.GREEN}✓ Consumed {len(msgs)} messages!{C.END}\n")

    # Show stream info
    print(f"{C.YELLOW}Step 5: Stream statistics...{C.END}\n")
    stream_info = await js.stream_info("agent-messages")
    print(f"  {C.CYAN}Stream Name:{C.END} {stream_info.config.name}")
    print(f"  {C.CYAN}Messages:{C.END} {stream_info.state.messages}")
    print(f"  {C.CYAN}Bytes:{C.END} {stream_info.state.bytes}")
    print(f"  {C.CYAN}First Seq:{C.END} {stream_info.state.first_seq}")
    print(f"  {C.CYAN}Last Seq:{C.END} {stream_info.state.last_seq}")
    print()

    # Demonstrate message replay (Kafka-like feature!)
    print(f"{C.YELLOW}Step 6: Message Replay (like Kafka!)...{C.END}\n")
    print(f"{C.CYAN}Replaying messages from the beginning...{C.END}\n")

    # Create a new consumer to replay from start
    psub2 = await js.pull_subscribe(
        subject="agent.>",
        durable="replay-consumer"
    )

    replay_msgs = await psub2.fetch(batch=3, timeout=2)
    for msg in replay_msgs:
        agent_type = msg.subject.split('.')[-1].upper()
        content = msg.data.decode()
        print(f"  {C.GREEN}⟲{C.END} {agent_type}: {content}")
        await msg.ack()

    print(f"\n{C.GREEN}✓ Replayed {len(replay_msgs)} messages!{C.END}\n")

    # Clean up
    await nc.close()

    # Final summary
    print(f"{C.BOLD}{C.CYAN}{'=' * 70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'✨ Demo Complete!'.center(70)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 70}{C.END}\n")

    print(f"{C.GREEN}What just happened:{C.END}")
    print(f"  ✓ Connected to NATS in milliseconds")
    print(f"  ✓ Created persistent stream with JetStream")
    print(f"  ✓ Published {len(messages)} messages (stored on disk)")
    print(f"  ✓ Consumed messages with acknowledgment")
    print(f"  ✓ Replayed messages from beginning (event sourcing!)")
    print()
    print(f"{C.CYAN}Key Benefits:{C.END}")
    print(f"  • {C.GREEN}Fast:{C.END} Sub-millisecond latency")
    print(f"  • {C.GREEN}Persistent:{C.END} Messages stored on disk")
    print(f"  • {C.GREEN}Simple:{C.END} No Zookeeper, no complex setup")
    print(f"  • {C.GREEN}Scalable:{C.END} Handles millions of messages/sec")
    print(f"  • {C.GREEN}Subject Routing:{C.END} Powerful pattern matching")
    print()
    print(f"{C.YELLOW}Compare to:{C.END}")
    print(f"  • Kafka: {C.CYAN}Same features, 10x more complex{C.END}")
    print(f"  • Redis: {C.CYAN}Similar features, slower and heavier{C.END}")
    print(f"  • RabbitMQ: {C.CYAN}No native replay, slower{C.END}")
    print()
    print(f"{C.BOLD}NATS = Best of all worlds! 🚀{C.END}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Demo interrupted{C.END}\n")
    except Exception as e:
        print(f"\n{C.YELLOW}Error: {e}{C.END}\n")
        import traceback
        traceback.print_exc()
