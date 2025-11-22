# Phase 03 - Git Operations Service

**Date:** 2025-11-21
**Priority:** P0 (Critical)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:**
  - [Phase 01 - Backend Foundation](./phase-01-backend-foundation.md)
  - [Phase 02 - E2B Sandbox Service](./phase-02-e2b-sandbox-service.md)
- **Related Research:** [Git & GitHub API](./research/researcher-02-git-github-api.md)

## Overview

Automate git operations inside E2B sandboxes using simple-git. Clone repos, create task branches, commit with conventional commits, push to GitHub. Enables agents to work on code in isolation.

**Why simple-git:**
- 5.9M weekly downloads vs 535K (isomorphic-git)
- Wrapper around Git CLI (already in sandboxes)
- Simpler API for automation
- Node.js native support in E2B

## Key Insights

From research:
- simple-git supports HTTPS auth with tokens
- Branch format: `task-{taskId}` (e.g., `task-123`)
- Conventional commits: `feat:`, `fix:`, `chore:`, etc.
- GitHub PAT auth: `https://x-access-token:{TOKEN}@github.com/owner/repo`
- Push requires `--set-upstream` for new branches

## Requirements

### Functional
- Clone repository into sandbox workspace
- Configure git user (name, email from config)
- Create task-specific branch from main
- Stage files for commit
- Commit with conventional commit messages
- Push branch to remote with upstream tracking
- Handle git errors (auth failures, conflicts)
- Store commit history in database

### Non-Functional
- Clone time: <30 seconds for typical repos
- Commit atomicity (all-or-nothing)
- Retry on transient network failures
- No credential leakage in logs
- Support private repositories

## Architecture

### Git Workflow in Sandbox

```
1. Clone repo → 2. Checkout main → 3. Create task branch → 4. Make changes
                                          ↓
8. Push to remote ← 7. Commit ← 6. Stage files ← 5. Agent work
         ↓
9. Update DB with commit SHA, branch name
```

### Service Structure

```python
# app/services/git_service.py
class GitService:
    async def clone_repo(sandbox_id, repo_url, github_token) -> CloneResult
    async def create_branch(sandbox_id, branch_name) -> BranchResult
    async def stage_files(sandbox_id, file_patterns=['*']) -> StageResult
    async def commit(sandbox_id, message, author) -> CommitResult
    async def push_branch(sandbox_id, branch_name) -> PushResult
    async def get_commit_history(sandbox_id) -> List[Commit]

    # Helper methods
    def _build_authenticated_url(repo_url, token) -> str
    def _validate_commit_message(message) -> bool
```

### Command Execution via E2B

```python
# Execute git commands in sandbox
from app.services.e2b_service import E2BSandboxService

e2b = E2BSandboxService()

# Example: Clone repo
clone_command = f"git clone {auth_url} /workspace/repo"
result = await e2b.execute_command(sandbox_id, clone_command)

if result.exit_code != 0:
    raise GitOperationError(result.stderr)
```

## Related Code Files

### New Files to Create
- `backend/app/services/git_service.py` - Git operations service
- `backend/app/api/v1/git.py` - Git API endpoints
- `backend/app/schemas/git.py` - Git operation schemas
- `backend/tests/test_git_service.py`

### Files to Modify
- `backend/app/config.py` - Add GIT_USER_NAME, GIT_USER_EMAIL
- `backend/app/api/v1/router.py` - Mount git router
- `backend/app/models/task.py` - Add git_branch, commit_sha fields (if not exists)

## Implementation Steps

1. **Update Configuration**
   - Add GITHUB_TOKEN to config.py
   - Add GIT_USER_NAME (default: "Agent Squad Bot")
   - Add GIT_USER_EMAIL (default: "bot@agentsquad.dev")
   - Add REPO_URL to config (or per-squad setting)

2. **Create Git Service Class**
   - Import E2BSandboxService dependency
   - Implement _build_authenticated_url helper
   - Add _validate_commit_message (regex for conventional commits)

3. **Implement Clone Repository**
   - Build authenticated URL: `https://x-access-token:{TOKEN}@{repo}`
   - Execute: `git clone {url} /workspace/repo`
   - Capture stdout/stderr
   - Handle errors: invalid token, repo not found, network timeout
   - Store operation in git_operations table

4. **Implement Branch Creation**
   - Navigate to repo: `cd /workspace/repo`
   - Fetch latest: `git fetch origin`
   - Checkout main: `git checkout main`
   - Pull latest: `git pull origin main`
   - Create branch: `git checkout -b task-{task_id}`
   - Update task.git_branch in database

5. **Implement File Staging**
   - Navigate to repo
   - Stage files: `git add {patterns}` (default: `.`)
   - Check status: `git status --porcelain`
   - Return list of staged files

6. **Implement Commit**
   - Validate commit message matches conventional commits pattern
   - Configure user: `git config user.name "{GIT_USER_NAME}"`
   - Configure email: `git config user.email "{GIT_USER_EMAIL}"`
   - Commit: `git commit -m "{message}"`
   - Parse commit SHA from output
   - Store in git_operations table with commit_sha

7. **Implement Push**
   - Push with upstream: `git push -u origin {branch_name}`
   - Handle errors: authentication, push rejected, conflicts
   - Retry on transient failures (3 attempts)
   - Update task.git_branch and last_commit_sha

8. **Implement Get Commit History**
   - Execute: `git log --oneline --max-count=20`
   - Parse output into Commit objects
   - Return list of commits with SHA, message, author, date

9. **API Endpoints**
   - POST /api/v1/git/clone - Clone repository into sandbox
   - POST /api/v1/git/branch - Create task branch
   - POST /api/v1/git/commit - Commit changes
   - POST /api/v1/git/push - Push to remote
   - GET /api/v1/git/{sandbox_id}/history - Get commit history

10. **Error Handling**
    - Catch git errors (exit code != 0)
    - Parse stderr for specific errors (auth, network, conflicts)
    - Return structured error responses
    - Log all git operations with sanitized output (no tokens)

11. **Conventional Commit Validation**
    - Regex pattern: `^(feat|fix|docs|chore|refactor|test|ci)(\(.+\))?!?: .{1,100}$`
    - Validate before commit
    - Return 400 Bad Request if invalid
    - Suggest correct format in error message

12. **Unit Tests**
    - Mock E2BSandboxService.execute_command
    - Test clone with valid/invalid tokens
    - Test branch creation from main
    - Test commit message validation
    - Test push with network errors
    - Test commit history parsing

## Todo List

### P0 - Critical

- [ ] Add GITHUB_TOKEN, GIT_USER_NAME, GIT_USER_EMAIL to config.py
- [ ] Create app/services/git_service.py with GitService class
- [ ] Implement _build_authenticated_url helper (sanitize token in logs)
- [ ] Implement clone_repo method with error handling
- [ ] Implement create_branch method (fetch, checkout main, create task branch)
- [ ] Implement stage_files method (git add)
- [ ] Implement commit method with user config and validation
- [ ] Implement push_branch method with --set-upstream
- [ ] Implement conventional commit validation regex
- [ ] Create POST /api/v1/git/clone endpoint
- [ ] Create POST /api/v1/git/branch endpoint
- [ ] Create POST /api/v1/git/commit endpoint
- [ ] Create POST /api/v1/git/push endpoint
- [ ] Add git operation logging to git_operations table
- [ ] Test clone with real GitHub repo and PAT
- [ ] Test push creates branch on GitHub
- [ ] Verify commits appear in GitHub history

### P1 - Important

- [ ] Implement get_commit_history method
- [ ] Create GET /api/v1/git/{sandbox_id}/history endpoint
- [ ] Add retry logic for network failures (tenacity)
- [ ] Implement git status checking before operations
- [ ] Add conflict detection and error messages
- [ ] Create unit tests for all git operations
- [ ] Document git workflow in backend/README.md
- [ ] Add git operation timing metrics

### P2 - Nice to Have

- [ ] Support SSH authentication (alternative to HTTPS)
- [ ] Implement git diff endpoint (see changes before commit)
- [ ] Add commit message templates
- [ ] Support multi-commit workflows (incremental commits)
- [ ] Add git tag creation for releases
- [ ] Implement branch cleanup after PR merge

## Success Criteria

- [ ] Repository clones successfully into sandbox
- [ ] Task branch created with format `task-{id}`
- [ ] Commits have conventional commit format
- [ ] Push creates branch on GitHub visible in web UI
- [ ] Commit history retrieved and parsed correctly
- [ ] Authentication errors handled gracefully
- [ ] No GitHub token leakage in logs or error messages
- [ ] git_operations table populated with operation metadata

## Risk Assessment

**High Risks:**
- Token leakage in logs/errors
- Authentication failures blocking all operations
- Merge conflicts on main branch
- Network timeouts during large repo clones

**Medium Risks:**
- Invalid commit messages breaking automation
- Branch naming conflicts
- Stale branches accumulating on remote

**Mitigation:**
- Sanitize all git output before logging (regex replace tokens)
- Test token validity before operations
- Use fresh checkout of main for every branch
- Set 30-second timeout for clone operations
- Validate commit messages before execution
- Add timestamp suffix to branch names if conflicts: `task-{id}-{timestamp}`
- Implement branch cleanup webhook (optional, Phase 04)

## Security Considerations

- **Token Handling:** Never log GitHub token, replace in output with `***`
- **Command Injection:** Validate all user inputs before git commands
- **Private Repos:** Ensure token has correct permissions (repo scope)
- **Credential Caching:** Disable git credential helper in sandboxes
- **HTTPS Only:** Use HTTPS for cloning (easier token management than SSH)
- **Token Rotation:** Support multiple tokens for rate limit distribution

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 40 min | Command generation, endpoint creation |
| Senior Dev | 5-7 hrs | Git automation patterns, error handling |
| Junior Dev | 12-15 hrs | Git concepts, subprocess handling, testing |

**Complexity:** Medium-High (subprocess management, error handling)

## Next Steps

After completion:
- [Phase 04 - GitHub Integration](./phase-04-github-integration.md) - Create PRs with Octokit
- [Phase 05 - SSE Real-Time Updates](./phase-05-sse-realtime-updates.md) - Stream git operation logs

## Unresolved Questions

1. **Repo Configuration:** One repo per squad or global config?
2. **Base Branch:** Always use `main` or support custom base branches?
3. **Commit Author:** Bot name or agent name? (e.g., "Agent Alice" vs "Agent Squad Bot")
4. **Incremental Commits:** Should agents commit multiple times during task? Or single commit at end?
5. **Merge Strategy:** Squash commits in PR or keep history?
6. **Branch Cleanup:** Delete branches after PR merge? Who triggers it?
7. **Conflict Resolution:** How to handle merge conflicts on main? Manual intervention?
