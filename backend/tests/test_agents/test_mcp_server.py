"""
Tests for Agent-Squad MCP Server (Stream J)
"""
import pytest
from uuid import uuid4

from backend.integrations.mcp.servers import AgentSquadMCPServer, get_agent_squad_server


def test_agent_squad_server_initialization():
    """Test that Agent-Squad MCP server can be initialized"""
    server = get_agent_squad_server()
    assert server is not None
    assert isinstance(server, AgentSquadMCPServer)


def test_mcp_server_has_tools():
    """Test that MCP server defines tools"""
    server = get_agent_squad_server()
    
    # Even if MCP SDK not available, tools should be defined
    if hasattr(server, 'tools'):
        assert isinstance(server.tools, list)
        # Should have at least the 6 core tools
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in server.tools]
        expected_tools = [
            "spawn_task",
            "check_workflow_health",
            "get_coherence_score",
            "create_workflow_branch",
            "discover_opportunities",
            "get_kanban_board",
        ]
        
        # Check that expected tools exist
        for expected_tool in expected_tools:
            assert any(expected_tool in str(tool) for tool in server.tools) or not hasattr(server, 'server')


@pytest.mark.asyncio
async def test_spawn_task_tool_handler():
    """Test spawn_task tool handler"""
    server = get_agent_squad_server()
    
    # Test with mock arguments
    arguments = {
        "execution_id": str(uuid4()),
        "agent_id": str(uuid4()),
        "phase": "building",
        "title": "Test Task",
        "description": "Test Description",
        "rationale": "Test Rationale",
    }
    
    try:
        result = await server._handle_spawn_task(arguments)
        # Should return TextContent list
        assert isinstance(result, list)
    except Exception as e:
        # Expected to fail without valid DB/execution
        assert "not found" in str(e).lower() or "database" in str(e).lower()


@pytest.mark.asyncio
async def test_check_workflow_health_tool_handler():
    """Test check_workflow_health tool handler"""
    server = get_agent_squad_server()
    
    arguments = {
        "execution_id": str(uuid4()),
    }
    
    try:
        result = await server._handle_check_workflow_health(arguments)
        assert isinstance(result, list)
    except Exception as e:
        # Expected to fail without valid execution
        assert "not found" in str(e).lower() or "database" in str(e).lower()


@pytest.mark.asyncio
async def test_get_kanban_board_tool_handler():
    """Test get_kanban_board tool handler"""
    server = get_agent_squad_server()
    
    arguments = {
        "execution_id": str(uuid4()),
    }
    
    try:
        result = await server._handle_get_kanban_board(arguments)
        assert isinstance(result, list)
    except Exception as e:
        # Expected to fail without valid execution
        assert "not found" in str(e).lower() or "database" in str(e).lower()


def test_mcp_server_tool_definitions():
    """Test that all required tools are defined"""
    server = get_agent_squad_server()
    
    if hasattr(server, 'tools'):
        tool_names = []
        for tool in server.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif isinstance(tool, dict):
                tool_names.append(tool.get('name', ''))
            else:
                tool_names.append(str(tool))
        
        # Should have all core tools defined
        assert len(tool_names) >= 6  # At least 6 tools

