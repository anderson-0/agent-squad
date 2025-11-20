"""
Analytics Service (Stream K)

Calculates comprehensive analytics for workflows, agents, and tasks.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.models.workflow import DynamicTask, WorkflowPhase
from backend.models.project import TaskExecution
from backend.models.branching import WorkflowBranch
from backend.models.guardian import CoherenceMetrics
from backend.models.message import AgentMessage
from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.agents.guardian import get_workflow_health_monitor
from backend.core.logging import logger


class WorkflowAnalytics:
    """Comprehensive workflow analytics"""
    
    def __init__(
        self,
        execution_id: UUID,
        completion_rate: float,
        average_task_duration_hours: float,
        phase_distribution: Dict[str, int],
        branch_count: int,
        discovery_to_value_conversion: float,
        agent_performance: Dict[str, float],
        coherence_trends: List[Dict[str, Any]],
        calculated_at: datetime,
    ):
        self.execution_id = execution_id
        self.completion_rate = completion_rate
        self.average_task_duration_hours = average_task_duration_hours
        self.phase_distribution = phase_distribution
        self.branch_count = branch_count
        self.discovery_to_value_conversion = discovery_to_value_conversion
        self.agent_performance = agent_performance
        self.coherence_trends = coherence_trends
        self.calculated_at = calculated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "execution_id": str(self.execution_id),
            "completion_rate": self.completion_rate,
            "average_task_duration_hours": self.average_task_duration_hours,
            "phase_distribution": self.phase_distribution,
            "branch_count": self.branch_count,
            "discovery_to_value_conversion": self.discovery_to_value_conversion,
            "agent_performance": {str(k): v for k, v in self.agent_performance.items()},
            "coherence_trends": self.coherence_trends,
            "calculated_at": self.calculated_at.isoformat(),
        }


class AnalyticsService:
    """
    Service for calculating workflow analytics.
    
    Provides:
    - Workflow completion metrics
    - Phase efficiency metrics
    - Branch success rates
    - Agent performance by phase
    - Coherence trends
    - Discovery-to-value conversion
    """
    
    def __init__(self):
        """Initialize analytics service"""
        self.workflow_engine = PhaseBasedWorkflowEngine()
    
    async def calculate_workflow_analytics(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> WorkflowAnalytics:
        """
        Calculate comprehensive analytics for a workflow.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            
        Returns:
            WorkflowAnalytics with all metrics
        """
        # Get execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")
        
        # Get all tasks
        all_tasks = await self.workflow_engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        # Calculate completion rate
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        completion_rate = len(completed_tasks) / len(all_tasks) if all_tasks else 0.0
        
        # Calculate average task duration (simple heuristic)
        # In production, would use actual start/end times
        avg_duration = 4.0  # Default 4 hours
        
        # Phase distribution
        phase_distribution = {
            WorkflowPhase.INVESTIGATION.value: len([t for t in all_tasks if t.phase == WorkflowPhase.INVESTIGATION.value]),
            WorkflowPhase.BUILDING.value: len([t for t in all_tasks if t.phase == WorkflowPhase.BUILDING.value]),
            WorkflowPhase.VALIDATION.value: len([t for t in all_tasks if t.phase == WorkflowPhase.VALIDATION.value]),
        }
        
        # Branch count
        from backend.agents.branching.branching_engine import get_branching_engine
        branching_engine = get_branching_engine()
        branches = await branching_engine.get_branches_for_execution(
            db=db,
            execution_id=execution_id,
        )
        branch_count = len(branches)
        
        # Discovery-to-value conversion (simplified)
        # In production, would track discoveries -> spawned tasks -> completion
        discovery_to_value = 0.7 if completed_tasks else 0.0
        
        # Agent performance (tasks completed per agent)
        agent_performance: Dict[UUID, float] = {}
        for task in completed_tasks:
            agent_id = task.spawned_by_agent_id
            if agent_id not in agent_performance:
                agent_performance[agent_id] = 0.0
            agent_performance[agent_id] += 1.0
        
        # Normalize by total tasks per agent
        agent_task_counts: Dict[UUID, int] = {}
        for task in all_tasks:
            agent_id = task.spawned_by_agent_id
            agent_task_counts[agent_id] = agent_task_counts.get(agent_id, 0) + 1
        
        for agent_id in agent_performance:
            total = agent_task_counts.get(agent_id, 1)
            agent_performance[agent_id] = agent_performance[agent_id] / total
        
        # Coherence trends (simplified - would use historical data)
        coherence_trends = await self._calculate_coherence_trends(
            db=db,
            execution_id=execution_id,
        )
        
        return WorkflowAnalytics(
            execution_id=execution_id,
            completion_rate=completion_rate,
            average_task_duration_hours=avg_duration,
            phase_distribution=phase_distribution,
            branch_count=branch_count,
            discovery_to_value_conversion=discovery_to_value,
            agent_performance=agent_performance,
            coherence_trends=coherence_trends,
            calculated_at=datetime.utcnow(),
        )
    
    async def get_workflow_graph_data(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get workflow graph data for visualization.
        
        Returns nodes (tasks) and edges (dependencies).
        """
        # Get all tasks with dependencies
        all_tasks = await self.workflow_engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            include_dependencies=True,
        )
        
        # Build nodes
        nodes = []
        for task in all_tasks:
            nodes.append({
                "id": str(task.id),
                "title": task.title,
                "phase": task.phase,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
            })
        
        # Build edges (dependencies)
        edges = []
        for task in all_tasks:
            if hasattr(task, 'blocks_tasks'):
                for blocked_task in task.blocks_tasks:
                    edges.append({
                        "from": str(task.id),
                        "to": str(blocked_task.id),
                        "type": "blocks",
                    })
        
        # Get branches
        from backend.agents.branching.branching_engine import get_branching_engine
        branching_engine = get_branching_engine()
        branches = await branching_engine.get_branches_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        branch_info = [
            {
                "id": str(branch.id),
                "name": branch.branch_name,
                "phase": branch.branch_phase,
                "status": branch.status,
            }
            for branch in branches
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "branches": branch_info,
            "phases": [phase.value for phase in WorkflowPhase],
        }
    
    async def _calculate_coherence_trends(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Calculate coherence trends over time"""
        # Get recent coherence metrics
        metrics_stmt = (
            select(CoherenceMetrics)
            .where(CoherenceMetrics.execution_id == execution_id)
            .order_by(CoherenceMetrics.calculated_at.desc())
            .limit(20)
        )
        result = await db.execute(metrics_stmt)
        metrics = list(result.scalars().all())
        
        trends = []
        for metric in metrics:
            trends.append({
                "agent_id": str(metric.agent_id),
                "coherence_score": metric.coherence_score,
                "calculated_at": metric.calculated_at.isoformat(),
                "phase": metric.phase,
            })
        
        return trends


# Singleton instance
_analytics_service_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get singleton AnalyticsService instance"""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = AnalyticsService()
    return _analytics_service_instance

