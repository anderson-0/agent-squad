"""
Cache Metrics Service

Tracks cache performance metrics to enable data-driven TTL optimization.

Features:
- Hit/miss rates by entity type
- Update frequency tracking
- TTL effectiveness analysis
- Automatic TTL recommendations

Usage:
    from backend.services.cache_metrics import track_cache_hit, track_cache_miss

    # In your cache service
    value = await cache.get(key)
    if value:
        track_cache_hit("user")
    else:
        track_cache_miss("user")
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict

from backend.core.redis import get_redis
from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EntityMetrics:
    """Metrics for a specific entity type"""
    entity_type: str
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    updates: int = 0  # How many times entity was updated/invalidated

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    @property
    def update_rate(self) -> float:
        """Updates per hour"""
        if self.total_requests == 0:
            return 0.0
        # Assuming metrics are tracked over CACHE_METRICS_WINDOW seconds
        hours = settings.CACHE_METRICS_WINDOW / 3600
        return self.updates / hours if hours > 0 else 0


@dataclass
class CacheMetricsSnapshot:
    """Complete snapshot of cache metrics"""
    timestamp: str
    overall_hit_rate: float
    total_requests: int
    metrics_by_type: Dict[str, EntityMetrics]
    ttl_recommendations: Dict[str, str]

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "overall_hit_rate": self.overall_hit_rate,
            "total_requests": self.total_requests,
            "metrics_by_type": {
                entity_type: asdict(metrics)
                for entity_type, metrics in self.metrics_by_type.items()
            },
            "ttl_recommendations": self.ttl_recommendations
        }


class CacheMetricsService:
    """
    Service to track and analyze cache performance metrics.

    Stores metrics in Redis with time-windowed tracking (default: 1 hour).
    Provides TTL recommendations based on actual usage patterns.
    """

    def __init__(self):
        self.enabled = settings.CACHE_METRICS_ENABLED
        self.window_seconds = settings.CACHE_METRICS_WINDOW
        self.prefix = f"{settings.CACHE_PREFIX}:metrics"

    def _metric_key(self, entity_type: str, metric_name: str) -> str:
        """Generate Redis key for a specific metric"""
        return f"{self.prefix}:{entity_type}:{metric_name}"

    async def track_hit(self, entity_type: str):
        """Track a cache hit for entity type"""
        if not self.enabled:
            return

        try:
            redis = await get_redis()
            key = self._metric_key(entity_type, "hits")

            # Increment counter with expiry
            await redis.incr(key)
            await redis.expire(key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track cache hit: {e}")

    async def track_miss(self, entity_type: str):
        """Track a cache miss for entity type"""
        if not self.enabled:
            return

        try:
            redis = await get_redis()
            key = self._metric_key(entity_type, "misses")

            # Increment counter with expiry
            await redis.incr(key)
            await redis.expire(key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track cache miss: {e}")

    async def track_invalidation(self, entity_type: str):
        """Track a cache invalidation (entity was deleted from cache)"""
        if not self.enabled:
            return

        try:
            redis = await get_redis()
            key = self._metric_key(entity_type, "invalidations")

            # Increment counter with expiry
            await redis.incr(key)
            await redis.expire(key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track invalidation: {e}")

    async def track_update(self, entity_type: str):
        """
        Track an entity update (write operation that invalidates cache).

        This is the KEY metric for TTL optimization!
        High update rate → shorter TTL needed
        Low update rate → longer TTL acceptable
        """
        if not self.enabled:
            return

        try:
            redis = await get_redis()

            # Increment update counter
            updates_key = self._metric_key(entity_type, "updates")
            await redis.incr(updates_key)
            await redis.expire(updates_key, self.window_seconds)

            # Track timestamp of last update for freshness analysis
            timestamp_key = self._metric_key(entity_type, "last_update")
            await redis.set(timestamp_key, int(time.time()))
            await redis.expire(timestamp_key, self.window_seconds)

        except Exception as e:
            logger.error(f"Failed to track update: {e}")

    async def get_metrics(self, entity_type: Optional[str] = None) -> CacheMetricsSnapshot:
        """
        Get current metrics snapshot.

        Args:
            entity_type: If specified, only get metrics for this type

        Returns:
            CacheMetricsSnapshot with all metrics and recommendations
        """
        try:
            redis = await get_redis()

            # Get all entity types we're tracking
            if entity_type:
                entity_types = [entity_type]
            else:
                # Scan for all entity types
                entity_types = ["user", "org", "squad", "task", "execution"]

            metrics_by_type = {}
            total_hits = 0
            total_misses = 0

            for etype in entity_types:
                hits = int(await redis.get(self._metric_key(etype, "hits")) or 0)
                misses = int(await redis.get(self._metric_key(etype, "misses")) or 0)
                invalidations = int(await redis.get(self._metric_key(etype, "invalidations")) or 0)
                updates = int(await redis.get(self._metric_key(etype, "updates")) or 0)

                metrics_by_type[etype] = EntityMetrics(
                    entity_type=etype,
                    hits=hits,
                    misses=misses,
                    invalidations=invalidations,
                    updates=updates
                )

                total_hits += hits
                total_misses += misses

            # Calculate overall hit rate
            total_requests = total_hits + total_misses
            overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

            # Generate TTL recommendations
            recommendations = await self._generate_recommendations(metrics_by_type)

            return CacheMetricsSnapshot(
                timestamp=datetime.utcnow().isoformat(),
                overall_hit_rate=round(overall_hit_rate, 2),
                total_requests=total_requests,
                metrics_by_type=metrics_by_type,
                ttl_recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            # Return empty metrics on error
            return CacheMetricsSnapshot(
                timestamp=datetime.utcnow().isoformat(),
                overall_hit_rate=0.0,
                total_requests=0,
                metrics_by_type={},
                ttl_recommendations={}
            )

    async def _generate_recommendations(
        self,
        metrics_by_type: Dict[str, EntityMetrics]
    ) -> Dict[str, str]:
        """
        Generate TTL recommendations based on metrics.

        Logic:
        - High update rate (>10/hr) + low hit rate (<60%) → Reduce TTL
        - Low update rate (<1/hr) + high hit rate (>90%) → Increase TTL
        - High update rate + high hit rate → TTL is optimal
        - Low hit rate + low update rate → Need more traffic data
        """
        recommendations = {}

        # Current TTL mapping
        current_ttls = {
            "user": settings.CACHE_USER_TTL,
            "org": settings.CACHE_ORG_TTL,
            "squad": settings.CACHE_SQUAD_TTL,
            "task": settings.CACHE_TASK_TTL,
            "execution": settings.CACHE_EXECUTION_STATUS_TTL,
        }

        for entity_type, metrics in metrics_by_type.items():
            if metrics.total_requests < 100:
                recommendations[entity_type] = "⏳ Need more data (< 100 requests)"
                continue

            hit_rate = metrics.hit_rate
            update_rate = metrics.update_rate
            current_ttl = current_ttls.get(entity_type, settings.CACHE_DEFAULT_TTL)

            # High update rate → shorter TTL might be better
            if update_rate > 10 and hit_rate < 60:
                new_ttl = max(10, current_ttl // 2)
                recommendations[entity_type] = (
                    f"⚠️  Reduce TTL: {current_ttl}s → {new_ttl}s "
                    f"(High updates: {update_rate:.1f}/hr, Low hit rate: {hit_rate:.1f}%)"
                )

            # Low update rate + high hit rate → could increase TTL
            elif update_rate < 1 and hit_rate > 90:
                new_ttl = min(3600, current_ttl * 2)
                recommendations[entity_type] = (
                    f"✅ Consider increasing TTL: {current_ttl}s → {new_ttl}s "
                    f"(Low updates: {update_rate:.1f}/hr, High hit rate: {hit_rate:.1f}%)"
                )

            # Moderate update rate + good hit rate → optimal
            elif hit_rate > 70:
                recommendations[entity_type] = (
                    f"✅ TTL optimal: {current_ttl}s "
                    f"(Hit rate: {hit_rate:.1f}%, Updates: {update_rate:.1f}/hr)"
                )

            # Low hit rate needs investigation
            elif hit_rate < 50:
                recommendations[entity_type] = (
                    f"⚠️  Low hit rate: {hit_rate:.1f}% - Investigate cache invalidation patterns"
                )

            else:
                recommendations[entity_type] = (
                    f"📊 Monitoring: Hit rate {hit_rate:.1f}%, Updates {update_rate:.1f}/hr"
                )

        return recommendations

    async def reset_metrics(self, entity_type: Optional[str] = None):
        """
        Reset metrics for entity type or all types.

        Useful for testing or after TTL adjustments.
        """
        try:
            redis = await get_redis()

            if entity_type:
                entity_types = [entity_type]
            else:
                entity_types = ["user", "org", "squad", "task", "execution"]

            for etype in entity_types:
                for metric in ["hits", "misses", "invalidations", "updates", "last_update"]:
                    await redis.delete(self._metric_key(etype, metric))

            logger.info(f"Reset metrics for: {entity_types}")

        except Exception as e:
            logger.error(f"Failed to reset metrics: {e}")


# Global instance
_metrics_service: Optional[CacheMetricsService] = None


def get_cache_metrics() -> CacheMetricsService:
    """Get or create cache metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = CacheMetricsService()
    return _metrics_service


# Convenience functions for easy import
async def track_cache_hit(entity_type: str):
    """Track a cache hit"""
    metrics = get_cache_metrics()
    await metrics.track_hit(entity_type)


async def track_cache_miss(entity_type: str):
    """Track a cache miss"""
    metrics = get_cache_metrics()
    await metrics.track_miss(entity_type)


async def track_cache_invalidation(entity_type: str):
    """Track a cache invalidation"""
    metrics = get_cache_metrics()
    await metrics.track_invalidation(entity_type)


async def track_entity_update(entity_type: str):
    """
    Track an entity update (the KEY metric!).

    Call this whenever an entity is updated/created/deleted.
    This helps determine optimal TTL values.
    """
    metrics = get_cache_metrics()
    await metrics.track_update(entity_type)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Instrument cache service to track hits/misses

    from backend.services.cache_metrics import track_cache_hit, track_cache_miss

    async def get_user_cached(user_id: UUID):
        cache_key = f"user:{user_id}"
        value = await cache.get(cache_key)

        if value:
            await track_cache_hit("user")
            return value
        else:
            await track_cache_miss("user")
            # Fetch from DB...


Example 2: Track entity updates to measure update frequency

    from backend.services.cache_metrics import track_entity_update

    async def update_task(task_id: UUID, **updates):
        # Update in database
        task = await db.execute(...)
        await db.commit()

        # Invalidate cache
        await cache.delete(f"task:{task_id}")

        # Track update for metrics
        await track_entity_update("task")

        return task


Example 3: Get metrics and recommendations

    from backend.services.cache_metrics import get_cache_metrics

    metrics_service = get_cache_metrics()
    snapshot = await metrics_service.get_metrics()

    print(f"Overall hit rate: {snapshot.overall_hit_rate}%")
    print(f"Total requests: {snapshot.total_requests}")

    for entity_type, recommendation in snapshot.ttl_recommendations.items():
        print(f"{entity_type}: {recommendation}")


Example 4: API endpoint to view metrics

    from backend.services.cache_metrics import get_cache_metrics

    @router.get("/cache/metrics")
    async def get_cache_metrics_endpoint():
        metrics_service = get_cache_metrics()
        snapshot = await metrics_service.get_metrics()
        return snapshot.to_dict()
"""
