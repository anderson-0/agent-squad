"""
API v1 Router - Includes all v1 API endpoints
"""
from fastapi import APIRouter

from backend.api.v1.endpoints import (
    auth,
    squads,
    squad_members,
    task_executions,
    agent_messages,
    sse,
    routing_rules,
    conversations,
    templates,
    analytics,
    multi_turn_conversations,
    workflows,
    pm_guardian,
    kanban,
    discovery,
    branching,
    advanced_guardian,
    intelligence,
    ml_detection,
    mcp,
    health,  # Enhanced health checks
    costs,  # Cost tracking
    agent_pool,  # Phase 2 optimization - Agent pool monitoring
    cache_metrics,  # Phase 3A - Cache performance metrics
    task_monitoring,  # Phase 3A - Task lifecycle monitoring for TTL optimization
)


# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router)  # Health checks (no prefix, at /api/v1/health)
api_router.include_router(auth.router)
api_router.include_router(squads.router)
api_router.include_router(squad_members.router)
api_router.include_router(task_executions.router)
api_router.include_router(agent_messages.router)
api_router.include_router(sse.router)
api_router.include_router(routing_rules.router)
api_router.include_router(conversations.router)
api_router.include_router(templates.router)
# Analytics router handled separately (existing endpoint)
# api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(multi_turn_conversations.router, prefix="/multi-turn-conversations", tags=["multi-turn-conversations"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(pm_guardian.router, tags=["pm-guardian"])
api_router.include_router(kanban.router, tags=["kanban"])
api_router.include_router(discovery.router, tags=["discovery"])
api_router.include_router(branching.router, tags=["branching"])
api_router.include_router(advanced_guardian.router, tags=["advanced-guardian"])
api_router.include_router(intelligence.router, tags=["intelligence"])
api_router.include_router(ml_detection.router, tags=["ml-detection"])
api_router.include_router(mcp.router, tags=["mcp"])
api_router.include_router(costs.router, tags=["costs"])
api_router.include_router(agent_pool.router, tags=["agent-pool"])  # Phase 2 optimization
api_router.include_router(cache_metrics.router, tags=["cache-metrics"])  # Phase 3A optimization
api_router.include_router(task_monitoring.router, tags=["task-monitoring"])  # Phase 3A optimization

# Future routers will be added here:
# api_router.include_router(projects.router)
# api_router.include_router(subscriptions.router)
# api_router.include_router(organizations.router)
# api_router.include_router(webhooks.router)
