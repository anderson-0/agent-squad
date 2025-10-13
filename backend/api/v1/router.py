"""
API v1 Router - Includes all v1 API endpoints
"""
from fastapi import APIRouter

from backend.api.v1.endpoints import auth


# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router)

# Future routers will be added here:
# api_router.include_router(squads.router)
# api_router.include_router(projects.router)
# api_router.include_router(agents.router)
# api_router.include_router(subscriptions.router)
# api_router.include_router(organizations.router)
# api_router.include_router(webhooks.router)
