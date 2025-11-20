"""
Coherence Scorer for PM-as-Guardian System (Stream C)

Calculates coherence scores for agent alignment with phases and workflow goals.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.workflow import WorkflowPhase
from backend.models.message import AgentMessage
from backend.models.project import TaskExecution
from backend.models.workflow import DynamicTask

logger = logging.getLogger(__name__)


class CoherenceScore:
    """
    Coherence score result.
    
    Coherence = How well agent's work aligns with phase goals and workflow objectives.
    """
    
    def __init__(
        self,
        overall_score: float,
        metrics: Dict[str, float],
        agent_id: UUID,
        phase: WorkflowPhase,
        calculated_at: datetime,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.overall_score = overall_score
        self.metrics = metrics
        self.agent_id = agent_id
        self.phase = phase
        self.calculated_at = calculated_at
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "metrics": self.metrics,
            "agent_id": str(self.agent_id),
            "phase": self.phase.value,
            "calculated_at": self.calculated_at.isoformat(),
            "details": self.details,
        }


class CoherenceScorer:
    """
    Calculates coherence scores for agent alignment with phases.
    
    Coherence metrics:
    - Phase alignment: Is work appropriate for phase?
    - Goal alignment: Does work contribute to phase goals?
    - Quality alignment: Is work quality appropriate?
    - Task relevance: Are spawned tasks relevant?
    """
    
    # Phase goal keywords (for alignment scoring)
    PHASE_GOALS = {
        WorkflowPhase.INVESTIGATION: [
            "analyze", "investigate", "explore", "discover", "research",
            "understand", "evaluate", "assess", "examine", "study"
        ],
        WorkflowPhase.BUILDING: [
            "implement", "build", "create", "develop", "construct",
            "code", "write", "add", "set up", "configure"
        ],
        WorkflowPhase.VALIDATION: [
            "test", "verify", "validate", "check", "confirm",
            "ensure", "prove", "demonstrate", "review", "inspect"
        ],
    }
    
    def __init__(self):
        """Initialize coherence scorer"""
        pass
    
    async def calculate_coherence(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        phase: WorkflowPhase,
        agent_messages: Optional[List[AgentMessage]] = None,
        agent_work: Optional[str] = None,
    ) -> CoherenceScore:
        """
        Calculate coherence score for an agent.
        
        Args:
            db: Database session
            agent_id: Agent being monitored
            execution_id: Task execution ID
            phase: Current workflow phase
            agent_messages: Optional list of recent agent messages
            agent_work: Optional agent work output
            
        Returns:
            CoherenceScore with overall score and detailed metrics
        """
        # Load agent messages if not provided
        if agent_messages is None:
            agent_messages = await self._load_agent_messages(
                db=db,
                agent_id=agent_id,
                execution_id=execution_id,
                limit=10,  # Recent messages
            )
        
        # Calculate individual metrics
        phase_alignment = self._analyze_phase_alignment(
            agent_messages=agent_messages,
            agent_work=agent_work,
            phase=phase,
        )
        
        goal_alignment = self._analyze_goal_contribution(
            agent_messages=agent_messages,
            agent_work=agent_work,
            execution_id=execution_id,
            db=db,
        )
        
        quality_alignment = self._analyze_quality_alignment(
            agent_messages=agent_messages,
            agent_work=agent_work,
            phase=phase,
        )
        
        task_relevance = await self._analyze_task_relevance(
            db=db,
            agent_id=agent_id,
            execution_id=execution_id,
        )
        
        # Combine metrics (weighted average)
        metrics = {
            "phase_alignment": phase_alignment,
            "goal_alignment": goal_alignment,
            "quality_alignment": quality_alignment,
            "task_relevance": task_relevance,
        }
        
        # Overall score (weighted average)
        # Phase alignment is most important (40%), then goal (30%), quality (20%), task (10%)
        overall_score = (
            phase_alignment * 0.4 +
            goal_alignment * 0.3 +
            quality_alignment * 0.2 +
            task_relevance * 0.1
        )
        
        return CoherenceScore(
            overall_score=overall_score,
            metrics=metrics,
            agent_id=agent_id,
            phase=phase,
            calculated_at=datetime.utcnow(),
            details={
                "message_count": len(agent_messages),
                "has_work_output": agent_work is not None,
            },
        )
    
    async def _load_agent_messages(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        limit: int = 10,
    ) -> List[AgentMessage]:
        """Load recent agent messages"""
        stmt = (
            select(AgentMessage)
            .where(
                AgentMessage.sender_id == agent_id,
                AgentMessage.task_execution_id == execution_id,
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    def _analyze_phase_alignment(
        self,
        agent_messages: List[AgentMessage],
        agent_work: Optional[str],
        phase: WorkflowPhase,
    ) -> float:
        """
        Analyze if agent's work aligns with phase goals.
        
        Returns score 0.0-1.0
        """
        if not agent_messages and not agent_work:
            return 0.5  # Neutral if no data
        
        # Get phase keywords
        phase_keywords = self.PHASE_GOALS.get(phase, [])
        
        # Analyze messages
        message_text = " ".join([msg.content.lower() for msg in agent_messages])
        work_text = (agent_work or "").lower()
        combined_text = message_text + " " + work_text
        
        # Count keyword matches
        matches = sum(1 for keyword in phase_keywords if keyword in combined_text)
        
        # Score based on keyword density
        # More keywords = higher alignment
        max_possible = len(phase_keywords)
        if max_possible == 0:
            return 0.5
        
        score = min(matches / max_possible, 1.0)
        
        # Boost score if messages are recent and relevant
        if len(agent_messages) > 0:
            score = min(score * 1.1, 1.0)  # Small boost for having messages
        
        return score
    
    async def _analyze_goal_contribution(
        self,
        agent_messages: List[AgentMessage],
        agent_work: Optional[str],
        execution_id: UUID,
        db: AsyncSession,
    ) -> float:
        """
        Analyze if agent's work contributes to workflow goals.
        
        Returns score 0.0-1.0
        """
        # For now, use heuristic: check if agent is active and producing work
        # In future, can analyze against actual workflow goals
        
        if len(agent_messages) == 0 and not agent_work:
            return 0.3  # Low score if no activity
        
        # Check if agent is spawning relevant tasks (from Stream B)
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        
        engine = PhaseBasedWorkflowEngine()
        
        # Get agent's spawned tasks
        all_tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        sender_id = agent_messages[0].sender_id if agent_messages else None
        if sender_id:
            agent_tasks = [t for t in all_tasks if t.spawned_by_agent_id == sender_id]
        else:
            agent_tasks = []
        
        # Higher score if agent is actively contributing
        if len(agent_messages) > 3 or agent_work or len(agent_tasks) > 0:
            return 0.8  # Good contribution
        
        return 0.5  # Moderate contribution
    
    def _analyze_quality_alignment(
        self,
        agent_messages: List[AgentMessage],
        agent_work: Optional[str],
        phase: WorkflowPhase,
    ) -> float:
        """
        Analyze if work quality is appropriate for phase.
        
        Returns score 0.0-1.0
        """
        # For now, use heuristic based on message quality
        # In future, can use LLM to analyze quality
        
        if not agent_messages:
            return 0.5  # Neutral
        
        # Check message quality indicators
        quality_indicators = [
            "complete", "done", "tested", "verified", "documented",
            "reviewed", "validated", "approved",
        ]
        
        message_text = " ".join([msg.content.lower() for msg in agent_messages])
        work_text = (agent_work or "").lower()
        combined_text = message_text + " " + work_text
        
        # Count quality indicators
        indicators_found = sum(1 for indicator in quality_indicators if indicator in combined_text)
        
        # Score based on indicators
        score = min(indicators_found / 3.0, 1.0)  # 3+ indicators = high quality
        
        return score
    
    async def _analyze_task_relevance(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
    ) -> float:
        """
        Analyze if spawned tasks are relevant.
        
        Returns score 0.0-1.0
        """
        # Load agent's spawned tasks
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        
        engine = PhaseBasedWorkflowEngine()
        tasks = await engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        agent_tasks = [t for t in tasks if t.spawned_by_agent_id == agent_id]
        
        if len(agent_tasks) == 0:
            return 0.7  # No tasks spawned = neutral (not bad, just no spawning yet)
        
        # Check if tasks have rationale (especially investigation tasks)
        tasks_with_rationale = sum(1 for t in agent_tasks if t.rationale)
        relevance_score = tasks_with_rationale / len(agent_tasks)
        
        return relevance_score


# Singleton instance
_coherence_scorer: Optional[CoherenceScorer] = None


def get_coherence_scorer() -> CoherenceScorer:
    """Get or create coherence scorer instance"""
    global _coherence_scorer
    if _coherence_scorer is None:
        _coherence_scorer = CoherenceScorer()
    return _coherence_scorer

