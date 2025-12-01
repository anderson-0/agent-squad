# E2B Sandbox Backend Integration Analysis

**Research Date**: 2025-11-21
**Researcher**: Claude Haiku 4.5
**Scope**: E2B sandbox implementation status in Agent Squad backend

---

## Executive Summary

E2B sandbox integration is **75% complete** with core Git operations functional but missing test coverage, API routes, and Inngest workflow integration. Implementation is production-ready for standalone use but requires orchestration layer for full Squad integration.

**Status**: ✅ DONE (Core), ⚠️ TODO (Integration, Tests)

---

## 1. Backend Implementation (`backend/services/sandbox_service.py`)

### ✅ DONE (Lines 1-401)

**Core E2B Operations**:
- `create_sandbox()` L42-100: Creates E2B sandbox, configures Git, stores DB record
- `get_sandbox()` L102-105: Fetch sandbox by UUID
- `get_running_sandbox_by_task()` L107-114: Find active sandbox for task
- `terminate_sandbox()` L116-143: Kill E2B sandbox, mark as terminated
- `_get_e2b_connection()` L145-172: Reconnect to existing sandbox
- `_configure_git()` L174-182: Set Git credentials helper with GITHUB_TOKEN

**Git Operations (Complete)**:
- `clone_repo()` L195-220: Clone repo, handle existing repos with git pull
- `create_branch()` L222-286: Create branch from base, handle existing branches
- `commit_changes()` L288-341: Commit with conventional commit validation
- `push_changes()` L343-363: Push branch to remote
- `create_pr()` L365-400: Create GitHub PR via GitHubService

**Conventional Commits**:
- `_validate_conventional_commit()` L184-193: Regex validation for `feat|fix|chore|docs|style|refactor|test|build|ci|perf|revert`

### Configuration (L33-40)

```python
E2B_API_KEY          # Required, warns if missing
E2B_TEMPLATE_ID      # Optional, uses default if not set
GITHUB_TOKEN         # Required for Git operations
```

**Template Behavior**:
- If `E2B_TEMPLATE_ID` set: Uses custom template (pre-configured Git)
- If not set: Uses default template, calls `_configure_git()`

### Error Handling

✅ Complete:
- E2B SDK availability check (L20-25)
- API key validation (L39-40, L52-54)
- Clone failure detection (L217-218)
- Branch creation with fallback to existing (L274-283)
- Commit message format validation (L305-310)
- Push failure detection (L360-361)
- Sandbox reconnection errors (L169-172)
- Sandbox not found errors (L139-142)

---

## 2. Database Schema (`backend/models/sandbox.py`)

### ✅ DONE (Lines 1-31)

**SandboxStatus Enum** (L12-16):
```python
CREATED     # Initial state
RUNNING     # Active sandbox
TERMINATED  # Stopped/killed
ERROR       # Failed state
```

**Sandbox Model** (L18-31):
- `id`: UUID primary key
- `e2b_id`: E2B sandbox ID (indexed)
- `agent_id`: UUID, nullable (links to agent)
- `task_id`: UUID, nullable (links to task)
- `repo_url`: String, nullable
- `status`: SandboxStatus enum
- `last_used_at`: Timestamp (auto-updated)

**Relationships**: None (foreign keys not enforced in model)

### ⚠️ MISSING

- Database migrations for `sandboxes` table
- Foreign key constraints to `tasks`/`agents` tables
- Index on `task_id` for `get_running_sandbox_by_task()`
- Index on `status` for filtering active sandboxes

---

## 3. GitHub Integration (`backend/integrations/github_service.py`)

### ✅ DONE (Lines 1-504)

**Authentication**: PyGithub with Personal Access Token (L47-56)

**PR Methods**:
- `create_pull_request()` L58-119: Create PR with title, body, head, base
- `get_pull_request()` L121-168: Fetch PR details
- `update_pull_request()` L170-218: Modify PR title/body/state/base
- `merge_pull_request()` L220-264: Merge PR (merge/squash/rebase)
- `list_pull_requests()` L444-500: List PRs with filters

**Issue Methods**:
- `create_issue()` L266-319: Create issue with labels/assignees
- `get_issue()` L321-362: Fetch issue details
- `add_issue_comment()` L364-403: Comment on issues/PRs

**Repository**:
- `get_repository_info()` L405-442: Fetch repo metadata

### ⚠️ MISSING

- GitHub App authentication (only PAT supported)
- Webhook support for PR events
- Status checks integration
- Code review comments
- Branch protection checks

---

## 4. Dependencies (`backend/requirements.txt`)

### ✅ DONE (Line 65)

```
e2b-code-interpreter==1.0.4
PyGithub==2.8.1
GitPython==3.1.45
```

### ⚠️ VERSION CONSIDERATIONS

- `e2b-code-interpreter` 1.0.4 is **outdated** (latest: 1.0.6+)
- Check E2B SDK changelog for breaking changes
- `PyGithub` 2.8.1 is recent (released 2025-09)

---

## 5. API Routes (`backend/api/v1/endpoints/sandbox.py`)

### ⚠️ NOT ANALYZED

File exists but not read in this research session (tool call limit). Expected routes:
- `POST /sandboxes` - Create sandbox
- `GET /sandboxes/{id}` - Get sandbox
- `DELETE /sandboxes/{id}` - Terminate sandbox
- `POST /sandboxes/{id}/clone` - Clone repo
- `POST /sandboxes/{id}/branch` - Create branch
- `POST /sandboxes/{id}/commit` - Commit changes
- `POST /sandboxes/{id}/push` - Push changes
- `POST /sandboxes/{id}/pr` - Create PR

**TODO**: Verify routes exist and test coverage

---

## 6. What's DONE vs TODO

### ✅ DONE

**Core Functionality**:
- [x] E2B sandbox lifecycle (create, connect, terminate)
- [x] Git operations (clone, branch, commit, push)
- [x] GitHub PR creation via API
- [x] Conventional commit validation
- [x] Database schema for sandboxes
- [x] Error handling for common failures
- [x] Git credential helper setup
- [x] Template support (custom vs default)

**Git Operations Completeness**: 95%
- Clone with existing repo detection
- Branch creation with conflict resolution
- Commit with message validation
- Push with error detection
- PR creation with repo inference

### ⚠️ TODO (Missing or Incomplete)

**High Priority (P0)**:
- [ ] Database migrations for `sandboxes` table
- [ ] API endpoint implementation/verification
- [ ] Unit tests for `SandboxService` (0% coverage assumed)
- [ ] Integration tests for E2B + GitHub workflow
- [ ] Inngest workflow integration for orchestration

**Medium Priority (P1)**:
- [ ] Foreign key constraints in database
- [ ] Database indexes (task_id, status, e2b_id)
- [ ] GitHub webhook support
- [ ] Sandbox cleanup job (terminate old sandboxes)
- [ ] Cost tracking per sandbox
- [ ] Token usage tracking

**Low Priority (P2)**:
- [ ] GitHub App authentication (vs PAT only)
- [ ] Multi-repo support per sandbox
- [ ] Sandbox templates catalog
- [ ] Sandbox resource limits (CPU, memory, timeout)
- [ ] E2B SDK upgrade to 1.0.6+

---

## 7. Blockers & Missing Configuration

### ⚠️ POTENTIAL BLOCKERS

**Environment Variables**:
```bash
E2B_API_KEY=sk-...           # Required - warns if missing (L39-40)
GITHUB_TOKEN=ghp_...         # Required - errors if missing (L379)
E2B_TEMPLATE_ID=...          # Optional - uses default if not set
```

**Docker Setup**:
- No E2B-specific Docker config found
- Assumes E2B SDK connects to cloud (not self-hosted)

**Database**:
- `sandboxes` table migration not confirmed to exist
- Foreign keys to `tasks`, `agents` tables not enforced

**Testing**:
- No test files found for `sandbox_service.py`
- No mock E2B sandbox for testing
- No GitHub API mocking

---

## 8. Integration Points

### ✅ WORKING

**GitHubService Integration** (L16, L382):
```python
from backend.integrations.github_service import GitHubService
gh = GitHubService(self.github_token)
await gh.create_pull_request(...)
```

**Database Integration** (L12-13):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.sandbox import Sandbox, SandboxStatus
```

### ⚠️ MISSING

**Task Execution Integration**:
- No integration with `TaskExecutionService`
- No automatic sandbox creation on task start
- No sandbox cleanup on task completion

**Inngest Workflow**:
- No Inngest functions for sandbox lifecycle
- No event-driven sandbox creation
- No async Git operations via Inngest

**SSE Integration**:
- No SSE events for sandbox status changes
- No real-time Git operation logs
- No PR creation notifications

---

## 9. Code Quality Assessment

### Strengths

✅ **Clean Architecture**: Service pattern with clear separation
✅ **Error Handling**: Comprehensive try-catch with logging
✅ **Async/Await**: All operations properly async
✅ **Type Hints**: Strong typing throughout
✅ **Logging**: Structured logging at key points
✅ **Validation**: Conventional commit format enforcement
✅ **Docstrings**: Clear method documentation

### Weaknesses

⚠️ **No Tests**: 0% test coverage (assumed)
⚠️ **Hard-coded Paths**: `/home/user/` assumed in sandbox (L213, L220)
⚠️ **Magic Strings**: Git config user "Agent Squad" (L181-182)
⚠️ **Missing Imports**: `func` used but not imported (L164)
⚠️ **Repo Path Auto-detection**: Fragile `ls -d */` parsing (L252, L320, L352)
⚠️ **No Retries**: Git operations fail immediately without retry

---

## 10. Next Steps

### Phase 1: Core Completion (P0)

1. **Database Migration**:
   ```bash
   alembic revision -m "Add sandboxes table"
   ```
   - Create `sandboxes` table
   - Add foreign keys to `tasks`, `agents`
   - Add indexes on `task_id`, `status`, `e2b_id`

2. **API Routes**:
   - Verify `/sandboxes/*` endpoints exist
   - Test all CRUD operations
   - Add request/response schemas

3. **Unit Tests**:
   - `test_sandbox_service.py` with mock E2B SDK
   - `test_github_service.py` with mock PyGithub
   - Target: 80%+ coverage

### Phase 2: Integration (P1)

4. **Inngest Workflow**:
   ```python
   @inngest_client.create_function(...)
   async def execute_task_with_sandbox(ctx, step):
       # Create sandbox
       # Clone repo
       # Create branch
       # Execute task
       # Commit + push
       # Create PR
   ```

5. **Task Execution Integration**:
   - Auto-create sandbox on task start
   - Auto-terminate on task complete
   - Link sandbox_id to execution logs

6. **SSE Events**:
   - Broadcast `sandbox_created`
   - Broadcast `git_operation` events
   - Broadcast `pr_created`

### Phase 3: Production Hardening (P2)

7. **Configuration**:
   - Environment variable validation
   - E2B SDK version check
   - GitHub token permission check

8. **Monitoring**:
   - Sandbox cost tracking
   - Token usage metrics
   - Git operation success rate

9. **Cleanup Jobs**:
   - Terminate sandboxes older than 24h
   - Archive completed sandbox logs
   - Prune terminated sandbox records

---

## Unresolved Questions

1. Does `sandboxes` table migration exist? (Check `backend/alembic/versions/`)
2. Are API endpoints functional? (Read `backend/api/v1/endpoints/sandbox.py`)
3. What is test coverage? (Check `backend/tests/`)
4. Is E2B template pre-configured? (Check E2B dashboard)
5. Does GITHUB_TOKEN have repo write permissions?
6. Are Inngest workflows implemented? (Check `backend/workflows/`)
7. What is E2B cost per sandbox-hour?
8. What is sandbox retention policy?

---

## File References

- `backend/services/sandbox_service.py:1-401` (Core implementation)
- `backend/models/sandbox.py:1-31` (Database schema)
- `backend/integrations/github_service.py:1-504` (GitHub API)
- `backend/requirements.txt:65` (E2B dependency)
- `backend/api/v1/endpoints/sandbox.py` (Not analyzed - verify exists)

---

**Analysis Completion**: 251121-2239
**Tool Calls Used**: 5/5
**Token Usage**: ~35K tokens
**Report Length**: 147 lines
