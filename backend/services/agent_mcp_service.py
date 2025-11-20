"""
Agent MCP Service

Service for managing agent MCP tool access.
Initializes MCP servers based on agent roles and executes tools with permission checking.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper, MCPToolMapper
from backend.integrations.mcp.client import MCPClientManager
from backend.models import SquadMember  # Fixed: Import from models package, not squad_member module

logger = logging.getLogger(__name__)


class AgentMCPService:
    """
    Service for managing agent MCP tool access.

    Responsibilities:
    - Initialize MCP servers for agent roles
    - Execute tools with permission checking
    - Manage MCP client lifecycle
    - Track tool usage
    """

    def __init__(self):
        """Initialize Agent MCP Service."""
        self.mapper: MCPToolMapper = get_tool_mapper()
        self.mcp_manager: MCPClientManager = MCPClientManager()
        self._role_sessions: Dict[str, Dict[str, Any]] = {}  # role -> {server -> session}

    async def initialize_agent_tools(
        self,
        role: str,
        force_reconnect: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize MCP servers and tools for an agent role.

        Args:
            role: Agent role (e.g., "backend_developer")
            force_reconnect: Force reconnection even if already connected

        Returns:
            Dictionary mapping server names to ClientSession objects

        Raises:
            ValueError: If role is not configured
        """
        # Validate role
        if not self.mapper.validate_role(role):
            raise ValueError(f"Role '{role}' is not configured for MCP tools")

        # Check if already initialized
        if role in self._role_sessions and not force_reconnect:
            logger.debug(f"MCP tools for role '{role}' already initialized")
            return self._role_sessions[role]

        # Get servers for this role
        servers = self.mapper.get_servers_for_role(role)

        if not servers:
            logger.info(f"Role '{role}' has no MCP servers configured")
            return {}

        # Connect to each server
        sessions = {}
        for server_name in servers:
            try:
                session = await self._connect_server(server_name)
                sessions[server_name] = session
                logger.info(f"Connected role '{role}' to MCP server '{server_name}'")
            except Exception as e:
                logger.error(
                    f"Failed to connect role '{role}' to server '{server_name}': {e}"
                )
                # Continue with other servers even if one fails

        # Cache sessions
        self._role_sessions[role] = sessions

        logger.info(
            f"Initialized {len(sessions)}/{len(servers)} MCP servers for role '{role}'"
        )

        return sessions

    async def _connect_server(self, server_name: str) -> Any:
        """
        Connect to an MCP server.

        Args:
            server_name: Server name (e.g., "git", "github")

        Returns:
            ClientSession object

        Raises:
            ValueError: If server is not configured
        """
        server_config = self.mapper.get_server_config(server_name)

        if not server_config:
            raise ValueError(f"Server '{server_name}' is not configured")

        # Connect using MCP client manager
        session = await self.mcp_manager.connect_server(
            name=server_name,
            command=server_config.get("command", "uvx"),
            args=server_config.get("args", []),
            env=server_config.get("env", {})
        )

        return session

    async def execute_tool(
        self,
        role: str,
        server: str,
        tool: str,
        arguments: Dict[str, Any],
        track_usage: bool = True
    ) -> Any:
        """
        Execute a tool if the role has permission.

        Args:
            role: Agent role
            server: MCP server name
            tool: Tool name
            arguments: Tool arguments
            track_usage: Whether to track usage (for audit/metrics)

        Returns:
            Tool execution result

        Raises:
            PermissionError: If role cannot use this tool
            ValueError: If server/tool not found
        """
        # Check permission
        if not self.mapper.can_use_tool(role, server, tool):
            error_msg = (
                f"Role '{role}' is not allowed to use tool '{tool}' "
                f"on server '{server}'"
            )
            logger.error(error_msg)
            raise PermissionError(error_msg)

        # Ensure server is connected
        if role not in self._role_sessions:
            await self.initialize_agent_tools(role)

        if server not in self._role_sessions.get(role, {}):
            error_msg = f"Server '{server}' not connected for role '{role}'"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Execute tool
        try:
            logger.info(
                f"Executing tool '{tool}' on server '{server}' for role '{role}'"
            )

            result = await self.mcp_manager.call_tool(
                server_name=server,
                tool_name=tool,
                arguments=arguments
            )

            logger.info(f"Tool '{tool}' executed successfully for role '{role}'")

            # TODO: Track usage if requested
            if track_usage:
                await self._track_tool_usage(role, server, tool, arguments, result, True)

            return result

        except Exception as e:
            logger.error(f"Tool '{tool}' execution failed for role '{role}': {e}")

            # Track failure
            if track_usage:
                await self._track_tool_usage(
                    role, server, tool, arguments, None, False, str(e)
                )

            raise

    async def get_available_tools(self, role: str) -> Dict[str, List[str]]:
        """
        Get all available tools for a role.

        Args:
            role: Agent role

        Returns:
            Dictionary mapping server name to list of tool names
        """
        return self.mapper.get_all_tools_for_role(role)

    async def get_role_summary(self, role: str) -> Dict:
        """
        Get summary of role's MCP access.

        Args:
            role: Role name

        Returns:
            Summary dict
        """
        return self.mapper.get_role_summary(role)

    async def disconnect_role_servers(self, role: str):
        """
        Disconnect all MCP servers for a role.

        Args:
            role: Agent role
        """
        if role not in self._role_sessions:
            return

        sessions = self._role_sessions.get(role, {})
        for server_name in sessions:
            try:
                await self.mcp_manager.disconnect(server_name)
                logger.info(f"Disconnected server '{server_name}' for role '{role}'")
            except Exception as e:
                logger.error(
                    f"Error disconnecting server '{server_name}' for role '{role}': {e}"
                )

        # Remove from cache
        del self._role_sessions[role]

    async def disconnect_all(self):
        """Disconnect all MCP servers for all roles."""
        roles = list(self._role_sessions.keys())
        for role in roles:
            await self.disconnect_role_servers(role)

    async def _track_tool_usage(
        self,
        role: str,
        server: str,
        tool: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Track tool usage for audit and metrics.

        Args:
            role: Agent role
            server: MCP server
            tool: Tool name
            arguments: Tool arguments
            result: Tool result
            success: Whether execution succeeded
            error_message: Error message if failed

        TODO: Implement database storage
        """
        # Placeholder for future implementation
        # Will store in tool_execution_logs table
        logger.debug(
            f"Tool usage: role={role}, server={server}, tool={tool}, success={success}"
        )

    def get_connected_servers(self, role: str) -> List[str]:
        """
        Get list of connected MCP servers for a role.

        Args:
            role: Agent role

        Returns:
            List of server names
        """
        return list(self._role_sessions.get(role, {}).keys())

    def is_server_connected(self, role: str, server: str) -> bool:
        """
        Check if a server is connected for a role.

        Args:
            role: Agent role
            server: Server name

        Returns:
            True if connected, False otherwise
        """
        return server in self._role_sessions.get(role, {})


# Singleton instance
_agent_mcp_service_instance: Optional[AgentMCPService] = None


def get_agent_mcp_service() -> AgentMCPService:
    """
    Get singleton AgentMCPService instance.

    Returns:
        AgentMCPService instance
    """
    global _agent_mcp_service_instance
    if _agent_mcp_service_instance is None:
        _agent_mcp_service_instance = AgentMCPService()
    return _agent_mcp_service_instance


def reset_agent_mcp_service():
    """Reset singleton (for testing)."""
    global _agent_mcp_service_instance
    if _agent_mcp_service_instance is not None:
        # Note: Should call disconnect_all() before resetting in production
        _agent_mcp_service_instance = None
