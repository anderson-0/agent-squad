"""
Rate Limiting Middleware

Provides API rate limiting to prevent abuse and ensure fair usage.
Uses Redis for distributed rate limiting across multiple instances.
"""
import time
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)

# Optional Redis integration for distributed rate limiting
REDIS_AVAILABLE = False
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("redis not available, rate limiting will use in-memory store")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API rate limiting.

    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (if authenticated)
    - Sliding window algorithm
    - Redis-based for distributed systems
    - In-memory fallback for development

    Rate Limits:
    - Anonymous: 100 requests/minute
    - Authenticated: 1000 requests/minute
    - Admin: 10000 requests/minute
    """

    def __init__(self, app, redis_client: Optional[any] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.in_memory_store = {}  # Fallback for development

        # Rate limits (requests per minute)
        self.limits = {
            "anonymous": 100,
            "authenticated": 1000,
            "admin": 10000,
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Determine client identifier
        client_id = self._get_client_id(request)
        user_type = self._get_user_type(request)
        limit = self.limits[user_type]

        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(
            client_id, limit
        )

        if not is_allowed:
            # Rate limit exceeded
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                user_type=user_type,
                path=request.url.path,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {limit}/minute",
                    "retry_after": int(reset_time - time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time())),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get authenticated user ID
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user.id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_user_type(self, request: Request) -> str:
        """Determine user type for rate limiting"""
        user = getattr(request.state, "user", None)
        if not user:
            return "anonymous"

        # Check if admin (implement your own logic)
        if getattr(user, "is_admin", False):
            return "admin"

        return "authenticated"

    async def _check_rate_limit(
        self, client_id: str, limit: int
    ) -> tuple[bool, int, float]:
        """
        Check if client is within rate limit.

        Returns: (is_allowed, remaining_requests, reset_timestamp)
        """
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        if REDIS_AVAILABLE and self.redis_client:
            return await self._check_rate_limit_redis(
                client_id, limit, window_start, current_time
            )
        else:
            return self._check_rate_limit_memory(
                client_id, limit, window_start, current_time
            )

    async def _check_rate_limit_redis(
        self, client_id: str, limit: int, window_start: float, current_time: float
    ) -> tuple[bool, int, float]:
        """Redis-based rate limiting (sliding window)"""
        key = f"ratelimit:{client_id}"

        try:
            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in window
            count = await self.redis_client.zcard(key)

            if count < limit:
                # Add current request
                await self.redis_client.zadd(key, {str(current_time): current_time})
                await self.redis_client.expire(key, 60)

                remaining = limit - count - 1
                reset_time = current_time + 60
                return True, remaining, reset_time
            else:
                # Rate limit exceeded
                reset_time = current_time + 60
                return False, 0, reset_time

        except Exception as e:
            logger.error("redis_rate_limit_error", error=str(e))
            # Fall back to allowing request if Redis fails
            return True, limit - 1, current_time + 60

    def _check_rate_limit_memory(
        self, client_id: str, limit: int, window_start: float, current_time: float
    ) -> tuple[bool, int, float]:
        """In-memory rate limiting (for development)"""
        if client_id not in self.in_memory_store:
            self.in_memory_store[client_id] = []

        # Remove old entries
        self.in_memory_store[client_id] = [
            t for t in self.in_memory_store[client_id] if t > window_start
        ]

        # Count requests
        count = len(self.in_memory_store[client_id])

        if count < limit:
            # Add current request
            self.in_memory_store[client_id].append(current_time)
            remaining = limit - count - 1
            reset_time = current_time + 60
            return True, remaining, reset_time
        else:
            # Rate limit exceeded
            reset_time = current_time + 60
            return False, 0, reset_time
