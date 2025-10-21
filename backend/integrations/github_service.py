"""
GitHub Service - PR and Issue management using PyGithub.
Provides GitHub API operations: PRs, issues, reviews.
"""

from typing import Optional, List, Dict, Any
import logging
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Issue import Issue

logger = logging.getLogger(__name__)


class GitHubService:
    """
    GitHub operations using PyGithub.

    Provides GitHub operations:
    - Create pull requests
    - Get PR details
    - Create issues
    - Manage issue comments
    - Get repository information

    Example:
        github = GitHubService(token="ghp_xxxxx")

        # Create pull request
        pr = await github.create_pull_request(
            repo="owner/repo",
            title="Add new feature",
            body="Description of changes",
            head="feature/new-feature",
            base="main"
        )

        # Create issue
        issue = await github.create_issue(
            repo="owner/repo",
            title="Bug report",
            body="Description of bug"
        )
    """

    def __init__(self, token: str):
        """
        Initialize GitHub service.

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.client = Github(token)
        logger.info("GitHub service initialized")

    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
        maintainer_can_modify: bool = True
    ) -> Dict[str, Any]:
        """
        Create a pull request.

        Args:
            repo: Repository in format "owner/repo"
            title: PR title
            body: PR description
            head: Branch containing changes
            base: Base branch (default: main)
            draft: Whether to create as draft PR
            maintainer_can_modify: Allow maintainers to edit PR

        Returns:
            Dictionary with PR details

        Raises:
            GithubException: If PR creation fails
        """
        try:
            logger.info(f"Creating PR in {repo}: {title}")

            # Get repository
            repo_obj = self.client.get_repo(repo)

            # Create PR
            pr = repo_obj.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft,
                maintainer_can_modify=maintainer_can_modify
            )

            logger.info(f"Created PR #{pr.number}: {pr.html_url}")

            return {
                "number": pr.number,
                "url": pr.html_url,
                "title": pr.title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "head": pr.head.ref,
                "base": pr.base.ref,
                "draft": pr.draft,
                "mergeable": pr.mergeable,
                "merged": pr.merged
            }

        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            raise

    async def get_pull_request(
        self,
        repo: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Get pull request details.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number

        Returns:
            Dictionary with PR details

        Raises:
            GithubException: If PR not found
        """
        try:
            logger.info(f"Getting PR #{pr_number} from {repo}")

            repo_obj = self.client.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            return {
                "number": pr.number,
                "url": pr.html_url,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "head": pr.head.ref,
                "base": pr.base.ref,
                "draft": pr.draft,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "user": pr.user.login,
                "comments": pr.comments,
                "commits": pr.commits,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files
            }

        except GithubException as e:
            logger.error(f"Failed to get PR #{pr_number}: {e}")
            raise

    async def update_pull_request(
        self,
        repo: str,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        base: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a pull request.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            title: New title (optional)
            body: New body (optional)
            state: New state - "open" or "closed" (optional)
            base: New base branch (optional)

        Returns:
            Dictionary with updated PR details

        Raises:
            GithubException: If update fails
        """
        try:
            logger.info(f"Updating PR #{pr_number} in {repo}")

            repo_obj = self.client.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            # Update fields that are provided
            if title is not None:
                pr.edit(title=title)
            if body is not None:
                pr.edit(body=body)
            if state is not None:
                pr.edit(state=state)
            if base is not None:
                pr.edit(base=base)

            logger.info(f"Updated PR #{pr_number}")

            return await self.get_pull_request(repo, pr_number)

        except GithubException as e:
            logger.error(f"Failed to update PR #{pr_number}: {e}")
            raise

    async def merge_pull_request(
        self,
        repo: str,
        pr_number: int,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merge a pull request.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            commit_message: Optional commit message
            merge_method: "merge", "squash", or "rebase"

        Returns:
            Dictionary with merge result

        Raises:
            GithubException: If merge fails
        """
        try:
            logger.info(f"Merging PR #{pr_number} in {repo}")

            repo_obj = self.client.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            # Merge PR
            result = pr.merge(
                commit_message=commit_message,
                merge_method=merge_method
            )

            logger.info(f"Merged PR #{pr_number}: {result.merged}")

            return {
                "merged": result.merged,
                "message": result.message,
                "sha": result.sha
            }

        except GithubException as e:
            logger.error(f"Failed to merge PR #{pr_number}: {e}")
            raise

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an issue.

        Args:
            repo: Repository in format "owner/repo"
            title: Issue title
            body: Issue description
            labels: List of label names
            assignees: List of usernames to assign

        Returns:
            Dictionary with issue details

        Raises:
            GithubException: If issue creation fails
        """
        try:
            logger.info(f"Creating issue in {repo}: {title}")

            repo_obj = self.client.get_repo(repo)

            # Create issue
            issue = repo_obj.create_issue(
                title=title,
                body=body or "",
                labels=labels or [],
                assignees=assignees or []
            )

            logger.info(f"Created issue #{issue.number}: {issue.html_url}")

            return {
                "number": issue.number,
                "url": issue.html_url,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "comments": issue.comments
            }

        except GithubException as e:
            logger.error(f"Failed to create issue: {e}")
            raise

    async def get_issue(
        self,
        repo: str,
        issue_number: int
    ) -> Dict[str, Any]:
        """
        Get issue details.

        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number

        Returns:
            Dictionary with issue details

        Raises:
            GithubException: If issue not found
        """
        try:
            logger.info(f"Getting issue #{issue_number} from {repo}")

            repo_obj = self.client.get_repo(repo)
            issue = repo_obj.get_issue(issue_number)

            return {
                "number": issue.number,
                "url": issue.html_url,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "user": issue.user.login,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "comments": issue.comments
            }

        except GithubException as e:
            logger.error(f"Failed to get issue #{issue_number}: {e}")
            raise

    async def add_issue_comment(
        self,
        repo: str,
        issue_number: int,
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue or PR.

        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue or PR number
            comment: Comment text

        Returns:
            Dictionary with comment details

        Raises:
            GithubException: If comment creation fails
        """
        try:
            logger.info(f"Adding comment to issue #{issue_number} in {repo}")

            repo_obj = self.client.get_repo(repo)
            issue = repo_obj.get_issue(issue_number)
            comment_obj = issue.create_comment(comment)

            logger.info(f"Created comment {comment_obj.id}")

            return {
                "id": comment_obj.id,
                "url": comment_obj.html_url,
                "body": comment_obj.body,
                "user": comment_obj.user.login,
                "created_at": comment_obj.created_at.isoformat()
            }

        except GithubException as e:
            logger.error(f"Failed to add comment: {e}")
            raise

    async def get_repository_info(self, repo: str) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            repo: Repository in format "owner/repo"

        Returns:
            Dictionary with repository details

        Raises:
            GithubException: If repository not found
        """
        try:
            logger.info(f"Getting repository info for {repo}")

            repo_obj = self.client.get_repo(repo)

            return {
                "name": repo_obj.name,
                "full_name": repo_obj.full_name,
                "description": repo_obj.description,
                "url": repo_obj.html_url,
                "default_branch": repo_obj.default_branch,
                "private": repo_obj.private,
                "fork": repo_obj.fork,
                "created_at": repo_obj.created_at.isoformat(),
                "updated_at": repo_obj.updated_at.isoformat(),
                "stars": repo_obj.stargazers_count,
                "forks": repo_obj.forks_count,
                "open_issues": repo_obj.open_issues_count,
                "language": repo_obj.language,
                "owner": repo_obj.owner.login
            }

        except GithubException as e:
            logger.error(f"Failed to get repository info: {e}")
            raise

    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        base: Optional[str] = None,
        head: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List pull requests in a repository.

        Args:
            repo: Repository in format "owner/repo"
            state: "open", "closed", or "all"
            base: Filter by base branch
            head: Filter by head branch
            limit: Maximum number of PRs to return

        Returns:
            List of PR dictionaries

        Raises:
            GithubException: If listing fails
        """
        try:
            logger.info(f"Listing PRs in {repo} (state={state})")

            repo_obj = self.client.get_repo(repo)
            prs = repo_obj.get_pulls(
                state=state,
                base=base,
                head=head
            )

            result = []
            for i, pr in enumerate(prs):
                if i >= limit:
                    break

                result.append({
                    "number": pr.number,
                    "url": pr.html_url,
                    "title": pr.title,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat(),
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                    "user": pr.user.login,
                    "draft": pr.draft
                })

            logger.info(f"Found {len(result)} PRs")
            return result

        except GithubException as e:
            logger.error(f"Failed to list PRs: {e}")
            raise

    def __repr__(self) -> str:
        return f"GitHubService(authenticated=True)"
