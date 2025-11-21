"""Async Prometheus metrics wrapper. Fire-and-forget pattern for minimal overhead."""
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from backend.monitoring.prometheus_metrics import (
        record_operation_start_async,
        record_operation_success_async,
        record_operation_failure_async,
        record_sandbox_cache_hit_async,
        record_sandbox_cache_miss_async,
        update_active_sandboxes_async,
        record_sandbox_creation_async,
    )
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Prometheus metrics not available")
    METRICS_AVAILABLE = False
    # No-op async functions
    async def record_operation_start_async(*args, **kwargs): pass
    async def record_operation_success_async(*args, **kwargs): pass
    async def record_operation_failure_async(*args, **kwargs): pass
    async def record_sandbox_cache_hit_async(*args, **kwargs): pass
    async def record_sandbox_cache_miss_async(*args, **kwargs): pass
    async def update_active_sandboxes_async(*args, **kwargs): pass
    async def record_sandbox_creation_async(*args, **kwargs): pass


class MetricsRecorder:
    """Async wrapper for Prometheus metrics with fire-and-forget pattern."""

    async def record_start(self, operation: str):
        """Record operation start (fire-and-forget)."""
        asyncio.create_task(record_operation_start_async(operation))

    async def record_success(self, operation: str, duration: float):
        """Record successful operation (fire-and-forget)."""
        asyncio.create_task(record_operation_success_async(operation, duration))

    async def record_failure(self, operation: str, duration: float, error_type: str = 'other'):
        """Record failed operation (fire-and-forget)."""
        asyncio.create_task(record_operation_failure_async(operation, duration, error_type))

    async def record_cache_hit(self):
        """Record sandbox cache hit (fire-and-forget)."""
        asyncio.create_task(record_sandbox_cache_hit_async())

    async def record_cache_miss(self):
        """Record sandbox cache miss (fire-and-forget)."""
        asyncio.create_task(record_sandbox_cache_miss_async())

    async def record_sandbox_creation(self, duration: float):
        """Record sandbox creation time (fire-and-forget)."""
        asyncio.create_task(record_sandbox_creation_async(duration))

    async def update_active_sandboxes(self, count: int):
        """Update active sandboxes gauge (fire-and-forget)."""
        asyncio.create_task(update_active_sandboxes_async(count))
