# Phase 4: MCP Integration - UPDATED PLAN

**Date**: October 13, 2025
**Status**: 🟢 DAYS 1-2 COMPLETE | 🟡 DAY 3 IN PROGRESS
**Stack**: 100% Pure Python ✅

---

## 🎯 Current Progress

### ✅ COMPLETED (Days 1-2)

#### Day 1: MCP Client + Git Read Operations
- ✅ Installed all MCP dependencies (mcp, mcp-server-git, mcp-atlassian, PyGithub, GitPython)
- ✅ Created MCPClientManager (241 LOC, 9/9 tests passing)
- ✅ Created GitIntegration for read operations (193 LOC)
- ✅ Git operations working: read files, list files, search grep, view logs

#### Day 2: Git Write + GitHub Integration
- ✅ Created GitService with GitPython (294 LOC, 25 tests, **95% coverage**)
- ✅ Created GitHubService with PyGithub (503 LOC, 22 tests, **99% coverage**)
- ✅ **47/47 tests passing (100%)**
- ✅ Git write operations: clone, branch, commit, push
- ✅ GitHub operations: create PRs, manage issues, merge PRs
- ✅ Complete test coverage achieved

**Total Progress**: ~1,230 LOC, 47 tests, 97% coverage ✅

---

## 🎯 NEXT: Day 3 - Jira + Confluence Integration

**Goal**: Full Atlassian ticketing system integration via mcp-atlassian

**Why This is Critical**:
- Agents need to work with tickets (Jira) and documentation (Confluence)
- This completes the 2 most important tools for agent workflows
- Enables complete ticket-to-PR automation

### Tasks for Day 3

#### 1. Create JiraService (`backend/integrations/jira_service.py`)

**Features Needed**:
```python
class JiraService:
    """Jira operations via mcp-atlassian MCP server."""

    async def initialize() -> None:
        """Connect to Jira MCP server"""

    async def get_issue(issue_key: str) -> Dict:
        """Get Jira issue details"""

    async def search_issues(jql: str, max_results: int = 50) -> List[Dict]:
        """Search issues with JQL"""

    async def create_issue(project: str, summary: str, description: str, issue_type: str) -> Dict:
        """Create new Jira issue"""

    async def update_issue(issue_key: str, fields: Dict) -> Dict:
        """Update issue fields"""

    async def add_comment(issue_key: str, comment: str) -> Dict:
        """Add comment to issue"""

    async def transition_issue(issue_key: str, status: str) -> Dict:
        """Change issue status (e.g., 'In Progress', 'Done')"""

    async def assign_issue(issue_key: str, assignee: str) -> Dict:
        """Assign issue to user"""

    async def get_transitions(issue_key: str) -> List[Dict]:
        """Get available status transitions"""
```

**MCP Tools Available** (from mcp-atlassian):
- `jira-get-issue` - Get issue details
- `jira-search-issues` - Search with JQL
- `jira-create-issue` - Create new issue
- `jira-update-issue` - Update issue fields
- `jira-add-comment` - Add comment
- `jira-transition-issue` - Change status
- `jira-assign-issue` - Assign to user

#### 2. Create ConfluenceService (`backend/integrations/confluence_service.py`)

**Features Needed**:
```python
class ConfluenceService:
    """Confluence operations via mcp-atlassian MCP server."""

    async def initialize() -> None:
        """Connect to Confluence MCP server"""

    async def search_content(query: str, space: Optional[str] = None) -> List[Dict]:
        """Search Confluence content"""

    async def get_page(page_id: str) -> Dict:
        """Get page content"""

    async def get_page_by_title(space: str, title: str) -> Dict:
        """Get page by space and title"""

    async def create_page(space: str, title: str, content: str, parent_id: Optional[str] = None) -> Dict:
        """Create new page"""

    async def update_page(page_id: str, content: str, version: int) -> Dict:
        """Update page content"""
```

**MCP Tools Available** (from mcp-atlassian):
- `confluence-search` - Search content
- `confluence-get-page` - Get page details
- `confluence-get-page-by-title` - Get page by title
- `confluence-create-page` - Create page
- `confluence-update-page` - Update page

#### 3. Environment Configuration

**Add to `.env`**:
```bash
# Jira Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence Configuration (same credentials as Jira usually)
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-jira-api-token
```

**How to get Jira API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it (e.g., "Agent Squad")
4. Copy the token (save it securely!)

#### 4. Create Comprehensive Tests

**Test Files**:
- `backend/tests/test_jira_service.py` (target: 85%+ coverage)
- `backend/tests/test_confluence_service.py` (target: 85%+ coverage)

**Test Coverage**:
- ✅ Service initialization with MCP
- ✅ Get issue operations
- ✅ Search operations (JQL for Jira, text for Confluence)
- ✅ Create/update operations
- ✅ Comment operations
- ✅ Status transitions (Jira)
- ✅ Error handling for all operations
- ✅ Mock MCP server responses

#### 5. Integration Test: Ticket-to-PR Workflow

**Create**: `backend/tests/test_integration/test_ticket_to_pr.py`

```python
@pytest.mark.asyncio
async def test_complete_jira_to_pr_workflow():
    """Test complete workflow: Jira ticket → code change → GitHub PR"""

    # 1. Get Jira issue
    jira = JiraService(mcp_client, JIRA_URL, USER, TOKEN)
    await jira.initialize()
    issue = await jira.get_issue("PROJ-123")

    # 2. Search relevant code
    git = GitIntegration(mcp_client, REPO_PATH)
    await git.initialize()
    files = await git.list_files(pattern="*.py")

    # 3. Create branch and commit
    git_service = GitService()
    repo = await git_service.clone_or_open(REPO_URL, LOCAL_PATH)
    await git_service.create_branch(repo, f"fix/PROJ-123")
    # ... make changes ...
    await git_service.commit_changes(repo, f"PROJ-123: {issue['summary']}")

    # 4. Create PR
    github = GitHubService(GITHUB_TOKEN)
    pr = await github.create_pull_request(
        repo="owner/repo",
        title=f"PROJ-123: {issue['summary']}",
        body=f"Fixes {issue['key']}",
        head="fix/PROJ-123",
        base="main"
    )

    # 5. Update Jira with PR link
    await jira.add_comment("PROJ-123", f"PR created: {pr['url']}")
    await jira.transition_issue("PROJ-123", "In Review")

    assert pr["number"] > 0
    assert "url" in pr
```

---

## 📦 Implementation Checklist

### Phase 4 Day 3 Tasks

- [ ] **Create JiraService class** (targeting ~300 LOC)
  - [ ] Initialize with MCP connection
  - [ ] Implement get_issue
  - [ ] Implement search_issues (JQL)
  - [ ] Implement create_issue
  - [ ] Implement update_issue
  - [ ] Implement add_comment
  - [ ] Implement transition_issue
  - [ ] Implement assign_issue
  - [ ] Implement get_transitions
  - [ ] Error handling and logging

- [ ] **Create ConfluenceService class** (targeting ~200 LOC)
  - [ ] Initialize with MCP connection
  - [ ] Implement search_content
  - [ ] Implement get_page
  - [ ] Implement get_page_by_title
  - [ ] Implement create_page
  - [ ] Implement update_page
  - [ ] Error handling and logging

- [ ] **Create comprehensive tests** (targeting 85%+ coverage)
  - [ ] JiraService unit tests (20+ tests)
  - [ ] ConfluenceService unit tests (15+ tests)
  - [ ] Mock MCP server responses
  - [ ] Error path testing
  - [ ] Integration test for ticket-to-PR workflow

- [ ] **Update documentation**
  - [ ] Add Jira/Confluence setup instructions
  - [ ] Document API token creation
  - [ ] Add usage examples
  - [ ] Create Day 3 completion summary

---

## 🎯 Success Criteria for Day 3

- ✅ JiraService with 85%+ test coverage
- ✅ ConfluenceService with 85%+ test coverage
- ✅ All tests passing (target: 35+ new tests)
- ✅ Complete ticket-to-PR integration test
- ✅ Documentation complete
- ✅ Ready for agent integration (Day 4)

---

## 📊 Overall Phase 4 Progress

| Day | Component | Status | LOC | Tests | Coverage |
|-----|-----------|--------|-----|-------|----------|
| 1 | MCP Client + Git Read | ✅ DONE | 434 | 9 | N/A |
| 2 | Git Write + GitHub | ✅ DONE | 797 | 47 | 97% |
| **3** | **Jira + Confluence** | 🟡 IN PROGRESS | **~500** | **~35** | **85%+** |
| 4 | Agent Integration | ⏳ PENDING | ~400 | ~20 | 85%+ |
| 5 | API Endpoints | ⏳ PENDING | ~300 | ~25 | 85%+ |
| 6 | E2E Testing | ⏳ PENDING | ~200 | ~10 | N/A |
| 7 | Documentation | ⏳ PENDING | N/A | N/A | N/A |

**Current Total**: 1,231 LOC, 56 tests, 97% coverage
**Target by End of Day 3**: ~1,731 LOC, ~91 tests, ~90% coverage

---

## 🚀 Why Focus on Jira + Confluence Now?

### Critical Path for Agent Workflows

1. **Ticket Management** (Jira)
   - Agents need to read requirements from tickets
   - Update ticket status as work progresses
   - Add comments with progress updates
   - Assign tasks to team members

2. **Documentation Access** (Confluence)
   - Agents need to search existing documentation
   - Reference architecture decisions
   - Find coding standards and patterns
   - Create documentation for new features

3. **Complete Automation**
   ```
   Jira Ticket → Read Requirements → Search Confluence Docs →
   Read Git Code → Make Changes → Commit → Push →
   Create GitHub PR → Update Jira Status → Done!
   ```

### Agent Use Cases Enabled

With Jira + Confluence + Git + GitHub, agents can:

1. **Bug Fix Workflow**
   - Read bug report from Jira
   - Search for related code in Git
   - Find relevant docs in Confluence
   - Create fix branch
   - Commit and push changes
   - Create PR on GitHub
   - Update Jira with PR link
   - Transition Jira to "In Review"

2. **Feature Implementation**
   - Read feature spec from Jira
   - Search Confluence for architecture docs
   - Create feature branch
   - Implement feature
   - Create PR with tests
   - Update Jira with implementation notes

3. **Documentation Updates**
   - Detect code changes needing docs
   - Search existing Confluence pages
   - Update or create documentation
   - Link docs in Jira ticket

---

## 📝 Next Steps

**Immediate (Day 3)**:
1. Start with JiraService implementation
2. Create unit tests alongside implementation
3. Add ConfluenceService
4. Create integration test
5. Achieve 85%+ coverage
6. Document everything

**After Day 3 (Days 4-7)**:
- Connect MCP tools to agent system
- Create API endpoints for MCP operations
- Build end-to-end agent workflows
- Comprehensive testing
- Production deployment

---

**Let's build the ticket system integration! 🎫🔧**
