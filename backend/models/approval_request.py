from sqlalchemy import Column, String, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from backend.models.base import Base

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("squad_members.id"), nullable=False)
    action_type = Column(String, nullable=False)  # e.g., "deploy", "delete_resource"
    payload = Column(JSON, nullable=True)  # Details of the action
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
