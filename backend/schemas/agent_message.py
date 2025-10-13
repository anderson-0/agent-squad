"""
Agent Message Schemas for A2A (Agent-to-Agent) Communication
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from uuid import UUID


class AgentMessageBase(BaseModel):
    """Base agent message schema"""
    content: str = Field(..., description="Message content")
    message_type: str = Field(..., description="Type of message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AgentMessageCreate(AgentMessageBase):
    """Schema for creating agent messages"""
    task_execution_id: UUID
    sender_id: UUID
    recipient_id: Optional[UUID] = Field(default=None, description="None for broadcast messages")


class AgentMessageResponse(AgentMessageBase):
    """Schema for agent message responses"""
    id: UUID
    task_execution_id: UUID
    sender_id: UUID
    recipient_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Structured A2A Protocol Messages

class TaskAssignment(BaseModel):
    """Task assignment message from PM to team member"""
    action: Literal["task_assignment"] = "task_assignment"
    recipient: UUID = Field(..., description="Agent ID to assign task to")
    task_id: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str] = Field(default_factory=list)
    context: str = Field(..., description="Retrieved from RAG or previous discussions")
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    estimated_hours: Optional[float] = None


class StatusRequest(BaseModel):
    """Status check message"""
    action: Literal["status_request"] = "status_request"
    recipient: UUID
    task_id: str


class StatusUpdate(BaseModel):
    """Status update response"""
    action: Literal["status_update"] = "status_update"
    task_id: str
    status: Literal["pending", "in_progress", "blocked", "completed", "failed"]
    progress_percentage: int = Field(..., ge=0, le=100)
    details: str
    blockers: List[str] = Field(default_factory=list)
    next_steps: Optional[str] = None


class Question(BaseModel):
    """Question from one agent to another"""
    action: Literal["question"] = "question"
    recipient: Optional[UUID] = Field(default=None, description="None for broadcast to all")
    task_id: str
    question: str
    context: str
    urgency: Literal["low", "normal", "high"] = "normal"


class Answer(BaseModel):
    """Answer to a question"""
    action: Literal["answer"] = "answer"
    recipient: UUID
    task_id: str
    question_id: str
    answer: str
    confidence: Literal["low", "medium", "high"] = "high"


class HumanInterventionRequired(BaseModel):
    """Escalation message to human"""
    action: Literal["human_intervention_required"] = "human_intervention_required"
    task_id: str
    reason: Literal[
        "ambiguous_requirements",
        "technical_blocker",
        "external_dependency",
        "resource_constraint",
        "decision_required",
        "other"
    ]
    details: str
    attempted_solutions: List[str] = Field(default_factory=list)
    urgency: Literal["low", "normal", "high"] = "high"


class CodeReviewRequest(BaseModel):
    """Code review request"""
    action: Literal["code_review_request"] = "code_review_request"
    recipient: UUID = Field(..., description="Tech lead or reviewer agent")
    task_id: str
    pull_request_url: str
    description: str
    changes_summary: str
    self_review_notes: Optional[str] = None


class CodeReviewResponse(BaseModel):
    """Code review response"""
    action: Literal["code_review_response"] = "code_review_response"
    recipient: UUID
    task_id: str
    pull_request_url: str
    approval_status: Literal["approved", "changes_requested", "commented"]
    comments: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {file, line, comment}"
    )
    summary: str


class TaskCompletion(BaseModel):
    """Task completion notification"""
    action: Literal["task_completion"] = "task_completion"
    recipient: UUID = Field(..., description="PM agent")
    task_id: str
    completion_summary: str
    deliverables: List[str]
    tests_passed: bool
    documentation_updated: bool
    notes: Optional[str] = None


class Standup(BaseModel):
    """Daily standup update"""
    action: Literal["standup"] = "standup"
    recipient: Optional[UUID] = Field(default=None, description="None for broadcast")
    agent_id: UUID
    yesterday: str = Field(..., description="What was accomplished yesterday")
    today: str = Field(..., description="What will be worked on today")
    blockers: List[str] = Field(default_factory=list, description="Any blockers")


# Union type for all structured messages
MessagePayload = (
    TaskAssignment |
    StatusRequest |
    StatusUpdate |
    Question |
    Answer |
    HumanInterventionRequired |
    CodeReviewRequest |
    CodeReviewResponse |
    TaskCompletion |
    Standup
)
