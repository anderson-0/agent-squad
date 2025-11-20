"""
Advanced Anomaly Detection for PM-as-Guardian (Stream G)

Detects unusual patterns, phase drift, and workflow health issues.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.message import AgentMessage
from backend.models.project import TaskExecution
from backend.core.logging import logger


class Anomaly:
    """Represents a detected anomaly"""
    def __init__(
        self,
        type: str,
        severity: str,
        description: str,
        recommendation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.type = type
        self.severity = severity  # "low", "medium", "high", "critical"
        self.description = description
        self.recommendation = recommendation
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection for workflow health monitoring.
    
    Detects:
    - Phase drift (agents not aligned with phase goals)
    - Low-value task spawning
    - Workflow stagnation
    - Resource imbalance
    - Communication gaps
    """
    
    def __init__(self):
        """Initialize anomaly detector"""
        pass
    
    async def detect_anomalies(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """
        Detect anomalies in workflow.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            return anomalies
        
        # Detect phase drift
        phase_drift = await self._detect_phase_drift(db, execution_id)
        if phase_drift:
            anomalies.extend(phase_drift)
        
        # Detect low-value tasks
        low_value = await self._detect_low_value_tasks(db, execution_id)
        if low_value:
            anomalies.extend(low_value)
        
        # Detect workflow stagnation
        stagnation = await self._detect_stagnation(db, execution_id)
        if stagnation:
            anomalies.extend(stagnation)
        
        # Detect resource imbalance
        imbalance = await self._detect_resource_imbalance(db, execution_id)
        if imbalance:
            anomalies.extend(imbalance)
        
        # Detect communication gaps
        gaps = await self._detect_communication_gaps(db, execution_id)
        if gaps:
            anomalies.extend(gaps)
        
        return anomalies
    
    async def _detect_phase_drift(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """Detect if agents are working outside their phase goals"""
        anomalies = []
        
        # Get recent tasks
        tasks_query = select(DynamicTask).where(
            DynamicTask.parent_execution_id == execution_id
        ).order_by(DynamicTask.created_at.desc()).limit(20)
        
        result = await db.execute(tasks_query)
        recent_tasks = list(result.scalars().all())
        
        if not recent_tasks:
            return anomalies
        
        # Get recent messages
        messages_query = select(AgentMessage).where(
            AgentMessage.task_execution_id == execution_id
        ).order_by(AgentMessage.created_at.desc()).limit(50)
        
        result = await db.execute(messages_query)
        recent_messages = list(result.scalars().all())
        
        # Check for phase-task mismatch
        phase_keywords = {
            WorkflowPhase.INVESTIGATION.value: ["analyze", "investigate", "explore", "discover", "research"],
            WorkflowPhase.BUILDING.value: ["implement", "build", "create", "develop", "code"],
            WorkflowPhase.VALIDATION.value: ["test", "verify", "validate", "check", "confirm"],
        }
        
        for task in recent_tasks[:10]:
            # Check if task description aligns with phase
            description_lower = task.description.lower()
            phase_words = phase_keywords.get(task.phase, [])
            
            if phase_words:
                matches = sum(1 for word in phase_words if word in description_lower)
                if matches == 0:
                    anomalies.append(Anomaly(
                        type="phase_drift",
                        severity="medium",
                        description=f"Task '{task.title[:50]}' in {task.phase} phase may not align with phase goals",
                        recommendation=f"Review task alignment with {task.phase} phase objectives",
                        metadata={"task_id": str(task.id), "phase": task.phase},
                    ))
        
        return anomalies
    
    async def _detect_low_value_tasks(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """Detect tasks with low predicted value or vague descriptions"""
        anomalies = []
        
        tasks_query = select(DynamicTask).where(
            DynamicTask.parent_execution_id == execution_id,
            DynamicTask.status.in_(["pending", "in_progress"]),
        )
        
        result = await db.execute(tasks_query)
        active_tasks = list(result.scalars().all())
        
        for task in active_tasks:
            # Check for vague descriptions
            if len(task.description) < 30:
                anomalies.append(Anomaly(
                    type="low_value_task",
                    severity="low",
                    description=f"Task '{task.title[:50]}' has very brief description",
                    recommendation="Request more detailed task description from spawning agent",
                    metadata={"task_id": str(task.id)},
                ))
            
            # Check for missing rationale (especially in investigation)
            if task.phase == WorkflowPhase.INVESTIGATION.value and not task.rationale:
                anomalies.append(Anomaly(
                    type="missing_rationale",
                    severity="low",
                    description=f"Investigation task '{task.title[:50]}' lacks rationale",
                    recommendation="Investigation tasks should include rationale for creation",
                    metadata={"task_id": str(task.id)},
                ))
        
        return anomalies
    
    async def _detect_stagnation(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """Detect workflow stagnation (no progress)"""
        anomalies = []
        
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            return anomalies
        
        # Check if execution is stuck
        if execution.status == "in_progress":
            # Check last activity
            last_message_query = select(AgentMessage).where(
                AgentMessage.task_execution_id == execution_id
            ).order_by(AgentMessage.created_at.desc()).limit(1)
            
            result = await db.execute(last_message_query)
            last_message = result.scalar_one_or_none()
            
            if last_message:
                time_since_activity = datetime.utcnow() - last_message.created_at
                
                # Stagnation thresholds
                if time_since_activity > timedelta(hours=24):
                    anomalies.append(Anomaly(
                        type="workflow_stagnation",
                        severity="high",
                        description=f"No activity for {time_since_activity.days} days",
                        recommendation="Check agent activity and unblock any blockers",
                        metadata={"hours_since_activity": time_since_activity.total_seconds() / 3600},
                    ))
                elif time_since_activity > timedelta(hours=8):
                    anomalies.append(Anomaly(
                        type="workflow_stagnation",
                        severity="medium",
                        description=f"No activity for {int(time_since_activity.total_seconds() / 3600)} hours",
                        recommendation="Monitor workflow progress",
                        metadata={"hours_since_activity": time_since_activity.total_seconds() / 3600},
                    ))
        
        return anomalies
    
    async def _detect_resource_imbalance(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """Detect resource imbalance (too many tasks in one phase)"""
        anomalies = []
        
        tasks_query = select(DynamicTask).where(
            DynamicTask.parent_execution_id == execution_id,
        )
        
        result = await db.execute(tasks_query)
        all_tasks = list(result.scalars().all())
        
        if len(all_tasks) < 5:
            return anomalies  # Not enough tasks for imbalance
        
        # Count tasks by phase
        phase_counts = {}
        for task in all_tasks:
            phase_counts[task.phase] = phase_counts.get(task.phase, 0) + 1
        
        total = len(all_tasks)
        
        # Check for imbalance (>70% in one phase)
        for phase, count in phase_counts.items():
            percentage = count / total
            if percentage > 0.7:
                anomalies.append(Anomaly(
                    type="phase_imbalance",
                    severity="medium",
                    description=f"{percentage:.0%} of tasks in {phase} phase ({count}/{total})",
                    recommendation="Consider distributing work across phases more evenly",
                    metadata={"phase": phase, "count": count, "total": total},
                ))
        
        return anomalies
    
    async def _detect_communication_gaps(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[Anomaly]:
        """Detect communication gaps between agents"""
        anomalies = []
        
        # Get recent messages
        messages_query = select(AgentMessage).where(
            AgentMessage.task_execution_id == execution_id
        ).order_by(AgentMessage.created_at.desc()).limit(20)
        
        result = await db.execute(messages_query)
        recent_messages = list(result.scalars().all())
        
        if len(recent_messages) < 3:
            return anomalies
        
        # Check for agents not communicating
        active_agents = {msg.sender_id for msg in recent_messages[:10]}
        
        # Get all agents in execution's squad
        execution = await db.get(TaskExecution, execution_id)
        if execution and hasattr(execution, 'squad'):
            squad_agents = {member.id for member in execution.squad.members if member.is_active}
            
            inactive_agents = squad_agents - active_agents
            if len(inactive_agents) > 0 and len(squad_agents) > 2:
                anomalies.append(Anomaly(
                    type="communication_gap",
                    severity="low",
                    description=f"{len(inactive_agents)} agent(s) not active recently",
                    recommendation="Engage inactive agents or review workload distribution",
                    metadata={"inactive_count": len(inactive_agents)},
                ))
        
        return anomalies


# Singleton instance
_anomaly_detector: Optional[AdvancedAnomalyDetector] = None


def get_anomaly_detector() -> AdvancedAnomalyDetector:
    """Get or create anomaly detector instance"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AdvancedAnomalyDetector()
    return _anomaly_detector

