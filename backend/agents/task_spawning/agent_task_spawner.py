"""
Agent Task Spawning Service

Provides task spawning capabilities to agents through a clean interface.
This service encapsulates the workflow engine and provides agent-friendly methods.
"""
from typing import Optional, List
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.models.workflow import WorkflowPhase, DynamicTask

logger = logging.getLogger(__name__)


class AgentTaskSpawner:
    """
    Service for agents to spawn tasks in any phase.
    
    This provides a clean interface between agents and the PhaseBasedWorkflowEngine,
    making it easy for agents to create tasks as they discover opportunities.
    """
    
    def __init__(self):
        """Initialize task spawner with workflow engine"""
        self.workflow_engine = PhaseBasedWorkflowEngine()
    
    async def spawn_investigation_task(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        title: str,
        description: str,
        rationale: str,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> DynamicTask:
        """
        Spawn a new investigation phase task.
        
        Investigation tasks are for exploring, analyzing, and discovering.
        Used when agents find opportunities that need investigation.
        
        Example:
            "Analyze auth caching pattern - could apply to 12 other API routes for 40% speedup"
        
        Args:
            db: Database session
            agent_id: Agent spawning the task
            execution_id: Parent task execution
            title: Task title
            description: Task description
            rationale: Why this task is being created (required for investigation)
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
        """
        return await self.workflow_engine.spawn_task(
            db=db,
            agent_id=agent_id,
            execution_id=execution_id,
            phase=WorkflowPhase.INVESTIGATION,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids or [],
        )
    
    async def spawn_building_task(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        title: str,
        description: str,
        rationale: Optional[str] = None,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> DynamicTask:
        """
        Spawn a new building/implementation phase task.
        
        Building tasks are for implementing, building, and creating.
        Used when agents need to implement something discovered or planned.
        
        Example:
            "Implement caching layer for auth routes"
        
        Args:
            db: Database session
            agent_id: Agent spawning the task
            execution_id: Parent task execution
            title: Task title
            description: Task description
            rationale: Optional reason why this task was created
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
        """
        return await self.workflow_engine.spawn_task(
            db=db,
            agent_id=agent_id,
            execution_id=execution_id,
            phase=WorkflowPhase.BUILDING,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids or [],
        )
    
    async def spawn_validation_task(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        title: str,
        description: str,
        rationale: Optional[str] = None,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> DynamicTask:
        """
        Spawn a new validation/testing phase task.
        
        Validation tasks are for testing, verifying, and validating.
        Used when agents need to test or verify work.
        
        Example:
            "Test API endpoints with new caching layer"
        
        Args:
            db: Database session
            agent_id: Agent spawning the task
            execution_id: Parent task execution
            title: Task title
            description: Task description
            rationale: Optional reason why this task was created
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
        """
        return await self.workflow_engine.spawn_task(
            db=db,
            agent_id=agent_id,
            execution_id=execution_id,
            phase=WorkflowPhase.VALIDATION,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids or [],
        )


# Singleton instance for agents to use
_agent_task_spawner: Optional[AgentTaskSpawner] = None


def get_agent_task_spawner() -> AgentTaskSpawner:
    """Get or create agent task spawner instance"""
    global _agent_task_spawner
    if _agent_task_spawner is None:
        _agent_task_spawner = AgentTaskSpawner()
    return _agent_task_spawner

