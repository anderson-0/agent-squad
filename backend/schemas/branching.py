"""
Branching Pydantic Schemas (Stream E)

Request/response schemas for workflow branching API endpoints.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from backend.models.workflow import WorkflowPhase


class CreateBranchRequest(BaseModel):
    """Request to create a branch from discovery"""
    discovery_id: UUID = Field(..., description="Discovery that triggers branch")
    branch_name: Optional[str] = Field(None, description="Optional custom branch name")
    initial_task_title: Optional[str] = Field(None, description="Title for initial branch task")
    initial_task_description: Optional[str] = Field(None, description="Description for initial branch task")
    agent_id: UUID = Field(..., description="Agent creating the branch")


class BranchResponse(BaseModel):
    """Branch response schema"""
    id: UUID
    parent_execution_id: UUID
    branch_name: str
    branch_phase: str
    discovery_origin_type: Optional[str] = None
    discovery_description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class MergeBranchRequest(BaseModel):
    """Request to merge a branch"""
    merge_summary: Optional[str] = Field(None, description="Optional summary of merge results")


class BranchTasksResponse(BaseModel):
    """Response with branch and its tasks"""
    branch: BranchResponse
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0

