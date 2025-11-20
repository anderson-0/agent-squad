"""
Pydantic Schemas for ML-Based Detection (Stream H)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from backend.models.workflow import WorkflowPhase


class OptimizationOpportunityResponse(BaseModel):
    """Response schema for an optimization opportunity"""
    type: str = Field(..., description="Type: optimization, bug, refactoring, performance")
    description: str = Field(..., description="Description of the opportunity")
    code_context: Optional[str] = Field(None, description="Relevant code context")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    estimated_value: float = Field(..., ge=0.0, le=1.0, description="Estimated value")
    suggested_phase: WorkflowPhase = Field(..., description="Suggested workflow phase")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        from_attributes = True
        use_enum_values = True


class TaskValuePredictionResponse(BaseModel):
    """Response schema for task value prediction"""
    task_description: str
    predicted_value: float = Field(..., ge=0.0, le=1.0, description="Predicted value (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in prediction")
    reasoning: Optional[str] = Field(None, description="Reasoning for the prediction")


class ModelMetricsResponse(BaseModel):
    """Response schema for model training metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    validation_samples: int
    trained_at: datetime

    class Config:
        from_attributes = True


class TrainModelRequest(BaseModel):
    """Request schema for training a model"""
    historical_data: List[Dict[str, Any]] = Field(..., description="Historical task/discovery data")
    validation_split: float = Field(0.2, ge=0.1, le=0.5, description="Validation split ratio")

