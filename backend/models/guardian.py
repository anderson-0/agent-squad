"""
Guardian Models for PM-as-Guardian System (Stream C)

Models for tracking coherence metrics and workflow health monitoring.
"""
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class CoherenceMetrics(Base, TimestampMixin):
    """
    Stores coherence scores calculated by PM Guardian.
    
    Coherence = How well agent's work aligns with phase goals and workflow objectives.
    """
    __tablename__ = "coherence_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("task_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task execution being monitored"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent being monitored"
    )
    monitored_by_pm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="PM agent that calculated this metric"
    )
    phase = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Phase: investigation, building, or validation"
    )
    coherence_score = Column(
        Float,
        nullable=False,
        comment="Overall coherence score (0.0-1.0)"
    )
    metrics = Column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Detailed breakdown: phase_alignment, goal_alignment, quality_alignment, task_relevance"
    )
    anomaly_detected = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether an anomaly was detected"
    )
    pm_action_taken = Column(
        String(255),
        nullable=True,
        comment="What PM did to correct (if any): 'logged', 'escalated', 'redirected', etc."
    )
    calculated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
        comment="When coherence was calculated"
    )

    # Relationships
    execution = relationship(
        "TaskExecution",
        foreign_keys=[execution_id]
    )
    agent = relationship(
        "SquadMember",
        foreign_keys=[agent_id]
    )
    monitored_by_pm = relationship(
        "SquadMember",
        foreign_keys=[monitored_by_pm_id]
    )

    __table_args__ = (
        Index("ix_coherence_metrics_execution_agent", "execution_id", "agent_id"),
        Index("ix_coherence_metrics_execution_phase", "execution_id", "phase"),
        Index("ix_coherence_metrics_agent_phase", "agent_id", "phase"),
        Index("ix_coherence_metrics_anomaly", "anomaly_detected", "calculated_at"),
        Index("ix_coherence_metrics_pm_action", "pm_action_taken"),
        # Composite index for common queries
        Index(
            "ix_coherence_metrics_execution_agent_phase",
            "execution_id",
            "agent_id",
            "phase"
        ),
    )

    def __repr__(self):
        return (
            f"<CoherenceMetrics(id={self.id}, agent={self.agent_id}, "
            f"score={self.coherence_score:.2f}, phase={self.phase})>"
        )

