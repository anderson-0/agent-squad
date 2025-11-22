# Phase 05 - SSE Real-Time Updates

**Date:** 2025-11-21
**Priority:** P1 (Important)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:**
  - [Phase 02 - E2B Sandbox Service](./phase-02-e2b-sandbox-service.md)
  - [Phase 03 - Git Operations Service](./phase-03-git-operations-service.md)
  - [Phase 04 - GitHub Integration](./phase-04-github-integration.md)
- **Related Docs:** [Scout Report](./scout/scout-01-architecture.md) - SSE_URL configured

## Overview

Implement Server-Sent Events (SSE) for real-time updates from backend to frontend. Stream sandbox status, git operation progress, command outputs, PR creation notifications to Agent Work page.

**Why SSE over WebSockets:**
- Simpler protocol (HTTP-based)
- Auto-reconnection in EventSource API
- One-way communication sufficient (server → client)
- Lower overhead for status updates
- Built-in browser support

## Key Insights

From scout report:
- Frontend expects SSE at `http://localhost:8000/api/v1/sse`
- Agent Work page ready for live logs
- No SSE client implementation exists yet
- Frontend uses EventSource API pattern

## Requirements

### Functional
- SSE endpoint at `/api/v1/sse`
- Event types: sandbox_status, git_operation, command_output, pr_created
- Per-agent event filtering
- Reconnection handling
- Event history replay (last 10 events per agent)
- Graceful disconnection

### Non-Functional
- Event delivery <500ms
- Support 100+ concurrent connections
- Automatic reconnection on disconnect
- Event ordering guarantee per agent
- Memory-efficient event buffering

## Architecture

### SSE Event Flow

```
Backend Service → Event Manager → SSE Endpoint → Frontend EventSource
     ↓                 ↓              ↓                ↓
(emit events)    (buffer/route)  (stream SSE)   (update UI)
```

### Event Types

```python
# Sandbox status
{
  "event": "sandbox_status",
  "data": {
    "sandbox_id": "...",
    "agent_id": "...",
    "status": "creating|running|stopped|error",
    "timestamp": "2025-11-21T16:30:00Z"
  }
}

# Git operation progress
{
  "event": "git_operation",
  "data": {
    "sandbox_id": "...",
    "operation": "clone|branch|commit|push",
    "status": "started|in_progress|completed|failed",
    "message": "Cloning repository...",
    "progress": 45,  # percentage
    "timestamp": "..."
  }
}

# Command output (live terminal)
{
  "event": "command_output",
  "data": {
    "sandbox_id": "...",
    "output": "npm install completed\n",
    "stream": "stdout|stderr",
    "timestamp": "..."
  }
}

# PR created
{
  "event": "pr_created",
  "data": {
    "task_id": "...",
    "pr_url": "https://github.com/...",
    "pr_number": 123,
    "timestamp": "..."
  }
}
```

## Related Code Files

### New Files to Create
- `backend/app/api/v1/sse.py` - SSE endpoint
- `backend/app/services/event_manager.py` - Event broadcasting service
- `backend/app/utils/sse.py` - SSE formatting helpers
- `backend/tests/test_sse.py`

### Files to Modify
- `backend/app/api/v1/router.py` - Mount SSE endpoint
- `backend/app/services/e2b_service.py` - Emit sandbox events
- `backend/app/services/git_service.py` - Emit git operation events
- `backend/app/services/github_service.py` - Emit PR creation events

## Implementation Steps

1. **Create Event Manager Service**
   - In-memory event buffer (collections.deque, max 100 events per agent)
   - Subscribe/unsubscribe methods for SSE connections
   - Broadcast method to send events to all subscribers
   - Filter events by agent_id
   - Thread-safe implementation (asyncio.Queue)

2. **Create SSE Utilities**
   - format_sse_message function (RFC 8895 format)
   - Event data serialization (JSON)
   - Heartbeat/keep-alive comments every 30 seconds

3. **Implement SSE Endpoint**
   - GET /api/v1/sse?agent_id={id}
   - Set headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`
   - Stream events to client with async generator
   - Handle client disconnections gracefully
   - Implement reconnection with Last-Event-ID

4. **Integrate with E2B Service**
   - Emit "sandbox_status" on create/destroy
   - Emit "command_output" for execute_command results
   - Include sandbox_id and agent_id in events

5. **Integrate with Git Service**
   - Emit "git_operation" events:
     - clone started/completed
     - branch created
     - commit created
     - push started/completed
   - Include progress percentages where applicable

6. **Integrate with GitHub Service**
   - Emit "pr_created" on successful PR creation
   - Include PR URL, number, task_id

7. **Event History Replay**
   - Store last 10 events per agent in memory
   - On new SSE connection, send history first
   - Then stream live events

8. **Heartbeat Implementation**
   - Send `:heartbeat\n\n` every 30 seconds
   - Prevent connection timeout
   - Client detects disconnect if no heartbeat in 60 seconds

9. **Error Handling**
   - Catch serialization errors (invalid JSON)
   - Handle client disconnects (asyncio.CancelledError)
   - Log SSE errors without crashing stream

10. **Testing**
    - Unit test event formatting
    - Integration test SSE endpoint with httpx
    - Test event filtering by agent_id
    - Test reconnection with Last-Event-ID

## Todo List

### P0 - Critical

- [ ] Create app/services/event_manager.py with EventManager singleton
- [ ] Implement event buffer (deque, max 100 per agent)
- [ ] Implement subscribe/unsubscribe for SSE connections
- [ ] Implement broadcast method (filter by agent_id)
- [ ] Create app/utils/sse.py with format_sse_message helper
- [ ] Create GET /api/v1/sse endpoint with agent_id filter
- [ ] Set SSE headers (text/event-stream, no-cache)
- [ ] Implement async generator for event streaming
- [ ] Emit sandbox_status events from E2BSandboxService
- [ ] Emit git_operation events from GitService
- [ ] Emit pr_created events from GitHubService
- [ ] Test SSE endpoint with curl or httpx
- [ ] Verify events received in correct order

### P1 - Important

- [ ] Implement event history replay (last 10 events)
- [ ] Add heartbeat comments every 30 seconds
- [ ] Handle client disconnections gracefully
- [ ] Implement Last-Event-ID reconnection logic
- [ ] Add event timestamp to all events
- [ ] Create unit tests for event formatting
- [ ] Create integration tests for SSE streaming
- [ ] Document SSE event types in README

### P2 - Nice to Have

- [ ] Add event persistence (Redis for multi-instance deployments)
- [ ] Implement event compression for large payloads
- [ ] Add SSE metrics (active connections, events sent)
- [ ] Support custom event filters (not just agent_id)
- [ ] Add event replay from specific timestamp
- [ ] Implement event batching for high-volume scenarios

## Success Criteria

- [ ] SSE endpoint streams events in SSE format
- [ ] Sandbox status updates appear in real-time
- [ ] Git operation progress visible in frontend
- [ ] PR creation notifications delivered instantly
- [ ] Heartbeats prevent connection timeouts
- [ ] Multiple clients receive events simultaneously
- [ ] Events filtered correctly by agent_id
- [ ] Reconnection works after network interruption

## Risk Assessment

**High Risks:**
- Memory leaks from unbounded event buffers
- Connection leaks (clients not cleaned up)
- Network interruptions breaking streams

**Medium Risks:**
- Event ordering issues under high load
- Serialization errors breaking streams
- Heartbeat timing drift

**Mitigation:**
- Limit event buffer size (100 events per agent)
- Use weak references for connections, auto-cleanup
- Implement reconnection logic with exponential backoff
- Use asyncio.Queue for thread-safe event ordering
- Catch serialization errors, skip malformed events
- Use precise async sleep for heartbeats

## Security Considerations

- **Authentication:** Verify JWT token in SSE endpoint (query param or cookie)
- **Authorization:** Only send events for agents user has access to
- **Data Sanitization:** Remove sensitive data (tokens) from events
- **Rate Limiting:** Limit SSE connections per user (max 10)
- **Event Validation:** Validate event data before broadcasting
- **XSS Prevention:** Escape HTML in event messages

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 30 min | Boilerplate SSE code, event integration |
| Senior Dev | 4-5 hrs | SSE patterns, async generators |
| Junior Dev | 10-12 hrs | SSE protocol, async Python, testing |

**Complexity:** Medium (async patterns, state management)

## Next Steps

After completion:
- [Phase 06 - Frontend Integration](./phase-06-frontend-integration.md) - Connect EventSource client
- [Phase 07 - UI Enhancements](./phase-07-ui-enhancements.md) - Display live logs

## Unresolved Questions

1. **Event Persistence:** Use Redis for multi-instance deployments or in-memory only?
2. **Authentication:** JWT in query params, headers, or cookies for SSE?
3. **Event Retention:** How long to keep event history? (Currently 10 events)
4. **Heartbeat Interval:** 30 seconds sufficient or adjust based on proxy timeouts?
5. **Event Compression:** Implement gzip for large events (command outputs)?
6. **Multi-Agent Filtering:** Support multiple agent_ids in single SSE connection?
7. **Error Events:** Should errors be separate event type or included in operation events?
