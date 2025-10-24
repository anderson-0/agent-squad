# MCP Tool Setup Guide - Self-Hosted (Recommended)

## 🎯 Why Self-Host?

✅ **Free unlimited usage** - No request limits
✅ **Full control** - You manage everything
✅ **Production-ready** - Best for real applications
✅ **Privacy** - Data never leaves your infrastructure
✅ **Scalable** - Unlimited growth without cost increase

**Setup Time**: ~15 minutes

---

## 📋 Prerequisites

```bash
# Check Node.js installed
node --version  # Should be 18+

# Check npm installed
npm --version

# Check Python (for Jira server)
python --version  # Should be 3.8+
```

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install MCP Servers

```bash
# Install Git MCP Server (required for local repos)
npm install -g @modelcontextprotocol/server-git

# Install GitHub MCP Server (required for GitHub API)
npm install -g @modelcontextprotocol/server-github

# Jira MCP Server (community package, auto-installs via npx)
# No installation needed - uses npx on-demand
```

**Verification**:
```bash
# Test installations
which mcp-server-git       # Should show path
which mcp-server-github    # Should show path

# Or test with uvx
uvx mcp-server-git --help
uvx mcp-server-github --help
```

### Step 2: Set Environment Variables

```bash
# Copy example file
cp .env.mcp.example .env

# Edit .env and add your credentials
GITHUB_TOKEN=ghp_your_github_token_here
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here
```

**Get GitHub Token**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`, `workflow`
4. Copy token to `.env`

**Get Jira API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy token to `.env`

### Step 3: Verify Configuration

```bash
# Check config file uses self_hosted profile
grep "active_profile" backend/agents/configuration/mcp_tool_mapping.yaml
# Should show: active_profile: "self_hosted"

# If it shows "smithery", change it to "self_hosted"
```

**That's it!** You're ready to use MCP tools.

---

## 🧪 Testing

### Quick Test

```bash
# Test Git server
uvx mcp-server-git

# Test GitHub server
export GITHUB_TOKEN=ghp_...
uvx mcp-server-github

# Test Jira server
export JIRA_URL=https://...
export JIRA_USERNAME=...
export JIRA_API_TOKEN=...
npx -y @aashari/mcp-server-atlassian-jira
```

### Integration Test

```bash
# Run Python tests
pytest backend/tests/test_mcp_integration.py -v

# Or test with agents
PYTHONPATH=$PWD python demo_mcp_tools.py
```

---

## 📝 Configuration Details

### Current Setup (mcp_tool_mapping.yaml)

```yaml
active_profile: "self_hosted"  # ← Using self-hosted

server_profiles:
  self_hosted:  # ← Free unlimited usage
    git:
      command: "uvx"
      args: ["mcp-server-git"]

    github:
      command: "uvx"
      args: ["mcp-server-github"]
      env:
        GITHUB_TOKEN: "${GITHUB_TOKEN}"

    jira:
      command: "npx"
      args: ["-y", "@aashari/mcp-server-atlassian-jira"]
      env:
        JIRA_URL: "${JIRA_URL}"
        JIRA_EMAIL: "${JIRA_USERNAME}"
        JIRA_API_TOKEN: "${JIRA_API_TOKEN}"
```

### Switching Profiles (Optional)

If you want to try Smithery later:

```python
from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper

mapper = get_tool_mapper()

# Switch to Smithery
mapper.set_active_profile("smithery")

# Switch back to self-hosted
mapper.set_active_profile("self_hosted")
```

Or edit YAML directly:
```yaml
# Change this line:
active_profile: "smithery"  # Use Smithery (10k free/month)
```

---

## 🔧 Server Details

### Git Server (@modelcontextprotocol/server-git)

**Install**: `npm install -g @modelcontextprotocol/server-git`

**Tools**:
- `git_status` - Show repository status
- `git_diff` - Show changes
- `git_log` - Show commit history
- `git_branch` - List/create branches
- `git_checkout` - Switch branches
- `git_commit` - Create commits
- `git_push` - Push to remote
- `git_pull` - Pull from remote
- `git_merge` - Merge branches

**Why Local**: Needs access to your `.git` directory

### GitHub Server (@modelcontextprotocol/server-github)

**Install**: `npm install -g @modelcontextprotocol/server-github`

**Tools**:
- `search_repositories` - Find repos
- `search_code` - Search code
- `search_users` - Find users
- `get_repository` - Get repo info
- `create_pull_request` - Create PR
- `get_pull_request` - Get PR details
- `update_pull_request` - Update PR
- `merge_pull_request` - Merge PR
- `create_issue` - Create issue
- `get_issue` - Get issue
- `add_issue_comment` - Comment on issue
- `list_issues` - List issues

**Why Self-Host**: Unlimited requests, no cost

### Jira Server (@aashari/mcp-server-atlassian-jira)

**Install**: Auto-installs via `npx -y` (no manual install needed)

**Tools**:
- `create_ticket` - Create Jira ticket
- `get_ticket` - Get ticket details
- `update_ticket` - Update ticket
- `add_comment` - Add comment
- `change_status` - Change ticket status
- `assign_ticket` - Assign ticket
- `search_tickets` - Search tickets
- `get_sprint` - Get sprint info

**Why This One**: Community-maintained, supports Jira Cloud

---

## 🛠️ Troubleshooting

### Git Server Issues

**Problem**: `git_status` fails
**Solution**: Make sure you're in a Git repository
```bash
cd /path/to/your/repo
git status  # Test native git first
```

**Problem**: `mcp-server-git: command not found`
**Solution**: Install globally
```bash
npm install -g @modelcontextprotocol/server-git
# Or use uvx
uvx mcp-server-git
```

### GitHub Server Issues

**Problem**: "Bad credentials" error
**Solution**: Check your GitHub token
```bash
# Test token
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user

# Verify scopes
# Token needs: repo, read:org, workflow
```

**Problem**: Rate limiting
**Solution**: Self-hosted has no rate limits! But GitHub API has limits:
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour

### Jira Server Issues

**Problem**: "Unauthorized" error
**Solution**: Check your Jira credentials
```bash
# Test Jira API
curl -H "Authorization: Bearer $JIRA_API_TOKEN" \
     -H "Content-Type: application/json" \
     "$JIRA_URL/rest/api/3/myself"
```

**Problem**: `npx` slow on first run
**Solution**: Normal! It's downloading the package. Subsequent runs are faster.

### General Issues

**Problem**: Environment variables not loaded
**Solution**: Source your .env file
```bash
export $(cat .env | xargs)
# Or use python-dotenv in your app
```

**Problem**: Server crashes randomly
**Solution**: Check logs
```bash
# Add logging
export DEBUG=mcp:*
uvx mcp-server-git
```

---

## 📊 Cost Comparison

| Aspect | Self-Hosted | Smithery |
|--------|-------------|----------|
| **Monthly Cost** | $0 | $0 for <10k requests, then $ |
| **Request Limit** | Unlimited | 10,000/month free |
| **Setup Time** | 15 min | 5 min |
| **Maintenance** | You manage | They manage |
| **Data Privacy** | 100% yours | Proxied |
| **Uptime** | Your responsibility | 91%+ guaranteed |
| **Best For** | Production | Quick testing |

**For production apps**: Self-hosted is **much better**

---

## 🔄 Maintenance

### Updating Servers

```bash
# Update Git server
npm update -g @modelcontextprotocol/server-git

# Update GitHub server
npm update -g @modelcontextprotocol/server-github

# Jira server auto-updates (uses npx -y)
```

### Monitoring

```bash
# Check server versions
npm list -g @modelcontextprotocol/server-git
npm list -g @modelcontextprotocol/server-github

# Check for updates
npm outdated -g
```

### Health Checks

```python
# In your app
from backend.services.agent_mcp_service import get_agent_mcp_service

service = get_agent_mcp_service()

# Check if servers are connected
assert service.is_server_connected("backend_developer", "git")
assert service.is_server_connected("backend_developer", "github")
```

---

## 🚀 Advanced Configuration

### Custom Server Locations

Edit `mcp_tool_mapping.yaml`:

```yaml
self_hosted:
  git:
    command: "/custom/path/to/mcp-server-git"
    args: ["--custom-arg"]
```

### Server Logging

```bash
# Enable debug logging
export DEBUG=mcp:*
export MCP_LOG_LEVEL=DEBUG

# Run your app
python your_app.py
```

### Multiple Jira Instances

```yaml
self_hosted:
  jira_prod:
    command: "npx"
    args: ["-y", "@aashari/mcp-server-atlassian-jira"]
    env:
      JIRA_URL: "${JIRA_PROD_URL}"
      # ...

  jira_staging:
    command: "npx"
    args: ["-y", "@aashari/mcp-server-atlassian-jira"]
    env:
      JIRA_URL: "${JIRA_STAGING_URL}"
      # ...
```

---

## 📚 Resources

- **Git MCP Server**: https://github.com/modelcontextprotocol/servers/tree/main/src/git
- **GitHub MCP Server**: https://github.com/modelcontextprotocol/servers/tree/main/src/github
- **Jira MCP Server**: https://github.com/aashari/mcp-server-atlassian-jira
- **MCP Specification**: https://spec.modelcontextprotocol.io/

---

## 🎉 Summary

**You've set up self-hosted MCP servers!**

✅ **Git Server** - Local repository operations
✅ **GitHub Server** - GitHub API access (unlimited)
✅ **Jira Server** - Jira API access (unlimited)

**Total Cost**: **$0/month** 💰
**Request Limit**: **Unlimited** 🚀
**Setup Time**: **15 minutes** ⏱️

**Next Steps**:
1. Test with `pytest backend/tests/test_mcp_integration.py -v`
2. Create your first agent that uses tools
3. Build amazing AI-powered workflows!

**Need help?** Check troubleshooting section or open an issue on GitHub.
