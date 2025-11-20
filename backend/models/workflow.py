"""
Workflow Models for Phase-Based Dynamic Tasks

These models support the Hephaestus-style phase-based workflow system
where agents can spawn tasks dynamically in any phase.
"""
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    Index,
    Boolean,
    CheckConstraint,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class WorkflowPhase(str, Enum):
    """
    Workflow phases - agents can spawn tasks in any phase.
    
    This enables the Hephaestus-style semi-structured workflows where
    workflows build themselves as agents discover what needs to be done.
    """
    INVESTIGATION = "investigation"  # Phase 1: Explore, analyze, discover
    BUILDING = "building"            # Phase 2: Implement, build, create
    VALIDATION = "validation"         # Phase 3: Test, verify, validate


class DynamicTask(Base, TimestampMixin):
    """
    Tasks spawned dynamically by agents during workflow execution.
    
    Unlike traditional tasks (from Task model), these are created
    by agents themselves as they discover opportunities or issues.
    """
    __tablename__ = "dynamic_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("task_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent task execution this task belongs to"
    )
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Workflow branch this task belongs to (if any)"
    )
    phase = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Phase: investigation, building, or validation"
    )
    spawned_by_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="Agent that spawned this task"
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="pending, in_progress, completed, failed"
    )
    
    # Optional rationale for why this task was spawned (especially for investigation)
    rationale = Column(Text, nullable=True, comment="Why this task was created")
    
    # Relationships
    parent_execution = relationship(
        "TaskExecution",
        foreign_keys=[parent_execution_id]
    )
    spawned_by_agent = relationship(
        "SquadMember",
        foreign_keys=[spawned_by_agent_id]
    )
    branch = relationship(
        "WorkflowBranch",
        foreign_keys=[branch_id]
    )
    
    # Many-to-many relationship for task dependencies (blocking relationships)
    blocks_tasks = relationship(
        "DynamicTask",
        secondary="task_dependencies",
        primaryjoin="DynamicTask.id == task_dependencies.c.task_id",
        secondaryjoin="DynamicTask.id == task_dependencies.c.blocks_task_id",
        backref="blocked_by_tasks",
        lazy="dynamic"
    )

    __table_args__ = (
        Index("ix_dynamic_tasks_execution_phase", "parent_execution_id", "phase"),
        Index("ix_dynamic_tasks_execution_status", "parent_execution_id", "status"),
        Index("ix_dynamic_tasks_phase_status", "phase", "status"),
        # Composite index for common query: execution + phase + status (optimizes filtered lists)
        Index(
            "ix_dynamic_tasks_execution_phase_status",
            "parent_execution_id",
            "phase",
            "status"
        ),
        CheckConstraint(
            "phase IN ('investigation', 'building', 'validation')",
            name="ck_dynamic_tasks_valid_phase"
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed', 'blocked')",
            name="ck_dynamic_tasks_valid_status"
        ),
    )

    def __repr__(self):
        return f"<DynamicTask(id={self.id}, phase={self.phase}, title={self.title[:50]}, status={self.status})>"


# Association table for task dependencies (blocking relationships)
task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column(
        "task_id",
        UUID(as_uuid=True),
        ForeignKey("dynamic_tasks.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Task that blocks other tasks"
    ),
    Column(
        "blocks_task_id",
        UUID(as_uuid=True),
        ForeignKey("dynamic_tasks.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Task that is blocked"
    ),
    CheckConstraint(
        "task_id != blocks_task_id",
        name="ck_no_self_dependency"
    ),
    Index("ix_task_dependencies_task_id", "task_id"),
    Index("ix_task_dependencies_blocks_task_id", "blocks_task_id"),
)

