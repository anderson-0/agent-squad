"""
Tests for MessageBus - Agent Communication
"""
import pytest
from uuid import uuid4
from datetime import datetime

from backend.agents.communication.message_bus import MessageBus, get_message_bus, reset_message_bus


@pytest.fixture
def message_bus():
    """Create a fresh message bus for each test"""
    reset_message_bus()
    bus = get_message_bus()
    yield bus
    reset_message_bus()


@pytest.mark.asyncio
async def test_send_message_point_to_point(message_bus):
    """Test sending a point-to-point message"""
    sender_id = uuid4()
    recipient_id = uuid4()

    message = await message_bus.send_message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content="Hello, agent!",
        message_type="question",
        metadata={"urgency": "high"}
    )

    assert message.sender_id == sender_id
    assert message.recipient_id == recipient_id
    assert message.content == "Hello, agent!"
    assert message.message_type == "question"
    assert message.message_metadata["urgency"] == "high"


@pytest.mark.asyncio
async def test_broadcast_message(message_bus):
    """Test broadcasting a message to all agents"""
    sender_id = uuid4()
    agent1_id = uuid4()
    agent2_id = uuid4()

    message = await message_bus.broadcast_message(
        sender_id=sender_id,
        content="Team announcement!",
        message_type="standup"
    )

    assert message.sender_id == sender_id
    assert message.recipient_id is None  # Broadcast has no specific recipient
    assert message.content == "Team announcement!"


@pytest.mark.asyncio
async def test_get_messages(message_bus):
    """Test retrieving messages for an agent"""
    sender_id = uuid4()
    recipient_id = uuid4()

    # Send multiple messages
    await message_bus.send_message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content="Message 1",
        message_type="question"
    )

    await message_bus.send_message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content="Message 2",
        message_type="answer"
    )

    # Get all messages
    messages = await message_bus.get_messages(recipient_id)
    assert len(messages) == 2

    # Filter by type
    questions = await message_bus.get_messages(recipient_id, message_type="question")
    assert len(questions) == 1
    assert questions[0].content == "Message 1"


@pytest.mark.asyncio
async def test_get_conversation(message_bus):
    """Test retrieving all messages for a task execution"""
    task_execution_id = uuid4()
    agent1_id = uuid4()
    agent2_id = uuid4()

    # Send messages for this task
    await message_bus.send_message(
        sender_id=agent1_id,
        recipient_id=agent2_id,
        content="Question",
        message_type="question",
        task_execution_id=task_execution_id
    )

    await message_bus.send_message(
        sender_id=agent2_id,
        recipient_id=agent1_id,
        content="Answer",
        message_type="answer",
        task_execution_id=task_execution_id
    )

    # Get conversation
    conversation = await message_bus.get_conversation(task_execution_id)
    assert len(conversation) == 2
    assert conversation[0].content == "Question"
    assert conversation[1].content == "Answer"


@pytest.mark.asyncio
async def test_subscribe_to_messages(message_bus):
    """Test subscribing to real-time messages"""
    agent_id = uuid4()
    received_messages = []

    # Define callback
    async def on_message(message):
        received_messages.append(message)

    # Subscribe
    await message_bus.subscribe(agent_id, on_message)

    # Send message
    await message_bus.send_message(
        sender_id=uuid4(),
        recipient_id=agent_id,
        content="Test notification",
        message_type="status_update"
    )

    # Check callback was called
    assert len(received_messages) == 1
    assert received_messages[0].content == "Test notification"


@pytest.mark.asyncio
async def test_message_bus_stats(message_bus):
    """Test message bus statistics"""
    sender_id = uuid4()
    recipient_id = uuid4()

    # Send some messages
    await message_bus.send_message(sender_id, recipient_id, "Msg 1", "question")
    await message_bus.send_message(sender_id, recipient_id, "Msg 2", "answer")
    await message_bus.broadcast_message(sender_id, "Broadcast", "standup")

    stats = message_bus.get_stats()

    assert stats["total_messages"] == 3
    assert stats["agents_with_messages"] >= 1


@pytest.mark.asyncio
async def test_clear_messages(message_bus):
    """Test clearing messages for an agent"""
    agent_id = uuid4()

    # Send messages
    await message_bus.send_message(uuid4(), agent_id, "Msg 1", "question")
    await message_bus.send_message(uuid4(), agent_id, "Msg 2", "answer")

    # Verify messages exist
    messages = await message_bus.get_messages(agent_id)
    assert len(messages) == 2

    # Clear messages
    await message_bus.clear_agent_messages(agent_id)

    # Verify cleared
    messages = await message_bus.get_messages(agent_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_message_filtering_by_time(message_bus):
    """Test filtering messages by timestamp"""
    import asyncio

    agent_id = uuid4()

    # Send first message
    await message_bus.send_message(uuid4(), agent_id, "Old message", "question")

    # Wait a bit
    await asyncio.sleep(0.1)

    # Record time
    since = datetime.utcnow()

    # Wait a bit more
    await asyncio.sleep(0.1)

    # Send second message
    await message_bus.send_message(uuid4(), agent_id, "New message", "answer")

    # Get messages since timestamp
    messages = await message_bus.get_messages(agent_id, since=since)

    # Should only get the new message
    assert len(messages) == 1
    assert messages[0].content == "New message"


@pytest.mark.asyncio
async def test_message_limit(message_bus):
    """Test limiting number of messages returned"""
    agent_id = uuid4()

    # Send multiple messages
    for i in range(10):
        await message_bus.send_message(
            uuid4(), agent_id, f"Message {i}", "question"
        )

    # Get with limit
    messages = await message_bus.get_messages(agent_id, limit=5)

    # Should only get last 5
    assert len(messages) == 5
