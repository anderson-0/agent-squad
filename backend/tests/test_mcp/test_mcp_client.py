"""
Basic tests for MCP Client Manager.
Tests the client manager without actually connecting to servers.
"""

import pytest
from backend.integrations.mcp.client import MCPClientManager


def test_mcp_client_creation():
    """Test that MCP client can be created"""
    client = MCPClientManager()

    assert client is not None
    assert len(client.connections) == 0
    assert len(client.tools) == 0


def test_mcp_client_list_servers_empty():
    """Test listing servers when none are connected"""
    client = MCPClientManager()

    servers = client.list_servers()
    assert servers == []


def test_mcp_client_is_connected_false():
    """Test is_connected returns False for non-existent server"""
    client = MCPClientManager()

    assert not client.is_connected("nonexistent")


def test_mcp_client_get_tools_empty():
    """Test getting tools when no servers connected"""
    client = MCPClientManager()

    tools = client.get_available_tools()
    assert tools == {}


def test_mcp_client_get_tools_nonexistent_server():
    """Test getting tools for non-existent server"""
    client = MCPClientManager()

    tools = client.get_available_tools("nonexistent")
    assert tools == {}


def test_mcp_client_repr():
    """Test string representation"""
    client = MCPClientManager()

    repr_str = repr(client)
    assert "MCPClientManager" in repr_str
    assert "none" in repr_str


@pytest.mark.asyncio
async def test_mcp_client_call_tool_not_connected():
    """Test that calling tool on non-connected server raises error"""
    client = MCPClientManager()

    with pytest.raises(ValueError, match="not connected"):
        await client.call_tool("nonexistent", "some_tool", {})


@pytest.mark.asyncio
async def test_mcp_client_disconnect_nonexistent():
    """Test disconnecting from non-existent server doesn't error"""
    client = MCPClientManager()

    # Should not raise error
    await client.disconnect("nonexistent")


@pytest.mark.asyncio
async def test_mcp_client_disconnect_all_empty():
    """Test disconnect_all on empty client"""
    client = MCPClientManager()

    # Should not raise error
    await client.disconnect_all()
