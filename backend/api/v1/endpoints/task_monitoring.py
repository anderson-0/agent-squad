"""
Task Monitoring API Endpoints

Provides insights into agent work patterns and task lifecycle for TTL optimization.
"""
from fastapi import APIRouter

from backend.services.task_monitoring import get_task_monitoring

router = APIRouter(prefix="/task-monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_task_lifecycle_metrics():
    """
    Get task lifecycle metrics.

    Returns insights about:
    - How fast agents complete tasks
    - How often tasks are updated
    - Task lifecycle patterns
    - Active tasks count

    Returns:
        {
            "total_tasks_completed": 145,
            "avg_completion_time_seconds": 180.5,
            "min_completion_time_seconds": 45.2,
            "max_completion_time_seconds": 720.8,
            "total_status_updates": 420,
            "avg_time_between_updates_seconds": 25.3,
            "active_tasks_count": 12,
            "completion_time_p50": 150.2,
            "completion_time_p95": 580.5,
            "completion_time_p99": 690.1
        }

    Use cases:
    - Understand agent work patterns
    - Determine if tasks complete quickly or slowly
    - Identify how frequently tasks update
    - Optimize cache TTLs based on real data
    """
    monitoring = get_task_monitoring()
    metrics = await monitoring.get_metrics()
    return {
        **metrics.__dict__,
        "insights": {
            "completion_speed": (
                "fast" if metrics.avg_completion_time_seconds < 60
                else "moderate" if metrics.avg_completion_time_seconds < 300
                else "slow"
            ),
            "update_frequency": (
                "high" if metrics.avg_time_between_updates_seconds < 30
                else "moderate" if metrics.avg_time_between_updates_seconds < 60
                else "low"
            )
        }
    }


@router.get("/ttl-recommendations")
async def get_ttl_recommendations():
    """
    Get data-driven TTL recommendations based on observed patterns.

    This is THE endpoint to use for optimizing cache TTLs!

    Returns:
        {
            "recommendations": [
                {
                    "entity_type": "task",
                    "current_ttl_seconds": 120,
                    "recommended_ttl_seconds": 30,
                    "reason": "Tasks complete quickly (avg 45s) - use shorter TTL",
                    "confidence": "high"
                },
                {
                    "entity_type": "execution_status",
                    "current_ttl_seconds": 10,
                    "recommended_ttl_seconds": 15,
                    "reason": "Status updates every 20s - moderate TTL",
                    "confidence": "high"
                }
            ],
            "metrics_summary": {
                "tasks_analyzed": 145,
                "avg_completion_time": "3.0 minutes",
                "avg_update_interval": "25.3 seconds"
            }
        }

    How to use:
    1. Let system run for 1+ hour to collect data
    2. Call this endpoint
    3. Review recommendations with "high" confidence
    4. Update TTLs in config.py
    5. Reset cache metrics and monitor improvement

    Example workflow:
    ```python
    # 1. Check recommendations
    GET /api/v1/task-monitoring/ttl-recommendations

    # 2. See: "Recommended task TTL: 30s (currently 120s)"

    # 3. Update config.py:
    CACHE_TASK_TTL: int = 30

    # 4. Restart app

    # 5. Monitor cache hit rate improvement
    GET /api/v1/cache/metrics
    ```
    """
    monitoring = get_task_monitoring()
    metrics = await monitoring.get_metrics()
    recommendations = await monitoring.get_ttl_recommendations()

    return {
        "recommendations": [
            {
                "entity_type": rec.entity_type,
                "current_ttl_seconds": rec.current_ttl_seconds,
                "recommended_ttl_seconds": rec.recommended_ttl_seconds,
                "reason": rec.reason,
                "confidence": rec.confidence
            }
            for rec in recommendations
        ],
        "metrics_summary": {
            "tasks_analyzed": metrics.total_tasks_completed,
            "avg_completion_time": f"{metrics.avg_completion_time_seconds / 60:.1f} minutes",
            "avg_update_interval": f"{metrics.avg_time_between_updates_seconds:.1f} seconds",
            "active_tasks": metrics.active_tasks_count
        },
        "notes": [
            "Recommendations based on last 1 hour of data",
            "High confidence = 10+ tasks completed",
            "Apply changes during low-traffic periods",
            "Monitor cache hit rates after changes"
        ]
    }


@router.get("/summary")
async def get_monitoring_summary():
    """
    Get a concise summary of task monitoring and recommendations.

    Quick overview perfect for dashboards or monitoring.

    Returns:
        {
            "status": "optimal" | "needs_attention" | "insufficient_data",
            "avg_completion_time": "3.0 minutes",
            "tasks_per_hour": 48,
            "active_tasks": 12,
            "top_recommendation": "Consider reducing task TTL to 30s",
            "next_steps": ["Let system run for 1+ hour", "Review recommendations"]
        }
    """
    monitoring = get_task_monitoring()
    metrics = await monitoring.get_metrics()
    recommendations = await monitoring.get_ttl_recommendations()

    # Determine status
    if metrics.total_tasks_completed < 10:
        status = "insufficient_data"
        next_steps = [
            "Let system run for 1+ hour",
            "Complete at least 10 tasks",
            "Then check recommendations"
        ]
    else:
        # Check if any recommendations differ significantly from current
        has_recommendations = any(
            abs(rec.recommended_ttl_seconds - rec.current_ttl_seconds) > 10
            for rec in recommendations
        )
        status = "needs_attention" if has_recommendations else "optimal"
        next_steps = (
            ["Review TTL recommendations", "Update config.py", "Monitor improvements"]
            if has_recommendations
            else ["Monitor regularly", "TTL values are optimal"]
        )

    # Get top recommendation (highest confidence, largest diff)
    top_rec = None
    if recommendations:
        high_conf_recs = [r for r in recommendations if r.confidence == "high"]
        if high_conf_recs:
            top_rec = max(
                high_conf_recs,
                key=lambda r: abs(r.recommended_ttl_seconds - r.current_ttl_seconds)
            )

    return {
        "status": status,
        "avg_completion_time": f"{metrics.avg_completion_time_seconds / 60:.1f} minutes",
        "tasks_per_hour": int(metrics.total_tasks_completed),  # Assuming 1hr window
        "active_tasks": metrics.active_tasks_count,
        "top_recommendation": (
            f"Update {top_rec.entity_type} TTL: {top_rec.current_ttl_seconds}s → "
            f"{top_rec.recommended_ttl_seconds}s ({top_rec.reason})"
            if top_rec
            else "No recommendations at this time"
        ),
        "next_steps": next_steps,
        "data_quality": {
            "tasks_analyzed": metrics.total_tasks_completed,
            "sufficient_data": metrics.total_tasks_completed >= 10,
            "recommendation_confidence": (
                "high" if metrics.total_tasks_completed >= 50
                else "medium" if metrics.total_tasks_completed >= 10
                else "low"
            )
        }
    }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example workflow for optimizing TTLs:

1. Let system run for 1+ hour with production traffic

2. Check summary:
   GET /api/v1/task-monitoring/summary

   Response:
   {
     "status": "needs_attention",
     "avg_completion_time": "2.5 minutes",
     "tasks_per_hour": 85,
     "top_recommendation": "Update task TTL: 120s → 30s (Tasks complete quickly)"
   }

3. Get detailed recommendations:
   GET /api/v1/task-monitoring/ttl-recommendations

   Response:
   {
     "recommendations": [
       {
         "entity_type": "task",
         "current_ttl_seconds": 120,
         "recommended_ttl_seconds": 30,
         "reason": "Tasks complete quickly (avg 45s)",
         "confidence": "high"
       }
     ]
   }

4. Update config.py:
   CACHE_TASK_TTL: int = 30  # Changed from 120

5. Restart application

6. Monitor improvement:
   GET /api/v1/cache/metrics

   Should see:
   - Higher hit rate for tasks
   - Fewer stale cache entries
   - Better cache effectiveness

7. Continue monitoring:
   GET /api/v1/task-monitoring/summary
   (Should show "optimal" status)
"""
