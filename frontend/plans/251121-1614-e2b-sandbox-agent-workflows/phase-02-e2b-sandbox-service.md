# Phase 02 - E2B Sandbox Service

**Date:** 2025-11-21
**Priority:** P0 (Critical)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** [Phase 01 - Backend Foundation](./phase-01-backend-foundation.md)
- **Related Research:** [E2B Integration](./research/researcher-01-e2b-integration.md)

## Overview

Integrate E2B SDK for sandbox lifecycle management. Create, execute commands, manage state, handle cleanup. Each agent gets isolated Firecracker microVM for secure code execution.

**Key Features:**
- Sub-200ms sandbox provisioning
- Full isolation (Firecracker microVMs)
- Execute terminal commands
- File system operations
- Up to 24hr sessions (Pro tier)

## Key Insights

From research:
- E2B startup: ~150-200ms (no cold starts)
- LLM-agnostic, works with any framework
- Python SDK: `pip install e2b-code-interpreter`
- Authentication via API key in env vars
- Pause/resume for state persistence (optional)
- Pricing unclear - test free tier first

## Requirements

### Functional
- Create sandbox for agent when task assigned
- Execute shell commands in sandbox
- Upload/download files to/from sandbox
- Monitor sandbox status (running, error, stopped)
- Destroy sandbox on task completion
- Handle sandbox crashes with cleanup
- Store sandbox metadata in database

### Non-Functional
- Sandbox creation <5 seconds
- Command execution timeout: 5 minutes
- Concurrent sandboxes: Up to tier limit
- Automatic cleanup on errors
- Retry logic for transient failures

## Architecture

### E2B Sandbox Lifecycle

```
Task Assigned → Create Sandbox → Initialize Env → Execute Commands → Destroy
                      ↓               ↓                ↓              ↓
                  Store ID        Install deps     Run git ops   Update DB
                  in DB           (Node, Git)      (Phase 03)    (cleanup)
```

### Service Structure

```python
# app/services/e2b_service.py
class E2BSandboxService:
    async def create_sandbox(agent_id, task_id) -> Sandbox
    async def execute_command(sandbox_id, command) -> ExecutionResult
    async def upload_file(sandbox_id, local_path, remote_path)
    async def download_file(sandbox_id, remote_path, local_path)
    async def get_status(sandbox_id) -> SandboxStatus
    async def destroy_sandbox(sandbox_id)
    async def cleanup_stale_sandboxes()  # Cron job
```

### Error Recovery

```python
# Retry logic for transient failures
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def create_sandbox_with_retry(agent_id, task_id):
    # Sandbox creation logic
```

## Related Code Files

### New Files to Create
- `backend/app/services/e2b_service.py` - Main E2B service
- `backend/app/services/__init__.py`
- `backend/app/api/v1/sandboxes.py` - Sandbox API endpoints
- `backend/tests/test_e2b_service.py`

### Files to Modify
- `backend/requirements.txt` - Add `e2b-code-interpreter`, `tenacity`
- `backend/app/config.py` - Add E2B_API_KEY env var
- `backend/app/api/v1/router.py` - Mount sandboxes router
- `backend/app/models/sandbox.py` - Add status fields if needed

## Implementation Steps

1. **Install E2B SDK**
   - Add to requirements.txt: `e2b-code-interpreter>=0.1.0`
   - Add retry library: `tenacity>=8.2.0`
   - Run `pip install -r requirements.txt`

2. **Update Configuration**
   - Add E2B_API_KEY to config.py settings
   - Add E2B_TIMEOUT config (default 300 seconds)
   - Add .env.example entry for E2B_API_KEY

3. **Create E2B Service Class**
   - Import E2B SDK: `from e2b_code_interpreter import Sandbox`
   - Implement create_sandbox with error handling
   - Store sandbox ID in database via SQLAlchemy
   - Return Sandbox model with status

4. **Implement Command Execution**
   - Create execute_command method
   - Handle stdout, stderr, exit codes
   - Store execution logs in git_operations table
   - Set timeout (5 min default)

5. **File Operations**
   - Implement upload_file for transferring scripts
   - Implement download_file for retrieving artifacts
   - Handle file not found errors

6. **Status Monitoring**
   - Create get_status method
   - Query E2B API for sandbox health
   - Update database sandbox status
   - Return structured SandboxStatus object

7. **Cleanup Logic**
   - Implement destroy_sandbox with DB update
   - Set destroyed_at timestamp
   - Handle already-destroyed cases gracefully
   - Create cleanup_stale_sandboxes for cron (sandboxes >24hrs old)

8. **API Endpoints**
   - POST /api/v1/sandboxes - Create sandbox
   - GET /api/v1/sandboxes/{id} - Get sandbox status
   - POST /api/v1/sandboxes/{id}/execute - Execute command
   - DELETE /api/v1/sandboxes/{id} - Destroy sandbox

9. **Error Handling**
   - Catch E2B exceptions (QuotaExceeded, Timeout, etc.)
   - Return structured error responses
   - Log errors with context (agent_id, task_id)
   - Implement exponential backoff retry

10. **Unit Tests**
    - Mock E2B SDK in tests
    - Test sandbox creation success/failure
    - Test command execution with various outputs
    - Test cleanup logic
    - Test retry mechanism

## Todo List

### P0 - Critical

- [ ] Add e2b-code-interpreter to requirements.txt
- [ ] Add E2B_API_KEY to config.py and .env.example
- [ ] Create app/services/e2b_service.py with E2BSandboxService class
- [ ] Implement create_sandbox method with DB persistence
- [ ] Implement execute_command with timeout and logging
- [ ] Implement destroy_sandbox with DB update
- [ ] Create POST /api/v1/sandboxes endpoint (create)
- [ ] Create GET /api/v1/sandboxes/{id} endpoint (status)
- [ ] Create POST /api/v1/sandboxes/{id}/execute endpoint
- [ ] Create DELETE /api/v1/sandboxes/{id} endpoint
- [ ] Add error handling for E2B quota exceeded
- [ ] Add error handling for sandbox timeouts
- [ ] Test sandbox creation with real E2B API key
- [ ] Verify sandbox destruction and DB cleanup
- [ ] Document E2B API key setup in README

### P1 - Important

- [ ] Implement get_status method for health checks
- [ ] Add upload_file and download_file methods
- [ ] Implement cleanup_stale_sandboxes cron job
- [ ] Add retry logic with tenacity for transient failures
- [ ] Create unit tests with mocked E2B SDK
- [ ] Add structured logging for all E2B operations
- [ ] Implement sandbox metadata caching (Redis optional)

### P2 - Nice to Have

- [ ] Add sandbox metrics (creation time, command count)
- [ ] Implement pause/resume functionality
- [ ] Add sandbox resource usage tracking
- [ ] Create admin endpoint to list all active sandboxes
- [ ] Add sandbox template pre-initialization (Node, Git pre-installed)

## Success Criteria

- [ ] Sandbox created in <5 seconds (verify with timer)
- [ ] Sandbox ID stored in database with agent_id and task_id
- [ ] Commands execute successfully with stdout/stderr captured
- [ ] Sandbox destroyed cleanly with DB updated
- [ ] Error handling prevents zombie sandboxes
- [ ] Retry logic works for transient E2B failures
- [ ] API endpoints return correct status codes (201, 200, 204, 404, 500)
- [ ] Tests cover create, execute, destroy flows

## Risk Assessment

**High Risks:**
- E2B quota limits (concurrent sandboxes unknown)
- Sandbox crashes during git operations
- API key expiration/invalidation
- Network timeouts during creation

**Medium Risks:**
- Memory leaks in long-running sandboxes
- File system cleanup issues
- Database connection timeouts during bulk operations

**Mitigation:**
- Contact E2B for quota details
- Implement health checks every 30 seconds
- Rotate API keys with monitoring
- Set aggressive timeouts (5 min max)
- Destroy sandboxes immediately after task completion
- Use async database operations
- Add circuit breaker pattern for E2B API calls

## Security Considerations

- **API Key Storage:** Environment variable only, never commit
- **Sandbox Isolation:** E2B Firecracker provides kernel-level isolation
- **Command Injection:** Validate all commands before execution (whitelist approach)
- **Resource Limits:** Set CPU/memory limits if E2B API supports
- **Access Control:** Verify agent owns sandbox before operations
- **Audit Logging:** Log all sandbox operations with timestamps

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 45 min | SDK integration, boilerplate generation |
| Senior Dev | 4-6 hrs | E2B SDK learning, async patterns |
| Junior Dev | 10-12 hrs | E2B concepts, error handling, testing |

**Complexity:** Medium-High (external SDK, async operations)

## Next Steps

After completion:
- [Phase 03 - Git Operations Service](./phase-03-git-operations-service.md) - Execute git commands in sandbox
- [Phase 05 - SSE Real-Time Updates](./phase-05-sse-realtime-updates.md) - Stream sandbox logs

## Unresolved Questions

1. **E2B Tier:** Free tier limits? Need Pro for 24hr sessions?
2. **Sandbox Templates:** Can we pre-install Node.js and Git in template?
3. **Concurrent Limits:** How many sandboxes allowed simultaneously?
4. **Health Checks:** Does E2B provide built-in health check API?
5. **File Transfer:** Max file size for upload/download?
6. **Cleanup Schedule:** How often to run stale sandbox cleanup? (Hourly? Daily?)
7. **Error Recovery:** Should we auto-retry sandbox creation on quota errors?
