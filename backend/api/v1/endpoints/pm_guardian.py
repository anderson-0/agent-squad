"""
PM Guardian API Endpoints (Stream C)

Endpoints for PM-as-Guardian monitoring capabilities:
- Coherence checking
- Workflow health monitoring
- Metrics retrieval
- Anomaly detection
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.workflow import WorkflowPhase
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.guardian import (
    CoherenceScore,
    WorkflowHealth,
    get_coherence_scorer,
    get_workflow_health_monitor,
)
from backend.services.agent_service import AgentService
from backend.core.logging import logger


router = APIRouter(prefix="/pm-guardian", tags=["pm-guardian"])


# Response schemas
class CoherenceResponse(BaseModel):
    """Coherence score response"""
    overall_score: float = Field(..., description="Overall coherence (0.0-1.0)")
    metrics: dict = Field(..., description="Detailed metrics breakdown")
    agent_id: str
    phase: str
    calculated_at: str
    details: dict = Field(default_factory=dict)


class WorkflowHealthResponse(BaseModel):
    """Workflow health response"""
    overall_score: float = Field(..., description="Overall health (0.0-1.0)")
    metrics: dict = Field(..., description="Health metrics")
    anomalies: List[dict] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    calculated_at: str


class OrchestrationReportResponse(BaseModel):
    """Orchestration with Guardian oversight response"""
    orchestration_status: str
    workflow_health: dict
    coherence_results: dict
    guardian_actions: List[str]


@router.get(
    "/workflows/{execution_id}/coherence/{agent_id}",
    response_model=CoherenceResponse,
    summary="Check agent coherence",
    description="Check if agent's work aligns with phase goals"
)
async def check_coherence(
    execution_id: UUID = Path(..., description="Task execution ID"),
    agent_id: UUID = Path(..., description="Agent ID to check"),
    phase: WorkflowPhase = Query(..., description="Workflow phase"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CoherenceResponse:
    """
    Check coherence for a specific agent.
    
    Returns coherence score indicating how well agent's work aligns with phase goals.
    """
    try:
        # Get PM agent (assume first PM in squad)
        from backend.models.project import TaskExecution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        from backend.models.squad import SquadMember
        from sqlalchemy import select
        
        # Get PM agent for this squad
        pm_query = select(SquadMember).where(
            SquadMember.squad_id == execution.squad_id,
            SquadMember.role == "project_manager",
            SquadMember.is_active == True,
        ).limit(1)
        pm_result = await db.execute(pm_query)
        pm_member = pm_result.scalar_one_or_none()
        
        if not pm_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active PM agent found in squad"
            )
        
        # Create PM agent instance
        from backend.agents.factory import AgentFactory
        pm_agent = AgentFactory.create_agent(
            agent_id=pm_member.id,
            role="project_manager",
            llm_provider=pm_member.llm_provider or "openai",
            llm_model=pm_member.llm_model or "gpt-4",
        )
        
        # Check coherence
        coherence = await pm_agent.check_phase_coherence(
            db=db,
            execution_id=execution_id,
            agent_id=agent_id,
            phase=phase,
        )
        
        return CoherenceResponse(
            overall_score=coherence.overall_score,
            metrics=coherence.metrics,
            agent_id=str(coherence.agent_id),
            phase=coherence.phase.value,
            calculated_at=coherence.calculated_at.isoformat(),
            details=coherence.details,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking coherence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check coherence: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/health",
    response_model=WorkflowHealthResponse,
    summary="Monitor workflow health",
    description="Get overall workflow health metrics"
)
async def get_workflow_health(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowHealthResponse:
    """Get workflow health metrics"""
    try:
        from backend.models.project import TaskExecution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        from backend.models.squad import SquadMember
        from sqlalchemy import select
        
        # Get PM agent
        pm_query = select(SquadMember).where(
            SquadMember.squad_id == execution.squad_id,
            SquadMember.role == "project_manager",
            SquadMember.is_active == True,
        ).limit(1)
        pm_result = await db.execute(pm_query)
        pm_member = pm_result.scalar_one_or_none()
        
        if not pm_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active PM agent found in squad"
            )
        
        from backend.agents.factory import AgentFactory
        pm_agent = AgentFactory.create_agent(
            agent_id=pm_member.id,
            role="project_manager",
            llm_provider=pm_member.llm_provider or "openai",
            llm_model=pm_member.llm_model or "gpt-4",
        )
        
        # Monitor health
        health = await pm_agent.monitor_workflow_health(
            db=db,
            execution_id=execution_id,
        )
        
        return WorkflowHealthResponse(
            overall_score=health.overall_score,
            metrics=health.metrics,
            anomalies=[a.to_dict() for a in health.anomalies],
            recommendations=health.recommendations,
            calculated_at=health.calculated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error monitoring health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor health: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/metrics",
    summary="Get coherence metrics",
    description="Get historical coherence metrics for an execution"
)
async def get_coherence_metrics(
    execution_id: UUID = Path(..., description="Task execution ID"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    phase: Optional[WorkflowPhase] = Query(None, description="Filter by phase"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get coherence metrics for an execution"""
    try:
        from backend.models.guardian import CoherenceMetrics
        from sqlalchemy import select
        
        query = select(CoherenceMetrics).where(
            CoherenceMetrics.execution_id == execution_id
        )
        
        if agent_id:
            query = query.where(CoherenceMetrics.agent_id == agent_id)
        
        if phase:
            query = query.where(CoherenceMetrics.phase == phase.value)
        
        query = query.order_by(CoherenceMetrics.calculated_at.desc()).limit(limit)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return {
            "metrics": [
                {
                    "id": str(m.id),
                    "agent_id": str(m.agent_id),
                    "phase": m.phase,
                    "coherence_score": m.coherence_score,
                    "metrics": m.metrics,
                    "anomaly_detected": m.anomaly_detected,
                    "pm_action_taken": m.pm_action_taken,
                    "calculated_at": m.calculated_at.isoformat(),
                }
                for m in metrics
            ],
            "total": len(metrics),
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.post(
    "/workflows/{execution_id}/orchestrate",
    response_model=OrchestrationReportResponse,
    summary="Orchestrate with Guardian oversight",
    description="PM orchestrates workflow while monitoring as Guardian"
)
async def orchestrate_with_guardian(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrchestrationReportResponse:
    """Orchestrate workflow with Guardian monitoring"""
    try:
        from backend.models.project import TaskExecution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        from backend.models.squad import SquadMember
        from sqlalchemy import select
        
        # Get PM agent
        pm_query = select(SquadMember).where(
            SquadMember.squad_id == execution.squad_id,
            SquadMember.role == "project_manager",
            SquadMember.is_active == True,
        ).limit(1)
        pm_result = await db.execute(pm_query)
        pm_member = pm_result.scalar_one_or_none()
        
        if not pm_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active PM agent found in squad"
            )
        
        from backend.agents.factory import AgentFactory
        pm_agent = AgentFactory.create_agent(
            agent_id=pm_member.id,
            role="project_manager",
            llm_provider=pm_member.llm_provider or "openai",
            llm_model=pm_member.llm_model or "gpt-4",
        )
        
        # Orchestrate with Guardian oversight
        report = await pm_agent.orchestrate_with_guardian_oversight(
            db=db,
            execution_id=execution_id,
        )
        
        return OrchestrationReportResponse(**report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error orchestrating with Guardian: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to orchestrate: {str(e)}"
        )

