"""
Enhanced Health Check Endpoints

Provides comprehensive health and readiness checks for
production monitoring and load balancer health probes.
"""
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.core.database import get_db
from backend.core.config import settings
from backend.core.agno_config import get_agno_config
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Application start time for uptime tracking
START_TIME = time.time()


@router.get("")
async def health_check():
    """
    Basic health check endpoint.

    Returns minimal response for simple health probes.
    Use this for basic load balancer health checks.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with component status.

    Checks:
    - Database connectivity (PostgreSQL)
    - Agno framework
    - Application uptime
    - Configuration validity

    Returns detailed status for monitoring dashboards.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - START_TIME,
        "environment": settings.ENV,
        "version": "0.1.0",
        "components": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        logger.error("database_health_check_failed", error=str(e))

    # Check Agno framework
    try:
        agno_config = get_agno_config()
        is_healthy = agno_config.health_check()
        health_status["components"]["agno"] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "framework": "agno",
            "version": "2.2.0",
        }
        if not is_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["agno"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        logger.error("agno_health_check_failed", error=str(e))

    # Check Redis (if configured)
    try:
        if settings.REDIS_URL:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            await redis_client.close()
            health_status["components"]["redis"] = {
                "status": "healthy",
            }
    except ImportError:
        health_status["components"]["redis"] = {
            "status": "not_configured",
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        logger.warning("redis_health_check_failed", error=str(e))

    # Check Cache status
    try:
        from backend.services.cache_service import get_cache

        cache = get_cache()
        metrics = cache.get_metrics()

        cache_status = "operational" if health_status["components"].get("redis", {}).get("status") == "healthy" else "unavailable"

        health_status["components"]["cache"] = {
            "enabled": settings.CACHE_ENABLED,
            "status": cache_status,
            "hit_rate": metrics["hit_rate_overall"],
            "total_requests": metrics["total_requests"]
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "enabled": settings.CACHE_ENABLED,
            "status": "error",
            "error": str(e),
        }
        logger.warning("cache_health_check_failed", error=str(e))

    # LLM Provider status
    llm_providers = {
        "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
        "anthropic": "configured" if settings.ANTHROPIC_API_KEY else "not_configured",
        "groq": "configured" if settings.GROQ_API_KEY else "not_configured",
    }

    # Check Ollama (local LLM)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                llm_providers["ollama"] = "running"
            else:
                llm_providers["ollama"] = "not_running"
    except Exception:
        llm_providers["ollama"] = "not_running"

    health_status["components"]["llm_providers"] = llm_providers

    return health_status


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check for Kubernetes/orchestration.

    Returns 200 if application is ready to serve traffic.
    Returns 503 if not ready (starting up, degraded, etc.)

    Use this for Kubernetes readiness probes.
    """
    try:
        # Check critical components
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": "Database not available",
                "timestamp": time.time(),
            }
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/orchestration.

    Returns 200 if application process is alive.
    Use this for Kubernetes liveness probes.

    This is a simple check that doesn't verify dependencies,
    preventing restart loops due to temporary dependency issues.
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - START_TIME,
    }


@router.get("/startup")
async def startup_check(db: AsyncSession = Depends(get_db)):
    """
    Startup check for Kubernetes/orchestration.

    Returns 200 once application has fully started.
    Use this for Kubernetes startup probes.
    """
    try:
        # Verify database is accessible
        await db.execute(text("SELECT 1"))

        # Verify Agno is initialized
        agno_config = get_agno_config()
        agno_config.health_check()

        return {
            "status": "started",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - START_TIME,
        }
    except Exception as e:
        logger.error("startup_check_failed", error=str(e))
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "starting",
                "error": str(e),
                "timestamp": time.time(),
            }
        )
