"""
Confluence Service - Confluence operations using mcp-atlassian MCP server.
Provides Confluence documentation access via MCP protocol.
"""

from typing import Optional, List, Dict, Any
import logging
from .mcp.client import MCPClientManager

logger = logging.getLogger(__name__)


class ConfluenceService:
    """
    Confluence operations using mcp-atlassian MCP server.

    Provides documentation management:
    - Search content
    - Get page details
    - Get page by title
    - Create pages
    - Update pages

    Example:
        confluence = ConfluenceService(
            mcp_client,
            "https://company.atlassian.net/wiki",
            "user@company.com",
            "api_token"
        )

        await confluence.initialize()

        # Search content
        results = await confluence.search_content("authentication")

        # Get page
        page = await confluence.get_page("123456")

        # Get page by title
        page = await confluence.get_page_by_title("DEV", "API Documentation")

        # Create page
        new_page = await confluence.create_page(
            space="DEV",
            title="New Feature Docs",
            content="<p>Documentation content</p>"
        )

        await confluence.cleanup()
    """

    def __init__(
        self,
        mcp_client: MCPClientManager,
        confluence_url: str,
        username: str,
        api_token: str
    ):
        """
        Initialize Confluence service.

        Args:
            mcp_client: MCP client manager instance
            confluence_url: Confluence instance URL (e.g., https://company.atlassian.net/wiki)
            username: Confluence username (email)
            api_token: Confluence API token (same as Jira)
        """
        self.client = mcp_client
        self.confluence_url = confluence_url
        self.username = username
        self.api_token = api_token
        self.server_name = f"confluence-{id(self)}"  # Unique name per instance
        self._initialized = False

    async def initialize(self):
        """
        Connect to Confluence MCP server.

        Raises:
            RuntimeError: If connection fails
        """
        if self._initialized:
            logger.warning(f"Confluence service already initialized for {self.confluence_url}")
            return

        logger.info(f"Initializing Confluence MCP server for {self.confluence_url}")

        # Configure environment for MCP server
        env = {
            "CONFLUENCE_URL": self.confluence_url,
            "CONFLUENCE_USERNAME": self.username,
            "CONFLUENCE_API_TOKEN": self.api_token
        }

        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-atlassian"],
            env=env
        )

        self._initialized = True

    async def search_content(
        self,
        query: str,
        space: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Search Confluence content.

        Args:
            query: Search query string
            space: Optional space key to limit search
            limit: Maximum number of results (default: 25)

        Returns:
            List of matching content

        Raises:
            RuntimeError: If not initialized or search fails
        """
        self._check_initialized()

        logger.info(f"Searching Confluence for: {query}")

        args: Dict[str, Any] = {
            "query": query,
            "limit": limit
        }

        if space:
            args["space"] = space

        result = await self.client.call_tool(
            self.server_name,
            "confluence-search",
            args
        )

        return self._extract_result(result)

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get Confluence page by ID.

        Args:
            page_id: Page ID

        Returns:
            Dictionary with page details

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info(f"Getting Confluence page {page_id}")

        result = await self.client.call_tool(
            self.server_name,
            "confluence-get-page",
            {"id": page_id}
        )

        return self._extract_result(result)

    async def get_page_by_title(
        self,
        space: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Get Confluence page by space and title.

        Args:
            space: Space key (e.g., "DEV")
            title: Page title

        Returns:
            Dictionary with page details

        Raises:
            RuntimeError: If not initialized or page not found
        """
        self._check_initialized()

        logger.info(f"Getting Confluence page '{title}' in space {space}")

        result = await self.client.call_tool(
            self.server_name,
            "confluence-get-page-by-title",
            {
                "space": space,
                "title": title
            }
        )

        return self._extract_result(result)

    async def create_page(
        self,
        space: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new Confluence page.

        Args:
            space: Space key (e.g., "DEV")
            title: Page title
            content: Page content (HTML format)
            parent_id: Optional parent page ID

        Returns:
            Dictionary with created page details

        Raises:
            RuntimeError: If not initialized or creation fails
        """
        self._check_initialized()

        logger.info(f"Creating Confluence page '{title}' in space {space}")

        args: Dict[str, Any] = {
            "space": space,
            "title": title,
            "content": content
        }

        if parent_id:
            args["parent_id"] = parent_id

        result = await self.client.call_tool(
            self.server_name,
            "confluence-create-page",
            args
        )

        return self._extract_result(result)

    async def update_page(
        self,
        page_id: str,
        content: str,
        version: int,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Confluence page.

        Args:
            page_id: Page ID
            content: New page content (HTML format)
            version: Current version number (for optimistic locking)
            title: Optional new title

        Returns:
            Dictionary with updated page details

        Raises:
            RuntimeError: If not initialized or update fails
        """
        self._check_initialized()

        logger.info(f"Updating Confluence page {page_id}")

        args: Dict[str, Any] = {
            "id": page_id,
            "content": content,
            "version": version
        }

        if title:
            args["title"] = title

        result = await self.client.call_tool(
            self.server_name,
            "confluence-update-page",
            args
        )

        return self._extract_result(result)

    async def delete_page(self, page_id: str) -> Dict[str, Any]:
        """
        Delete Confluence page.

        Args:
            page_id: Page ID

        Returns:
            Dictionary with deletion result

        Raises:
            RuntimeError: If not initialized or deletion fails
        """
        self._check_initialized()

        logger.info(f"Deleting Confluence page {page_id}")

        result = await self.client.call_tool(
            self.server_name,
            "confluence-delete-page",
            {"id": page_id}
        )

        return self._extract_result(result)

    async def get_space(self, space_key: str) -> Dict[str, Any]:
        """
        Get Confluence space details.

        Args:
            space_key: Space key (e.g., "DEV")

        Returns:
            Dictionary with space details

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info(f"Getting Confluence space {space_key}")

        result = await self.client.call_tool(
            self.server_name,
            "confluence-get-space",
            {"key": space_key}
        )

        return self._extract_result(result)

    async def list_spaces(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        List Confluence spaces.

        Args:
            limit: Maximum number of results (default: 25)

        Returns:
            List of space dictionaries

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info("Listing Confluence spaces")

        result = await self.client.call_tool(
            self.server_name,
            "confluence-list-spaces",
            {"limit": limit}
        )

        return self._extract_result(result)

    def _check_initialized(self):
        """Check if service is initialized."""
        if not self._initialized:
            raise RuntimeError(
                "Confluence service not initialized. Call await confluence.initialize() first."
            )

    def _extract_result(self, result: Any) -> Any:
        """Extract result from MCP response."""
        if hasattr(result, 'content') and len(result.content) > 0:
            # Try to get structured data
            content = result.content[0]
            if hasattr(content, 'text'):
                return content.text
            return content
        return result

    async def cleanup(self):
        """Disconnect from Confluence MCP server."""
        if not self._initialized:
            return

        logger.info(f"Cleaning up Confluence service for {self.confluence_url}")
        await self.client.disconnect(self.server_name)
        self._initialized = False

    def __repr__(self) -> str:
        status = "initialized" if self._initialized else "not initialized"
        return f"ConfluenceService(url={self.confluence_url}, {status})"
