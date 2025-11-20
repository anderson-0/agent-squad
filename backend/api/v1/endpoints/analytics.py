"""
Analytics API Endpoints (Stream K)

Provides API for:
- Workflow analytics
- Workflow graph visualization
- Historical metrics
"""
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.project import TaskExecution
from backend.services.analytics_service import get_analytics_service, WorkflowAnalytics
from backend.schemas.analytics import (
    WorkflowAnalyticsResponse,
    WorkflowGraphResponse,
    PhaseDistribution,
    CoherenceTrend,
)
from datetime import datetime
from backend.core.logging import logger


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/workflows/{execution_id}",
    response_model=WorkflowAnalyticsResponse,
    summary="Get workflow analytics",
    description="Get comprehensive analytics for a workflow"
)
async def get_workflow_analytics(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowAnalyticsResponse:
    """
    Get comprehensive analytics for a workflow.
    
    Returns:
    - Completion metrics
    - Phase distribution
    - Branch information
    - Agent performance
    - Coherence trends
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Calculate analytics
        analytics_service = get_analytics_service()
        analytics = await analytics_service.calculate_workflow_analytics(
            db=db,
            execution_id=execution_id,
        )
        
        # Convert to response
        return WorkflowAnalyticsResponse(
            execution_id=analytics.execution_id,
            completion_rate=analytics.completion_rate,
            average_task_duration_hours=analytics.average_task_duration_hours,
            phase_distribution=PhaseDistribution(
                investigation=analytics.phase_distribution.get("investigation", 0),
                building=analytics.phase_distribution.get("building", 0),
                validation=analytics.phase_distribution.get("validation", 0),
            ),
            branch_count=analytics.branch_count,
            discovery_to_value_conversion=analytics.discovery_to_value_conversion,
            agent_performance={str(k): v for k, v in analytics.agent_performance.items()},
            coherence_trends=[
                CoherenceTrend(
                    agent_id=UUID(trend["agent_id"]),
                    coherence_score=trend["coherence_score"],
                    calculated_at=datetime.fromisoformat(trend["calculated_at"].replace("Z", "+00:00")),
                    phase=trend["phase"],
                )
                for trend in analytics.coherence_trends
            ],
            calculated_at=analytics.calculated_at,
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate analytics: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/graph",
    response_model=WorkflowGraphResponse,
    summary="Get workflow graph",
    description="Get workflow graph data for visualization"
)
async def get_workflow_graph(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowGraphResponse:
    """
    Get workflow graph data for visualization.
    
    Returns nodes (tasks), edges (dependencies), and branches.
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get graph data
        analytics_service = get_analytics_service()
        graph_data = await analytics_service.get_workflow_graph_data(
            db=db,
            execution_id=execution_id,
        )
        
        return WorkflowGraphResponse(
            nodes=[
                {
                    "id": node["id"],
                    "title": node["title"],
                    "phase": node["phase"],
                    "status": node["status"],
                    "created_at": node["created_at"],
                }
                for node in graph_data["nodes"]
            ],
            edges=[
                WorkflowGraphEdge(
                    from_node=edge["from"],
                    to=edge["to"],
                    type=edge["type"],
                )
                for edge in graph_data["edges"]
            ],
            branches=[
                {
                    "id": branch["id"],
                    "name": branch["name"],
                    "phase": branch["phase"],
                    "status": branch["status"],
                }
                for branch in graph_data["branches"]
            ],
            phases=graph_data["phases"],
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow graph: {str(e)}"
        )
