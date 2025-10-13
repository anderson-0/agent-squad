"""
Tests for Agent Messages API Endpoints
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient

from backend.models.user import User
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project, Task, TaskExecution
from backend.models.agent_message import AgentMessage


async def create_test_data(test_db, user_id):
    """Helper to create test data"""
    # Create squad
    squad = Squad(
        user_id=user_id,
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

    # Create task
    task = Task(
        project_id=project.id,
        title="Test Task",
        description="Test task",
        status="in_progress"
    )
    test_db.add(task)
    await test_db.flush()

    # Create task execution
    task_execution = TaskExecution(
        task_id=task.id,
        squad_id=squad.id,
        status="in_progress"
    )
    test_db.add(task_execution)
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

    # Create agent messages
    message1 = AgentMessage(
        task_execution_id=task_execution.id,
        sender_id=sender.id,
        recipient_id=recipient.id,
        content="Hello from backend",
        message_type="chat",
        message_metadata={"priority": "high"}
    )
    message2 = AgentMessage(
        task_execution_id=task_execution.id,
        sender_id=recipient.id,
        recipient_id=sender.id,
        content="Hello from frontend",
        message_type="chat",
        message_metadata={}
    )
    message3 = AgentMessage(
        task_execution_id=task_execution.id,
        sender_id=sender.id,
        recipient_id=None,  # Broadcast
        content="Broadcast message",
        message_type="status_update",
        message_metadata={}
    )
    test_db.add_all([message1, message2, message3])
    await test_db.flush()
    await test_db.commit()

    return {
        "squad": squad,
        "task_execution": task_execution,
        "sender": sender,
        "recipient": recipient,
        "message1": message1,
        "message2": message2,
        "message3": message3,
    }


async def get_auth_token(client: AsyncClient, test_user_data):
    """Helper to register and login"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_list_agent_messages(client: AsyncClient, test_db, test_user_data):
    """Test listing agent messages"""
    token = await get_auth_token(client, test_user_data)

    # Get user_id
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 3
    assert all("content" in msg for msg in result)


@pytest.mark.asyncio
async def test_list_agent_messages_by_sender(client: AsyncClient, test_db, test_user_data):
    """Test listing messages filtered by sender"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    sender_id = data["sender"].id

    response = await client.get(
        f"/api/v1/agent-messages?sender_id={sender_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 2  # message1 and message3


@pytest.mark.asyncio
async def test_list_agent_messages_by_type(client: AsyncClient, test_db, test_user_data):
    """Test listing messages filtered by type"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}&message_type=chat",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert all(msg["message_type"] == "chat" for msg in result)


@pytest.mark.asyncio
async def test_list_agent_messages_with_pagination(client: AsyncClient, test_db, test_user_data):
    """Test pagination"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}&skip=1&limit=1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_agent_messages_task_not_found(client: AsyncClient, test_db, test_user_data):
    """Test listing with non-existent task execution"""
    token = await get_auth_token(client, test_user_data)
    fake_id = uuid4()

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_agent_messages_without_auth(client: AsyncClient, test_db, test_user_data):
    """Test listing without authentication"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}"
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_agent_message(client: AsyncClient, test_db, test_user_data):
    """Test getting a specific message"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    message_id = data["message1"].id

    response = await client.get(
        f"/api/v1/agent-messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(message_id)
    assert result["content"] == "Hello from backend"


@pytest.mark.asyncio
async def test_get_agent_message_not_found(client: AsyncClient, test_user_data):
    """Test getting non-existent message"""
    token = await get_auth_token(client, test_user_data)
    fake_id = uuid4()

    response = await client.get(
        f"/api/v1/agent-messages/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_conversation(client: AsyncClient, test_db, test_user_data):
    """Test getting conversation between two agents"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    agent1_id = data["sender"].id
    agent2_id = data["recipient"].id

    response = await client.get(
        f"/api/v1/agent-messages/conversation/{agent1_id}/{agent2_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2  # message1 and message2


@pytest.mark.asyncio
async def test_get_agent_conversation_with_task_filter(client: AsyncClient, test_db, test_user_data):
    """Test getting conversation filtered by task execution"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    agent1_id = data["sender"].id
    agent2_id = data["recipient"].id
    task_execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages/conversation/{agent1_id}/{agent2_id}?task_execution_id={task_execution_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_agent_conversation_task_not_found(client: AsyncClient, test_db, test_user_data):
    """Test conversation with non-existent task execution"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    agent1_id = data["sender"].id
    agent2_id = data["recipient"].id
    fake_id = uuid4()

    response = await client.get(
        f"/api/v1/agent-messages/conversation/{agent1_id}/{agent2_id}?task_execution_id={fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_message_stats(client: AsyncClient, test_db, test_user_data):
    """Test getting message statistics"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    execution_id = data["task_execution"].id

    response = await client.get(
        f"/api/v1/agent-messages/stats/execution/{execution_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total_messages"] == 3
    assert result["execution_id"] == str(execution_id)
    assert result["messages_by_type"]["chat"] == 2
    assert result["broadcast_count"] == 1


@pytest.mark.asyncio
async def test_get_message_stats_not_found(client: AsyncClient, test_user_data):
    """Test stats for non-existent execution"""
    token = await get_auth_token(client, test_user_data)
    fake_id = uuid4()

    response = await client.get(
        f"/api/v1/agent-messages/stats/execution/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_agent_message(client: AsyncClient, test_db, test_user_data):
    """Test sending a message"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    sender_id = data["sender"].id
    recipient_id = data["recipient"].id
    task_execution_id = data["task_execution"].id

    message_data = {
        "sender_id": str(sender_id),
        "recipient_id": str(recipient_id),
        "content": "Test message",
        "message_type": "task_assignment",
        "task_execution_id": str(task_execution_id),
        "message_metadata": {"test": "data"}
    }

    response = await client.post(
        "/api/v1/agent-messages",
        json=message_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    result = response.json()
    assert result["content"] == "Test message"
    assert result["message_type"] == "task_assignment"


@pytest.mark.asyncio
async def test_send_agent_message_broadcast(client: AsyncClient, test_db, test_user_data):
    """Test sending a broadcast message"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    sender_id = data["sender"].id
    task_execution_id = data["task_execution"].id

    message_data = {
        "sender_id": str(sender_id),
        "recipient_id": None,  # Broadcast
        "content": "Broadcast test",
        "message_type": "announcement",
        "task_execution_id": str(task_execution_id)
    }

    response = await client.post(
        "/api/v1/agent-messages",
        json=message_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    result = response.json()
    assert result["recipient_id"] is None
    assert result["content"] == "Broadcast test"


@pytest.mark.asyncio
async def test_send_agent_message_task_not_found(client: AsyncClient, test_db, test_user_data):
    """Test sending message with non-existent task execution"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    sender_id = data["sender"].id
    recipient_id = data["recipient"].id
    fake_id = uuid4()

    message_data = {
        "sender_id": str(sender_id),
        "recipient_id": str(recipient_id),
        "content": "Test",
        "message_type": "chat",
        "task_execution_id": str(fake_id)
    }

    response = await client.post(
        "/api/v1/agent-messages",
        json=message_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_agent_messages_by_recipient(client: AsyncClient, test_db, test_user_data):
    """Test listing messages filtered by recipient"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    recipient_id = data["recipient"].id

    response = await client.get(
        f"/api/v1/agent-messages?recipient_id={recipient_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 1  # At least message1


@pytest.mark.asyncio
async def test_list_agent_messages_since_timestamp(client: AsyncClient, test_db, test_user_data):
    """Test listing messages filtered by timestamp"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    # Get messages created recently
    since = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}&since={since}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_agent_messages_empty_result(client: AsyncClient, test_db, test_user_data):
    """Test listing with filters that return no results"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    task_execution_id = data["task_execution"].id

    # Filter for messages in the future
    since = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = await client.get(
        f"/api/v1/agent-messages?task_execution_id={task_execution_id}&since={since}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_agent_conversation_empty(client: AsyncClient, test_db, test_user_data):
    """Test conversation between agents with no messages"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)

    # Use two non-interacting agent IDs
    fake_id1 = uuid4()
    fake_id2 = uuid4()

    response = await client.get(
        f"/api/v1/agent-messages/conversation/{fake_id1}/{fake_id2}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_message_stats_empty(client: AsyncClient, test_db, test_user_data):
    """Test stats for execution with no messages"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    # Create execution without messages
    squad = Squad(
        user_id=user.id,
        name="Empty Squad",
        status="active",
        config={}
    )
    test_db.add(squad)
    await test_db.flush()

    project = Project(
        squad_id=squad.id,
        name="Empty Project",
        description="Test",
        is_active=True
    )
    test_db.add(project)
    await test_db.flush()

    task = Task(
        project_id=project.id,
        title="Empty Task",
        description="Test task",
        status="in_progress"
    )
    test_db.add(task)
    await test_db.flush()

    task_execution = TaskExecution(
        task_id=task.id,
        squad_id=squad.id,
        status="in_progress"
    )
    test_db.add(task_execution)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/agent-messages/stats/execution/{task_execution.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total_messages"] == 0
    assert result["broadcast_count"] == 0


@pytest.mark.asyncio
async def test_delete_agent_message(client: AsyncClient, test_db, test_user_data):
    """Test deleting a message"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    message_id = data["message1"].id

    response = await client.delete(
        f"/api/v1/agent-messages/{message_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_agent_message_not_found(client: AsyncClient, test_user_data):
    """Test deleting non-existent message"""
    token = await get_auth_token(client, test_user_data)
    fake_id = uuid4()

    response = await client.delete(
        f"/api/v1/agent-messages/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_message_without_auth(client: AsyncClient, test_db, test_user_data):
    """Test deleting without authentication"""
    token = await get_auth_token(client, test_user_data)
    from backend.models.user import User
    from sqlalchemy import select
    result = await test_db.execute(select(User).where(User.email == test_user_data["email"]))
    user = result.scalar_one()

    data = await create_test_data(test_db, user.id)
    message_id = data["message1"].id

    response = await client.delete(
        f"/api/v1/agent-messages/{message_id}"
    )

    assert response.status_code == 403
