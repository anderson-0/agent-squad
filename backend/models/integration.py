"""
Integration and Webhook Models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class Integration(Base, TimestampMixin):
    """Integration model (Git, Jira, Slack, etc.)"""

    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # git, jira, slack, etc.
    provider = Column(String, nullable=True)  # github, gitlab, bitbucket (for git type)
    credentials = Column(Text, nullable=False)  # Encrypted JSON
    config = Column(JSON, nullable=False, server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    project = relationship("Project", back_populates="integrations")
    webhooks = relationship("Webhook", back_populates="integration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_integrations_project_id", "project_id"),
        Index("ix_integrations_project_id_type", "project_id", "type"),
    )


class Webhook(Base, TimestampMixin):
    """Webhook model"""

    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_triggered = Column(DateTime, nullable=True)

    # Relationships
    integration = relationship("Integration", back_populates="webhooks")

    __table_args__ = (Index("ix_webhooks_integration_id", "integration_id"),)
