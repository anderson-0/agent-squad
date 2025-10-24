# MCP Tool Setup with Smithery.ai

## Why Smithery.ai?

**Before (Manual Setup)**:
```bash
# Install 3 separate MCP servers
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-github
npm install -g mcp-server-jira  # Need to find/create custom server

# Manage 3 server processes
# Deal with server crashes, updates, etc.
```

**After (Smithery)**:
```bash
# Only install Git server (local repo access required)
npm install -g @modelcontextprotocol/server-git

# GitHub & Jira are HOSTED by Smithery - zero installation! 🎉
```

---

## Setup Steps

### 1. Install Prerequisites

```bash
# Install Node.js (if not already installed)
# Check: node --version

# Install Smithery CLI (optional, helps with discovery)
npm install -g @smithery/cli
```

### 2. Install Git MCP Server

**Only needed for local Git operations** (commit, push, branch, etc.):

```bash
# Option 1: Using npm
npm install -g @modelcontextprotocol/server-git

# Option 2: Using uvx (Python tool)
uvx mcp-server-git

# Verify installation
which mcp-server-git
```

### 3. Configure Environment Variables

```bash
# Copy example file
cp .env.mcp.example .env

# Edit .env and add your credentials:
GITHUB_TOKEN=ghp_your_github_token_here
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here
```

**Get GitHub Token**:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`, `workflow`
4. Copy token to `.env`

**Get Jira API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Copy token to `.env`

### 4. Test Connection (Optional)

```bash
# Test GitHub server via Smithery
npx -y @smithery/cli run @smithery-ai/github

# Test Jira server via Smithery
npx -y @smithery/cli run @aashari/mcp-server-atlassian-jira

# Test local Git server
mcp-server-git --help
```

---

## How It Works

### Architecture with Smithery

```
Your Agent Squad Application
         ↓
   AgentMCPService
         ↓
    MCPClientManager
         ↓
    ┌────────┴────────┐
    ↓                 ↓
Git Server      GitHub/Jira via Smithery CLI
(Local)         └─► Smithery Hosted Servers
                    └─► https://smithery.ai
```

### Server Details

#### Git Server (Local)
- **Installation**: Required (local repo access)
- **Command**: `uvx mcp-server-git`
- **Why Local**: Needs access to your local `.git` directory

#### GitHub Server (Smithery Hosted)
- **Installation**: None needed! 🎉
- **Command**: `npx -y @smithery/cli run @smithery-ai/github`
- **Uptime**: 91.72%
- **Response Time**: 5.61s (P95)
- **URL**: https://smithery.ai/server/@smithery-ai/github

#### Jira Server (Smithery Community)
- **Installation**: None needed! 🎉
- **Command**: `npx -y @smithery/cli run @aashari/mcp-server-atlassian-jira`
- **Provider**: Community (@aashari)
- **URL**: https://smithery.ai/server/@aashari/mcp-server-atlassian-jira

---

## Configuration File

Our `mcp_tool_mapping.yaml` is already configured for Smithery:

```yaml
mcp_servers:
  git:
    command: "uvx"
    args: ["mcp-server-git"]
    source: "npm"

  github:
    command: "npx"
    args: ["-y", "@smithery/cli", "run", "@smithery-ai/github"]
    source: "smithery"  # Hosted!

  jira:
    command: "npx"
    args: ["-y", "@smithery/cli", "run", "@aashari/mcp-server-atlassian-jira"]
    source: "smithery"  # Hosted!
```

**Note**: The `-y` flag auto-accepts prompts, making it non-interactive.

---

## Available Tools

### Git Server (Local)
```
git_status       - Show repository status
git_diff         - Show changes
git_log          - Show commit history
git_branch       - List/create branches
git_checkout     - Switch branches
git_commit       - Create commits
git_push         - Push to remote
git_pull         - Pull from remote
git_merge        - Merge branches
```

### GitHub Server (Smithery)
```
search_repositories    - Find repos
search_code           - Search code
search_users          - Find users
get_repository        - Get repo info
create_pull_request   - Create PR
get_pull_request      - Get PR details
update_pull_request   - Update PR
merge_pull_request    - Merge PR
create_issue          - Create issue
get_issue            - Get issue
add_issue_comment    - Comment on issue
list_issues          - List issues
```

### Jira Server (Smithery)
```
create_ticket      - Create Jira ticket
get_ticket        - Get ticket details
update_ticket     - Update ticket
add_comment       - Add comment
change_status     - Change ticket status
assign_ticket     - Assign ticket
search_tickets    - Search tickets
get_sprint        - Get sprint info
```

---

## Testing

### Quick Test

```bash
# 1. Set environment variables
export GITHUB_TOKEN=ghp_...
export JIRA_URL=https://your-company.atlassian.net
export JIRA_USERNAME=your-email@company.com
export JIRA_API_TOKEN=...

# 2. Test GitHub via Smithery
npx -y @smithery/cli run @smithery-ai/github

# This will:
# - Download Smithery CLI (if needed)
# - Connect to Smithery's hosted GitHub server
# - You can then interact with it via MCP protocol

# 3. Test Jira via Smithery
npx -y @smithery/cli run @aashari/mcp-server-atlassian-jira
```

### Full Integration Test

```bash
# Run Python tests
pytest backend/tests/test_mcp_integration.py -v

# Or run a demo
PYTHONPATH=$PWD python demo_mcp_tools.py
```

---

## Benefits of Smithery Approach

### ✅ Simplicity
- No need to manage GitHub/Jira server processes
- Smithery handles hosting, uptime, updates
- One less thing to worry about

### ✅ Reliability
- 91.72% uptime for GitHub server
- Professional monitoring and maintenance
- Automatic updates and security patches

### ✅ Discovery
- Browse 2,143 community MCP servers on Smithery.ai
- Find pre-built servers for common services
- No need to build custom servers

### ✅ Cost
- Free to use (Smithery's hosted servers)
- No server hosting costs
- Pay only for API usage (GitHub, Jira)

### ✅ Development Speed
- Start using tools immediately
- No server setup/configuration
- Focus on agent logic, not infrastructure

---

## Comparison

| Aspect | Manual Setup | Smithery Approach |
|--------|--------------|-------------------|
| **GitHub Server** | Install locally | Hosted (zero install) |
| **Jira Server** | Build custom or find one | Community server |
| **Git Server** | Install locally | Install locally (same) |
| **Maintenance** | You manage updates | Smithery manages |
| **Uptime** | Your responsibility | 91%+ guaranteed |
| **Setup Time** | ~30 min | ~5 min |
| **Dependencies** | 3 servers to manage | 1 server (Git only) |

---

## Troubleshooting

### GitHub Server Issues

**Q: GitHub tools not working?**
```bash
# Test connection manually
npx -y @smithery/cli run @smithery-ai/github

# Check token
echo $GITHUB_TOKEN

# Verify token scopes at:
# https://github.com/settings/tokens
```

### Jira Server Issues

**Q: Jira tools not working?**
```bash
# Test connection manually
npx -y @smithery/cli run @aashari/mcp-server-atlassian-jira

# Check credentials
echo $JIRA_URL
echo $JIRA_USERNAME
echo $JIRA_API_TOKEN

# Test Jira API directly:
curl -H "Authorization: Bearer $JIRA_API_TOKEN" \
     -H "Content-Type: application/json" \
     "$JIRA_URL/rest/api/3/myself"
```

### Git Server Issues

**Q: Git operations failing?**
```bash
# Verify installation
which mcp-server-git

# Test in local repo
cd /path/to/your/repo
mcp-server-git

# Check Git config
git config --list
```

### Smithery CLI Issues

**Q: npx @smithery/cli not working?**
```bash
# Install globally
npm install -g @smithery/cli

# Use directly
smithery run @smithery-ai/github

# Clear cache and retry
npm cache clean --force
npx -y @smithery/cli run @smithery-ai/github
```

---

## Alternative Jira Servers

If `@aashari/mcp-server-atlassian-jira` doesn't work for your setup, try these alternatives:

1. **@George5562/Jira-MCP-Server** (9 tools, natural language)
   ```bash
   npx -y @smithery/cli run @George5562/Jira-MCP-Server
   ```

2. **@ayasahmad/mcp-atlassian** (Jira + Confluence, supports Cloud & Server)
   ```bash
   npx -y @smithery/cli run @ayasahmad/mcp-atlassian
   ```

3. **@rahulthedevil/Jira-Context-MCP** (focused on issue context)
   ```bash
   npx -y @smithery/cli run @rahulthedevil/Jira-Context-MCP
   ```

Browse more: https://smithery.ai/?search=jira

---

## Next Steps

1. ✅ Set environment variables (`.env`)
2. ✅ Install Git MCP server (only local dependency)
3. ✅ Test GitHub connection via Smithery
4. ✅ Test Jira connection via Smithery
5. ✅ Run integration tests
6. ✅ Start using agents with real tools!

---

## Resources

- **Smithery.ai**: https://smithery.ai
- **Smithery CLI**: https://github.com/smithery-ai/cli
- **GitHub Server**: https://smithery.ai/server/@smithery-ai/github
- **Jira Server**: https://smithery.ai/server/@aashari/mcp-server-atlassian-jira
- **MCP Specification**: https://spec.modelcontextprotocol.io/

---

## Summary

**With Smithery, you only need to:**
1. Install Git MCP server (1 command)
2. Set 4 environment variables
3. Done! GitHub and Jira are hosted for you.

**No more:**
- ❌ Installing multiple servers
- ❌ Managing server processes
- ❌ Dealing with server crashes
- ❌ Updating servers manually
- ❌ Building custom Jira server

**Just:**
- ✅ Configure credentials
- ✅ Use the tools
- ✅ Build amazing agents
