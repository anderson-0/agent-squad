"""
Tests for MemoryStore - Redis-based Short-term Memory
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys

# Mock modules to avoid import issues
sys.modules['backend.agents.context.rag_service'] = MagicMock()
sys.modules['backend.agents.context.context_manager'] = MagicMock()

from backend.agents.context.memory_store import MemoryStore


@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.close = AsyncMock()
    redis_mock.setex = AsyncMock()
    redis_mock.get = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.keys = AsyncMock()
    return redis_mock


@pytest.fixture
def memory_store(mock_redis):
    """Create MemoryStore with mocked Redis"""
    with patch('redis.asyncio.from_url', return_value=mock_redis):
        store = MemoryStore()
        return store


@pytest.mark.asyncio
async def test_close(memory_store, mock_redis):
    """Test closing Redis connection"""
    await memory_store.close()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_build_key_basic(memory_store):
    """Test building basic Redis key"""
    agent_id = uuid4()
    key = memory_store._build_key(agent_id)

    assert key == f"agent:{agent_id}:memory"


@pytest.mark.asyncio
async def test_build_key_with_task(memory_store):
    """Test building key with task execution ID"""
    agent_id = uuid4()
    task_id = uuid4()

    key = memory_store._build_key(agent_id, task_id)

    assert key == f"agent:{agent_id}:task:{task_id}:memory"


@pytest.mark.asyncio
async def test_build_key_with_suffix(memory_store):
    """Test building key with suffix"""
    agent_id = uuid4()
    task_id = uuid4()

    key = memory_store._build_key(agent_id, task_id, "state")

    assert key == f"agent:{agent_id}:task:{task_id}:memory:state"


@pytest.mark.asyncio
async def test_store(memory_store, mock_redis):
    """Test storing a value"""
    agent_id = uuid4()
    task_id = uuid4()

    await memory_store.store(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="test_key",
        value={"data": "test"},
        ttl_seconds=3600
    )

    # Verify setex was called with correct arguments
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    # Check key format
    assert f"agent:{agent_id}:task:{task_id}:memory:test_key" == call_args[0]
    # Check TTL
    assert call_args[1] == 3600
    # Check value is JSON serialized
    assert json.loads(call_args[2]) == {"data": "test"}


@pytest.mark.asyncio
async def test_get(memory_store, mock_redis):
    """Test retrieving a value"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock Redis returning JSON string
    mock_redis.get.return_value = json.dumps({"data": "test"})

    result = await memory_store.get(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="test_key"
    )

    assert result == {"data": "test"}
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_with_default(memory_store, mock_redis):
    """Test getting value that doesn't exist returns default"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock Redis returning None
    mock_redis.get.return_value = None

    result = await memory_store.get(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="nonexistent",
        default={"default": "value"}
    )

    assert result == {"default": "value"}


@pytest.mark.asyncio
async def test_delete(memory_store, mock_redis):
    """Test deleting a value"""
    agent_id = uuid4()
    task_id = uuid4()

    await memory_store.delete(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="test_key"
    )

    mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_keys(memory_store, mock_redis):
    """Test getting all memory keys"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock Redis returning keys
    base_key = f"agent:{agent_id}:task:{task_id}:memory:"
    mock_redis.keys.return_value = [
        f"{base_key}key1",
        f"{base_key}key2",
        f"{base_key}key3"
    ]

    keys = await memory_store.get_all_keys(agent_id, task_id)

    assert keys == ["key1", "key2", "key3"]


@pytest.mark.asyncio
async def test_get_context(memory_store, mock_redis):
    """Test getting all memory as context dictionary"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock keys
    base_key = f"agent:{agent_id}:task:{task_id}:memory:"
    mock_redis.keys.return_value = [
        f"{base_key}state",
        f"{base_key}plan"
    ]

    # Mock get calls
    async def mock_get(key):
        if key.endswith(":state"):
            return json.dumps({"current": "planning"})
        elif key.endswith(":plan"):
            return json.dumps({"step": 1})
        return None

    mock_redis.get.side_effect = mock_get

    context = await memory_store.get_context(agent_id, task_id)

    assert "state" in context
    assert "plan" in context
    assert context["state"] == {"current": "planning"}
    assert context["plan"] == {"step": 1}


@pytest.mark.asyncio
async def test_clear(memory_store, mock_redis):
    """Test clearing all memory"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock keys
    mock_redis.keys.return_value = ["key1", "key2", "key3"]

    await memory_store.clear(agent_id, task_id)

    # Should delete all returned keys
    mock_redis.delete.assert_called_once_with("key1", "key2", "key3")


@pytest.mark.asyncio
async def test_clear_no_keys(memory_store, mock_redis):
    """Test clearing when no keys exist"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock no keys
    mock_redis.keys.return_value = []

    await memory_store.clear(agent_id, task_id)

    # Should not call delete
    mock_redis.delete.assert_not_called()


@pytest.mark.asyncio
async def test_store_decision(memory_store, mock_redis):
    """Test storing a decision"""
    agent_id = uuid4()
    task_id = uuid4()

    await memory_store.store_decision(
        agent_id=agent_id,
        task_execution_id=task_id,
        decision="Use PostgreSQL",
        reasoning="Better ACID compliance",
        alternatives_considered=["MongoDB", "MySQL"],
        ttl_seconds=7200
    )

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    # Check TTL
    assert call_args[1] == 7200

    # Check stored data
    stored_data = json.loads(call_args[2])
    assert stored_data["decision"] == "Use PostgreSQL"
    assert stored_data["reasoning"] == "Better ACID compliance"
    assert "MongoDB" in stored_data["alternatives_considered"]


@pytest.mark.asyncio
async def test_get_last_decision(memory_store, mock_redis):
    """Test getting last decision"""
    agent_id = uuid4()
    task_id = uuid4()

    decision_data = {
        "decision": "Use PostgreSQL",
        "reasoning": "Better ACID compliance",
        "alternatives_considered": ["MongoDB"]
    }
    mock_redis.get.return_value = json.dumps(decision_data)

    result = await memory_store.get_last_decision(agent_id, task_id)

    assert result["decision"] == "Use PostgreSQL"
    assert result["reasoning"] == "Better ACID compliance"


@pytest.mark.asyncio
async def test_store_task_state(memory_store, mock_redis):
    """Test storing task state"""
    agent_id = uuid4()
    task_id = uuid4()

    await memory_store.store_task_state(
        agent_id=agent_id,
        task_execution_id=task_id,
        state="implementing",
        progress_percentage=45,
        details="Working on authentication",
        ttl_seconds=3600
    )

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    stored_data = json.loads(call_args[2])
    assert stored_data["state"] == "implementing"
    assert stored_data["progress_percentage"] == 45
    assert stored_data["details"] == "Working on authentication"


@pytest.mark.asyncio
async def test_get_task_state(memory_store, mock_redis):
    """Test getting task state"""
    agent_id = uuid4()
    task_id = uuid4()

    state_data = {
        "state": "implementing",
        "progress_percentage": 45
    }
    mock_redis.get.return_value = json.dumps(state_data)

    result = await memory_store.get_task_state(agent_id, task_id)

    assert result["state"] == "implementing"
    assert result["progress_percentage"] == 45


@pytest.mark.asyncio
async def test_store_blockers(memory_store, mock_redis):
    """Test storing blockers"""
    agent_id = uuid4()
    task_id = uuid4()

    blockers = [
        {"blocker": "Missing API credentials", "severity": "high"},
        {"blocker": "Waiting for code review", "severity": "medium"}
    ]

    await memory_store.store_blockers(
        agent_id=agent_id,
        task_execution_id=task_id,
        blockers=blockers,
        ttl_seconds=3600
    )

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    stored_data = json.loads(call_args[2])
    assert len(stored_data) == 2
    assert stored_data[0]["blocker"] == "Missing API credentials"


@pytest.mark.asyncio
async def test_get_blockers(memory_store, mock_redis):
    """Test getting blockers"""
    agent_id = uuid4()
    task_id = uuid4()

    blockers = [{"blocker": "Test blocker", "severity": "low"}]
    mock_redis.get.return_value = json.dumps(blockers)

    result = await memory_store.get_blockers(agent_id, task_id)

    assert len(result) == 1
    assert result[0]["blocker"] == "Test blocker"


@pytest.mark.asyncio
async def test_get_blockers_empty(memory_store, mock_redis):
    """Test getting blockers when none exist"""
    agent_id = uuid4()
    task_id = uuid4()

    mock_redis.get.return_value = None

    result = await memory_store.get_blockers(agent_id, task_id)

    assert result == []


@pytest.mark.asyncio
async def test_add_blocker(memory_store, mock_redis):
    """Test adding a new blocker"""
    agent_id = uuid4()
    task_id = uuid4()

    # Mock existing blockers
    existing = [{"blocker": "Existing", "severity": "low"}]
    mock_redis.get.return_value = json.dumps(existing)

    await memory_store.add_blocker(
        agent_id=agent_id,
        task_execution_id=task_id,
        blocker="New blocker",
        severity="high"
    )

    # Should have called setex to store updated blockers
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    stored_data = json.loads(call_args[2])
    assert len(stored_data) == 2
    assert stored_data[1]["blocker"] == "New blocker"
    assert stored_data[1]["severity"] == "high"


@pytest.mark.asyncio
async def test_store_implementation_plan(memory_store, mock_redis):
    """Test storing implementation plan"""
    agent_id = uuid4()
    task_id = uuid4()

    plan = {
        "steps": ["Step 1", "Step 2"],
        "estimated_hours": 8
    }

    await memory_store.store_implementation_plan(
        agent_id=agent_id,
        task_execution_id=task_id,
        plan=plan,
        ttl_seconds=7200
    )

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]

    assert call_args[1] == 7200
    stored_data = json.loads(call_args[2])
    assert stored_data["steps"] == ["Step 1", "Step 2"]


@pytest.mark.asyncio
async def test_get_implementation_plan(memory_store, mock_redis):
    """Test getting implementation plan"""
    agent_id = uuid4()
    task_id = uuid4()

    plan = {"steps": ["Step 1"], "estimated_hours": 4}
    mock_redis.get.return_value = json.dumps(plan)

    result = await memory_store.get_implementation_plan(agent_id, task_id)

    assert result["steps"] == ["Step 1"]
    assert result["estimated_hours"] == 4
