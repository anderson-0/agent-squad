"""
Git Service - Write operations using GitPython.
Provides Git write operations: clone, branch, commit, push.
"""

from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
import git
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class GitService:
    """
    Git write operations using GitPython.

    Provides write operations:
    - Clone repositories
    - Create branches
    - Commit changes
    - Push to remote
    - Checkout branches

    For read operations, use GitIntegration (MCP-based).

    Example:
        git_service = GitService()

        # Clone or open repository
        repo = await git_service.clone_or_open(
            "https://github.com/user/repo.git",
            "/tmp/repo"
        )

        # Create branch and commit
        await git_service.create_branch(repo, "feature/new-feature")
        await git_service.commit_changes(
            repo,
            "Added new feature",
            files=["file1.py", "file2.py"]
        )

        # Push to remote
        await git_service.push(repo, "feature/new-feature")
    """

    def __init__(self):
        """Initialize Git service."""
        pass

    async def clone_or_open(
        self,
        repo_url: str,
        local_path: str,
        branch: Optional[str] = None
    ) -> Repo:
        """
        Clone a repository or open if it already exists.

        Args:
            repo_url: URL of the Git repository
            local_path: Local path to clone/open repository
            branch: Optional branch to checkout after clone

        Returns:
            GitPython Repo object

        Raises:
            GitCommandError: If clone or open fails
        """
        local_path_obj = Path(local_path)

        try:
            # Check if repository already exists
            if local_path_obj.exists() and (local_path_obj / ".git").exists():
                logger.info(f"Opening existing repository at {local_path}")
                repo = Repo(local_path)

                # Pull latest changes
                logger.info("Pulling latest changes from origin")
                origin = repo.remote("origin")
                origin.pull()
            else:
                # Clone repository
                logger.info(f"Cloning repository from {repo_url} to {local_path}")
                repo = Repo.clone_from(repo_url, local_path)

            # Checkout specific branch if requested
            if branch:
                logger.info(f"Checking out branch {branch}")
                repo.git.checkout(branch)

            return repo

        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            raise

    async def create_branch(
        self,
        repo: Repo,
        branch_name: str,
        from_branch: Optional[str] = None
    ) -> None:
        """
        Create and checkout a new branch.

        Args:
            repo: GitPython Repo object
            branch_name: Name of the new branch
            from_branch: Optional branch to create from (default: current branch)

        Raises:
            GitCommandError: If branch creation fails
        """
        try:
            # Checkout base branch if specified
            if from_branch:
                logger.info(f"Checking out base branch {from_branch}")
                repo.git.checkout(from_branch)

            # Create and checkout new branch
            logger.info(f"Creating and checking out branch {branch_name}")
            repo.git.checkout("-b", branch_name)

        except GitCommandError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            raise

    async def commit_changes(
        self,
        repo: Repo,
        message: str,
        files: Optional[List[str]] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """
        Stage and commit changes.

        Args:
            repo: GitPython Repo object
            message: Commit message
            files: Optional list of specific files to commit (default: all changes)
            author_name: Optional author name
            author_email: Optional author email

        Returns:
            Commit SHA

        Raises:
            GitCommandError: If commit fails
        """
        try:
            # Stage files
            if files:
                logger.info(f"Staging specific files: {files}")
                repo.index.add(files)
            else:
                logger.info("Staging all changes")
                repo.git.add("-A")

            # Check if there are changes to commit
            if not repo.index.diff("HEAD") and not repo.untracked_files:
                logger.warning("No changes to commit")
                return ""

            # Create commit
            logger.info(f"Creating commit: {message}")

            # Set author if provided
            if author_name and author_email:
                commit = repo.index.commit(
                    message,
                    author=git.Actor(author_name, author_email)
                )
            else:
                commit = repo.index.commit(message)

            logger.info(f"Created commit {commit.hexsha}")
            return commit.hexsha

        except GitCommandError as e:
            logger.error(f"Failed to commit changes: {e}")
            raise

    async def push(
        self,
        repo: Repo,
        branch: Optional[str] = None,
        remote: str = "origin",
        force: bool = False
    ) -> None:
        """
        Push branch to remote.

        Args:
            repo: GitPython Repo object
            branch: Optional branch name (default: current branch)
            remote: Remote name (default: origin)
            force: Whether to force push

        Raises:
            GitCommandError: If push fails
        """
        try:
            # Get current branch if not specified
            if not branch:
                branch = repo.active_branch.name

            # Get remote
            remote_obj = repo.remote(remote)

            # Push
            logger.info(f"Pushing branch {branch} to {remote}")
            if force:
                logger.warning(f"Force pushing to {remote}/{branch}")
                remote_obj.push(branch, force=True)
            else:
                remote_obj.push(branch)

            logger.info(f"Successfully pushed {branch} to {remote}")

        except GitCommandError as e:
            logger.error(f"Failed to push branch {branch}: {e}")
            raise

    async def checkout(
        self,
        repo: Repo,
        branch: str
    ) -> None:
        """
        Checkout an existing branch.

        Args:
            repo: GitPython Repo object
            branch: Branch name to checkout

        Raises:
            GitCommandError: If checkout fails
        """
        try:
            logger.info(f"Checking out branch {branch}")
            repo.git.checkout(branch)

        except GitCommandError as e:
            logger.error(f"Failed to checkout branch {branch}: {e}")
            raise

    async def get_status(self, repo: Repo) -> Dict[str, Any]:
        """
        Get repository status.

        Args:
            repo: GitPython Repo object

        Returns:
            Dictionary with status information
        """
        try:
            return {
                "branch": repo.active_branch.name,
                "modified": [item.a_path for item in repo.index.diff(None)],
                "staged": [item.a_path for item in repo.index.diff("HEAD")],
                "untracked": repo.untracked_files,
                "is_dirty": repo.is_dirty()
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise

    async def get_remote_url(self, repo: Repo, remote: str = "origin") -> str:
        """
        Get remote URL.

        Args:
            repo: GitPython Repo object
            remote: Remote name (default: origin)

        Returns:
            Remote URL
        """
        try:
            remote_obj = repo.remote(remote)
            return list(remote_obj.urls)[0]
        except Exception as e:
            logger.error(f"Failed to get remote URL: {e}")
            raise

    def __repr__(self) -> str:
        return "GitService()"
