"""Git Operations - Modular architecture. Token-efficient exports."""
from .facade import GitOperationsFacade
from .interface import GitOperation, SandboxManager, MetricsRecorder

__all__ = [
    "GitOperationsFacade",
    "GitOperation",
    "SandboxManager",
    "MetricsRecorder",
]

__version__ = "2.0.0"  # Phase 2: Modular architecture
