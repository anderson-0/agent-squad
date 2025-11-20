# Approach 1: Quick Win - Extend Existing E2B MCP Server

## Overview

Extend existing E2B MCP server (`python_executor_server.py`) with git operation tools. Minimal changes, fast implementation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent (Agno)                             │
│  - Backend Developer Agent                                  │
│  - Frontend Developer Agent                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼ MCP Tool Call
┌─────────────────────────────────────────────────────────────┐
│         Git Operations MCP Server (NEW)                     │
│  Tools:                                                     │
│  - git_clone(repo_url, branch, agent_id)                   │
│  - git_pull(sandbox_id, auto_rebase)                       │
│  - git_push(sandbox_id, commit_msg)                        │
│  - git_status(sandbox_id)                                  │
│  - git_diff(sandbox_id)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼ Create/Use E2B Sandbox
┌─────────────────────────────────────────────────────────────┐
│                E2B Sandbox (Firecracker VM)                 │
│  /workspace/                                                │
│    └── <repo-name>/                                        │
│        ├── .git/                                           │
│        ├── backend/                                        │
│        └── frontend/                                       │
│                                                             │
│  Git Operations:                                           │
│  1. Inject GitHub PAT via env var                          │
│  2. Configure git credential helper                        │
│  3. Clone repo to /workspace/<repo>                        │
│  4. Create agent branch: agent-<id>-<task>                 │
│  5. Execute git commands via sandbox.commands.run()        │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. New File: `git_operations_server.py`

**Location:** `backend/integrations/mcp/servers/git_operations_server.py`

**Structure:** Similar to `python_executor_server.py`

**Tools:**
```python
class GitOperationsServer:
    tools = [
        # Clone repository and create agent branch
        {
            "name": "git_clone",
            "description": "Clone git repository into E2B sandbox",
            "input": {
                "repo_url": str,        # e.g., https://github.com/user/repo
                "branch": str,          # default: main
                "agent_id": str,        # e.g., agent-123
                "task_id": str          # e.g., task-456
            },
            "output": {
                "success": bool,
                "sandbox_id": str,      # For subsequent operations
                "agent_branch": str,    # e.g., agent-123-task-456
                "error": str | None
            }
        },

        # Pull latest changes with auto-rebase
        {
            "name": "git_pull",
            "description": "Pull latest changes from remote",
            "input": {
                "sandbox_id": str,
                "auto_rebase": bool     # default: True
            },
            "output": {
                "success": bool,
                "conflicts": List[str], # Files with conflicts
                "error": str | None
            }
        },

        # Push changes to remote
        {
            "name": "git_push",
            "description": "Push changes to remote repository",
            "input": {
                "sandbox_id": str,
                "commit_message": str,
                "files": List[str]      # Files to stage (empty = all)
            },
            "output": {
                "success": bool,
                "commit_hash": str,
                "pushed_branch": str,
                "error": str | None
            }
        },

        # Get git status
        {
            "name": "git_status",
            "description": "Get current git status",
            "input": {
                "sandbox_id": str
            },
            "output": {
                "success": bool,
                "modified": List[str],
                "untracked": List[str],
                "staged": List[str],
                "current_branch": str
            }
        },

        # Get git diff
        {
            "name": "git_diff",
            "description": "Get diff of changes",
            "input": {
                "sandbox_id": str,
                "files": List[str]      # Specific files (empty = all)
            },
            "output": {
                "success": bool,
                "diff": str
            }
        }
    ]
```

**Implementation Pattern:**
```python
class GitOperationsServer:
    def __init__(self, config):
        self.e2b_api_key = config.get("e2b_api_key") or os.environ.get("E2B_API_KEY")
        self.github_token = config.get("github_token") or os.environ.get("GITHUB_TOKEN")
        self.sandbox_cache = {}  # sandbox_id -> Sandbox instance

    async def _handle_git_clone(self, arguments):
        """Clone repo and create agent branch"""
        repo_url = arguments["repo_url"]
        branch = arguments.get("branch", "main")
        agent_id = arguments["agent_id"]
        task_id = arguments["task_id"]

        # Create E2B sandbox
        sandbox = Sandbox.create(
            api_key=self.e2b_api_key,
            envs={"GITHUB_TOKEN": self.github_token}
        )

        # Configure git credentials
        sandbox.commands.run(
            "git config --global credential.helper '!f() { "
            "echo \"username=token\"; "
            "echo \"password=$GITHUB_TOKEN\"; "
            "}; f'"
        )

        # Clone repository
        result = sandbox.commands.run(f"git clone {repo_url} /workspace/repo")
        if result.exit_code != 0:
            return {"success": False, "error": result.stderr}

        # Create agent branch
        agent_branch = f"agent-{agent_id}-{task_id}"
        sandbox.commands.run(
            f"cd /workspace/repo && "
            f"git checkout -b {agent_branch}"
        )

        # Cache sandbox
        self.sandbox_cache[sandbox.sandbox_id] = sandbox

        return {
            "success": True,
            "sandbox_id": sandbox.sandbox_id,
            "agent_branch": agent_branch
        }

    async def _handle_git_push(self, arguments):
        """Push changes with auto-retry on conflict"""
        sandbox_id = arguments["sandbox_id"]
        commit_msg = arguments["commit_message"]
        files = arguments.get("files", [])

        sandbox = self.sandbox_cache.get(sandbox_id)
        if not sandbox:
            return {"success": False, "error": "Sandbox not found"}

        # Stage files
        stage_cmd = "cd /workspace/repo && git add ."
        if files:
            stage_cmd = f"cd /workspace/repo && git add {' '.join(files)}"
        sandbox.commands.run(stage_cmd)

        # Commit
        result = sandbox.commands.run(
            f"cd /workspace/repo && git commit -m '{commit_msg}'"
        )
        commit_hash = result.stdout.split()[0] if result.exit_code == 0 else None

        # Pull with rebase before push
        max_retries = 3
        for attempt in range(max_retries):
            # Pull
            sandbox.commands.run("cd /workspace/repo && git pull --rebase origin main")

            # Push
            push_result = sandbox.commands.run("cd /workspace/repo && git push")
            if push_result.exit_code == 0:
                return {
                    "success": True,
                    "commit_hash": commit_hash,
                    "pushed_branch": self._get_current_branch(sandbox)
                }

            # Retry if push failed
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {
            "success": False,
            "error": "Failed to push after retries"
        }
```

### 2. Modify: `mcp_tool_mapping.yaml`

**Location:** `backend/agents/configuration/mcp_tool_mapping.yaml`

**Add Git Operations Tools:**
```yaml
# Git Operations (E2B Sandbox)
git_clone:
  server: "git_operations"
  tool: "git_clone"
  description: "Clone repository into isolated sandbox"
  roles: ["backend_developer", "frontend_developer", "qa_tester"]

git_pull:
  server: "git_operations"
  tool: "git_pull"
  description: "Pull latest changes from remote"
  roles: ["backend_developer", "frontend_developer"]

git_push:
  server: "git_operations"
  tool: "git_push"
  description: "Push changes to remote repository"
  roles: ["backend_developer", "frontend_developer"]

git_status:
  server: "git_operations"
  tool: "git_status"
  description: "Get current git status"
  roles: ["backend_developer", "frontend_developer", "qa_tester"]

git_diff:
  server: "git_operations"
  tool: "git_diff"
  description: "Get diff of changes"
  roles: ["backend_developer", "frontend_developer", "qa_tester"]
```

### 3. Modify: `config.py`

**Location:** `backend/core/config.py`

**Add GitHub Token Config:**
```python
class Settings(BaseSettings):
    # ... existing config ...

    # GitHub Integration (for git operations in E2B)
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")
    GITHUB_DEFAULT_BRANCH: str = "main"

    # Git Sandbox Configuration
    GIT_SANDBOX_TIMEOUT: int = 300  # 5 minutes
    GIT_SANDBOX_MAX_RETRIES: int = 3
```

## Implementation Phases

### Phase 1: Core Git Operations (P0)
**Priority:** P0 (Must Have)

**Tasks:**
- [ ] Create `git_operations_server.py` with MCP server boilerplate
- [ ] Implement `git_clone` tool
- [ ] Implement `git_status` tool
- [ ] Implement `git_diff` tool
- [ ] Add GITHUB_TOKEN to config
- [ ] Update `mcp_tool_mapping.yaml` with git tools
- [ ] Write unit tests for git_clone

**Time Estimate:**
| Executor | Time |
|----------|------|
| Claude | 15 min |
| Senior Dev | 2 hrs |
| Junior Dev | 4 hrs |

**Success Criteria:**
- Agent can clone repository into E2B sandbox
- Agent can view git status
- Agent can view diffs
- GitHub token injected securely

### Phase 2: Push/Pull Operations (P0)
**Priority:** P0 (Must Have)

**Tasks:**
- [ ] Implement `git_push` with basic retry
- [ ] Implement `git_pull` with auto-rebase
- [ ] Add credential helper configuration
- [ ] Implement sandbox caching (dict-based)
- [ ] Add conflict detection logic
- [ ] Write integration tests for push/pull

**Time Estimate:**
| Executor | Time |
|----------|------|
| Claude | 15 min |
| Senior Dev | 2 hrs |
| Junior Dev | 4 hrs |

**Success Criteria:**
- Agent can push changes to remote
- Agent can pull latest changes
- Auto-rebase works on conflicts
- Retry logic handles transient failures

### Phase 3: Agent Branch Management (P1)
**Priority:** P1 (Should Have)

**Tasks:**
- [ ] Implement automatic agent branch creation pattern
- [ ] Add branch naming convention: `agent-{id}-{task_id}`
- [ ] Implement branch cleanup helper (optional)
- [ ] Add logging for git operations
- [ ] Document git workflow for agents

**Time Estimate:**
| Executor | Time |
|----------|------|
| Claude | 10 min |
| Senior Dev | 1 hr |
| Junior Dev | 2 hrs |

**Success Criteria:**
- Each agent gets unique branch
- Branches follow naming convention
- Branches can be cleaned up manually
- Operations logged properly

## Trade-offs

### Pros
1. **Fast implementation:** 30-45 min for Claude, 4-6 hrs for developers
2. **Low risk:** Extends proven E2B integration pattern
3. **Simple debugging:** Minimal moving parts
4. **Low maintenance:** Few files to maintain
5. **Cost-effective:** No additional infrastructure

### Cons
1. **Sandbox lifecycle:** New sandbox per clone operation (costs ~$0.01/hr on E2B)
2. **No pooling:** Can't reuse sandboxes across operations
3. **Basic retry:** Simple exponential backoff, no distributed coordination
4. **Limited monitoring:** Basic logging only
5. **Manual cleanup:** Agents must manage sandbox lifecycle

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| E2B sandbox costs accumulate | Medium | Medium | Implement timeout cleanup, monitor usage |
| Git push conflicts with parallel agents | High | Medium | Use branch-per-agent, retry with backoff |
| GitHub token exposure | Low | High | Inject via env vars, never log |
| Sandbox creation failures | Low | Medium | Retry with exponential backoff |
| Network issues (E2B -> GitHub) | Low | Low | E2B has good connectivity, retry handles transient issues |

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 30-45 min | Parallel file creation, automated testing |
| Senior Dev | 4-6 hrs | Familiar with E2B/git patterns, minimal research |
| Junior Dev | 8-12 hrs | Learning E2B SDK, git internals, testing |

**Complexity:** Simple

## Success Criteria

1. **Functional:**
   - ✅ Agents can clone repositories
   - ✅ Agents can commit and push changes
   - ✅ Agents can pull latest changes
   - ✅ Branch-per-agent isolation works

2. **Performance:**
   - ✅ Clone operation < 30 seconds
   - ✅ Push operation < 10 seconds
   - ✅ Retry logic handles conflicts

3. **Security:**
   - ✅ GitHub tokens never logged
   - ✅ Tokens injected via env vars only
   - ✅ Sandboxes isolated per agent

4. **Reliability:**
   - ✅ 95%+ success rate on git operations
   - ✅ Automatic retry on transient failures
   - ✅ Clear error messages for agents

## Testing Strategy

### Unit Tests
```python
# test_git_operations_server.py
async def test_git_clone_success():
    """Test successful repository clone"""
    server = GitOperationsServer(config)
    result = await server._handle_git_clone({
        "repo_url": "https://github.com/test/repo",
        "agent_id": "agent-123",
        "task_id": "task-456"
    })
    assert result["success"] == True
    assert "sandbox_id" in result
    assert result["agent_branch"] == "agent-123-task-456"

async def test_git_push_with_retry():
    """Test git push with conflict retry"""
    # Mock sandbox with conflict on first push
    # Verify retry logic
    pass
```

### Integration Tests
```python
async def test_full_git_workflow():
    """Test complete clone -> commit -> push workflow"""
    # 1. Clone repo
    # 2. Make file change
    # 3. Commit changes
    # 4. Push to remote
    # 5. Verify branch created
    pass
```

## Migration Path to Approach 2

If scaling requirements increase:

1. **Add sandbox pooling:** Extract sandbox management to dedicated service
2. **Add distributed locks:** Integrate Redis for coordination
3. **Add metrics:** Implement prometheus metrics
4. **Database layer:** Track sandbox state in PostgreSQL

Estimated migration effort: 1-2 days

## Unresolved Questions

1. Should sandboxes persist across multiple git operations or one-per-operation?
2. Max sandbox TTL before cleanup? (Suggest: 1 hour)
3. GitHub token scope: per-project or global?
4. Conflict resolution: auto-rebase only or support other strategies?
5. Branch cleanup: automatic or manual via separate tool?
