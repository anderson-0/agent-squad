"""
LLM Cost Tracking Models

Tracks token usage and costs for all LLM API calls across providers.
Enables cost analysis, budgeting, and optimization.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from backend.models.base import Base, TimestampMixin


class LLMProvider(str, enum.Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"


class LLMCostEntry(Base, TimestampMixin):
    """
    Individual LLM API call cost tracking.

    Tracks every LLM API call with token usage and costs.
    Supports cost analysis, budgeting, and optimization.
    """
    __tablename__ = "llm_cost_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What was called
    provider = Column(String, nullable=False, index=True)  # LLMProvider enum values stored as strings
    model = Column(String, nullable=False, index=True)

    # Who called it
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Squad member ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Context
    task_execution_id = Column(UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Token usage
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    # Cost (in USD)
    prompt_cost_usd = Column(Float, nullable=False, default=0.0)
    completion_cost_usd = Column(Float, nullable=False, default=0.0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)

    # Pricing at time of call (per 1M tokens)
    prompt_price_per_1m = Column(Float, nullable=True)  # USD per 1M input tokens
    completion_price_per_1m = Column(Float, nullable=True)  # USD per 1M output tokens

    # Request details
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)

    # Response metadata
    finish_reason = Column(String, nullable=True)  # stop, length, content_filter, etc.
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata = Column(JSON, nullable=True)  # Any additional tracking data

    # Timestamp (from TimestampMixin)
    # created_at, updated_at automatically added

    # Indexes for common queries
    __table_args__ = (
        Index('idx_llm_cost_provider_model', 'provider', 'model'),
        Index('idx_llm_cost_squad_created', 'squad_id', 'created_at'),
        Index('idx_llm_cost_org_created', 'organization_id', 'created_at'),
        Index('idx_llm_cost_execution', 'task_execution_id'),
        Index('idx_llm_cost_created_at', 'created_at'),
    )

    # Relationships
    squad = relationship("Squad", back_populates="llm_cost_entries")
    user = relationship("User", back_populates="llm_cost_entries")
    organization = relationship("Organization", back_populates="llm_cost_entries")
    task_execution = relationship("TaskExecution", back_populates="llm_cost_entries")

    def __repr__(self):
        return (
            f"<LLMCostEntry("
            f"id={self.id}, "
            f"provider={self.provider}, "
            f"model={self.model}, "
            f"tokens={self.total_tokens}, "
            f"cost=${self.total_cost_usd:.6f})>"
        )


class LLMCostSummary(Base):
    """
    Aggregated cost summary for fast dashboard queries.

    Periodically updated materialized view of cost aggregations.
    Speeds up dashboard queries by pre-calculating common aggregations.
    """
    __tablename__ = "llm_cost_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What this summary is for
    summary_type = Column(String, nullable=False, index=True)  # daily, weekly, monthly
    summary_date = Column(DateTime, nullable=False, index=True)  # Date this summary represents

    # Who
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="CASCADE"), nullable=True, index=True)

    # Provider breakdown
    provider = Column(String, nullable=True, index=True)  # LLMProvider enum values stored as strings
    model = Column(String, nullable=True)

    # Aggregated metrics
    total_requests = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)

    # Average metrics
    avg_tokens_per_request = Column(Float, nullable=True)
    avg_cost_per_request = Column(Float, nullable=True)
    avg_response_time_ms = Column(Float, nullable=True)

    # Updated timestamp
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_summary_type_date', 'summary_type', 'summary_date'),
        Index('idx_summary_org_date', 'organization_id', 'summary_date'),
        Index('idx_summary_squad_date', 'squad_id', 'summary_date'),
        Index('idx_summary_provider', 'provider', 'summary_date'),
    )

    # Relationships
    organization = relationship("Organization")
    squad = relationship("Squad")

    def __repr__(self):
        return (
            f"<LLMCostSummary("
            f"type={self.summary_type}, "
            f"date={self.summary_date}, "
            f"requests={self.total_requests}, "
            f"cost=${self.total_cost_usd:.2f})>"
        )


# Pricing constants (per 1M tokens in USD)
# Updated as of November 2025
LLM_PRICING = {
    "openai": {
        "gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"prompt": 3.00, "completion": 15.00},
        "claude-3-5-sonnet-20240620": {"prompt": 3.00, "completion": 15.00},
        "claude-3-opus-20240229": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet-20240229": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
    },
    "groq": {
        # Groq pricing (free tier, then paid)
        "llama-3.1-405b-reasoning": {"prompt": 0.00, "completion": 0.00},  # Free tier
        "llama-3.1-70b-versatile": {"prompt": 0.00, "completion": 0.00},  # Free tier
        "llama-3.1-8b-instant": {"prompt": 0.00, "completion": 0.00},  # Free tier
        "mixtral-8x7b-32768": {"prompt": 0.00, "completion": 0.00},  # Free tier
    },
    "ollama": {
        # All Ollama models are free (local)
        "default": {"prompt": 0.00, "completion": 0.00},
    },
}


def get_model_pricing(provider: str, model: str) -> dict:
    """
    Get pricing for a specific model.

    Args:
        provider: LLM provider (openai, anthropic, groq, ollama)
        model: Model name

    Returns:
        Dict with 'prompt' and 'completion' pricing per 1M tokens

    Example:
        >>> get_model_pricing("openai", "gpt-4o-mini")
        {'prompt': 0.15, 'completion': 0.60}
    """
    provider = provider.lower()

    # Ollama is always free
    if provider == "ollama":
        return {"prompt": 0.00, "completion": 0.00}

    # Get provider pricing
    provider_pricing = LLM_PRICING.get(provider, {})

    # Try exact match
    if model in provider_pricing:
        return provider_pricing[model]

    # Try partial match (for model variants)
    for model_key, pricing in provider_pricing.items():
        if model.startswith(model_key) or model_key in model:
            return pricing

    # Return default pricing if not found
    default_pricing = {"prompt": 1.00, "completion": 3.00}  # Conservative default
    return default_pricing


def calculate_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> dict:
    """
    Calculate cost for an LLM API call.

    Args:
        provider: LLM provider
        model: Model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Dict with cost breakdown:
        {
            'prompt_cost_usd': float,
            'completion_cost_usd': float,
            'total_cost_usd': float,
            'prompt_price_per_1m': float,
            'completion_price_per_1m': float,
        }

    Example:
        >>> calculate_cost("openai", "gpt-4o-mini", 1000, 500)
        {
            'prompt_cost_usd': 0.00015,
            'completion_cost_usd': 0.0003,
            'total_cost_usd': 0.00045,
            'prompt_price_per_1m': 0.15,
            'completion_price_per_1m': 0.60
        }
    """
    pricing = get_model_pricing(provider, model)

    # Calculate costs (pricing is per 1M tokens)
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    total_cost = prompt_cost + completion_cost

    return {
        "prompt_cost_usd": round(prompt_cost, 8),
        "completion_cost_usd": round(completion_cost, 8),
        "total_cost_usd": round(total_cost, 8),
        "prompt_price_per_1m": pricing["prompt"],
        "completion_price_per_1m": pricing["completion"],
    }
