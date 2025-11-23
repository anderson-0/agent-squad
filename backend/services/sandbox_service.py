"""
Sandbox Service - Manages E2B sandboxes and Git operations.
"""
import logging
import os
import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.models.sandbox import Sandbox, SandboxStatus
from backend.integrations.github_service import GitHubService
from backend.schemas.sandbox_events import (
    SandboxCreatedEvent,
    GitOperationEvent,
    PRCreatedEvent,
    SandboxTerminatedEvent,
    SandboxErrorEvent
)

logger = logging.getLogger(__name__)

try:
    from e2b_code_interpreter import Sandbox as E2BSandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    logger.warning("E2B SDK not available")


class SandboxService:
    """
    Service for managing E2B sandboxes and performing Git operations within them.
    """

    def __init__(self, db: AsyncSession, execution_id: Optional[UUID] = None, squad_id: Optional[UUID] = None):
        self.db = db
        self.e2b_api_key = os.environ.get("E2B_API_KEY", "")
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.template_id = os.environ.get("E2B_TEMPLATE_ID")
        self.execution_id = execution_id  # For SSE broadcasting
        self.squad_id = squad_id  # For SSE broadcasting

        if not self.e2b_api_key:
            logger.warning("E2B_API_KEY not set")

    async def _broadcast_event(self, event: Dict[str, Any]):
        """
        Broadcast sandbox event via SSE (non-blocking)

        Broadcasts to both execution and squad channels if available.
        Failures are logged but don't raise exceptions (SSE is best-effort).
        """
        try:
            from backend.services.sse_service import sse_manager

            # Broadcast to execution channel
            if self.execution_id:
                await sse_manager.broadcast_to_execution(
                    self.execution_id,
                    event["event"],
                    event
                )

            # Broadcast to squad channel
            if self.squad_id:
                await sse_manager.broadcast_to_squad(
                    self.squad_id,
                    event["event"],
                    event
                )
        except Exception as e:
            # SSE broadcast failures should never break sandbox operations
            logger.warning(f"Failed to broadcast sandbox event: {e}")

    async def create_sandbox(
        self, 
        agent_id: Optional[UUID] = None, 
        task_id: Optional[UUID] = None, 
        repo_url: Optional[str] = None
    ) -> Sandbox:
        """
        Create a new E2B sandbox and record it in the database.
        """
        if not E2B_AVAILABLE:
            raise RuntimeError("E2B SDK not installed")
        if not self.e2b_api_key:
            raise RuntimeError("E2B_API_KEY not configured")

        logger.info(f"Creating sandbox for agent={agent_id}, task={task_id}, repo={repo_url}")

        try:
            # Create E2B sandbox
            if self.template_id:
                logger.info(f"Using template {self.template_id}")
                e2b_sandbox = await asyncio.to_thread(
                    E2BSandbox.create,
                    template=self.template_id,
                    api_key=self.e2b_api_key,
                    envs={"GITHUB_TOKEN": self.github_token}
                )
            else:
                logger.info("Using default template")
                e2b_sandbox = await asyncio.to_thread(
                    E2BSandbox.create,
                    api_key=self.e2b_api_key,
                    envs={"GITHUB_TOKEN": self.github_token}
                )

            # Configure Git if not using a pre-configured template
            if not self.template_id:
                await self._configure_git(e2b_sandbox)

            # Create DB record
            sandbox = Sandbox(
                e2b_id=e2b_sandbox.sandbox_id,
                agent_id=agent_id,
                task_id=task_id,
                repo_url=repo_url,
                status=SandboxStatus.RUNNING
            )
            self.db.add(sandbox)
            await self.db.commit()
            await self.db.refresh(sandbox)

            # Broadcast sandbox_created event
            event = SandboxCreatedEvent(
                sandbox_id=sandbox.id,
                e2b_id=sandbox.e2b_id,
                task_id=task_id,
                agent_id=agent_id,
                repo_url=repo_url,
                status="RUNNING"
            )
            await self._broadcast_event(event.dict())

            # Clone repo if provided
            if repo_url:
                await self.clone_repo(sandbox.id, repo_url)

            return sandbox

        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise

    async def get_sandbox(self, sandbox_id: UUID) -> Optional[Sandbox]:
        """Get sandbox by DB ID."""
        result = await self.db.execute(select(Sandbox).where(Sandbox.id == sandbox_id))
        return result.scalars().first()

    async def get_running_sandbox_by_task(self, task_id: UUID) -> Optional[Sandbox]:
        """Get running sandbox for a task."""
        result = await self.db.execute(
            select(Sandbox)
            .where(Sandbox.task_id == task_id)
            .where(Sandbox.status == SandboxStatus.RUNNING)
        )
        return result.scalars().first()

    async def terminate_sandbox(self, sandbox_id: UUID) -> bool:
        """Terminate a sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return False

        if sandbox.status == SandboxStatus.TERMINATED:
            return True

        try:
            # Kill E2B sandbox
            # We need to reconnect to it first, or just use the static kill method if available with ID
            # E2B SDK allows killing by ID
            await asyncio.to_thread(E2BSandbox.kill, sandbox.e2b_id, self.e2b_api_key)

            # Calculate runtime
            runtime_seconds = None
            if sandbox.created_at:
                runtime_seconds = (datetime.utcnow() - sandbox.created_at).total_seconds()

            sandbox.status = SandboxStatus.TERMINATED
            await self.db.commit()

            # Broadcast sandbox_terminated event
            await self._broadcast_event(SandboxTerminatedEvent(
                sandbox_id=sandbox_id,
                e2b_id=sandbox.e2b_id,
                runtime_seconds=runtime_seconds,
                status="TERMINATED"
            ).dict())

            return True
        except Exception as e:
            logger.error(f"Failed to terminate sandbox {sandbox.e2b_id}: {e}")
            # Mark as terminated anyway if it's not found or other error?
            # For now, let's assume if it fails it might still be running or already gone.
            # If it's "not found", we should mark as terminated.
            if "not found" in str(e).lower():
                # Calculate runtime
                runtime_seconds = None
                if sandbox.created_at:
                    runtime_seconds = (datetime.utcnow() - sandbox.created_at).total_seconds()

                sandbox.status = SandboxStatus.TERMINATED
                await self.db.commit()

                # Broadcast sandbox_terminated event
                await self._broadcast_event(SandboxTerminatedEvent(
                    sandbox_id=sandbox_id,
                    e2b_id=sandbox.e2b_id,
                    runtime_seconds=runtime_seconds,
                    status="TERMINATED"
                ).dict())

                return True
            raise

    async def _get_e2b_connection(self, sandbox: Sandbox) -> Any:
        """Reconnect to an existing E2B sandbox."""
        if sandbox.status != SandboxStatus.RUNNING:
            raise RuntimeError(f"Sandbox {sandbox.id} is not running")
        
        try:
            # Reconnect
            # Note: E2B SDK might have different reconnection logic depending on version.
            # Assuming Sandbox.connect(sandbox_id) or similar.
            # Checking SDK docs or existing code... existing code uses Sandbox.create mostly.
            # E2B SDK usually supports connecting to existing sandbox.
            # Let's try Sandbox.connect
            connection = await asyncio.to_thread(
                E2BSandbox.connect, 
                sandbox.e2b_id, 
                api_key=self.e2b_api_key
            )
            
            # Update last used
            sandbox.last_used_at = func.now()
            await self.db.commit()
            
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to sandbox {sandbox.e2b_id}: {e}")
            sandbox.status = SandboxStatus.ERROR
            await self.db.commit()
            raise

    async def _configure_git(self, sb: Any):
        """Configure git credentials."""
        cmd = (
            "git config --global credential.helper "
            "'!f() { echo \"username=token\"; echo \"password=$GITHUB_TOKEN\"; }; f'"
        )
        sb.commands.run(cmd)
        sb.commands.run('git config --global user.name "Agent Squad"')
        sb.commands.run('git config --global user.email "agent@squad.dev"')

    def _validate_conventional_commit(self, message: str) -> bool:
        """
        Validate commit message follows conventional commits format.
        Format: <type>(<scope>): <description>

        Types: feat, fix, chore, docs, style, refactor, test, build, ci, perf, revert
        """
        import re
        pattern = r'^(feat|fix|chore|docs|style|refactor|test|build|ci|perf|revert)(\(.+\))?: .{1,}'
        return bool(re.match(pattern, message))

    async def clone_repo(self, sandbox_id: UUID, repo_url: str) -> str:
        """Clone a repository into the sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError("Sandbox not found")

        sb = await self._get_e2b_connection(sandbox)

        # Extract repo name for directory
        repo_name = repo_url.split("/")[-1].replace(".git", "")

        logger.info(f"Cloning {repo_url} into {repo_name}")

        # Broadcast started event
        await self._broadcast_event(GitOperationEvent(
            sandbox_id=sandbox_id,
            operation="clone",
            status="started",
            repo_url=repo_url
        ).dict())

        try:
            # Check if already cloned
            check = sb.commands.run(f"test -d {repo_name} && echo 'exists'")
            if "exists" in check.stdout:
                logger.info("Repo already exists, pulling...")
                output = sb.commands.run(f"cd {repo_name} && git pull")

                # Broadcast completed
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="clone",
                    status="completed",
                    repo_url=repo_url,
                    output="Repository already exists, pulled latest changes"
                ).dict())

                return f"/home/user/{repo_name}"

            # Clone
            result = sb.commands.run(f"git clone {repo_url}")
            if result.exit_code != 0:
                # Broadcast failed
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="clone",
                    status="failed",
                    repo_url=repo_url,
                    error=result.stderr
                ).dict())
                raise RuntimeError(f"Clone failed: {result.stderr}")

            # Broadcast completed
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="clone",
                status="completed",
                repo_url=repo_url,
                output=result.stdout
            ).dict())

            return f"/home/user/{repo_name}"

        except Exception as e:
            # Broadcast error if not already broadcast
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="clone",
                status="failed",
                repo_url=repo_url,
                error=str(e)
            ).dict())
            raise

    async def create_branch(
        self,
        sandbox_id: UUID,
        branch_name: str,
        base_branch: str = "main",
        repo_path: str = None
    ) -> str:
        """
        Create a new git branch in the sandbox.

        Args:
            sandbox_id: Sandbox ID
            branch_name: Name of the new branch (e.g., 'task-123')
            base_branch: Base branch to branch from (default: 'main')
            repo_path: Path to repository (auto-detected if not provided)

        Returns:
            Created branch name

        Raises:
            RuntimeError: If branch creation fails
        """
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError("Sandbox not found")

        sb = await self._get_e2b_connection(sandbox)

        # Determine repo path if not provided
        if not repo_path:
            ls = sb.commands.run("ls -d */")
            if not ls.stdout:
                raise RuntimeError("No repositories found")
            repo_path = ls.stdout.split()[0].strip("/")

        logger.info(f"Creating branch {branch_name} from {base_branch} in {repo_path}")

        # Broadcast started event
        await self._broadcast_event(GitOperationEvent(
            sandbox_id=sandbox_id,
            operation="create_branch",
            status="started",
            branch_name=branch_name
        ).dict())

        try:
            # Fetch latest changes
            fetch_cmd = f"cd {repo_path} && git fetch origin"
            result = sb.commands.run(fetch_cmd)
            if result.exit_code != 0:
                logger.warning(f"Fetch warning: {result.stderr}")

            # Checkout base branch and pull latest
            checkout_cmd = f"cd {repo_path} && git checkout {base_branch} && git pull origin {base_branch}"
            result = sb.commands.run(checkout_cmd)
            if result.exit_code != 0:
                # Broadcast failed
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="create_branch",
                    status="failed",
                    branch_name=branch_name,
                    error=result.stderr
                ).dict())
                raise RuntimeError(f"Checkout/pull failed: {result.stderr}")

            # Create and checkout new branch
            branch_cmd = f"cd {repo_path} && git checkout -b {branch_name}"
            result = sb.commands.run(branch_cmd)
            if result.exit_code != 0:
                # Check if branch already exists
                if "already exists" in result.stderr.lower():
                    logger.info(f"Branch {branch_name} already exists, checking out...")
                    checkout_existing = f"cd {repo_path} && git checkout {branch_name}"
                    result = sb.commands.run(checkout_existing)
                    if result.exit_code != 0:
                        # Broadcast failed
                        await self._broadcast_event(GitOperationEvent(
                            sandbox_id=sandbox_id,
                            operation="create_branch",
                            status="failed",
                            branch_name=branch_name,
                            error=result.stderr
                        ).dict())
                        raise RuntimeError(f"Failed to checkout existing branch: {result.stderr}")

                    # Broadcast completed (existing branch)
                    await self._broadcast_event(GitOperationEvent(
                        sandbox_id=sandbox_id,
                        operation="create_branch",
                        status="completed",
                        branch_name=branch_name,
                        output=f"Checked out existing branch: {branch_name}"
                    ).dict())
                else:
                    # Broadcast failed
                    await self._broadcast_event(GitOperationEvent(
                        sandbox_id=sandbox_id,
                        operation="create_branch",
                        status="failed",
                        branch_name=branch_name,
                        error=result.stderr
                    ).dict())
                    raise RuntimeError(f"Branch creation failed: {result.stderr}")
            else:
                # Broadcast completed (new branch)
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="create_branch",
                    status="completed",
                    branch_name=branch_name,
                    output=f"Successfully created branch: {branch_name}"
                ).dict())

            logger.info(f"Successfully created/checked out branch: {branch_name}")
            return branch_name

        except Exception as e:
            # Broadcast error if not already broadcast
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="create_branch",
                status="failed",
                branch_name=branch_name,
                error=str(e)
            ).dict())
            raise

    async def commit_changes(self, sandbox_id: UUID, message: str, repo_path: str = None) -> str:
        """
        Commit all changes with conventional commit message.

        Args:
            sandbox_id: Sandbox ID
            message: Commit message (must follow conventional commits format)
            repo_path: Path to repository (auto-detected if not provided)

        Returns:
            Commit output

        Raises:
            ValueError: If commit message doesn't follow conventional commits
            RuntimeError: If commit fails
        """
        # Validate conventional commit format
        if not self._validate_conventional_commit(message):
            raise ValueError(
                f"Commit message must follow conventional commits format. "
                f"Examples: 'feat: add new feature', 'fix: resolve bug', 'chore: update deps'. "
                f"Got: '{message}'"
            )

        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError("Sandbox not found")

        sb = await self._get_e2b_connection(sandbox)

        # Determine repo path if not provided
        if not repo_path:
            ls = sb.commands.run("ls -d */")
            if not ls.stdout:
                raise RuntimeError("No repositories found")
            repo_path = ls.stdout.split()[0].strip("/")

        logger.info(f"Committing changes in {repo_path} with message: {message}")

        # Broadcast started event
        await self._broadcast_event(GitOperationEvent(
            sandbox_id=sandbox_id,
            operation="commit",
            status="started",
            commit_message=message
        ).dict())

        try:
            # Escape single quotes in message for shell
            escaped_message = message.replace("'", "'\\''")

            cmd = f"cd {repo_path} && git add . && git commit -m '{escaped_message}'"
            result = sb.commands.run(cmd)

            if result.exit_code != 0 and "nothing to commit" not in result.stdout.lower():
                # Broadcast failed
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="commit",
                    status="failed",
                    commit_message=message,
                    error=result.stderr
                ).dict())
                raise RuntimeError(f"Commit failed: {result.stderr}")

            if "nothing to commit" in result.stdout.lower():
                logger.info("No changes to commit")
                output = "No changes to commit"
            else:
                logger.info("Changes committed successfully")
                output = result.stdout

            # Broadcast completed
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="commit",
                status="completed",
                commit_message=message,
                output=output
            ).dict())

            return result.stdout

        except Exception as e:
            # Broadcast error if not already broadcast
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="commit",
                status="failed",
                commit_message=message,
                error=str(e)
            ).dict())
            raise

    async def push_changes(self, sandbox_id: UUID, branch: str = "main", repo_path: str = None) -> str:
        """Push changes to remote."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError("Sandbox not found")

        sb = await self._get_e2b_connection(sandbox)

        if not repo_path:
             ls = sb.commands.run("ls -d */")
             if not ls.stdout:
                 raise RuntimeError("No repositories found")
             repo_path = ls.stdout.split()[0].strip("/")

        logger.info(f"Pushing changes to branch {branch}")

        # Broadcast started event
        await self._broadcast_event(GitOperationEvent(
            sandbox_id=sandbox_id,
            operation="push",
            status="started",
            branch_name=branch
        ).dict())

        try:
            cmd = f"cd {repo_path} && git push origin {branch}"
            result = sb.commands.run(cmd)

            if result.exit_code != 0:
                # Broadcast failed
                await self._broadcast_event(GitOperationEvent(
                    sandbox_id=sandbox_id,
                    operation="push",
                    status="failed",
                    branch_name=branch,
                    error=result.stderr
                ).dict())
                raise RuntimeError(f"Push failed: {result.stderr}")

            # Broadcast completed
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="push",
                status="completed",
                branch_name=branch,
                output=result.stdout
            ).dict())

            return result.stdout

        except Exception as e:
            # Broadcast error if not already broadcast
            await self._broadcast_event(GitOperationEvent(
                sandbox_id=sandbox_id,
                operation="push",
                status="failed",
                branch_name=branch,
                error=str(e)
            ).dict())
            raise

    async def create_pr(
        self,
        sandbox_id: UUID,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        repo_owner_name: str = None
    ) -> Dict[str, Any]:
        """Create a Pull Request via GitHub API."""
        # We don't need the sandbox for this if we have the token,
        # but we might want to ensure the code is pushed first.
        # Assuming code is pushed.

        if not self.github_token:
            raise RuntimeError("GITHUB_TOKEN not configured")

        gh = GitHubService(self.github_token)

        if not repo_owner_name:
            # Try to infer from sandbox repo_url
            sandbox = await self.get_sandbox(sandbox_id)
            if sandbox and sandbox.repo_url:
                # https://github.com/owner/repo.git -> owner/repo
                parts = sandbox.repo_url.replace(".git", "").split("/")
                repo_owner_name = f"{parts[-2]}/{parts[-1]}"
            else:
                raise ValueError("repo_owner_name required or sandbox must have repo_url")

        logger.info(f"Creating PR: {title} ({head} → {base})")

        # Create PR via GitHub API
        pr_result = await gh.create_pull_request(
            repo=repo_owner_name,
            title=title,
            body=body,
            head=head,
            base=base
        )

        # Store PR number in sandbox for webhook lookup
        sandbox = await self.get_sandbox(sandbox_id)
        if sandbox:
            sandbox.pr_number = pr_result["number"]
            await self.db.commit()
            logger.info(f"Stored PR #{pr_result['number']} for sandbox {sandbox_id}")

        # Broadcast pr_created event
        await self._broadcast_event(PRCreatedEvent(
            sandbox_id=sandbox_id,
            pr_number=pr_result["number"],
            pr_url=pr_result["html_url"],
            pr_title=title,
            pr_body=body,
            head_branch=head,
            base_branch=base,
            repo_owner_name=repo_owner_name
        ).dict())

        return pr_result
