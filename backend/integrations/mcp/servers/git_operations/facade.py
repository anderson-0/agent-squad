"""Git Operations Facade - Single entry point. Token-efficient (~50 lines)."""
from typing import Dict, Any, Optional
from .operations import CloneOperation, StatusOperation, DiffOperation, PullOperation, PushOperation
from .sandbox import SandboxManager
from .metrics import MetricsRecorder


class GitOperationsFacade:
    """
    Phase 3: Single entry point for git operations with template, pooling, dynamic TTL.

    Call initialize() after construction to warm up connection pool.
    Call shutdown() before exit to cleanup resources.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize facade with config.

        Args:
            config: {e2b_api_key?, github_token?, timeout?, max_retries?, default_branch?,
                     e2b_template_id?, sandbox_pool_min_size?, sandbox_pool_max_size?}
        """
        self.config = config or {}

        # Initialize shared components
        self.sandbox_manager = SandboxManager(self.config)
        self.metrics = MetricsRecorder()

        # Build operation registry
        default_branch = self.config.get("default_branch", "main")
        max_retries = self.config.get("max_retries", 3)

        self._operations: Dict[str, Any] = {
            'clone': CloneOperation(self.sandbox_manager, self.metrics),
            'status': StatusOperation(self.sandbox_manager, self.metrics),
            'diff': DiffOperation(self.sandbox_manager, self.metrics),
            'pull': PullOperation(self.sandbox_manager, self.metrics, default_branch),
            'push': PushOperation(self.sandbox_manager, self.metrics, max_retries, default_branch),
        }

    async def initialize(self):
        """
        Phase 3: Initialize facade - warm pool and start background tasks.

        Call once after construction, before executing operations.
        Warms up connection pool (2+ sandboxes) for instant access.
        """
        await self.sandbox_manager.initialize()

    async def shutdown(self):
        """
        Phase 3: Shutdown facade - cleanup resources and kill sandboxes.

        Call before exit to gracefully cleanup.
        """
        await self.sandbox_manager.shutdown()

    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Execute git operation.

        Args:
            operation: Operation name (clone|status|diff|pull|push)
            **kwargs: Operation-specific args

        Returns: {success, ...} or {success: False, error}
        Raises: KeyError if operation unknown
        """
        if operation not in self._operations:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        return await self._operations[operation].execute(**kwargs)

    def list_operations(self) -> list:
        """List available operations."""
        return list(self._operations.keys())
