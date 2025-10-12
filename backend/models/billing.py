"""
Billing and Usage Tracking Models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, JSON, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from backend.models.base import Base, TimestampMixin


class Subscription(Base, TimestampMixin):
    """Subscription model"""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=False, index=True)
    stripe_price_id = Column(String, nullable=False)
    plan_tier = Column(String, nullable=False)  # starter, pro, enterprise
    status = Column(String, nullable=False)  # active, canceled, past_due, etc.
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_stripe_subscription_id", "stripe_subscription_id"),
    )


class UsageMetrics(Base):
    """Usage Metrics model"""

    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), nullable=False)
    metric_type = Column(String, nullable=False)  # task_executions, llm_calls, tokens_used
    value = Column(Float, nullable=False)
    cost = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=False, server_default="{}")
    recorded_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_usage_metrics_squad_id", "squad_id"),
        Index("ix_usage_metrics_squad_id_metric_type", "squad_id", "metric_type"),
        Index("ix_usage_metrics_recorded_at", "recorded_at"),
    )
