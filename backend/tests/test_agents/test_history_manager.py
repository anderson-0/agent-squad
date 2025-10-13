"""
Tests for HistoryManager - Conversation History Management
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.agents.communication.history_manager import HistoryManager
from backend.models.message import AgentMessage
from backend.models.user import User
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project, TaskExecution


@pytest.fixture
async def test_fixtures(test_db):
    """Create test fixtures for messages"""
    # Create user
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hash",
        plan_tier="pro",
        is_active=True
    )
    test_db.add(user)
    await test_db.flush()

    # Create squad
    squad = Squad(
        user_id=user.id,
        name="Test Squad",
        status="active",
        config={}
    )
    test_db.add(squad)
    await test_db.flush()

    # Create project
    project = Project(
        squad_id=squad.id,
        name="Test Project",
        description="Test",
        is_active=True
    )
    test_db.add(project)
    await test_db.flush()

    # Create task (required for TaskExecution)
    from backend.models.project import Task
    task = Task(
        project_id=project.id,
        title="Test Task",
        description="Test task description",
        status="in_progress"
    )
    test_db.add(task)
    await test_db.flush()

    # Create squad members
    sender = SquadMember(
        squad_id=squad.id,
        role="backend_developer",
        system_prompt="You are a backend developer.",
        llm_provider="openai",
        llm_model="gpt-4",
        is_active=True
    )
    recipient = SquadMember(
        squad_id=squad.id,
        role="frontend_developer",
        system_prompt="You are a frontend developer.",
        llm_provider="openai",
        llm_model="gpt-4",
        is_active=True
    )
    test_db.add_all([sender, recipient])
    await test_db.flush()

    # Create task execution
    task_execution = TaskExecution(
        task_id=task.id,
        squad_id=squad.id,
        status="in_progress"
    )
    test_db.add(task_execution)
    await test_db.flush()
    await test_db.commit()

    return {
        "task_execution_id": task_execution.id,
        "sender_id": sender.id,
        "recipient_id": recipient.id,
        "user": user,
        "squad": squad,
        "project": project,
        "task": task,
    }


@pytest.mark.asyncio
async def test_store_message(test_db, test_fixtures):
    """Test storing a message"""
    history_manager = HistoryManager(test_db)

    message = await history_manager.store_message(
        task_execution_id=test_fixtures["task_execution_id"],
        sender_id=test_fixtures["sender_id"],
        recipient_id=test_fixtures["recipient_id"],
        content="Test message content",
        message_type="task_assignment",
        metadata={"priority": "high"},
    )

    assert message.id is not None
    assert message.task_execution_id == test_fixtures["task_execution_id"]
    assert message.sender_id == test_fixtures["sender_id"]
    assert message.recipient_id == test_fixtures["recipient_id"]
    assert message.content == "Test message content"
    assert message.message_type == "task_assignment"
    assert message.message_metadata["priority"] == "high"


@pytest.mark.asyncio
async def test_store_message_without_metadata(test_db, test_fixtures):
    """Test storing a message without metadata"""
    history_manager = HistoryManager(test_db)

    message = await history_manager.store_message(
        task_execution_id=test_fixtures["task_execution_id"],
        sender_id=test_fixtures["sender_id"],
        recipient_id=None,  # Broadcast message
        content="Broadcast message",
        message_type="status_update",
    )

    assert message.id is not None
    assert message.recipient_id is None
    assert message.message_metadata == {}


@pytest.mark.asyncio
async def test_get_conversation_history(test_db, test_fixtures):
    """Test retrieving conversation history"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]
    sender_id = test_fixtures["sender_id"]

    # Store multiple messages
    for i in range(5):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=sender_id,
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Get conversation history
    messages = await history_manager.get_conversation_history(
        task_execution_id=task_execution_id
    )

    assert len(messages) == 5
    assert messages[0].content == "Message 1"
    assert messages[4].content == "Message 5"


@pytest.mark.asyncio
async def test_get_conversation_history_with_limit(test_db, test_fixtures):
    """Test conversation history with limit"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store 10 messages
    for i in range(10):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Get with limit
    messages = await history_manager.get_conversation_history(
        task_execution_id=task_execution_id,
        limit=3
    )

    assert len(messages) == 3


@pytest.mark.asyncio
async def test_get_conversation_history_with_offset(test_db, test_fixtures):
    """Test conversation history with offset"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store 5 messages
    for i in range(5):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Skip first 2 messages
    messages = await history_manager.get_conversation_history(
        task_execution_id=task_execution_id,
        offset=2
    )

    assert len(messages) == 3
    assert messages[0].content == "Message 3"


@pytest.mark.asyncio
async def test_get_conversation_history_since(test_db, test_fixtures):
    """Test conversation history filtered by time"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store messages
    for i in range(3):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Get messages from 1 hour ago (should get all)
    since = datetime.utcnow() - timedelta(hours=1)
    messages = await history_manager.get_conversation_history(
        task_execution_id=task_execution_id,
        since=since
    )

    assert len(messages) == 3


@pytest.mark.asyncio
async def test_get_agent_messages(test_db, test_fixtures):
    """Test getting messages for a specific agent"""
    history_manager = HistoryManager(test_db)

    agent_id = test_fixtures["sender_id"]
    task_execution_id = test_fixtures["task_execution_id"]
    other_agent_id = test_fixtures["recipient_id"]

    # Store messages where agent is sender
    await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=agent_id,
        recipient_id=other_agent_id,
        content="From agent",
        message_type="chat",
    )

    # Store message where agent is recipient
    await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=other_agent_id,
        recipient_id=agent_id,
        content="To agent",
        message_type="chat",
    )

    # Store broadcast message
    await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=other_agent_id,
        recipient_id=None,
        content="Broadcast",
        message_type="status_update",
    )

    # Get agent messages
    messages = await history_manager.get_agent_messages(
        agent_id=agent_id,
        task_execution_id=task_execution_id
    )

    assert len(messages) == 3


@pytest.mark.asyncio
async def test_get_agent_messages_filtered_by_type(test_db, test_fixtures):
    """Test getting agent messages filtered by type"""
    history_manager = HistoryManager(test_db)

    agent_id = test_fixtures["sender_id"]
    task_execution_id = test_fixtures["task_execution_id"]

    # Store different types of messages
    await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=agent_id,
        recipient_id=test_fixtures["recipient_id"],
        content="Chat message",
        message_type="chat",
    )

    await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=agent_id,
        recipient_id=test_fixtures["recipient_id"],
        content="Task assignment",
        message_type="task_assignment",
    )

    # Get only task_assignment messages
    messages = await history_manager.get_agent_messages(
        agent_id=agent_id,
        task_execution_id=task_execution_id,
        message_type="task_assignment"
    )

    assert len(messages) == 1
    assert messages[0].message_type == "task_assignment"


@pytest.mark.asyncio
async def test_get_conversation_summary(test_db, test_fixtures):
    """Test getting conversation summary"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]
    sender_id = test_fixtures["sender_id"]
    recipient_id = test_fixtures["recipient_id"]

    # Store some messages
    for i in range(3):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Get summary
    summary = await history_manager.get_conversation_summary(
        task_execution_id=task_execution_id
    )

    assert "Conversation History (3 messages)" in summary
    assert "Message 1" in summary
    assert "Message 2" in summary
    assert "Message 3" in summary


@pytest.mark.asyncio
async def test_get_conversation_summary_empty(test_db):
    """Test getting summary for empty conversation"""
    history_manager = HistoryManager(test_db)

    summary = await history_manager.get_conversation_summary(
        task_execution_id=uuid4()
    )

    assert summary == "No conversation history."


@pytest.mark.asyncio
async def test_summarize_conversation(test_db, test_fixtures):
    """Test conversation summarization with old/recent split"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store some messages
    for i in range(5):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Summarize (all messages are recent)
    result = await history_manager.summarize_conversation(
        task_execution_id=task_execution_id,
        summarize_older_than_hours=24
    )

    assert result["summary"] is None  # No old messages
    assert len(result["recent_messages"]) == 5
    assert result["total_messages"] == 5


@pytest.mark.asyncio
async def test_get_message_count(test_db, test_fixtures):
    """Test getting message count"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store messages
    for i in range(7):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Get count
    count = await history_manager.get_message_count(
        task_execution_id=task_execution_id
    )

    assert count == 7


@pytest.mark.asyncio
async def test_get_message_count_empty(test_db):
    """Test message count for conversation with no messages"""
    history_manager = HistoryManager(test_db)

    count = await history_manager.get_message_count(
        task_execution_id=uuid4()
    )

    assert count == 0


@pytest.mark.asyncio
async def test_delete_old_messages(test_db, test_fixtures):
    """Test deleting old messages"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]

    # Store some messages
    for i in range(3):
        await history_manager.store_message(
            task_execution_id=task_execution_id,
            sender_id=test_fixtures["sender_id"],
            recipient_id=test_fixtures["recipient_id"],
            content=f"Message {i+1}",
            message_type="chat",
        )

    # Try to delete messages older than 30 days (should delete none)
    deleted_count = await history_manager.delete_old_messages(
        older_than_days=30
    )

    # Since messages were just created, none should be deleted
    assert deleted_count == 0


@pytest.mark.asyncio
async def test_to_conversation_messages(test_db, test_fixtures):
    """Test converting database messages to conversation format"""
    history_manager = HistoryManager(test_db)

    task_execution_id = test_fixtures["task_execution_id"]
    sender_id = test_fixtures["sender_id"]
    recipient_id = test_fixtures["recipient_id"]

    # Store a message
    db_message = await history_manager.store_message(
        task_execution_id=task_execution_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        content="Test message",
        message_type="chat",
    )

    # Convert to conversation messages
    conversation_messages = history_manager.to_conversation_messages([db_message])

    assert len(conversation_messages) == 1
    msg = conversation_messages[0]
    assert msg.role == "user"
    assert msg.content == "Test message"
    assert msg.metadata["sender_id"] == str(sender_id)
    assert msg.metadata["recipient_id"] == str(recipient_id)
    assert msg.metadata["message_type"] == "chat"
