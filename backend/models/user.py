"""
User and Organization Models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=True, index=True)
    plan_tier = Column(String, nullable=False, default="starter")  # starter, pro, enterprise
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)

    # Relationships
    organizations = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")
    squads = relationship("Squad", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    multi_turn_conversations = relationship("MultiTurnConversation", back_populates="user", cascade="all, delete-orphan")


class Organization(Base, TimestampMixin):
    """Organization model"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="organizations")
    squads = relationship("Squad", back_populates="organization")

    __table_args__ = (Index("ix_organizations_owner_id", "owner_id"),)
