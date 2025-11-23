"""
Sandbox Model
"""
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from .base import Base, TimestampMixin

class SandboxStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    TERMINATED = "terminated"
    ERROR = "error"

class Sandbox(Base, TimestampMixin):
    __tablename__ = "sandboxes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    e2b_id = Column(String, nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), nullable=True)  # Can be linked to an agent
    task_id = Column(UUID(as_uuid=True), nullable=True)   # Can be linked to a task
    repo_url = Column(String, nullable=True)
    pr_number = Column(Integer, nullable=True, index=True)  # GitHub PR number for webhook lookup
    status = Column(SAEnum(SandboxStatus), default=SandboxStatus.CREATED, nullable=False)
    last_used_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Sandbox {self.id} (e2b_id={self.e2b_id})>"
