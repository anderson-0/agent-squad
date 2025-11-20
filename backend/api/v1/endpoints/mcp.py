"""
MCP Integration API Endpoints (Stream J)

Provides API for:
- Agent-Squad MCP server status
- MCP tool discovery
- Session management (future)
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.integrations.mcp.servers import get_agent_squad_server
from backend.schemas.mcp import MCPToolsListResponse
from backend.core.logging import logger


router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get(
    "/server/tools",
    response_model=MCPToolsListResponse,
    summary="List MCP tools",
    description="List all available tools from Agent-Squad MCP server"
)
async def list_mcp_tools(
    current_user: User = Depends(get_current_user),
) -> MCPToolsListResponse:
    """
    List all available MCP tools from Agent-Squad server.
    
    Returns tools like:
    - spawn_task
    - check_workflow_health
    - get_coherence_score
    - create_workflow_branch
    - discover_opportunities
    - get_kanban_board
    """
    try:
        server = get_agent_squad_server()
        
        if not hasattr(server, 'tools') or not server.tools:
            return MCPToolsListResponse(
                server_name="agent-squad",
                tools=[],
                total_tools=0,
            )
        
        tools_list = [
            {
                "name": tool.name if hasattr(tool, 'name') else str(tool),
                "description": getattr(tool, 'description', ''),
                "input_schema": getattr(tool, 'inputSchema', {}),
            }
            for tool in server.tools
        ]
        
        return MCPToolsListResponse(
            server_name="agent-squad",
            tools=tools_list,
            total_tools=len(tools_list),
        )
    
    except Exception as e:
        logger.error(f"Error listing MCP tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP tools: {str(e)}"
        )


@router.get(
    "/server/status",
    summary="Get MCP server status",
    description="Get status of Agent-Squad MCP server"
)
async def get_mcp_server_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get status of Agent-Squad MCP server.
    
    Returns:
    - Server name
    - Tool count
    - Availability status
    """
    try:
        server = get_agent_squad_server()
        
        tool_count = len(server.tools) if hasattr(server, 'tools') and server.tools else 0
        
        return {
            "server_name": "agent-squad",
            "tool_count": tool_count,
            "status": "available" if tool_count > 0 else "unavailable",
            "mcp_sdk_available": hasattr(server, 'server') and server.server is not None,
        }
    
    except Exception as e:
        logger.error(f"Error getting MCP server status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP server status: {str(e)}"
        )

