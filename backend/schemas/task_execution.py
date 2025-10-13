"""
Task Execution Pydantic Schemas

Request/response schemas for Task Execution API endpoints.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from backend.schemas.agent_message import AgentMessageResponse


class TaskExecutionBase(BaseModel):
    """Base task execution schema"""
    pass


class TaskExecutionCreate(BaseModel):
    """Schema for creating a task execution"""
    task_id: UUID = Field(..., description="Task to execute")
    squad_id: UUID = Field(..., description="Squad to execute the task")
    execution_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional execution metadata"
    )


class TaskExecutionResponse(BaseModel):
    """Schema for task execution response"""
    id: UUID
    task_id: UUID
    squad_id: UUID
    status: str = Field(..., description="Execution status")
    started_at: Optional[datetime] = Field(None, description="When execution started")
    completed_at: Optional[datetime] = Field(None, description="When execution completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Execution logs")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskExecutionWithMessages(TaskExecutionResponse):
    """Task execution with messages"""
    messages: List[AgentMessageResponse] = Field(
        default_factory=list,
        description="Agent messages for this execution"
    )
    total_messages: int = Field(0, description="Total message count")


class TaskExecutionSummary(BaseModel):
    """Task execution summary"""
    execution_id: UUID
    task_id: UUID
    squad_id: UUID
    status: str
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    message_count: int = Field(0, description="Total messages")
    messages_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Message count by type"
    )
    agent_activity: Dict[str, int] = Field(
        default_factory=dict,
        description="Message count by agent"
    )
    log_count: int = Field(0, description="Total log entries")
    error_count: int = Field(0, description="Number of error logs")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskExecutionCancel(BaseModel):
    """Schema for cancelling a task execution"""
    reason: Optional[str] = Field(None, description="Cancellation reason")


class HumanIntervention(BaseModel):
    """Schema for human intervention"""
    action: str = Field(
        ...,
        pattern="^(continue|cancel|retry)$",
        description="Intervention action"
    )
    instructions: Optional[str] = Field(
        None,
        max_length=1000,
        description="Instructions for agents"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
