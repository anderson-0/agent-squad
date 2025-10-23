# Message Bus Database Persistence - Implementation Summary

## Overview

Updated the `message_bus.py` to automatically persist messages to the database when a database session is provided, ensuring all agent-to-agent communications are stored for historical retrieval and SSE streaming.

## Changes Made

### 1. Updated `backend/agents/communication/message_bus.py`

**Added import:**
```python
from uuid import UUID, uuid4
from backend.models.agent_message import AgentMessage
```

**Updated `send_message()` method:**
- Changed message ID generation from `UUID(int=len(self._all_messages))` to `uuid4()` for unique IDs
- Added automatic database persistence when `db` session is provided:
  - Creates `AgentMessage` database object
  - Inserts into database with `db.add()` and `db.flush()`
  - Updates response message with database timestamp
  - Includes error handling to prevent message sending failures

**Key changes (lines 91-126):**
```python
async with self._lock:
    # Generate unique message ID
    message_id = uuid4()

    # Create message
    message = AgentMessageResponse(
        id=message_id,
        task_execution_id=task_execution_id or UUID(int=0),
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        message_type=message_type,
        message_metadata=metadata or {},
        created_at=datetime.utcnow()
    )

    # Persist to database if db session provided
    if db is not None and task_execution_id is not None:
        try:
            db_message = AgentMessage(
                id=message_id,
                task_execution_id=task_execution_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                message_metadata=metadata or {}
            )
            db.add(db_message)
            await db.flush()
            # Update message with database timestamp
            message.created_at = db_message.created_at
        except Exception as e:
            # Log error but don't fail message sending
            print(f"Error persisting message to database: {e}")

    # ... rest of the method continues unchanged
```

### 2. Updated `create_squad_now.py`

**Added `db.commit()` calls after each message:**
- Ensures each message is committed to the database immediately
- Prevents message loss if script fails partway through
- Added after all 7 message sends

**Example change:**
```python
await bus.send_message(
    sender_id=pm.id,
    recipient_id=None,
    content="Good morning team! Today we're building user authentication.",
    message_type="standup",
    task_execution_id=execution.id,
    db=db
)
await db.commit()  # NEW: Commit immediately after sending
await asyncio.sleep(0.5)  # Reduced from 1 second
```

## Benefits

1. **Automatic Persistence**: No need to manually call database insert operations
2. **Historical Record**: All messages stored in `agent_messages` table
3. **SSE Streaming**: Database messages can be queried and streamed to frontend
4. **Error Resilience**: Database errors don't break message bus functionality
5. **Backward Compatible**: Works with or without database session
6. **Unique IDs**: Proper UUID generation ensures no ID collisions

## Testing

Created comprehensive test that verified:
- ✅ Messages successfully inserted into database
- ✅ Correct sender/recipient IDs stored
- ✅ Message content and type preserved
- ✅ Timestamps generated correctly
- ✅ All 3 test messages retrieved from database

**Test Results:**
```
================================================================================
                ✅ TEST PASSED: Messages Persisted Successfully!
================================================================================

Execution ID: 1ad3f75f-78f8-49f5-be77-ca2e8b4f13a6
Messages Stored: 3

[1] Project Manager → All Agents
    Type: STANDUP
    Content: Testing message bus with database persistence!
    Time: 13:41:28

[2] Project Manager → Backend Developer
    Type: TASK_ASSIGNMENT
    Content: Please implement the feature.
    Time: 13:41:29

[3] Backend Developer → Project Manager
    Type: ACKNOWLEDGMENT
    Content: Got it! Starting now.
    Time: 13:41:29
```

## Usage

### Before (manual persistence):
```python
# Send message
await bus.send_message(
    sender_id=agent_a,
    recipient_id=agent_b,
    content="Hello!",
    message_type="question",
    task_execution_id=execution_id,
    db=db
)

# MANUALLY persist to database
db_message = AgentMessage(...)
db.add(db_message)
await db.commit()
```

### After (automatic persistence):
```python
# Send message - automatically persisted!
await bus.send_message(
    sender_id=agent_a,
    recipient_id=agent_b,
    content="Hello!",
    message_type="question",
    task_execution_id=execution_id,
    db=db
)
await db.commit()  # Just commit the transaction
```

## Requirements

To persist messages to database, both parameters must be provided:
1. `db`: AsyncSession database session
2. `task_execution_id`: Valid task execution UUID

If either is missing, messages are only stored in-memory (message bus queue) but not persisted.

## Database Schema

Messages are stored in the `agent_messages` table:
```sql
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY,
    task_execution_id UUID NOT NULL REFERENCES task_executions(id),
    sender_id UUID NOT NULL REFERENCES squad_members(id),
    recipient_id UUID REFERENCES squad_members(id),  -- NULL for broadcasts
    content TEXT NOT NULL,
    message_type VARCHAR NOT NULL,
    message_metadata JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Future Enhancements

Potential improvements for production:
1. Batch inserts for high-volume messaging
2. Message compression for large content
3. TTL/archival for old messages
4. Read replicas for query performance
5. Message indexing for faster searches

## Related Files

- `backend/agents/communication/message_bus.py` - Updated message bus
- `backend/models/agent_message.py` - Database model
- `create_squad_now.py` - Demo script using updated bus
- `backend/cli/stream_agent_messages.py` - SSE streaming client

## Documentation

See `/backend/agents/communication/CLAUDE.md` for complete message bus documentation.
