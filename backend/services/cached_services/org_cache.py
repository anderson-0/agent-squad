"""
Organization Cache Service

Provides caching for organization data with automatic invalidation.

Features:
- Cache by organization_id
- Cache organization list by owner_id
- Automatic invalidation on updates
- Configurable TTL (default: 10 minutes)
"""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import Organization
from backend.services.cache_service import get_cache
from backend.core.config import settings

logger = logging.getLogger(__name__)


class OrganizationCacheService:
    """
    Organization caching service with invalidation support.

    Cache Keys:
    - org:{org_id} -> Full organization object
    - org:owner:{owner_id} -> List of organizations for owner

    TTL: CACHE_ORG_TTL (default: 600 seconds = 10 minutes)
    """

    def __init__(self):
        self.cache = get_cache()
        self.ttl = settings.CACHE_ORG_TTL

    def _org_key(self, org_id: UUID) -> str:
        """Generate cache key for organization by ID"""
        return f"org:{str(org_id)}"

    def _owner_orgs_key(self, owner_id: UUID) -> str:
        """Generate cache key for owner's organizations"""
        return f"org:owner:{str(owner_id)}"

    def _serialize_org(self, org: Organization) -> dict:
        """Serialize organization object to dict for caching"""
        return {
            "id": str(org.id),
            "name": org.name,
            "owner_id": str(org.owner_id),
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }

    async def get_organization_by_id(
        self,
        db: AsyncSession,
        org_id: UUID,
        use_cache: bool = True
    ) -> Optional[Organization]:
        """
        Get organization by ID with caching.

        Args:
            db: Database session
            org_id: Organization ID
            use_cache: Whether to use cache (default: True)

        Returns:
            Organization object or None if not found
        """
        cache_key = self._org_key(org_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        result = await db.execute(
            select(Organization).filter(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()

        # Cache the result
        if org:
            serialized = self._serialize_org(org)
            await self.cache.set(cache_key, serialized, ttl=self.ttl)

        return org

    async def get_organizations_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        use_cache: bool = True
    ) -> List[Organization]:
        """
        Get all organizations for an owner with caching.

        Args:
            db: Database session
            owner_id: Owner user ID
            use_cache: Whether to use cache (default: True)

        Returns:
            List of Organization objects
        """
        cache_key = self._owner_orgs_key(owner_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        result = await db.execute(
            select(Organization).filter(Organization.owner_id == owner_id)
        )
        orgs = result.scalars().all()

        # Cache the result
        serialized_list = [self._serialize_org(org) for org in orgs]
        await self.cache.set(cache_key, serialized_list, ttl=self.ttl)

        # Also cache individual organizations
        for org in orgs:
            org_key = self._org_key(org.id)
            serialized = self._serialize_org(org)
            await self.cache.set(org_key, serialized, ttl=self.ttl)

        return orgs

    async def invalidate_organization(
        self,
        org_id: UUID,
        owner_id: Optional[UUID] = None
    ):
        """
        Invalidate organization cache.

        Args:
            org_id: Organization ID to invalidate
            owner_id: Optional owner ID to invalidate owner's org list
        """
        # Invalidate organization cache
        org_key = self._org_key(org_id)
        await self.cache.delete(org_key)
        logger.info(f"Invalidated cache: {org_key}")

        # Invalidate owner's organizations list if provided
        if owner_id:
            owner_key = self._owner_orgs_key(owner_id)
            await self.cache.delete(owner_key)
            logger.info(f"Invalidated cache: {owner_key}")

    async def invalidate_owner_orgs(self, owner_id: UUID):
        """
        Invalidate all organization caches for an owner.

        Args:
            owner_id: Owner user ID
        """
        owner_key = self._owner_orgs_key(owner_id)
        await self.cache.delete(owner_key)
        logger.info(f"Invalidated cache: {owner_key}")

    async def warm_cache(
        self,
        db: AsyncSession,
        org_ids: List[UUID]
    ) -> int:
        """
        Warm cache for multiple organizations.

        Args:
            db: Database session
            org_ids: List of organization IDs to cache

        Returns:
            Number of organizations cached
        """
        result = await db.execute(
            select(Organization).filter(Organization.id.in_(org_ids))
        )
        orgs = result.scalars().all()

        cached_count = 0
        for org in orgs:
            serialized = self._serialize_org(org)

            # Cache by ID
            org_key = self._org_key(org.id)
            await self.cache.set(org_key, serialized, ttl=self.ttl)

            cached_count += 1

        logger.info(f"Warmed cache for {cached_count} organizations")
        return cached_count


# Global instance
_org_cache_service: Optional[OrganizationCacheService] = None


def get_org_cache() -> OrganizationCacheService:
    """Get or create organization cache service instance"""
    global _org_cache_service
    if _org_cache_service is None:
        _org_cache_service = OrganizationCacheService()
    return _org_cache_service


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Get organization by ID with caching

    from backend.services.cached_services.org_cache import get_org_cache

    org_cache = get_org_cache()
    org = await org_cache.get_organization_by_id(db, org_id)


Example 2: Get all organizations for a user

    org_cache = get_org_cache()
    orgs = await org_cache.get_organizations_by_owner(db, user_id)


Example 3: Invalidate organization cache after update

    from backend.services.cached_services.org_cache import get_org_cache

    # Update organization in database
    org.name = "New Name"
    await db.commit()

    # Invalidate cache
    org_cache = get_org_cache()
    await org_cache.invalidate_organization(org.id, org.owner_id)


Example 4: Warm cache for active organizations

    org_cache = get_org_cache()
    active_org_ids = [org1_id, org2_id, org3_id]
    cached_count = await org_cache.warm_cache(db, active_org_ids)
    print(f"Cached {cached_count} organizations")


Example 5: Invalidate owner's organization list

    org_cache = get_org_cache()
    # After creating/deleting organization for owner
    await org_cache.invalidate_owner_orgs(owner_id)
"""
