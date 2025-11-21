"""Git diff operation. Token-efficient."""
import time
import logging
from typing import Dict, Any, List
from ..utils import run_sandbox_command, classify_error_type, build_git_command

logger = logging.getLogger(__name__)


class DiffOperation:
    """Get git diff of changes."""

    def __init__(self, sandbox_manager, metrics):
        self.sandbox_manager = sandbox_manager
        self.metrics = metrics

    async def execute(self, sandbox_id: str, files: List[str] = None) -> Dict[str, Any]:
        """
        Get git diff.

        Args:
            sandbox_id: Sandbox ID from clone operation
            files: Specific files to diff (optional, default: all changes)

        Returns: {success, diff} or {success: False, error}
        """
        if not sandbox_id:
            return {"success": False, "error": "Missing required param: sandbox_id"}

        # Get sandbox from cache
        sandbox = await self.sandbox_manager.get_sandbox(sandbox_id)
        if not sandbox:
            await self.metrics.record_cache_miss()
            await self.metrics.record_failure('diff', 0, 'sandbox_not_found')
            return {
                "success": False,
                "error": f"Sandbox {sandbox_id} not found in cache"
            }

        await self.metrics.record_cache_hit()
        await self.metrics.record_start('diff')
        start_time = time.time()

        try:
            # Build diff command
            diff_cmd = "git diff"
            if files:
                diff_cmd += " " + " ".join(files)

            diff_cmd = build_git_command(diff_cmd)

            # Execute diff
            diff_result = await run_sandbox_command(sandbox, diff_cmd)

            if diff_result["exit_code"] != 0:
                duration = time.time() - start_time
                await self.metrics.record_failure('diff', duration, 'other')
                return {
                    "success": False,
                    "error": f"Diff failed: {diff_result['stderr']}"
                }

            # Success
            duration = time.time() - start_time
            await self.metrics.record_success('diff', duration)

            return {
                "success": True,
                "diff": diff_result["stdout"]
            }

        except Exception as e:
            duration = time.time() - start_time
            error_type = classify_error_type(str(e))
            await self.metrics.record_failure('diff', duration, error_type)
            logger.error(f"Diff operation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
