"""
Jira Service - Jira operations using mcp-atlassian MCP server.
Provides Jira ticket management via MCP protocol.
"""

from typing import Optional, List, Dict, Any
import logging
from .mcp.client import MCPClientManager

logger = logging.getLogger(__name__)


class JiraService:
    """
    Jira operations using mcp-atlassian MCP server.

    Provides ticket management:
    - Get issue details
    - Search issues with JQL
    - Create issues
    - Update issues
    - Add comments
    - Transition status
    - Assign issues

    Example:
        jira = JiraService(
            mcp_client,
            "https://company.atlassian.net",
            "user@company.com",
            "api_token"
        )

        await jira.initialize()

        # Get issue
        issue = await jira.get_issue("PROJ-123")

        # Search issues
        results = await jira.search_issues("project = PROJ AND status = Open")

        # Update issue
        await jira.update_issue("PROJ-123", {"description": "Updated description"})

        # Add comment
        await jira.add_comment("PROJ-123", "Work in progress")

        # Change status
        await jira.transition_issue("PROJ-123", "In Progress")

        await jira.cleanup()
    """

    def __init__(
        self,
        mcp_client: MCPClientManager,
        jira_url: str,
        username: str,
        api_token: str
    ):
        """
        Initialize Jira service.

        Args:
            mcp_client: MCP client manager instance
            jira_url: Jira instance URL (e.g., https://company.atlassian.net)
            username: Jira username (email)
            api_token: Jira API token
        """
        self.client = mcp_client
        self.jira_url = jira_url
        self.username = username
        self.api_token = api_token
        self.server_name = f"jira-{id(self)}"  # Unique name per instance
        self._initialized = False

    async def initialize(self):
        """
        Connect to Jira MCP server.

        Raises:
            RuntimeError: If connection fails
        """
        if self._initialized:
            logger.warning(f"Jira service already initialized for {self.jira_url}")
            return

        logger.info(f"Initializing Jira MCP server for {self.jira_url}")

        # Configure environment for MCP server
        env = {
            "JIRA_URL": self.jira_url,
            "JIRA_USERNAME": self.username,
            "JIRA_API_TOKEN": self.api_token
        }

        await self.client.connect_server(
            name=self.server_name,
            command="uvx",
            args=["mcp-atlassian"],
            env=env
        )

        self._initialized = True

    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get Jira issue details.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            Dictionary with issue details

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info(f"Getting Jira issue {issue_key}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-get-issue",
            {"key": issue_key}
        )

        return self._extract_result(result)

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search Jira issues using JQL.

        Args:
            jql: JQL query string
            max_results: Maximum number of results (default: 50)
            start_at: Starting index for pagination (default: 0)

        Returns:
            List of issue dictionaries

        Raises:
            RuntimeError: If not initialized or search fails
        """
        self._check_initialized()

        logger.info(f"Searching Jira with JQL: {jql}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-search-issues",
            {
                "jql": jql,
                "maxResults": max_results,
                "startAt": start_at
            }
        )

        return self._extract_result(result)

    async def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new Jira issue.

        Args:
            project: Project key (e.g., "PROJ")
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (default: "Task")
            priority: Issue priority (optional)
            labels: List of labels (optional)
            assignee: Assignee username (optional)

        Returns:
            Dictionary with created issue details

        Raises:
            RuntimeError: If not initialized or creation fails
        """
        self._check_initialized()

        logger.info(f"Creating Jira issue in project {project}")

        fields: Dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }

        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels
        if assignee:
            fields["assignee"] = {"name": assignee}

        result = await self.client.call_tool(
            self.server_name,
            "jira-create-issue",
            {"fields": fields}
        )

        return self._extract_result(result)

    async def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update Jira issue fields.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            fields: Dictionary of fields to update

        Returns:
            Dictionary with update result

        Raises:
            RuntimeError: If not initialized or update fails
        """
        self._check_initialized()

        logger.info(f"Updating Jira issue {issue_key}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-update-issue",
            {
                "key": issue_key,
                "fields": fields
            }
        )

        return self._extract_result(result)

    async def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add comment to Jira issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            comment: Comment text

        Returns:
            Dictionary with comment details

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info(f"Adding comment to Jira issue {issue_key}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-add-comment",
            {
                "key": issue_key,
                "body": comment
            }
        )

        return self._extract_result(result)

    async def transition_issue(
        self,
        issue_key: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Transition Jira issue to new status.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            status: Target status name (e.g., "In Progress", "Done")

        Returns:
            Dictionary with transition result

        Raises:
            RuntimeError: If not initialized or transition fails
        """
        self._check_initialized()

        logger.info(f"Transitioning Jira issue {issue_key} to {status}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-transition-issue",
            {
                "key": issue_key,
                "status": status
            }
        )

        return self._extract_result(result)

    async def assign_issue(
        self,
        issue_key: str,
        assignee: str
    ) -> Dict[str, Any]:
        """
        Assign Jira issue to user.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            assignee: Assignee username

        Returns:
            Dictionary with assignment result

        Raises:
            RuntimeError: If not initialized or assignment fails
        """
        self._check_initialized()

        logger.info(f"Assigning Jira issue {issue_key} to {assignee}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-assign-issue",
            {
                "key": issue_key,
                "assignee": assignee
            }
        )

        return self._extract_result(result)

    async def get_transitions(
        self,
        issue_key: str
    ) -> List[Dict[str, Any]]:
        """
        Get available status transitions for issue.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            List of available transitions

        Raises:
            RuntimeError: If not initialized or operation fails
        """
        self._check_initialized()

        logger.info(f"Getting transitions for Jira issue {issue_key}")

        result = await self.client.call_tool(
            self.server_name,
            "jira-get-transitions",
            {"key": issue_key}
        )

        return self._extract_result(result)

    def _check_initialized(self):
        """Check if service is initialized."""
        if not self._initialized:
            raise RuntimeError(
                "Jira service not initialized. Call await jira.initialize() first."
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
        """Disconnect from Jira MCP server."""
        if not self._initialized:
            return

        logger.info(f"Cleaning up Jira service for {self.jira_url}")
        await self.client.disconnect(self.server_name)
        self._initialized = False

    def __repr__(self) -> str:
        status = "initialized" if self._initialized else "not initialized"
        return f"JiraService(url={self.jira_url}, {status})"
