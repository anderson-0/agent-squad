"""
Advanced PM Guardian API Endpoints (Stream G)

Enhanced endpoints for advanced Guardian monitoring:
- Advanced coherence metrics
- Anomaly detection
- Recommendations
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.project import TaskExecution
from backend.agents.guardian.advanced_anomaly_detector import (
    AdvancedAnomalyDetector,
    Anomaly,
    get_anomaly_detector,
)
from backend.agents.guardian.recommendations_engine import (
    RecommendationsEngine,
    Recommendation,
    get_recommendations_engine,
)
from backend.agents.guardian.coherence_scorer import CoherenceScorer, get_coherence_scorer
from backend.models.workflow import WorkflowPhase
from backend.core.logging import logger


router = APIRouter(prefix="/advanced-guardian", tags=["advanced-guardian"])


# Response schemas
class AnomalyResponse(BaseModel):
    """Anomaly response"""
    type: str
    severity: str
    description: str
    recommendation: str
    metadata: dict = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Recommendation response"""
    type: str
    action: str
    priority: str
    target_agents: List[UUID] = Field(default_factory=list)
    rationale: str = None
    metadata: dict = Field(default_factory=dict)


class AdvancedMetricsResponse(BaseModel):
    """Advanced metrics response"""
    execution_id: UUID
    anomalies: List[AnomalyResponse]
    recommendations: List[RecommendationResponse]
    coherence_scores: List[dict] = Field(default_factory=list)


@router.get(
    "/workflows/{execution_id}/anomalies",
    response_model=List[AnomalyResponse],
    summary="Detect workflow anomalies",
    description="Detect anomalies in workflow execution"
)
async def detect_anomalies(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AnomalyResponse]:
    """
    Detect anomalies in workflow.
    
    Detects:
    - Phase drift
    - Low-value tasks
    - Workflow stagnation
    - Resource imbalance
    - Communication gaps
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Detect anomalies
        detector = get_anomaly_detector()
        anomalies = await detector.detect_anomalies(db, execution_id)
        
        return [
            AnomalyResponse(
                type=anomaly.type,
                severity=anomaly.severity,
                description=anomaly.description,
                recommendation=anomaly.recommendation,
                metadata=anomaly.metadata,
            )
            for anomaly in anomalies
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect anomalies: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/recommendations",
    response_model=List[RecommendationResponse],
    summary="Get recommendations",
    description="Get actionable recommendations for workflow improvement"
)
async def get_recommendations(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RecommendationResponse]:
    """
    Get recommendations for workflow improvement.
    
    Recommendations are generated based on:
    - Detected anomalies
    - Coherence scores
    - Workflow health
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get coherence scores for all agents
        scorer = get_coherence_scorer()
        coherence_scores = []
        
        # Get all active agents in execution's squad
        if hasattr(execution, 'squad') and execution.squad:
            for member in execution.squad.members:
                if member.is_active:
                    try:
                        score = await scorer.calculate_coherence(
                            db=db,
                            agent_id=member.id,
                            execution_id=execution_id,
                            phase=WorkflowPhase.BUILDING,  # Default, can be enhanced
                        )
                        coherence_scores.append(score)
                    except Exception as e:
                        logger.debug(f"Could not calculate coherence for agent {member.id}: {e}")
        
        # Generate recommendations
        recommendations_engine = get_recommendations_engine()
        recommendations = await recommendations_engine.generate_recommendations(
            db=db,
            execution_id=execution_id,
            coherence_scores=coherence_scores,
        )
        
        return [
            RecommendationResponse(
                type=rec.type,
                action=rec.action,
                priority=rec.priority,
                target_agents=rec.target_agents,
                rationale=rec.rationale,
                metadata=rec.metadata,
            )
            for rec in recommendations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/advanced-metrics",
    response_model=AdvancedMetricsResponse,
    summary="Get advanced metrics",
    description="Get comprehensive advanced metrics (anomalies + recommendations + coherence)"
)
async def get_advanced_metrics(
    execution_id: UUID = Path(..., description="Task execution ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdvancedMetricsResponse:
    """
    Get comprehensive advanced metrics.
    
    Returns:
    - Detected anomalies
    - Recommendations
    - Coherence scores for all agents
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get anomalies
        detector = get_anomaly_detector()
        anomalies = await detector.detect_anomalies(db, execution_id)
        
        # Get coherence scores
        scorer = get_coherence_scorer()
        coherence_scores = []
        
        if hasattr(execution, 'squad') and execution.squad:
            for member in execution.squad.members:
                if member.is_active:
                    try:
                        score = await scorer.calculate_coherence(
                            db=db,
                            agent_id=member.id,
                            execution_id=execution_id,
                            phase=WorkflowPhase.BUILDING,
                        )
                        coherence_scores.append(score.to_dict())
                    except Exception as e:
                        logger.debug(f"Could not calculate coherence for agent {member.id}: {e}")
        
        # Get recommendations
        recommendations_engine = get_recommendations_engine()
        recommendations = await recommendations_engine.generate_recommendations(
            db=db,
            execution_id=execution_id,
            coherence_scores=[scorer for scorer in coherence_scores if isinstance(scorer, dict)],
        )
        
        return AdvancedMetricsResponse(
            execution_id=execution_id,
            anomalies=[
                AnomalyResponse(
                    type=anomaly.type,
                    severity=anomaly.severity,
                    description=anomaly.description,
                    recommendation=anomaly.recommendation,
                    metadata=anomaly.metadata,
                )
                for anomaly in anomalies
            ],
            recommendations=[
                RecommendationResponse(
                    type=rec.type,
                    action=rec.action,
                    priority=rec.priority,
                    target_agents=rec.target_agents,
                    rationale=rec.rationale,
                    metadata=rec.metadata,
                )
                for rec in recommendations
            ],
            coherence_scores=coherence_scores,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting advanced metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get advanced metrics: {str(e)}"
        )

