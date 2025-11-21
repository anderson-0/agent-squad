"""Git push operation with automatic retry and conflict handling. Token-efficient."""
import time
import asyncio
import logging
from typing import Dict, Any, List
from ..utils import run_sandbox_command, classify_error_type, build_git_command, escape_shell_string

logger = logging.getLogger(__name__)


class PushOperation:
    """Push changes to remote with automatic retry on conflict (max 3 attempts, exponential backoff)."""

    def __init__(self, sandbox_manager, metrics, max_retries: int = 3, default_branch: str = "main"):
        self.sandbox_manager = sandbox_manager
        self.metrics = metrics
        self.max_retries = max_retries
        self.default_branch = default_branch

    async def execute(
        self,
        sandbox_id: str,
        commit_message: str,
        files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Push changes with automatic retry.

        Args:
            sandbox_id: Sandbox ID from clone operation
            commit_message: Commit message for changes
            files: Files to stage (optional, default: all changes)

        Returns: {success, commit_hash, pushed_branch, attempt} or {success: False, error, attempt}
        """
        if not sandbox_id or not commit_message:
            return {"success": False, "error": "Missing required params: sandbox_id, commit_message"}

        # Get sandbox from cache
        sandbox = await self.sandbox_manager.get_sandbox(sandbox_id)
        if not sandbox:
            await self.metrics.record_cache_miss()
            await self.metrics.record_failure('push', 0, 'sandbox_not_found')
            return {
                "success": False,
                "error": f"Sandbox {sandbox_id} not found in cache"
            }

        await self.metrics.record_cache_hit()
        await self.metrics.record_start('push')
        start_time = time.time()

        try:
            # Stage files
            if files:
                stage_cmd = build_git_command(f"git add {' '.join(files)}")
            else:
                stage_cmd = build_git_command("git add .")

            stage_result = await run_sandbox_command(sandbox, stage_cmd)
            if stage_result["exit_code"] != 0:
                return {"success": False, "error": f"Stage failed: {stage_result['stderr']}", "attempt": 0}

            # Commit changes
            escaped_msg = escape_shell_string(commit_message)
            commit_cmd = build_git_command(f"git commit -m '{escaped_msg}'")
            commit_result = await run_sandbox_command(sandbox, commit_cmd)

            if commit_result["exit_code"] != 0:
                if "nothing to commit" in commit_result["stdout"]:
                    return {"success": False, "error": "Nothing to commit (no changes)", "attempt": 0}
                return {"success": False, "error": f"Commit failed: {commit_result['stderr']}", "attempt": 0}

            # Get commit hash
            hash_cmd = build_git_command("git rev-parse HEAD")
            hash_result = await run_sandbox_command(sandbox, hash_cmd)
            commit_hash = hash_result["stdout"].strip()[:7] if hash_result["exit_code"] == 0 else None

            # Retry logic for push
            for attempt in range(self.max_retries):
                # Pull with rebase before push
                pull_cmd = build_git_command(f"git pull --rebase origin {self.default_branch}")
                pull_result = await run_sandbox_command(sandbox, pull_cmd)

                # Check for conflicts
                if pull_result["exit_code"] != 0:
                    if "CONFLICT" in pull_result["stdout"] or "CONFLICT" in pull_result["stderr"]:
                        logger.warning(f"Conflict on attempt {attempt + 1}/{self.max_retries}")

                        if attempt < self.max_retries - 1:
                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            duration = time.time() - start_time
                            await self.metrics.record_failure('push', duration, 'conflict')
                            return {
                                "success": False,
                                "error": "Failed to resolve conflicts after retries",
                                "attempt": attempt + 1,
                                "commit_hash": commit_hash
                            }

                # Push to remote
                push_cmd = build_git_command("git push origin HEAD")
                push_result = await run_sandbox_command(sandbox, push_cmd)

                if push_result["exit_code"] == 0:
                    # Get pushed branch
                    branch_cmd = build_git_command("git branch --show-current")
                    branch_result = await run_sandbox_command(sandbox, branch_cmd)
                    pushed_branch = branch_result["stdout"].strip() if branch_result["exit_code"] == 0 else "unknown"

                    # Success
                    duration = time.time() - start_time
                    await self.metrics.record_success('push', duration)

                    return {
                        "success": True,
                        "commit_hash": commit_hash,
                        "pushed_branch": pushed_branch,
                        "attempt": attempt + 1
                    }
                else:
                    # Push rejected
                    if "rejected" in push_result["stderr"] or "failed to push" in push_result["stderr"]:
                        logger.warning(f"Push rejected on attempt {attempt + 1}/{self.max_retries}")

                        if attempt < self.max_retries - 1:
                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            duration = time.time() - start_time
                            await self.metrics.record_failure('push', duration, 'rejected')
                            return {
                                "success": False,
                                "error": f"Push rejected after {self.max_retries} attempts: {push_result['stderr']}",
                                "attempt": attempt + 1,
                                "commit_hash": commit_hash
                            }
                    else:
                        # Other error, don't retry
                        duration = time.time() - start_time
                        await self.metrics.record_failure('push', duration, 'other')
                        return {
                            "success": False,
                            "error": f"Push failed: {push_result['stderr']}",
                            "attempt": attempt + 1,
                            "commit_hash": commit_hash
                        }

            # Should not reach here
            duration = time.time() - start_time
            await self.metrics.record_failure('push', duration, 'other')
            return {
                "success": False,
                "error": "Push failed after all retries",
                "attempt": self.max_retries,
                "commit_hash": commit_hash
            }

        except Exception as e:
            duration = time.time() - start_time
            error_type = classify_error_type(str(e))
            await self.metrics.record_failure('push', duration, error_type)
            logger.error(f"Push operation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e), "attempt": 0}
