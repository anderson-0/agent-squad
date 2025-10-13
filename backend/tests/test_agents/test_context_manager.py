"""
Tests for ContextManager - Context Aggregation from Multiple Sources
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Mock problematic imports before importing ContextManager
import sys
sys.modules['backend.database'] = MagicMock()
sys.modules['backend.models.agent'] = MagicMock()
sys.modules['backend.agents.context.rag_service'] = MagicMock()

from backend.agents.context.context_manager import ContextManager


def mock_database_session():
    """Helper to create properly mocked database session"""
    mock_session = MagicMock()
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__.return_value = mock_db

    # Mock execute to return result with scalar_one_or_none
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    return mock_session


@pytest.fixture
def mock_rag_service():
    """Create a mocked RAG service"""
    rag = AsyncMock()
    rag.query = AsyncMock()
    rag.upsert = AsyncMock()
    return rag


@pytest.fixture
def mock_memory_store():
    """Create a mocked Memory store"""
    memory = AsyncMock()
    memory.get_context = AsyncMock()
    memory.store = AsyncMock()
    return memory


@pytest.fixture
def mock_history_manager():
    """Create a mocked History manager"""
    history = AsyncMock()
    history.get_conversation_history = AsyncMock()
    return history


@pytest.fixture
def context_manager(mock_rag_service, mock_memory_store, mock_history_manager):
    """Create ContextManager with mocked dependencies"""
    return ContextManager(
        rag_service=mock_rag_service,
        memory_store=mock_memory_store,
        history_manager=mock_history_manager,
    )


@pytest.mark.asyncio
async def test_init(mock_rag_service, mock_memory_store, mock_history_manager):
    """Test ContextManager initialization"""
    cm = ContextManager(
        rag_service=mock_rag_service,
        memory_store=mock_memory_store,
        history_manager=mock_history_manager,
    )

    assert cm.rag == mock_rag_service
    assert cm.memory == mock_memory_store
    assert cm.history == mock_history_manager


@pytest.mark.asyncio
async def test_build_context_basic(context_manager, mock_rag_service, mock_memory_store):
    """Test basic context building"""
    agent_id = uuid4()
    squad_id = uuid4()
    query = "How to implement authentication?"

    # Mock dependencies
    mock_rag_service.query.return_value = [
        {"id": "code_1", "text": "auth code", "score": 0.95}
    ]
    mock_memory_store.get_context.return_value = {"state": "implementing"}

    # Mock helper methods to avoid database issues
    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
        )

    # Verify context structure
    assert context["query"] == query
    assert context["squad_id"] == str(squad_id)
    assert context["agent_id"] == str(agent_id)
    assert "timestamp" in context
    assert "rag" in context
    assert "memory" in context
    assert context["conversation_history"] == []

    # Verify RAG was called for default sources (conversations=False by default)
    # Default: code=True, tickets=True, docs=True, conversations=False, decisions=True = 4 calls
    assert mock_rag_service.query.call_count == 4
    mock_memory_store.get_context.assert_called_once()


@pytest.mark.asyncio
async def test_build_context_with_code_only(context_manager, mock_rag_service, mock_memory_store):
    """Test context building with only code enabled"""
    agent_id = uuid4()
    squad_id = uuid4()
    query = "authentication logic"

    mock_rag_service.query.return_value = [{"id": "1", "text": "code"}]
    mock_memory_store.get_context.return_value = {}

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            include_code=True,
            include_tickets=False,
            include_docs=False,
            include_conversations=False,
            include_decisions=False,
        )

    # Only code should be queried
    assert mock_rag_service.query.call_count == 1
    mock_rag_service.query.assert_called_with(
        squad_id=squad_id,
        namespace="code",
        query=query,
        top_k=5,
    )
    assert "code" in context["rag"]


@pytest.mark.asyncio
async def test_build_context_with_all_sources(context_manager, mock_rag_service, mock_memory_store):
    """Test context building with all RAG sources enabled"""
    agent_id = uuid4()
    squad_id = uuid4()
    query = "test query"

    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            include_code=True,
            include_tickets=True,
            include_docs=True,
            include_conversations=True,
            include_decisions=True,
        )

    # All sources should be queried
    assert mock_rag_service.query.call_count == 5
    assert "code" in context["rag"]
    assert "tickets" in context["rag"]
    assert "docs" in context["rag"]
    assert "conversations" in context["rag"]
    assert "decisions" in context["rag"]


@pytest.mark.asyncio
async def test_build_context_with_task_execution(context_manager, mock_rag_service,
                                                  mock_memory_store, mock_history_manager):
    """Test context building with task execution ID (includes conversation history)"""
    agent_id = uuid4()
    squad_id = uuid4()
    task_execution_id = uuid4()
    query = "test"

    # Mock history messages
    mock_msg = MagicMock()
    mock_msg.created_at = datetime.utcnow()
    mock_msg.sender_id = uuid4()
    mock_msg.recipient_id = uuid4()
    mock_msg.message_type = "chat"
    mock_msg.content = "Test message"

    mock_history_manager.get_conversation_history.return_value = [mock_msg]
    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            task_execution_id=task_execution_id,
        )

    # Verify conversation history was retrieved
    mock_history_manager.get_conversation_history.assert_called_once_with(
        task_execution_id=task_execution_id,
        limit=20,
    )

    assert len(context["conversation_history"]) == 1
    assert context["conversation_history"][0]["content"] == "Test message"
    assert context["conversation_history"][0]["message_type"] == "chat"


@pytest.mark.asyncio
async def test_build_context_custom_limits(context_manager, mock_rag_service,
                                           mock_memory_store, mock_history_manager):
    """Test context building with custom limits"""
    agent_id = uuid4()
    squad_id = uuid4()
    task_execution_id = uuid4()

    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}
    mock_history_manager.get_conversation_history.return_value = []

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        await context_manager.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query="test",
            task_execution_id=task_execution_id,
            conversation_history_limit=50,
            max_results_per_source=10,
        )

    # Verify custom limits were used
    mock_history_manager.get_conversation_history.assert_called_once_with(
        task_execution_id=task_execution_id,
        limit=50,
    )

    # Check RAG was called with custom top_k
    for call in mock_rag_service.query.call_args_list:
        assert call[1]["top_k"] == 10


@pytest.mark.asyncio
async def test_build_context_for_ticket_review(context_manager, mock_rag_service, mock_memory_store):
    """Test specialized context for ticket review"""
    agent_id = uuid4()
    squad_id = uuid4()
    ticket = {
        "title": "Add user authentication",
        "description": "Implement JWT-based auth",
        "priority": "high"
    }

    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context_for_ticket_review(
            agent_id=agent_id,
            squad_id=squad_id,
            ticket=ticket,
        )

    # Verify ticket is included
    assert context["ticket"] == ticket

    # Verify query includes ticket info
    assert "Add user authentication" in context["query"]

    # Verify appropriate sources are queried (code, tickets, docs, decisions)
    # conversations should be False for ticket review
    assert mock_rag_service.query.call_count == 4


@pytest.mark.asyncio
async def test_build_context_for_implementation(context_manager, mock_rag_service,
                                                mock_memory_store, mock_history_manager):
    """Test specialized context for implementation"""
    agent_id = uuid4()
    squad_id = uuid4()
    task_execution_id = uuid4()
    task = {
        "description": "Implement login endpoint",
        "acceptance_criteria": ["Must use JWT", "Must hash passwords"]
    }

    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}
    mock_history_manager.get_conversation_history.return_value = []

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context_for_implementation(
            agent_id=agent_id,
            squad_id=squad_id,
            task=task,
            task_execution_id=task_execution_id,
        )

    # Verify task is included
    assert context["task"] == task

    # Verify query includes task info
    assert "Implement login endpoint" in context["query"]

    # Verify all sources are queried (including conversations)
    assert mock_rag_service.query.call_count == 5

    # Verify conversation history with higher limit
    mock_history_manager.get_conversation_history.assert_called_once_with(
        task_execution_id=task_execution_id,
        limit=30,
    )


@pytest.mark.asyncio
async def test_build_context_for_code_review(context_manager, mock_rag_service, mock_memory_store):
    """Test specialized context for code review"""
    agent_id = uuid4()
    squad_id = uuid4()
    pr_description = "Add JWT authentication"
    code_diff = "diff --git a/auth.py..."
    acceptance_criteria = ["Secure token generation", "Proper error handling"]

    mock_rag_service.query.return_value = []
    mock_memory_store.get_context.return_value = {}

    with patch.object(context_manager, '_get_squad_metadata', new=AsyncMock(return_value={})), \
         patch.object(context_manager, '_get_agent_metadata', new=AsyncMock(return_value={})):
        context = await context_manager.build_context_for_code_review(
            agent_id=agent_id,
            squad_id=squad_id,
            pr_description=pr_description,
            code_diff=code_diff,
            acceptance_criteria=acceptance_criteria,
        )

    # Verify PR details are included
    assert context["pr_description"] == pr_description
    assert context["code_diff"] == code_diff
    assert context["acceptance_criteria"] == acceptance_criteria

    # Verify query includes PR description
    assert "Add JWT authentication" in context["query"]

    # Verify only relevant sources are queried (code, docs, decisions)
    # tickets and conversations should be False
    assert mock_rag_service.query.call_count == 3


@pytest.mark.asyncio
async def test_store_context_in_memory(context_manager, mock_memory_store):
    """Test storing context in memory"""
    agent_id = uuid4()
    task_execution_id = uuid4()
    key = "implementation_plan"
    value = {"steps": ["Step 1", "Step 2"]}

    await context_manager.store_context_in_memory(
        agent_id=agent_id,
        task_execution_id=task_execution_id,
        key=key,
        value=value,
        ttl_seconds=7200,
    )

    mock_memory_store.store.assert_called_once_with(
        agent_id=agent_id,
        task_execution_id=task_execution_id,
        key=key,
        value=value,
        ttl_seconds=7200,
    )


@pytest.mark.asyncio
async def test_store_context_in_memory_default_ttl(context_manager, mock_memory_store):
    """Test storing context with default TTL"""
    agent_id = uuid4()

    await context_manager.store_context_in_memory(
        agent_id=agent_id,
        task_execution_id=None,
        key="test",
        value={"data": "test"},
    )

    # Verify default TTL is used
    mock_memory_store.store.assert_called_once()
    call_args = mock_memory_store.store.call_args[1]
    assert call_args["ttl_seconds"] == 3600


@pytest.mark.asyncio
async def test_update_rag_with_conversation(context_manager, mock_rag_service):
    """Test updating RAG with conversation summary"""
    squad_id = uuid4()
    task_execution_id = uuid4()
    summary = "Team discussed authentication approach and decided on JWT"

    await context_manager.update_rag_with_conversation(
        squad_id=squad_id,
        task_execution_id=task_execution_id,
        conversation_summary=summary,
    )

    # Verify RAG upsert was called
    mock_rag_service.upsert.assert_called_once()
    call_args = mock_rag_service.upsert.call_args[1]

    assert call_args["squad_id"] == squad_id
    assert call_args["namespace"] == "conversations"
    assert len(call_args["documents"]) == 1

    doc = call_args["documents"][0]
    assert doc["id"] == f"conversation_{task_execution_id}"
    assert doc["text"] == summary
    assert "task_execution_id" in doc["metadata"]


@pytest.mark.asyncio
async def test_update_rag_with_decision(context_manager, mock_rag_service):
    """Test updating RAG with architecture decision"""
    squad_id = uuid4()
    decision_id = "ADR-001"
    decision_text = "We will use PostgreSQL for relational data"
    metadata = {"author": "tech_lead", "date": "2025-10-13"}

    await context_manager.update_rag_with_decision(
        squad_id=squad_id,
        decision_id=decision_id,
        decision_text=decision_text,
        metadata=metadata,
    )

    # Verify RAG upsert was called
    mock_rag_service.upsert.assert_called_once()
    call_args = mock_rag_service.upsert.call_args[1]

    assert call_args["squad_id"] == squad_id
    assert call_args["namespace"] == "decisions"
    assert len(call_args["documents"]) == 1

    doc = call_args["documents"][0]
    assert doc["id"] == decision_id
    assert doc["text"] == decision_text
    assert doc["metadata"] == metadata


@pytest.mark.asyncio
async def test_update_rag_with_decision_no_metadata(context_manager, mock_rag_service):
    """Test updating RAG with decision without metadata"""
    squad_id = uuid4()
    decision_id = "ADR-002"
    decision_text = "Use Redis for caching"

    await context_manager.update_rag_with_decision(
        squad_id=squad_id,
        decision_id=decision_id,
        decision_text=decision_text,
    )

    # Verify empty metadata dict is used
    call_args = mock_rag_service.upsert.call_args[1]
    doc = call_args["documents"][0]
    assert doc["metadata"] == {}
