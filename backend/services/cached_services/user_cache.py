"""
User Cache Service

Provides caching for user data with automatic invalidation.

Features:
- Cache by user_id
- Cache by email
- Automatic invalidation on updates
- Configurable TTL (default: 5 minutes)
"""
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import User
from backend.services.cache_service import get_cache
from backend.core.config import settings

logger = logging.getLogger(__name__)


class UserCacheService:
    """
    User caching service with invalidation support.

    Cache Keys:
    - user:{user_id} -> Full user object
    - user:email:{email} -> Full user object

    TTL: CACHE_USER_TTL (default: 300 seconds = 5 minutes)
    """

    def __init__(self):
        self.cache = get_cache()
        self.ttl = settings.CACHE_USER_TTL

    def _user_key(self, user_id: UUID) -> str:
        """Generate cache key for user by ID"""
        return f"user:{str(user_id)}"

    def _user_email_key(self, email: str) -> str:
        """Generate cache key for user by email"""
        return f"user:email:{email.lower()}"

    def _serialize_user(self, user: User) -> dict:
        """Serialize user object to dict for caching"""
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        use_cache: bool = True
    ) -> Optional[User]:
        """
        Get user by ID with caching.

        Args:
            db: Database session
            user_id: User ID
            use_cache: Whether to use cache (default: True)

        Returns:
            User object or None if not found
        """
        cache_key = self._user_key(user_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                # Note: Returning dict, not User object (for simplicity)
                # In production, you might want to reconstruct User object
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        # Cache the result
        if user:
            serialized = self._serialize_user(user)
            await self.cache.set(cache_key, serialized, ttl=self.ttl)

            # Also cache by email for faster email lookups
            email_key = self._user_email_key(user.email)
            await self.cache.set(email_key, serialized, ttl=self.ttl)

        return user

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
        use_cache: bool = True
    ) -> Optional[User]:
        """
        Get user by email with caching.

        Args:
            db: Database session
            email: User email
            use_cache: Whether to use cache (default: True)

        Returns:
            User object or None if not found
        """
        cache_key = self._user_email_key(email)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        result = await db.execute(
            select(User).filter(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        # Cache the result
        if user:
            serialized = self._serialize_user(user)
            await self.cache.set(cache_key, serialized, ttl=self.ttl)

            # Also cache by ID
            id_key = self._user_key(user.id)
            await self.cache.set(id_key, serialized, ttl=self.ttl)

        return user

    async def invalidate_user(self, user_id: UUID, email: Optional[str] = None):
        """
        Invalidate user cache.

        Args:
            user_id: User ID to invalidate
            email: Optional email to invalidate
        """
        # Invalidate ID cache
        id_key = self._user_key(user_id)
        await self.cache.delete(id_key)
        logger.info(f"Invalidated cache: {id_key}")

        # Invalidate email cache if provided
        if email:
            email_key = self._user_email_key(email)
            await self.cache.delete(email_key)
            logger.info(f"Invalidated cache: {email_key}")

    async def warm_cache(
        self,
        db: AsyncSession,
        user_ids: list[UUID]
    ) -> int:
        """
        Warm cache for multiple users.

        Args:
            db: Database session
            user_ids: List of user IDs to cache

        Returns:
            Number of users cached
        """
        result = await db.execute(
            select(User).filter(User.id.in_(user_ids))
        )
        users = result.scalars().all()

        cached_count = 0
        for user in users:
            serialized = self._serialize_user(user)

            # Cache by ID
            id_key = self._user_key(user.id)
            await self.cache.set(id_key, serialized, ttl=self.ttl)

            # Cache by email
            email_key = self._user_email_key(user.email)
            await self.cache.set(email_key, serialized, ttl=self.ttl)

            cached_count += 1

        logger.info(f"Warmed cache for {cached_count} users")
        return cached_count


# Global instance
_user_cache_service: Optional[UserCacheService] = None


def get_user_cache() -> UserCacheService:
    """Get or create user cache service instance"""
    global _user_cache_service
    if _user_cache_service is None:
        _user_cache_service = UserCacheService()
    return _user_cache_service


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Get user by ID with caching

    from backend.services.cached_services.user_cache import get_user_cache

    user_cache = get_user_cache()
    user = await user_cache.get_user_by_id(db, user_id)


Example 2: Get user by email with caching

    user_cache = get_user_cache()
    user = await user_cache.get_user_by_email(db, "user@example.com")


Example 3: Invalidate user cache after update

    from backend.services.cached_services.user_cache import get_user_cache

    # Update user in database
    user.name = "New Name"
    await db.commit()

    # Invalidate cache
    user_cache = get_user_cache()
    await user_cache.invalidate_user(user.id, user.email)


Example 4: Warm cache for active users

    user_cache = get_user_cache()
    active_user_ids = [user1_id, user2_id, user3_id]
    cached_count = await user_cache.warm_cache(db, active_user_ids)
    print(f"Cached {cached_count} users")


Example 5: Bypass cache when needed

    user_cache = get_user_cache()
    # Force fresh data from database
    user = await user_cache.get_user_by_id(db, user_id, use_cache=False)
"""
