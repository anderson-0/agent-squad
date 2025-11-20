"""
API v1 Endpoints

All API endpoint modules.
"""
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
    agent_pool,  # Phase 2 optimization - Agent pool monitoring
)

__all__ = [
    "auth",
    "squads",
    "squad_members",
    "task_executions",
    "agent_messages",
    "sse",
    "routing_rules",
    "conversations",
    "templates",
    "analytics",
    "multi_turn_conversations",
    "workflows",
    "pm_guardian",
    "kanban",
    "discovery",
    "branching",
    "advanced_guardian",
    "intelligence",
    "ml_detection",
    "mcp",
    "agent_pool",
]
