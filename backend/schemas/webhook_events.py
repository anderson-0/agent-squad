"""
GitHub Webhook Event Schemas

Pydantic schemas for GitHub webhook events with SSE broadcasting support.
These events update PR status in real-time when PRs are approved, merged, or closed.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID


class PRApprovedEvent(BaseModel):
    """PR approved by reviewer (pull_request_review.submitted with state=approved)"""
    event: Literal["pr_approved"] = "pr_approved"
    sandbox_id: UUID
    pr_number: int
    pr_url: str
    reviewer: str  # GitHub username
    review_state: str  # "approved", "changes_requested", "commented"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PRMergedEvent(BaseModel):
    """PR merged into base branch (pull_request.closed with merged=true)"""
    event: Literal["pr_merged"] = "pr_merged"
    sandbox_id: UUID
    pr_number: int
    pr_url: str
    merged_by: str  # GitHub username
    merge_commit_sha: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PRClosedEvent(BaseModel):
    """PR closed without merging (pull_request.closed with merged=false)"""
    event: Literal["pr_closed"] = "pr_closed"
    sandbox_id: UUID
    pr_number: int
    pr_url: str
    closed_by: str  # GitHub username
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PRReopenedEvent(BaseModel):
    """PR reopened after being closed"""
    event: Literal["pr_reopened"] = "pr_reopened"
    sandbox_id: UUID
    pr_number: int
    pr_url: str
    reopened_by: str  # GitHub username
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class GitHubWebhookPayload(BaseModel):
    """
    GitHub webhook payload wrapper

    This is the raw payload received from GitHub.
    We'll extract relevant data and convert to our event schemas.
    """
    action: str  # "opened", "closed", "reopened", "submitted", etc.
    pull_request: Optional[dict] = None
    review: Optional[dict] = None
    repository: dict
    sender: dict


class WebhookValidationError(Exception):
    """Raised when webhook signature validation fails"""
    pass
