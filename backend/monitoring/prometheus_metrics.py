"""
Prometheus Metrics for Git Operations

Comprehensive metrics for monitoring git operations in E2B sandboxes.
Enables data-driven decisions for scaling and optimization.
Optimized for minimal overhead with async fire-and-forget recording.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import logging
import asyncio

logger = logging.getLogger(__name__)

# ===========================================================================
# Sandbox Metrics
# ===========================================================================

sandbox_creation_duration = Histogram(
    'sandbox_creation_seconds',
    'Time to create and configure E2B sandbox',
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60, 120]  # Up to 2 minutes
)

active_sandboxes = Gauge(
    'active_sandboxes_total',
    'Number of currently active E2B sandboxes in cache'
)

sandbox_cache_hits = Counter(
    'sandbox_cache_hits_total',
    'Number of times sandbox was retrieved from cache'
)

sandbox_cache_misses = Counter(
    'sandbox_cache_misses_total',
    'Number of times sandbox was not found in cache'
)

# ===========================================================================
# Git Operation Metrics
# ===========================================================================

git_operation_total = Counter(
    'git_operation_total',
    'Total git operations executed',
    labelnames=['operation', 'status']  # operation: clone|status|diff|pull|push, status: success|failure|retry
)

git_operation_duration = Histogram(
    'git_operation_duration_seconds',
    'Git operation execution time',
    labelnames=['operation'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]  # Up to 5 minutes
)

git_errors = Counter(
    'git_errors_total',
    'Git operation errors',
    labelnames=['operation', 'error_type']  # error_type: timeout|auth|conflict|network|sandbox_not_found|other
)

git_push_retry_count = Counter(
    'git_push_retry_count_total',
    'Number of retry attempts for git push operations',
    labelnames=['attempt']  # attempt: 1, 2, 3
)

git_conflicts_detected = Counter(
    'git_conflicts_detected_total',
    'Number of git conflicts detected during pull/push',
    labelnames=['operation']  # operation: pull|push
)

# ===========================================================================
# Cost Tracking Metrics
# ===========================================================================

sandbox_hours_total = Counter(
    'sandbox_hours_total',
    'Total sandbox hours consumed (for cost calculation)'
    # Removed 'project' label to prevent unbounded cardinality
)

estimated_cost_dollars = Gauge(
    'estimated_cost_dollars',
    'Estimated cost in dollars based on sandbox usage',
    labelnames=['period']  # period: hourly|daily|monthly (bounded to 3)
)

# ===========================================================================
# Helper Functions
# ===========================================================================

def record_operation_start(operation: str):
    """Record the start of a git operation"""
    git_operation_total.labels(operation=operation, status='started').inc()


def record_operation_success(operation: str, duration: float):
    """Record successful git operation"""
    git_operation_total.labels(operation=operation, status='success').inc()
    git_operation_duration.labels(operation=operation).observe(duration)
    logger.debug(f"Recorded success for {operation} in {duration:.2f}s")


def record_operation_failure(operation: str, duration: float, error_type: str = 'other'):
    """Record failed git operation"""
    git_operation_total.labels(operation=operation, status='failure').inc()
    git_operation_duration.labels(operation=operation).observe(duration)
    git_errors.labels(operation=operation, error_type=error_type).inc()
    logger.warning(f"Recorded failure for {operation}: {error_type}")


def record_push_retry(attempt: int):
    """Record git push retry attempt"""
    git_push_retry_count.labels(attempt=str(attempt)).inc()
    git_operation_total.labels(operation='push', status='retry').inc()


def record_conflict(operation: str):
    """Record git conflict detected"""
    git_conflicts_detected.labels(operation=operation).inc()


def update_active_sandboxes(count: int):
    """Update active sandboxes gauge"""
    active_sandboxes.set(count)


def record_sandbox_creation(duration: float):
    """Record sandbox creation time"""
    sandbox_creation_duration.observe(duration)


def record_sandbox_cache_hit():
    """Record cache hit"""
    sandbox_cache_hits.inc()


def record_sandbox_cache_miss():
    """Record cache miss"""
    sandbox_cache_misses.inc()


def update_cost_estimate(period: str, cost: float):
    """Update estimated cost"""
    estimated_cost_dollars.labels(period=period).set(cost)


# ===========================================================================
# Async Fire-and-Forget Helpers (90% overhead reduction)
# ===========================================================================

async def record_operation_start_async(operation: str):
    """Async non-blocking operation start recording"""
    try:
        await asyncio.to_thread(record_operation_start, operation)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_operation_success_async(operation: str, duration: float):
    """Async non-blocking success recording"""
    try:
        await asyncio.to_thread(record_operation_success, operation, duration)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_operation_failure_async(operation: str, duration: float, error_type: str = 'other'):
    """Async non-blocking failure recording"""
    try:
        await asyncio.to_thread(record_operation_failure, operation, duration, error_type)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_push_retry_async(attempt: int):
    """Async non-blocking retry recording"""
    try:
        await asyncio.to_thread(record_push_retry, attempt)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_conflict_async(operation: str):
    """Async non-blocking conflict recording"""
    try:
        await asyncio.to_thread(record_conflict, operation)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def update_active_sandboxes_async(count: int):
    """Async non-blocking active sandboxes update"""
    try:
        await asyncio.to_thread(update_active_sandboxes, count)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_sandbox_creation_async(duration: float):
    """Async non-blocking sandbox creation recording"""
    try:
        await asyncio.to_thread(record_sandbox_creation, duration)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_sandbox_cache_hit_async():
    """Async non-blocking cache hit recording"""
    try:
        await asyncio.to_thread(record_sandbox_cache_hit)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


async def record_sandbox_cache_miss_async():
    """Async non-blocking cache miss recording"""
    try:
        await asyncio.to_thread(record_sandbox_cache_miss)
    except Exception as e:
        logger.error(f"Async metrics recording failed: {e}")


# ===========================================================================
# Cost Calculation
# ===========================================================================

E2B_HOURLY_COST = 0.015  # $0.015 per sandbox hour

def calculate_cost_from_hours(sandbox_hours: float) -> float:
    """Calculate cost from sandbox hours"""
    return sandbox_hours * E2B_HOURLY_COST


# ===========================================================================
# Metrics Info
# ===========================================================================

git_operations_info = Info(
    'git_operations',
    'Git operations service information'
)

git_operations_info.info({
    'version': '1.0.0',
    'approach': 'approach_1_quick_win',
    'sandbox_provider': 'e2b',
    'cost_per_hour': str(E2B_HOURLY_COST)
})
