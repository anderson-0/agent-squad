"""
Squad Cache Service

Provides caching for squad data with automatic invalidation.

Features:
- Cache by squad_id
- Cache squad members list by squad_id
- Cache squads by organization_id
- Automatic invalidation on updates
- Configurable TTL (default: 5 minutes)
"""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models.squad import Squad, SquadMember
from backend.services.cache_service import get_cache
from backend.services.cache_metrics import get_cache_metrics
from backend.core.config import settings

logger = logging.getLogger(__name__)


class SquadCacheService:
    """
    Squad caching service with invalidation support.

    Cache Keys:
    - squad:{squad_id} -> Full squad object
    - squad:members:{squad_id} -> List of squad members
    - squad:org:{org_id} -> List of squads for organization

    TTL: CACHE_SQUAD_TTL (default: 300 seconds = 5 minutes)
    """

    def __init__(self):
        self.cache = get_cache()
        self.metrics = get_cache_metrics()
        self.ttl = settings.CACHE_SQUAD_TTL

    def _squad_key(self, squad_id: UUID) -> str:
        """Generate cache key for squad by ID"""
        return f"squad:{str(squad_id)}"

    def _squad_members_key(self, squad_id: UUID) -> str:
        """Generate cache key for squad members list"""
        return f"squad:members:{str(squad_id)}"

    def _org_squads_key(self, org_id: UUID) -> str:
        """Generate cache key for organization's squads"""
        return f"squad:org:{str(org_id)}"

    def _serialize_squad(self, squad: Squad) -> dict:
        """Serialize squad object to dict for caching"""
        return {
            "id": str(squad.id),
            "org_id": str(squad.org_id),
            "user_id": str(squad.user_id),
            "name": squad.name,
            "description": squad.description,
            "status": squad.status,
            "config": squad.config,
            "created_at": squad.created_at.isoformat() if squad.created_at else None,
            "updated_at": squad.updated_at.isoformat() if squad.updated_at else None,
        }

    def _serialize_squad_member(self, member: SquadMember) -> dict:
        """Serialize squad member object to dict for caching"""
        return {
            "id": str(member.id),
            "squad_id": str(member.squad_id),
            "role": member.role,
            "specialization": member.specialization,
            "llm_provider": member.llm_provider,
            "llm_model": member.llm_model,
            "system_prompt": member.system_prompt,
            "config": member.config,
            "is_active": member.is_active,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "updated_at": member.updated_at.isoformat() if member.updated_at else None,
        }

    async def get_squad_by_id(
        self,
        db: AsyncSession,
        squad_id: UUID,
        use_cache: bool = True
    ) -> Optional[Squad]:
        """
        Get squad by ID with caching.

        Args:
            db: Database session
            squad_id: Squad ID
            use_cache: Whether to use cache (default: True)

        Returns:
            Squad object or None if not found
        """
        cache_key = self._squad_key(squad_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("squad")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("squad")

        result = await db.execute(
            select(Squad).filter(Squad.id == squad_id)
        )
        squad = result.scalar_one_or_none()

        # Cache the result
        if squad:
            serialized = self._serialize_squad(squad)
            await self.cache.set(cache_key, serialized, ttl=self.ttl)

        return squad

    async def get_squad_members(
        self,
        db: AsyncSession,
        squad_id: UUID,
        use_cache: bool = True,
        active_only: bool = False
    ) -> List[SquadMember]:
        """
        Get all squad members with caching.

        Args:
            db: Database session
            squad_id: Squad ID
            use_cache: Whether to use cache (default: True)
            active_only: Only return active members (default: False)

        Returns:
            List of SquadMember objects
        """
        cache_key = self._squad_members_key(squad_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("squad")
                # Filter active_only if needed
                if active_only:
                    return [m for m in cached_data if m.get("is_active", True)]
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("squad")

        query = select(SquadMember).filter(SquadMember.squad_id == squad_id)

        result = await db.execute(query)
        members = result.scalars().all()

        # Cache all members (we'll filter on return)
        serialized_list = [self._serialize_squad_member(m) for m in members]
        await self.cache.set(cache_key, serialized_list, ttl=self.ttl)

        # Return filtered if needed
        if active_only:
            return [m for m in members if m.is_active]
        return members

    async def get_squads_by_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        use_cache: bool = True,
        active_only: bool = False
    ) -> List[Squad]:
        """
        Get all squads for an organization with caching.

        Args:
            db: Database session
            org_id: Organization ID
            use_cache: Whether to use cache (default: True)
            active_only: Only return active squads (default: False)

        Returns:
            List of Squad objects
        """
        cache_key = self._org_squads_key(org_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("squad")
                # Filter active_only if needed
                if active_only:
                    return [s for s in cached_data if s.get("status") == "active"]
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("squad")

        query = select(Squad).filter(Squad.org_id == org_id)

        result = await db.execute(query)
        squads = result.scalars().all()

        # Cache all squads
        serialized_list = [self._serialize_squad(s) for s in squads]
        await self.cache.set(cache_key, serialized_list, ttl=self.ttl)

        # Also cache individual squads
        for squad in squads:
            squad_key = self._squad_key(squad.id)
            serialized = self._serialize_squad(squad)
            await self.cache.set(squad_key, serialized, ttl=self.ttl)

        # Return filtered if needed
        if active_only:
            return [s for s in squads if s.status == "active"]
        return squads

    async def invalidate_squad(
        self,
        squad_id: UUID,
        org_id: Optional[UUID] = None
    ):
        """
        Invalidate squad cache.

        Args:
            squad_id: Squad ID to invalidate
            org_id: Optional organization ID to invalidate org's squad list
        """
        # Invalidate squad cache
        squad_key = self._squad_key(squad_id)
        await self.cache.delete(squad_key)
        await self.metrics.track_invalidation("squad")
        logger.info(f"Invalidated cache: {squad_key}")

        # Invalidate squad members cache
        members_key = self._squad_members_key(squad_id)
        await self.cache.delete(members_key)
        await self.metrics.track_invalidation("squad")
        logger.info(f"Invalidated cache: {members_key}")

        # Invalidate organization's squads list if provided
        if org_id:
            org_key = self._org_squads_key(org_id)
            await self.cache.delete(org_key)
            await self.metrics.track_invalidation("squad")
            logger.info(f"Invalidated cache: {org_key}")

    async def invalidate_squad_member(
        self,
        squad_id: UUID
    ):
        """
        Invalidate squad members cache (when member added/removed/updated).

        Args:
            squad_id: Squad ID
        """
        members_key = self._squad_members_key(squad_id)
        await self.cache.delete(members_key)
        await self.metrics.track_invalidation("squad")
        logger.info(f"Invalidated cache: {members_key}")

    async def invalidate_org_squads(self, org_id: UUID):
        """
        Invalidate all squad caches for an organization.

        Args:
            org_id: Organization ID
        """
        org_key = self._org_squads_key(org_id)
        await self.cache.delete(org_key)
        await self.metrics.track_invalidation("squad")
        logger.info(f"Invalidated cache: {org_key}")

    async def warm_cache(
        self,
        db: AsyncSession,
        squad_ids: List[UUID]
    ) -> int:
        """
        Warm cache for multiple squads and their members.

        Args:
            db: Database session
            squad_ids: List of squad IDs to cache

        Returns:
            Number of squads cached
        """
        result = await db.execute(
            select(Squad)
            .filter(Squad.id.in_(squad_ids))
            .options(selectinload(Squad.members))  # Eager load members
        )
        squads = result.scalars().all()

        cached_count = 0
        for squad in squads:
            # Cache squad
            serialized = self._serialize_squad(squad)
            squad_key = self._squad_key(squad.id)
            await self.cache.set(squad_key, serialized, ttl=self.ttl)

            # Cache squad members
            if hasattr(squad, 'members') and squad.members:
                members_serialized = [
                    self._serialize_squad_member(m) for m in squad.members
                ]
                members_key = self._squad_members_key(squad.id)
                await self.cache.set(members_key, members_serialized, ttl=self.ttl)

            cached_count += 1

        logger.info(f"Warmed cache for {cached_count} squads")
        return cached_count


# Global instance
_squad_cache_service: Optional[SquadCacheService] = None


def get_squad_cache() -> SquadCacheService:
    """Get or create squad cache service instance"""
    global _squad_cache_service
    if _squad_cache_service is None:
        _squad_cache_service = SquadCacheService()
    return _squad_cache_service


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Get squad by ID with caching

    from backend.services.cached_services.squad_cache import get_squad_cache

    squad_cache = get_squad_cache()
    squad = await squad_cache.get_squad_by_id(db, squad_id)


Example 2: Get squad members with caching

    squad_cache = get_squad_cache()
    members = await squad_cache.get_squad_members(db, squad_id, active_only=True)


Example 3: Get all squads for an organization

    squad_cache = get_squad_cache()
    squads = await squad_cache.get_squads_by_organization(db, org_id, active_only=True)


Example 4: Invalidate squad cache after update

    from backend.services.cached_services.squad_cache import get_squad_cache

    # Update squad in database
    squad.name = "New Squad Name"
    await db.commit()

    # Invalidate cache
    squad_cache = get_squad_cache()
    await squad_cache.invalidate_squad(squad.id, squad.org_id)


Example 5: Invalidate squad members cache after member change

    squad_cache = get_squad_cache()

    # After adding/removing/updating squad member
    await squad_cache.invalidate_squad_member(squad_id)


Example 6: Warm cache for active squads

    squad_cache = get_squad_cache()
    active_squad_ids = [squad1_id, squad2_id, squad3_id]
    cached_count = await squad_cache.warm_cache(db, active_squad_ids)
    print(f"Cached {cached_count} squads with their members")


Example 7: Bypass cache when needed

    squad_cache = get_squad_cache()
    # Force fresh data from database
    squad = await squad_cache.get_squad_by_id(db, squad_id, use_cache=False)
"""
