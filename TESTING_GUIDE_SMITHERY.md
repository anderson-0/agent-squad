# Testing Agents with Smithery & GitHub - Step by Step

**Goal**: Test your backend developer agent using GitHub MCP tools via Smithery

**Time Required**: ~10 minutes

---

## Prerequisites Check

Before we start, make sure you have:
- [ ] Node.js installed (`node --version` should work)
- [ ] Python 3.8+ installed
- [ ] A GitHub account
- [ ] Access to a GitHub repository (can be a test repo)

---

## Step 1: Get Your GitHub Token (5 minutes)

### 1.1 Go to GitHub Settings

1. Open your browser
2. Go to: https://github.com/settings/tokens
3. Click **"Generate new token"** → **"Generate new token (classic)"**

### 1.2 Configure Token

**Name**: `Agent Squad MCP Testing`

**Expiration**: Choose `90 days` (or whatever you prefer)

**Select Scopes** (check these boxes):
- ✅ `repo` (Full control of private repositories)
- ✅ `read:org` (Read org and team membership)
- ✅ `workflow` (Update GitHub Action workflows)

### 1.3 Generate and Copy

1. Scroll down, click **"Generate token"**
2. **COPY THE TOKEN NOW** (you won't see it again!)
3. Should look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## Step 2: Set Up Environment Variables (2 minutes)

### 2.1 Copy Example File

```bash
# In your terminal, from the project root
cd /Users/anderson/Documents/anderson-0/agent-squad

# Copy the example file
cp .env.mcp.example .env
```

### 2.2 Edit .env File

```bash
# Open .env in your editor
code .env  # or nano .env, or vim .env
```

### 2.3 Add Your GitHub Token

Find this line:
```bash
GITHUB_TOKEN=ghp_your_github_personal_access_token_here
```

Replace with YOUR token:
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**IMPORTANT**:
- Don't add quotes around the token
- No spaces before or after the `=`
- Save the file!

### 2.4 (Optional) Skip Jira for Now

If you don't have Jira, comment out these lines:
```bash
# JIRA_URL=https://your-company.atlassian.net
# JIRA_USERNAME=your-email@company.com
# JIRA_API_TOKEN=your_jira_api_token_here
```

We'll test GitHub first!

---

## Step 3: Install Dependencies (1 minute)

```bash
# Make sure you're in the project root
cd /Users/anderson/Documents/anderson-0/agent-squad

# Activate your virtual environment (if not already)
source backend/.venv/bin/activate

# Or if using uv:
source .venv/bin/activate

# Install Smithery CLI (optional but helpful)
npm install -g @smithery/cli

# Install Git MCP server (still needed for local git operations)
npm install -g @modelcontextprotocol/server-git
```

---

## Step 4: Verify Configuration (1 minute)

```bash
# Check that Smithery is active
grep "active_profile" backend/agents/configuration/mcp_tool_mapping.yaml

# Should show:
# active_profile: "smithery"
```

If it doesn't say "smithery", let me know!

---

## Step 5: Understanding the Test Script

I've created a comprehensive test script at `demo_github_mcp_test.py` that will:

### What the script does:

**Test 1: Configuration Check**
- Verifies active profile is "smithery"
- Checks your GitHub token is present and valid
- Ensures all prerequisites are met

**Test 2: Agent Creation**
- Creates a backend developer agent
- Initializes MCP tools for the agent
- Shows how many tools are available
- Lists the first 5 tools

**Test 3: MCP Service**
- Tests the MCP service directly
- Shows which servers are available
- Lists all tools for each server
- Initializes connections

**Test 4: GitHub Operation**
- Asks agent to search for popular Python repo on GitHub
- This tests real GitHub API access via Smithery
- Shows if agent actually used the tools
- Displays the response

The script has detailed success/error messages so you'll know exactly what's working!

---

## Step 6: Run the Test (2 minutes)

### 6.1 Load Environment Variables

```bash
# Make sure your .env is loaded
export $(cat .env | xargs)

# Or if using dotenv:
# The script loads .env automatically
```

### 6.2 Run the Test Script

```bash
# Make sure you're in project root
cd /Users/anderson/Documents/anderson-0/agent-squad

# Activate virtual environment
source backend/.venv/bin/activate

# Run the test
PYTHONPATH=$PWD python demo_github_mcp_test.py
```

### 6.3 What You Should See

If everything works, you'll see:

```
======================================================================
🚀 AGENT SQUAD - GitHub MCP Testing (Smithery)
======================================================================

======================================================================
STEP 1: Checking Configuration
======================================================================

ℹ️  Active MCP profile: smithery
✅ Configuration set to Smithery!
✅ GitHub token found and looks valid!

======================================================================
STEP 2: Creating Backend Developer Agent
======================================================================

✅ Agent created successfully!
ℹ️  Agent: AgnoBackendDeveloperAgent(agent_id=...)
ℹ️  Agent has 15 tools configured
✅ MCP tools initialized!
ℹ️  Available tools:
  - git_status
  - git_diff
  - git_log
  - search_repositories
  - get_repository
  ... and 10 more

======================================================================
STEP 3: Testing MCP Service
======================================================================

ℹ️  Tools available for backend_developer:

  git server:
    - git_status
    - git_diff
    - git_log
    - git_commit
    - git_push
    ... and 3 more

  github server:
    - search_repositories
    - get_repository
    - create_pull_request
    - search_code
    - get_pull_request
    ... and 3 more

ℹ️  Initializing MCP servers...
✅ Initialized 2 MCP servers!
  ✓ git
  ✓ github

======================================================================
STEP 4: Testing GitHub Operation
======================================================================

ℹ️  We'll ask the agent to search for a GitHub repository
ℹ️  This tests that Smithery's GitHub MCP server is working

✅ Agent responded!
ℹ️  Agent's response:

The most popular Python repository on GitHub is "python/cpython" -
the official Python programming language repository.

✅ Agent used 1 tool(s)!
  - github.search_repositories

======================================================================
🎉 TESTING COMPLETE!
======================================================================

✅ Your agents can now use GitHub tools via Smithery!

Next steps:
  1. Try more complex operations (create issues, PRs, etc.)
  2. Test with your own repositories
  3. Build your AI-powered workflows!

======================================================================
```

---

## Step 7: Troubleshooting

### Problem: "Configuration is not set to 'smithery'"

**Solution**:
```bash
# Check current setting
grep "active_profile" backend/agents/configuration/mcp_tool_mapping.yaml

# If not "smithery", update it
# Open the file and change line 15 to:
active_profile: "smithery"
```

---

### Problem: "GITHUB_TOKEN not found in environment"

**Solution**:
```bash
# Check if .env exists
ls -la .env

# If not, copy from example
cp .env.mcp.example .env

# Edit .env and add your GitHub token
code .env  # or nano .env

# Load environment
export $(cat .env | xargs)

# Verify it's loaded
echo $GITHUB_TOKEN  # Should show your token (ghp_...)
```

---

### Problem: "GitHub token doesn't start with 'ghp_'"

**Solution**:
- Make sure you copied the full token from GitHub
- Classic tokens start with `ghp_`
- Fine-grained tokens start with `github_pat_`
- Both should work, but classic is simpler

---

### Problem: "No tools found on agent"

**Possible causes**:

1. **MCP servers not installed**
```bash
# Install Smithery CLI
npm install -g @smithery/cli

# Install Git MCP server
npm install -g @modelcontextprotocol/server-git

# Verify installations
which smithery
which mcp-server-git
```

2. **Python dependencies missing**
```bash
# Make sure MCP client is installed
pip list | grep mcp

# If not:
pip install mcp
```

3. **Configuration issue**
```bash
# Test MCP mapper
python -c "from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper; print(get_tool_mapper().get_servers_for_role('backend_developer'))"

# Should print: ['git', 'github']
```

---

### Problem: "Agent didn't use any tools"

This might mean:
- Agent decided it doesn't need tools for this query
- Try a more specific query that requires GitHub access

**Better test queries**:
```bash
# These REQUIRE GitHub API calls
"Get details of the repository 'anthropics/anthropic-sdk-python'"
"Search for repositories with topic 'fastapi' and 'python'"
"Show me the latest release of 'python/cpython'"
```

---

### Problem: "Permission denied" or "API rate limit"

**Solution**:
- Check your GitHub token has correct scopes (repo, read:org, workflow)
- GitHub has rate limits: 5000 requests/hour for authenticated requests
- Wait a few minutes if you hit the limit

---

### Problem: "ModuleNotFoundError"

**Solution**:
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=$PWD

# Or run with full path
PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python demo_github_mcp_test.py
```

---

## Step 8: What's Next?

Now that your agents can use GitHub tools, you can:

### 1. Test More GitHub Operations

Create a test script for different operations:
```python
# Search repositories
await agent.process_message("Find Python FastAPI starter templates")

# Get repository details
await agent.process_message("Get details of repository 'tiangolo/fastapi'")

# Search code
await agent.process_message("Find examples of FastAPI authentication")

# List issues
await agent.process_message("Show open issues in repository 'anthropics/anthropic-sdk-python'")
```

### 2. Test with Your Own Repository

```python
await agent.process_message(
    "Get the README file from my repository 'username/my-repo'"
)
```

### 3. Multi-Agent Collaboration

```python
# Create multiple agents
pm = AgentFactory.create_agent(role="project_manager", ...)
backend = AgentFactory.create_agent(role="backend_developer", ...)
frontend = AgentFactory.create_agent(role="frontend_developer", ...)

# PM asks backend to create a feature
pm_response = await pm.process_message("Create a user authentication API")

# Backend dev implements and creates PR
backend_response = await backend.process_message(
    f"Implement this: {pm_response.content}. Create a PR when done."
)
```

### 4. Add More MCP Tools

Once GitHub is working, add Jira:

```bash
# Get Jira API token: https://id.atlassian.com/manage-profile/security/api-tokens

# Add to .env:
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_token

# Test Jira
await pm.process_message("Create a Jira ticket for user authentication feature")
```

### 5. Switch to Self-Hosted (Optional)

Once you've tested and are ready for unlimited usage:

```bash
# Update config
# In backend/agents/configuration/mcp_tool_mapping.yaml
active_profile: "self_hosted"

# Install servers (one-time)
npm install -g @modelcontextprotocol/server-github

# Done! Now unlimited free usage
```

---

## Step 9: Getting Help

If you run into issues:

1. **Check Logs**
```bash
# Run with verbose logging
DEBUG=true PYTHONPATH=$PWD python demo_github_mcp_test.py
```

2. **Test Components Individually**
```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test MCP mapper
python -c "from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper; print(get_tool_mapper().get_active_profile())"
```

3. **Check Documentation**
- MCP Setup: See `MCP_FLEXIBLE_SETUP.md`
- Smithery Guide: See `MCP_SETUP_SMITHERY.md`
- Self-Hosted Guide: See `MCP_SETUP_GUIDE.md`
- Implementation Details: See `MCP_IMPLEMENTATION_SUMMARY.md`

4. **Common Issues**
- Token not loading: Make sure to run `export $(cat .env | xargs)`
- PYTHONPATH error: Always set `PYTHONPATH=$PWD` when running scripts
- Import errors: Activate virtual environment first

---

## Success! 🎉

You've successfully set up your Agent Squad to use GitHub tools via Smithery!

**What you've accomplished**:
- ✅ Configured Smithery as your MCP provider
- ✅ Set up GitHub authentication
- ✅ Created and tested an agent with MCP tools
- ✅ Verified agent can interact with GitHub API

**Your agents can now**:
- Search repositories
- Get repository details
- Create/update issues
- Create pull requests
- Search code
- And much more!

Welcome to AI-powered development with Agent Squad! 🚀
