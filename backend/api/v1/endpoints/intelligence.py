"""
Workflow Intelligence API Endpoints (Stream I)

Provides API for:
- AI-powered task suggestions
- Workflow outcome predictions
- Task ordering optimization
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.project import TaskExecution
from backend.agents.intelligence import (
    WorkflowIntelligence,
    get_workflow_intelligence,
)
from backend.agents.intelligence.workflow_intelligence import (
    TaskSuggestion,
    WorkflowPrediction,
)
from backend.schemas.intelligence import (
    TaskSuggestionResponse,
    WorkflowPredictionResponse,
    OptimizedTaskOrderResponse,
)
from backend.core.logging import logger


router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get(
    "/workflows/{execution_id}/suggestions",
    response_model=List[TaskSuggestionResponse],
    summary="Get task suggestions",
    description="Get AI-powered task suggestions based on workflow intelligence"
)
async def get_task_suggestions(
    execution_id: UUID = Path(..., description="Task execution ID"),
    agent_id: Optional[UUID] = Query(None, description="Optional specific agent to suggest for"),
    max_suggestions: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TaskSuggestionResponse]:
    """
    Get intelligent task suggestions for a workflow.
    
    Considers:
    - Current workflow state
    - Agent coherence scores
    - Discovery opportunities
    - Active branches
    - Task dependencies
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get suggestions
        intelligence = get_workflow_intelligence()
        suggestions = await intelligence.suggest_next_tasks(
            db=db,
            execution_id=execution_id,
            agent_id=agent_id,
            max_suggestions=max_suggestions,
        )
        
        return [
            TaskSuggestionResponse(
                title=s.title,
                description=s.description,
                phase=s.phase,
                rationale=s.rationale,
                estimated_value=s.estimated_value,
                priority=s.priority,
                blocking_task_ids=s.blocking_task_ids,
                suggested_agent_id=s.suggested_agent_id,
                confidence=s.confidence,
                reasoning=s.reasoning,
                estimated_duration_hours=s.estimated_duration_hours,
            )
            for s in suggestions
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task suggestions: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/prediction",
    response_model=WorkflowPredictionResponse,
    summary="Predict workflow outcomes",
    description="Predict workflow completion time and success probability"
)
async def predict_workflow_outcomes(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowPredictionResponse:
    """
    Predict workflow outcomes.
    
    Returns:
    - Predicted completion time
    - Success probability
    - Risk factors
    - Confidence level
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get prediction
        intelligence = get_workflow_intelligence()
        prediction = await intelligence.predict_workflow_outcomes(
            db=db,
            execution_id=execution_id,
        )
        
        return WorkflowPredictionResponse(
            execution_id=prediction.execution_id,
            predicted_completion_time=prediction.predicted_completion_time,
            success_probability=prediction.success_probability,
            estimated_total_hours=prediction.estimated_total_hours,
            risk_factors=prediction.risk_factors,
            confidence=prediction.confidence,
            reasoning=prediction.reasoning,
            calculated_at=prediction.calculated_at,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting workflow outcomes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict workflow outcomes: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/optimize-order",
    response_model=OptimizedTaskOrderResponse,
    summary="Optimize task ordering",
    description="Get optimized task ordering for best completion"
)
async def optimize_task_ordering(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OptimizedTaskOrderResponse:
    """
    Optimize task ordering for optimal completion.
    
    Uses dependency analysis and priority to reorder tasks.
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get optimized order
        intelligence = get_workflow_intelligence()
        ordered_tasks = await intelligence.optimize_task_ordering(
            db=db,
            execution_id=execution_id,
        )
        
        # Build response
        pending = len([t for t in ordered_tasks if t.status == "pending"])
        in_progress = len([t for t in ordered_tasks if t.status == "in_progress"])
        
        return OptimizedTaskOrderResponse(
            execution_id=execution_id,
            ordered_tasks=[
                {
                    "id": str(t.id),
                    "title": t.title,
                    "phase": t.phase,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                }
                for t in ordered_tasks
            ],
            optimization_rationale="Tasks ordered by dependencies and creation time for optimal completion",
            total_tasks=len(ordered_tasks),
            pending_tasks=pending,
            in_progress_tasks=in_progress,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing task order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize task order: {str(e)}"
        )

