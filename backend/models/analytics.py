from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from backend.models.base import Base

class SquadMetrics(Base):
    """
    Squad Metrics Model
    
    Stores aggregated hourly metrics for squads.
    Calculated by background Inngest jobs.
    """
    __tablename__ = "squad_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False, index=True)
    
    # Time period
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    period_type = Column(String, default="hourly") # hourly, daily
    
    # Aggregated Metrics
    total_questions = Column(Integer, default=0)
    total_resolved = Column(Integer, default=0)
    total_escalated = Column(Integer, default=0)
    total_timeouts = Column(Integer, default=0)
    
    avg_resolution_time_seconds = Column(Float, default=0.0)
    avg_escalation_depth = Column(Float, default=0.0)
    
    # Cost Metrics
    total_cost = Column(Float, default=0.0)
    
    # JSON Breakdowns
    questions_by_type = Column(JSON, default=dict) # {"implementation": 10, "architecture": 5}
    agent_performance = Column(JSON, default=dict) # {"agent_id": {"answered": 5, "avg_time": 120}}
    
    created_at = Column(DateTime, default=datetime.utcnow)
