"""
Recommendations Engine for PM-as-Guardian (Stream G)

Generates actionable recommendations based on coherence metrics
and anomaly detection.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.workflow import WorkflowPhase
from backend.agents.guardian.coherence_scorer import CoherenceScore
from backend.agents.guardian.advanced_anomaly_detector import Anomaly, get_anomaly_detector
from backend.core.logging import logger


class Recommendation:
    """Represents a recommendation for workflow improvement"""
    def __init__(
        self,
        type: str,
        action: str,
        priority: str,
        target_agents: Optional[List[UUID]] = None,
        rationale: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.type = type
        self.action = action
        self.priority = priority  # "low", "medium", "high", "urgent"
        self.target_agents = target_agents or []
        self.rationale = rationale
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "action": self.action,
            "priority": self.priority,
            "target_agents": [str(agent_id) for agent_id in self.target_agents],
            "rationale": self.rationale,
            "metadata": self.metadata,
        }


class RecommendationsEngine:
    """
    Generates actionable recommendations based on:
    - Coherence metrics
    - Detected anomalies
    - Workflow health
    """
    
    def __init__(self):
        """Initialize recommendations engine"""
        self.anomaly_detector = get_anomaly_detector()
    
    async def generate_recommendations(
        self,
        db: AsyncSession,
        execution_id: UUID,
        coherence_scores: Optional[List[CoherenceScore]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations for workflow improvement.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            coherence_scores: Optional list of coherence scores for agents
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Get anomalies
        anomalies = await self.anomaly_detector.detect_anomalies(db, execution_id)
        
        # Generate recommendations from anomalies
        for anomaly in anomalies:
            rec = self._anomaly_to_recommendation(anomaly)
            if rec:
                recommendations.append(rec)
        
        # Generate recommendations from coherence scores
        if coherence_scores:
            coherence_recs = self._coherence_to_recommendations(coherence_scores)
            recommendations.extend(coherence_recs)
        
        # Sort by priority
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))
        
        return recommendations
    
    def _anomaly_to_recommendation(self, anomaly: Anomaly) -> Optional[Recommendation]:
        """Convert anomaly to recommendation"""
        # Map anomaly severity to recommendation priority
        severity_to_priority = {
            "critical": "urgent",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        
        priority = severity_to_priority.get(anomaly.severity, "medium")
        
        return Recommendation(
            type=f"resolve_{anomaly.type}",
            action=anomaly.recommendation,
            priority=priority,
            rationale=anomaly.description,
            metadata=anomaly.metadata,
        )
    
    def _coherence_to_recommendations(
        self,
        coherence_scores: List[CoherenceScore],
    ) -> List[Recommendation]:
        """Generate recommendations from coherence scores"""
        recommendations = []
        
        for score in coherence_scores:
            # Low phase alignment
            if score.metrics.get("phase_alignment", 1.0) < 0.7:
                recommendations.append(Recommendation(
                    type="phase_alignment",
                    action=f"Conduct phase alignment review with agent",
                    priority="high",
                    target_agents=[score.agent_id],
                    rationale=f"Agent has low phase alignment ({score.metrics.get('phase_alignment', 0):.2f})",
                    metadata={"phase": score.phase.value, "score": score.metrics.get("phase_alignment", 0)},
                ))
            
            # Low task relevance
            if score.metrics.get("task_relevance", 1.0) < 0.6:
                recommendations.append(Recommendation(
                    type="task_relevance",
                    action="Review spawned tasks for relevance",
                    priority="medium",
                    target_agents=[score.agent_id],
                    rationale=f"Agent spawned tasks with low relevance score ({score.metrics.get('task_relevance', 0):.2f})",
                    metadata={"score": score.metrics.get("task_relevance", 0)},
                ))
            
            # Low overall coherence
            if score.overall_score < 0.6:
                recommendations.append(Recommendation(
                    type="general_coherence",
                    action="Schedule workflow review session",
                    priority="high",
                    target_agents=[score.agent_id],
                    rationale=f"Agent has low overall coherence ({score.overall_score:.2f})",
                    metadata={"overall_score": score.overall_score},
                ))
        
        return recommendations


# Singleton instance
_recommendations_engine: Optional[RecommendationsEngine] = None


def get_recommendations_engine() -> RecommendationsEngine:
    """Get or create recommendations engine instance"""
    global _recommendations_engine
    if _recommendations_engine is None:
        _recommendations_engine = RecommendationsEngine()
    return _recommendations_engine

