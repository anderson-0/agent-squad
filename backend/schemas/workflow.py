"""
Workflow Pydantic Schemas

Request/response schemas for Phase-Based Workflow API endpoints.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.models.workflow import WorkflowPhase


class TaskSpawnRequest(BaseModel):
    """Schema for spawning a new dynamic task"""
    phase: WorkflowPhase = Field(..., description="Phase: investigation, building, or validation")
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: str = Field(..., min_length=1, description="Task description")
    rationale: Optional[str] = Field(None, description="Why this task was created (especially for investigation)")
    blocking_task_ids: Optional[List[UUID]] = Field(
        None,
        description="Optional list of task IDs this task blocks"
    )

    @field_validator('phase')
    @classmethod
    def validate_phase(cls, v):
        """Ensure phase is valid"""
        if not isinstance(v, WorkflowPhase):
            try:
                v = WorkflowPhase(v)
            except ValueError:
                raise ValueError(f"Invalid phase: {v}. Must be one of: {[p.value for p in WorkflowPhase]}")
        return v


class TaskSpawnResponse(BaseModel):
    """Schema for spawned task response"""
    id: UUID
    parent_execution_id: UUID
    phase: str
    spawned_by_agent_id: UUID
    title: str
    description: str
    status: str
    rationale: Optional[str] = None
    blocking_task_ids: List[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Schema for dynamic task response"""
    id: UUID
    parent_execution_id: UUID
    phase: str
    spawned_by_agent_id: UUID
    title: str
    description: str
    status: str
    rationale: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    blocks_tasks: List["TaskResponse"] = Field(default_factory=list)
    blocked_by_tasks: List["TaskResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status"""
    status: str = Field(..., description="New status: pending, in_progress, completed, failed, blocked")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is valid"""
        valid_statuses = ["pending", "in_progress", "completed", "failed", "blocked"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of: {valid_statuses}")
        return v


class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: List[TaskResponse]
    total: int
    phase: Optional[str] = None
    status: Optional[str] = None

