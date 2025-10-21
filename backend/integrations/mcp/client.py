"""
MCP Client Manager - Manages connections to multiple MCP servers.
100% Python implementation using official MCP SDK.
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to multiple Python MCP servers via stdio.

    Example:
        manager = MCPClientManager()

        # Connect to Git MCP server
        await manager.connect_server(
            name="git",
            command="uvx",
            args=["mcp-server-git", "--repository", "/path/to/repo"]
        )

        # Call a tool
        result = await manager.call_tool(
            "git",
            "git_show",
            {"path": "README.md", "ref": "HEAD"}
        )

        # Cleanup
        await manager.disconnect_all()
    """

    def __init__(self):
        self.connections: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._read_streams: Dict[str, Any] = {}
        self._write_streams: Dict[str, Any] = {}
        self._stdio_contexts: Dict[str, Any] = {}

    async def connect_server(
        self,
        name: str,
        command: str = "uvx",
        args: List[str] = None,
        env: Dict[str, str] = None
    ) -> ClientSession:
        """
        Connect to a Python MCP server using stdio transport.

        Args:
            name: Unique name for this server connection
            command: Command to run the server (default: "uvx")
            args: Arguments to pass to the command
            env: Environment variables for the server process

        Returns:
            ClientSession: The connected MCP client session

        Raises:
            ValueError: If server with this name is already connected
            RuntimeError: If connection fails
        """
        if name in self.connections:
            raise ValueError(f"Server '{name}' is already connected")

        logger.info(f"Connecting to MCP server '{name}': {command} {args}")

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args or [],
                env=env or {}
            )

            # Create stdio transport (it's an async context manager)
            stdio_context = stdio_client(server_params)
            read, write = await stdio_context.__aenter__()

            # Store streams and context for cleanup
            self._read_streams[name] = read
            self._write_streams[name] = write
            # Store context manager for proper cleanup
            if not hasattr(self, '_stdio_contexts'):
                self._stdio_contexts = {}
            self._stdio_contexts[name] = stdio_context

            # Create session
            session = ClientSession(read, write)
            await session.__aenter__()

            # Initialize connection
            await session.initialize()

            # Store connection
            self.connections[name] = session

            # List available tools
            tools_result = await session.list_tools()
            self.tools[name] = {
                tool.name: {
                    "name": tool.name,
                    "description": tool.description if hasattr(tool, 'description') else None,
                    "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                }
                for tool in tools_result.tools
            }

            logger.info(
                f"Connected to '{name}' with {len(self.tools[name])} tools: "
                f"{', '.join(self.tools[name].keys())}"
            )

            return session

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}': {e}")
            # Cleanup on failure
            if name in self._read_streams:
                del self._read_streams[name]
            if name in self._write_streams:
                del self._write_streams[name]
            raise RuntimeError(f"Failed to connect to MCP server '{name}': {e}")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on a specific MCP server.

        Args:
            server_name: Name of the connected server
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If server is not connected
            RuntimeError: If tool execution fails
        """
        if server_name not in self.connections:
            available = ', '.join(self.connections.keys()) if self.connections else 'none'
            raise ValueError(
                f"Server '{server_name}' not connected. "
                f"Available servers: {available}"
            )

        session = self.connections[server_name]

        try:
            logger.debug(f"Calling tool '{tool_name}' on '{server_name}' with args: {arguments}")
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool call failed: {server_name}.{tool_name}: {e}")
            raise RuntimeError(f"Tool call failed: {server_name}.{tool_name}: {e}")

    def get_available_tools(self, server_name: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get list of available tools from all or specific server.

        Args:
            server_name: Optional server name to filter tools

        Returns:
            Dictionary of available tools
        """
        if server_name:
            return self.tools.get(server_name, {})
        return self.tools

    def list_servers(self) -> List[str]:
        """Get list of connected server names."""
        return list(self.connections.keys())

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return server_name in self.connections

    async def disconnect(self, server_name: str):
        """
        Disconnect from a specific server.

        Args:
            server_name: Name of the server to disconnect
        """
        if server_name not in self.connections:
            logger.warning(f"Server '{server_name}' not connected, nothing to disconnect")
            return

        try:
            logger.info(f"Disconnecting from MCP server '{server_name}'")

            session = self.connections[server_name]
            await session.__aexit__(None, None, None)

            # Cleanup stdio context if exists
            if server_name in self._stdio_contexts:
                stdio_context = self._stdio_contexts[server_name]
                try:
                    await stdio_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error cleaning up stdio context for '{server_name}': {e}")
                del self._stdio_contexts[server_name]

            # Cleanup
            del self.connections[server_name]
            del self.tools[server_name]

            if server_name in self._read_streams:
                del self._read_streams[server_name]
            if server_name in self._write_streams:
                del self._write_streams[server_name]

            logger.info(f"Disconnected from '{server_name}'")

        except Exception as e:
            logger.error(f"Error disconnecting from '{server_name}': {e}")

    async def disconnect_all(self):
        """Disconnect from all servers."""
        logger.info(f"Disconnecting from all servers ({len(self.connections)})")

        for name in list(self.connections.keys()):
            await self.disconnect(name)

    def __repr__(self) -> str:
        servers = ', '.join(self.connections.keys()) if self.connections else 'none'
        total_tools = sum(len(tools) for tools in self.tools.values())
        return f"MCPClientManager(servers={servers}, total_tools={total_tools})"
