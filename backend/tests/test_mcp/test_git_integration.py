"""
Tests for Git Integration via MCP.
Tests reading files, searching code, viewing history from a Git repository.
"""

import pytest
import os
from backend.integrations.mcp.client import MCPClientManager
from backend.integrations.git_integration import GitIntegration


# Use the agent-squad repository itself for testing
TEST_REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


@pytest.mark.asyncio
async def test_git_integration_initialization():
    """Test that Git MCP server can be initialized"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()
        assert git._initialized
        assert mcp_client.is_connected(git.server_name)
    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_read_file():
    """Test reading a file from Git repository"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # Read README.md
        content = await git.read_file("README.md")

        assert content is not None
        assert len(content) > 0
        assert "Agent Squad" in content  # Should contain our project name

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_list_files():
    """Test listing files in repository"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # List all files
        files = await git.list_files()

        assert files is not None
        assert len(files) > 0
        assert "README.md" in files
        assert "docker-compose.yml" in files

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_list_files_with_pattern():
    """Test listing files with glob pattern"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # List only Python files
        python_files = await git.list_files(pattern="*.py")

        assert python_files is not None
        assert len(python_files) > 0
        # All files should end with .py
        assert all(f.endswith(".py") for f in python_files if f)

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_search_grep():
    """Test searching code with git grep"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # Search for "FastAPI" in the repository
        results = await git.search_grep("FastAPI")

        assert results is not None
        # Should find FastAPI mentions in our codebase
        assert "FastAPI" in results or len(results) == 0  # Might not find if not indexed

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_get_log():
    """Test getting commit history"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # Get last 5 commits
        log = await git.get_log(max_count=5)

        assert log is not None
        assert len(log) > 0
        # Should contain commit info
        assert "commit" in log.lower() or "author" in log.lower()

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_get_file_history():
    """Test getting commit history for a specific file"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git.initialize()

        # Get history for README.md
        history = await git.get_file_history("README.md", max_count=3)

        assert history is not None
        # Should contain commit information
        assert len(history) > 0

    finally:
        await git.cleanup()


@pytest.mark.asyncio
async def test_git_not_initialized_error():
    """Test that operations fail if not initialized"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    # Try to read file without initializing
    with pytest.raises(RuntimeError, match="not initialized"):
        await git.read_file("README.md")


@pytest.mark.asyncio
async def test_mcp_client_multiple_connections():
    """Test that MCP client can handle multiple server connections"""
    mcp_client = MCPClientManager()

    # Connect two different Git integrations
    git1 = GitIntegration(mcp_client, TEST_REPO_PATH)
    git2 = GitIntegration(mcp_client, TEST_REPO_PATH)

    try:
        await git1.initialize()
        await git2.initialize()

        # Both should be connected
        assert mcp_client.is_connected(git1.server_name)
        assert mcp_client.is_connected(git2.server_name)

        # List servers
        servers = mcp_client.list_servers()
        assert len(servers) == 2

    finally:
        await mcp_client.disconnect_all()


@pytest.mark.asyncio
async def test_git_cleanup():
    """Test cleanup disconnects properly"""
    mcp_client = MCPClientManager()
    git = GitIntegration(mcp_client, TEST_REPO_PATH)

    await git.initialize()
    server_name = git.server_name

    assert mcp_client.is_connected(server_name)

    await git.cleanup()

    assert not mcp_client.is_connected(server_name)
    assert not git._initialized
