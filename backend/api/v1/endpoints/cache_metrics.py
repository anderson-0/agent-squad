"""
Cache Metrics API Endpoints

Provides access to cache performance metrics and TTL optimization recommendations.
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.cache_metrics import get_cache_metrics
from backend.services.cache_service import get_cache
from backend.services.cached_services.squad_cache import get_squad_cache
from backend.services.cached_services.task_cache import get_task_cache
from backend.core.database import get_db

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/metrics")
async def get_cache_performance_metrics(
    entity_type: Optional[str] = None
):
    """
    Get cache performance metrics and TTL recommendations.

    Args:
        entity_type: Optional filter for specific entity type
                    (user, org, squad, task, execution)

    Returns:
        {
            "timestamp": "2025-11-07T10:30:00Z",
            "overall_hit_rate": 78.5,
            "total_requests": 15847,
            "metrics_by_type": {
                "user": {
                    "hits": 1450,
                    "misses": 150,
                    "hit_rate": 90.6,
                    "updates": 12,
                    "update_rate": 12.0
                },
                "task": {
                    "hits": 850,
                    "misses": 450,
                    "hit_rate": 65.4,
                    "updates": 45,
                    "update_rate": 45.0
                }
            },
            "ttl_recommendations": {
                "user": "✅ TTL optimal: 300s (Hit rate: 90.6%, Updates: 12.0/hr)",
                "task": "⚠️  Reduce TTL: 120s → 60s (High updates: 45.0/hr, Low hit rate: 65.4%)"
            }
        }

    Use cases:
    - Monitor cache effectiveness in production
    - Get data-driven TTL recommendations
    - Identify caching issues (low hit rates)
    - Track update frequencies for optimization
    """
    metrics_service = get_cache_metrics()
    snapshot = await metrics_service.get_metrics(entity_type)
    return snapshot.to_dict()


@router.get("/metrics/{entity_type}")
async def get_entity_metrics(entity_type: str):
    """
    Get detailed metrics for a specific entity type.

    Args:
        entity_type: Entity type (user, org, squad, task, execution)

    Returns:
        Detailed metrics and recommendations for this entity type
    """
    valid_types = ["user", "org", "squad", "task", "execution"]
    if entity_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity_type. Must be one of: {valid_types}"
        )

    metrics_service = get_cache_metrics()
    snapshot = await metrics_service.get_metrics(entity_type)

    if entity_type not in snapshot.metrics_by_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for entity_type: {entity_type}"
        )

    return {
        "entity_type": entity_type,
        "metrics": snapshot.metrics_by_type[entity_type],
        "recommendation": snapshot.ttl_recommendations.get(entity_type, "No recommendation"),
        "timestamp": snapshot.timestamp
    }


@router.post("/metrics/reset")
async def reset_cache_metrics(entity_type: Optional[str] = None):
    """
    Reset cache metrics (useful after TTL adjustments or for testing).

    Args:
        entity_type: Optional - reset only specific entity type

    Returns:
        Confirmation message

    Note: This does NOT clear the actual cache, only the metrics tracking.
    """
    metrics_service = get_cache_metrics()
    await metrics_service.reset_metrics(entity_type)

    return {
        "status": "success",
        "message": f"Cache metrics reset for: {entity_type or 'all entity types'}",
        "note": "Actual cache data was NOT cleared"
    }


@router.get("/health")
async def get_cache_health():
    """
    Get cache health status based on performance metrics.

    Returns:
        {
            "status": "healthy" | "warning" | "critical",
            "overall_hit_rate": 78.5,
            "issues": ["task: Low hit rate (65%)"],
            "recommendations": ["Consider reducing task TTL"]
        }

    Health criteria:
    - healthy: overall hit rate > 70%
    - warning: overall hit rate 50-70%
    - critical: overall hit rate < 50%
    """
    metrics_service = get_cache_metrics()
    snapshot = await metrics_service.get_metrics()

    # Determine health status
    if snapshot.overall_hit_rate >= 70:
        status_value = "healthy"
    elif snapshot.overall_hit_rate >= 50:
        status_value = "warning"
    else:
        status_value = "critical"

    # Identify issues
    issues = []
    recommendations = []

    for entity_type, metrics in snapshot.metrics_by_type.items():
        if metrics.hit_rate < 60:
            issues.append(f"{entity_type}: Low hit rate ({metrics.hit_rate:.1f}%)")

        recommendation = snapshot.ttl_recommendations.get(entity_type, "")
        if "⚠️" in recommendation or "Reduce TTL" in recommendation:
            recommendations.append(f"{entity_type}: {recommendation}")

    return {
        "status": status_value,
        "overall_hit_rate": snapshot.overall_hit_rate,
        "total_requests": snapshot.total_requests,
        "issues": issues if issues else ["No issues detected"],
        "recommendations": recommendations if recommendations else ["Cache performance is optimal"],
        "timestamp": snapshot.timestamp
    }


@router.post("/clear")
async def clear_all_cache():
    """
    Clear entire cache (use with caution!).

    Returns:
        Confirmation message with count of keys deleted

    Warning: This will clear ALL cached data across all entity types.
    Only use this for debugging or after major schema changes.
    """
    cache = get_cache()

    # Get all keys matching our prefix pattern
    keys_deleted = await cache.clear_pattern("*")

    return {
        "status": "success",
        "message": f"Cleared entire cache",
        "keys_deleted": keys_deleted,
        "warning": "All cached data has been removed. Performance may be degraded until cache warms up."
    }


@router.post("/clear/{entity_type}")
async def clear_entity_cache(entity_type: str):
    """
    Clear cache for a specific entity type.

    Args:
        entity_type: Entity type to clear (user, org, squad, task, execution)

    Returns:
        Confirmation message with count of keys deleted
    """
    valid_types = ["user", "org", "squad", "task", "execution"]
    if entity_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity_type. Must be one of: {valid_types}"
        )

    cache = get_cache()

    # Clear all keys matching the entity type pattern
    keys_deleted = await cache.clear_pattern(f"{entity_type}:*")

    return {
        "status": "success",
        "entity_type": entity_type,
        "keys_deleted": keys_deleted,
        "message": f"Cleared all {entity_type} cache entries"
    }


@router.post("/warm/squads")
async def warm_squad_cache(
    squad_ids: List[UUID],
    db: AsyncSession = Depends(get_db)
):
    """
    Warm cache for specific squads and their members.

    Args:
        squad_ids: List of squad IDs to warm cache for

    Returns:
        Count of squads cached
    """
    if len(squad_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot warm more than 100 squads at once"
        )

    squad_cache = get_squad_cache()
    cached_count = await squad_cache.warm_cache(db, squad_ids)

    return {
        "status": "success",
        "squads_cached": cached_count,
        "message": f"Warmed cache for {cached_count} squads"
    }


@router.post("/warm/tasks")
async def warm_task_cache(
    task_ids: List[UUID],
    db: AsyncSession = Depends(get_db)
):
    """
    Warm cache for specific tasks.

    Args:
        task_ids: List of task IDs to warm cache for

    Returns:
        Count of tasks cached
    """
    if len(task_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot warm more than 100 tasks at once"
        )

    task_cache = get_task_cache()
    cached_count = await task_cache.warm_task_cache(db, task_ids)

    return {
        "status": "success",
        "tasks_cached": cached_count,
        "message": f"Warmed cache for {cached_count} tasks"
    }


@router.post("/warm/executions")
async def warm_execution_cache(
    execution_ids: List[UUID],
    db: AsyncSession = Depends(get_db)
):
    """
    Warm cache for specific executions.

    Args:
        execution_ids: List of execution IDs to warm cache for

    Returns:
        Count of executions cached
    """
    if len(execution_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot warm more than 100 executions at once"
        )

    task_cache = get_task_cache()
    cached_count = await task_cache.warm_execution_cache(db, execution_ids)

    return {
        "status": "success",
        "executions_cached": cached_count,
        "message": f"Warmed cache for {cached_count} executions"
    }


@router.delete("/invalidate/squad/{squad_id}")
async def invalidate_squad(
    squad_id: UUID,
    org_id: Optional[UUID] = None
):
    """
    Invalidate cache for a specific squad.

    Args:
        squad_id: Squad ID to invalidate
        org_id: Optional organization ID to also invalidate org's squad list

    Returns:
        Confirmation message
    """
    squad_cache = get_squad_cache()
    await squad_cache.invalidate_squad(squad_id, org_id)

    return {
        "status": "success",
        "squad_id": str(squad_id),
        "message": "Squad cache invalidated"
    }


@router.delete("/invalidate/task/{task_id}")
async def invalidate_task(
    task_id: UUID,
    project_id: Optional[UUID] = None
):
    """
    Invalidate cache for a specific task.

    Args:
        task_id: Task ID to invalidate
        project_id: Optional project ID to also invalidate project's task list

    Returns:
        Confirmation message
    """
    task_cache = get_task_cache()
    await task_cache.invalidate_task(task_id, project_id)

    return {
        "status": "success",
        "task_id": str(task_id),
        "message": "Task cache invalidated"
    }


@router.delete("/invalidate/execution/{execution_id}")
async def invalidate_execution(
    execution_id: UUID,
    task_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
):
    """
    Invalidate cache for a specific execution.

    Args:
        execution_id: Execution ID to invalidate
        task_id: Optional task ID to also invalidate task's execution list
        squad_id: Optional squad ID to also invalidate squad's execution list

    Returns:
        Confirmation message
    """
    task_cache = get_task_cache()
    await task_cache.invalidate_execution(execution_id, task_id, squad_id)

    return {
        "status": "success",
        "execution_id": str(execution_id),
        "message": "Execution cache invalidated (including HOT PATH status cache)"
    }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example API calls:

1. Get all metrics:
   GET /api/v1/cache/metrics

2. Get metrics for specific entity:
   GET /api/v1/cache/metrics?entity_type=task
   GET /api/v1/cache/metrics/task

3. Check cache health:
   GET /api/v1/cache/health

4. Reset metrics after TTL adjustment:
   POST /api/v1/cache/metrics/reset
   POST /api/v1/cache/metrics/reset?entity_type=task

Example response from /cache/metrics:

{
  "timestamp": "2025-11-07T10:30:00Z",
  "overall_hit_rate": 78.5,
  "total_requests": 15847,
  "metrics_by_type": {
    "user": {
      "entity_type": "user",
      "hits": 1450,
      "misses": 150,
      "invalidations": 8,
      "updates": 12,
      "total_requests": 1600,
      "hit_rate": 90.6,
      "update_rate": 12.0
    },
    "task": {
      "entity_type": "task",
      "hits": 850,
      "misses": 450,
      "invalidations": 35,
      "updates": 45,
      "total_requests": 1300,
      "hit_rate": 65.4,
      "update_rate": 45.0
    }
  },
  "ttl_recommendations": {
    "user": "✅ TTL optimal: 300s (Hit rate: 90.6%, Updates: 12.0/hr)",
    "task": "⚠️  Reduce TTL: 120s → 60s (High updates: 45.0/hr, Low hit rate: 65.4%)",
    "squad": "✅ Consider increasing TTL: 300s → 600s (Low updates: 0.5/hr, High hit rate: 92.1%)"
  }
}
"""
