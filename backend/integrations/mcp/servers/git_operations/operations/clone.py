"""Clone git repository operation. Concise for token efficiency."""
import time
import logging
from typing import Dict, Any
from ..utils import run_sandbox_command, classify_error_type, build_git_command

logger = logging.getLogger(__name__)


class CloneOperation:
    """Clone git repository with optional shallow clone (70-90% faster)."""

    def __init__(self, sandbox_manager, metrics):
        self.sandbox_manager = sandbox_manager
        self.metrics = metrics

    async def execute(
        self,
        repo_url: str,
        branch: str = "main",
        agent_id: str = None,
        task_id: str = None,
        shallow: bool = False
    ) -> Dict[str, Any]:
        """
        Clone repo and create agent branch.

        Args:
            repo_url: Git repository URL (HTTPS)
            branch: Base branch to checkout (default: main)
            agent_id: Agent ID for branch naming (required)
            task_id: Task ID for branch naming (required)
            shallow: Use shallow clone (--depth=1 --single-branch) for 70-90% speedup

        Returns: {success, sandbox_id, agent_branch, workspace_path} or {success: False, error}
        Raises: ValueError if required params missing
        """
        # Validate
        if not repo_url or not agent_id or not task_id:
            return {"success": False, "error": "Missing required params: repo_url, agent_id, task_id"}

        await self.metrics.record_start('clone')
        start_time = time.time()

        try:
            # Create sandbox
            sandbox_id, sandbox = await self.sandbox_manager.create_sandbox()

            # Record sandbox creation
            creation_duration = time.time() - start_time
            await self.metrics.record_sandbox_creation(creation_duration)
            await self.metrics.update_active_sandboxes(self.sandbox_manager.get_active_count())

            # Build clone command
            clone_cmd = f"git clone"
            if shallow:
                clone_cmd += " --depth=1 --single-branch"
            clone_cmd += f" --branch={branch} {repo_url} /workspace/repo"

            # Execute clone
            clone_result = await run_sandbox_command(sandbox, clone_cmd, timeout=120)

            if clone_result["exit_code"] != 0:
                duration = time.time() - start_time
                await self.metrics.record_failure('clone', duration, 'other')
                return {
                    "success": False,
                    "error": f"Clone failed: {clone_result['stderr']}"
                }

            # Create agent branch
            agent_branch = f"agent-{agent_id}-{task_id}"
            branch_cmd = build_git_command(f"git checkout -b {agent_branch}")
            branch_result = await run_sandbox_command(sandbox, branch_cmd)

            if branch_result["exit_code"] != 0:
                duration = time.time() - start_time
                await self.metrics.record_failure('clone', duration, 'other')
                return {
                    "success": False,
                    "error": f"Branch creation failed: {branch_result['stderr']}"
                }

            # Success
            duration = time.time() - start_time
            await self.metrics.record_success('clone', duration)

            return {
                "success": True,
                "sandbox_id": sandbox_id,
                "agent_branch": agent_branch,
                "base_branch": branch,
                "repo_url": repo_url,
                "workspace_path": "/workspace/repo"
            }

        except Exception as e:
            duration = time.time() - start_time
            error_type = classify_error_type(str(e))
            await self.metrics.record_failure('clone', duration, error_type)
            logger.error(f"Clone operation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
