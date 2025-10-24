# MCP Tool Mapping Design

## Overview

This document defines which MCP tools each agent role can access and use. The mapping enables agents to perform real operations on GitHub and Jira rather than just exchanging messages.

## Architecture

```
┌─────────────────┐
│  Agno Agent     │
│  (Backend Dev)  │
└────────┬────────┘
         │
         ├─ MCP Client Manager
         │
         ├─► Git MCP Server
         │   └─ Tools: branch, commit, push, status
         │
         └─► GitHub MCP Server
             └─ Tools: create_pr, review_pr, create_issue
```

## MCP Servers

### 1. Git Server
**MCP Package**: `@modelcontextprotocol/server-git`
**Command**: `uvx mcp-server-git`
**Purpose**: Local git operations

**Available Tools**:
- `git_status` - Show working directory status
- `git_diff` - Show changes
- `git_log` - Show commit history
- `git_branch` - List/create branches
- `git_checkout` - Switch branches
- `git_commit` - Create commits
- `git_push` - Push to remote
- `git_pull` - Pull from remote
- `git_merge` - Merge branches

### 2. GitHub Server
**MCP Package**: `@modelcontextprotocol/server-github`
**Command**: `uvx mcp-server-github`
**Purpose**: GitHub API operations

**Available Tools**:
- `create_pull_request` - Create PR
- `get_pull_request` - Get PR details
- `update_pull_request` - Update PR
- `merge_pull_request` - Merge PR
- `create_issue` - Create issue
- `get_issue` - Get issue details
- `add_issue_comment` - Comment on issue
- `list_issues` - List issues
- `get_repository` - Get repo info
- `search_code` - Search repository code

### 3. Jira Server (Custom)
**Implementation**: `backend/integrations/mcp/servers/jira_server.py`
**Command**: `python -m backend.integrations.mcp.servers.jira_server`
**Purpose**: Jira API operations

**Available Tools**:
- `create_ticket` - Create Jira ticket
- `get_ticket` - Get ticket details
- `update_ticket` - Update ticket
- `add_comment` - Add comment
- `change_status` - Change ticket status
- `assign_ticket` - Assign ticket
- `search_tickets` - Search tickets
- `get_sprint` - Get sprint info

---

## Agent Tool Mapping

### 1. Project Manager
**Primary Responsibility**: Planning, coordination, ticket management

**MCP Servers**:
- ✅ Jira Server
- ✅ GitHub Server (limited)

**Allowed Tools**:
```yaml
jira:
  - create_ticket          # Create new tickets
  - get_ticket            # Read ticket details
  - update_ticket         # Update tickets
  - add_comment           # Add comments
  - change_status         # Update status
  - assign_ticket         # Assign to team
  - search_tickets        # Search tickets
  - get_sprint            # Sprint info

github:
  - list_issues           # View GitHub issues
  - create_issue          # Create issues
  - get_repository        # Repo information
```

**Use Cases**:
- Create Jira tickets from user requests
- Assign tickets to appropriate team members
- Track sprint progress
- Create GitHub issues for bugs/features
- Monitor repository activity

---

### 2. Tech Lead
**Primary Responsibility**: Code review, architecture decisions, mentoring

**MCP Servers**:
- ✅ Git Server
- ✅ GitHub Server
- ✅ Jira Server (limited)

**Allowed Tools**:
```yaml
git:
  - git_status            # Check repository state
  - git_diff              # Review changes
  - git_log               # Review history
  - git_branch            # Manage branches
  - git_merge             # Merge branches

github:
  - get_pull_request      # Review PRs
  - update_pull_request   # Request changes
  - merge_pull_request    # Approve and merge
  - add_issue_comment     # Comment on issues
  - search_code           # Code review
  - get_repository        # Repo info

jira:
  - get_ticket            # Read ticket details
  - add_comment           # Add comments
  - search_tickets        # Search tickets
```

**Use Cases**:
- Review pull requests
- Provide code review feedback
- Merge approved PRs
- Guide architecture decisions
- Monitor code quality

---

### 3. Backend Developer
**Primary Responsibility**: Backend implementation, API development

**MCP Servers**:
- ✅ Git Server (full access)
- ✅ GitHub Server

**Allowed Tools**:
```yaml
git:
  - git_status            # Check status
  - git_diff              # View changes
  - git_log               # View history
  - git_branch            # Create feature branches
  - git_checkout          # Switch branches
  - git_commit            # Commit changes
  - git_push              # Push code
  - git_pull              # Pull updates

github:
  - create_pull_request   # Create PRs
  - get_pull_request      # Check PR status
  - update_pull_request   # Update PR
  - create_issue          # Report issues
  - add_issue_comment     # Comment on issues
  - search_code           # Search codebase
```

**Use Cases**:
- Create feature branches
- Commit backend code
- Push changes to remote
- Create pull requests
- Respond to code review feedback
- Search codebase for examples

---

### 4. Frontend Developer
**Primary Responsibility**: Frontend implementation, UI development

**MCP Servers**:
- ✅ Git Server (full access)
- ✅ GitHub Server

**Allowed Tools**:
```yaml
git:
  - git_status            # Check status
  - git_diff              # View changes
  - git_log               # View history
  - git_branch            # Create feature branches
  - git_checkout          # Switch branches
  - git_commit            # Commit changes
  - git_push              # Push code
  - git_pull              # Pull updates

github:
  - create_pull_request   # Create PRs
  - get_pull_request      # Check PR status
  - update_pull_request   # Update PR
  - create_issue          # Report issues
  - add_issue_comment     # Comment on issues
  - search_code           # Search codebase
```

**Use Cases**:
- Create feature branches
- Commit frontend code
- Push changes to remote
- Create pull requests
- Respond to code review feedback
- Search for UI components

---

### 5. QA Tester
**Primary Responsibility**: Testing, quality assurance, bug reporting

**MCP Servers**:
- ✅ GitHub Server
- ✅ Jira Server

**Allowed Tools**:
```yaml
github:
  - create_issue          # Report bugs
  - get_issue            # Check bug status
  - add_issue_comment    # Add testing notes
  - list_issues          # View issues
  - get_pull_request     # Test PRs

jira:
  - get_ticket           # Read test requirements
  - update_ticket        # Update test results
  - add_comment          # Add test notes
  - change_status        # Mark as tested
  - create_ticket        # Create bug tickets
  - search_tickets       # Find related tickets
```

**Use Cases**:
- Create bug reports on GitHub
- Update Jira tickets with test results
- Comment on PRs with test feedback
- Track testing progress
- Report test coverage

---

### 6. DevOps Engineer
**Primary Responsibility**: Infrastructure, deployment, CI/CD

**MCP Servers**:
- ✅ Git Server
- ✅ GitHub Server (extended)

**Allowed Tools**:
```yaml
git:
  - git_status            # Check repository state
  - git_diff              # View changes
  - git_log               # View history
  - git_branch            # Manage branches
  - git_checkout          # Switch branches
  - git_merge             # Merge branches
  - git_push              # Push changes
  - git_pull              # Pull updates

github:
  - create_pull_request   # Infrastructure PRs
  - merge_pull_request    # Deploy merges
  - create_issue          # Infrastructure issues
  - get_repository        # Repo settings
  - search_code           # Search configs
```

**Use Cases**:
- Manage deployment branches
- Update CI/CD configurations
- Create infrastructure PRs
- Monitor repository settings
- Deploy to production

---

### 7. Solution Architect
**Primary Responsibility**: Architecture design, technical decisions

**MCP Servers**:
- ✅ GitHub Server (read-only)
- ✅ Jira Server (limited)

**Allowed Tools**:
```yaml
github:
  - get_repository        # Analyze repository
  - search_code           # Review architecture
  - get_pull_request      # Review design changes
  - list_issues           # Track architecture issues

jira:
  - get_ticket            # Read requirements
  - add_comment           # Architecture guidance
  - search_tickets        # Find related work
```

**Use Cases**:
- Review architecture decisions
- Analyze codebase structure
- Provide technical guidance
- Document architecture patterns

---

### 8. AI Engineer
**Primary Responsibility**: AI/ML implementation, model integration

**MCP Servers**:
- ✅ Git Server (full access)
- ✅ GitHub Server

**Allowed Tools**:
```yaml
git:
  - git_status            # Check status
  - git_diff              # View changes
  - git_log               # View history
  - git_branch            # Create ML branches
  - git_checkout          # Switch branches
  - git_commit            # Commit ML code
  - git_push              # Push changes
  - git_pull              # Pull updates

github:
  - create_pull_request   # Create ML PRs
  - get_pull_request      # Check PR status
  - update_pull_request   # Update PR
  - create_issue          # Report ML issues
  - search_code           # Search ML codebase
```

**Use Cases**:
- Implement ML models
- Create ML feature branches
- Push model updates
- Create PRs for model changes
- Document ML experiments

---

### 9. Designer
**Primary Responsibility**: UI/UX design, design systems

**MCP Servers**:
- ✅ GitHub Server (limited)

**Allowed Tools**:
```yaml
github:
  - create_issue          # Design feedback
  - add_issue_comment     # Design comments
  - get_issue            # Review design tickets
  - list_issues          # Track design work
```

**Use Cases**:
- Provide design feedback on issues
- Create design-related issues
- Comment on UI/UX discussions
- Track design implementation

---

## Configuration Structure

### Database Schema

```python
# New table: agent_mcp_tools
class AgentMCPTool(Base):
    __tablename__ = "agent_mcp_tools"

    id = Column(UUID, primary_key=True, default=uuid4)
    role = Column(String, nullable=False)           # e.g., "backend_developer"
    mcp_server = Column(String, nullable=False)     # e.g., "git", "github", "jira"
    tool_name = Column(String, nullable=False)      # e.g., "git_commit"
    enabled = Column(Boolean, default=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('role', 'mcp_server', 'tool_name'),
    )
```

### Configuration File: `backend/agents/configuration/mcp_tool_mapping.yaml`

```yaml
# MCP Tool Mapping Configuration
version: "1.0"

mcp_servers:
  git:
    command: "uvx"
    args: ["mcp-server-git"]
    env: {}

  github:
    command: "uvx"
    args: ["mcp-server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"

  jira:
    command: "python"
    args: ["-m", "backend.integrations.mcp.servers.jira_server"]
    env:
      JIRA_URL: "${JIRA_URL}"
      JIRA_USERNAME: "${JIRA_USERNAME}"
      JIRA_API_TOKEN: "${JIRA_API_TOKEN}"

roles:
  project_manager:
    mcp_servers:
      - jira
      - github
    tools:
      jira:
        - create_ticket
        - get_ticket
        - update_ticket
        - add_comment
        - change_status
        - assign_ticket
        - search_tickets
        - get_sprint
      github:
        - list_issues
        - create_issue
        - get_repository

  tech_lead:
    mcp_servers:
      - git
      - github
      - jira
    tools:
      git:
        - git_status
        - git_diff
        - git_log
        - git_branch
        - git_merge
      github:
        - get_pull_request
        - update_pull_request
        - merge_pull_request
        - add_issue_comment
        - search_code
        - get_repository
      jira:
        - get_ticket
        - add_comment
        - search_tickets

  backend_developer:
    mcp_servers:
      - git
      - github
    tools:
      git:
        - git_status
        - git_diff
        - git_log
        - git_branch
        - git_checkout
        - git_commit
        - git_push
        - git_pull
      github:
        - create_pull_request
        - get_pull_request
        - update_pull_request
        - create_issue
        - add_issue_comment
        - search_code

  frontend_developer:
    mcp_servers:
      - git
      - github
    tools:
      git:
        - git_status
        - git_diff
        - git_log
        - git_branch
        - git_checkout
        - git_commit
        - git_push
        - git_pull
      github:
        - create_pull_request
        - get_pull_request
        - update_pull_request
        - create_issue
        - add_issue_comment
        - search_code

  qa_tester:
    mcp_servers:
      - github
      - jira
    tools:
      github:
        - create_issue
        - get_issue
        - add_issue_comment
        - list_issues
        - get_pull_request
      jira:
        - get_ticket
        - update_ticket
        - add_comment
        - change_status
        - create_ticket
        - search_tickets

  devops_engineer:
    mcp_servers:
      - git
      - github
    tools:
      git:
        - git_status
        - git_diff
        - git_log
        - git_branch
        - git_checkout
        - git_merge
        - git_push
        - git_pull
      github:
        - create_pull_request
        - merge_pull_request
        - create_issue
        - get_repository
        - search_code

  solution_architect:
    mcp_servers:
      - github
      - jira
    tools:
      github:
        - get_repository
        - search_code
        - get_pull_request
        - list_issues
      jira:
        - get_ticket
        - add_comment
        - search_tickets

  ai_engineer:
    mcp_servers:
      - git
      - github
    tools:
      git:
        - git_status
        - git_diff
        - git_log
        - git_branch
        - git_checkout
        - git_commit
        - git_push
        - git_pull
      github:
        - create_pull_request
        - get_pull_request
        - update_pull_request
        - create_issue
        - search_code

  designer:
    mcp_servers:
      - github
    tools:
      github:
        - create_issue
        - add_issue_comment
        - get_issue
        - list_issues
```

---

## Implementation Classes

### 1. MCPToolMapper

```python
# backend/agents/configuration/mcp_tool_mapper.py

from typing import Dict, List, Set
import yaml
from pathlib import Path

class MCPToolMapper:
    """
    Manages MCP tool mapping configuration.

    Loads tool mapping from YAML and provides methods to query
    which tools each agent role can access.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "mcp_tool_mapping.yaml"

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_servers_for_role(self, role: str) -> List[str]:
        """Get list of MCP servers for a role."""
        role_config = self.config["roles"].get(role, {})
        return role_config.get("mcp_servers", [])

    def get_tools_for_role(self, role: str, server: str) -> List[str]:
        """Get list of allowed tools for a role on a specific server."""
        role_config = self.config["roles"].get(role, {})
        tools = role_config.get("tools", {})
        return tools.get(server, [])

    def can_use_tool(self, role: str, server: str, tool: str) -> bool:
        """Check if a role can use a specific tool."""
        allowed_tools = self.get_tools_for_role(role, server)
        return tool in allowed_tools

    def get_server_config(self, server: str) -> Dict:
        """Get connection configuration for an MCP server."""
        return self.config["mcp_servers"].get(server, {})

    def get_all_tools_for_role(self, role: str) -> Dict[str, List[str]]:
        """Get all tools organized by server for a role."""
        role_config = self.config["roles"].get(role, {})
        return role_config.get("tools", {})
```

### 2. AgentMCPService

```python
# backend/services/agent_mcp_service.py

from backend.agents.configuration.mcp_tool_mapper import MCPToolMapper
from backend.integrations.mcp.client import MCPClientManager
from typing import Dict, Any, List

class AgentMCPService:
    """
    Service for managing agent MCP tool access.
    """

    def __init__(self):
        self.mapper = MCPToolMapper()
        self.mcp_manager = MCPClientManager()

    async def initialize_agent_tools(self, role: str) -> Dict[str, Any]:
        """
        Initialize MCP servers and tools for an agent role.

        Returns:
            Dictionary mapping server names to ClientSession objects
        """
        servers = self.mapper.get_servers_for_role(role)
        sessions = {}

        for server_name in servers:
            server_config = self.mapper.get_server_config(server_name)

            session = await self.mcp_manager.connect_server(
                name=server_name,
                command=server_config["command"],
                args=server_config.get("args", []),
                env=server_config.get("env", {})
            )

            sessions[server_name] = session

        return sessions

    async def execute_tool(
        self,
        role: str,
        server: str,
        tool: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool if the role has permission.

        Raises:
            PermissionError: If role cannot use this tool
        """
        if not self.mapper.can_use_tool(role, server, tool):
            raise PermissionError(
                f"Role '{role}' is not allowed to use tool '{tool}' "
                f"on server '{server}'"
            )

        return await self.mcp_manager.call_tool(
            server_name=server,
            tool_name=tool,
            arguments=arguments
        )

    def get_available_tools(self, role: str) -> Dict[str, List[str]]:
        """Get all available tools for a role."""
        return self.mapper.get_all_tools_for_role(role)
```

---

## Security Considerations

### 1. Tool Permissions
- Each role has explicit whitelist of allowed tools
- Attempting to use unauthorized tool raises `PermissionError`
- Audit log of all tool executions

### 2. Authentication
- GitHub requires `GITHUB_TOKEN` environment variable
- Jira requires `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`
- Tokens stored securely, never in code

### 3. Rate Limiting
- Implement rate limits per role
- Track tool usage metrics
- Alert on unusual patterns

### 4. Audit Trail
```python
class ToolExecutionLog(Base):
    __tablename__ = "tool_execution_logs"

    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    squad_member_id = Column(UUID, ForeignKey("squad_members.id"))
    role = Column(String)
    server = Column(String)
    tool = Column(String)
    arguments = Column(JSONB)
    result = Column(JSONB)
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
```

---

## Environment Variables Required

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=xxxxxxxxxxxxx

# MCP Configuration
MCP_CONFIG_PATH=/path/to/mcp_tool_mapping.yaml  # Optional
```

---

## Testing Strategy

### 1. Unit Tests
```python
# test_mcp_tool_mapper.py
def test_backend_dev_has_git_access():
    mapper = MCPToolMapper()
    servers = mapper.get_servers_for_role("backend_developer")
    assert "git" in servers

def test_designer_cannot_use_git():
    mapper = MCPToolMapper()
    assert not mapper.can_use_tool("designer", "git", "git_commit")
```

### 2. Integration Tests
```python
# test_agent_mcp_service.py
@pytest.mark.asyncio
async def test_backend_dev_can_commit():
    service = AgentMCPService()
    await service.initialize_agent_tools("backend_developer")

    result = await service.execute_tool(
        role="backend_developer",
        server="git",
        tool="git_status",
        arguments={}
    )

    assert result is not None
```

### 3. E2E Tests
- Create full workflow: ticket → code → PR → review → merge
- Test with real GitHub/Jira accounts (test environment)
- Verify permission boundaries

---

## Migration Plan

### Phase 1: Core Infrastructure (Week 1)
- ✅ Design tool mapping (this document)
- Create `MCPToolMapper` class
- Create `AgentMCPService` class
- Write unit tests

### Phase 2: Agent Integration (Week 2)
- Update `AgnoSquadAgent._prepare_tools()` to load MCP tools
- Initialize MCP connections on agent creation
- Implement tool execution in agent workflow
- Add error handling

### Phase 3: Testing (Week 3)
- Integration tests with test MCP servers
- E2E tests with real GitHub/Jira (test accounts)
- Permission boundary testing
- Performance testing

### Phase 4: Production (Week 4)
- Deploy to staging environment
- Monitor tool usage and errors
- Add audit logging dashboard
- Production rollout

---

## Future Enhancements

1. **Dynamic Tool Discovery**: Auto-detect available tools from MCP servers
2. **Tool Chaining**: Allow agents to chain multiple tools
3. **Custom Tools**: Support role-specific custom MCP servers
4. **Tool Analytics**: Dashboard showing tool usage patterns
5. **Tool Recommendations**: Suggest tools based on conversation context
6. **Multi-tenancy**: Different tool mappings per organization

---

## Related Documentation

- See `backend/integrations/mcp/CLAUDE.md` for MCP client details
- See `backend/agents/CLAUDE.md` for agent architecture
- See `AGNO_ARCHITECTURE_GUIDE.md` for Agno framework details
