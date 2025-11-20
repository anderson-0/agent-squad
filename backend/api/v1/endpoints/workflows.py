"""
Workflow API Endpoints

Endpoints for phase-based workflow management including:
- Spawning dynamic tasks
- Listing tasks
- Updating task status
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.schemas.workflow import (
    TaskSpawnRequest,
    TaskSpawnResponse,
    TaskResponse,
    TaskStatusUpdate,
    TaskListResponse,
)
from backend.services.squad_service import SquadService
from backend.core.logging import logger


router = APIRouter(prefix="/workflows", tags=["workflows"])

# Global engine instance (singleton pattern)
_workflow_engine: Optional[PhaseBasedWorkflowEngine] = None


def get_workflow_engine() -> PhaseBasedWorkflowEngine:
    """Get or create workflow engine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = PhaseBasedWorkflowEngine()
    return _workflow_engine


@router.post(
    "/{execution_id}/tasks/spawn",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskSpawnResponse,
    summary="Spawn a dynamic task",
    description="Spawn a new task in any phase (investigation, building, validation)"
)
async def spawn_task(
    execution_id: UUID = Path(..., description="Parent task execution ID"),
    request: TaskSpawnRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    workflow_engine: PhaseBasedWorkflowEngine = Depends(get_workflow_engine),
) -> TaskSpawnResponse:
    """
    Spawn a new dynamic task in any phase.
    
    This enables Hephaestus-style dynamic workflow creation where agents
    can create tasks as they discover opportunities or issues.
    
    **Phases:**
    - **investigation**: Explore, analyze, discover
    - **building**: Implement, build, create  
    - **validation**: Test, verify, validate
    
    **Example:**
    ```json
    {
      "phase": "investigation",
      "title": "Analyze auth caching pattern",
      "description": "Could apply to 12 other API routes for 40% speedup",
      "rationale": "Discovered during API testing",
      "blocking_task_ids": []
    }
    ```
    """
    try:
        # Get agent_id from user context (for now, use first active squad member)
        # TODO: In future, agent_id should come from authenticated agent context
        # For now, we'll need to get it from request or user's squad
        # This is a placeholder - Stream B will provide proper agent context
        
        # Validate execution exists and user has access
        from backend.models.project import TaskExecution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # For now, get first agent from execution's squad
        # TODO: Stream B will provide proper agent_id in context
        from backend.models.squad import SquadMember
        from sqlalchemy import select
        
        agent_query = select(SquadMember).where(
            SquadMember.squad_id == execution.squad_id,
            SquadMember.is_active == True
        ).limit(1)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active agents found in squad"
            )
        
        # Spawn the task
        dynamic_task = await workflow_engine.spawn_task(
            db=db,
            agent_id=agent.id,
            execution_id=execution_id,
            phase=request.phase,
            title=request.title,
            description=request.description,
            rationale=request.rationale,
            blocking_task_ids=request.blocking_task_ids or [],
        )
        
        # Get blocking task IDs (query after commit to get relationships)
        blocking_ids = []
        if request.blocking_task_ids:
            blocking_ids = request.blocking_task_ids
        
        return TaskSpawnResponse(
            id=dynamic_task.id,
            parent_execution_id=dynamic_task.parent_execution_id,
            phase=dynamic_task.phase,
            spawned_by_agent_id=dynamic_task.spawned_by_agent_id,
            title=dynamic_task.title,
            description=dynamic_task.description,
            status=dynamic_task.status,
            rationale=dynamic_task.rationale,
            blocking_task_ids=blocking_ids,
            created_at=dynamic_task.created_at,
            updated_at=dynamic_task.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error spawning task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to spawn task: {str(e)}"
        )


@router.get(
    "/{execution_id}/tasks",
    response_model=TaskListResponse,
    summary="List dynamic tasks",
    description="Get all dynamic tasks for a workflow execution"
)
async def list_tasks(
    execution_id: UUID = Path(..., description="Parent task execution ID"),
    phase: Optional[WorkflowPhase] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    workflow_engine: PhaseBasedWorkflowEngine = Depends(get_workflow_engine),
) -> TaskListResponse:
    """
    List all dynamic tasks for a workflow execution.
    
    Can be filtered by phase and/or status.
    """
    try:
        # Validate execution exists
        from backend.models.project import TaskExecution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get tasks with dependencies eagerly loaded (prevents N+1 queries)
        tasks = await workflow_engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            phase=phase,
            status=status,
            include_dependencies=True,  # Eager load to prevent N+1
        )
        
        # Convert to response models (dependencies already loaded)
        task_responses = [
            TaskResponse(
                id=task.id,
                parent_execution_id=task.parent_execution_id,
                phase=task.phase,
                spawned_by_agent_id=task.spawned_by_agent_id,
                title=task.title,
                description=task.description,
                status=task.status,
                rationale=task.rationale,
                created_at=task.created_at,
                updated_at=task.updated_at,
                blocks_tasks=[],  # Simplified for list view (avoid deep nesting)
                blocked_by_tasks=[],  # Simplified for list view (avoid deep nesting)
            )
            for task in tasks
        ]
        
        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses),
            phase=phase.value if phase else None,
            status=status,
        )
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.get(
    "/{execution_id}/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    description="Get a specific dynamic task with its dependencies"
)
async def get_task(
    execution_id: UUID = Path(..., description="Parent task execution ID"),
    task_id: UUID = Path(..., description="Task ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    workflow_engine: PhaseBasedWorkflowEngine = Depends(get_workflow_engine),
) -> TaskResponse:
    """Get task details with dependencies"""
    try:
        task = await workflow_engine.get_task_with_dependencies(
            db=db,
            task_id=task_id,
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        if task.parent_execution_id != execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task {task_id} does not belong to execution {execution_id}"
            )
        
        # Convert to response with dependencies
        blocks = [
            TaskResponse(
                id=t.id,
                parent_execution_id=t.parent_execution_id,
                phase=t.phase,
                spawned_by_agent_id=t.spawned_by_agent_id,
                title=t.title,
                description=t.description,
                status=t.status,
                rationale=t.rationale,
                created_at=t.created_at,
                updated_at=t.updated_at,
                blocks_tasks=[],
                blocked_by_tasks=[],
            )
            for t in task.blocks_tasks
        ]
        
        blocked_by = [
            TaskResponse(
                id=t.id,
                parent_execution_id=t.parent_execution_id,
                phase=t.phase,
                spawned_by_agent_id=t.spawned_by_agent_id,
                title=t.title,
                description=t.description,
                status=t.status,
                rationale=t.rationale,
                created_at=t.created_at,
                updated_at=t.updated_at,
                blocks_tasks=[],
                blocked_by_tasks=[],
            )
            for t in task.blocked_by_tasks
        ]
        
        return TaskResponse(
            id=task.id,
            parent_execution_id=task.parent_execution_id,
            phase=task.phase,
            spawned_by_agent_id=task.spawned_by_agent_id,
            title=task.title,
            description=task.description,
            status=task.status,
            rationale=task.rationale,
            created_at=task.created_at,
            updated_at=task.updated_at,
            blocks_tasks=blocks,
            blocked_by_tasks=blocked_by,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.patch(
    "/{execution_id}/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update task status",
    description="Update the status of a dynamic task"
)
async def update_task_status(
    execution_id: UUID = Path(..., description="Parent task execution ID"),
    task_id: UUID = Path(..., description="Task ID"),
    request: TaskStatusUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    workflow_engine: PhaseBasedWorkflowEngine = Depends(get_workflow_engine),
) -> TaskResponse:
    """Update task status"""
    try:
        # Validate task exists and belongs to execution
        task = await db.get(DynamicTask, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        if task.parent_execution_id != execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task {task_id} does not belong to execution {execution_id}"
            )
        
        # Update status
        updated_task = await workflow_engine.update_task_status(
            db=db,
            task_id=task_id,
            new_status=request.status,
            metadata=request.metadata,
        )
        
        # Return with dependencies
        task_with_deps = await workflow_engine.get_task_with_dependencies(
            db=db,
            task_id=updated_task.id,
        )
        
        blocks = [
            TaskResponse(
                id=t.id,
                parent_execution_id=t.parent_execution_id,
                phase=t.phase,
                spawned_by_agent_id=t.spawned_by_agent_id,
                title=t.title,
                description=t.description,
                status=t.status,
                rationale=t.rationale,
                created_at=t.created_at,
                updated_at=t.updated_at,
                blocks_tasks=[],
                blocked_by_tasks=[],
            )
            for t in (task_with_deps.blocks_tasks if task_with_deps else [])
        ]
        
        blocked_by = [
            TaskResponse(
                id=t.id,
                parent_execution_id=t.parent_execution_id,
                phase=t.phase,
                spawned_by_agent_id=t.spawned_by_agent_id,
                title=t.title,
                description=t.description,
                status=t.status,
                rationale=t.rationale,
                created_at=t.created_at,
                updated_at=t.updated_at,
                blocks_tasks=[],
                blocked_by_tasks=[],
            )
            for t in (task_with_deps.blocked_by_tasks if task_with_deps else [])
        ]
        
        return TaskResponse(
            id=updated_task.id,
            parent_execution_id=updated_task.parent_execution_id,
            phase=updated_task.phase,
            spawned_by_agent_id=updated_task.spawned_by_agent_id,
            title=updated_task.title,
            description=updated_task.description,
            status=updated_task.status,
            rationale=updated_task.rationale,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
            blocks_tasks=blocks,
            blocked_by_tasks=blocked_by,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task status: {str(e)}"
        )

