"""
Tests for Jira Service (Jira operations using mcp-atlassian).
Tests issue management, search, comments, and transitions.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.integrations.jira_service import JiraService
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
def jira_service(mcp_client):
    """Create JiraService instance."""
    return JiraService(
        mcp_client,
        "https://company.atlassian.net",
        "user@company.com",
        "fake_token"
    )


@pytest.fixture
def mock_issue():
    """Create mock Jira issue."""
    return {
        "key": "PROJ-123",
        "fields": {
            "summary": "Test issue",
            "description": "Test description",
            "status": {"name": "Open"},
            "assignee": {"name": "testuser"},
            "priority": {"name": "High"}
        }
    }


@pytest.fixture
def mock_mcp_response():
    """Create mock MCP response."""
    response = Mock()
    response.content = [Mock()]
    response.content[0].text = '{"success": true}'
    return response


def test_jira_service_creation(jira_service):
    """Test that JiraService can be created."""
    assert jira_service is not None
    assert jira_service.jira_url == "https://company.atlassian.net"
    assert jira_service.username == "user@company.com"
    assert not jira_service._initialized


@pytest.mark.asyncio
async def test_initialize(jira_service, mcp_client):
    """Test Jira service initialization."""
    await jira_service.initialize()

    assert jira_service._initialized
    mcp_client.connect_server.assert_called_once()

    # Verify environment was configured
    call_args = mcp_client.connect_server.call_args
    assert call_args[1]["env"]["JIRA_URL"] == "https://company.atlassian.net"
    assert call_args[1]["env"]["JIRA_USERNAME"] == "user@company.com"
    assert call_args[1]["env"]["JIRA_API_TOKEN"] == "fake_token"


@pytest.mark.asyncio
async def test_initialize_already_initialized(jira_service, mcp_client):
    """Test initializing when already initialized."""
    await jira_service.initialize()

    # Reset mock
    mcp_client.connect_server.reset_mock()

    # Try to initialize again
    await jira_service.initialize()

    # Should not call connect_server again
    mcp_client.connect_server.assert_not_called()


@pytest.mark.asyncio
async def test_get_issue(jira_service, mcp_client, mock_issue):
    """Test getting Jira issue."""
    await jira_service.initialize()

    # Setup mock response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_issue))]
    )

    result = await jira_service.get_issue("PROJ-123")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-get-issue",
        {"key": "PROJ-123"}
    )


@pytest.mark.asyncio
async def test_get_issue_not_initialized(jira_service):
    """Test error when getting issue without initialization."""
    with pytest.raises(RuntimeError, match="not initialized"):
        await jira_service.get_issue("PROJ-123")


@pytest.mark.asyncio
async def test_search_issues(jira_service, mcp_client):
    """Test searching Jira issues with JQL."""
    await jira_service.initialize()

    # Setup mock response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='[{"key": "PROJ-123"}]')]
    )

    result = await jira_service.search_issues(
        "project = PROJ AND status = Open",
        max_results=10
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-search-issues",
        {
            "jql": "project = PROJ AND status = Open",
            "maxResults": 10,
            "startAt": 0
        }
    )


@pytest.mark.asyncio
async def test_search_issues_with_pagination(jira_service, mcp_client):
    """Test searching with pagination."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='[]')]
    )

    await jira_service.search_issues(
        "project = PROJ",
        max_results=25,
        start_at=50
    )

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["maxResults"] == 25
    assert call_args["startAt"] == 50


@pytest.mark.asyncio
async def test_create_issue(jira_service, mcp_client):
    """Test creating Jira issue."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"key": "PROJ-456"}')]
    )

    result = await jira_service.create_issue(
        project="PROJ",
        summary="New issue",
        description="Issue description",
        issue_type="Bug"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once()

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["fields"]["project"]["key"] == "PROJ"
    assert call_args["fields"]["summary"] == "New issue"
    assert call_args["fields"]["issuetype"]["name"] == "Bug"


@pytest.mark.asyncio
async def test_create_issue_with_optional_fields(jira_service, mcp_client):
    """Test creating issue with optional fields."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"key": "PROJ-456"}')]
    )

    result = await jira_service.create_issue(
        project="PROJ",
        summary="New issue",
        description="Description",
        issue_type="Task",
        priority="High",
        labels=["backend", "bug"],
        assignee="testuser"
    )

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["fields"]["priority"]["name"] == "High"
    assert call_args["fields"]["labels"] == ["backend", "bug"]
    assert call_args["fields"]["assignee"]["name"] == "testuser"


@pytest.mark.asyncio
async def test_update_issue(jira_service, mcp_client):
    """Test updating Jira issue."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"success": true}')]
    )

    result = await jira_service.update_issue(
        "PROJ-123",
        {"description": "Updated description"}
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-update-issue",
        {
            "key": "PROJ-123",
            "fields": {"description": "Updated description"}
        }
    )


@pytest.mark.asyncio
async def test_add_comment(jira_service, mcp_client):
    """Test adding comment to issue."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "12345"}')]
    )

    result = await jira_service.add_comment(
        "PROJ-123",
        "This is a comment"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-add-comment",
        {
            "key": "PROJ-123",
            "body": "This is a comment"
        }
    )


@pytest.mark.asyncio
async def test_transition_issue(jira_service, mcp_client):
    """Test transitioning issue status."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"success": true}')]
    )

    result = await jira_service.transition_issue(
        "PROJ-123",
        "In Progress"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-transition-issue",
        {
            "key": "PROJ-123",
            "status": "In Progress"
        }
    )


@pytest.mark.asyncio
async def test_assign_issue(jira_service, mcp_client):
    """Test assigning issue to user."""
    await jira_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"success": true}')]
    )

    result = await jira_service.assign_issue(
        "PROJ-123",
        "testuser"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-assign-issue",
        {
            "key": "PROJ-123",
            "assignee": "testuser"
        }
    )


@pytest.mark.asyncio
async def test_get_transitions(jira_service, mcp_client):
    """Test getting available transitions."""
    await jira_service.initialize()

    transitions = [
        {"id": "1", "name": "In Progress"},
        {"id": "2", "name": "Done"}
    ]

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(transitions))]
    )

    result = await jira_service.get_transitions("PROJ-123")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        jira_service.server_name,
        "jira-get-transitions",
        {"key": "PROJ-123"}
    )


@pytest.mark.asyncio
async def test_cleanup(jira_service, mcp_client):
    """Test cleanup disconnects properly."""
    await jira_service.initialize()
    server_name = jira_service.server_name

    assert jira_service._initialized

    await jira_service.cleanup()

    assert not jira_service._initialized
    mcp_client.disconnect.assert_called_once_with(server_name)


@pytest.mark.asyncio
async def test_cleanup_not_initialized(jira_service, mcp_client):
    """Test cleanup when not initialized."""
    # Should not raise error
    await jira_service.cleanup()

    mcp_client.disconnect.assert_not_called()


def test_repr(jira_service):
    """Test string representation."""
    repr_str = repr(jira_service)
    assert "JiraService" in repr_str
    assert "https://company.atlassian.net" in repr_str
    assert "not initialized" in repr_str


def test_repr_initialized(jira_service):
    """Test string representation when initialized."""
    jira_service._initialized = True
    repr_str = repr(jira_service)
    assert "initialized" in repr_str


@pytest.mark.asyncio
async def test_extract_result_with_content(jira_service):
    """Test extracting result from MCP response."""
    await jira_service.initialize()

    result = Mock()
    result.content = [Mock(text="test result")]

    extracted = jira_service._extract_result(result)
    assert extracted == "test result"


@pytest.mark.asyncio
async def test_extract_result_no_content(jira_service):
    """Test extracting result with no content."""
    await jira_service.initialize()

    result = "direct result"
    extracted = jira_service._extract_result(result)
    assert extracted == "direct result"
