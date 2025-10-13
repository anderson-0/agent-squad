"""
Memory Store

The Memory Store provides short-term working memory for agents using Redis.
This enables agents to:
- Remember context within a task execution
- Store intermediate results
- Cache frequently accessed data
- Share working memory across agent interactions

Uses Redis for fast in-memory storage with TTL support.
"""
from typing import Any, Dict, Optional, List
from uuid import UUID
import json
import os

import redis.asyncio as redis


class MemoryStore:
    """
    Memory Store - Short-term Working Memory with Redis

    Responsibilities:
    - Store agent working memory (task context, decisions, etc.)
    - Retrieve memory by agent and task
    - Automatic expiration via TTL
    - JSON serialization for complex types

    Key Format:
    - agent:{agent_id}:memory - Agent-wide memory
    - agent:{agent_id}:task:{task_execution_id}:memory - Task-specific memory
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Memory Store

        Args:
            redis_url: Redis connection URL (default from env)
        """
        url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        self.redis = redis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self) -> None:
        """Close Redis connection"""
        await self.redis.close()

    def _build_key(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID] = None,
        key_suffix: Optional[str] = None,
    ) -> str:
        """
        Build Redis key for agent memory.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
            key_suffix: Optional additional key suffix

        Returns:
            Redis key string
        """
        base = f"agent:{agent_id}"

        if task_execution_id:
            base += f":task:{task_execution_id}"

        base += ":memory"

        if key_suffix:
            base += f":{key_suffix}"

        return base

    async def store(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID],
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Store value in agent memory.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
            key: Memory key
            value: Value to store (will be JSON serialized)
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        redis_key = self._build_key(agent_id, task_execution_id, key)

        # Serialize value to JSON
        serialized = json.dumps(value, default=str)

        # Store with TTL
        await self.redis.setex(
            redis_key,
            ttl_seconds,
            serialized,
        )

    async def get(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID],
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve value from agent memory.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
            key: Memory key
            default: Default value if not found

        Returns:
            Stored value or default
        """
        redis_key = self._build_key(agent_id, task_execution_id, key)

        value = await self.redis.get(redis_key)

        if value is None:
            return default

        # Deserialize from JSON
        return json.loads(value)

    async def delete(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID],
        key: str,
    ) -> None:
        """
        Delete value from agent memory.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
            key: Memory key
        """
        redis_key = self._build_key(agent_id, task_execution_id, key)
        await self.redis.delete(redis_key)

    async def get_all_keys(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> List[str]:
        """
        Get all memory keys for an agent or task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID

        Returns:
            List of memory key suffixes
        """
        pattern = self._build_key(agent_id, task_execution_id) + ":*"
        keys = await self.redis.keys(pattern)

        # Extract key suffixes
        base_key = self._build_key(agent_id, task_execution_id) + ":"
        return [key.replace(base_key, "") for key in keys]

    async def get_context(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get all memory as a context dictionary.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID

        Returns:
            Dictionary of all stored memory
        """
        keys = await self.get_all_keys(agent_id, task_execution_id)

        context = {}
        for key in keys:
            value = await self.get(agent_id, task_execution_id, key)
            context[key] = value

        return context

    async def clear(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> None:
        """
        Clear all memory for an agent or task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
        """
        pattern = self._build_key(agent_id, task_execution_id) + ":*"
        keys = await self.redis.keys(pattern)

        if keys:
            await self.redis.delete(*keys)

    # Specialized memory operations

    async def store_decision(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
        decision: str,
        reasoning: str,
        alternatives_considered: List[str],
        ttl_seconds: int = 7200,  # 2 hours
    ) -> None:
        """
        Store an agent decision with reasoning.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID
            decision: Decision made
            reasoning: Why this decision was made
            alternatives_considered: Other options considered
            ttl_seconds: Time to live (default 2 hours)
        """
        await self.store(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="last_decision",
            value={
                "decision": decision,
                "reasoning": reasoning,
                "alternatives_considered": alternatives_considered,
                "timestamp": None,  # Will be serialized as string by default
            },
            ttl_seconds=ttl_seconds,
        )

    async def get_last_decision(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the last decision made by agent in this task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID

        Returns:
            Decision dictionary or None
        """
        return await self.get(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="last_decision",
        )

    async def store_task_state(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
        state: str,
        progress_percentage: int,
        details: Optional[str] = None,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Store current task state for an agent.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID
            state: Current state (planning, implementing, testing, etc.)
            progress_percentage: Progress (0-100)
            details: Optional details
            ttl_seconds: Time to live (default 1 hour)
        """
        await self.store(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="task_state",
            value={
                "state": state,
                "progress_percentage": progress_percentage,
                "details": details,
            },
            ttl_seconds=ttl_seconds,
        )

    async def get_task_state(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current task state for an agent.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID

        Returns:
            Task state dictionary or None
        """
        return await self.get(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="task_state",
        )

    async def store_blockers(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
        blockers: List[Dict[str, Any]],
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Store current blockers for a task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID
            blockers: List of blocker dictionaries
            ttl_seconds: Time to live (default 1 hour)
        """
        await self.store(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="blockers",
            value=blockers,
            ttl_seconds=ttl_seconds,
        )

    async def get_blockers(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get current blockers for a task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID

        Returns:
            List of blocker dictionaries
        """
        return await self.get(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="blockers",
            default=[],
        )

    async def add_blocker(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
        blocker: str,
        severity: str = "medium",
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Add a new blocker to the task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID
            blocker: Blocker description
            severity: Severity level (low, medium, high, critical)
            ttl_seconds: Time to live (default 1 hour)
        """
        blockers = await self.get_blockers(agent_id, task_execution_id)

        blockers.append({
            "blocker": blocker,
            "severity": severity,
            "added_at": None,  # Will be serialized as string
        })

        await self.store_blockers(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            blockers=blockers,
            ttl_seconds=ttl_seconds,
        )

    async def store_implementation_plan(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
        plan: Dict[str, Any],
        ttl_seconds: int = 7200,  # 2 hours
    ) -> None:
        """
        Store implementation plan for a task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID
            plan: Implementation plan dictionary
            ttl_seconds: Time to live (default 2 hours)
        """
        await self.store(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="implementation_plan",
            value=plan,
            ttl_seconds=ttl_seconds,
        )

    async def get_implementation_plan(
        self,
        agent_id: UUID,
        task_execution_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get implementation plan for a task.

        Args:
            agent_id: Agent UUID
            task_execution_id: Task execution UUID

        Returns:
            Implementation plan dictionary or None
        """
        return await self.get(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key="implementation_plan",
        )
