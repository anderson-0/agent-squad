"""
Agent Task Spawning Module

Provides task spawning capabilities to agents.
"""
from backend.agents.task_spawning.agent_task_spawner import (
    AgentTaskSpawner,
    get_agent_task_spawner,
)

__all__ = [
    "AgentTaskSpawner",
    "get_agent_task_spawner",
]

