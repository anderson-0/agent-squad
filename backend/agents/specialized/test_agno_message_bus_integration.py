"""
Tests for Agno Message Bus Integration

Verifies that Agno agents can send and receive messages via the message bus.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.agents.factory import AgentFactory
from backend.core.agno_config import initialize_agno, shutdown_agno
from backend.agents.communication.message_bus import get_message_bus, reset_message_bus
from backend.schemas.agent_message import TaskAssignment, Question, Answer


@pytest.fixture(scope="module", autouse=True)
def setup_agno():
    """Initialize Agno framework for all tests"""
    initialize_agno()
    yield
    shutdown_agno()


@pytest.fixture
async def clean_message_bus():
    """Reset message bus before each test"""
    await reset_message_bus()
    yield
    await reset_message_bus()


@pytest.mark.asyncio
async def test_agno_agent_send_message(clean_message_bus):
    """Test Agno agent can send message via message bus"""
    # Create agents with IDs
    pm_id = uuid4()
    dev_id = uuid4()

    pm = AgentFactory.create_agent(
        agent_id=pm_id,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
    )

    dev = AgentFactory.create_agent(
        agent_id=dev_id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
    )

    # Verify agents have IDs
    assert pm.agent_id == pm_id
    assert dev.agent_id == dev_id

    # PM sends message to Dev
    execution_id = uuid4()
    message = await pm.send_message(
        recipient_id=dev_id,
        content="Test message content",
        message_type="task_assignment",
        task_execution_id=execution_id,
    )

    # Verify message was sent
    assert message is not None
    assert message.sender_id == pm_id
    assert message.recipient_id == dev_id
    assert message.content == "Test message content"
    assert message.message_type == "task_assignment"
    assert message.task_execution_id == execution_id

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_receive_messages(clean_message_bus):
    """Test Agno agent can receive messages from message bus"""
    # Create agents
    pm_id = uuid4()
    dev_id = uuid4()

    pm = AgentFactory.create_agent(
        agent_id=pm_id,
        role="project_manager",
        force_agno=True,
    )

    dev = AgentFactory.create_agent(
        agent_id=dev_id,
        role="backend_developer",
        force_agno=True,
    )

    # PM sends message to Dev
    await pm.send_message(
        recipient_id=dev_id,
        content="Message 1",
        message_type="task_assignment",
    )

    await pm.send_message(
        recipient_id=dev_id,
        content="Message 2",
        message_type="question",
    )

    # Dev receives messages
    messages = await dev.receive_messages()

    # Verify messages received
    assert len(messages) == 2
    assert all(msg.sender_id == pm_id for msg in messages)
    assert all(msg.recipient_id == dev_id for msg in messages)

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_broadcast_message(clean_message_bus):
    """Test Agno agent can broadcast message to all agents"""
    # Create agents
    pm_id = uuid4()
    dev1_id = uuid4()
    dev2_id = uuid4()

    pm = AgentFactory.create_agent(agent_id=pm_id, role="project_manager", force_agno=True)
    dev1 = AgentFactory.create_agent(agent_id=dev1_id, role="backend_developer", force_agno=True)
    dev2 = AgentFactory.create_agent(agent_id=dev2_id, role="frontend_developer", force_agno=True)

    # Ensure message bus has initialized queues by sending a non-broadcast message first
    # This is a quirk of the in-memory message bus implementation - queues are created
    # lazily when first message is sent to that agent
    await pm.send_message(
        recipient_id=dev1_id,
        content="Initialize queue",
        message_type="test",
    )

    await pm.send_message(
        recipient_id=dev2_id,
        content="Initialize queue",
        message_type="test",
    )

    # PM broadcasts message
    broadcast_msg = await pm.broadcast_message(
        content="Standup time!",
        message_type="standup",
    )

    # Verify broadcast
    assert broadcast_msg.sender_id == pm_id
    assert broadcast_msg.recipient_id is None  # Broadcast has no specific recipient

    # Both agents should receive 2 messages each (initialize + broadcast)
    dev1_messages = await dev1.receive_messages()
    dev2_messages = await dev2.receive_messages()

    assert len(dev1_messages) == 2
    assert len(dev2_messages) == 2

    # Verify broadcast was received by both agents
    dev1_broadcasts = [m for m in dev1_messages if m.message_type == "standup"]
    dev2_broadcasts = [m for m in dev2_messages if m.message_type == "standup"]

    assert len(dev1_broadcasts) == 1
    assert len(dev2_broadcasts) == 1

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_message_filtering(clean_message_bus):
    """Test Agno agent can filter messages by type"""
    # Create agents
    pm_id = uuid4()
    dev_id = uuid4()

    pm = AgentFactory.create_agent(agent_id=pm_id, role="project_manager", force_agno=True)
    dev = AgentFactory.create_agent(agent_id=dev_id, role="backend_developer", force_agno=True)

    # Send different message types
    await pm.send_message(
        recipient_id=dev_id,
        content="Task 1",
        message_type="task_assignment",
    )

    await pm.send_message(
        recipient_id=dev_id,
        content="Question 1",
        message_type="question",
    )

    await pm.send_message(
        recipient_id=dev_id,
        content="Task 2",
        message_type="task_assignment",
    )

    # Filter by message type
    task_messages = await dev.receive_messages(message_type="task_assignment")
    question_messages = await dev.receive_messages(message_type="question")

    assert len(task_messages) == 2
    assert len(question_messages) == 1
    assert all(msg.message_type == "task_assignment" for msg in task_messages)
    assert all(msg.message_type == "question" for msg in question_messages)

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_message_with_structured_payload(clean_message_bus):
    """Test sending structured message payloads (TaskAssignment, Question, etc.)"""
    # Create agents
    pm_id = uuid4()
    dev_id = uuid4()
    tl_id = uuid4()

    pm = AgentFactory.create_agent(agent_id=pm_id, role="project_manager", force_agno=True)
    dev = AgentFactory.create_agent(agent_id=dev_id, role="backend_developer", force_agno=True)
    tl = AgentFactory.create_agent(agent_id=tl_id, role="tech_lead", force_agno=True)

    # Send TaskAssignment
    task = TaskAssignment(
        recipient=dev_id,
        task_id="TASK-001",
        description="Implement feature X",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        context="Project context",
        priority="high",
    )

    await pm.send_message(
        recipient_id=dev_id,
        content=task.model_dump_json(),
        message_type="task_assignment",
        metadata={"task_id": task.task_id},
    )

    # Send Question
    question = Question(
        recipient=tl_id,
        task_id="TASK-001",
        question="How should we implement this?",
        context="Need guidance",
        urgency="high",
    )

    await dev.send_message(
        recipient_id=tl_id,
        content=question.model_dump_json(),
        message_type="question",
        metadata={"task_id": question.task_id},
    )

    # Send Answer
    answer = Answer(
        recipient=dev_id,
        task_id="TASK-001",
        question_id="Q1",
        answer="Here's how to implement it...",
        confidence="high",
    )

    await tl.send_message(
        recipient_id=dev_id,
        content=answer.model_dump_json(),
        message_type="answer",
        metadata={"task_id": answer.task_id},
    )

    # Verify messages
    dev_messages = await dev.receive_messages()
    tl_messages = await tl.receive_messages()

    assert len(dev_messages) == 2  # TaskAssignment + Answer
    assert len(tl_messages) == 1   # Question

    # Verify structured content can be parsed
    task_msg = next(m for m in dev_messages if m.message_type == "task_assignment")
    task_parsed = TaskAssignment.model_validate_json(task_msg.content)
    assert task_parsed.task_id == "TASK-001"
    assert task_parsed.priority == "high"

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_conversation_tracking(clean_message_bus):
    """Test full conversation tracking across multiple messages"""
    # Create agents
    pm_id = uuid4()
    dev_id = uuid4()

    pm = AgentFactory.create_agent(agent_id=pm_id, role="project_manager", force_agno=True)
    dev = AgentFactory.create_agent(agent_id=dev_id, role="backend_developer", force_agno=True)

    # Create task execution
    execution_id = uuid4()

    # Send multiple messages
    await pm.send_message(
        recipient_id=dev_id,
        content="Message 1",
        message_type="task_assignment",
        task_execution_id=execution_id,
    )

    await dev.send_message(
        recipient_id=pm_id,
        content="Message 2",
        message_type="status_update",
        task_execution_id=execution_id,
    )

    await pm.send_message(
        recipient_id=dev_id,
        content="Message 3",
        message_type="question",
        task_execution_id=execution_id,
    )

    # Get conversation
    message_bus = get_message_bus()
    conversation = await message_bus.get_conversation(
        task_execution_id=execution_id,
    )

    # Verify conversation
    assert len(conversation) == 3
    assert all(msg.task_execution_id == execution_id for msg in conversation)

    # Verify chronological order
    assert conversation[0].message_type == "task_assignment"
    assert conversation[1].message_type == "status_update"
    assert conversation[2].message_type == "question"

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_agno_agent_requires_agent_id():
    """Test that message bus methods require agent_id"""
    # Create agent without agent_id
    agent = AgentFactory.create_agent(
        agent_id=uuid4(),
        role="project_manager",
        force_agno=True,
    )

    # Manually set agent_id to None to test error handling
    agent.agent_id = None

    # Verify send_message raises ValueError
    with pytest.raises(ValueError, match="agent_id must be configured"):
        await agent.send_message(
            recipient_id=uuid4(),
            content="Test",
            message_type="test",
        )

    # Verify receive_messages raises ValueError
    with pytest.raises(ValueError, match="agent_id must be configured"):
        await agent.receive_messages()

    # Verify subscribe_to_messages raises ValueError
    with pytest.raises(ValueError, match="agent_id must be configured"):
        await agent.subscribe_to_messages(callback=lambda msg: None)

    # Clean up
    AgentFactory.clear_all_agents()


@pytest.mark.asyncio
async def test_message_metadata_includes_framework_info(clean_message_bus):
    """Test that messages include Agno framework metadata"""
    # Create agents
    pm_id = uuid4()
    dev_id = uuid4()

    pm = AgentFactory.create_agent(agent_id=pm_id, role="project_manager", force_agno=True)
    dev = AgentFactory.create_agent(agent_id=dev_id, role="backend_developer", force_agno=True)

    # Send message
    await pm.send_message(
        recipient_id=dev_id,
        content="Test message",
        message_type="task_assignment",
    )

    # Receive and verify metadata
    messages = await dev.receive_messages()
    assert len(messages) == 1

    msg = messages[0]
    assert msg.message_metadata is not None
    assert msg.message_metadata["framework"] == "agno"
    assert msg.message_metadata["agent_role"] == "project_manager"
    assert "session_id" in msg.message_metadata

    # Clean up
    AgentFactory.clear_all_agents()
