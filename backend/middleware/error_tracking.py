"""
Error Tracking Middleware

Provides comprehensive error tracking and reporting with
optional Sentry integration.
"""
import traceback
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)

# Optional Sentry integration
SENTRY_AVAILABLE = False
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
        SENTRY_AVAILABLE = True
    except ImportError:
        logger.warning("sentry_sdk not installed, error tracking limited")


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error tracking.

    Features:
    - Catch all unhandled exceptions
    - Log with full context
    - Send to Sentry (if configured)
    - Return user-friendly error responses
    - Preserve stack traces in debug mode
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error tracking"""
        try:
            response = await call_next(request)
            return response

        except Exception as e:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", "unknown")

            # Log error with full context
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                stack_trace=traceback.format_exc(),
                exc_info=True,
            )

            # Send to Sentry if available
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)

            # Return appropriate error response
            if settings.DEBUG:
                # Debug mode: include stack trace
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal Server Error",
                        "message": str(e),
                        "type": type(e).__name__,
                        "request_id": request_id,
                        "stack_trace": traceback.format_exc(),
                    }
                )
            else:
                # Production mode: user-friendly message
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred. Please try again later.",
                        "request_id": request_id,
                    }
                )
