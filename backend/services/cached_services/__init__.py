"""
Cached Services

High-level caching services for domain entities.
Each service provides entity-specific caching with automatic invalidation.

Features:
- User caching with profile data
- Organization caching
- Squad caching (future)
- Task execution status caching (future)

Usage:
    from backend.services.cached_services import get_user_cache, get_org_cache

    user_cache = get_user_cache()
    user = await user_cache.get_user_by_id(db, user_id)

    org_cache = get_org_cache()
    org = await org_cache.get_organization_by_id(db, org_id)
"""

# Re-export cached services
from .user_cache import UserCacheService, get_user_cache
from .org_cache import OrganizationCacheService, get_org_cache

__all__ = [
    "UserCacheService",
    "get_user_cache",
    "OrganizationCacheService",
    "get_org_cache",
]
