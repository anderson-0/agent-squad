"""
Feedback and Learning Models
"""
from sqlalchemy import Column, String, ForeignKey, Index, Text, JSON, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func

from backend.models.base import Base


class Feedback(Base):
    """User Feedback model"""

    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_execution_id = Column(
        UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comments = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    task_execution = relationship("TaskExecution", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

    __table_args__ = (
        Index("ix_feedback_user_id", "user_id"),
        Index("ix_feedback_rating", "rating"),
    )


class LearningInsight(Base):
    """Learning Insight model for RAG"""

    __tablename__ = "learning_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="CASCADE"), nullable=False)
    insight_text = Column(Text, nullable=False)
    vector_id = Column(String, nullable=True)  # Reference to Pinecone vector
    source_feedback_id = Column(String, nullable=True)
    category = Column(String, nullable=True)  # success, failure, improvement
    insight_metadata = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    squad = relationship("Squad", back_populates="learning_insights")

    __table_args__ = (
        Index("ix_learning_insights_squad_id", "squad_id"),
        Index("ix_learning_insights_category", "category"),
    )
