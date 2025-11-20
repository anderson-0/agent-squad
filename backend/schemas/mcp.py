"""
Pydantic Schemas for MCP Integration (Stream J)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class MCPSessionInfo(BaseModel):
    """Information about an MCP session"""
    session_id: str
    agent_id: UUID
    tools: List[str]
    created_at: datetime
    status: str  # "active", "inactive", "closed"


class MCPToolResponse(BaseModel):
    """Response from an MCP tool call"""
    tool_name: str
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class MCPToolsListResponse(BaseModel):
    """List of available MCP tools"""
    server_name: str
    tools: List[Dict[str, Any]]
    total_tools: int

