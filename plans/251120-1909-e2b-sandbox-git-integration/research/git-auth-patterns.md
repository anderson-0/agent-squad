# Git Authentication Patterns for Sandbox Environments

## Overview
Secure git authentication in ephemeral sandbox environments requires special considerations for SSH keys, tokens, and multi-agent parallel operations.

## Authentication Methods

### 1. SSH Key Authentication
**Injection Methods:**
- Environment variable with base64-encoded key
- File mounting (Kubernetes secrets, Docker volumes)
- Runtime file creation from secure storage
- SSH agent forwarding (not recommended for sandboxes)

**Implementation Patterns:**
```bash
# Method 1: GIT_SSH_COMMAND
GIT_SSH_COMMAND="ssh -i /path/to/key -o StrictHostKeyChecking=no" git clone <repo>

# Method 2: git config
git clone -c "core.sshCommand=ssh -i ~/.ssh/id_rsa" <repo>

# Method 3: SSH config file
# ~/.ssh/config
Host github.com
  IdentityFile ~/.ssh/deploy_key
  StrictHostKeyChecking no
```

### 2. Personal Access Tokens (PAT)
**Advantages:**
- Simpler than SSH keys
- Revocable without key rotation
- Scope-limited permissions
- Works over HTTPS

**Implementation:**
```bash
# Method 1: URL embedding (less secure)
git clone https://<token>@github.com/user/repo.git

# Method 2: Git credential helper
git config credential.helper store
echo "https://<token>:x-oauth-basic@github.com" > ~/.git-credentials

# Method 3: Environment variable
git config credential.helper '!f() { echo "username=token"; echo "password=$GIT_TOKEN"; }; f'
```

### 3. Deploy Keys vs User Keys
**Deploy Keys:**
- Repository-specific
- Read-only or read-write per repo
- Better for automation
- No user context

**User Keys:**
- Access multiple repos
- User-level permissions
- Audit trail tied to user
- Better for interactive work

## Multi-Agent Parallel Git Operations

### Concurrency Challenges
1. **Merge conflicts** - Multiple agents pushing simultaneously
2. **Race conditions** - Pull before push may be outdated
3. **Branch management** - Agent-specific branches vs shared
4. **Lock contention** - Large repos with many files

### Best Practices
1. **Agent-specific branches:**
   ```
   feature/<agent-id>-<task-id>
   ```

2. **Optimistic locking pattern:**
   ```bash
   git pull --rebase
   # make changes
   git push || (git pull --rebase && git push)
   ```

3. **Lease-based coordination:**
   - Redis/Consul for distributed locks
   - Timeout-based lease expiration
   - Queue-based task assignment

4. **Git worktrees:**
   ```bash
   git worktree add ../agent-1-workspace branch-name
   ```

## Security Best Practices

### SSH Key Management
- ✅ Use deploy keys with minimal permissions
- ✅ Rotate keys regularly
- ✅ One key per sandbox/agent
- ✅ Destroy keys when sandbox terminates
- ❌ Never commit private keys
- ❌ Avoid long-lived keys in ephemeral environments

### Token Management
- ✅ Use short-lived tokens (GitHub Apps)
- ✅ Scope tokens to specific repos
- ✅ Store in secret management systems (Vault, AWS Secrets Manager)
- ✅ Inject at runtime, never hardcode
- ❌ Never log tokens
- ❌ Avoid embedding in URLs (visible in logs)

### E2B-Specific Considerations
1. **Environment variables:** Use E2B's `envs` parameter for secrets
2. **File injection:** Write SSH keys to sandbox filesystem at creation
3. **Cleanup:** Ensure keys are deleted when sandbox terminates
4. **Network access:** Verify E2B allows outbound git connections

## Parallel Operations Architecture

### Option 1: Branch-per-Agent
```
main
├── agent-1-feature-auth
├── agent-2-feature-api
└── agent-3-feature-ui
```
**Pros:** No conflicts, clear ownership
**Cons:** Many branches, complex merging

### Option 2: Shared Branch with Locking
```
Redis: "branch:feature/payment" -> agent-id (TTL: 5min)
```
**Pros:** Fewer branches, simpler workflow
**Cons:** Blocking, single point of contention

### Option 3: File-Level Granularity
```
agent-1: src/auth/**
agent-2: src/api/**
agent-3: src/ui/**
```
**Pros:** Minimal conflicts, high parallelism
**Cons:** Requires task planning, hard boundaries

## Recommended Pattern for Agent-Squad

### Hybrid Approach
1. **Initial clone:** Use PAT for simplicity
2. **Branch strategy:** agent-<id>/<feature-name>
3. **Conflict resolution:** Auto-rebase with retry
4. **Merge strategy:** PR-based with CI checks
5. **Cleanup:** Delete agent branches after merge

### Implementation Sketch
```python
class GitSandboxManager:
    def setup_git_auth(self, sandbox, repo_url):
        # Inject PAT as env var
        token = get_secret("GITHUB_PAT")
        sandbox.commands.run(f"git config --global credential.helper '!f() {{ echo \"username=token\"; echo \"password={token}\"; }}; f'")

    def clone_repo(self, sandbox, repo_url, agent_id):
        branch = f"agent-{agent_id}-{task_id}"
        sandbox.commands.run(f"git clone {repo_url} /workspace")
        sandbox.commands.run(f"cd /workspace && git checkout -b {branch}")

    def push_changes(self, sandbox, agent_id):
        # Pull-rebase-push pattern
        result = sandbox.commands.run("cd /workspace && git pull --rebase origin main")
        if result.exit_code != 0:
            # Handle conflicts
            pass
        sandbox.commands.run(f"cd /workspace && git push origin agent-{agent_id}-*")
```

## Unresolved Questions
1. Does E2B restrict outbound SSH/HTTPS git connections?
2. What's the maximum file size for git operations in E2B?
3. How to handle SSH key passphrase protection in sandboxes?
4. Best retry strategy for git push conflicts with 10+ agents?

## References
- Git credential helpers: https://git-scm.com/docs/gitcredentials
- GitHub Deploy Keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys
- E2B Sandbox: https://e2b.dev/docs
