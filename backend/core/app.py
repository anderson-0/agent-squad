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
from backend.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    setup_logging()
    await init_db()
    print(f"🚀 {settings.APP_NAME} started in {settings.ENV} mode")

    yield

    # Shutdown
    await close_db()
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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus Metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.ENV,
            "version": "0.1.0",
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
