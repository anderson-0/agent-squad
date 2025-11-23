"""
FastAPI Application Setup
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.database import init_db, close_db
from backend.core.agno_config import initialize_agno, shutdown_agno
from backend.core.redis import get_redis, close_redis
from backend.api.v1.router import api_router

# Production middleware
from backend.middleware import (
    RequestLoggingMiddleware,
    ErrorTrackingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    setup_logging()
    initialize_agno()  # Initialize Agno framework
    await init_db()
    await get_redis()  # Initialize Redis cache
    print(f"🚀 {settings.APP_NAME} started in {settings.ENV} mode")

    yield

    # Shutdown
    await close_redis()  # Close Redis connection
    await close_db()
    shutdown_agno()  # Shutdown Agno framework
    print("👋 Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Software Development SaaS Platform",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Production Middleware Stack (order matters!)

# 1. Security headers (first - apply to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS (before rate limiting to handle preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# 3. Rate limiting (protect API from abuse)
if settings.ENV == "production":
    app.add_middleware(RateLimitMiddleware)

# 4. Request logging (track all requests)
app.add_middleware(RequestLoggingMiddleware)

# 5. Error tracking (catch all errors)
app.add_middleware(ErrorTrackingMiddleware)

# 6. GZip compression (last - compress responses)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus Metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Inngest Background Jobs
# Mount Inngest endpoint for background workflow execution
# This enables async agent execution with instant API responses
try:
    from inngest.fastapi import serve as inngest_serve
    from backend.core.inngest import inngest
    from backend.workflows.agent_workflows import (
        execute_agent_workflow,
        execute_single_agent_workflow
    )
    from backend.workflows.sandbox_workflows import (
        execute_task_with_sandbox,
        cleanup_old_sandboxes
    )
    from backend.workflows.hitl_workflows import (
        handle_approval_approved,
        handle_approval_rejected
    )

    app.mount(
        "/api/inngest",
        inngest_serve(
            inngest,
            [
                execute_agent_workflow,
                execute_single_agent_workflow,
                execute_task_with_sandbox,
                cleanup_old_sandboxes,
                handle_approval_approved,
                handle_approval_rejected,
            ],
        ),
    )
    print("✅ Inngest workflows registered: /api/inngest")
    print("   - execute_agent_workflow")
    print("   - execute_single_agent_workflow")
    print("   - execute_task_with_sandbox")
    print("   - cleanup_old_sandboxes")
    print("   - handle_approval_approved")
    print("   - handle_approval_rejected")
except ImportError:
    print("⚠️  Inngest not available - install with: pip install inngest")


# Basic health check (redirect to detailed endpoint)
@app.get("/health")
async def health_check():
    """Simple health check (use /health/detailed for more info)"""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.ENV,
            "version": "0.1.0",
            "docs": {
                "detailed": "/health/detailed",
                "ready": "/health/ready",
                "live": "/health/live",
            }
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
