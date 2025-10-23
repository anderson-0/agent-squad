"""
Squad Template Model

Complete squad templates including agents, routing rules, system prompts, and examples.
"""
from sqlalchemy import Column, String, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from backend.models.base import Base, TimestampMixin


class SquadTemplate(Base, TimestampMixin):
    """
    Complete squad template with all configuration needed to spin up a squad

    Includes:
    - Agent definitions (roles, LLM configs)
    - Routing rules (escalation hierarchy)
    - System prompts
    - Example conversations
    - Success metrics
    """

    __tablename__ = "squad_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # "Software Development Squad"
    slug = Column(String, nullable=False, unique=True, index=True)  # "software-dev-squad"
    description = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)  # "development", "support", etc.
    is_active = Column(Boolean, nullable=False, default=True)
    is_featured = Column(Boolean, nullable=False, default=False)

    # Complete template definition (JSON)
    # Contains: agents, routing_rules, success_metrics, example_conversations, use_cases, tags
    template_definition = Column(JSON, nullable=False)

    # Usage statistics
    usage_count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=True)

    def __repr__(self):
        return f"<SquadTemplate {self.name} ({self.slug})>"
