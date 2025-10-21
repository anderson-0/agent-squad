# Phase 4: MCP Server Integration - Implementation Plan

**Timeline**: 7-10 days
**Status**: 🟡 IN PROGRESS
**Start Date**: October 13, 2025

**⚠️ IMPORTANT NOTE**: We're implementing Day 4 first, then returning to Day 3 (Jira/Confluence integration) later. This is because:
- Day 4 (Advanced Orchestration) doesn't depend on Jira/Confluence
- Jira Cloud setup requires API tokens and testing setup
- We can complete Day 4 with existing Git integration
- We'll return to Jira/Confluence MCP integration after Day 4 is complete

**Current Focus**: Day 4 - Advanced Orchestration & Multi-Agent Coordination

---

## 🎯 Goals

Connect AI agents to real development tools so they can:
- Read and write code in Git repositories
- Manage Jira tickets (read, update status, comment)
- Access documentation from various sources
- Create commits and pull requests
- Enable end-to-end automation: Jira ticket → code → PR

---

## 📋 Prerequisites

### Understanding MCP (Model Context Protocol)

MCP is a standardized protocol that allows AI models to interact with external tools and data sources. Instead of building custom integrations for each tool, we use MCP servers that provide:

- **Standardized Interface**: All tools expose the same API
- **Tool Discovery**: Automatically list available tools
- **Type Safety**: Structured tool definitions with schemas
- **Multiple Transports**: stdio, SSE, or HTTP

### MCP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Squad Platform                      │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ BaseAgent    │      │ Specialized  │                    │
│  │              │      │ Agents       │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│         ┌──────────▼──────────┐                            │
│         │  MCP Client Manager │                            │
│         │  - Connection pool  │                            │
│         │  - Tool registry    │                            │
│         │  - Request routing  │                            │
│         └──────────┬──────────┘                            │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │ MCP Protocol (stdio/SSE)
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
    │ Git MCP │ │ Jira   │ │ Filesystem │
    │ Server  │ │ Server │ │ MCP Server │
    └────┬────┘ └───┬────┘ └───┬────┘
         │          │          │
    ┌────▼────┐ ┌──▼─────┐ ┌──▼─────┐
    │ GitHub  │ │ Jira   │ │ Local  │
    │ API     │ │ API    │ │ Files  │
    └─────────┘ └────────┘ └────────┘
```

---

## 📅 Day-by-Day Implementation Plan

### Day 1: Setup & MCP Client Foundation
**Goal**: Install MCP SDK and create client manager

#### Tasks

1. **Install MCP Python SDK**
```bash
cd backend
uv pip install mcp anthropic-mcp
```

2. **Create MCP client manager** (`backend/integrations/mcp/client.py`)
   - Connection pool for multiple MCP servers
   - Tool registry to track available tools
   - Async connection management
   - Error handling and reconnection logic

3. **Create base types** (`backend/integrations/mcp/types.py`)
   - Type definitions for MCP messages
   - Tool definitions
   - Response schemas

4. **Add configuration** (`backend/core/config.py`)
   - MCP server endpoints
   - Authentication tokens
   - Connection timeouts

**Deliverables:**
- ✅ MCP SDK installed
- ✅ MCPClientManager class
- ✅ Type definitions
- ✅ Configuration added

---

### Day 2: Git Integration
**Goal**: Enable agents to read/write code via Git

#### Tasks

1. **Create Git integration wrapper** (`backend/integrations/mcp/git_integration.py`)
   - Clone repositories
   - Read files
   - List files with patterns
   - Create branches
   - Commit changes
   - Push to remote
   - Create pull requests

2. **Set up Git MCP server**
   - Use `@modelcontextprotocol/server-git` or custom implementation
   - Configure authentication (GitHub tokens)
   - Test basic operations

3. **Create Git service** (`backend/services/git_service.py`)
   - High-level operations for agents
   - Repository caching
   - Diff generation
   - File search

4. **Add database models** (if needed)
   - Track cloned repositories
   - Store Git credentials securely
   - Cache repository metadata

**Deliverables:**
- ✅ GitIntegration class
- ✅ Git MCP server running
- ✅ Basic operations working (clone, read, commit)

**Test Cases:**
- Clone a public repository
- Read a file from repository
- Create a branch
- Commit a change
- Push to remote

---

### Day 3: Jira Integration
**Status**: ⏸️ **POSTPONED** - Will return to this after Day 4
**Goal**: Enable agents to work with Jira tickets

**📝 Note**: Partial implementation exists. Need to complete:
1. Set up Jira Cloud account and API token
2. Update .env with Jira Cloud credentials
3. Test mcp-atlassian integration or use direct REST API
4. Complete integration tests

**What's Already Done:**
- ✅ JiraService class created (`backend/integrations/jira_service.py`)
- ✅ Direct REST API test script (`test_jira_direct.py`)
- ✅ MCP client bug fixed (context manager issue)
- ✅ Docker setup for local Jira (optional, using Cloud instead)
- ✅ Integration test skeleton (`backend/tests/test_integration/test_real_atlassian.py`)

**What's Pending:**
- ⏸️ Jira Cloud API token setup
- ⏸️ Update environment variables with Cloud credentials
- ⏸️ Test real Jira integration (create ticket, get by ID, add comment)
- ⏸️ Confluence integration setup and testing
- ⏸️ Webhook handler implementation

#### Tasks (When we return to this)

1. **Complete Jira Cloud setup**
   - Create API token at https://id.atlassian.com/manage-profile/security/api-tokens
   - Update .env with: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
   - Create TEST project in Jira Cloud

2. **Test Jira integration**
   - Run `test_jira_direct.py` to verify API access
   - Test create ticket, get ticket, add comment, update status

3. **Set up Confluence (optional)**
   - Use same Atlassian account
   - Create API token
   - Test basic operations

4. **Webhook handler** (`backend/api/v1/endpoints/webhooks.py`)
   - Handle Jira webhooks
   - Trigger task execution on ticket events
   - Update local ticket cache

**Deliverables:**
- ⏸️ JiraIntegration class
- ⏸️ Jira MCP server configured
- ⏸️ Basic operations working
- ⏸️ Webhook handler

**Test Cases:**
- Fetch a Jira ticket
- Update ticket status
- Add a comment
- Search tickets with JQL
- Handle webhook event

---

### Day 4: Advanced Orchestration & Multi-Agent Coordination
**Status**: ✅ **COMPLETED** - October 13, 2025
**Goal**: Implement advanced multi-agent coordination patterns and orchestration

**Why This Day?**: This doesn't require Jira/Confluence - we can use existing Git integration to build and test orchestration patterns.

**📝 Implementation Summary**:
- ✅ Added MCP client integration to BaseSquadAgent
- ✅ Implemented tool discovery and execution methods
- ✅ Created tool-aware prompt generation system
- ✅ Built automatic tool execution loop (process_message_with_tools)
- ✅ Added tool execution history tracking
- ✅ Tested with real Git MCP server (12 tools working)
- ✅ Created comprehensive test suite (all tests passing)
- ✅ Full documentation created (docs/DAY_4_ADVANCED_ORCHESTRATION.md)

#### Tasks

1. **Update BaseSquadAgent** (`backend/agents/base_agent.py`)
   - Add MCP client as parameter
   - Create tool execution method
   - Add tool discovery
   - Implement tool calling in LLM prompts

2. **Tool-aware prompt generation**
   - List available tools in system prompt
   - Format tool descriptions for LLM
   - Parse tool use from LLM responses
   - Execute tools and feed results back

3. **Update specialized agents**
   - BackendDeveloperAgent: Add Git operations
   - FrontendDeveloperAgent: Add Git operations
   - ProjectManagerAgent: Add Jira operations
   - TechLeadAgent: Add Git + code review tools

4. **Tool execution flow**
```python
# Agent receives message
# → LLM suggests tool use
# → Agent executes tool via MCP
# → Agent receives tool result
# → LLM processes result
# → Agent responds with result
```

**Deliverables:**
- ✅ Tool execution in BaseSquadAgent
- ✅ Tool-aware prompts
- ✅ Specialized agents updated
- ✅ Tool result processing

**Test Cases:**
- Agent reads a file from Git
- Agent lists files in repository
- Agent commits a change
- Agent reads a Jira ticket
- Agent updates ticket status

---

### Day 5: Task Execution with MCP
**Goal**: Update task execution service to use MCP

#### Tasks

1. **Update TaskExecutionService** (`backend/services/task_execution_service.py`)
   - Initialize MCP clients for execution
   - Pass MCP client to agents
   - Handle tool errors gracefully
   - Clean up connections after execution

2. **Create execution context**
   - Project configuration (Git repo, Jira project)
   - MCP server connections
   - Tool permissions
   - Execution environment

3. **Implement end-to-end workflow**
```python
# 1. Receive Jira ticket webhook
# 2. PM analyzes ticket
# 3. Delegate to developer
# 4. Developer clones repo
# 5. Developer reads relevant files
# 6. Developer makes changes
# 7. Developer commits and creates PR
# 8. Tech Lead reviews PR (via GitHub API)
# 9. Update Jira ticket status
```

4. **Error handling and rollback**
   - Handle tool failures
   - Rollback Git changes on error
   - Update ticket status on failure
   - Retry logic

**Deliverables:**
- ✅ MCP-enabled task execution
- ✅ End-to-end workflow
- ✅ Error handling
- ✅ Connection cleanup

**Test Cases:**
- Execute task with Git operations
- Execute task with Jira operations
- Handle tool failure gracefully
- Clean up connections properly

---

### Day 6: API Endpoints & Schemas
**Goal**: Create REST API for MCP management

#### Tasks

1. **Create MCP schemas** (`backend/schemas/mcp.py`)
```python
class MCPServerCreate(BaseModel):
    name: str
    project_id: str
    server_type: str  # git, jira, filesystem
    config: Dict[str, Any]

class MCPServerConfig(BaseModel):
    id: str
    name: str
    project_id: str
    server_type: str
    status: str  # connected, disconnected, error
    available_tools: List[str]

class MCPToolInfo(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPToolExecution(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class MCPToolResult(BaseModel):
    success: bool
    result: Any
    error: Optional[str]
```

2. **Create MCP endpoints** (`backend/api/v1/endpoints/mcp.py`)
   - `POST /mcp/servers` - Register MCP server
   - `GET /mcp/servers/{project_id}` - List servers
   - `GET /mcp/servers/{server_id}` - Get server details
   - `DELETE /mcp/servers/{server_id}` - Remove server
   - `GET /mcp/tools/{server_id}` - List available tools
   - `POST /mcp/tools/{server_id}/{tool_name}` - Execute tool
   - `GET /mcp/health/{server_id}` - Check server health

3. **Add to API router** (`backend/api/v1/router.py`)

4. **Update database models**
   - MCPServer model
   - Store server configurations
   - Track connection status

**Deliverables:**
- ✅ MCP schemas
- ✅ 7 API endpoints
- ✅ Database models
- ✅ API documentation

**Test Cases:**
- Register a Git server
- List servers for project
- Execute tool via API
- Check server health
- Delete server configuration

---

### Day 7: Testing & Documentation
**Goal**: Comprehensive testing and documentation

#### Tasks

1. **Unit Tests**
   - `tests/test_mcp/test_client.py` - Client manager tests
   - `tests/test_mcp/test_git_integration.py` - Git operations
   - `tests/test_mcp/test_jira_integration.py` - Jira operations
   - `tests/test_agents/test_mcp_tools.py` - Agent tool usage

2. **Integration Tests**
   - `tests/test_integration/test_mcp_workflow.py`
     - End-to-end: Jira ticket → code change → PR
     - Test Git clone, read, commit, push
     - Test Jira ticket updates
     - Test error handling

3. **API Tests**
   - `tests/test_api/test_mcp_endpoints.py`
     - Test all MCP endpoints
     - Test authentication
     - Test error cases

4. **Documentation**
   - MCP integration guide
   - Tool usage examples
   - Configuration guide
   - Troubleshooting guide

**Deliverables:**
- ✅ 20+ test cases
- ✅ 80%+ test coverage on MCP code
- ✅ Integration tests passing
- ✅ Comprehensive documentation

**Test Coverage Goals:**
- MCPClientManager: 85%+
- GitIntegration: 80%+
- JiraIntegration: 80%+
- Agent tool execution: 75%+
- API endpoints: 85%+

---

## 📊 Success Criteria

### Functional Requirements
- ✅ Agents can clone Git repositories
- ✅ Agents can read files from repositories
- ✅ Agents can create branches
- ✅ Agents can commit changes
- ✅ Agents can push to remote
- ✅ Agents can create pull requests
- ✅ Agents can read Jira tickets
- ✅ Agents can update Jira ticket status
- ✅ Agents can add comments to tickets
- ✅ End-to-end workflow works: Jira → Code → PR

### Technical Requirements
- ✅ MCP client properly manages connections
- ✅ Error handling for tool failures
- ✅ Connection cleanup on completion
- ✅ Concurrent tool execution supported
- ✅ Tool results properly formatted for LLMs
- ✅ Authentication secure (tokens encrypted)
- ✅ API endpoints authenticated

### Quality Requirements
- ✅ All tests passing (target: 50+ tests)
- ✅ 80%+ code coverage on critical paths
- ✅ No memory leaks in long-running connections
- ✅ Proper error messages for debugging
- ✅ Comprehensive documentation

---

## 🔧 Technical Details

### MCP Connection Lifecycle

```python
# 1. Initialize
mcp_client = MCPClientManager()

# 2. Connect to server
await mcp_client.connect_server(
    name="git",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-git"],
    env={"GIT_REPO_PATH": "/path/to/repo"}
)

# 3. List available tools
tools = mcp_client.get_available_tools("git")
# → ["git_clone", "read_file", "list_files", "commit", "push"]

# 4. Call tool
result = await mcp_client.call_tool(
    "git",
    "read_file",
    {"path": "src/main.py"}
)

# 5. Disconnect
await mcp_client.disconnect_all()
```

### Agent Tool Execution Flow

```python
# 1. Agent receives task
task = "Fix the bug in user authentication"

# 2. PM analyzes, delegates to Backend Developer
dev_agent = BackendDeveloperAgent(mcp_client=mcp_client)

# 3. Developer asks LLM for plan
# LLM response includes tool use:
{
  "action": "use_tool",
  "tool": "git_read_file",
  "args": {"path": "src/auth.py"}
}

# 4. Agent executes tool
file_content = await dev_agent.execute_tool(
    "git_read_file",
    path="src/auth.py"
)

# 5. Agent asks LLM to analyze code
analysis = await dev_agent.process_message(
    f"Here's the code:\n{file_content}\nWhat's the bug?",
    context={"task": task}
)

# 6. LLM identifies bug and suggests fix
# 7. Agent executes more tools to make changes
# 8. Agent commits and creates PR
```

### Database Schema for MCP

```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    server_type VARCHAR(50) NOT NULL, -- git, jira, filesystem
    config JSONB NOT NULL, -- credentials, endpoints
    status VARCHAR(50) DEFAULT 'disconnected',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mcp_servers_project ON mcp_servers(project_id);
```

---

## 🎯 Key Milestones

- **Day 1**: MCP SDK installed, client manager working
- **Day 2**: Git operations functional
- **Day 3**: Jira operations functional
- **Day 4**: Agents can use tools
- **Day 5**: End-to-end workflow working
- **Day 6**: API complete
- **Day 7**: All tests passing

---

## 📚 Resources

### MCP Documentation
- Official MCP Spec: https://spec.modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Example servers: https://github.com/modelcontextprotocol/servers

### Available MCP Servers
- Git: `@modelcontextprotocol/server-git`
- Jira: Custom implementation needed
- Filesystem: `@modelcontextprotocol/server-filesystem`
- GitHub: `@modelcontextprotocol/server-github`
- PostgreSQL: `@modelcontextprotocol/server-postgres`

### Testing Tools
- pytest for unit tests
- pytest-asyncio for async tests
- httpx for API testing
- Mock MCP server for testing

---

## 🚨 Risk Mitigation

### Risk: MCP connection failures
**Mitigation**: Retry logic, connection pooling, health checks

### Risk: Tool execution timeouts
**Mitigation**: Configurable timeouts, async execution, progress tracking

### Risk: Large file operations
**Mitigation**: Streaming, chunking, file size limits

### Risk: Security (leaked tokens)
**Mitigation**: Encrypt credentials in database, use environment variables, audit logs

---

## 📈 Expected Outcomes

After Phase 4, the Agent Squad platform will:
1. ✅ Connect to real development tools (Git, Jira)
2. ✅ Enable agents to make actual code changes
3. ✅ Automate end-to-end workflows
4. ✅ Support multiple projects with different tool configurations
5. ✅ Provide real-time visibility into tool usage
6. ✅ Handle errors gracefully

This makes the platform truly useful for real software development work!

---

**Ready to begin Phase 4!** 🚀
