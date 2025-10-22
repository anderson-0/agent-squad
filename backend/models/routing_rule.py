"""
Routing Rule Model

Stores customizable agent routing hierarchies per squad.
Allows users to define which agents should be asked for help based on question type.
"""
from sqlalchemy import Column, String, ForeignKey, Index, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class RoutingRule(Base, TimestampMixin):
    """
    Defines routing hierarchy for agent questions.

    Users can customize which agents to ask for specific question types.
    This allows flexible team structures and escalation paths.

    Example:
        Squad X's backend developers should ask:
        - Tech Lead (level 0) for implementation questions
        - Solution Architect (level 1) for architecture questions
        - Project Manager (level 2) as final escalation
    """

    __tablename__ = "routing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Scope: squad-level or org-level routing rules
    squad_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squads.id", ondelete="CASCADE"),
        nullable=True
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )

    # Rule definition
    asker_role = Column(String(100), nullable=False)  # e.g., 'backend_developer'
    question_type = Column(String(100), nullable=False)  # e.g., 'implementation', 'architecture', 'default'

    # Escalation chain (ordered by escalation_level)
    # Multiple rules can have same asker_role + question_type but different escalation_level
    escalation_level = Column(Integer, nullable=False, default=0)  # 0 = first contact, 1 = escalate once, etc.
    responder_role = Column(String(100), nullable=False)  # e.g., 'tech_lead'

    # Optional: target specific agent instead of role
    specific_responder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="CASCADE"),
        nullable=True
    )  # If set, route to this specific agent instead of any agent with the role

    # Rule configuration
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=0)  # For conflict resolution (higher = higher priority)

    # Additional metadata (e.g., conditions, tags, etc.)
    # Using rule_metadata instead of metadata which is reserved by SQLAlchemy
    rule_metadata = Column(JSON, nullable=False, server_default="{}")

    # Relationships
    squad = relationship("Squad", backref="routing_rules")
    organization = relationship("Organization", backref="routing_rules")
    specific_responder = relationship("SquadMember", backref="targeted_routing_rules")

    __table_args__ = (
        # Ensure we can quickly lookup rules for a given asker and question type
        Index("ix_routing_rules_squad_asker_question", "squad_id", "asker_role", "question_type"),
        Index("ix_routing_rules_org_asker_question", "organization_id", "asker_role", "question_type"),
        Index("ix_routing_rules_escalation", "escalation_level"),
        Index("ix_routing_rules_active", "is_active"),
    )

    def __repr__(self):
        return (
            f"<RoutingRule(asker={self.asker_role}, question={self.question_type}, "
            f"level={self.escalation_level}, responder={self.responder_role})>"
        )


class DefaultRoutingTemplate(Base, TimestampMixin):
    """
    Default routing templates that can be applied to new squads.

    Provides pre-configured routing hierarchies for common team structures.

    Examples:
        - "Standard Software Team" template
        - "DevOps Team" template
        - "AI/ML Team" template
    """

    __tablename__ = "default_routing_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(200), nullable=False)  # e.g., "Standard Software Team"
    description = Column(String(500), nullable=True)
    template_type = Column(String(100), nullable=False)  # e.g., "software", "devops", "ml"

    # The routing rules as JSON (can be applied when creating a squad)
    routing_rules_template = Column(JSON, nullable=False)  # Array of rule definitions

    # Metadata
    is_public = Column(Boolean, nullable=False, default=True)  # Can be used by all orgs
    is_default = Column(Boolean, nullable=False, default=False)  # Default for new squads

    created_by_org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )  # If custom template created by an org

    __table_args__ = (
        Index("ix_routing_templates_type", "template_type"),
        Index("ix_routing_templates_public", "is_public"),
        Index("ix_routing_templates_default", "is_default"),
    )

    def __repr__(self):
        return f"<DefaultRoutingTemplate(name={self.name}, type={self.template_type})>"
