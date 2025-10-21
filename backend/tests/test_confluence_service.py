"""
Tests for Confluence Service (Confluence operations using mcp-atlassian).
Tests content search, page management, and space operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.integrations.confluence_service import ConfluenceService
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
def confluence_service(mcp_client):
    """Create ConfluenceService instance."""
    return ConfluenceService(
        mcp_client,
        "https://company.atlassian.net/wiki",
        "user@company.com",
        "fake_token"
    )


@pytest.fixture
def mock_page():
    """Create mock Confluence page."""
    return {
        "id": "123456",
        "type": "page",
        "status": "current",
        "title": "Test Page",
        "space": {"key": "DEV", "name": "Development"},
        "body": {
            "storage": {
                "value": "<p>Test content</p>",
                "representation": "storage"
            }
        },
        "version": {"number": 1}
    }


@pytest.fixture
def mock_space():
    """Create mock Confluence space."""
    return {
        "key": "DEV",
        "name": "Development",
        "type": "global",
        "status": "current"
    }


def test_confluence_service_creation(confluence_service):
    """Test that ConfluenceService can be created."""
    assert confluence_service is not None
    assert confluence_service.confluence_url == "https://company.atlassian.net/wiki"
    assert confluence_service.username == "user@company.com"
    assert not confluence_service._initialized


@pytest.mark.asyncio
async def test_initialize(confluence_service, mcp_client):
    """Test Confluence service initialization."""
    await confluence_service.initialize()

    assert confluence_service._initialized
    mcp_client.connect_server.assert_called_once()

    # Verify environment was configured
    call_args = mcp_client.connect_server.call_args
    assert call_args[1]["env"]["CONFLUENCE_URL"] == "https://company.atlassian.net/wiki"
    assert call_args[1]["env"]["CONFLUENCE_USERNAME"] == "user@company.com"
    assert call_args[1]["env"]["CONFLUENCE_API_TOKEN"] == "fake_token"


@pytest.mark.asyncio
async def test_initialize_already_initialized(confluence_service, mcp_client):
    """Test initializing when already initialized."""
    await confluence_service.initialize()

    # Reset mock
    mcp_client.connect_server.reset_mock()

    # Try to initialize again
    await confluence_service.initialize()

    # Should not call connect_server again
    mcp_client.connect_server.assert_not_called()


@pytest.mark.asyncio
async def test_search_content(confluence_service, mcp_client):
    """Test searching Confluence content."""
    await confluence_service.initialize()

    # Setup mock response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='[{"id": "123", "title": "Test"}]')]
    )

    result = await confluence_service.search_content("authentication")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-search",
        {
            "query": "authentication",
            "limit": 25
        }
    )


@pytest.mark.asyncio
async def test_search_content_with_space(confluence_service, mcp_client):
    """Test searching content in specific space."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='[]')]
    )

    result = await confluence_service.search_content(
        "API docs",
        space="DEV",
        limit=10
    )

    assert result is not None
    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["query"] == "API docs"
    assert call_args["space"] == "DEV"
    assert call_args["limit"] == 10


@pytest.mark.asyncio
async def test_search_content_not_initialized(confluence_service):
    """Test error when searching without initialization."""
    with pytest.raises(RuntimeError, match="not initialized"):
        await confluence_service.search_content("test")


@pytest.mark.asyncio
async def test_get_page(confluence_service, mcp_client, mock_page):
    """Test getting Confluence page by ID."""
    await confluence_service.initialize()

    # Setup mock response
    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_page))]
    )

    result = await confluence_service.get_page("123456")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-get-page",
        {"id": "123456"}
    )


@pytest.mark.asyncio
async def test_get_page_not_initialized(confluence_service):
    """Test error when getting page without initialization."""
    with pytest.raises(RuntimeError, match="not initialized"):
        await confluence_service.get_page("123456")


@pytest.mark.asyncio
async def test_get_page_by_title(confluence_service, mcp_client, mock_page):
    """Test getting page by space and title."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_page))]
    )

    result = await confluence_service.get_page_by_title(
        "DEV",
        "API Documentation"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-get-page-by-title",
        {
            "space": "DEV",
            "title": "API Documentation"
        }
    )


@pytest.mark.asyncio
async def test_create_page(confluence_service, mcp_client):
    """Test creating Confluence page."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "789", "title": "New Page"}')]
    )

    result = await confluence_service.create_page(
        space="DEV",
        title="New Feature Docs",
        content="<p>Documentation content</p>"
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once()

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["space"] == "DEV"
    assert call_args["title"] == "New Feature Docs"
    assert call_args["content"] == "<p>Documentation content</p>"


@pytest.mark.asyncio
async def test_create_page_with_parent(confluence_service, mcp_client):
    """Test creating page with parent page."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "789"}')]
    )

    result = await confluence_service.create_page(
        space="DEV",
        title="Child Page",
        content="<p>Child content</p>",
        parent_id="123456"
    )

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["parent_id"] == "123456"


@pytest.mark.asyncio
async def test_update_page(confluence_service, mcp_client):
    """Test updating Confluence page."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "123456", "version": {"number": 2}}')]
    )

    result = await confluence_service.update_page(
        page_id="123456",
        content="<p>Updated content</p>",
        version=1
    )

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-update-page",
        {
            "id": "123456",
            "content": "<p>Updated content</p>",
            "version": 1
        }
    )


@pytest.mark.asyncio
async def test_update_page_with_title(confluence_service, mcp_client):
    """Test updating page with new title."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"id": "123456"}')]
    )

    result = await confluence_service.update_page(
        page_id="123456",
        content="<p>Content</p>",
        version=1,
        title="New Title"
    )

    call_args = mcp_client.call_tool.call_args[0][2]
    assert call_args["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_page(confluence_service, mcp_client):
    """Test deleting Confluence page."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text='{"success": true}')]
    )

    result = await confluence_service.delete_page("123456")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-delete-page",
        {"id": "123456"}
    )


@pytest.mark.asyncio
async def test_get_space(confluence_service, mcp_client, mock_space):
    """Test getting Confluence space details."""
    await confluence_service.initialize()

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(mock_space))]
    )

    result = await confluence_service.get_space("DEV")

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-get-space",
        {"key": "DEV"}
    )


@pytest.mark.asyncio
async def test_list_spaces(confluence_service, mcp_client):
    """Test listing Confluence spaces."""
    await confluence_service.initialize()

    spaces = [
        {"key": "DEV", "name": "Development"},
        {"key": "PROD", "name": "Production"}
    ]

    mcp_client.call_tool.return_value = Mock(
        content=[Mock(text=str(spaces))]
    )

    result = await confluence_service.list_spaces(limit=50)

    assert result is not None
    mcp_client.call_tool.assert_called_once_with(
        confluence_service.server_name,
        "confluence-list-spaces",
        {"limit": 50}
    )


@pytest.mark.asyncio
async def test_cleanup(confluence_service, mcp_client):
    """Test cleanup disconnects properly."""
    await confluence_service.initialize()
    server_name = confluence_service.server_name

    assert confluence_service._initialized

    await confluence_service.cleanup()

    assert not confluence_service._initialized
    mcp_client.disconnect.assert_called_once_with(server_name)


@pytest.mark.asyncio
async def test_cleanup_not_initialized(confluence_service, mcp_client):
    """Test cleanup when not initialized."""
    # Should not raise error
    await confluence_service.cleanup()

    mcp_client.disconnect.assert_not_called()


def test_repr(confluence_service):
    """Test string representation."""
    repr_str = repr(confluence_service)
    assert "ConfluenceService" in repr_str
    assert "https://company.atlassian.net/wiki" in repr_str
    assert "not initialized" in repr_str


def test_repr_initialized(confluence_service):
    """Test string representation when initialized."""
    confluence_service._initialized = True
    repr_str = repr(confluence_service)
    assert "initialized" in repr_str


@pytest.mark.asyncio
async def test_extract_result_with_content(confluence_service):
    """Test extracting result from MCP response."""
    await confluence_service.initialize()

    result = Mock()
    result.content = [Mock(text="test result")]

    extracted = confluence_service._extract_result(result)
    assert extracted == "test result"


@pytest.mark.asyncio
async def test_extract_result_no_content(confluence_service):
    """Test extracting result with no content."""
    await confluence_service.initialize()

    result = "direct result"
    extracted = confluence_service._extract_result(result)
    assert extracted == "direct result"
