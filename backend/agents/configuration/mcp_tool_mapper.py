"""
MCP Tool Mapper

Manages MCP tool mapping configuration, determining which tools each agent role can access.
Loads configuration from YAML file and provides query methods.
"""

from typing import Dict, List, Set, Optional
import yaml
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class MCPToolMapper:
    """
    Manages MCP tool mapping configuration.

    Loads tool mapping from YAML and provides methods to query
    which tools each agent role can access.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MCP tool mapper.

        Args:
            config_path: Path to YAML config file (optional, uses default)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "mcp_tool_mapping.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded MCP tool mapping from {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"MCP tool mapping file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing MCP tool mapping YAML: {e}")
            raise

    def get_servers_for_role(self, role: str) -> List[str]:
        """
        Get list of MCP servers for a role.

        Args:
            role: Agent role name

        Returns:
            List of server names (e.g., ["git", "github"])
        """
        # Handle aliases
        role = self._resolve_alias(role)

        role_config = self.config["roles"].get(role, {})
        servers = role_config.get("mcp_servers", [])

        logger.debug(f"Role '{role}' has access to servers: {servers}")
        return servers

    def get_tools_for_role(self, role: str, server: str) -> List[str]:
        """
        Get list of allowed tools for a role on a specific server.

        Args:
            role: Agent role name
            server: MCP server name

        Returns:
            List of tool names
        """
        # Handle aliases
        role = self._resolve_alias(role)

        role_config = self.config["roles"].get(role, {})
        tools = role_config.get("tools", {})
        server_tools = tools.get(server, [])

        logger.debug(f"Role '{role}' can use {len(server_tools)} tools on '{server}' server")
        return server_tools

    def can_use_tool(self, role: str, server: str, tool: str) -> bool:
        """
        Check if a role can use a specific tool.

        Args:
            role: Agent role name
            server: MCP server name
            tool: Tool name

        Returns:
            True if role can use tool, False otherwise
        """
        # Handle aliases
        role = self._resolve_alias(role)

        allowed_tools = self.get_tools_for_role(role, server)
        can_use = tool in allowed_tools

        if not can_use:
            logger.warning(
                f"Role '{role}' attempted to use unauthorized tool '{tool}' "
                f"on server '{server}'"
            )

        return can_use

    def get_server_config(self, server: str) -> Dict:
        """
        Get connection configuration for an MCP server.

        Uses the active profile (self_hosted or smithery) to determine configuration.

        Args:
            server: Server name (e.g., "git", "github", "jira")

        Returns:
            Server configuration dict with command, args, env
        """
        # Get active profile (default to self_hosted)
        active_profile = self.config.get("active_profile", "self_hosted")

        # Get server config from active profile
        server_profiles = self.config.get("server_profiles", {})
        profile_config = server_profiles.get(active_profile, {})
        server_config = profile_config.get(server, {})

        # Fallback: try old config format (for backward compatibility)
        if not server_config:
            server_config = self.config.get("mcp_servers", {}).get(server, {})

        if not server_config:
            logger.warning(
                f"No configuration found for server '{server}' in profile '{active_profile}'"
            )
            return {}

        # Expand environment variables in env section
        if "env" in server_config:
            server_config["env"] = self._expand_env_vars(server_config["env"])

        logger.debug(
            f"Using '{active_profile}' profile for server '{server}'"
        )

        return server_config

    def get_all_tools_for_role(self, role: str) -> Dict[str, List[str]]:
        """
        Get all tools organized by server for a role.

        Args:
            role: Agent role name

        Returns:
            Dict mapping server name to list of tool names
            Example: {"git": ["git_status", "git_commit"], "github": ["create_pr"]}
        """
        # Handle aliases
        role = self._resolve_alias(role)

        role_config = self.config["roles"].get(role, {})
        tools = role_config.get("tools", {})

        logger.info(f"Role '{role}' has access to {len(tools)} server(s)")
        return tools

    def get_all_roles(self) -> List[str]:
        """
        Get list of all configured roles.

        Returns:
            List of role names
        """
        return list(self.config["roles"].keys())

    def get_all_servers(self) -> List[str]:
        """
        Get list of all configured MCP servers.

        Returns:
            List of server names
        """
        # Get from active profile
        active_profile = self.config.get("active_profile", "self_hosted")
        server_profiles = self.config.get("server_profiles", {})
        profile_config = server_profiles.get(active_profile, {})

        if profile_config:
            return list(profile_config.keys())

        # Fallback to old format
        return list(self.config.get("mcp_servers", {}).keys())

    def get_active_profile(self) -> str:
        """
        Get the currently active server profile.

        Returns:
            Active profile name ("self_hosted" or "smithery")
        """
        return self.config.get("active_profile", "self_hosted")

    def set_active_profile(self, profile: str) -> None:
        """
        Switch to a different server profile.

        Args:
            profile: Profile name ("self_hosted" or "smithery")

        Raises:
            ValueError: If profile doesn't exist
        """
        server_profiles = self.config.get("server_profiles", {})
        if profile not in server_profiles:
            raise ValueError(
                f"Profile '{profile}' not found. Available: {list(server_profiles.keys())}"
            )

        self.config["active_profile"] = profile
        logger.info(f"Switched to MCP profile: {profile}")

    def validate_role(self, role: str) -> bool:
        """
        Check if a role is valid (configured).

        Args:
            role: Role name to validate

        Returns:
            True if role is configured, False otherwise
        """
        # Handle aliases
        role = self._resolve_alias(role)
        return role in self.config["roles"]

    def validate_server(self, server: str) -> bool:
        """
        Check if a server is valid (configured).

        Args:
            server: Server name to validate

        Returns:
            True if server is configured, False otherwise
        """
        return server in self.config["mcp_servers"]

    def get_role_summary(self, role: str) -> Dict:
        """
        Get summary of role's MCP access.

        Args:
            role: Role name

        Returns:
            Summary dict with servers, tool counts, etc.
        """
        # Handle aliases
        role = self._resolve_alias(role)

        if not self.validate_role(role):
            return {
                "role": role,
                "valid": False,
                "error": "Role not configured"
            }

        servers = self.get_servers_for_role(role)
        all_tools = self.get_all_tools_for_role(role)

        total_tools = sum(len(tools) for tools in all_tools.values())

        return {
            "role": role,
            "valid": True,
            "servers": servers,
            "server_count": len(servers),
            "tools_by_server": {
                server: len(tools) for server, tools in all_tools.items()
            },
            "total_tools": total_tools
        }

    def _resolve_alias(self, role: str) -> str:
        """
        Resolve role alias to actual role name.

        Args:
            role: Role name or alias

        Returns:
            Actual role name
        """
        aliases = self.config.get("aliases", {})
        return aliases.get(role, role)

    def _expand_env_vars(self, env_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Expand environment variables in env configuration.

        Args:
            env_dict: Dict with values like "${VAR_NAME}"

        Returns:
            Dict with expanded values from environment
        """
        expanded = {}
        for key, value in env_dict.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]  # Remove ${ and }
                expanded[key] = os.environ.get(var_name, "")
                if not expanded[key]:
                    logger.warning(
                        f"Environment variable '{var_name}' not set for MCP server config"
                    )
            else:
                expanded[key] = value
        return expanded


# Singleton instance
_tool_mapper_instance: Optional[MCPToolMapper] = None


def get_tool_mapper() -> MCPToolMapper:
    """
    Get singleton MCPToolMapper instance.

    Returns:
        MCPToolMapper instance
    """
    global _tool_mapper_instance
    if _tool_mapper_instance is None:
        _tool_mapper_instance = MCPToolMapper()
    return _tool_mapper_instance


def reset_tool_mapper():
    """Reset singleton (for testing)."""
    global _tool_mapper_instance
    _tool_mapper_instance = None
