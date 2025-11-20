"""
Discovery Engine API Endpoints (Stream D)

Endpoints for discovery engine:
- Analyze work context
- Get task suggestions
- Evaluate discovery value
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.workflow import WorkflowPhase
from backend.models.project import TaskExecution
from backend.agents.discovery.discovery_engine import (
    DiscoveryEngine,
    TaskSuggestion,
    WorkContext,
    get_discovery_engine,
)
from backend.core.logging import logger


router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get(
    "/workflows/{execution_id}/analyze",
    summary="Analyze work context for discoveries",
    description="Analyze agent work context and discover opportunities"
)
async def analyze_work_context(
    execution_id: UUID = Path(..., description="Task execution ID"),
    agent_id: UUID = Query(..., description="Agent ID to analyze"),
    phase: WorkflowPhase = Query(..., description="Current workflow phase"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Analyze work context for discoveries.
    
    Returns list of discoveries with value scores.
    """
    try:
        # Validate execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Load agent messages
        from backend.models.message import AgentMessage
        from sqlalchemy import select
        
        message_stmt = (
            select(AgentMessage)
            .where(
                AgentMessage.task_execution_id == execution_id,
                AgentMessage.sender_id == agent_id,
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(20)
        )
        result = await db.execute(message_stmt)
        messages = list(result.scalars().all())
        
        # Load recent tasks
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        
        engine = PhaseBasedWorkflowEngine()
        all_tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        recent_tasks = [t for t in all_tasks if t.spawned_by_agent_id == agent_id][:10]
        
        # Create work context
        context = WorkContext(
            execution_id=execution_id,
            agent_id=agent_id,
            phase=phase,
            recent_messages=messages,
            recent_tasks=recent_tasks,
            work_output=None,  # Can be enhanced later
        )
        
        # Analyze
        discovery_engine = get_discovery_engine()
        discoveries = await discovery_engine.analyze_work_context(db, context)
        
        return {
            "discoveries": [d.model_dump() for d in discoveries],
            "total": len(discoveries),
            "execution_id": str(execution_id),
            "agent_id": str(agent_id),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing work context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze work context: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/suggestions",
    summary="Get task suggestions from discoveries",
    description="Discover opportunities and generate task suggestions"
)
async def get_task_suggestions(
    execution_id: UUID = Path(..., description="Task execution ID"),
    agent_id: UUID = Query(..., description="Agent ID"),
    phase: WorkflowPhase = Query(..., description="Current workflow phase"),
    min_value: float = Query(0.5, ge=0.0, le=1.0, description="Minimum value threshold"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Discover opportunities and generate task suggestions.
    
    Returns list of task suggestions ready to spawn.
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Load context (similar to analyze endpoint)
        from backend.models.message import AgentMessage
        from sqlalchemy import select
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        
        message_stmt = (
            select(AgentMessage)
            .where(
                AgentMessage.task_execution_id == execution_id,
                AgentMessage.sender_id == agent_id,
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(20)
        )
        result = await db.execute(message_stmt)
        messages = list(result.scalars().all())
        
        engine = PhaseBasedWorkflowEngine()
        all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution_id)
        recent_tasks = [t for t in all_tasks if t.spawned_by_agent_id == agent_id][:10]
        
        context = WorkContext(
            execution_id=execution_id,
            agent_id=agent_id,
            phase=phase,
            recent_messages=messages,
            recent_tasks=recent_tasks,
        )
        
        # Get suggestions
        discovery_engine = get_discovery_engine()
        suggestions = await discovery_engine.discover_and_suggest_tasks(
            db=db,
            context=context,
            min_value_threshold=min_value,
        )
        
        return {
            "suggestions": [s.model_dump() for s in suggestions],
            "total": len(suggestions),
            "execution_id": str(execution_id),
            "agent_id": str(agent_id),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )

