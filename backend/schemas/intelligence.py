"""
Pydantic Schemas for Workflow Intelligence (Stream I)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from backend.models.workflow import WorkflowPhase


class TaskSuggestionResponse(BaseModel):
    """Response schema for a task suggestion"""
    title: str = Field(..., description="Suggested task title")
    description: str = Field(..., description="Task description")
    phase: WorkflowPhase = Field(..., description="Suggested phase")
    rationale: str = Field(..., description="Why this task is suggested")
    estimated_value: float = Field(..., ge=0.0, le=1.0, description="Estimated value (0.0-1.0)")
    priority: str = Field(..., description="Priority: low, medium, high, urgent")
    blocking_task_ids: List[UUID] = Field(default_factory=list, description="Tasks that must complete first")
    suggested_agent_id: Optional[UUID] = Field(None, description="Suggested agent for this task")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in suggestion (0.0-1.0)")
    reasoning: str = Field(..., description="Detailed reasoning for the suggestion")
    estimated_duration_hours: Optional[float] = Field(None, description="Estimated duration in hours")

    class Config:
        from_attributes = True
        use_enum_values = True


class WorkflowPredictionResponse(BaseModel):
    """Response schema for workflow outcome prediction"""
    execution_id: UUID
    predicted_completion_time: Optional[datetime] = Field(None, description="Predicted completion datetime")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of success (0.0-1.0)")
    estimated_total_hours: Optional[float] = Field(None, description="Estimated remaining hours")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in prediction (0.0-1.0)")
    reasoning: str = Field(..., description="Human-readable reasoning")
    calculated_at: datetime

    class Config:
        from_attributes = True


class OptimizedTaskOrderResponse(BaseModel):
    """Response schema for optimized task ordering"""
    execution_id: UUID
    ordered_tasks: List[Dict[str, Any]] = Field(..., description="Tasks in optimized order")
    optimization_rationale: str = Field(..., description="Why this ordering was chosen")
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int

    class Config:
        from_attributes = True

