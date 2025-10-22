"""
Conversation and ConversationEvent Schemas

Pydantic schemas for conversation tracking with timeout, retry, and escalation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ConversationStateEnum(str, Enum):
    """Conversation state options"""
    INITIATED = "initiated"
    WAITING = "waiting"
    TIMEOUT = "timeout"
    FOLLOW_UP = "follow_up"
    ESCALATING = "escalating"
    ESCALATED = "escalated"
    ANSWERED = "answered"
    CANCELLED = "cancelled"


# Conversation Schemas

class ConversationBase(BaseModel):
    """Base conversation schema"""
    question_type: Optional[str] = Field(None, description="Type of question (implementation, architecture, etc.)")
    task_execution_id: Optional[UUID] = Field(None, description="Related task execution")


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    initial_message_id: UUID = Field(..., description="Message that started this conversation")
    asker_id: UUID = Field(..., description="Agent asking the question")
    current_responder_id: UUID = Field(..., description="Agent expected to respond")
    conv_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    current_state: Optional[ConversationStateEnum] = None
    current_responder_id: Optional[UUID] = None
    escalation_level: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    conv_metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation responses"""
    id: UUID
    initial_message_id: UUID
    current_state: ConversationStateEnum
    asker_id: UUID
    current_responder_id: UUID
    escalation_level: int
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    conv_metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ConversationWithDetails(ConversationResponse):
    """Conversation with related messages and events"""
    initial_message_content: Optional[str] = None
    asker_role: Optional[str] = None
    responder_role: Optional[str] = None
    event_count: Optional[int] = None
    message_count: Optional[int] = None


# Conversation Event Schemas

class ConversationEventBase(BaseModel):
    """Base conversation event schema"""
    event_type: str = Field(..., description="Type of event (acknowledged, timeout, escalated, etc.)")
    to_state: ConversationStateEnum = Field(..., description="New conversation state")
    from_state: Optional[ConversationStateEnum] = Field(None, description="Previous state")
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")


class ConversationEventCreate(ConversationEventBase):
    """Schema for creating a conversation event"""
    conversation_id: UUID
    message_id: Optional[UUID] = Field(None, description="Related message if any")
    triggered_by_agent_id: Optional[UUID] = Field(None, description="Agent who triggered this event")


class ConversationEventResponse(ConversationEventBase):
    """Schema for conversation event responses"""
    id: UUID
    conversation_id: UUID
    message_id: Optional[UUID] = None
    triggered_by_agent_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# API Request/Response Schemas

class InitiateQuestionRequest(BaseModel):
    """Request to initiate a question (creates a conversation)"""
    asker_id: UUID = Field(..., description="Agent asking the question")
    question_content: str = Field(..., description="The question content")
    question_type: str = Field(..., description="Type of question (implementation, architecture, etc.)")
    task_execution_id: Optional[UUID] = Field(None, description="Related task execution")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class InitiateQuestionResponse(BaseModel):
    """Response after initiating a question"""
    conversation_id: UUID
    message_id: UUID
    responder_id: UUID
    responder_role: str
    estimated_timeout: datetime


class SendAcknowledgmentRequest(BaseModel):
    """Request to send acknowledgment for a question"""
    conversation_id: UUID
    responder_id: UUID
    custom_message: Optional[str] = Field(None, description="Custom acknowledgment message (optional)")


class SendAnswerRequest(BaseModel):
    """Request to send an answer to a question"""
    conversation_id: UUID
    responder_id: UUID
    answer_content: str = Field(..., description="The answer to the question")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EscalateConversationRequest(BaseModel):
    """Request to escalate a conversation to the next level"""
    conversation_id: UUID
    reason: str = Field(..., description="Reason for escalation")
    manual: bool = Field(default=False, description="Whether this is manual escalation or auto-timeout")


class CantHelpRequest(BaseModel):
    """Request when an agent can't help and needs to route to an expert"""
    conversation_id: UUID
    current_responder_id: UUID
    reason: str = Field(..., description="Why the agent can't help")
    suggested_expert_role: Optional[str] = Field(None, description="Suggested role to route to")


class ConversationStatsResponse(BaseModel):
    """Statistics about conversations"""
    total_conversations: int
    by_state: Dict[ConversationStateEnum, int]
    by_question_type: Dict[str, int]
    average_resolution_time_seconds: Optional[float] = None
    escalation_rate: float = Field(..., description="Percentage of conversations that escalated")
    timeout_rate: float = Field(..., description="Percentage of conversations that timed out")
    average_escalation_level: float


class ConversationTimelineEvent(BaseModel):
    """Single event in a conversation timeline"""
    timestamp: datetime
    event_type: str
    description: str
    agent_id: Optional[UUID] = None
    agent_role: Optional[str] = None
    message_content: Optional[str] = None


class ConversationTimeline(BaseModel):
    """Full timeline of a conversation"""
    conversation_id: UUID
    asker_id: UUID
    asker_role: str
    question_content: str
    current_state: ConversationStateEnum
    events: List[ConversationTimelineEvent] = Field(default_factory=list)
    created_at: datetime
    resolved_at: Optional[datetime] = None
    total_duration_seconds: Optional[int] = None
