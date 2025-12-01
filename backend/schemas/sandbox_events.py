"""
Sandbox Event Schemas for SSE Broadcasting

These schemas define the structure of SSE events emitted during sandbox operations.
Events are broadcast to execution and squad channels for real-time frontend updates.

Event Types:
- sandbox_created: Sandbox initialized
- git_operation: Git command executed (clone, branch, commit, push)
- pr_created: Pull Request created on GitHub
- sandbox_terminated: Sandbox cleaned up
- sandbox_error: Error during sandbox operation
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime


class SandboxCreatedEvent(BaseModel):
    """
    Emitted when a new E2B sandbox is created

    Broadcast channels: execution, squad
    """
    event: Literal["sandbox_created"] = "sandbox_created"
    sandbox_id: UUID
    e2b_id: str
    task_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    repo_url: Optional[str] = None
    status: str = "RUNNING"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class GitOperationEvent(BaseModel):
    """
    Emitted when a Git operation is performed

    Operations: clone, create_branch, commit, push
    Broadcast channels: execution, squad
    """
    event: Literal["git_operation"] = "git_operation"
    sandbox_id: UUID
    operation: Literal["clone", "create_branch", "commit", "push"]
    status: Literal["started", "completed", "failed"]
    repo_url: Optional[str] = None
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PRCreatedEvent(BaseModel):
    """
    Emitted when a GitHub Pull Request is created

    Broadcast channels: execution, squad
    """
    event: Literal["pr_created"] = "pr_created"
    sandbox_id: UUID
    pr_number: int
    pr_url: str
    pr_title: str
    pr_body: Optional[str] = None
    head_branch: str
    base_branch: str
    repo_owner_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SandboxTerminatedEvent(BaseModel):
    """
    Emitted when a sandbox is terminated

    Broadcast channels: execution, squad
    """
    event: Literal["sandbox_terminated"] = "sandbox_terminated"
    sandbox_id: UUID
    e2b_id: str
    runtime_seconds: Optional[float] = None
    status: str = "TERMINATED"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SandboxErrorEvent(BaseModel):
    """
    Emitted when a sandbox operation fails

    Broadcast channels: execution, squad
    """
    event: Literal["sandbox_error"] = "sandbox_error"
    sandbox_id: UUID
    operation: str
    error_message: str
    error_details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# Union type for all sandbox events
SandboxEvent = (
    SandboxCreatedEvent |
    GitOperationEvent |
    PRCreatedEvent |
    SandboxTerminatedEvent |
    SandboxErrorEvent
)
