"""Git pull operation with conflict detection. Token-efficient."""
import time
import logging
from typing import Dict, Any
from ..utils import run_sandbox_command, classify_error_type, build_git_command

logger = logging.getLogger(__name__)


class PullOperation:
    """Pull latest changes from remote with optional auto-rebase."""

    def __init__(self, sandbox_manager, metrics, default_branch: str = "main"):
        self.sandbox_manager = sandbox_manager
        self.metrics = metrics
        self.default_branch = default_branch

    async def execute(self, sandbox_id: str, auto_rebase: bool = True) -> Dict[str, Any]:
        """
        Pull latest changes.

        Args:
            sandbox_id: Sandbox ID from clone operation
            auto_rebase: Automatically rebase on pull (default: True)

        Returns: {success, conflicts, has_conflicts, output} or {success: False, error}
        """
        if not sandbox_id:
            return {"success": False, "error": "Missing required param: sandbox_id"}

        # Get sandbox from cache
        sandbox = await self.sandbox_manager.get_sandbox(sandbox_id)
        if not sandbox:
            await self.metrics.record_cache_miss()
            await self.metrics.record_failure('pull', 0, 'sandbox_not_found')
            return {
                "success": False,
                "error": f"Sandbox {sandbox_id} not found in cache"
            }

        await self.metrics.record_cache_hit()
        await self.metrics.record_start('pull')
        start_time = time.time()

        try:
            # Build pull command
            pull_cmd = "git pull"
            if auto_rebase:
                pull_cmd += " --rebase"
            pull_cmd += f" origin {self.default_branch}"

            pull_cmd = build_git_command(pull_cmd)

            # Execute pull
            pull_result = await run_sandbox_command(sandbox, pull_cmd)

            # Check for conflicts
            has_conflicts = "CONFLICT" in pull_result["stdout"] or "CONFLICT" in pull_result["stderr"]
            conflicts = []

            if has_conflicts:
                # Parse conflict files
                conflict_cmd = build_git_command("git diff --name-only --diff-filter=U")
                conflict_result = await run_sandbox_command(sandbox, conflict_cmd)

                if conflict_result["exit_code"] == 0:
                    conflicts = [f.strip() for f in conflict_result["stdout"].strip().split("\n") if f.strip()]

            # Success or conflict
            success = pull_result["exit_code"] == 0
            duration = time.time() - start_time

            if success:
                await self.metrics.record_success('pull', duration)
            else:
                error_type = 'conflict' if has_conflicts else classify_error_type(pull_result["stderr"])
                await self.metrics.record_failure('pull', duration, error_type)

            return {
                "success": success,
                "conflicts": conflicts,
                "has_conflicts": has_conflicts,
                "output": pull_result["stdout"],
                "error": pull_result["stderr"] if not success else None
            }

        except Exception as e:
            duration = time.time() - start_time
            error_type = classify_error_type(str(e))
            await self.metrics.record_failure('pull', duration, error_type)
            logger.error(f"Pull operation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conflicts": [],
                "has_conflicts": False
            }
