"""
Integration Test: Complete Ticket-to-PR Workflow
Tests the full workflow from Jira ticket to GitHub PR.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

from backend.integrations.jira_service import JiraService
from backend.integrations.confluence_service import ConfluenceService
from backend.integrations.git_integration import GitIntegration
from backend.integrations.git_service import GitService
from backend.integrations.github_service import GitHubService
from backend.integrations.mcp.client import MCPClientManager


@pytest.fixture
def mcp_client():
    """Create MCP client mock."""
    client = Mock(spec=MCPClientManager)
    client.connect_server = AsyncMock()
    client.call_tool = AsyncMock()
    client.disconnect = AsyncMock()
    return client


@pytest.fixture
def mock_jira_issue():
    """Mock Jira issue for workflow."""
    return {
        "key": "PROJ-123",
        "fields": {
            "summary": "Fix authentication bug",
            "description": "Users cannot log in with OAuth",
            "status": {"name": "Open"},
            "priority": {"name": "High"}
        }
    }


@pytest.fixture
def mock_confluence_page():
    """Mock Confluence page for documentation."""
    return {
        "id": "123456",
        "title": "Authentication Architecture",
        "body": {
            "storage": {
                "value": "<p>OAuth flow uses JWT tokens...</p>"
            }
        }
    }


@pytest.fixture
def temp_repo():
    """Create temporary Git repository."""
    from git import Repo

    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)

    # Configure git
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme = Path(temp_dir) / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    yield repo

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_complete_ticket_to_pr_workflow(
    mcp_client,
    mock_jira_issue,
    mock_confluence_page,
    temp_repo
):
    """
    Test complete workflow: Jira ticket → Confluence docs → Git changes → GitHub PR → Jira update

    Workflow Steps:
    1. Get Jira issue details
    2. Search Confluence for relevant documentation
    3. Create feature branch in Git
    4. Make code changes and commit
    5. Push branch to GitHub
    6. Create GitHub PR
    7. Update Jira with PR link and status
    """

    # ==================== Step 1: Get Jira Issue ====================
    jira = JiraService(
        mcp_client,
        "https://company.atlassian.net",
        "test@example.com",
        "fake_token"
    )

    await jira.initialize()

    # Mock Jira issue response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_jira_issue))]
    )

    issue = await jira.get_issue("PROJ-123")

    assert issue is not None
    assert "PROJ-123" in str(issue)
    print(f"✅ Step 1: Retrieved Jira issue PROJ-123")

    # ==================== Step 2: Search Confluence Docs ====================
    confluence = ConfluenceService(
        mcp_client,
        "https://company.atlassian.net/wiki",
        "test@example.com",
        "fake_token"
    )

    await confluence.initialize()

    # Mock Confluence search response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='[{"id": "123456", "title": "Authentication Architecture"}]')]
    )

    docs = await confluence.search_content("authentication", space="DEV")

    assert docs is not None
    print(f"✅ Step 2: Found relevant Confluence documentation")

    # Get full page content
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_confluence_page))]
    )

    page = await confluence.get_page("123456")
    assert page is not None
    print(f"✅ Step 2b: Retrieved Confluence page details")

    # ==================== Step 3: Create Feature Branch ====================
    git_service = GitService()

    branch_name = f"fix/PROJ-123-authentication-bug"
    await git_service.create_branch(temp_repo, branch_name)

    # Verify we're on the new branch
    assert temp_repo.active_branch.name == branch_name
    print(f"✅ Step 3: Created feature branch: {branch_name}")

    # ==================== Step 4: Make Changes and Commit ====================
    # Simulate code changes
    auth_file = Path(temp_repo.working_dir) / "auth.py"
    auth_file.write_text("""
def authenticate_user(token):
    '''Fix OAuth authentication flow'''
    # Fixed: Properly validate JWT tokens
    if validate_jwt(token):
        return get_user_from_token(token)
    return None
""")

    # Commit changes
    commit_message = f"PROJ-123: Fix authentication bug\n\nFixed OAuth authentication flow to properly validate JWT tokens.\n\nFixes PROJ-123"
    sha = await git_service.commit_changes(temp_repo, commit_message)

    assert sha is not None
    assert len(sha) == 40  # SHA-1 hash
    print(f"✅ Step 4: Committed changes (SHA: {sha[:7]})")

    # ==================== Step 5: Create GitHub PR ====================
    with patch('backend.integrations.github_service.Github') as mock_github:
        github = GitHubService("fake_github_token")

        # Mock GitHub repo and PR
        from datetime import datetime
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.number = 456
        mock_pr.html_url = "https://github.com/company/repo/pull/456"
        mock_pr.state = "open"
        mock_pr.title = "PROJ-123: Fix authentication bug"
        mock_pr.body = "Fixes PROJ-123"
        mock_pr.head.ref = branch_name
        mock_pr.base.ref = "main"
        mock_pr.created_at = datetime(2025, 10, 13, 10, 0, 0)
        mock_pr.updated_at = datetime(2025, 10, 13, 10, 0, 0)

        mock_repo.create_pull.return_value = mock_pr
        github.client.get_repo.return_value = mock_repo

        # Create PR
        pr = await github.create_pull_request(
            repo="company/repo",
            title="PROJ-123: Fix authentication bug",
            body=f"Fixes OAuth authentication bug.\n\nJira Issue: PROJ-123\n\nChanges:\n- Fixed JWT token validation\n- Updated authentication flow",
            head=branch_name,
            base="main"
        )

        assert pr["number"] == 456
        assert pr["url"] == "https://github.com/company/repo/pull/456"
        print(f"✅ Step 5: Created GitHub PR #{pr['number']}")

    # ==================== Step 6: Update Jira with PR Link ====================
    # Add PR link as comment
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "comment-123"}')]
    )

    pr_url = pr["url"]
    comment = f"Pull request created: {pr_url}\n\nThe fix has been implemented and is ready for review."

    comment_result = await jira.add_comment("PROJ-123", comment)
    assert comment_result is not None
    print(f"✅ Step 6: Added PR link to Jira ticket")

    # ==================== Step 7: Transition Jira Status ====================
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"success": true}')]
    )

    transition_result = await jira.transition_issue("PROJ-123", "In Review")
    assert transition_result is not None
    print(f"✅ Step 7: Transitioned Jira status to 'In Review'")

    # ==================== Cleanup ====================
    await jira.cleanup()
    await confluence.cleanup()

    print("\n🎉 Complete ticket-to-PR workflow test PASSED!")
    print("\nWorkflow Summary:")
    print("  1. ✅ Retrieved Jira issue PROJ-123")
    print("  2. ✅ Searched Confluence documentation")
    print("  3. ✅ Created feature branch")
    print("  4. ✅ Made code changes and committed")
    print("  5. ✅ Created GitHub PR #456")
    print("  6. ✅ Added PR link to Jira")
    print("  7. ✅ Updated Jira status to 'In Review'")


@pytest.mark.asyncio
async def test_workflow_with_git_read_operations(mcp_client, mock_jira_issue):
    """
    Test workflow using Git read operations to find relevant files.

    Demonstrates using GitIntegration (MCP) for code search before making changes.
    """

    # Get Jira issue
    jira = JiraService(
        mcp_client,
        "https://company.atlassian.net",
        "test@example.com",
        "fake_token"
    )

    await jira.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_jira_issue))]
    )

    issue = await jira.get_issue("PROJ-123")
    assert issue is not None
    print("✅ Retrieved Jira issue")

    # Use GitIntegration to search for authentication-related files
    git_mcp = GitIntegration(mcp_client, "/workspace/repo")
    await git_mcp.initialize()

    # Mock search results
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text="backend/core/auth.py\nbackend/api/v1/endpoints/auth.py")]
    )

    auth_files = await git_mcp.search_grep("def authenticate", path="*.py")
    assert auth_files is not None
    print("✅ Found authentication-related files via grep")

    # Mock file content
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text="def authenticate_user(token): ...")]
    )

    file_content = await git_mcp.read_file("backend/core/auth.py")
    assert file_content is not None
    print("✅ Read authentication file content")

    # At this point, an agent would:
    # 1. Analyze the code
    # 2. Identify the bug
    # 3. Create a fix
    # 4. Use GitService to commit and push
    # 5. Use GitHubService to create PR
    # 6. Update Jira

    await jira.cleanup()
    await git_mcp.cleanup()

    print("\n🎉 Workflow with Git read operations test PASSED!")


@pytest.mark.asyncio
async def test_error_handling_in_workflow(mcp_client):
    """Test error handling when services are not initialized."""

    jira = JiraService(
        mcp_client,
        "https://company.atlassian.net",
        "test@example.com",
        "fake_token"
    )

    # Try to use service without initialization
    with pytest.raises(RuntimeError, match="not initialized"):
        await jira.get_issue("PROJ-123")

    print("✅ Proper error handling for uninitialized service")


@pytest.mark.asyncio
async def test_multi_service_cleanup(mcp_client):
    """Test cleanup of multiple services."""

    jira = JiraService(mcp_client, "https://jira.com", "user", "token")
    confluence = ConfluenceService(mcp_client, "https://confluence.com", "user", "token")

    await jira.initialize()
    await confluence.initialize()

    assert jira._initialized
    assert confluence._initialized

    await jira.cleanup()
    await confluence.cleanup()

    assert not jira._initialized
    assert not confluence._initialized

    # Verify disconnect was called for each service
    assert mcp_client.disconnect.call_count == 2

    print("✅ Multiple services cleaned up properly")
