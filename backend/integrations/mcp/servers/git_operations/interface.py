"""Protocol definitions for git operations. Minimal typing for token efficiency."""
from typing import Protocol, Dict, Any, Optional, Tuple
from typing_extensions import runtime_checkable


@runtime_checkable
class GitOperation(Protocol):
    """Protocol for git operations."""
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute operation. Returns: {success, error?, data?}. Raises: ValueError, RuntimeError."""
        ...


@runtime_checkable
class SandboxManager(Protocol):
    """Protocol for E2B sandbox management."""
    async def get_sandbox(self, sandbox_id: str) -> Optional[Any]:
        """Get cached sandbox. Returns None if not found."""
        ...

    async def create_sandbox(self) -> Tuple[str, Any]:
        """Create new sandbox. Returns: (sandbox_id, sandbox_obj). Raises: RuntimeError."""
        ...


@runtime_checkable
class MetricsRecorder(Protocol):
    """Protocol for metrics recording."""
    async def record_start(self, operation: str):
        """Record operation start (fire-and-forget)."""
        ...

    async def record_success(self, operation: str, duration: float):
        """Record successful operation (fire-and-forget)."""
        ...

    async def record_failure(self, operation: str, duration: float, error_type: str):
        """Record failed operation (fire-and-forget)."""
        ...

    async def record_cache_hit(self):
        """Record sandbox cache hit (fire-and-forget)."""
        ...

    async def record_cache_miss(self):
        """Record sandbox cache miss (fire-and-forget)."""
        ...
