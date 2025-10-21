"""
Tests for GitHub Service (PR and issue operations using PyGithub).
These are unit tests using mocks - no actual GitHub API calls.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from backend.integrations.github_service import GitHubService


@pytest.fixture
def mock_github():
    """Mock Github client."""
    with patch('backend.integrations.github_service.Github') as mock:
        yield mock


@pytest.fixture
def github_service(mock_github):
    """Create GitHubService instance with mocked client."""
    service = GitHubService(token="fake_token")
    return service


@pytest.fixture
def mock_repo():
    """Create a mock repository object."""
    repo = Mock()
    repo.name = "test-repo"
    repo.full_name = "owner/test-repo"
    repo.description = "Test repository"
    repo.html_url = "https://github.com/owner/test-repo"
    repo.default_branch = "main"
    repo.private = False
    repo.fork = False
    repo.created_at = datetime(2023, 1, 1)
    repo.updated_at = datetime(2023, 12, 1)
    repo.stargazers_count = 100
    repo.forks_count = 20
    repo.open_issues_count = 5
    repo.language = "Python"
    repo.owner = Mock(login="owner")
    return repo


@pytest.fixture
def mock_pr():
    """Create a mock pull request object."""
    pr = Mock()
    pr.number = 123
    pr.html_url = "https://github.com/owner/repo/pull/123"
    pr.title = "Test PR"
    pr.body = "Test description"
    pr.state = "open"
    pr.created_at = datetime(2023, 12, 1)
    pr.updated_at = datetime(2023, 12, 2)
    pr.head = Mock(ref="feature/test")
    pr.base = Mock(ref="main")
    pr.draft = False
    pr.mergeable = True
    pr.merged = False
    pr.user = Mock(login="testuser")
    pr.comments = 2
    pr.commits = 3
    pr.additions = 100
    pr.deletions = 50
    pr.changed_files = 5
    return pr


@pytest.fixture
def mock_issue():
    """Create a mock issue object."""
    issue = Mock()
    issue.number = 456
    issue.html_url = "https://github.com/owner/repo/issues/456"
    issue.title = "Test Issue"
    issue.body = "Test issue description"
    issue.state = "open"
    issue.created_at = datetime(2023, 12, 1)
    issue.updated_at = datetime(2023, 12, 2)
    issue.closed_at = None
    issue.user = Mock(login="testuser")
    issue.labels = []
    issue.assignees = []
    issue.comments = 1
    return issue


def test_github_service_creation(github_service):
    """Test that GitHubService can be created."""
    assert github_service is not None
    assert github_service.token == "fake_token"


@pytest.mark.asyncio
async def test_create_pull_request(github_service, mock_repo, mock_pr):
    """Test creating a pull request."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.create_pull.return_value = mock_pr

    # Create PR
    result = await github_service.create_pull_request(
        repo="owner/test-repo",
        title="Test PR",
        body="Test description",
        head="feature/test",
        base="main"
    )

    # Verify
    assert result["number"] == 123
    assert result["url"] == "https://github.com/owner/repo/pull/123"
    assert result["title"] == "Test PR"
    assert result["state"] == "open"
    assert result["head"] == "feature/test"
    assert result["base"] == "main"

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")
    mock_repo.create_pull.assert_called_once()


@pytest.mark.asyncio
async def test_get_pull_request(github_service, mock_repo, mock_pr):
    """Test getting PR details."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.return_value = mock_pr

    # Get PR
    result = await github_service.get_pull_request(
        repo="owner/test-repo",
        pr_number=123
    )

    # Verify
    assert result["number"] == 123
    assert result["title"] == "Test PR"
    assert result["state"] == "open"
    assert result["user"] == "testuser"
    assert result["comments"] == 2
    assert result["commits"] == 3

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")
    mock_repo.get_pull.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_update_pull_request(github_service, mock_repo, mock_pr):
    """Test updating a pull request."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.return_value = mock_pr

    # Update PR
    result = await github_service.update_pull_request(
        repo="owner/test-repo",
        pr_number=123,
        title="Updated Title",
        body="Updated description"
    )

    # Verify API calls
    mock_pr.edit.assert_called()


@pytest.mark.asyncio
async def test_merge_pull_request(github_service, mock_repo, mock_pr):
    """Test merging a pull request."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.return_value = mock_pr

    # Mock merge result
    merge_result = Mock()
    merge_result.merged = True
    merge_result.message = "Pull Request successfully merged"
    merge_result.sha = "abc123def456"
    mock_pr.merge.return_value = merge_result

    # Merge PR
    result = await github_service.merge_pull_request(
        repo="owner/test-repo",
        pr_number=123,
        commit_message="Merge feature",
        merge_method="squash"
    )

    # Verify
    assert result["merged"] is True
    assert result["sha"] == "abc123def456"

    # Verify API calls
    mock_pr.merge.assert_called_once_with(
        commit_message="Merge feature",
        merge_method="squash"
    )


@pytest.mark.asyncio
async def test_create_issue(github_service, mock_repo, mock_issue):
    """Test creating an issue."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.create_issue.return_value = mock_issue

    # Create issue
    result = await github_service.create_issue(
        repo="owner/test-repo",
        title="Test Issue",
        body="Issue description",
        labels=["bug"],
        assignees=["testuser"]
    )

    # Verify
    assert result["number"] == 456
    assert result["url"] == "https://github.com/owner/repo/issues/456"
    assert result["title"] == "Test Issue"
    assert result["state"] == "open"

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")
    mock_repo.create_issue.assert_called_once()


@pytest.mark.asyncio
async def test_get_issue(github_service, mock_repo, mock_issue):
    """Test getting issue details."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_issue.return_value = mock_issue

    # Get issue
    result = await github_service.get_issue(
        repo="owner/test-repo",
        issue_number=456
    )

    # Verify
    assert result["number"] == 456
    assert result["title"] == "Test Issue"
    assert result["state"] == "open"
    assert result["user"] == "testuser"

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")
    mock_repo.get_issue.assert_called_once_with(456)


@pytest.mark.asyncio
async def test_add_issue_comment(github_service, mock_repo, mock_issue):
    """Test adding a comment to an issue."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_issue.return_value = mock_issue

    # Mock comment
    mock_comment = Mock()
    mock_comment.id = 789
    mock_comment.html_url = "https://github.com/owner/repo/issues/456#issuecomment-789"
    mock_comment.body = "Test comment"
    mock_comment.user = Mock(login="testuser")
    mock_comment.created_at = datetime(2023, 12, 3)
    mock_issue.create_comment.return_value = mock_comment

    # Add comment
    result = await github_service.add_issue_comment(
        repo="owner/test-repo",
        issue_number=456,
        comment="Test comment"
    )

    # Verify
    assert result["id"] == 789
    assert result["body"] == "Test comment"
    assert result["user"] == "testuser"

    # Verify API calls
    mock_issue.create_comment.assert_called_once_with("Test comment")


@pytest.mark.asyncio
async def test_get_repository_info(github_service, mock_repo):
    """Test getting repository information."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo

    # Get repo info
    result = await github_service.get_repository_info("owner/test-repo")

    # Verify
    assert result["name"] == "test-repo"
    assert result["full_name"] == "owner/test-repo"
    assert result["description"] == "Test repository"
    assert result["default_branch"] == "main"
    assert result["stars"] == 100
    assert result["forks"] == 20
    assert result["language"] == "Python"
    assert result["owner"] == "owner"

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")


@pytest.mark.asyncio
async def test_list_pull_requests(github_service, mock_repo):
    """Test listing pull requests."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo

    # Create mock PR list
    pr1 = Mock()
    pr1.number = 1
    pr1.html_url = "https://github.com/owner/repo/pull/1"
    pr1.title = "PR 1"
    pr1.state = "open"
    pr1.created_at = datetime(2023, 12, 1)
    pr1.head = Mock(ref="feature/1")
    pr1.base = Mock(ref="main")
    pr1.user = Mock(login="user1")
    pr1.draft = False

    pr2 = Mock()
    pr2.number = 2
    pr2.html_url = "https://github.com/owner/repo/pull/2"
    pr2.title = "PR 2"
    pr2.state = "open"
    pr2.created_at = datetime(2023, 12, 2)
    pr2.head = Mock(ref="feature/2")
    pr2.base = Mock(ref="main")
    pr2.user = Mock(login="user2")
    pr2.draft = True

    mock_repo.get_pulls.return_value = [pr1, pr2]

    # List PRs
    result = await github_service.list_pull_requests(
        repo="owner/test-repo",
        state="open",
        limit=10
    )

    # Verify
    assert len(result) == 2
    assert result[0]["number"] == 1
    assert result[0]["title"] == "PR 1"
    assert result[1]["number"] == 2
    assert result[1]["draft"] is True

    # Verify API calls
    github_service.client.get_repo.assert_called_once_with("owner/test-repo")
    mock_repo.get_pulls.assert_called_once()


def test_repr(github_service):
    """Test string representation."""
    repr_str = repr(github_service)
    assert "GitHubService" in repr_str
    assert "authenticated" in repr_str


@pytest.mark.asyncio
async def test_create_pull_request_error_handling(github_service, mock_repo):
    """Test error handling when creating PR fails."""
    from github import GithubException

    # Setup mock to raise error
    github_service.client.get_repo.side_effect = GithubException(404, {"message": "Not found"})

    # Try to create PR (should raise error)
    with pytest.raises(GithubException):
        await github_service.create_pull_request(
            repo="owner/nonexistent",
            title="Test",
            body="Test",
            head="feature",
            base="main"
        )


@pytest.mark.asyncio
async def test_get_pull_request_error(github_service, mock_repo):
    """Test error when getting non-existent PR."""
    from github import GithubException

    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.side_effect = GithubException(404, {"message": "Not found"})

    with pytest.raises(GithubException):
        await github_service.get_pull_request("owner/repo", 999)


@pytest.mark.asyncio
async def test_update_pull_request_all_fields(github_service, mock_repo, mock_pr):
    """Test updating all PR fields."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.return_value = mock_pr

    # Update all fields
    result = await github_service.update_pull_request(
        repo="owner/repo",
        pr_number=123,
        title="New Title",
        body="New Body",
        state="closed",
        base="develop"
    )

    # Verify all edit calls
    assert mock_pr.edit.call_count == 4


@pytest.mark.asyncio
async def test_update_pull_request_error(github_service, mock_repo):
    """Test error when updating PR fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.side_effect = GithubException(404, {"message": "Not found"})

    with pytest.raises(GithubException):
        await github_service.update_pull_request(
            repo="owner/repo",
            pr_number=999,
            title="New Title"
        )


@pytest.mark.asyncio
async def test_merge_pull_request_error(github_service, mock_repo):
    """Test error when merging PR fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pull.side_effect = GithubException(405, {"message": "Cannot merge"})

    with pytest.raises(GithubException):
        await github_service.merge_pull_request("owner/repo", 123)


@pytest.mark.asyncio
async def test_create_issue_error(github_service, mock_repo):
    """Test error when creating issue fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.create_issue.side_effect = GithubException(422, {"message": "Validation failed"})

    with pytest.raises(GithubException):
        await github_service.create_issue(
            repo="owner/repo",
            title="Test Issue"
        )


@pytest.mark.asyncio
async def test_get_issue_error(github_service, mock_repo):
    """Test error when getting issue fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_issue.side_effect = GithubException(404, {"message": "Not found"})

    with pytest.raises(GithubException):
        await github_service.get_issue("owner/repo", 999)


@pytest.mark.asyncio
async def test_add_issue_comment_error(github_service, mock_repo, mock_issue):
    """Test error when adding comment fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_issue.return_value = mock_issue
    mock_issue.create_comment.side_effect = GithubException(403, {"message": "Forbidden"})

    with pytest.raises(GithubException):
        await github_service.add_issue_comment(
            repo="owner/repo",
            issue_number=123,
            comment="Test"
        )


@pytest.mark.asyncio
async def test_get_repository_info_error(github_service):
    """Test error when getting repository info fails."""
    from github import GithubException

    github_service.client.get_repo.side_effect = GithubException(404, {"message": "Not found"})

    with pytest.raises(GithubException):
        await github_service.get_repository_info("owner/nonexistent")


@pytest.mark.asyncio
async def test_list_pull_requests_error(github_service, mock_repo):
    """Test error when listing PRs fails."""
    from github import GithubException

    github_service.client.get_repo.return_value = mock_repo
    mock_repo.get_pulls.side_effect = GithubException(500, {"message": "Server error"})

    with pytest.raises(GithubException):
        await github_service.list_pull_requests("owner/repo")


@pytest.mark.asyncio
async def test_list_pull_requests_with_filters(github_service, mock_repo):
    """Test listing PRs with filters."""
    # Setup mock
    github_service.client.get_repo.return_value = mock_repo
    pr = Mock()
    pr.number = 1
    pr.html_url = "https://github.com/owner/repo/pull/1"
    pr.title = "Test PR"
    pr.state = "closed"
    pr.created_at = datetime(2023, 12, 1)
    pr.head = Mock(ref="feature/test")
    pr.base = Mock(ref="main")
    pr.user = Mock(login="testuser")
    pr.draft = False

    mock_repo.get_pulls.return_value = [pr]

    # List with filters
    result = await github_service.list_pull_requests(
        repo="owner/repo",
        state="closed",
        base="main",
        head="feature/test",
        limit=5
    )

    # Verify
    assert len(result) == 1
    assert result[0]["state"] == "closed"

    # Verify filters were passed
    mock_repo.get_pulls.assert_called_once_with(
        state="closed",
        base="main",
        head="feature/test"
    )
