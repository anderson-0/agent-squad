"""Git status operation. Token-efficient."""
import time
import logging
from typing import Dict, Any
from ..utils import run_sandbox_command, classify_error_type, build_git_command, parse_git_status

logger = logging.getLogger(__name__)


class StatusOperation:
    """Get current git status (modified, staged, untracked files)."""

    def __init__(self, sandbox_manager, metrics):
        self.sandbox_manager = sandbox_manager
        self.metrics = metrics

    async def execute(self, sandbox_id: str) -> Dict[str, Any]:
        """
        Get git status.

        Args:
            sandbox_id: Sandbox ID from clone operation

        Returns: {success, modified, untracked, staged, current_branch} or {success: False, error}
        """
        if not sandbox_id:
            return {"success": False, "error": "Missing required param: sandbox_id"}

        # Get sandbox from cache
        sandbox = await self.sandbox_manager.get_sandbox(sandbox_id)
        if not sandbox:
            await self.metrics.record_cache_miss()
            await self.metrics.record_failure('status', 0, 'sandbox_not_found')
            return {
                "success": False,
                "error": f"Sandbox {sandbox_id} not found in cache"
            }

        await self.metrics.record_cache_hit()
        await self.metrics.record_start('status')
        start_time = time.time()

        try:
            # Get git status
            status_cmd = build_git_command("git status --porcelain")
            status_result = await run_sandbox_command(sandbox, status_cmd)

            if status_result["exit_code"] != 0:
                duration = time.time() - start_time
                await self.metrics.record_failure('status', duration, 'other')
                return {
                    "success": False,
                    "error": f"Status failed: {status_result['stderr']}"
                }

            # Parse status output
            parsed = parse_git_status(status_result["stdout"])

            # Get current branch
            branch_cmd = build_git_command("git branch --show-current")
            branch_result = await run_sandbox_command(sandbox, branch_cmd)
            current_branch = branch_result["stdout"].strip() if branch_result["exit_code"] == 0 else "unknown"

            # Success
            duration = time.time() - start_time
            await self.metrics.record_success('status', duration)

            return {
                "success": True,
                "modified": parsed["modified"],
                "untracked": parsed["untracked"],
                "staged": parsed["staged"],
                "current_branch": current_branch
            }

        except Exception as e:
            duration = time.time() - start_time
            error_type = classify_error_type(str(e))
            await self.metrics.record_failure('status', duration, error_type)
            logger.error(f"Status operation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
