"""
Kanban Board API Endpoints (Stream F)

Endpoints for Kanban board visualization of dynamic tasks:
- Get Kanban board data
- Get task dependencies graph
- Real-time updates via SSE (future)
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.core.logging import logger


router = APIRouter(prefix="/kanban", tags=["kanban"])


# Response schemas
class KanbanTask(BaseModel):
    """Task for Kanban board"""
    id: UUID
    title: str
    description: str
    phase: str
    status: str
    rationale: Optional[str]
    spawned_by_agent_id: UUID
    created_at: str
    updated_at: str
    blocking_task_ids: List[UUID] = Field(default_factory=list)
    blocked_by_task_ids: List[UUID] = Field(default_factory=list)


class KanbanColumn(BaseModel):
    """Column in Kanban board (represents a phase)"""
    phase: str
    title: str
    tasks: List[KanbanTask] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0


class DependencyEdge(BaseModel):
    """Edge in dependency graph"""
    from_task_id: UUID
    to_task_id: UUID
    type: str = "blocks"  # "blocks" means from_task blocks to_task


class KanbanBoardResponse(BaseModel):
    """Complete Kanban board data"""
    execution_id: UUID
    columns: List[KanbanColumn]
    dependencies: List[DependencyEdge] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0


@router.get(
    "/workflows/{execution_id}",
    response_model=KanbanBoardResponse,
    summary="Get Kanban board",
    description="Get Kanban board data for a workflow execution"
)
async def get_kanban_board(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KanbanBoardResponse:
    """
    Get Kanban board data for a workflow execution.
    
    Returns tasks organized by phase (columns) with status information.
    """
    try:
        # Validate execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get workflow engine
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        engine = PhaseBasedWorkflowEngine()
        
        # Get all tasks with dependencies eagerly loaded
        all_tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            include_dependencies=True,
        )
        
        # Organize tasks by phase
        columns = []
        phase_order = [
            (WorkflowPhase.INVESTIGATION, "Investigation"),
            (WorkflowPhase.BUILDING, "Building"),
            (WorkflowPhase.VALIDATION, "Validation"),
        ]
        
        dependencies = []
        all_blocking_ids = set()
        all_blocked_by_ids = set()
        
        for phase_enum, phase_title in phase_order:
            phase_tasks = [t for t in all_tasks if t.phase == phase_enum.value]
            
            # Convert to KanbanTask format
            kanban_tasks = []
            for task in phase_tasks:
                # Get blocking relationships
                blocking_ids = [t.id for t in task.blocks_tasks]
                blocked_by_ids = [t.id for t in task.blocked_by_tasks]
                
                all_blocking_ids.update(blocking_ids)
                all_blocked_by_ids.update(blocked_by_ids)
                
                # Add dependency edges
                for blocked_id in blocking_ids:
                    dependencies.append(DependencyEdge(
                        from_task_id=task.id,
                        to_task_id=blocked_id,
                        type="blocks",
                    ))
                
                kanban_tasks.append(KanbanTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    phase=task.phase,
                    status=task.status,
                    rationale=task.rationale,
                    spawned_by_agent_id=task.spawned_by_agent_id,
                    created_at=task.created_at.isoformat(),
                    updated_at=task.updated_at.isoformat(),
                    blocking_task_ids=blocking_ids,
                    blocked_by_task_ids=blocked_by_ids,
                ))
            
            # Count tasks by status
            completed = sum(1 for t in kanban_tasks if t.status == "completed")
            in_progress = sum(1 for t in kanban_tasks if t.status == "in_progress")
            pending = sum(1 for t in kanban_tasks if t.status == "pending")
            
            columns.append(KanbanColumn(
                phase=phase_enum.value,
                title=phase_title,
                tasks=kanban_tasks,
                total_tasks=len(kanban_tasks),
                completed_tasks=completed,
                in_progress_tasks=in_progress,
                pending_tasks=pending,
            ))
        
        # Calculate totals
        total_completed = sum(col.completed_tasks for col in columns)
        total_in_progress = sum(col.in_progress_tasks for col in columns)
        total_pending = sum(col.pending_tasks for col in columns)
        total_tasks = len(all_tasks)
        
        return KanbanBoardResponse(
            execution_id=execution_id,
            columns=columns,
            dependencies=dependencies,
            total_tasks=total_tasks,
            completed_tasks=total_completed,
            in_progress_tasks=total_in_progress,
            pending_tasks=total_pending,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Kanban board: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Kanban board: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/dependencies",
    summary="Get dependency graph",
    description="Get dependency graph data for visualization"
)
async def get_dependency_graph(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get dependency graph data for visualization.
    
    Returns nodes (tasks) and edges (dependencies) for graph rendering.
    """
    try:
        # Validate execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get workflow engine
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        engine = PhaseBasedWorkflowEngine()
        
        # Get all tasks with dependencies
        all_tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            include_dependencies=True,
        )
        
        # Build nodes
        nodes = [
            {
                "id": str(task.id),
                "title": task.title,
                "phase": task.phase,
                "status": task.status,
                "label": task.title[:30] + ("..." if len(task.title) > 30 else ""),
            }
            for task in all_tasks
        ]
        
        # Build edges
        edges = []
        for task in all_tasks:
            # Task blocks other tasks
            for blocked_task in task.blocks_tasks:
                edges.append({
                    "from": str(task.id),
                    "to": str(blocked_task.id),
                    "type": "blocks",
                    "label": "blocks",
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "execution_id": str(execution_id),
            "total_tasks": len(all_tasks),
            "total_dependencies": len(edges),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dependency graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dependency graph: {str(e)}"
        )

