# Phase 4: MCP Integration - FINAL PLAN (100% Python)

**Timeline**: 7-10 days
**Status**: 🟡 READY TO START
**Stack**: 100% Pure Python

---

## 🎯 Final Technology Stack

After researching all available options, here's the **optimal 100% Python stack**:

### MCP Servers (Python)
```bash
# 1. Atlassian (Jira + Confluence) - PYTHON ✅
uv pip install mcp-atlassian
# Source: https://github.com/sooperset/mcp-atlassian
# Features: Jira issues, Confluence pages, 99.89% success rate

# 2. Git Operations - PYTHON ✅
uv pip install mcp-server-git
# Features: Read files, search, git log, git diff (read-only)
```

### Direct Python Libraries (No MCP Needed)
```bash
# 3. GitHub API - PYTHON ✅
uv pip install PyGithub
# Better to use PyGithub directly than TypeScript MCP server
# Features: PRs, issues, commits, branches, reviews

# 4. Git Write Operations - PYTHON ✅
uv pip install GitPython
# Features: Clone, branch, commit, push
# Complements read-only mcp-server-git

# 5. MCP SDK - PYTHON ✅
uv pip install "mcp[cli]"
# Official Python SDK for MCP client
```

---

## 🏗️ Architecture - 100% Pure Python

```
┌─────────────────────────────────────────────────────────────┐
│        Agent Squad Platform (Python/FastAPI)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ BaseAgent    │      │ Specialized  │                    │
│  │              │      │ Agents       │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│         ┌──────────▼──────────────────┐                    │
│         │  Integration Manager        │                    │
│         │  ┌────────────┬────────────┐│                    │
│         │  │ MCP Client │ Direct API ││                    │
│         │  └────────────┴────────────┘│                    │
│         └──────────┬──────────────────┘                    │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬────────────┐
         │           │           │            │
    ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌───▼─────┐
    │mcp-git  │ │mcp-    │ │PyGithub │ │GitPython│
    │(Python) │ │atlassian│ │(Python) │ │(Python) │
    │         │ │(Python) │ │         │ │         │
    └────┬────┘ └───┬────┘ └───┬─────┘ └───┬─────┘
         │          │          │           │
    ┌────▼────┐ ┌──▼──────┐ ┌─▼──────┐ ┌──▼──────┐
    │   Git   │ │Jira API │ │GitHub  │ │  Git    │
    │  Repos  │ │Conflu.  │ │  API   │ │ Repos   │
    └─────────┘ └─────────┘ └────────┘ └─────────┘
```

**100% Python - No Node.js!** 🐍✅

---

## 📦 Installation & Setup

### Step 1: Install All Dependencies

```bash
cd backend

# MCP Core
uv pip install "mcp[cli]"

# MCP Servers (Python)
uv pip install mcp-server-git        # Git read operations
uv pip install mcp-atlassian         # Jira + Confluence

# Direct Python APIs
uv pip install PyGithub              # GitHub API
uv pip install GitPython             # Git write operations
```

### Step 2: Add to requirements.txt

```txt
# MCP Integration
mcp[cli]>=1.2.0
mcp-server-git>=0.1.0
mcp-atlassian>=0.11.9
PyGithub>=2.1.0
GitPython>=3.1.40
```

### Step 3: Update Docker

```dockerfile
# backend/Dockerfile
RUN uv pip install \
    "mcp[cli]" \
    mcp-server-git \
    mcp-atlassian \
    PyGithub \
    GitPython
```

---

## 📅 Implementation Plan - 7 Days

### Day 1: Setup & Git Integration (Read)
**Goal**: MCP client + Git read operations working

#### Tasks

1. **Install dependencies** (see above)

2. **Create MCP Client Manager** (`backend/integrations/mcp/client.py`)
```python
from typing import Dict, List, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """Manages MCP server connections (100% Python)"""

    def __init__(self):
        self.connections: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}

    async def connect_server(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None
    ) -> ClientSession:
        """Connect to a Python MCP server via stdio"""
        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {}
        )

        read, write = await stdio_client(server_params)
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()

        self.connections[name] = session
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
        """Call a tool on MCP server"""
        if server_name not in self.connections:
            raise ValueError(f"Server {server_name} not connected")

        session = self.connections[server_name]
        return await session.call_tool(tool_name, arguments)

    async def disconnect_all(self):
        """Cleanup all connections"""
        for name in list(self.connections.keys()):
            session = self.connections[name]
            await session.__aexit__(None, None, None)
            del self.connections[name]
```

3. **Create Git Integration** (`backend/integrations/git_integration.py`)
```python
from typing import Optional, List
from .mcp.client import MCPClientManager

class GitIntegration:
    """Git operations via mcp-server-git (Python)"""

    def __init__(self, mcp_client: MCPClientManager, repo_path: str):
        self.client = mcp_client
        self.repo_path = repo_path
        self.server_name = "git"

    async def initialize(self):
        """Connect to Git MCP server"""
        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-server-git", "--repository", self.repo_path]
        )

    async def read_file(self, file_path: str, ref: str = "HEAD") -> str:
        """Read file from Git"""
        result = await self.client.call_tool(
            self.server_name,
            "git_show",
            {"path": file_path, "ref": ref}
        )
        return result.content[0].text

    async def list_files(self, pattern: Optional[str] = None) -> List[str]:
        """List files in repo"""
        result = await self.client.call_tool(
            self.server_name,
            "git_ls_files",
            {"pattern": pattern} if pattern else {}
        )
        return result.content[0].text.split("\n")

    async def search_grep(self, pattern: str) -> str:
        """Search code with git grep"""
        result = await self.client.call_tool(
            self.server_name,
            "git_grep",
            {"pattern": pattern}
        )
        return result.content[0].text

    async def get_log(self, max_count: int = 10) -> str:
        """Get commit history"""
        result = await self.client.call_tool(
            self.server_name,
            "git_log",
            {"max_count": max_count}
        )
        return result.content[0].text
```

**Deliverables Day 1:**
- ✅ MCP client manager working
- ✅ Git read operations functional
- ✅ Can read files, search code, view history

---

### Day 2: Git Write Operations + GitHub
**Goal**: Enable branch creation, commits, PRs

#### Tasks

1. **Git Write Service** (`backend/integrations/git_service.py`)
```python
from git import Repo
from typing import List, Optional

class GitService:
    """Git write operations via GitPython"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo: Optional[Repo] = None

    def clone_or_open(self, clone_url: Optional[str] = None):
        """Clone or open existing repo"""
        if os.path.exists(self.repo_path):
            self.repo = Repo(self.repo_path)
        elif clone_url:
            self.repo = Repo.clone_from(clone_url, self.repo_path)

    def create_branch(self, branch_name: str, from_branch: str = "main") -> str:
        """Create new branch"""
        self.repo.git.checkout(from_branch)
        new_branch = self.repo.create_head(branch_name)
        new_branch.checkout()
        return branch_name

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> str:
        """Commit changes"""
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)
        commit = self.repo.index.commit(message)
        return commit.hexsha

    def push(self, branch: Optional[str] = None, remote: str = "origin"):
        """Push to remote"""
        branch = branch or self.repo.active_branch.name
        self.repo.remote(remote).push(branch)
```

2. **GitHub Service** (`backend/integrations/github_service.py`)
```python
from github import Github, GithubException
from typing import Dict, Optional

class GitHubService:
    """GitHub API via PyGithub"""

    def __init__(self, token: str):
        self.client = Github(token)

    def create_pull_request(
        self,
        repo: str,  # "owner/repo"
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict:
        """Create PR"""
        try:
            gh_repo = self.client.get_repo(repo)
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            return {
                "success": True,
                "number": pr.number,
                "url": pr.html_url
            }
        except GithubException as e:
            return {"success": False, "error": str(e)}

    def get_issue(self, repo: str, issue_number: int) -> Dict:
        """Get issue details"""
        gh_repo = self.client.get_repo(repo)
        issue = gh_repo.get_issue(issue_number)
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state
        }

    def create_issue(self, repo: str, title: str, body: str) -> Dict:
        """Create new issue"""
        gh_repo = self.client.get_repo(repo)
        issue = gh_repo.create_issue(title=title, body=body)
        return {"number": issue.number, "url": issue.html_url}
```

**Deliverables Day 2:**
- ✅ Git write operations working
- ✅ GitHub PR creation working
- ✅ GitHub issue management

---

### Day 3: Jira + Confluence Integration
**Goal**: Full Atlassian integration via mcp-atlassian

#### Tasks

1. **Jira Integration** (`backend/integrations/jira_integration.py`)
```python
from typing import List, Dict, Any
from .mcp.client import MCPClientManager

class JiraIntegration:
    """Jira operations via mcp-atlassian (Python)"""

    def __init__(
        self,
        mcp_client: MCPClientManager,
        jira_url: str,
        username: str,
        api_token: str
    ):
        self.client = mcp_client
        self.server_name = "jira"
        self.config = {
            "JIRA_URL": jira_url,
            "JIRA_USERNAME": username,
            "JIRA_API_TOKEN": api_token
        }

    async def initialize(self):
        """Connect to Jira MCP server"""
        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-atlassian"],
            env=self.config
        )

    async def get_issue(self, issue_key: str) -> Dict:
        """Get issue details"""
        result = await self.client.call_tool(
            self.server_name,
            "jira-get-issue",
            {"key": issue_key}
        )
        return result.content[0].text

    async def search_issues(self, jql: str, max_results: int = 50) -> List[Dict]:
        """Search with JQL"""
        result = await self.client.call_tool(
            self.server_name,
            "jira-search-issues",
            {"jql": jql, "maxResults": max_results}
        )
        return result.content[0].text

    async def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update issue"""
        result = await self.client.call_tool(
            self.server_name,
            "jira-update-issue",
            {"key": issue_key, "fields": fields}
        )
        return result.content[0].text

    async def add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add comment"""
        result = await self.client.call_tool(
            self.server_name,
            "jira-add-comment",
            {"key": issue_key, "body": comment}
        )
        return result.content[0].text

    async def transition_issue(self, issue_key: str, status: str) -> Dict:
        """Change issue status"""
        result = await self.client.call_tool(
            self.server_name,
            "jira-transition-issue",
            {"key": issue_key, "status": status}
        )
        return result.content[0].text
```

2. **Confluence Integration** (`backend/integrations/confluence_integration.py`)
```python
class ConfluenceIntegration:
    """Confluence via mcp-atlassian (Python)"""

    def __init__(
        self,
        mcp_client: MCPClientManager,
        confluence_url: str,
        username: str,
        api_token: str
    ):
        self.client = mcp_client
        self.server_name = "confluence"
        self.config = {
            "CONFLUENCE_URL": confluence_url,
            "CONFLUENCE_USERNAME": username,
            "CONFLUENCE_API_TOKEN": api_token
        }

    async def initialize(self):
        """Connect to Confluence MCP server"""
        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-atlassian"],
            env=self.config
        )

    async def search_content(self, query: str) -> List[Dict]:
        """Search Confluence"""
        result = await self.client.call_tool(
            self.server_name,
            "confluence-search",
            {"query": query}
        )
        return result.content[0].text

    async def get_page(self, page_id: str) -> Dict:
        """Get page content"""
        result = await self.client.call_tool(
            self.server_name,
            "confluence-get-page",
            {"id": page_id}
        )
        return result.content[0].text
```

**Deliverables Day 3:**
- ✅ Jira CRUD operations
- ✅ Confluence search & read
- ✅ Issue status transitions

---

### Day 4: Agent Integration
**Goal**: Agents can use all tools

*(See PHASE_4_PYTHON_MCP_PLAN.md Day 4 - same implementation)*

---

### Day 5: End-to-End Workflow
**Goal**: Complete Jira → Code → PR workflow

```python
# backend/workflows/ticket_to_pr.py

async def execute_jira_to_pr_workflow(
    jira_ticket: str,
    github_repo: str,
    git_repo_path: str
):
    """
    Complete workflow: Jira ticket → code change → GitHub PR
    100% PYTHON!
    """

    mcp_client = MCPClientManager()

    # Initialize all integrations
    jira = JiraIntegration(mcp_client, JIRA_URL, USER, TOKEN)
    git_mcp = GitIntegration(mcp_client, git_repo_path)
    git_service = GitService(git_repo_path)
    github = GitHubService(GITHUB_TOKEN)

    await jira.initialize()
    await git_mcp.initialize()

    try:
        # 1. Get Jira ticket
        ticket = await jira.get_issue(jira_ticket)

        # 2. Search relevant code
        search_results = await git_mcp.search_grep("auth")

        # 3. Read files
        code = await git_mcp.read_file("src/auth.py")

        # 4. Create branch
        branch_name = f"fix/{jira_ticket.lower()}"
        git_service.create_branch(branch_name)

        # 5. Make changes (agent-driven)
        # ... agent modifies files ...

        # 6. Commit
        commit_hash = git_service.commit_changes(
            f"{jira_ticket}: {ticket['summary']}"
        )

        # 7. Push
        git_service.push(branch_name)

        # 8. Create PR
        pr = github.create_pull_request(
            github_repo,
            f"{jira_ticket}: {ticket['summary']}",
            f"Fixes {jira_ticket}",
            branch_name
        )

        # 9. Update Jira
        await jira.add_comment(jira_ticket, f"PR: {pr['url']}")
        await jira.transition_issue(jira_ticket, "In Review")

        return pr

    finally:
        await mcp_client.disconnect_all()
```

---

### Day 6-7: API, Testing, Documentation

*(Same as previous plans - see PHASE_4_PYTHON_MCP_PLAN.md)*

---

## 📊 Final Stack Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| **Git Read** | mcp-server-git (Python) | MCP standard, read-only |
| **Git Write** | GitPython | Full control, Python native |
| **GitHub** | PyGithub | Direct API, simpler than MCP |
| **Jira** | mcp-atlassian (Python) | Best Python Jira MCP |
| **Confluence** | mcp-atlassian (Python) | Bonus: included with Jira |
| **MCP Client** | mcp SDK (Python) | Official SDK |

**Result: 100% Python, Zero Node.js!** 🎉🐍

---

## ✅ Success Criteria

- ✅ Read files from Git repos
- ✅ Create branches and commits
- ✅ Push to remote
- ✅ Create GitHub PRs
- ✅ Manage Jira tickets
- ✅ Search Confluence docs
- ✅ End-to-end: Jira → Code → PR
- ✅ All Python, no Node.js
- ✅ 50+ tests passing
- ✅ 80%+ coverage

---

**Ready to start Phase 4 with 100% Python!** 🚀
