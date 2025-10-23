"""
Squad and Squad Member Models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class Squad(Base, TimestampMixin):
    """Squad model"""

    __tablename__ = "squads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active, paused, archived
    config = Column(JSON, nullable=False, server_default="{}")

    # Relationships
    organization = relationship("Organization", back_populates="squads")
    user = relationship("User", back_populates="squads")
    members = relationship("SquadMember", back_populates="squad", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="squad", cascade="all, delete-orphan")
    task_executions = relationship("TaskExecution", back_populates="squad", cascade="all, delete-orphan")
    learning_insights = relationship("LearningInsight", back_populates="squad", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_squads_user_id", "user_id"),
        Index("ix_squads_org_id", "org_id"),
        Index("ix_squads_user_id_status", "user_id", "status"),
    )


class SquadMember(Base, TimestampMixin):
    """Squad Member (Agent) model"""

    __tablename__ = "squad_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # project_manager, backend_developer, etc.
    specialization = Column(String, nullable=True)  # nodejs_express, python_fastapi, etc.
    llm_provider = Column(String, nullable=False, default="openai")
    llm_model = Column(String, nullable=False, default="gpt-4")
    system_prompt = Column(Text, nullable=False)
    config = Column(JSON, nullable=False, server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    squad = relationship("Squad", back_populates="members")
    sent_messages = relationship(
        "AgentMessage",
        foreign_keys="AgentMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_messages = relationship(
        "AgentMessage",
        foreign_keys="AgentMessage.recipient_id",
        back_populates="recipient"
    )
    multi_turn_conversations = relationship(
        "MultiTurnConversation",
        back_populates="primary_responder",
        foreign_keys="MultiTurnConversation.primary_responder_id"
    )

    __table_args__ = (
        Index("ix_squad_members_squad_id", "squad_id"),
        Index("ix_squad_members_squad_id_role", "squad_id", "role"),
    )
