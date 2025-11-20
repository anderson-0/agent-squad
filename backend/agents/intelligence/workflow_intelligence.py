"""
Workflow Intelligence System (Stream I)

AI-powered workflow recommendations, predictions, and optimizations.

Provides:
- Task suggestions based on workflow state
- Outcome predictions (completion time, success probability)
- Task ordering optimization
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.models.branching import WorkflowBranch
from backend.agents.discovery.discovery_engine import DiscoveryEngine, get_discovery_engine, TaskSuggestion as DiscoveryTaskSuggestion, WorkContext
from backend.agents.guardian import (
    CoherenceScorer,
    WorkflowHealthMonitor,
    get_coherence_scorer,
    get_workflow_health_monitor,
    CoherenceScore,
    WorkflowHealth,
)
from backend.agents.branching.branching_engine import BranchingEngine, get_branching_engine
from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.models.message import AgentMessage
from backend.models.squad import SquadMember

logger = logging.getLogger(__name__)


class TaskSuggestion(BaseModel):
    """
    Task suggestion from workflow intelligence.
    
    Enhanced version that considers:
    - Current workflow state
    - Agent coherence scores
    - Discovery opportunities
    - Branch status
    - Task dependencies
    """
    title: str
    description: str
    phase: WorkflowPhase
    rationale: str
    estimated_value: float  # 0.0-1.0
    priority: str  # "low", "medium", "high", "urgent"
    blocking_task_ids: List[UUID] = []
    suggested_agent_id: Optional[UUID] = None
    confidence: float  # 0.0-1.0 confidence in suggestion
    reasoning: str  # Detailed reasoning for the suggestion
    estimated_duration_hours: Optional[float] = None


class WorkflowPrediction(BaseModel):
    """
    Prediction of workflow outcomes.
    """
    execution_id: UUID
    predicted_completion_time: Optional[datetime]
    success_probability: float  # 0.0-1.0
    estimated_total_hours: Optional[float]
    risk_factors: List[str] = []
    confidence: float  # 0.0-1.0 confidence in prediction
    reasoning: str
    calculated_at: datetime


class WorkflowIntelligence:
    """
    AI-powered workflow intelligence system.
    
    Provides:
    - Intelligent task suggestions
    - Workflow outcome predictions
    - Task ordering optimization
    - Integration with Guardian, Discovery, and Branching systems
    """
    
    def __init__(self):
        """Initialize workflow intelligence system"""
        self.discovery_engine = get_discovery_engine()
        self.coherence_scorer = get_coherence_scorer()
        self.health_monitor = get_workflow_health_monitor()
        self.branching_engine = get_branching_engine()
        self.workflow_engine = PhaseBasedWorkflowEngine()
    
    async def suggest_next_tasks(
        self,
        db: AsyncSession,
        execution_id: UUID,
        agent_id: Optional[UUID] = None,
        max_suggestions: int = 5,
    ) -> List[TaskSuggestion]:
        """
        Suggest next tasks based on workflow intelligence.
        
        Considers:
        - Current workflow state
        - Agent coherence scores
        - Discovery opportunities
        - Active branches
        - Task dependencies
        - Phase distribution
        
        Args:
            db: Database session
            execution_id: Task execution ID
            agent_id: Optional specific agent to suggest for
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of task suggestions (sorted by priority and value)
        """
        # Get workflow state
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")
        
        # Get all tasks
        all_tasks = await self.workflow_engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            include_dependencies=True,
        )
        
        # Get workflow health
        workflow_health = await self.health_monitor.calculate_health(
            db=db,
            execution_id=execution_id,
        )
        
        # Get agent coherence scores
        agent_coherence: Dict[UUID, CoherenceScore] = {}
        if hasattr(execution, 'squad') and execution.squad:
            current_phase = self._determine_current_phase(all_tasks)
            for member in execution.squad.members:
                if member.is_active:
                    try:
                        score = await self.coherence_scorer.calculate_coherence(
                            db=db,
                            agent_id=member.id,
                            execution_id=execution_id,
                            phase=current_phase,
                        )
                        agent_coherence[member.id] = score
                    except Exception as e:
                        logger.debug(f"Could not calculate coherence for agent {member.id}: {e}")
        
        # Get discoveries from DiscoveryEngine
        discovery_suggestions: List[DiscoveryTaskSuggestion] = []
        if agent_id:
            # Get suggestions for specific agent
            try:
                # Load recent messages
                message_stmt = (
                    select(AgentMessage)
                    .where(
                        AgentMessage.task_execution_id == execution_id,
                        AgentMessage.sender_id == agent_id,
                    )
                    .order_by(AgentMessage.created_at.desc())
                    .limit(20)
                )
                result = await db.execute(message_stmt)
                recent_messages = list(result.scalars().all())
                
                # Load recent tasks
                recent_tasks = [t for t in all_tasks if t.spawned_by_agent_id == agent_id][:10]
                
                context = WorkContext(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    phase=self._determine_current_phase(all_tasks),
                    recent_messages=recent_messages,
                    recent_tasks=recent_tasks,
                )
                
                discovery_suggestions = await self.discovery_engine.discover_and_suggest_tasks(
                    db=db,
                    context=context,
                )
            except Exception as e:
                logger.debug(f"Could not get discovery suggestions: {e}")
        
        # Get active branches (status="active")
        active_branches = await self.branching_engine.get_branches_for_execution(
            db=db,
            execution_id=execution_id,
        )
        # Filter to active branches only
        active_branches = [b for b in active_branches if b.status == "active"]
        
        # Generate intelligent suggestions
        suggestions: List[TaskSuggestion] = []
        
        # 1. Suggestions from discoveries
        for disc_suggestion in discovery_suggestions[:max_suggestions]:
            suggestions.append(self._convert_discovery_suggestion(
                disc_suggestion=disc_suggestion,
                agent_coherence=agent_coherence,
                all_tasks=all_tasks,
            ))
        
        # 2. Suggestions based on workflow gaps
        gap_suggestions = await self._suggest_from_workflow_gaps(
            db=db,
            execution_id=execution_id,
            all_tasks=all_tasks,
            workflow_health=workflow_health,
            active_branches=active_branches,
        )
        suggestions.extend(gap_suggestions)
        
        # 3. Suggestions based on coherence gaps
        coherence_suggestions = await self._suggest_from_coherence_gaps(
            db=db,
            execution_id=execution_id,
            agent_coherence=agent_coherence,
            all_tasks=all_tasks,
        )
        suggestions.extend(coherence_suggestions)
        
        # 4. Suggestions from active branches
        branch_suggestions = await self._suggest_from_branches(
            db=db,
            active_branches=active_branches,
            all_tasks=all_tasks,
        )
        suggestions.extend(branch_suggestions)
        
        # Deduplicate and sort by priority + value
        suggestions = self._deduplicate_suggestions(suggestions)
        suggestions = self._sort_suggestions(suggestions)
        
        return suggestions[:max_suggestions]
    
    async def predict_workflow_outcomes(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> WorkflowPrediction:
        """
        Predict workflow outcomes (completion time, success probability).
        
        Considers:
        - Task completion rate
        - Average task duration (historical)
        - Blocking issues
        - Agent coherence scores
        - Workflow health
        - Active branches
        
        Args:
            db: Database session
            execution_id: Task execution ID
            
        Returns:
            WorkflowPrediction with outcomes
        """
        # Get workflow state
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")
        
        # Get all tasks
        all_tasks = await self.workflow_engine.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
        )
        
        # Get workflow health
        workflow_health = await self.health_monitor.calculate_health(
            db=db,
            execution_id=execution_id,
        )
        
        # Calculate completion metrics
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        pending_tasks = [t for t in all_tasks if t.status == "pending"]
        in_progress_tasks = [t for t in all_tasks if t.status == "in_progress"]
        
        completion_rate = workflow_health.metrics.get("task_completion_rate", 0.0)
        
        # Estimate remaining work
        # Simple heuristic: assume average task takes 4 hours
        avg_task_hours = 4.0
        remaining_hours = (len(pending_tasks) + len(in_progress_tasks)) * avg_task_hours
        
        # Adjust for blocking issues
        blocking_issues = workflow_health.metrics.get("blocking_issues", 0)
        if blocking_issues > 0:
            remaining_hours *= 1.5  # 50% penalty for blockers
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            workflow_health=workflow_health,
            completion_rate=completion_rate,
            blocking_issues=blocking_issues,
        )
        
        # Predict completion time
        predicted_completion_time = None
        if remaining_hours > 0:
            predicted_completion_time = datetime.utcnow() + timedelta(hours=remaining_hours)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            workflow_health=workflow_health,
            all_tasks=all_tasks,
            blocking_issues=blocking_issues,
        )
        
        # Calculate confidence
        confidence = self._calculate_prediction_confidence(
            completion_rate=completion_rate,
            task_count=len(all_tasks),
        )
        
        reasoning = self._generate_prediction_reasoning(
            completion_rate=completion_rate,
            remaining_tasks=len(pending_tasks) + len(in_progress_tasks),
            blocking_issues=blocking_issues,
            success_probability=success_probability,
            risk_factors=risk_factors,
        )
        
        return WorkflowPrediction(
            execution_id=execution_id,
            predicted_completion_time=predicted_completion_time,
            success_probability=success_probability,
            estimated_total_hours=remaining_hours,
            risk_factors=risk_factors,
            confidence=confidence,
            reasoning=reasoning,
            calculated_at=datetime.utcnow(),
        )
    
    async def optimize_task_ordering(
        self,
        db: AsyncSession,
        execution_id: UUID,
        tasks: Optional[List[DynamicTask]] = None,
    ) -> List[DynamicTask]:
        """
        Optimize task ordering for optimal completion.
        
        Uses dependency analysis and priority to reorder tasks.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            tasks: Optional list of tasks (if None, fetches all tasks)
            
        Returns:
            Optimized list of tasks (ordered for best completion)
        """
        if tasks is None:
            tasks = await self.workflow_engine.get_tasks_for_execution(
                db=db,
                execution_id=execution_id,
                include_dependencies=True,
            )
        
        # Filter to pending/in_progress tasks
        active_tasks = [t for t in tasks if t.status in ["pending", "in_progress"]]
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(active_tasks)
        
        # Topological sort with priority consideration
        ordered_tasks = self._topological_sort_with_priority(
            tasks=active_tasks,
            dependency_graph=dependency_graph,
        )
        
        # Append completed tasks at the end (for reference)
        completed_tasks = [t for t in tasks if t.status == "completed"]
        ordered_tasks.extend(completed_tasks)
        
        return ordered_tasks
    
    # Helper methods
    
    def _determine_current_phase(self, tasks: List[DynamicTask]) -> WorkflowPhase:
        """Determine current workflow phase based on task distribution"""
        if not tasks:
            return WorkflowPhase.INVESTIGATION
        
        phase_counts: Dict[WorkflowPhase, int] = {
            WorkflowPhase.INVESTIGATION: 0,
            WorkflowPhase.BUILDING: 0,
            WorkflowPhase.VALIDATION: 0,
        }
        
        for task in tasks:
            if task.status != "completed":
                phase_counts[WorkflowPhase(task.phase)] += 1
        
        # Return phase with most active tasks
        return max(phase_counts.items(), key=lambda x: x[1])[0]
    
    def _convert_discovery_suggestion(
        self,
        disc_suggestion: DiscoveryTaskSuggestion,
        agent_coherence: Dict[UUID, CoherenceScore],
        all_tasks: List[DynamicTask],
    ) -> TaskSuggestion:
        """Convert DiscoveryEngine suggestion to Intelligence suggestion"""
        # Find best agent for this task
        suggested_agent_id = self._find_best_agent_for_phase(
            phase=disc_suggestion.phase,
            agent_coherence=agent_coherence,
        )
        
        confidence = disc_suggestion.estimated_value  # Use discovery value as confidence
        
        return TaskSuggestion(
            title=disc_suggestion.title,
            description=disc_suggestion.description,
            phase=disc_suggestion.phase,
            rationale=disc_suggestion.rationale,
            estimated_value=disc_suggestion.estimated_value,
            priority=disc_suggestion.priority,
            blocking_task_ids=disc_suggestion.blocking_task_ids,
            suggested_agent_id=suggested_agent_id,
            confidence=confidence,
            reasoning=f"Based on discovery opportunity (value: {disc_suggestion.estimated_value:.2f})",
            estimated_duration_hours=4.0,  # Default estimate
        )
    
    def _find_best_agent_for_phase(
        self,
        phase: WorkflowPhase,
        agent_coherence: Dict[UUID, CoherenceScore],
    ) -> Optional[UUID]:
        """Find best agent for a given phase based on coherence"""
        if not agent_coherence:
            return None
        
        # Find agent with highest coherence for this phase
        best_agent = None
        best_score = 0.0
        
        for agent_id, score in agent_coherence.items():
            if score.phase == phase and score.overall_score > best_score:
                best_score = score.overall_score
                best_agent = agent_id
        
        return best_agent
    
    async def _suggest_from_workflow_gaps(
        self,
        db: AsyncSession,
        execution_id: UUID,
        all_tasks: List[DynamicTask],
        workflow_health: WorkflowHealth,
        active_branches: List[WorkflowBranch],
    ) -> List[TaskSuggestion]:
        """Suggest tasks based on workflow gaps"""
        suggestions = []
        
        # Check for phase imbalance
        phase_distribution = workflow_health.metrics.get("phase_distribution", {})
        
        # phase_distribution is a dict like {"investigation": 5, "building": 3, ...}
        # If we have many investigation tasks but few building tasks, suggest building
        investigation_count = phase_distribution.get(WorkflowPhase.INVESTIGATION.value, 0) if isinstance(phase_distribution, dict) else 0
        building_count = phase_distribution.get(WorkflowPhase.BUILDING.value, 0) if isinstance(phase_distribution, dict) else 0
        
        if investigation_count > 3 and building_count < 2:
            suggestions.append(TaskSuggestion(
                title="Transition to Building Phase",
                description="Consider moving to implementation based on investigation findings",
                phase=WorkflowPhase.BUILDING,
                rationale="Workflow has many investigation tasks but few building tasks",
                estimated_value=0.7,
                priority="medium",
                confidence=0.6,
                reasoning="Phase distribution suggests we should start building",
            ))
        
        # Check for validation gaps
        validation_count = phase_distribution.get(WorkflowPhase.VALIDATION.value, 0) if isinstance(phase_distribution, dict) else 0
        if building_count > 3 and validation_count == 0:
            suggestions.append(TaskSuggestion(
                title="Plan Validation Activities",
                description="Consider adding validation tasks for completed building work",
                phase=WorkflowPhase.VALIDATION,
                rationale="Building phase has progress but no validation planned",
                estimated_value=0.8,
                priority="high",
                blocking_task_ids=[],
                suggested_agent_id=None,
                confidence=0.7,
                reasoning="Validation should follow building activities",
                estimated_duration_hours=4.0,
            ))
        
        return suggestions
    
    async def _suggest_from_coherence_gaps(
        self,
        db: AsyncSession,
        execution_id: UUID,
        agent_coherence: Dict[UUID, CoherenceScore],
        all_tasks: List[DynamicTask],
    ) -> List[TaskSuggestion]:
        """Suggest tasks based on agent coherence gaps"""
        suggestions = []
        
        # Find agents with low coherence
        for agent_id, score in agent_coherence.items():
            if score.overall_score < 0.6:
                suggestions.append(TaskSuggestion(
                    title=f"Improve Alignment for Agent",
                    description=f"Agent has low coherence ({score.overall_score:.2f}). Consider re-aligning with phase goals.",
                    phase=score.phase,
                    rationale=f"Low coherence score indicates misalignment",
                    estimated_value=0.6,
                    priority="medium",
                    blocking_task_ids=[],
                    suggested_agent_id=agent_id,
                    confidence=0.8,
                    reasoning=f"Agent coherence is {score.overall_score:.2f}, below threshold of 0.6",
                    estimated_duration_hours=2.0,
                ))
        
        return suggestions
    
    async def _suggest_from_branches(
        self,
        db: AsyncSession,
        active_branches: List[WorkflowBranch],
        all_tasks: List[DynamicTask],
    ) -> List[TaskSuggestion]:
        """Suggest tasks based on active branches"""
        suggestions = []
        
        for branch in active_branches:
            branch_tasks = await self.branching_engine.get_branch_tasks(
                db=db,
                branch_id=branch.id,
            )
            
            # If branch has no tasks or all tasks are completed, suggest next steps
            if not branch_tasks or all(t.status == "completed" for t in branch_tasks):
                suggestions.append(TaskSuggestion(
                    title=f"Continue Branch: {branch.branch_name}",
                    description=f"Branch '{branch.branch_name}' is active but has no remaining tasks. Consider next steps.",
                    phase=WorkflowPhase(branch.branch_phase),
                    rationale=f"Active branch needs continuation",
                    estimated_value=0.7,
                    priority="medium",
                    blocking_task_ids=[],
                    suggested_agent_id=None,
                    confidence=0.6,
                    reasoning=f"Branch '{branch.branch_name}' appears to need next steps",
                    estimated_duration_hours=4.0,
                ))
        
        return suggestions
    
    def _deduplicate_suggestions(self, suggestions: List[TaskSuggestion]) -> List[TaskSuggestion]:
        """Remove duplicate suggestions"""
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            key = (suggestion.title.lower(), suggestion.phase.value)
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique
    
    def _sort_suggestions(self, suggestions: List[TaskSuggestion]) -> List[TaskSuggestion]:
        """Sort suggestions by priority and value"""
        priority_weights = {
            "urgent": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }
        
        return sorted(
            suggestions,
            key=lambda s: (
                priority_weights.get(s.priority, 0),
                s.estimated_value,
                s.confidence,
            ),
            reverse=True,
        )
    
    def _calculate_success_probability(
        self,
        workflow_health: WorkflowHealth,
        completion_rate: float,
        blocking_issues: int,
    ) -> float:
        """Calculate success probability for workflow"""
        base_probability = workflow_health.overall_score
        
        # Adjust for completion rate
        completion_factor = completion_rate * 0.3
        
        # Adjust for blocking issues
        blocking_penalty = min(blocking_issues * 0.1, 0.3)
        
        success_probability = base_probability * 0.5 + completion_factor * 0.5 - blocking_penalty
        
        return max(0.0, min(1.0, success_probability))
    
    def _identify_risk_factors(
        self,
        workflow_health: WorkflowHealth,
        all_tasks: List[DynamicTask],
        blocking_issues: int,
    ) -> List[str]:
        """Identify risk factors for workflow"""
        risks = []
        
        if blocking_issues > 3:
            risks.append(f"{blocking_issues} blocking issues detected")
        
        if workflow_health.overall_score < 0.5:
            risks.append("Low overall workflow health")
        
        pending_count = len([t for t in all_tasks if t.status == "pending"])
        if pending_count > 10:
            risks.append(f"Large backlog ({pending_count} pending tasks)")
        
        # Check for anomalies
        for anomaly in workflow_health.anomalies:
            if anomaly.severity in ["high", "critical"]:
                risks.append(anomaly.description)
        
        return risks
    
    def _calculate_prediction_confidence(
        self,
        completion_rate: float,
        task_count: int,
    ) -> float:
        """Calculate confidence in prediction"""
        # More tasks = more confidence (we have more data)
        task_factor = min(task_count / 20.0, 1.0)
        
        # Higher completion rate = more confidence
        completion_factor = completion_rate
        
        confidence = (task_factor * 0.5) + (completion_factor * 0.5)
        
        return max(0.3, min(1.0, confidence))  # Minimum 30% confidence
    
    def _generate_prediction_reasoning(
        self,
        completion_rate: float,
        remaining_tasks: int,
        blocking_issues: int,
        success_probability: float,
        risk_factors: List[str],
    ) -> str:
        """Generate human-readable reasoning for prediction"""
        reasoning_parts = []
        
        reasoning_parts.append(f"Completion rate: {completion_rate:.0%}")
        reasoning_parts.append(f"Remaining tasks: {remaining_tasks}")
        
        if blocking_issues > 0:
            reasoning_parts.append(f"Blocking issues: {blocking_issues}")
        
        reasoning_parts.append(f"Success probability: {success_probability:.0%}")
        
        if risk_factors:
            reasoning_parts.append(f"Risk factors: {', '.join(risk_factors[:3])}")
        
        return ". ".join(reasoning_parts) + "."
    
    def _build_dependency_graph(
        self,
        tasks: List[DynamicTask],
    ) -> Dict[UUID, List[UUID]]:
        """Build dependency graph for tasks"""
        graph: Dict[UUID, List[UUID]] = {task.id: [] for task in tasks}
        
        for task in tasks:
            # Get blocking tasks (tasks that this task blocks)
            if hasattr(task, 'blocks_tasks'):
                for blocked_task in task.blocks_tasks:
                    if blocked_task.id in graph:
                        graph[task.id].append(blocked_task.id)
        
        return graph
    
    def _topological_sort_with_priority(
        self,
        tasks: List[DynamicTask],
        dependency_graph: Dict[UUID, List[UUID]],
    ) -> List[DynamicTask]:
        """
        Topological sort with priority consideration.
        
        Ensures dependencies are respected while prioritizing high-value tasks.
        """
        # Build reverse graph (what blocks what)
        reverse_graph: Dict[UUID, List[UUID]] = {task.id: [] for task in tasks}
        for task_id, blocking in dependency_graph.items():
            for blocked_id in blocking:
                reverse_graph[blocked_id].append(task_id)
        
        # Priority weights
        priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        
        # Calculate in-degrees
        in_degree = {task.id: len(reverse_graph[task.id]) for task in tasks}
        
        # Start with tasks that have no dependencies
        queue = [
            task for task in tasks
            if in_degree[task.id] == 0
        ]
        
        # Sort queue by created_at (earlier tasks first)
        # Note: DynamicTask doesn't have priority field, so we use created_at
        queue.sort(key=lambda t: t.created_at)
        
        result = []
        
        while queue:
            # Get task with highest priority and no dependencies
            current = queue.pop(0)
            result.append(current)
            
            # Remove this task's dependencies from other tasks
            for blocked_id in dependency_graph[current.id]:
                in_degree[blocked_id] -= 1
                if in_degree[blocked_id] == 0:
                    # Find the task and add to queue
                    blocked_task = next((t for t in tasks if t.id == blocked_id), None)
                    if blocked_task:
                        queue.append(blocked_task)
            
            # Re-sort queue (new tasks might have been added)
            queue.sort(key=lambda t: t.created_at)
        
        # Handle cycles (tasks that couldn't be ordered due to circular dependencies)
        remaining = [task for task in tasks if task not in result]
        result.extend(remaining)
        
        return result


# Singleton instance
_workflow_intelligence_instance: Optional[WorkflowIntelligence] = None


def get_workflow_intelligence() -> WorkflowIntelligence:
    """
    Get the singleton instance of WorkflowIntelligence.
    """
    global _workflow_intelligence_instance
    if _workflow_intelligence_instance is None:
        _workflow_intelligence_instance = WorkflowIntelligence()
    return _workflow_intelligence_instance

