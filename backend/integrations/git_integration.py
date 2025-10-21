"""
Git Integration - Read operations via mcp-server-git (Python).
Provides read-only access to Git repositories through MCP.
"""

from typing import Optional, List, Dict
import logging
from .mcp.client import MCPClientManager

logger = logging.getLogger(__name__)


class GitIntegration:
    """
    Git read operations using Python mcp-server-git MCP server.

    This provides read-only operations:
    - Read files from Git
    - List files in repository
    - Search code with git grep
    - View commit history
    - View diffs

    For write operations (branch, commit, push), use GitService.

    Example:
        mcp_client = MCPClientManager()
        git = GitIntegration(mcp_client, "/path/to/repo")

        await git.initialize()
        content = await git.read_file("README.md")
        files = await git.list_files()

        await git.cleanup()
    """

    def __init__(self, mcp_client: MCPClientManager, repo_path: str):
        """
        Initialize Git integration.

        Args:
            mcp_client: MCP client manager instance
            repo_path: Absolute path to Git repository
        """
        self.client = mcp_client
        self.repo_path = repo_path
        self.server_name = f"git-{id(self)}"  # Unique name per instance
        self._initialized = False

    async def initialize(self):
        """
        Connect to Git MCP server for this repository.

        Raises:
            RuntimeError: If connection fails
        """
        if self._initialized:
            logger.warning(f"Git integration already initialized for {self.repo_path}")
            return

        logger.info(f"Initializing Git MCP server for {self.repo_path}")

        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-server-git", "--repository", self.repo_path]
        )

        self._initialized = True

    async def read_file(self, file_path: str, ref: str = "HEAD") -> str:
        """
        Read a file from the Git repository.

        Args:
            file_path: Path to file relative to repository root
            ref: Git ref (commit, branch, tag) to read from

        Returns:
            File content as string

        Raises:
            RuntimeError: If not initialized or tool call fails
        """
        self._check_initialized()

        result = await self.client.call_tool(
            self.server_name,
            "git_show",
            {
                "path": file_path,
                "ref": ref
            }
        )

        # Extract text from MCP response
        if hasattr(result, 'content') and len(result.content) > 0:
            return result.content[0].text
        return str(result)

    async def list_files(
        self,
        directory: str = ".",
        pattern: Optional[str] = None
    ) -> List[str]:
        """
        List files in the repository.

        Args:
            directory: Directory to list (relative to repo root)
            pattern: Optional glob pattern to filter files

        Returns:
            List of file paths
        """
        self._check_initialized()

        args: Dict = {"directory": directory}
        if pattern:
            args["pattern"] = pattern

        result = await self.client.call_tool(
            self.server_name,
            "git_ls_files",
            args
        )

        # Extract and split file list
        if hasattr(result, 'content') and len(result.content) > 0:
            text = result.content[0].text
            return [f.strip() for f in text.split('\n') if f.strip()]
        return []

    async def search_grep(
        self,
        pattern: str,
        path: Optional[str] = None,
        case_insensitive: bool = False
    ) -> str:
        """
        Search for pattern in repository using git grep.

        Args:
            pattern: Pattern to search for (regex)
            path: Optional path to limit search
            case_insensitive: Whether to ignore case

        Returns:
            Search results as string
        """
        self._check_initialized()

        args: Dict = {"pattern": pattern}
        if path:
            args["path"] = path
        if case_insensitive:
            args["case_insensitive"] = True

        result = await self.client.call_tool(
            self.server_name,
            "git_grep",
            args
        )

        if hasattr(result, 'content') and len(result.content) > 0:
            return result.content[0].text
        return str(result)

    async def get_diff(
        self,
        ref1: str = "HEAD",
        ref2: Optional[str] = None,
        path: Optional[str] = None
    ) -> str:
        """
        Get diff between commits or working tree.

        Args:
            ref1: First ref to compare (default: HEAD)
            ref2: Second ref to compare (default: working tree)
            path: Optional path to limit diff

        Returns:
            Diff output as string
        """
        self._check_initialized()

        args: Dict = {"ref1": ref1}
        if ref2:
            args["ref2"] = ref2
        if path:
            args["path"] = path

        result = await self.client.call_tool(
            self.server_name,
            "git_diff",
            args
        )

        if hasattr(result, 'content') and len(result.content) > 0:
            return result.content[0].text
        return str(result)

    async def get_log(
        self,
        max_count: int = 10,
        path: Optional[str] = None,
        ref: str = "HEAD"
    ) -> str:
        """
        Get commit history.

        Args:
            max_count: Maximum number of commits to return
            path: Optional path to filter commits
            ref: Ref to start from (default: HEAD)

        Returns:
            Git log output as string
        """
        self._check_initialized()

        args: Dict = {
            "max_count": max_count,
            "ref": ref
        }
        if path:
            args["path"] = path

        result = await self.client.call_tool(
            self.server_name,
            "git_log",
            args
        )

        if hasattr(result, 'content') and len(result.content) > 0:
            return result.content[0].text
        return str(result)

    async def get_file_history(
        self,
        file_path: str,
        max_count: int = 10
    ) -> str:
        """
        Get commit history for a specific file.

        Args:
            file_path: Path to file
            max_count: Maximum number of commits

        Returns:
            Git log output for file
        """
        return await self.get_log(max_count=max_count, path=file_path)

    def _check_initialized(self):
        """Check if integration is initialized."""
        if not self._initialized:
            raise RuntimeError(
                "Git integration not initialized. Call await git.initialize() first."
            )

    async def cleanup(self):
        """Disconnect from Git MCP server."""
        if not self._initialized:
            return

        logger.info(f"Cleaning up Git integration for {self.repo_path}")
        await self.client.disconnect(self.server_name)
        self._initialized = False

    def __repr__(self) -> str:
        status = "initialized" if self._initialized else "not initialized"
        return f"GitIntegration(repo={self.repo_path}, {status})"
