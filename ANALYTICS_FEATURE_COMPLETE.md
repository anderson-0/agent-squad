# Squad Analytics Feature - Complete ✅

## Overview

The Squad Analytics feature has been successfully implemented and tested. This feature provides comprehensive tracking and reporting of squad member activities, token usage, and communication patterns.

## What Was Requested

**User Request:**
> "I would like that for every member of each squad we keep track of how many input and output tokens the members consumed individually, how many messages they sent in total to the team and how many messages were exchange with each other member of the squad and to be able to filter conversations between team members"

## What Was Delivered

### 1. Database Schema (`squad_member_stats` table)

**Location:** `backend/alembic/versions/003_add_squad_member_stats.py`

**Schema:**
```sql
CREATE TABLE squad_member_stats (
    id UUID PRIMARY KEY,
    squad_member_id UUID UNIQUE NOT NULL,  -- FK to squad_members

    -- Token Usage Tracking
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,

    -- Message Tracking
    total_messages_sent INTEGER DEFAULT 0,
    total_messages_received INTEGER DEFAULT 0,

    -- Activity Timestamps
    last_message_sent_at TIMESTAMP NULL,
    last_message_received_at TIMESTAMP NULL,
    last_llm_call_at TIMESTAMP NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (squad_member_id) REFERENCES squad_members(id) ON DELETE CASCADE
);

CREATE INDEX ix_squad_member_stats_squad_member_id ON squad_member_stats(squad_member_id);
CREATE INDEX ix_squad_member_stats_total_tokens ON squad_member_stats(total_tokens);
CREATE INDEX ix_squad_member_stats_updated_at ON squad_member_stats(updated_at);
```

### 2. Service Layer

**Location:** `backend/services/squad_analytics_service.py`

**Key Methods:**

#### Tracking Methods (Call these in your agent code)
- `update_token_usage(db, squad_member_id, input_tokens, output_tokens)` - Track LLM token consumption
- `update_message_sent(db, squad_member_id)` - Increment message sent counter
- `update_message_received(db, squad_member_id)` - Increment message received counter

#### Retrieval Methods
- `get_member_stats(db, squad_member_id)` - Get comprehensive stats for one member
- `get_squad_stats(db, squad_id)` - Get aggregated stats for entire squad
- `get_communication_matrix(db, squad_id, since=None)` - Who talks to whom (pairwise counts)
- `get_conversations_between_members(db, member_a_id, member_b_id, limit, offset, since, until)` - Filter messages between two members

### 3. REST API Endpoints

**Location:** `backend/api/v1/endpoints/analytics.py`

**Available Endpoints:**

#### GET Endpoints (Retrieval)

**Get Squad Statistics:**
```
GET /analytics/squads/{squad_id}/stats
```
Returns:
- Total members in squad
- Aggregated token usage (all members)
- Total messages sent
- Per-member breakdown

**Get Member Statistics:**
```
GET /analytics/squad-members/{member_id}/stats
```
Returns:
- Role and specialization
- Token usage (input/output/total)
- Message counts (sent/received/total)
- Last activity timestamps

**Get Communication Matrix:**
```
GET /analytics/squads/{squad_id}/communication-matrix?since_days=7
```
Returns:
- List of squad members
- Matrix showing message counts between all pairs
- Supports time filtering with `since_days` parameter

Example response:
```json
{
  "squad_id": "...",
  "members": [...],
  "communication_matrix": {
    "member_a_id": {
      "member_b_id": 15,    // 15 messages from A to B
      "member_c_id": 3,     // 3 messages from A to C
      "broadcast": 2        // 2 broadcast messages from A
    },
    "member_b_id": {
      "member_a_id": 8,     // 8 messages from B to A
      "member_c_id": 12
    }
  }
}
```

**Get Conversations Between Members:**
```
GET /analytics/conversations/between?member_a_id=UUID&member_b_id=UUID&limit=100&offset=0&since_days=7
```
Returns:
- Total message count (bidirectional)
- Paginated list of messages
- Message details (content, type, timestamps, metadata)

#### POST Endpoints (Tracking)

**Update Token Usage:**
```
POST /analytics/squad-members/{member_id}/stats/tokens?input_tokens=1000&output_tokens=500
```

**Record Message Sent:**
```
POST /analytics/squad-members/{member_id}/stats/message-sent
```

**Record Message Received:**
```
POST /analytics/squad-members/{member_id}/stats/message-received
```

## How to Use

### 1. Track Token Usage (After LLM Calls)

```python
from backend.services.squad_analytics_service import SquadAnalyticsService

# After calling LLM
response = await agent.process_message(message)

# Track token usage
await SquadAnalyticsService.update_token_usage(
    db=db,
    squad_member_id=agent_member_id,
    input_tokens=response.metadata["input_tokens"],
    output_tokens=response.metadata["output_tokens"]
)
```

### 2. Track Message Activity

```python
# When member sends a message
await SquadAnalyticsService.update_message_sent(db, sender_id)

# When member receives a message
await SquadAnalyticsService.update_message_received(db, recipient_id)
```

### 3. Get Analytics

```python
# Get stats for one member
member_stats = await SquadAnalyticsService.get_member_stats(db, member_id)
print(f"Total tokens: {member_stats['token_usage']['total_tokens']}")
print(f"Messages sent: {member_stats['message_counts']['total_sent']}")

# Get squad-wide stats
squad_stats = await SquadAnalyticsService.get_squad_stats(db, squad_id)
print(f"Squad total tokens: {squad_stats['aggregate_stats']['total_tokens']}")

# Get communication matrix
matrix = await SquadAnalyticsService.get_communication_matrix(db, squad_id)
for sender_id, recipients in matrix["communication_matrix"].items():
    for recipient_id, count in recipients.items():
        print(f"{sender_id} → {recipient_id}: {count} messages")

# Get conversation between two members
conversations = await SquadAnalyticsService.get_conversations_between_members(
    db=db,
    member_a_id=member_a_id,
    member_b_id=member_b_id,
    limit=100,
    offset=0,
    since_days=7
)
print(f"Total messages: {conversations['total_messages']}")
for msg in conversations["messages"]:
    print(f"{msg['sender_id']}: {msg['content']}")
```

## Testing

**Test File:** `test_analytics_e2e.py`

**Tests Performed:**
1. ✅ Token usage tracking and accumulation
2. ✅ Message sent/received counting
3. ✅ Individual member statistics retrieval
4. ✅ Squad-level aggregated statistics
5. ✅ Communication matrix generation (pairwise counts)
6. ✅ Bidirectional conversation filtering
7. ✅ Time-based filtering (since parameter)

**Test Results:** All tests passing ✅

## Database Migration

**Migration Status:** ✅ Applied

**Migration ID:** `003`

**Command Used:**
```bash
cd backend && PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad .venv/bin/alembic upgrade head
```

**Migration Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 8ac963704cb9 -> 003, add squad_member_stats table
```

## Files Created/Modified

### New Files Created:
1. `backend/models/squad_member_stats.py` - SQLAlchemy model
2. `backend/services/squad_analytics_service.py` - Business logic service
3. `backend/api/v1/endpoints/analytics.py` - REST API endpoints
4. `backend/alembic/versions/003_add_squad_member_stats.py` - Database migration
5. `test_analytics_e2e.py` - End-to-end test suite

### Files Modified:
1. `backend/models/__init__.py` - Added SquadMemberStats export
2. `backend/api/v1/router.py` - Registered analytics router

## Architecture Decisions

### Why Aggregated Stats Instead of Per-Message?

**Decision:** Store aggregated counters in `squad_member_stats` table instead of calculating from individual messages.

**Rationale:**
- **Performance:** Aggregating millions of messages on-the-fly would be slow
- **Scalability:** Counters are O(1) updates, queries are O(1) lookups
- **Cost:** Reduced database query load

**Trade-off:** Slightly more complex tracking logic (must call update methods)

### Why Separate Communication Matrix Query?

**Decision:** Provide dedicated endpoint for communication matrix instead of including in squad stats.

**Rationale:**
- **Optional Data:** Not always needed, so don't compute it unnecessarily
- **Performance:** Matrix calculation requires JOIN across messages table
- **Flexibility:** Allows time-based filtering independent of stats

## Future Enhancements

Potential additions (not implemented):

1. **Cost Tracking**: Calculate $ cost based on token usage and model pricing
2. **Historical Trends**: Track stats over time (daily/weekly snapshots)
3. **Performance Metrics**: Average response time, success rates
4. **Alerting**: Notify when token usage exceeds threshold
5. **Comparative Analytics**: Compare members or squads
6. **Export**: CSV/JSON export of analytics data
7. **Dashboard**: Frontend visualization of analytics

## Integration with Existing System

The analytics feature integrates seamlessly with the existing agent-squad architecture:

1. **Non-Intrusive**: Doesn't modify existing models or workflows
2. **Opt-In Tracking**: Only tracks when you explicitly call update methods
3. **Backward Compatible**: Existing code continues to work without changes
4. **Independent Queries**: Analytics queries don't affect operational queries

## Performance Considerations

1. **Indexes Created:**
   - `squad_member_id` - Fast lookups by member
   - `total_tokens` - Fast sorting/filtering by token usage
   - `updated_at` - Fast time-based queries

2. **Query Patterns:**
   - Member stats: Single SELECT by primary key (O(1))
   - Squad stats: One SELECT per member + aggregation (O(n) where n = members)
   - Communication matrix: Single GROUP BY query (efficient with indexes)
   - Conversations: SELECT with WHERE + ORDER BY + LIMIT (efficient with indexes)

3. **Write Performance:**
   - All updates are single-row UPDATEs (O(1))
   - Minimal transaction overhead

## Summary

✅ **Feature Complete**

The Squad Analytics feature is fully implemented, tested, and ready for production use. All requested functionality has been delivered:

- ✅ Track input/output tokens per member
- ✅ Track total messages sent per member
- ✅ Track messages exchanged between members (communication matrix)
- ✅ Filter conversations between specific members
- ✅ Time-based filtering
- ✅ REST API endpoints
- ✅ Comprehensive test coverage

**Next Step:** Phase 4 - Multi-Turn Conversations

---

**Completion Date:** October 23, 2025
**Migration ID:** 003
**Test Status:** All passing ✅
