"""
Workflow Health Monitor for PM-as-Guardian System (Stream C)

Monitors workflow health metrics and detects anomalies.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.models.guardian import CoherenceMetrics

logger = logging.getLogger(__name__)


class WorkflowAnomaly:
    """Represents a workflow anomaly detected by PM Guardian"""
    
    def __init__(
        self,
        type: str,
        severity: str,
        description: str,
        affected_agents: List[UUID],
        suggested_action: str,
    ):
        self.type = type
        self.severity = severity  # "low", "medium", "high"
        self.description = description
        self.affected_agents = affected_agents
        self.suggested_action = suggested_action
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "affected_agents": [str(aid) for aid in self.affected_agents],
            "suggested_action": self.suggested_action,
        }


class WorkflowHealth:
    """Workflow health metrics"""
    
    def __init__(
        self,
        overall_score: float,
        metrics: Dict[str, Any],
        anomalies: List[WorkflowAnomaly],
        recommendations: List[str],
        calculated_at: datetime,
    ):
        self.overall_score = overall_score
        self.metrics = metrics
        self.anomalies = anomalies
        self.recommendations = recommendations
        self.calculated_at = calculated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "metrics": self.metrics,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "recommendations": self.recommendations,
            "calculated_at": self.calculated_at.isoformat(),
        }


class WorkflowHealthMonitor:
    """
    Monitors workflow health metrics.
    
    Tracks:
    - Task completion rates
    - Phase distribution
    - Blocking issues
    - Agent activity levels
    - Discovery rate
    - Coherence scores
    """
    
    def __init__(self):
        """Initialize workflow health monitor"""
        pass
    
    async def calculate_health(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> WorkflowHealth:
        """
        Calculate overall workflow health.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            
        Returns:
            WorkflowHealth with overall score and detailed metrics
        """
        # Get execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")
        
        # Load tasks
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        
        engine = PhaseBasedWorkflowEngine()
        all_tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        # Calculate metrics
        task_completion_rate = self._calculate_completion_rate(all_tasks)
        phase_distribution = self._calculate_phase_distribution(all_tasks)
        blocking_issues = len(await engine.get_blocked_tasks(db=db, execution_id=execution_id))
        agent_activity = await self._calculate_agent_activity(db=db, execution_id=execution_id)
        discovery_rate = self._calculate_discovery_rate(all_tasks)
        avg_coherence = await self._calculate_avg_coherence(db=db, execution_id=execution_id)
        
        metrics = {
            "task_completion_rate": task_completion_rate,
            "phase_distribution": phase_distribution,
            "blocking_issues": blocking_issues,
            "agent_activity": agent_activity,
            "discovery_rate": discovery_rate,
            "avg_coherence": avg_coherence,
        }
        
        # Calculate overall score (weighted average)
        overall_score = (
            task_completion_rate * 0.3 +
            (1.0 - (blocking_issues / max(len(all_tasks), 1))) * 0.25 +
            avg_coherence * 0.25 +
            (sum(agent_activity.values()) / max(len(agent_activity), 1)) * 0.2
        )
        
        # Ensure score is 0.0-1.0
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Detect anomalies
        anomalies = await self.detect_anomalies(
            db=db,
            execution_id=execution_id,
            metrics=metrics,
            all_tasks=all_tasks,
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, anomalies)
        
        return WorkflowHealth(
            overall_score=overall_score,
            metrics=metrics,
            anomalies=anomalies,
            recommendations=recommendations,
            calculated_at=datetime.utcnow(),
        )
    
    def _calculate_completion_rate(self, tasks: List[DynamicTask]) -> float:
        """Calculate task completion rate"""
        if len(tasks) == 0:
            return 0.0
        
        completed = sum(1 for t in tasks if t.status == "completed")
        return completed / len(tasks)
    
    def _calculate_phase_distribution(self, tasks: List[DynamicTask]) -> Dict[str, int]:
        """Calculate distribution of tasks across phases"""
        distribution = {
            "investigation": 0,
            "building": 0,
            "validation": 0,
        }
        
        for task in tasks:
            if task.phase in distribution:
                distribution[task.phase] += 1
        
        return distribution
    
    async def _calculate_agent_activity(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> Dict[UUID, int]:
        """Calculate activity level per agent"""
        from backend.models.message import AgentMessage
        
        stmt = (
            select(
                AgentMessage.sender_id,
                func.count(AgentMessage.id).label("message_count")
            )
            .where(AgentMessage.task_execution_id == execution_id)
            .group_by(AgentMessage.sender_id)
        )
        
        result = await db.execute(stmt)
        activity = {row[0]: row[1] for row in result.all()}
        
        return activity
    
    def _calculate_discovery_rate(self, tasks: List[DynamicTask]) -> float:
        """Calculate discovery rate (tasks with rationale)"""
        if len(tasks) == 0:
            return 0.0
        
        with_rationale = sum(1 for t in tasks if t.rationale)
        return with_rationale / len(tasks)
    
    async def _calculate_avg_coherence(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> float:
        """Calculate average coherence score"""
        stmt = (
            select(func.avg(CoherenceMetrics.coherence_score))
            .where(CoherenceMetrics.execution_id == execution_id)
        )
        
        result = await db.execute(stmt)
        avg_score = result.scalar()
        
        return avg_score if avg_score is not None else 0.7  # Default if no metrics yet
    
    async def detect_anomalies(
        self,
        db: AsyncSession,
        execution_id: UUID,
        metrics: Dict[str, Any],
        all_tasks: List[DynamicTask],
    ) -> List[WorkflowAnomaly]:
        """
        Detect anomalies in workflow execution.
        
        Returns list of detected anomalies.
        """
        anomalies = []
        
        # Check phase imbalance
        phase_dist = metrics.get("phase_distribution", {})
        total_tasks = sum(phase_dist.values())
        
        if total_tasks > 0:
            for phase, count in phase_dist.items():
                percentage = count / total_tasks
                if percentage > 0.7:  # More than 70% in one phase
                    anomalies.append(WorkflowAnomaly(
                        type="phase_imbalance",
                        severity="medium" if percentage > 0.8 else "low",
                        description=f"{percentage:.0%} of tasks in {phase} phase - potential imbalance",
                        affected_agents=[],  # Would need to determine from tasks
                        suggested_action=f"Consider spawning tasks in other phases for better balance",
                    ))
        
        # Check low coherence
        avg_coherence = metrics.get("avg_coherence", 1.0)
        if avg_coherence < 0.5:
            anomalies.append(WorkflowAnomaly(
                type="low_coherence",
                severity="high",
                description=f"Average coherence score is {avg_coherence:.2f} - agents may be misaligned",
                affected_agents=[],
                suggested_action="PM should review agent work and provide guidance",
            ))
        
        # Check high blocking
        blocking_issues = metrics.get("blocking_issues", 0)
        if blocking_issues > len(all_tasks) * 0.3:  # More than 30% blocked
            anomalies.append(WorkflowAnomaly(
                type="high_blocking",
                severity="high",
                description=f"{blocking_issues} tasks are blocked ({blocking_issues/len(all_tasks):.0%} of total)",
                affected_agents=[],
                suggested_action="Review dependencies and unblock tasks",
            ))
        
        # Check agent inactivity
        agent_activity = metrics.get("agent_activity", {})
        if len(agent_activity) == 0:
            anomalies.append(WorkflowAnomaly(
                type="agent_inactivity",
                severity="medium",
                description="No agent activity detected",
                affected_agents=[],
                suggested_action="Check if agents are processing messages",
            ))
        
        return anomalies
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        anomalies: List[WorkflowAnomaly],
    ) -> List[str]:
        """Generate recommendations based on metrics and anomalies"""
        recommendations = []
        
        # Recommendations based on anomalies
        for anomaly in anomalies:
            if anomaly.severity == "high":
                recommendations.append(f"🚨 {anomaly.suggested_action}")
            elif anomaly.severity == "medium":
                recommendations.append(f"⚠️ {anomaly.suggested_action}")
            else:
                recommendations.append(f"ℹ️ {anomaly.suggested_action}")
        
        # Additional recommendations based on metrics
        completion_rate = metrics.get("task_completion_rate", 0.0)
        if completion_rate < 0.3:
            recommendations.append("Consider prioritizing task completion - rate is low")
        
        discovery_rate = metrics.get("discovery_rate", 0.0)
        if discovery_rate < 0.2:
            recommendations.append("Agents may benefit from encouragement to discover opportunities")
        
        return recommendations


# Singleton instance
_workflow_health_monitor: Optional[WorkflowHealthMonitor] = None


def get_workflow_health_monitor() -> WorkflowHealthMonitor:
    """Get or create workflow health monitor instance"""
    global _workflow_health_monitor
    if _workflow_health_monitor is None:
        _workflow_health_monitor = WorkflowHealthMonitor()
    return _workflow_health_monitor

