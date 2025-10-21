# Phase 4: 100% Python MCP Integration - Implementation Plan

**Timeline**: 7-10 days
**Status**: 🟡 READY TO START
**Approach**: Pure Python using Smithery.ai + Python MCP Servers

---

## 🎯 Goals - 100% Python Stack

Connect AI agents to real development tools using **pure Python implementations**:
- ✅ Python MCP SDK for client
- ✅ Python MCP servers for Git, Jira, Filesystem
- ✅ No Node.js dependencies
- ✅ Native Python tooling with `uvx`
- ✅ Leveraging Smithery.ai registry (7,600+ servers)

---

## 📚 Available Python MCP Servers

### From Smithery.ai & Community

#### 1. **Git Operations** (Python)
- **Package**: `mcp-server-git` (PyPI)
- **Installation**: `uvx mcp-server-git`
- **Tools**:
  - Read files from Git repos
  - Search Git history
  - Manipulate Git repositories
  - Commit changes
  - Branch operations

#### 2. **Jira Integration** (Python) - Multiple Options!
- **mcp-jira-python** (Kallows/mcp-jira-python)
  - delete_issue, create_jira_issue, get_issue, get_issue_attachment
- **mcp-jira** (InfinitIQ-Tech/mcp-jira)
  - Uses jira-python library
  - Full REST API integration
- **mcp-atlassian** (sooperset/mcp-atlassian)
  - Jira + Confluence support

#### 3. **Filesystem** (Python)
- **Package**: `mcp-server-filesystem`
- **Tools**:
  - Read/write local files
  - Search codebase
  - File operations

#### 4. **GitHub API** (Python available via PyGithub)
- Can build custom MCP server with PyGithub
- PR creation, issues, reviews

---

## 📦 Technology Stack - 100% Python

```bash
# MCP Core
mcp[cli]                    # Official Python MCP SDK

# MCP Servers (Python)
mcp-server-git              # Git operations
mcp-jira-python             # Jira integration
# mcp-server-filesystem     # File operations (if needed)

# Python Libraries for Custom Servers
PyGithub                    # GitHub API wrapper
jira                        # Jira Python SDK
GitPython                   # Advanced Git operations
```

---

## 🏗️ Architecture - Pure Python

```
┌─────────────────────────────────────────────────────────────┐
│              Agent Squad Platform (Python/FastAPI)           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ BaseAgent    │      │ Specialized  │                    │
│  │              │      │ Agents       │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│         ┌──────────▼──────────┐                            │
│         │  MCP Client Manager │  ◄── Python mcp SDK        │
│         │  (Python)           │                            │
│         └──────────┬──────────┘                            │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │ MCP Protocol (stdio)
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼─────┐ ┌──▼──────┐ ┌──▼────────┐
    │ Git MCP  │ │ Jira    │ │ GitHub    │
    │ Server   │ │ MCP     │ │ MCP       │
    │ (Python) │ │ (Python)│ │ (Python)  │
    └────┬─────┘ └───┬─────┘ └───┬───────┘
         │           │           │
    ┌────▼─────┐ ┌──▼──────┐ ┌──▼────────┐
    │ GitPython│ │ jira-py │ │ PyGithub  │
    │          │ │         │ │           │
    └──────────┘ └─────────┘ └───────────┘
         │           │           │
    ┌────▼─────┐ ┌──▼──────┐ ┌──▼────────┐
    │   Git    │ │ Jira    │ │ GitHub    │
    │   Repos  │ │ API     │ │ API       │
    └──────────┘ └─────────┘ └───────────┘
```

**Key Point**: Everything runs as Python processes, connected via stdio!

---

## 📅 Day-by-Day Implementation Plan

### Day 1: Setup Python MCP Environment
**Goal**: Install all Python MCP dependencies and test basic connectivity

#### Tasks

1. **Install MCP Python SDK**
```bash
cd backend
uv pip install "mcp[cli]"
```

2. **Install Python MCP Servers**
```bash
# Git server
uv pip install mcp-server-git

# Jira server (we'll use mcp-jira-python)
# Clone and install from GitHub
git clone https://github.com/Kallows/mcp-jira-python.git /tmp/mcp-jira-python
cd /tmp/mcp-jira-python
uv pip install -e .

# Or use alternative: InfinitIQ-Tech/mcp-jira
# uv pip install git+https://github.com/InfinitIQ-Tech/mcp-jira.git
```

3. **Test MCP servers with uvx**
```bash
# Test Git server
uvx mcp-server-git --repository /path/to/test/repo

# Test with MCP inspector
npx @modelcontextprotocol/inspector uvx mcp-server-git
```

4. **Create MCP Client Manager** (`backend/integrations/mcp/client.py`)

```python
from typing import Dict, List, Optional, Any
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """
    Manages connections to multiple Python MCP servers via stdio.
    100% Python implementation - no Node.js required!
    """

    def __init__(self):
        self.connections: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._processes: Dict[str, asyncio.subprocess.Process] = {}

    async def connect_server(
        self,
        name: str,
        command: str = "uvx",  # Use uvx to run Python packages
        args: List[str] = None,
        env: Dict[str, str] = None
    ) -> ClientSession:
        """
        Connect to a Python MCP server using uvx.

        Example:
            await manager.connect_server(
                name="git",
                command="uvx",
                args=["mcp-server-git", "--repository", "/path/to/repo"]
            )
        """
        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {}
        )

        # Create stdio transport
        read, write = await stdio_client(server_params)

        # Create session
        session = ClientSession(read, write)
        await session.__aenter__()

        # Initialize connection
        await session.initialize()

        # Store connection
        self.connections[name] = session

        # List available tools
        tools_result = await session.list_tools()
        self.tools[name] = {
            tool.name: tool.model_dump() for tool in tools_result.tools
        }

        return session

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on a specific MCP server"""
        if server_name not in self.connections:
            raise ValueError(f"Server {server_name} not connected")

        session = self.connections[server_name]
        result = await session.call_tool(tool_name, arguments)

        return result

    def get_available_tools(self, server_name: Optional[str] = None) -> Dict:
        """Get list of available tools from all or specific server"""
        if server_name:
            return self.tools.get(server_name, {})
        return self.tools

    async def disconnect(self, server_name: str):
        """Disconnect from a server"""
        if server_name in self.connections:
            session = self.connections[server_name]
            await session.__aexit__(None, None, None)
            del self.connections[server_name]
            del self.tools[server_name]

    async def disconnect_all(self):
        """Disconnect from all servers"""
        for name in list(self.connections.keys()):
            await self.disconnect(name)
```

**Deliverables:**
- ✅ MCP SDK installed
- ✅ Python MCP servers installed (git, jira)
- ✅ MCPClientManager working
- ✅ Basic connectivity tested

---

### Day 2: Git Integration (Pure Python)
**Goal**: Enable agents to read/write code via Git using Python MCP server

#### Tasks

1. **Create Git Integration Wrapper** (`backend/integrations/mcp/git_integration.py`)

```python
from typing import Optional, List, Dict, Any
from .client import MCPClientManager

class GitIntegration:
    """
    Git operations using Python mcp-server-git.
    100% Python - no Node.js required!
    """

    def __init__(self, mcp_client: MCPClientManager, repo_path: str):
        self.client = mcp_client
        self.server_name = "git"
        self.repo_path = repo_path

    async def initialize(self):
        """Connect to Git MCP server for this repository"""
        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-server-git", "--repository", self.repo_path]
        )

    async def read_file(self, file_path: str, ref: str = "HEAD") -> str:
        """Read a file from the Git repository"""
        result = await self.client.call_tool(
            self.server_name,
            "git_show",
            {
                "path": file_path,
                "ref": ref
            }
        )
        return result.content[0].text

    async def list_files(
        self,
        directory: str = ".",
        pattern: Optional[str] = None
    ) -> List[str]:
        """List files in the repository"""
        result = await self.client.call_tool(
            self.server_name,
            "git_ls_files",
            {
                "directory": directory,
                "pattern": pattern
            }
        )
        return result.content[0].text.split("\n")

    async def search_grep(self, pattern: str, path: Optional[str] = None) -> str:
        """Search for pattern in repository using git grep"""
        result = await self.client.call_tool(
            self.server_name,
            "git_grep",
            {
                "pattern": pattern,
                "path": path
            }
        )
        return result.content[0].text

    async def get_diff(self, ref1: str = "HEAD", ref2: Optional[str] = None) -> str:
        """Get diff between commits"""
        result = await self.client.call_tool(
            self.server_name,
            "git_diff",
            {
                "ref1": ref1,
                "ref2": ref2
            }
        )
        return result.content[0].text

    async def get_log(self, max_count: int = 10, path: Optional[str] = None) -> str:
        """Get commit history"""
        result = await self.client.call_tool(
            self.server_name,
            "git_log",
            {
                "max_count": max_count,
                "path": path
            }
        )
        return result.content[0].text

    async def commit(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """
        Commit changes (if server supports it).
        Note: mcp-server-git is read-only, we may need to use GitPython directly.
        """
        # For write operations, we'll use GitPython directly
        # See Day 3 for write operations
        raise NotImplementedError("Use GitService for write operations")

    async def cleanup(self):
        """Disconnect from Git MCP server"""
        await self.client.disconnect(self.server_name)
```

2. **Create Git Service for Write Operations** (`backend/services/git_service.py`)

```python
from typing import List, Optional, Dict
from git import Repo
from git.exc import GitCommandError
import os

class GitService:
    """
    Git write operations using GitPython.
    Complements read-only mcp-server-git.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo: Optional[Repo] = None

    def clone_or_open(self, clone_url: Optional[str] = None):
        """Clone repository or open existing"""
        if os.path.exists(self.repo_path):
            self.repo = Repo(self.repo_path)
        elif clone_url:
            self.repo = Repo.clone_from(clone_url, self.repo_path)
        else:
            raise ValueError("Repository doesn't exist and no clone URL provided")

    def create_branch(self, branch_name: str, from_branch: str = "main") -> str:
        """Create a new branch"""
        if not self.repo:
            raise ValueError("Repository not initialized")

        # Checkout base branch
        self.repo.git.checkout(from_branch)

        # Create and checkout new branch
        new_branch = self.repo.create_head(branch_name)
        new_branch.checkout()

        return branch_name

    def commit_changes(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> str:
        """Commit changes to repository"""
        if not self.repo:
            raise ValueError("Repository not initialized")

        # Stage files
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)  # Add all changes

        # Commit
        commit = self.repo.index.commit(message)
        return commit.hexsha

    def push(self, branch: Optional[str] = None, remote: str = "origin"):
        """Push changes to remote"""
        if not self.repo:
            raise ValueError("Repository not initialized")

        branch = branch or self.repo.active_branch.name
        origin = self.repo.remote(remote)
        origin.push(branch)

    def create_pr_via_api(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict:
        """
        Create PR via GitHub API (using PyGithub).
        Implementation in Day 3.
        """
        raise NotImplementedError("See Day 3 for GitHub PR creation")
```

3. **Add GitPython dependency**
```bash
uv pip install GitPython
```

**Deliverables:**
- ✅ GitIntegration class (read operations via MCP)
- ✅ GitService class (write operations via GitPython)
- ✅ Read files from Git repos
- ✅ Search Git history
- ✅ Create branches and commits

**Test Cases:**
```python
# Test reading from Git
git = GitIntegration(mcp_client, "/path/to/repo")
await git.initialize()

content = await git.read_file("README.md")
files = await git.list_files()
matches = await git.search_grep("TODO")

# Test writing to Git
git_service = GitService("/path/to/repo")
git_service.clone_or_open()
git_service.create_branch("feature/new-feature")
# ... make changes ...
git_service.commit_changes("Add new feature")
git_service.push()
```

---

### Day 3: Jira Integration (Pure Python)
**Goal**: Enable agents to work with Jira tickets using Python MCP server

#### Tasks

1. **Install Jira MCP Server** (Choose one):

**Option A: Kallows/mcp-jira-python** (Recommended)
```bash
git clone https://github.com/Kallows/mcp-jira-python.git /tmp/mcp-jira-python
cd /tmp/mcp-jira-python
uv pip install -e .
```

**Option B: InfinitIQ-Tech/mcp-jira**
```bash
uv pip install git+https://github.com/InfinitIQ-Tech/mcp-jira.git
```

2. **Create Jira Integration Wrapper** (`backend/integrations/mcp/jira_integration.py`)

```python
from typing import List, Optional, Dict, Any
from .client import MCPClientManager

class JiraIntegration:
    """
    Jira operations using Python mcp-jira MCP server.
    100% Python - no Node.js required!
    """

    def __init__(
        self,
        mcp_client: MCPClientManager,
        jira_url: str,
        jira_email: str,
        jira_api_token: str
    ):
        self.client = mcp_client
        self.server_name = "jira"
        self.jira_url = jira_url
        self.jira_email = jira_email
        self.jira_api_token = jira_api_token

    async def initialize(self):
        """Connect to Jira MCP server"""
        await self.client.connect_server(
            name=self.server_name,
            command="python",  # or "uvx" if packaged
            args=["-m", "mcp_jira"],  # Adjust based on server
            env={
                "JIRA_URL": self.jira_url,
                "JIRA_EMAIL": self.jira_email,
                "JIRA_API_TOKEN": self.jira_api_token
            }
        )

    async def get_issue(self, issue_key: str) -> Dict:
        """Get Jira issue details"""
        result = await self.client.call_tool(
            self.server_name,
            "get_issue",
            {"issue_key": issue_key}
        )
        return result.content[0].text

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        **kwargs
    ) -> Dict:
        """Create a new Jira issue"""
        result = await self.client.call_tool(
            self.server_name,
            "create_jira_issue",
            {
                "project_key": project_key,
                "summary": summary,
                "description": description,
                "issue_type": issue_type,
                **kwargs
            }
        )
        return result.content[0].text

    async def update_issue_status(
        self,
        issue_key: str,
        status: str
    ) -> Dict:
        """Update issue status (transition)"""
        result = await self.client.call_tool(
            self.server_name,
            "transition_issue",
            {
                "issue_key": issue_key,
                "status": status
            }
        )
        return result.content[0].text

    async def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict:
        """Add comment to issue"""
        result = await self.client.call_tool(
            self.server_name,
            "add_comment",
            {
                "issue_key": issue_key,
                "comment": comment
            }
        )
        return result.content[0].text

    async def delete_issue(self, issue_key: str) -> Dict:
        """Delete a Jira issue"""
        result = await self.client.call_tool(
            self.server_name,
            "delete_issue",
            {"issue_key": issue_key}
        )
        return result.content[0].text

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[Dict]:
        """Search issues using JQL"""
        result = await self.client.call_tool(
            self.server_name,
            "search_issues",
            {
                "jql": jql,
                "max_results": max_results
            }
        )
        return result.content[0].text

    async def cleanup(self):
        """Disconnect from Jira MCP server"""
        await self.client.disconnect(self.server_name)
```

3. **Add GitHub PR Creation** (using PyGithub)

```bash
uv pip install PyGithub
```

```python
# backend/services/github_service.py
from github import Github, GithubException
from typing import Dict

class GitHubService:
    """GitHub API operations using PyGithub"""

    def __init__(self, token: str):
        self.client = Github(token)

    def create_pull_request(
        self,
        repo_full_name: str,  # e.g., "owner/repo"
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict:
        """Create a pull request"""
        try:
            repo = self.client.get_repo(repo_full_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "state": pr.state
            }
        except GithubException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_pull_request(self, repo_full_name: str, pr_number: int) -> Dict:
        """Get PR details"""
        repo = self.client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "url": pr.html_url,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat()
        }
```

**Deliverables:**
- ✅ JiraIntegration class
- ✅ Jira MCP server configured
- ✅ CRUD operations for Jira issues
- ✅ GitHubService for PR creation

**Test Cases:**
```python
# Test Jira
jira = JiraIntegration(mcp_client, JIRA_URL, EMAIL, TOKEN)
await jira.initialize()

issue = await jira.get_issue("PROJ-123")
new_issue = await jira.create_issue("PROJ", "Bug fix", "Description")
await jira.add_comment("PROJ-123", "Working on this")
await jira.update_issue_status("PROJ-123", "In Progress")

# Test GitHub
github = GitHubService(GITHUB_TOKEN)
pr = github.create_pull_request(
    "owner/repo",
    "Fix authentication bug",
    "This PR fixes...",
    "fix/auth-bug"
)
```

---

### Day 4: Agent MCP Integration
**Goal**: Integrate MCP tools into agent system

#### Tasks

1. **Update BaseSquadAgent** (`backend/agents/base_agent.py`)

```python
from typing import Optional, Dict, Any
from backend.integrations.mcp.client import MCPClientManager
from backend.integrations.mcp.git_integration import GitIntegration
from backend.integrations.mcp.jira_integration import JiraIntegration

class BaseSquadAgent:
    def __init__(
        self,
        # ... existing params
        mcp_client: Optional[MCPClientManager] = None,
        git_repo_path: Optional[str] = None,
        jira_config: Optional[Dict] = None
    ):
        # ... existing code
        self.mcp_client = mcp_client
        self.git: Optional[GitIntegration] = None
        self.jira: Optional[JiraIntegration] = None

        # Initialize integrations if provided
        if mcp_client and git_repo_path:
            self.git = GitIntegration(mcp_client, git_repo_path)

        if mcp_client and jira_config:
            self.jira = JiraIntegration(
                mcp_client,
                jira_config["url"],
                jira_config["email"],
                jira_config["token"]
            )

    async def initialize_tools(self):
        """Initialize MCP tool connections"""
        if self.git:
            await self.git.initialize()
        if self.jira:
            await self.jira.initialize()

    async def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        tools = []
        if self.git:
            tools.extend([
                "read_file", "list_files", "search_code",
                "get_diff", "get_log"
            ])
        if self.jira:
            tools.extend([
                "get_jira_issue", "create_jira_issue",
                "update_jira_status", "add_jira_comment"
            ])
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """Execute an MCP tool"""
        # Git tools
        if tool_name == "read_file":
            return await self.git.read_file(**kwargs)
        elif tool_name == "list_files":
            return await self.git.list_files(**kwargs)
        elif tool_name == "search_code":
            return await self.git.search_grep(**kwargs)
        elif tool_name == "get_diff":
            return await self.git.get_diff(**kwargs)
        elif tool_name == "get_log":
            return await self.git.get_log(**kwargs)

        # Jira tools
        elif tool_name == "get_jira_issue":
            return await self.jira.get_issue(**kwargs)
        elif tool_name == "create_jira_issue":
            return await self.jira.create_issue(**kwargs)
        elif tool_name == "update_jira_status":
            return await self.jira.update_issue_status(**kwargs)
        elif tool_name == "add_jira_comment":
            return await self.jira.add_comment(**kwargs)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def process_with_tools(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Process message with MCP tool access.
        Agent can request tool usage via structured response.
        """
        # Add tool descriptions to system prompt
        available_tools = await self.get_available_tools()

        tool_prompt = f"""
You have access to these tools: {', '.join(available_tools)}

To use a tool, respond with JSON:
{{
    "thought": "why I need this tool",
    "tool": "tool_name",
    "args": {{"param": "value"}}
}}

After seeing tool results, provide your final response.
"""

        # Get LLM response
        response = await self.process_message(
            message=message,
            context={**context, "tools": available_tools},
            system_prompt_addition=tool_prompt
        )

        # Check if response requests tool use
        try:
            import json
            parsed = json.loads(response)

            if "tool" in parsed and parsed["tool"]:
                # Execute tool
                tool_result = await self.execute_tool(
                    parsed["tool"],
                    **parsed.get("args", {})
                )

                # Process tool result with LLM
                follow_up = await self.process_message(
                    message=f"Tool '{parsed['tool']}' returned:\n{tool_result}\n\nProvide your analysis:",
                    context=context
                )
                return follow_up
        except json.JSONDecodeError:
            pass  # Not a tool request, return as-is

        return response

    async def cleanup_tools(self):
        """Cleanup MCP connections"""
        if self.git:
            await self.git.cleanup()
        if self.jira:
            await self.jira.cleanup()
```

2. **Update Specialized Agents**

```python
# backend/agents/specialized/backend_developer.py

class BackendDeveloperAgent(BaseSquadAgent):

    async def implement_feature(
        self,
        task_description: str,
        jira_ticket: Optional[str] = None
    ) -> str:
        """Implement a feature with MCP tool access"""

        # 1. Get Jira ticket if provided
        ticket_details = None
        if jira_ticket and self.jira:
            ticket_details = await self.jira.get_issue(jira_ticket)

        # 2. Search for relevant code
        search_results = await self.git.search_grep("class.*Auth")

        # 3. Read relevant files
        auth_code = await self.git.read_file("src/auth/service.py")

        # 4. Ask LLM to analyze and suggest implementation
        analysis = await self.process_message(
            message=f"""
Task: {task_description}
Ticket: {ticket_details}
Existing code: {auth_code[:1000]}

Please suggest implementation.
            """,
            context={}
        )

        return analysis
```

**Deliverables:**
- ✅ Tool execution in BaseSquadAgent
- ✅ Tool-aware prompts
- ✅ Specialized agents using tools
- ✅ Async tool execution

---

### Day 5: Task Execution with MCP
**Goal**: Update task execution service to use MCP tools

#### Tasks

1. **Update TaskExecutionService**

```python
# backend/services/task_execution_service.py

class TaskExecutionService:

    async def execute_with_mcp(
        self,
        task_execution_id: str,
        project_config: Dict
    ):
        """Execute task with MCP tool access (100% Python)"""

        execution = await self.get_execution(task_execution_id)

        # Initialize MCP client
        mcp_client = MCPClientManager()

        try:
            # Get project configuration
            git_repo_path = project_config.get("git_repo_path")
            jira_config = project_config.get("jira")

            # Create agent with MCP access
            agent = await self._create_agent_with_tools(
                execution.squad_id,
                mcp_client,
                git_repo_path,
                jira_config
            )

            # Initialize tools
            await agent.initialize_tools()

            # Execute task
            result = await agent.execute_task(execution.task_id)

            # Update execution
            await self.complete_execution(
                task_execution_id,
                result
            )

        finally:
            # Cleanup MCP connections
            await mcp_client.disconnect_all()

    async def _create_agent_with_tools(
        self,
        squad_id: str,
        mcp_client: MCPClientManager,
        git_repo_path: Optional[str],
        jira_config: Optional[Dict]
    ) -> BaseSquadAgent:
        """Create agent with MCP tool access"""

        # Get squad and primary agent
        squad = await self.squad_service.get_squad(squad_id)
        primary_agent_record = squad.members[0]  # PM or lead

        # Create agent instance
        agent = AgentFactory.create_agent(
            role=primary_agent_record.role,
            specialization=primary_agent_record.specialization,
            llm_provider=primary_agent_record.llm_provider,
            llm_model=primary_agent_record.llm_model,
            mcp_client=mcp_client,
            git_repo_path=git_repo_path,
            jira_config=jira_config
        )

        return agent
```

2. **Implement End-to-End Workflow**

```python
# backend/workflows/ticket_to_pr_workflow.py

async def execute_ticket_to_pr_workflow(
    jira_ticket_id: str,
    git_repo_path: str,
    github_repo: str,
    mcp_client: MCPClientManager
):
    """
    End-to-end workflow: Jira ticket → code change → PR
    100% Python!
    """

    # 1. Initialize integrations
    jira = JiraIntegration(mcp_client, JIRA_URL, EMAIL, TOKEN)
    git = GitIntegration(mcp_client, git_repo_path)
    git_service = GitService(git_repo_path)
    github = GitHubService(GITHUB_TOKEN)

    await jira.initialize()
    await git.initialize()

    try:
        # 2. Get ticket details
        ticket = await jira.get_issue(jira_ticket_id)

        # 3. Create branch
        branch_name = f"fix/{jira_ticket_id.lower()}"
        git_service.create_branch(branch_name)

        # 4. Read relevant code
        files = await git.list_files()
        # ... analyze which files to modify ...

        # 5. Make changes (manual or agent-driven)
        # ... write code ...

        # 6. Commit changes
        commit_hash = git_service.commit_changes(
            message=f"{jira_ticket_id}: {ticket['summary']}",
            files=["src/auth.py"]
        )

        # 7. Push to remote
        git_service.push(branch=branch_name)

        # 8. Create PR
        pr = github.create_pull_request(
            github_repo,
            title=f"{jira_ticket_id}: {ticket['summary']}",
            body=f"Fixes {jira_ticket_id}\n\n{ticket['description']}",
            head_branch=branch_name
        )

        # 9. Update Jira ticket
        await jira.add_comment(
            jira_ticket_id,
            f"PR created: {pr['pr_url']}"
        )
        await jira.update_issue_status(jira_ticket_id, "In Review")

        return pr

    finally:
        await jira.cleanup()
        await git.cleanup()
```

**Deliverables:**
- ✅ MCP-enabled task execution
- ✅ End-to-end workflow implementation
- ✅ Error handling
- ✅ Connection cleanup

---

### Day 6: API Endpoints & Schemas
**Goal**: Create REST API for MCP management

*(Same as original plan - see Phase 4 plan Day 6)*

---

### Day 7: Testing & Documentation
**Goal**: Comprehensive testing of Python MCP integration

#### Test Files

```python
# tests/test_mcp/test_git_integration.py
import pytest
from backend.integrations.mcp.client import MCPClientManager
from backend.integrations.mcp.git_integration import GitIntegration

@pytest.mark.asyncio
async def test_git_read_file():
    """Test reading file via Python MCP server"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, "/path/to/test/repo")

    await git.initialize()
    content = await git.read_file("README.md")

    assert "# Test Repo" in content
    await git.cleanup()

@pytest.mark.asyncio
async def test_git_search():
    """Test searching code via Python MCP server"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, "/path/to/test/repo")

    await git.initialize()
    results = await git.search_grep("TODO")

    assert len(results) > 0
    await git.cleanup()

# tests/test_mcp/test_jira_integration.py
@pytest.mark.asyncio
async def test_jira_get_issue():
    """Test getting Jira issue via Python MCP server"""
    mcp_client = MCPClientManager()
    jira = JiraIntegration(mcp_client, JIRA_URL, EMAIL, TOKEN)

    await jira.initialize()
    issue = await jira.get_issue("PROJ-123")

    assert issue["key"] == "PROJ-123"
    await jira.cleanup()

# tests/test_integration/test_e2e_workflow.py
@pytest.mark.asyncio
async def test_ticket_to_pr_workflow():
    """Test complete workflow: Jira → Git → PR (100% Python)"""
    # ... test end-to-end workflow ...
```

**Deliverables:**
- ✅ 30+ test cases
- ✅ 80%+ coverage on MCP code
- ✅ Integration tests
- ✅ Documentation

---

## 📊 Success Criteria

### Technical Requirements - 100% Python ✅
- ✅ Pure Python MCP SDK
- ✅ Python MCP servers (git, jira)
- ✅ No Node.js dependencies
- ✅ All connections via stdio
- ✅ Async/await throughout

### Functional Requirements
- ✅ Read Git repositories
- ✅ Search code history
- ✅ Create branches & commits
- ✅ Manage Jira tickets
- ✅ Create GitHub PRs
- ✅ End-to-end workflow: Jira → Code → PR

### Quality Requirements
- ✅ 50+ tests passing
- ✅ 80%+ coverage on critical paths
- ✅ Comprehensive documentation
- ✅ Error handling & cleanup

---

## 🎉 Why This Approach is Better

1. **100% Python** - No Node.js, no mixed stack
2. **Native Integration** - Everything in your Python codebase
3. **Better Control** - Can modify/extend MCP servers
4. **Easier Debugging** - Single language stack
5. **Community Support** - 7,600+ servers on Smithery.ai
6. **Standards-Based** - Uses official MCP protocol

---

**Ready to build Phase 4 with 100% Python!** 🚀🐍
