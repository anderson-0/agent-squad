"""
Pydantic Schemas for Analytics (Stream K)
"""
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class PhaseDistribution(BaseModel):
    """Phase distribution metrics"""
    investigation: int
    building: int
    validation: int


class AgentPerformance(BaseModel):
    """Agent performance metrics"""
    agent_id: UUID
    completion_rate: float
    tasks_completed: int
    tasks_total: int


class CoherenceTrend(BaseModel):
    """Coherence trend data point"""
    agent_id: UUID
    coherence_score: float
    calculated_at: datetime
    phase: str


class WorkflowAnalyticsResponse(BaseModel):
    """Response schema for workflow analytics"""
    execution_id: UUID
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="Task completion rate")
    average_task_duration_hours: float = Field(..., description="Average task duration")
    phase_distribution: PhaseDistribution
    branch_count: int = Field(..., ge=0, description="Number of workflow branches")
    discovery_to_value_conversion: float = Field(..., ge=0.0, le=1.0, description="Discovery conversion rate")
    agent_performance: Dict[str, float] = Field(..., description="Performance per agent")
    coherence_trends: List[CoherenceTrend]
    calculated_at: datetime


class WorkflowGraphNode(BaseModel):
    """Node in workflow graph"""
    id: str
    title: str
    phase: str
    status: str
    created_at: str


class WorkflowGraphEdge(BaseModel):
    """Edge in workflow graph"""
    from_node: str = Field(..., alias="from", description="Source node ID")
    to: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Edge type (e.g., 'blocks')")
    
    class Config:
        populate_by_name = True  # Allow using both 'from' and 'from_node'


class WorkflowGraphBranch(BaseModel):
    """Branch in workflow graph"""
    id: str
    name: str
    phase: str
    status: str


class WorkflowGraphResponse(BaseModel):
    """Response schema for workflow graph"""
    nodes: List[WorkflowGraphNode]
    edges: List[WorkflowGraphEdge]
    branches: List[WorkflowGraphBranch]
    phases: List[str]

