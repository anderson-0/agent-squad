"""
ML-Based Detection API Endpoints (Stream H)

Provides API for:
- ML-powered opportunity detection
- Task value prediction
- Model training
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.agents.ml import (
    OpportunityDetector,
    get_opportunity_detector,
    OptimizationOpportunity,
    ModelMetrics,
)
from backend.schemas.ml import (
    OptimizationOpportunityResponse,
    TaskValuePredictionResponse,
    ModelMetricsResponse,
    TrainModelRequest,
)
from backend.core.logging import logger


router = APIRouter(prefix="/ml-detection", tags=["ml-detection"])


@router.post(
    "/opportunities/detect",
    response_model=List[OptimizationOpportunityResponse],
    summary="Detect optimization opportunities",
    description="Use ML to detect optimization opportunities in code context"
)
async def detect_opportunities(
    code_context: str = Body(..., description="Code or context to analyze"),
    execution_id: Optional[UUID] = Body(None, description="Optional execution ID"),
    performance_metrics: Optional[dict] = Body(None, description="Optional performance metrics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[OptimizationOpportunityResponse]:
    """
    Detect optimization opportunities using ML.
    
    Analyzes code context for:
    - Optimization opportunities
    - Performance issues
    - Refactoring needs
    - Bugs
    """
    try:
        detector = get_opportunity_detector()
        opportunities = await detector.detect_optimization_opportunities(
            code_context=code_context,
            performance_metrics=performance_metrics,
            execution_id=execution_id,
        )
        
        return [
            OptimizationOpportunityResponse(
                type=opp.type,
                description=opp.description,
                code_context=opp.code_context,
                confidence=opp.confidence,
                estimated_value=opp.estimated_value,
                suggested_phase=opp.suggested_phase,
                metadata=opp.metadata,
            )
            for opp in opportunities
        ]
    
    except Exception as e:
        logger.error(f"Error detecting opportunities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect opportunities: {str(e)}"
        )


@router.post(
    "/predict-value",
    response_model=TaskValuePredictionResponse,
    summary="Predict task value",
    description="Predict the value of a potential task"
)
async def predict_task_value(
    task_description: str = Body(..., description="Task description"),
    execution_id: Optional[UUID] = Body(None, description="Optional execution ID for context"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskValuePredictionResponse:
    """
    Predict the value of a potential task.
    
    Uses ML and historical data to predict task value.
    """
    try:
        detector = get_opportunity_detector()
        
        # Get historical tasks if execution_id provided
        historical_tasks = None
        if execution_id:
            from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
            engine = PhaseBasedWorkflowEngine()
            historical_tasks = await engine.get_tasks_for_execution(
                db=db,
                execution_id=execution_id,
            )
        
        predicted_value = await detector.predict_task_value(
            task_description=task_description,
            historical_similar_tasks=historical_tasks[:10] if historical_tasks else None,
        )
        
        # Simple confidence based on description quality
        confidence = min(len(task_description) / 100.0, 0.9) if task_description else 0.5
        
        return TaskValuePredictionResponse(
            task_description=task_description,
            predicted_value=predicted_value,
            confidence=confidence,
            reasoning=f"Predicted value: {predicted_value:.2f} based on description analysis",
        )
    
    except Exception as e:
        logger.error(f"Error predicting task value: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict task value: {str(e)}"
        )


@router.post(
    "/train",
    response_model=ModelMetricsResponse,
    summary="Train model",
    description="Train ML model on historical data"
)
async def train_model(
    request: TrainModelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelMetricsResponse:
    """
    Train ML model on historical data.
    
    Requires scikit-learn to be installed.
    """
    try:
        detector = get_opportunity_detector()
        
        if not detector.use_ml:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML features are not available. Install scikit-learn for training."
            )
        
        metrics = await detector.train_model(
            historical_data=request.historical_data,
            validation_split=request.validation_split,
        )
        
        return ModelMetricsResponse(
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            training_samples=metrics.training_samples,
            validation_samples=metrics.validation_samples,
            trained_at=metrics.trained_at,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train model: {str(e)}"
        )

