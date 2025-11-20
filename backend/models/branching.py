"""
Workflow Branching Models (Stream E)

Models for discovery-driven workflow branching where agents create
parallel investigation/optimization tracks based on discoveries.
"""
from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class WorkflowBranch(Base, TimestampMixin):
    """
    Represents a workflow branch spawned from a discovery.
    
    Branches allow workflows to diverge into parallel tracks when
    agents discover opportunities or issues that need investigation.
    """
    __tablename__ = "workflow_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("task_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent task execution this branch belongs to"
    )
    branch_name = Column(
        String(255),
        nullable=False,
        comment="Human-readable branch name"
    )
    branch_phase = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Phase this branch focuses on (investigation, building, validation)"
    )
    discovery_origin_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the discovery that triggered this branch (if any)"
    )
    discovery_origin_type = Column(
        String(50),
        nullable=True,
        comment="Type of discovery (optimization, bug, refactoring, etc.)"
    )
    discovery_description = Column(
        Text,
        nullable=True,
        comment="Description of the discovery that created this branch"
    )
    
    # Branch metadata
    branch_metadata = Column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Additional metadata about the branch"
    )
    
    # Branch status
    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="active, merged, abandoned, completed"
    )
    
    # Relationships
    parent_execution = relationship(
        "TaskExecution",
        foreign_keys=[parent_execution_id]
    )
    
    # Tasks in this branch (via dynamic_tasks.branch_id - will add this)
    
    __table_args__ = (
        Index("ix_workflow_branches_execution", "parent_execution_id"),
        Index("ix_workflow_branches_execution_status", "parent_execution_id", "status"),
        Index("ix_workflow_branches_phase", "branch_phase"),
        CheckConstraint(
            "branch_phase IN ('investigation', 'building', 'validation')",
            name="ck_workflow_branches_valid_phase"
        ),
        CheckConstraint(
            "status IN ('active', 'merged', 'abandoned', 'completed')",
            name="ck_workflow_branches_valid_status"
        ),
    )

    def __repr__(self):
        return f"<WorkflowBranch(id={self.id}, name={self.branch_name}, phase={self.branch_phase}, status={self.status})>"

