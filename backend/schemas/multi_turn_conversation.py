"""
Multi-Turn Conversation Schemas

Pydantic schemas for universal multi-turn conversations (user-agent, agent-agent, multi-party).
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ConversationType(str, Enum):
    """Conversation type options"""
    USER_AGENT = "user_agent"
    AGENT_AGENT = "agent_agent"
    MULTI_PARTY = "multi_party"


class ParticipantType(str, Enum):
    """Participant type options"""
    USER = "user"
    AGENT = "agent"


class ConversationStatus(str, Enum):
    """Conversation status options"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"


class MessageRole(str, Enum):
    """Message role options (for LLM context)"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ParticipantRole(str, Enum):
    """Participant role options"""
    INITIATOR = "initiator"
    RESPONDER = "responder"
    OBSERVER = "observer"
    MODERATOR = "moderator"


# ============================================================================
# CONVERSATION SCHEMAS
# ============================================================================

class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    tags: Optional[List[str]] = Field(default_factory=list, description="Conversation tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class CreateUserAgentConversationRequest(ConversationBase):
    """Request to create a user-agent conversation"""
    agent_id: UUID = Field(..., description="UUID of the agent (squad member)")


class CreateAgentAgentConversationRequest(ConversationBase):
    """Request to create an agent-agent conversation"""
    initiator_agent_id: UUID = Field(..., description="UUID of the initiating agent")
    responder_agent_id: UUID = Field(..., description="UUID of the responding agent")
    agent_conversation_id: Optional[UUID] = Field(None, description="Optional link to hierarchical routing conversation")


class ConversationResponse(BaseModel):
    """Response schema for conversation"""
    id: UUID
    conversation_type: ConversationType
    initiator_id: UUID
    initiator_type: ParticipantType
    primary_responder_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    agent_conversation_id: Optional[UUID] = None
    title: Optional[str] = None
    status: ConversationStatus
    total_messages: int
    total_tokens_used: int
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ConversationWithMessagesResponse(ConversationResponse):
    """Conversation with messages included"""
    messages: List["MessageResponse"] = Field(default_factory=list)
    participant_count: int = 0


class ConversationListResponse(BaseModel):
    """Response for list of conversations"""
    conversations: List[ConversationResponse]
    total_count: int
    limit: int
    offset: int


# ============================================================================
# MESSAGE SCHEMAS
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation"""
    content: str = Field(..., min_length=1, description="Message content")
    role: Optional[MessageRole] = Field(MessageRole.USER, description="Message role for LLM context")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MessageResponse(BaseModel):
    """Response schema for message"""
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_type: ParticipantType
    role: MessageRole
    content: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_used: Optional[str] = None
    temperature: Optional[float] = None
    llm_provider: Optional[str] = None
    created_at: datetime
    response_time_ms: Optional[int] = None
    agent_message_id: Optional[UUID] = None
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response for list of messages"""
    messages: List[MessageResponse]
    total_count: int
    limit: int
    offset: int


class ConversationHistoryResponse(BaseModel):
    """Response for conversation history with context"""
    conversation_id: UUID
    messages: List[MessageResponse]
    total_messages: int
    total_tokens: int
    context_window_tokens: Optional[int] = None


# ============================================================================
# PARTICIPANT SCHEMAS
# ============================================================================

class AddParticipantRequest(BaseModel):
    """Request to add a participant to a conversation"""
    participant_id: UUID = Field(..., description="UUID of the participant")
    participant_type: ParticipantType = Field(..., description="Type of participant")
    role: ParticipantRole = Field(ParticipantRole.OBSERVER, description="Participant role")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ParticipantResponse(BaseModel):
    """Response schema for participant"""
    id: UUID
    conversation_id: UUID
    participant_id: UUID
    participant_type: ParticipantType
    role: ParticipantRole
    is_active: bool
    joined_at: datetime
    left_at: Optional[datetime] = None
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ParticipantListResponse(BaseModel):
    """Response for list of participants"""
    participants: List[ParticipantResponse]
    total_count: int


# ============================================================================
# UPDATE SCHEMAS
# ============================================================================

class UpdateConversationTitleRequest(BaseModel):
    """Request to update conversation title"""
    title: str = Field(..., min_length=1, max_length=255, description="New conversation title")


class UpdateConversationSummaryRequest(BaseModel):
    """Request to update conversation summary"""
    summary: str = Field(..., min_length=1, description="Conversation summary")


class UpdateConversationTagsRequest(BaseModel):
    """Request to update conversation tags"""
    tags: List[str] = Field(..., description="List of tags")


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ConversationStatsResponse(BaseModel):
    """Statistics about conversations"""
    total_conversations: int
    by_type: Dict[ConversationType, int]
    by_status: Dict[ConversationStatus, int]
    total_messages: int
    total_tokens_used: int
    average_messages_per_conversation: float
    average_tokens_per_conversation: float
    active_conversations: int
    archived_conversations: int
    closed_conversations: int


class UserConversationStatsResponse(BaseModel):
    """Statistics about a user's conversations"""
    user_id: UUID
    total_conversations: int
    active_conversations: int
    total_messages_sent: int
    total_messages_received: int
    total_tokens_used: int
    average_conversation_length: float
    most_contacted_agents: List[Dict[str, Any]] = Field(default_factory=list)


class AgentConversationStatsResponse(BaseModel):
    """Statistics about an agent's conversations"""
    agent_id: UUID
    total_conversations: int
    user_agent_conversations: int
    agent_agent_conversations: int
    total_messages_sent: int
    total_messages_received: int
    total_tokens_used: int
    average_response_time_ms: Optional[float] = None
    most_contacted_users: List[Dict[str, Any]] = Field(default_factory=list)


# Forward reference resolution for nested models
ConversationWithMessagesResponse.model_rebuild()
