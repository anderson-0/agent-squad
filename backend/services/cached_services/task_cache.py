"""
Task and Execution Cache Service

Provides caching for task and execution data with automatic invalidation.

Features:
- Cache by task_id
- Cache tasks by project_id
- Cache execution by execution_id
- Cache execution status (high-frequency updates, 10s TTL)
- Cache executions by task_id
- Cache executions by squad_id
- Automatic invalidation on updates
- Configurable TTL (task: 30s, execution: 10s)
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models.project import Task, TaskExecution
from backend.services.cache_service import get_cache
from backend.services.cache_metrics import get_cache_metrics
from backend.core.config import settings

logger = logging.getLogger(__name__)


class TaskCacheService:
    """
    Task and execution caching service with invalidation support.

    Cache Keys:
    - task:{task_id} -> Full task object
    - task:project:{project_id} -> List of tasks for project
    - execution:{execution_id} -> Full execution object
    - execution:status:{execution_id} -> Execution status only (hot path)
    - execution:task:{task_id} -> List of executions for task
    - execution:squad:{squad_id} -> List of executions for squad

    TTL:
    - Tasks: CACHE_TASK_TTL (default: 30 seconds)
    - Executions: CACHE_EXECUTION_TTL (default: 10 seconds)
    """

    def __init__(self):
        self.cache = get_cache()
        self.metrics = get_cache_metrics()
        self.task_ttl = settings.CACHE_TASK_TTL  # 30 seconds
        self.execution_ttl = settings.CACHE_EXECUTION_TTL  # 10 seconds

    # =====================================================================
    # CACHE KEY GENERATORS
    # =====================================================================

    def _task_key(self, task_id: UUID) -> str:
        """Generate cache key for task by ID"""
        return f"task:{str(task_id)}"

    def _project_tasks_key(self, project_id: UUID) -> str:
        """Generate cache key for project's tasks"""
        return f"task:project:{str(project_id)}"

    def _execution_key(self, execution_id: UUID) -> str:
        """Generate cache key for execution by ID"""
        return f"execution:{str(execution_id)}"

    def _execution_status_key(self, execution_id: UUID) -> str:
        """Generate cache key for execution status (hot path)"""
        return f"execution:status:{str(execution_id)}"

    def _task_executions_key(self, task_id: UUID) -> str:
        """Generate cache key for task's executions"""
        return f"execution:task:{str(task_id)}"

    def _squad_executions_key(self, squad_id: UUID) -> str:
        """Generate cache key for squad's executions"""
        return f"execution:squad:{str(squad_id)}"

    # =====================================================================
    # SERIALIZATION
    # =====================================================================

    def _serialize_task(self, task: Task) -> dict:
        """Serialize task object to dict for caching"""
        return {
            "id": str(task.id),
            "project_id": str(task.project_id),
            "external_id": task.external_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assigned_to": task.assigned_to,
            "task_metadata": task.task_metadata,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    def _serialize_execution(self, execution: TaskExecution) -> dict:
        """Serialize execution object to dict for caching"""
        return {
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "squad_id": str(execution.squad_id),
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "logs": execution.logs,
            "error_message": execution.error_message,
            "execution_metadata": execution.execution_metadata,
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
        }

    # =====================================================================
    # TASK CACHING
    # =====================================================================

    async def get_task_by_id(
        self,
        db: AsyncSession,
        task_id: UUID,
        use_cache: bool = True
    ) -> Optional[Task]:
        """
        Get task by ID with caching.

        Args:
            db: Database session
            task_id: Task ID
            use_cache: Whether to use cache (default: True)

        Returns:
            Task object or None if not found
        """
        cache_key = self._task_key(task_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("task")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("task")

        result = await db.execute(
            select(Task).filter(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        # Cache the result
        if task:
            serialized = self._serialize_task(task)
            await self.cache.set(cache_key, serialized, ttl=self.task_ttl)

        return task

    async def get_tasks_by_project(
        self,
        db: AsyncSession,
        project_id: UUID,
        use_cache: bool = True,
        status: Optional[str] = None
    ) -> List[Task]:
        """
        Get all tasks for a project with caching.

        Args:
            db: Database session
            project_id: Project ID
            use_cache: Whether to use cache (default: True)
            status: Optional status filter

        Returns:
            List of Task objects
        """
        cache_key = self._project_tasks_key(project_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("task")
                # Filter by status if provided
                if status:
                    return [t for t in cached_data if t.get("status") == status]
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("task")

        query = select(Task).filter(Task.project_id == project_id)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # Cache all tasks
        serialized_list = [self._serialize_task(t) for t in tasks]
        await self.cache.set(cache_key, serialized_list, ttl=self.task_ttl)

        # Also cache individual tasks
        for task in tasks:
            task_key = self._task_key(task.id)
            serialized = self._serialize_task(task)
            await self.cache.set(task_key, serialized, ttl=self.task_ttl)

        # Return filtered if needed
        if status:
            return [t for t in tasks if t.status == status]
        return tasks

    # =====================================================================
    # EXECUTION CACHING
    # =====================================================================

    async def get_execution_by_id(
        self,
        db: AsyncSession,
        execution_id: UUID,
        use_cache: bool = True
    ) -> Optional[TaskExecution]:
        """
        Get execution by ID with caching.

        Args:
            db: Database session
            execution_id: Execution ID
            use_cache: Whether to use cache (default: True)

        Returns:
            TaskExecution object or None if not found
        """
        cache_key = self._execution_key(execution_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("execution")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("execution")

        result = await db.execute(
            select(TaskExecution).filter(TaskExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        # Cache the result
        if execution:
            serialized = self._serialize_execution(execution)
            await self.cache.set(cache_key, serialized, ttl=self.execution_ttl)

        return execution

    async def get_execution_status(
        self,
        db: AsyncSession,
        execution_id: UUID,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get execution status with caching (HOT PATH - status polling).

        This is a specialized method for the most frequent query: getting just
        the execution status. Uses separate cache key with shorter TTL.

        Args:
            db: Database session
            execution_id: Execution ID
            use_cache: Whether to use cache (default: True)

        Returns:
            Execution status string or None if not found
        """
        cache_key = self._execution_status_key(execution_id)

        # Try cache first
        if use_cache:
            cached_status = await self.cache.get(cache_key)
            if cached_status:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("execution")
                return cached_status

        # Cache miss - fetch from database (status only)
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("execution")

        result = await db.execute(
            select(TaskExecution.status).filter(TaskExecution.id == execution_id)
        )
        status = result.scalar_one_or_none()

        # Cache just the status
        if status:
            await self.cache.set(cache_key, status, ttl=self.execution_ttl)

        return status

    async def get_executions_by_task(
        self,
        db: AsyncSession,
        task_id: UUID,
        use_cache: bool = True
    ) -> List[TaskExecution]:
        """
        Get all executions for a task with caching.

        Args:
            db: Database session
            task_id: Task ID
            use_cache: Whether to use cache (default: True)

        Returns:
            List of TaskExecution objects
        """
        cache_key = self._task_executions_key(task_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("execution")
                return cached_data

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("execution")

        result = await db.execute(
            select(TaskExecution)
            .filter(TaskExecution.task_id == task_id)
            .order_by(TaskExecution.created_at.desc())
        )
        executions = result.scalars().all()

        # Cache the results
        serialized_list = [self._serialize_execution(e) for e in executions]
        await self.cache.set(cache_key, serialized_list, ttl=self.execution_ttl)

        # Also cache individual executions
        for execution in executions:
            exec_key = self._execution_key(execution.id)
            serialized = self._serialize_execution(execution)
            await self.cache.set(exec_key, serialized, ttl=self.execution_ttl)

        return executions

    async def get_executions_by_squad(
        self,
        db: AsyncSession,
        squad_id: UUID,
        use_cache: bool = True,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskExecution]:
        """
        Get executions for a squad with caching.

        Args:
            db: Database session
            squad_id: Squad ID
            use_cache: Whether to use cache (default: True)
            status: Optional status filter
            limit: Max executions to return (default: 100)

        Returns:
            List of TaskExecution objects
        """
        cache_key = self._squad_executions_key(squad_id)

        # Try cache first
        if use_cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT: {cache_key}")
                await self.metrics.track_hit("execution")
                # Filter by status if provided
                filtered = cached_data
                if status:
                    filtered = [e for e in filtered if e.get("status") == status]
                return filtered[:limit]

        # Cache miss - fetch from database
        logger.debug(f"Cache MISS: {cache_key}")
        await self.metrics.track_miss("execution")

        query = (
            select(TaskExecution)
            .filter(TaskExecution.squad_id == squad_id)
            .order_by(TaskExecution.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        executions = result.scalars().all()

        # Cache the results
        serialized_list = [self._serialize_execution(e) for e in executions]
        await self.cache.set(cache_key, serialized_list, ttl=self.execution_ttl)

        # Return filtered if needed
        if status:
            return [e for e in executions if e.status == status]
        return executions

    # =====================================================================
    # INVALIDATION
    # =====================================================================

    async def invalidate_task(
        self,
        task_id: UUID,
        project_id: Optional[UUID] = None
    ):
        """
        Invalidate task cache.

        Args:
            task_id: Task ID to invalidate
            project_id: Optional project ID to invalidate project's task list
        """
        # Invalidate task cache
        task_key = self._task_key(task_id)
        await self.cache.delete(task_key)
        await self.metrics.track_invalidation("task")
        logger.info(f"Invalidated cache: {task_key}")

        # Invalidate task's executions list
        executions_key = self._task_executions_key(task_id)
        await self.cache.delete(executions_key)
        await self.metrics.track_invalidation("execution")
        logger.info(f"Invalidated cache: {executions_key}")

        # Invalidate project's tasks list if provided
        if project_id:
            project_key = self._project_tasks_key(project_id)
            await self.cache.delete(project_key)
            await self.metrics.track_invalidation("task")
            logger.info(f"Invalidated cache: {project_key}")

    async def invalidate_execution(
        self,
        execution_id: UUID,
        task_id: Optional[UUID] = None,
        squad_id: Optional[UUID] = None
    ):
        """
        Invalidate execution cache.

        Args:
            execution_id: Execution ID to invalidate
            task_id: Optional task ID to invalidate task's execution list
            squad_id: Optional squad ID to invalidate squad's execution list
        """
        # Invalidate execution cache
        exec_key = self._execution_key(execution_id)
        await self.cache.delete(exec_key)
        await self.metrics.track_invalidation("execution")
        logger.info(f"Invalidated cache: {exec_key}")

        # Invalidate execution status cache (HOT PATH)
        status_key = self._execution_status_key(execution_id)
        await self.cache.delete(status_key)
        await self.metrics.track_invalidation("execution")
        logger.info(f"Invalidated cache: {status_key}")

        # Invalidate task's executions list if provided
        if task_id:
            task_exec_key = self._task_executions_key(task_id)
            await self.cache.delete(task_exec_key)
            await self.metrics.track_invalidation("execution")
            logger.info(f"Invalidated cache: {task_exec_key}")

        # Invalidate squad's executions list if provided
        if squad_id:
            squad_exec_key = self._squad_executions_key(squad_id)
            await self.cache.delete(squad_exec_key)
            await self.metrics.track_invalidation("execution")
            logger.info(f"Invalidated cache: {squad_exec_key}")

    async def invalidate_project_tasks(self, project_id: UUID):
        """
        Invalidate all task caches for a project.

        Args:
            project_id: Project ID
        """
        project_key = self._project_tasks_key(project_id)
        await self.cache.delete(project_key)
        await self.metrics.track_invalidation("task")
        logger.info(f"Invalidated cache: {project_key}")

    async def invalidate_squad_executions(self, squad_id: UUID):
        """
        Invalidate all execution caches for a squad.

        Args:
            squad_id: Squad ID
        """
        squad_key = self._squad_executions_key(squad_id)
        await self.cache.delete(squad_key)
        await self.metrics.track_invalidation("execution")
        logger.info(f"Invalidated cache: {squad_key}")

    # =====================================================================
    # CACHE WARMING
    # =====================================================================

    async def warm_task_cache(
        self,
        db: AsyncSession,
        task_ids: List[UUID]
    ) -> int:
        """
        Warm cache for multiple tasks.

        Args:
            db: Database session
            task_ids: List of task IDs to cache

        Returns:
            Number of tasks cached
        """
        result = await db.execute(
            select(Task).filter(Task.id.in_(task_ids))
        )
        tasks = result.scalars().all()

        cached_count = 0
        for task in tasks:
            serialized = self._serialize_task(task)
            task_key = self._task_key(task.id)
            await self.cache.set(task_key, serialized, ttl=self.task_ttl)
            cached_count += 1

        logger.info(f"Warmed cache for {cached_count} tasks")
        return cached_count

    async def warm_execution_cache(
        self,
        db: AsyncSession,
        execution_ids: List[UUID]
    ) -> int:
        """
        Warm cache for multiple executions.

        Args:
            db: Database session
            execution_ids: List of execution IDs to cache

        Returns:
            Number of executions cached
        """
        result = await db.execute(
            select(TaskExecution).filter(TaskExecution.id.in_(execution_ids))
        )
        executions = result.scalars().all()

        cached_count = 0
        for execution in executions:
            # Cache full execution
            serialized = self._serialize_execution(execution)
            exec_key = self._execution_key(execution.id)
            await self.cache.set(exec_key, serialized, ttl=self.execution_ttl)

            # Cache status separately (HOT PATH)
            status_key = self._execution_status_key(execution.id)
            await self.cache.set(status_key, execution.status, ttl=self.execution_ttl)

            cached_count += 1

        logger.info(f"Warmed cache for {cached_count} executions")
        return cached_count


# Global instance
_task_cache_service: Optional[TaskCacheService] = None


def get_task_cache() -> TaskCacheService:
    """Get or create task cache service instance"""
    global _task_cache_service
    if _task_cache_service is None:
        _task_cache_service = TaskCacheService()
    return _task_cache_service


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Get task by ID with caching

    from backend.services.cached_services.task_cache import get_task_cache

    task_cache = get_task_cache()
    task = await task_cache.get_task_by_id(db, task_id)


Example 2: Get tasks for a project

    task_cache = get_task_cache()
    tasks = await task_cache.get_tasks_by_project(db, project_id)

    # Filter by status
    active_tasks = await task_cache.get_tasks_by_project(
        db, project_id, status="in_progress"
    )


Example 3: Get execution with caching

    task_cache = get_task_cache()
    execution = await task_cache.get_execution_by_id(db, execution_id)


Example 4: Get execution status (HOT PATH - most frequent query)

    task_cache = get_task_cache()
    # This uses a separate cache key optimized for status polling
    status = await task_cache.get_execution_status(db, execution_id)


Example 5: Get executions for a task

    task_cache = get_task_cache()
    executions = await task_cache.get_executions_by_task(db, task_id)


Example 6: Get executions for a squad

    task_cache = get_task_cache()
    executions = await task_cache.get_executions_by_squad(
        db, squad_id, status="in_progress", limit=50
    )


Example 7: Invalidate after task update

    # Update task in database
    task.status = "completed"
    await db.commit()

    # Invalidate cache
    task_cache = get_task_cache()
    await task_cache.invalidate_task(task.id, task.project_id)


Example 8: Invalidate after execution update

    # Update execution in database
    execution.status = "in_progress"
    await db.commit()

    # Invalidate cache (including HOT PATH status cache)
    task_cache = get_task_cache()
    await task_cache.invalidate_execution(
        execution.id,
        task_id=execution.task_id,
        squad_id=execution.squad_id
    )


Example 9: Warm cache for active executions

    task_cache = get_task_cache()
    active_execution_ids = [exec1_id, exec2_id, exec3_id]
    cached_count = await task_cache.warm_execution_cache(db, active_execution_ids)
    print(f"Cached {cached_count} executions")


Example 10: Bypass cache when needed

    task_cache = get_task_cache()
    # Force fresh data from database
    task = await task_cache.get_task_by_id(db, task_id, use_cache=False)
"""
