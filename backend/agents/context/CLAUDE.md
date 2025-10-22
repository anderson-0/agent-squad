# Context Management Module

## Overview

The `context/` module provides intelligent context aggregation for agents, combining information from multiple sources (RAG, memory, history, database) to help agents make informed decisions.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                     Context Management                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Context Manager (Aggregator)                 │    │
│  │          Builds comprehensive context for agents          │    │
│  └────────────┬─────────────────────┬─────────────┬─────────┘    │
│               │                     │             │               │
│               ▼                     ▼             ▼               │
│  ┌─────────────────┐   ┌────────────────┐   ┌────────────────┐  │
│  │   RAG Service   │   │  Memory Store  │   │    History     │  │
│  │   (Pinecone)    │   │    (Redis)     │   │   Manager      │  │
│  │                 │   │                │   │  (PostgreSQL)  │  │
│  │ - Code          │   │ - Task State   │   │ - Messages     │  │
│  │ - Tickets       │   │ - Decisions    │   │ - Conversations│  │
│  │ - Docs          │   │ - Blockers     │   │                │  │
│  │ - Conversations │   │ - Plans        │   │                │  │
│  │ - Decisions     │   │                │   │                │  │
│  └─────────────────┘   └────────────────┘   └────────────────┘  │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `context_manager.py` - Context Aggregator

**Purpose**: Aggregates context from all sources for agent decision-making

**Key Method**: `build_context()`
Location: `context_manager.py:60`

```python
context = await context_manager.build_context(
    agent_id=agent_id,
    squad_id=squad_id,
    query="user authentication implementation",
    task_execution_id=execution_id,
    include_code=True,
    include_tickets=True,
    include_docs=True,
    include_conversations=False,
    include_decisions=True,
    max_results_per_source=5
)

# Returns:
# {
#     "query": "...",
#     "timestamp": "...",
#     "squad": {...},
#     "agent": {...},
#     "rag": {
#         "code": [...],
#         "tickets": [...],
#         "docs": [...],
#         "decisions": [...]
#     },
#     "memory": {...},
#     "conversation_history": [...]
# }
```

**Specialized Context Builders**:
- `build_context_for_ticket_review()`: PM + TL ticket review (location: `context_manager.py:178`)
- `build_context_for_implementation()`: Developer implementation (location: `context_manager.py:215`)
- `build_context_for_code_review()`: Tech Lead code review (location: `context_manager.py:255`)

**Business Rules**:
1. Context is query-driven (semantic search via RAG)
2. Recent conversation history included automatically
3. Memory TTL: default 1 hour
4. RAG results limited to avoid context overflow
5. Namespaces isolated by squad_id

---

### 2. `rag_service.py` - Vector Search (Pinecone)

**Purpose**: Semantic search across code, tickets, docs, conversations, and decisions

**Architecture**:
- **Single Pinecone Index**: `agent-squad`
- **Namespace Strategy**: `{squad_id}:{knowledge_type}`
- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Similarity Metric**: Cosine similarity

**Knowledge Types (Namespaces)**:
1. `code`: Code from Git repositories
2. `tickets`: Jira/ClickUp tickets and resolutions
3. `docs`: Confluence, Notion, Google Docs
4. `conversations`: Past agent discussions
5. `decisions`: Architecture Decision Records (ADRs)

**Key Methods**:

#### `upsert()` - Store documents
Location: `rag_service.py:147`

```python
await rag_service.upsert(
    squad_id=squad_id,
    namespace="code",
    documents=[
        {
            "id": "src/auth/login.py",
            "text": "...file content...",
            "metadata": {
                "repository": "backend",
                "branch": "main",
                "file_path": "src/auth/login.py"
            }
        }
    ]
)
```

**Batch Processing**:
- Embeddings generated in batches of 2048
- Upserts in batches of 100 (Pinecone limit)

#### `query()` - Semantic search
Location: `rag_service.py:198`

```python
results = await rag_service.query(
    squad_id=squad_id,
    namespace="code",
    query="user authentication login",
    top_k=5,
    filter_metadata={"repository": "backend"}
)

# Returns:
# [
#     {
#         "id": "src/auth/login.py",
#         "score": 0.87,  # Similarity score (0-1)
#         "text": "...",
#         "metadata": {...}
#     },
#     ...
# ]
```

#### `query_multiple_namespaces()` - Parallel search
Location: `rag_service.py:253`

```python
results = await rag_service.query_multiple_namespaces(
    squad_id=squad_id,
    namespaces=["code", "tickets", "docs"],
    query="authentication",
    top_k_per_namespace=3
)

# Returns: {"code": [...], "tickets": [...], "docs": [...]}
```

**Specialized Indexers**:

```python
# Index code file
await rag_service.index_code_file(
    squad_id=squad_id,
    file_path="src/auth/login.py",
    content=file_content,
    repository="backend",
    branch="main",
    commit_hash="abc123"
)

# Index ticket
await rag_service.index_ticket(
    squad_id=squad_id,
    ticket_id="PROJ-123",
    title="Implement login",
    description="...",
    resolution="Implemented JWT authentication",
    metadata={"priority": "high"}
)

# Index documentation
await rag_service.index_document(
    squad_id=squad_id,
    document_id="auth-guide",
    title="Authentication Guide",
    content="...",
    source="confluence",
    url="https://..."
)
```

**Business Rules**:
1. Squad isolation via namespaces (`{squad_id}:{type}`)
2. Automatic metadata addition (squad_id, namespace_type)
3. Text truncated to 1000 chars in metadata
4. Embedding caching via `@lru_cache` (optional)
5. Serverless Pinecone (AWS, us-east-1)

**Cost Considerations**:
- OpenAI embeddings: ~$0.02 per 1M tokens
- Pinecone: Serverless pricing (pay per request)
- Batch processing reduces API calls

---

### 3. `memory_store.py` - Short-term Memory (Redis)

**Purpose**: Fast, temporary working memory for agents during task execution

**Key Format**: `agent:{agent_id}:task:{task_execution_id}:memory:{key}`

**Core Operations**:

```python
# Store value with TTL
await memory_store.store(
    agent_id=agent_id,
    task_execution_id=execution_id,
    key="current_plan",
    value={"step": 1, "status": "planning"},
    ttl_seconds=3600  # 1 hour
)

# Retrieve value
plan = await memory_store.get(
    agent_id=agent_id,
    task_execution_id=execution_id,
    key="current_plan",
    default=None
)

# Get all memory as context
context = await memory_store.get_context(
    agent_id=agent_id,
    task_execution_id=execution_id
)
```

**Specialized Memory Methods**:

#### Store Decision
Location: `memory_store.py:229`

```python
await memory_store.store_decision(
    agent_id=tech_lead_id,
    task_execution_id=execution_id,
    decision="Use JWT for authentication",
    reasoning="Industry standard, stateless, scalable",
    alternatives_considered=["Sessions", "OAuth only"],
    ttl_seconds=7200  # 2 hours
)
```

#### Store Task State
Location: `memory_store.py:283`

```python
await memory_store.store_task_state(
    agent_id=developer_id,
    task_execution_id=execution_id,
    state="implementing",
    progress_percentage=60,
    details="Completed login API, working on tests"
)
```

#### Store Blockers
Location: `memory_store.py:336`

```python
await memory_store.add_blocker(
    agent_id=developer_id,
    task_execution_id=execution_id,
    blocker="Waiting for API spec from PM",
    severity="high"
)

blockers = await memory_store.get_blockers(
    agent_id=developer_id,
    task_execution_id=execution_id
)
```

#### Store Implementation Plan
Location: `memory_store.py:415`

```python
await memory_store.store_implementation_plan(
    agent_id=developer_id,
    task_execution_id=execution_id,
    plan={
        "steps": [...],
        "files_to_modify": [...],
        "estimated_hours": 8
    }
)
```

**Business Rules**:
1. Default TTL: 1 hour (3600 seconds)
2. Decision TTL: 2 hours (7200 seconds)
3. JSON serialization for complex types
4. Automatic expiration via Redis TTL
5. Task-specific memory cleared when task completes

**Redis Key Strategy**:
- Agent-wide: `agent:{agent_id}:memory:{key}`
- Task-specific: `agent:{agent_id}:task:{task_id}:memory:{key}`
- Pattern matching for cleanup: `agent:{agent_id}:*`

---

## Integration Flow

### Example: Developer implements feature

```
1. Context Manager builds context:
   ├─ RAG: Query "user authentication" in code namespace
   │  └─ Returns: Existing auth code, patterns, examples
   │
   ├─ RAG: Query "authentication" in tickets namespace
   │  └─ Returns: Past auth tickets, solutions
   │
   ├─ RAG: Query "authentication" in docs namespace
   │  └─ Returns: Auth documentation, guides
   │
   ├─ Memory: Get agent's current task state
   │  └─ Returns: {state: "planning", progress: 20%}
   │
   └─ History: Get recent conversation messages
      └─ Returns: Questions asked, answers received

2. Developer receives comprehensive context:
   {
     "rag": {
       "code": [5 relevant code files],
       "tickets": [3 similar past tickets],
       "docs": [2 auth guides]
     },
     "memory": {
       "task_state": {...},
       "last_decision": {...}
     },
     "conversation_history": [10 recent messages]
   }

3. Developer creates implementation plan
4. Plan stored in memory (TTL: 2 hours)
5. As work progresses, state updated in memory
6. When blocked, blocker added to memory
7. On completion, conversation stored in RAG for future reference
```

---

## Performance Optimization

### RAG Service
- **Embedding Generation**: Batch up to 2048 texts
- **Pinecone Queries**: ~100ms per query
- **Parallel Queries**: Use `query_multiple_namespaces()`
- **Caching**: Consider LRU cache for common queries

### Memory Store
- **Redis Performance**: Sub-millisecond retrieval
- **TTL Management**: Automatic expiration (no manual cleanup)
- **Batch Operations**: Use pipelines for multiple gets/sets
- **Connection Pooling**: Redis connection pool (default: 10)

### Context Manager
- **Parallel Retrieval**: RAG queries run in parallel
- **Result Limiting**: Max 5 results per source (configurable)
- **Query Optimization**: Truncate long queries to 500 chars
- **Selective Inclusion**: Only include needed context types

---

## Business Rules Summary

### Context Manager
1. Query drives semantic search
2. Context tailored to task type (ticket review, implementation, code review)
3. Squad metadata always included
4. Agent metadata always included
5. Conversation history limited (default: 20 messages)

### RAG Service
1. Squad isolation via namespaces
2. All embeddings via OpenAI
3. Cosine similarity for ranking
4. Serverless Pinecone (auto-scaling)
5. Metadata filters for precision

### Memory Store
1. Task-specific memory auto-expires
2. Default TTL: 1 hour
3. Decisions stored for 2 hours
4. JSON serialization for all types
5. Redis connection via URL (env var)

---

## Production Considerations

### Scaling RAG
- **Index Size**: Monitor Pinecone vector count
- **Query Performance**: Add metadata indexes
- **Cost Optimization**: Cache common queries
- **Embedding Caching**: Deduplicate before generating embeddings

### Scaling Memory
- **Redis Cluster**: Multi-node for high availability
- **Persistence**: Enable Redis AOF for durability
- **Eviction Policy**: `allkeys-lru` for memory limits
- **Monitoring**: Track memory usage, hit rates

### Scaling Context
- **Lazy Loading**: Don't fetch unused context types
- **Caching Layer**: Cache context for repeat requests
- **Compression**: Compress large context before passing to LLM
- **Summarization**: Summarize long RAG results

---

## Testing

```python
import pytest
from backend.agents.context import ContextManager, RAGService, MemoryStore

@pytest.mark.asyncio
async def test_build_context():
    context_manager = ContextManager(rag_service, memory_store, history_manager)

    context = await context_manager.build_context(
        agent_id=agent_id,
        squad_id=squad_id,
        query="test query",
        include_code=True
    )

    assert "rag" in context
    assert "code" in context["rag"]
    assert "memory" in context

@pytest.mark.asyncio
async def test_rag_upsert_query():
    rag = RAGService()

    # Upsert
    await rag.upsert(
        squad_id=squad_id,
        namespace="test",
        documents=[{"id": "1", "text": "test", "metadata": {}}]
    )

    # Query
    results = await rag.query(
        squad_id=squad_id,
        namespace="test",
        query="test",
        top_k=1
    )

    assert len(results) == 1
    assert results[0]["id"] == "1"

@pytest.mark.asyncio
async def test_memory_store():
    memory = MemoryStore()

    await memory.store(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="test",
        value={"data": "value"},
        ttl_seconds=60
    )

    value = await memory.get(
        agent_id=agent_id,
        task_execution_id=task_id,
        key="test"
    )

    assert value == {"data": "value"}

    await memory.close()
```

---

## Troubleshooting

**Q: RAG query returns no results?**
- Verify documents were upserted to correct namespace
- Check squad_id matches
- Verify Pinecone index exists
- Test query with broader search terms

**Q: Memory values not persisting?**
- Check Redis connection (REDIS_URL env var)
- Verify TTL hasn't expired
- Check Redis memory limits
- Review Redis logs for errors

**Q: Context too large for LLM?**
- Reduce `max_results_per_source`
- Disable unused context types
- Truncate RAG result text
- Summarize conversation history

**Q: Slow context building?**
- Use `query_multiple_namespaces()` for parallel queries
- Reduce number of context sources
- Cache frequently requested contexts
- Optimize RAG queries with metadata filters

---

## Related Documentation

- See `../CLAUDE.md` for agent architecture
- See `../communication/CLAUDE.md` for message history
- See `../orchestration/CLAUDE.md` for task orchestration
- See `/backend/services/` for service layer
- See Pinecone docs: https://docs.pinecone.io
- See Redis docs: https://redis.io/docs
