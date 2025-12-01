"""Shared utilities for git operations. Token-efficient helpers."""
import asyncio
from typing import Any, Dict


async def run_sandbox_command(sandbox: Any, command: str, timeout: int = 60) -> Dict[str, Any]:
    """Run command in sandbox. Returns: {exit_code, stdout, stderr}. Raises: TimeoutError."""
    def _run_sync():
        result = sandbox.commands.run(command, timeout=timeout)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    return await asyncio.to_thread(_run_sync)


def classify_error_type(error_msg: str) -> str:
    """Classify error message into bounded error types for metrics."""
    error_lower = error_msg.lower()

    if 'timeout' in error_lower:
        return 'timeout'
    elif 'auth' in error_lower or 'credential' in error_lower or 'permission' in error_lower:
        return 'auth'
    elif 'network' in error_lower or 'connection' in error_lower:
        return 'network'
    elif 'conflict' in error_lower:
        return 'conflict'
    elif 'sandbox' in error_lower and 'not found' in error_lower:
        return 'sandbox_not_found'
    else:
        return 'other'


def build_git_command(base_cmd: str, repo_path: str = "/workspace/repo") -> str:
    """Build git command with repo path prefix."""
    return f"cd {repo_path} && {base_cmd}"


def parse_git_status(status_output: str) -> Dict[str, list]:
    """Parse `git status --porcelain` output. Returns: {modified, untracked, staged}."""
    modified = []
    untracked = []
    staged = []

    for line in status_output.strip().split("\n"):
        if not line:
            continue

        status_code = line[:2]
        filepath = line[3:]

        if status_code[0] != " " and status_code[0] != "?":
            staged.append(filepath)
        if status_code[1] == "M":
            modified.append(filepath)
        if status_code == "??":
            untracked.append(filepath)

    return {"modified": modified, "untracked": untracked, "staged": staged}


def escape_shell_string(s: str) -> str:
    """Escape string for safe shell execution."""
    return s.replace("'", "'\\''")
