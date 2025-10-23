"""
Squad Member Statistics Model

Tracks usage statistics for each squad member:
- Token consumption (input/output)
- Message counts
- Last activity timestamps
"""
from sqlalchemy import Column, ForeignKey, Index, Integer, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func

from backend.models.base import Base


class SquadMemberStats(Base):
    """
    Tracks aggregated statistics for a squad member.

    This model stores:
    - Token usage (input/output tokens consumed by LLM calls)
    - Message counts (total messages sent)
    - Activity timestamps (last message, last updated)
    """

    __tablename__ = "squad_member_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to squad member
    squad_member_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One stats record per squad member
    )

    # Token usage tracking
    total_input_tokens = Column(BigInteger, nullable=False, default=0)
    total_output_tokens = Column(BigInteger, nullable=False, default=0)
    total_tokens = Column(BigInteger, nullable=False, default=0)

    # Message tracking
    total_messages_sent = Column(Integer, nullable=False, default=0)
    total_messages_received = Column(Integer, nullable=False, default=0)

    # Activity tracking
    last_message_sent_at = Column(DateTime, nullable=True)
    last_message_received_at = Column(DateTime, nullable=True)
    last_llm_call_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    squad_member = relationship("SquadMember", backref="stats")

    __table_args__ = (
        Index("ix_squad_member_stats_squad_member_id", "squad_member_id"),
        Index("ix_squad_member_stats_total_tokens", "total_tokens"),
        Index("ix_squad_member_stats_updated_at", "updated_at"),
    )

    def __repr__(self):
        return (
            f"<SquadMemberStats(squad_member_id={self.squad_member_id}, "
            f"tokens={self.total_tokens}, messages={self.total_messages_sent})>"
        )
