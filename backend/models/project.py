"""
Project and Task Models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, JSON, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """Project model"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    git_repo_url = Column(String, nullable=True)
    git_provider = Column(String, nullable=True)  # github, gitlab, bitbucket
    ticket_system_url = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    squad = relationship("Squad", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_squad_id", "squad_id"),
        Index("ix_projects_squad_id_is_active", "squad_id", "is_active"),
    )


class Task(Base, TimestampMixin):
    """Task model"""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, nullable=True, index=True)  # ID from Jira, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, blocked, completed, failed
    priority = Column(String, nullable=False, default="medium")  # low, medium, high, urgent
    assigned_to = Column(String, nullable=True)
    task_metadata = Column(JSON, nullable=False, server_default="{}")

    # Relationships
    project = relationship("Project", back_populates="tasks")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tasks_project_id", "project_id"),
        Index("ix_tasks_project_id_status", "project_id", "status"),
        Index("ix_tasks_project_id_status_priority", "project_id", "status", "priority"),
        # external_id already has index due to index=True
    )


class TaskExecution(Base, TimestampMixin):
    """Task Execution model"""

    __tablename__ = "task_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, completed, failed, blocked
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    logs = Column(JSON, nullable=False, server_default="[]")
    error_message = Column(Text, nullable=True)
    execution_metadata = Column(JSON, nullable=False, server_default="{}")

    # Relationships
    task = relationship("Task", back_populates="executions")
    squad = relationship("Squad", back_populates="task_executions")
    messages = relationship("AgentMessage", back_populates="task_execution", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="task_execution", uselist=False)
    llm_cost_entries = relationship("LLMCostEntry", back_populates="task_execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_task_executions_task_id", "task_id"),
        Index("ix_task_executions_squad_id", "squad_id"),
        Index("ix_task_executions_squad_id_status", "squad_id", "status"),
        Index("ix_task_executions_status_created_at", "status", "created_at"),
    )
