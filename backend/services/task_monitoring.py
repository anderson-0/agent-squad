"""
Task & Execution Monitoring Service

Tracks agent work patterns and task lifecycle to optimize cache TTLs.

This monitors:
- How fast agents complete tasks (avg completion time)
- How often tasks are updated (status changes)
- Task lifecycle patterns (creation → completion)
- Agent performance metrics

Use this data to determine optimal TTL values for task/execution caching!

Example insights:
- "Tasks complete in avg 2 minutes → use 30-60s TTL"
- "Tasks updated every 15 seconds on average → use 10-20s TTL"
- "90% of updates happen in first 5 minutes → shorter TTL early, longer later"
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from uuid import UUID

from backend.core.redis import get_redis
from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TaskLifecycleMetrics:
    """Metrics for task lifecycle analysis"""
    # Completion metrics
    total_tasks_completed: int = 0
    avg_completion_time_seconds: float = 0.0
    min_completion_time_seconds: float = 0.0
    max_completion_time_seconds: float = 0.0

    # Update frequency metrics
    total_status_updates: int = 0
    avg_time_between_updates_seconds: float = 0.0

    # Current active tasks
    active_tasks_count: int = 0

    # Distribution
    completion_time_p50: float = 0.0  # Median
    completion_time_p95: float = 0.0  # 95th percentile
    completion_time_p99: float = 0.0  # 99th percentile


@dataclass
class TTLRecommendation:
    """TTL recommendation based on actual patterns"""
    entity_type: str
    current_ttl_seconds: int
    recommended_ttl_seconds: int
    reason: str
    confidence: str  # high, medium, low


class TaskMonitoringService:
    """
    Monitors task and execution lifecycle to optimize cache TTLs.

    Key metrics:
    1. Task completion time (creation → done)
    2. Status update frequency
    3. Time between updates
    4. Agent work patterns

    This data tells us:
    - If tasks complete quickly → use shorter TTL
    - If tasks update frequently → use shorter TTL
    - If tasks are stable → can use longer TTL
    """

    def __init__(self):
        self.prefix = f"{settings.CACHE_PREFIX}:task_monitoring"
        self.window_seconds = 3600  # Track last 1 hour

    def _key(self, metric_name: str) -> str:
        """Generate Redis key for metric"""
        return f"{self.prefix}:{metric_name}"

    async def track_task_created(self, task_id: UUID):
        """
        Track when a task is created.

        Stores creation timestamp for lifecycle analysis.
        """
        try:
            redis = await get_redis()
            key = f"{self.prefix}:task:{task_id}:created"
            await redis.set(key, int(time.time()))
            await redis.expire(key, self.window_seconds)

            # Increment active tasks counter
            await redis.incr(self._key("active_tasks"))

        except Exception as e:
            logger.error(f"Failed to track task creation: {e}")

    async def track_task_status_update(
        self,
        task_id: UUID,
        old_status: str,
        new_status: str
    ):
        """
        Track when task status changes.

        This is KEY for determining update frequency!

        Args:
            task_id: Task ID
            old_status: Previous status
            new_status: New status
        """
        try:
            redis = await get_redis()

            # Increment total status updates
            await redis.incr(self._key("status_updates_total"))

            # Track timestamp of this update
            timestamp = int(time.time())
            update_key = f"{self.prefix}:task:{task_id}:last_update"

            # Get previous update time to calculate interval
            prev_timestamp = await redis.get(update_key)
            if prev_timestamp:
                interval = timestamp - int(prev_timestamp)
                # Add to running average of intervals
                await self._add_to_average(
                    "avg_update_interval",
                    interval,
                    self.window_seconds
                )

            # Store current update timestamp
            await redis.set(update_key, timestamp)
            await redis.expire(update_key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track status update: {e}")

    async def track_task_completed(
        self,
        task_id: UUID,
        completion_time_seconds: Optional[float] = None
    ):
        """
        Track when a task completes.

        Calculates completion time from creation to completion.

        Args:
            task_id: Task ID
            completion_time_seconds: Optional pre-calculated completion time
        """
        try:
            redis = await get_redis()

            # Get creation time
            created_key = f"{self.prefix}:task:{task_id}:created"
            created_timestamp = await redis.get(created_key)

            if created_timestamp and not completion_time_seconds:
                # Calculate completion time
                completion_time_seconds = time.time() - int(created_timestamp)

            if completion_time_seconds:
                # Add to completion time statistics
                await self._add_to_average(
                    "avg_completion_time",
                    completion_time_seconds,
                    self.window_seconds
                )

                # Track min/max
                await self._update_min_max(
                    "completion_time",
                    completion_time_seconds
                )

                # Store in percentile bucket for distribution analysis
                await self._add_to_percentile_bucket(
                    "completion_time",
                    completion_time_seconds
                )

            # Increment completed tasks counter
            await redis.incr(self._key("tasks_completed"))

            # Decrement active tasks counter
            await redis.decr(self._key("active_tasks"))

            # Clean up creation timestamp
            await redis.delete(created_key)

        except Exception as e:
            logger.error(f"Failed to track task completion: {e}")

    async def track_execution_status_update(
        self,
        execution_id: UUID,
        status: str
    ):
        """
        Track execution status updates.

        Executions update MORE frequently than tasks!
        This helps us tune execution status cache TTL.

        Args:
            execution_id: Execution ID
            status: New status (pending, in_progress, completed, failed)
        """
        try:
            redis = await get_redis()

            # Increment total execution updates
            await redis.incr(self._key("execution_updates_total"))

            # Track timestamp
            timestamp = int(time.time())
            update_key = f"{self.prefix}:execution:{execution_id}:last_update"

            # Get previous update time
            prev_timestamp = await redis.get(update_key)
            if prev_timestamp:
                interval = timestamp - int(prev_timestamp)
                # Track execution update interval (usually faster than tasks)
                await self._add_to_average(
                    "avg_execution_update_interval",
                    interval,
                    self.window_seconds
                )

            await redis.set(update_key, timestamp)
            await redis.expire(update_key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track execution update: {e}")

    async def _add_to_average(self, metric_name: str, value: float, ttl: int):
        """Add value to running average"""
        try:
            redis = await get_redis()

            # Use sorted set to track last N values
            key = self._key(f"{metric_name}_values")
            timestamp = time.time()

            # Add with timestamp as score
            await redis.zadd(key, {str(value): timestamp})

            # Remove old values (older than window)
            cutoff = timestamp - ttl
            await redis.zremrangebyscore(key, 0, cutoff)

            # Set expiry
            await redis.expire(key, ttl)

        except Exception as e:
            logger.error(f"Failed to add to average: {e}")

    async def _update_min_max(self, metric_name: str, value: float):
        """Update min/max values"""
        try:
            redis = await get_redis()

            # Update min
            min_key = self._key(f"{metric_name}_min")
            current_min = await redis.get(min_key)
            if current_min is None or value < float(current_min):
                await redis.set(min_key, value)
                await redis.expire(min_key, self.window_seconds)

            # Update max
            max_key = self._key(f"{metric_name}_max")
            current_max = await redis.get(max_key)
            if current_max is None or value > float(current_max):
                await redis.set(max_key, value)
                await redis.expire(max_key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to update min/max: {e}")

    async def _add_to_percentile_bucket(self, metric_name: str, value: float):
        """Add value to percentile buckets for distribution analysis"""
        try:
            redis = await get_redis()

            # Use sorted set for percentile calculation
            key = self._key(f"{metric_name}_distribution")
            await redis.zadd(key, {str(value): value})

            # Keep only last 1000 values to avoid memory bloat
            await redis.zremrangebyrank(key, 0, -1001)

            await redis.expire(key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to add to percentile bucket: {e}")

    async def get_metrics(self) -> TaskLifecycleMetrics:
        """Get current task lifecycle metrics"""
        try:
            redis = await get_redis()

            # Get basic counters
            tasks_completed = int(await redis.get(self._key("tasks_completed")) or 0)
            active_tasks = int(await redis.get(self._key("active_tasks")) or 0)
            status_updates = int(await redis.get(self._key("status_updates_total")) or 0)

            # Calculate averages from stored values
            avg_completion_time = await self._calculate_average("avg_completion_time_values")
            avg_update_interval = await self._calculate_average("avg_update_interval_values")

            # Get min/max
            min_completion = float(await redis.get(self._key("completion_time_min")) or 0)
            max_completion = float(await redis.get(self._key("completion_time_max")) or 0)

            # Calculate percentiles
            percentiles = await self._calculate_percentiles("completion_time_distribution")

            return TaskLifecycleMetrics(
                total_tasks_completed=tasks_completed,
                avg_completion_time_seconds=round(avg_completion_time, 2),
                min_completion_time_seconds=round(min_completion, 2),
                max_completion_time_seconds=round(max_completion, 2),
                total_status_updates=status_updates,
                avg_time_between_updates_seconds=round(avg_update_interval, 2),
                active_tasks_count=active_tasks,
                completion_time_p50=round(percentiles.get("p50", 0), 2),
                completion_time_p95=round(percentiles.get("p95", 0), 2),
                completion_time_p99=round(percentiles.get("p99", 0), 2),
            )

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return TaskLifecycleMetrics()

    async def _calculate_average(self, key: str) -> float:
        """Calculate average from stored values"""
        try:
            redis = await get_redis()
            full_key = self._key(key)

            # Get all values from sorted set
            values = await redis.zrange(full_key, 0, -1)

            if not values:
                return 0.0

            # Calculate average
            float_values = [float(v) for v in values]
            return sum(float_values) / len(float_values)

        except Exception as e:
            logger.error(f"Failed to calculate average: {e}")
            return 0.0

    async def _calculate_percentiles(self, key: str) -> Dict[str, float]:
        """Calculate percentiles from distribution"""
        try:
            redis = await get_redis()
            full_key = self._key(key)

            # Get all values sorted
            values = await redis.zrange(full_key, 0, -1, withscores=True)

            if not values:
                return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

            # Extract scores (the actual values)
            scores = [score for _, score in values]
            scores.sort()

            count = len(scores)
            return {
                "p50": scores[int(count * 0.50)] if count > 0 else 0.0,
                "p95": scores[int(count * 0.95)] if count > 0 else 0.0,
                "p99": scores[int(count * 0.99)] if count > 0 else 0.0,
            }

        except Exception as e:
            logger.error(f"Failed to calculate percentiles: {e}")
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

    async def get_ttl_recommendations(self) -> List[TTLRecommendation]:
        """
        Generate TTL recommendations based on observed patterns.

        Logic:
        - If avg completion time < 1 min → recommend 20-30s task TTL
        - If avg completion time 1-5 min → recommend 30-60s task TTL
        - If avg completion time > 5 min → recommend 60-120s task TTL
        - If avg update interval < 30s → recommend 10-15s execution TTL
        - If avg update interval > 60s → recommend 20-30s execution TTL
        """
        metrics = await self.get_metrics()

        if metrics.total_tasks_completed < 10:
            return [
                TTLRecommendation(
                    entity_type="task",
                    current_ttl_seconds=settings.CACHE_TASK_TTL,
                    recommended_ttl_seconds=settings.CACHE_TASK_TTL,
                    reason="Need more data (< 10 completed tasks)",
                    confidence="low"
                )
            ]

        recommendations = []

        # Task TTL recommendation based on completion time
        avg_completion = metrics.avg_completion_time_seconds
        current_task_ttl = settings.CACHE_TASK_TTL

        if avg_completion < 60:  # Less than 1 minute
            recommended_ttl = 30
            reason = f"Tasks complete quickly (avg {avg_completion:.0f}s) - use shorter TTL"
            confidence = "high"
        elif avg_completion < 300:  # 1-5 minutes
            recommended_ttl = 45
            reason = f"Tasks complete in {avg_completion/60:.1f} min - moderate TTL appropriate"
            confidence = "high"
        else:  # > 5 minutes
            recommended_ttl = 60
            reason = f"Tasks take longer (avg {avg_completion/60:.1f} min) - can use longer TTL"
            confidence = "medium"

        recommendations.append(
            TTLRecommendation(
                entity_type="task",
                current_ttl_seconds=current_task_ttl,
                recommended_ttl_seconds=recommended_ttl,
                reason=reason,
                confidence=confidence
            )
        )

        # Execution status TTL recommendation based on update frequency
        avg_update_interval = metrics.avg_time_between_updates_seconds
        current_exec_ttl = settings.CACHE_EXECUTION_STATUS_TTL

        if avg_update_interval > 0:
            if avg_update_interval < 30:
                recommended_exec_ttl = 10
                reason = f"Status updates every {avg_update_interval:.0f}s - use short TTL"
                confidence = "high"
            elif avg_update_interval < 60:
                recommended_exec_ttl = 20
                reason = f"Status updates every {avg_update_interval:.0f}s - moderate TTL"
                confidence = "high"
            else:
                recommended_exec_ttl = 30
                reason = f"Status updates infrequent ({avg_update_interval:.0f}s) - longer TTL safe"
                confidence = "medium"

            recommendations.append(
                TTLRecommendation(
                    entity_type="execution_status",
                    current_ttl_seconds=current_exec_ttl,
                    recommended_ttl_seconds=recommended_exec_ttl,
                    reason=reason,
                    confidence=confidence
                )
            )

        return recommendations


# Global instance
_monitoring_service: Optional[TaskMonitoringService] = None


def get_task_monitoring() -> TaskMonitoringService:
    """Get or create task monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = TaskMonitoringService()
    return _monitoring_service


# Convenience functions
async def track_task_created(task_id: UUID):
    """Track task creation"""
    monitoring = get_task_monitoring()
    await monitoring.track_task_created(task_id)


async def track_task_status_update(task_id: UUID, old_status: str, new_status: str):
    """Track task status update"""
    monitoring = get_task_monitoring()
    await monitoring.track_task_status_update(task_id, old_status, new_status)


async def track_task_completed(task_id: UUID, completion_time_seconds: Optional[float] = None):
    """Track task completion"""
    monitoring = get_task_monitoring()
    await monitoring.track_task_completed(task_id, completion_time_seconds)


async def track_execution_status_update(execution_id: UUID, status: str):
    """Track execution status update"""
    monitoring = get_task_monitoring()
    await monitoring.track_execution_status_update(execution_id, status)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Instrument task creation

    from backend.services.task_monitoring import track_task_created

    async def create_task(...):
        task = Task(...)
        await db.commit()

        # Track creation
        await track_task_created(task.id)

        return task


Example 2: Instrument task status updates

    from backend.services.task_monitoring import track_task_status_update

    async def update_task_status(task_id, new_status):
        task = await db.get(Task, task_id)
        old_status = task.status

        task.status = new_status
        await db.commit()

        # Track update
        await track_task_status_update(task_id, old_status, new_status)


Example 3: Track task completion

    from backend.services.task_monitoring import track_task_completed

    async def complete_task(task_id):
        task = await db.get(Task, task_id)
        task.status = "completed"

        completion_time = (datetime.utcnow() - task.created_at).total_seconds()
        await db.commit()

        # Track completion
        await track_task_completed(task_id, completion_time)


Example 4: Get metrics and recommendations

    from backend.services.task_monitoring import get_task_monitoring

    monitoring = get_task_monitoring()

    # Get current metrics
    metrics = await monitoring.get_metrics()
    print(f"Avg completion time: {metrics.avg_completion_time_seconds}s")
    print(f"Avg update interval: {metrics.avg_time_between_updates_seconds}s")

    # Get TTL recommendations
    recommendations = await monitoring.get_ttl_recommendations()
    for rec in recommendations:
        print(f"{rec.entity_type}: {rec.recommended_ttl_seconds}s ({rec.reason})")
"""
