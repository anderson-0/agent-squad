# Agent Communication Module

## Overview

The `communication/` module provides the infrastructure for agent-to-agent (A2A) communication. It implements a message bus pattern with pub/sub capabilities, structured message protocols, and conversation history management.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  Communication Architecture                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐          ┌──────────────┐          ┌─────────┐ │
│  │  Agent A  │─────────▶│ Message Bus  │◀─────────│ Agent B │ │
│  └───────────┘          │  (Pub/Sub)   │          └─────────┘ │
│       │                 └──────┬───────┘                │      │
│       │                        │                        │      │
│       │                        ▼                        │      │
│       │                 ┌──────────────┐               │      │
│       │                 │  A2A         │               │      │
│       │                 │  Protocol    │               │      │
│       │                 │  (Parser)    │               │      │
│       │                 └──────┬───────┘               │      │
│       │                        │                        │      │
│       │                        ▼                        │      │
│       │                 ┌──────────────┐               │      │
│       └────────────────▶│  History     │◀──────────────┘      │
│                         │  Manager     │                       │
│                         │  (Database)  │                       │
│                         └──────────────┘                       │
│                                 │                               │
│                                 ▼                               │
│                         ┌──────────────┐                       │
│                         │  SSE Service │                       │
│                         │  (Frontend)  │                       │
│                         └──────────────┘                       │
└────────────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `message_bus.py`

**Purpose**: Central message routing hub for inter-agent communication

**Key Components**:
- `MessageBus`: Main message bus class
- `get_message_bus()`: Singleton accessor
- `reset_message_bus()`: Test utility

**Features**:
1. **Point-to-Point Messaging**: Send message to specific agent
2. **Broadcast Messaging**: Send to all agents
3. **Message Queuing**: In-memory deque per agent
4. **Pub/Sub Pattern**: Real-time subscriptions
5. **History Tracking**: All messages stored
6. **SSE Integration**: Broadcasts to frontend via Server-Sent Events

**Key Methods**:

#### `send_message()`
Location: `message_bus.py:60`

```python
await message_bus.send_message(
    sender_id=UUID("..."),
    recipient_id=UUID("..."),  # or None for broadcast
    content="Message content",
    message_type="task_assignment",
    metadata={"key": "value"},
    task_execution_id=UUID("...")
)
```

**Parameters**:
- `sender_id`: Sending agent UUID
- `recipient_id`: Receiving agent UUID (None = broadcast)
- `content`: Message content (string)
- `message_type`: Message type (see protocol.py)
- `metadata`: Optional metadata dict
- `task_execution_id`: Optional task context

**Returns**: `AgentMessageResponse` object

---

#### `broadcast_message()`
Location: `message_bus.py:135`

```python
await message_bus.broadcast_message(
    sender_id=pm_id,
    content="Daily standup starting",
    message_type="standup",
    task_execution_id=execution_id
)
```

Sends message to ALL agents.

---

#### `get_messages()`
Location: `message_bus.py:165`

```python
messages = await message_bus.get_messages(
    agent_id=agent_id,
    since=datetime.utcnow() - timedelta(hours=1),
    limit=50,
    message_type="question"
)
```

Retrieve messages for an agent with filtering.

---

#### `get_conversation()`
Location: `message_bus.py:201`

```python
conversation = await message_bus.get_conversation(
    task_execution_id=execution_id,
    limit=100
)
```

Get all messages for a task execution (chronologically ordered).

---

#### `subscribe()`
Location: `message_bus.py:231`

```python
async def on_message(message: AgentMessageResponse):
    print(f"Received: {message.content}")

subscription_id = await message_bus.subscribe(
    agent_id=agent_id,
    callback=on_message
)
```

Real-time subscription to messages.

---

**Data Structures**:

```python
# Message queues (per agent)
_queues: Dict[UUID, deque] = defaultdict(lambda: deque(maxlen=1000))

# Broadcast queue (all agents)
_broadcast_queue: deque = deque(maxlen=1000)

# Subscribers (real-time notifications)
_subscribers: Dict[UUID, List[Callable]] = defaultdict(list)

# All messages (history)
_all_messages: deque = deque(maxlen=10000)
```

**Business Rules**:
1. Messages are stored in-memory (can be upgraded to Redis)
2. Maximum 1000 messages per agent queue
3. Maximum 10000 total messages in history
4. Broadcasts are also added to individual agent queues
5. SSE notifications sent to frontend (non-blocking)
6. Lock ensures thread-safety (`asyncio.Lock`)

---

### 2. `protocol.py`

**Purpose**: A2A (Agent-to-Agent) protocol parser and validator

**Key Components**:
- `A2AProtocol`: Protocol handler class
- `MESSAGE_TYPE_MAP`: Mapping of action types to message classes
- Helper functions: `parse_message()`, `serialize_message()`, `validate_message()`

**Supported Message Types**:

Location: `protocol.py:27`

| Action Type | Class | Purpose |
|-------------|-------|---------|
| `task_assignment` | `TaskAssignment` | PM → Developer: Assign task |
| `status_request` | `StatusRequest` | PM → Agent: Request status |
| `status_update` | `StatusUpdate` | Agent → PM: Provide status |
| `question` | `Question` | Agent → Agent: Ask question |
| `answer` | `Answer` | Agent → Agent: Answer question |
| `human_intervention_required` | `HumanInterventionRequired` | PM → Human: Escalation |
| `code_review_request` | `CodeReviewRequest` | Dev → TL: Request review |
| `code_review_response` | `CodeReviewResponse` | TL → Dev: Review feedback |
| `task_completion` | `TaskCompletion` | Agent → PM: Task done |
| `standup` | `Standup` | PM → All: Standup request |

**Key Methods**:

#### `parse_message()`
Location: `protocol.py:53`

```python
# From JSON string
message = A2AProtocol.parse_message('{"action": "question", ...}')

# From dict
message = A2AProtocol.parse_message({"action": "question", ...})

# Returns typed object (Question, Answer, etc.)
```

**Validation**:
- Checks for required fields (`action`)
- Validates action type against `MESSAGE_TYPE_MAP`
- Uses Pydantic for schema validation
- Raises `ValueError` or `ValidationError` on failure

---

#### `serialize_message()`
Location: `protocol.py:101`

```python
message = TaskAssignment(...)
json_str = A2AProtocol.serialize_message(message)
# Returns formatted JSON string
```

---

#### `validate_message()`
Location: `protocol.py:127`

```python
is_valid = A2AProtocol.validate_message(raw_message)
# Returns True/False (no exceptions)
```

---

#### `extract_metadata()`
Location: `protocol.py:144`

```python
metadata = A2AProtocol.extract_metadata(message)
# Returns: {
#     "action": "task_assignment",
#     "message_class": "TaskAssignment",
#     "task_id": "...",
#     "recipient": "...",
#     "priority": "high"
# }
```

---

**Helper Factories**:

```python
# Create TaskAssignment
task_msg = A2AProtocol.create_task_assignment(
    recipient=agent_id,
    task_id="TASK-123",
    description="Implement feature",
    acceptance_criteria=["AC1", "AC2"],
    context="...",
    priority="high"
)

# Create StatusUpdate
status_msg = A2AProtocol.create_status_update(
    task_id="TASK-123",
    status="in_progress",
    progress_percentage=50,
    details="Completed backend, working on frontend",
    blockers=["Waiting for API spec"]
)

# Create Question
question_msg = A2AProtocol.create_question(
    task_id="TASK-123",
    question="How should we handle authentication?",
    context="Working on login feature",
    recipient=tech_lead_id,  # or None for broadcast
    urgency="high"
)

# Create HumanIntervention
escalation = A2AProtocol.create_human_intervention(
    task_id="TASK-123",
    reason="Cannot proceed without product decision",
    details="Need clarification on user flow",
    attempted_solutions=["Reviewed docs", "Asked team"],
    urgency="high"
)
```

---

### 3. `history_manager.py`

**Purpose**: Manages conversation history persistence and retrieval

**Key Components**:
- `HistoryManager`: Main history management class
- Database-backed message storage
- Conversation summarization
- Message filtering and retrieval

**Key Methods**:

#### `store_message()`
Location: `history_manager.py:32`

```python
stored_msg = await history_manager.store_message(
    task_execution_id=execution_id,
    sender_id=sender_id,
    recipient_id=recipient_id,
    content="Message content",
    message_type="question",
    metadata={"key": "value"}
)
```

Stores message in database (`agent_messages` table).

---

#### `get_conversation_history()`
Location: `history_manager.py:70`

```python
messages = await history_manager.get_conversation_history(
    task_execution_id=execution_id,
    limit=50,
    offset=0,
    since=datetime.utcnow() - timedelta(hours=24)
)
```

**Features**:
- Chronological order (oldest first)
- Pagination (limit/offset)
- Time-based filtering (since)
- Returns `List[AgentMessage]`

---

#### `get_agent_messages()`
Location: `history_manager.py:111`

```python
messages = await history_manager.get_agent_messages(
    agent_id=agent_id,
    task_execution_id=execution_id,  # optional
    limit=50,
    message_type="question"  # optional
)
```

Get messages to/from specific agent:
- Sent by agent
- Sent to agent
- Broadcast messages

---

#### `get_conversation_summary()`
Location: `history_manager.py:155`

```python
summary = await history_manager.get_conversation_summary(
    task_execution_id=execution_id,
    max_messages=100
)
```

Returns formatted text summary of conversation.

---

#### `summarize_conversation()`
Location: `history_manager.py:193`

```python
result = await history_manager.summarize_conversation(
    task_execution_id=execution_id,
    summarize_older_than_hours=24
)

# Returns:
# {
#     "summary": "Summary of 50 older messages...",
#     "recent_messages": [list of recent AgentMessage objects],
#     "old_message_count": 50,
#     "recent_message_count": 20,
#     "total_messages": 70
# }
```

**Use Case**: When conversation is too long for LLM context window.

**Strategy**:
- Keep recent messages in full
- Summarize older messages
- Cutoff time configurable (default 24 hours)

---

#### `to_conversation_messages()`
Location: `history_manager.py:343`

```python
conversation_messages = history_manager.to_conversation_messages(
    messages=agent_messages
)
# Converts AgentMessage → ConversationMessage for LLM
```

Converts database messages to LLM-compatible format.

---

#### `delete_old_messages()`
Location: `history_manager.py:317`

```python
deleted_count = await history_manager.delete_old_messages(
    older_than_days=30
)
```

Cleanup utility for old messages.

---

## Message Flow

### Example: Developer asks Tech Lead a question

```
┌─────────────────────────────────────────────────────────────┐
│                     Message Flow                             │
└─────────────────────────────────────────────────────────────┘

1. Developer creates Question message:
   ┌──────────────────────────────────┐
   │ A2AProtocol.create_question()    │
   └──────────────────────────────────┘
                  │
                  ▼
2. Send via Message Bus:
   ┌──────────────────────────────────┐
   │ message_bus.send_message()       │
   │ - Adds to TL's queue              │
   │ - Notifies TL subscribers         │
   │ - Broadcasts to SSE (frontend)    │
   │ - Stores in all_messages          │
   └──────────────────────────────────┘
                  │
                  ▼
3. Persist to Database:
   ┌──────────────────────────────────┐
   │ history_manager.store_message()  │
   │ - Saves to agent_messages table   │
   └──────────────────────────────────┘
                  │
                  ▼
4. Tech Lead retrieves:
   ┌──────────────────────────────────┐
   │ message_bus.get_messages(tl_id)  │
   │ - Returns Question object         │
   └──────────────────────────────────┘
                  │
                  ▼
5. Tech Lead responds:
   ┌──────────────────────────────────┐
   │ A2AProtocol.create_answer()      │
   │ message_bus.send_message()       │
   └──────────────────────────────────┘
                  │
                  ▼
6. Developer receives answer
```

---

## Integration with Other Modules

### Orchestration
The `TaskOrchestrator` uses message bus to:
- Delegate tasks to agents
- Monitor progress
- Collect status updates

### Collaboration
Collaboration patterns use message bus for:
- Problem solving (Q&A)
- Code review cycles
- Standup coordination

### Frontend (SSE)
Message bus broadcasts to SSE service:
- Real-time updates to user
- Task execution progress
- Agent conversations

---

## Business Rules

### Message Bus Rules
1. **In-Memory Storage**: Messages stored in memory (production: use Redis)
2. **Message Limits**: 1000 messages per agent, 10000 total
3. **Broadcast Behavior**: Broadcasts added to ALL agent queues
4. **Thread Safety**: All operations protected by async lock
5. **SSE Integration**: Non-blocking (failures don't break messaging)

### Protocol Rules
1. **Required Fields**: All messages must have `action` field
2. **Validation**: Pydantic validates all message schemas
3. **Unknown Actions**: Rejected with clear error message
4. **Type Safety**: Protocol ensures type-safe message handling

### History Rules
1. **Persistence**: All messages persisted to PostgreSQL
2. **Pagination**: Use limit/offset for large conversations
3. **Cleanup**: Old messages can be deleted (default: 30 days)
4. **Summarization**: Long conversations summarized to fit context window
5. **Filtering**: Filter by time, agent, message type

---

## Performance Considerations

### Message Bus
- **In-Memory Speed**: Fast (microseconds per operation)
- **Memory Usage**: ~1KB per message × 10000 = ~10MB
- **Scalability Limit**: Single server (use Redis for multi-server)
- **Lock Contention**: Async lock may bottleneck under high load

### History Manager
- **Database Queries**: Indexed by `task_execution_id`, `sender_id`, `recipient_id`
- **Large Conversations**: Use pagination (limit/offset)
- **Summarization**: Currently simple (upgrade to LLM for production)

### Protocol
- **Parsing**: Fast (Pydantic BaseModel)
- **Validation**: Automatic schema validation
- **Serialization**: JSON (efficient)

---

## Production Upgrades

### Recommended for Scale

1. **Redis Message Bus**:
   - Replace in-memory deques with Redis streams
   - Enable multi-server deployment
   - Persist messages across restarts
   - Pub/Sub for real-time subscriptions

2. **Message Queue (RabbitMQ/Kafka)**:
   - Guaranteed delivery
   - Message routing
   - Dead-letter queues for failed messages
   - Message replay capability

3. **LLM Summarization**:
   - Replace `_create_simple_summary()` with LLM call
   - Better conversation understanding
   - Context compression for long conversations

4. **Caching Layer**:
   - Cache recent conversations (Redis)
   - Reduce database queries
   - Faster message retrieval

---

## Testing

### Testing Message Bus

```python
import pytest
from backend.agents.communication.message_bus import MessageBus, reset_message_bus
from uuid import uuid4

@pytest.fixture
def message_bus():
    reset_message_bus()  # Clear singleton
    return MessageBus()

@pytest.mark.asyncio
async def test_send_message(message_bus):
    sender = uuid4()
    recipient = uuid4()

    msg = await message_bus.send_message(
        sender_id=sender,
        recipient_id=recipient,
        content="Test message",
        message_type="question",
        task_execution_id=uuid4()
    )

    assert msg.content == "Test message"

    # Verify recipient received it
    messages = await message_bus.get_messages(recipient)
    assert len(messages) == 1
    assert messages[0].content == "Test message"

@pytest.mark.asyncio
async def test_broadcast(message_bus):
    sender = uuid4()
    agents = [uuid4() for _ in range(3)]

    await message_bus.broadcast_message(
        sender_id=sender,
        content="Broadcast",
        message_type="standup",
        task_execution_id=uuid4()
    )

    # All agents should receive it
    for agent in agents:
        messages = await message_bus.get_messages(agent)
        assert len(messages) == 1
```

### Testing Protocol

```python
import pytest
from backend.agents.communication.protocol import A2AProtocol, parse_message

def test_parse_task_assignment():
    raw = {
        "action": "task_assignment",
        "recipient": str(uuid4()),
        "task_id": "TASK-1",
        "description": "Test",
        "acceptance_criteria": ["AC1"],
        "context": "Test context",
        "dependencies": [],
        "priority": "high"
    }

    msg = parse_message(raw)
    assert isinstance(msg, TaskAssignment)
    assert msg.task_id == "TASK-1"
    assert msg.priority == "high"

def test_invalid_message():
    with pytest.raises(ValueError):
        parse_message({"invalid": "message"})
```

---

## Common Patterns

### Pattern: Ask Team for Help

```python
# Developer asks broadcast question
question_msg = A2AProtocol.create_question(
    task_id=task_id,
    question="How should we implement caching?",
    context="Working on API performance",
    recipient=None,  # Broadcast
    urgency="normal"
)

await message_bus.broadcast_message(
    sender_id=developer_id,
    content=serialize_message(question_msg),
    message_type="question",
    task_execution_id=execution_id
)

# Wait for answers (async)
await asyncio.sleep(60)  # 1 minute

# Collect answers
messages = await message_bus.get_messages(
    developer_id,
    message_type="answer"
)
```

### Pattern: PM Delegates Task

```python
# PM creates task assignment
task_msg = A2AProtocol.create_task_assignment(
    recipient=backend_dev_id,
    task_id="TASK-123",
    description="Implement user login",
    acceptance_criteria=[
        "User can log in with email/password",
        "JWT token generated",
        "Tests pass"
    ],
    context=rag_context,
    priority="high",
    estimated_hours=8
)

# Send via message bus
await message_bus.send_message(
    sender_id=pm_id,
    recipient_id=backend_dev_id,
    content=serialize_message(task_msg),
    message_type="task_assignment",
    task_execution_id=execution_id
)

# Store in history
await history_manager.store_message(
    task_execution_id=execution_id,
    sender_id=pm_id,
    recipient_id=backend_dev_id,
    content=serialize_message(task_msg),
    message_type="task_assignment"
)
```

---

## Troubleshooting

**Q: Messages not being received?**
- Check agent is subscribed or polling `get_messages()`
- Verify recipient_id is correct
- Check message bus stats: `message_bus.get_stats()`

**Q: Message parsing fails?**
- Validate message format with `validate_message()`
- Check `action` field matches `MESSAGE_TYPE_MAP`
- Review Pydantic validation errors

**Q: Conversation history missing?**
- Verify `history_manager.store_message()` was called
- Check database for `agent_messages` table
- Review task_execution_id filter

**Q: High memory usage?**
- Reduce `max_history_per_agent` (default: 1000)
- Implement cleanup job for old messages
- Upgrade to Redis for production

---

## Related Documentation

- See `../CLAUDE.md` for agent architecture
- See `../orchestration/CLAUDE.md` for workflow coordination
- See `../collaboration/CLAUDE.md` for collaboration patterns
- See `/backend/schemas/agent_message.py` for message schemas
- See `/backend/services/sse_service.py` for SSE integration
