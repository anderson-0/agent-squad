"""
Discovery Engine for Stream D

Advanced discovery system that analyzes agent work context, evaluates discovery value,
and generates task suggestions. Builds on the basic DiscoveryDetector from Stream B.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.message import AgentMessage
from backend.models.project import TaskExecution
from backend.agents.discovery.discovery_detector import DiscoveryDetector, Discovery, get_discovery_detector
from backend.agents.task_spawning import AgentTaskSpawner, get_agent_task_spawner

logger = logging.getLogger(__name__)


class TaskSuggestion(BaseModel):
    """Suggestion for a task to spawn based on a discovery"""
    title: str
    description: str
    phase: WorkflowPhase
    rationale: str
    estimated_value: float  # 0.0-1.0
    priority: str  # "low", "medium", "high", "urgent"
    blocking_task_ids: List[UUID] = []


class WorkContext:
    """Context about agent's work for analysis"""
    def __init__(
        self,
        execution_id: UUID,
        agent_id: UUID,
        phase: WorkflowPhase,
        recent_messages: List[AgentMessage],
        recent_tasks: List[DynamicTask],
        work_output: Optional[str] = None,
    ):
        self.execution_id = execution_id
        self.agent_id = agent_id
        self.phase = phase
        self.recent_messages = recent_messages
        self.recent_tasks = recent_tasks
        self.work_output = work_output


class DiscoveryEngine:
    """
    Advanced discovery engine that analyzes work context and generates task suggestions.
    
    Builds on DiscoveryDetector (Stream B) with:
    - Context-aware analysis
    - Advanced value scoring
    - Task suggestion generation
    - Integration with workflow
    """
    
    def __init__(self):
        """Initialize discovery engine"""
        self.detector = get_discovery_detector()
        self.task_spawner = get_agent_task_spawner()
    
    async def analyze_work_context(
        self,
        db: AsyncSession,
        context: WorkContext,
    ) -> List[Discovery]:
        """
        Analyze agent work context for discoveries.
        
        This is more sophisticated than basic detection - it considers:
        - Recent agent messages
        - Recent tasks spawned
        - Current phase context
        - Work output
        
        Args:
            db: Database session
            context: Work context to analyze
            
        Returns:
            List of discoveries found
        """
        discoveries = []
        
        # Analyze recent messages
        for message in context.recent_messages[:10]:  # Last 10 messages
            discovery = self.detector.analyze_agent_message(
                message=message,
                context={"execution_id": str(context.execution_id), "phase": context.phase.value},
            )
            if discovery:
                # Enhance discovery with context
                discovery = self._enhance_discovery_with_context(discovery, context)
                discoveries.append(discovery)
        
        # Analyze work output if available
        if context.work_output:
            work_discoveries = self.detector.analyze_agent_work(
                work_output=context.work_output,
                phase=context.phase,
                context={"execution_id": str(context.execution_id)},
            )
            for discovery in work_discoveries:
                discovery = self._enhance_discovery_with_context(discovery, context)
                discoveries.append(discovery)
        
        # Analyze task patterns (if many tasks in one phase, might indicate discovery opportunity)
        discoveries.extend(await self._analyze_task_patterns(db, context))
        
        # Deduplicate and rank by value
        unique_discoveries = self._deduplicate_discoveries(discoveries)
        return sorted(unique_discoveries, key=lambda d: d.value_score, reverse=True)
    
    async def evaluate_discovery_value(
        self,
        db: AsyncSession,
        discovery: Discovery,
        context: WorkContext,
    ) -> float:
        """
        Evaluate the value of a discovery more accurately.
        
        Uses context-aware scoring:
        - Impact on current workflow
        - Number of tasks/routes affected
        - Phase appropriateness
        - Historical success of similar discoveries
        
        Args:
            db: Database session
            discovery: Discovery to evaluate
            context: Work context
            
        Returns:
            Value score 0.0-1.0 (updated)
        """
        base_score = discovery.value_score
        
        # Boost if discovery type matches current phase
        if discovery.suggested_phase == context.phase:
            base_score = min(base_score * 1.15, 1.0)
        
        # Boost if description contains specific impact metrics
        description_lower = discovery.description.lower()
        
        # Check for impact indicators
        if any(indicator in description_lower for indicator in [
            "apply to", "affects", "impacts", "benefits",
            "improves", "reduces", "increases",
        ]):
            base_score = min(base_score * 1.1, 1.0)
        
        # Check for number indicators (e.g., "12 routes", "40% speedup")
        import re
        number_match = re.search(r'(\d+).*(?:route|endpoint|function|method|%|times)', description_lower)
        if number_match:
            # Boost based on numbers mentioned
            base_score = min(base_score * 1.05, 1.0)
        
        # Reduce score if discovery is too vague
        if len(discovery.description) < 30:
            base_score = base_score * 0.9
        
        # Boost confidence-weighted score
        confidence_weighted = base_score * discovery.confidence
        
        return min(confidence_weighted, 1.0)
    
    async def suggest_task_from_discovery(
        self,
        db: AsyncSession,
        discovery: Discovery,
        context: WorkContext,
    ) -> TaskSuggestion:
        """
        Generate a task suggestion from a discovery.
        
        Creates a TaskSuggestion with:
        - Appropriate title and description
        - Phase recommendation
        - Rationale
        - Priority based on value
        
        Args:
            db: Database session
            discovery: Discovery to convert to task
            context: Work context
            
        Returns:
            TaskSuggestion ready to spawn
        """
        # Generate title from discovery
        title = self._generate_task_title(discovery)
        
        # Generate description
        description = self._generate_task_description(discovery, context)
        
        # Determine phase (use discovery's suggestion or context phase)
        phase = discovery.suggested_phase if discovery.suggested_phase else context.phase
        
        # Generate rationale
        rationale = self._generate_rationale(discovery, context)
        
        # Determine priority based on value score
        priority = self._determine_priority(discovery.value_score)
        
        # Check for blocking dependencies (simplified - can enhance later)
        blocking_task_ids = await self._find_blocking_tasks(db, context, discovery)
        
        return TaskSuggestion(
            title=title,
            description=description,
            phase=phase,
            rationale=rationale,
            estimated_value=discovery.value_score,
            priority=priority,
            blocking_task_ids=blocking_task_ids,
        )
    
    async def discover_and_suggest_tasks(
        self,
        db: AsyncSession,
        context: WorkContext,
        min_value_threshold: float = 0.5,
    ) -> List[TaskSuggestion]:
        """
        Complete flow: discover opportunities and generate task suggestions.
        
        This is the main method that combines discovery + evaluation + suggestion.
        
        Args:
            db: Database session
            context: Work context to analyze
            min_value_threshold: Minimum value score to include (default 0.5)
            
        Returns:
            List of task suggestions (sorted by value)
        """
        # Discover opportunities
        discoveries = await self.analyze_work_context(db, context)
        
        # Evaluate and filter by value
        valuable_discoveries = []
        for discovery in discoveries:
            evaluated_value = await self.evaluate_discovery_value(db, discovery, context)
            if evaluated_value >= min_value_threshold:
                # Update discovery with evaluated value
                discovery.value_score = evaluated_value
                valuable_discoveries.append(discovery)
        
        # Generate task suggestions
        suggestions = []
        for discovery in valuable_discoveries:
            suggestion = await self.suggest_task_from_discovery(db, discovery, context)
            suggestions.append(suggestion)
        
        # Sort by estimated value
        return sorted(suggestions, key=lambda s: s.estimated_value, reverse=True)
    
    def _enhance_discovery_with_context(
        self,
        discovery: Discovery,
        context: WorkContext,
    ) -> Discovery:
        """Enhance discovery with work context"""
        # Add context to discovery
        discovery.context.update({
            "execution_id": str(context.execution_id),
            "agent_id": str(context.agent_id),
            "current_phase": context.phase.value,
            "message_count": len(context.recent_messages),
            "task_count": len(context.recent_tasks),
        })
        
        return discovery
    
    async def _analyze_task_patterns(
        self,
        db: AsyncSession,
        context: WorkContext,
    ) -> List[Discovery]:
        """Analyze task patterns for discovery opportunities"""
        discoveries = []
        
        # If many tasks in one phase, might indicate opportunity
        if len(context.recent_tasks) >= 5:
            phase_counts = {}
            for task in context.recent_tasks:
                phase_counts[task.phase] = phase_counts.get(task.phase, 0) + 1
            
            # If >70% of tasks in one phase, might indicate imbalance
            total_tasks = len(context.recent_tasks)
            for phase, count in phase_counts.items():
                if count / total_tasks > 0.7:
                    discoveries.append(Discovery(
                        type="workflow_balance",
                        description=f"Workflow imbalance detected: {count}/{total_tasks} tasks in {phase} phase",
                        value_score=0.6,
                        suggested_phase=WorkflowPhase.INVESTIGATION,
                        confidence=0.7,
                        context={"pattern": "phase_imbalance"},
                    ))
        
        return discoveries
    
    def _deduplicate_discoveries(self, discoveries: List[Discovery]) -> List[Discovery]:
        """Remove duplicate discoveries, keeping highest value"""
        seen = {}
        for discovery in discoveries:
            # Create key from type + description hash
            key = f"{discovery.type}:{hash(discovery.description[:50])}"
            
            if key not in seen:
                seen[key] = discovery
            else:
                # Keep the one with higher value
                if discovery.value_score > seen[key].value_score:
                    seen[key] = discovery
        
        return list(seen.values())
    
    def _generate_task_title(self, discovery: Discovery) -> str:
        """Generate task title from discovery"""
        # Extract key phrase from description
        description = discovery.description
        
        # Try to extract a concise title (first 60 chars or first sentence)
        if len(description) <= 60:
            return description.capitalize()
        
        # Take first sentence
        sentences = description.split('.')
        if sentences:
            title = sentences[0].strip()
            if len(title) > 60:
                title = title[:57] + "..."
            return title.capitalize()
        
        return description[:60].capitalize()
    
    def _generate_task_description(
        self,
        discovery: Discovery,
        context: WorkContext,
    ) -> str:
        """Generate detailed task description"""
        description = discovery.description
        
        # Add context if available
        if discovery.context:
            context_info = []
            if "message_id" in discovery.context:
                context_info.append(f"Discovered in message {discovery.context['message_id'][:8]}")
            if "current_phase" in discovery.context:
                context_info.append(f"Current phase: {discovery.context['current_phase']}")
            
            if context_info:
                description += f"\n\nContext: {', '.join(context_info)}"
        
        return description
    
    def _generate_rationale(
        self,
        discovery: Discovery,
        context: WorkContext,
    ) -> str:
        """Generate rationale for task"""
        rationale = f"Discovered {discovery.type} opportunity"
        
        if discovery.value_score >= 0.8:
            rationale += " with high potential value"
        elif discovery.value_score >= 0.6:
            rationale += " with moderate value"
        
        rationale += f" during {context.phase.value} phase"
        
        return rationale
    
    def _determine_priority(self, value_score: float) -> str:
        """Determine priority from value score"""
        if value_score >= 0.8:
            return "high"
        elif value_score >= 0.6:
            return "medium"
        elif value_score >= 0.4:
            return "low"
        else:
            return "low"
    
    async def _find_blocking_tasks(
        self,
        db: AsyncSession,
        context: WorkContext,
        discovery: Discovery,
    ) -> List[UUID]:
        """Find tasks that should block this new task"""
        # Simplified - can enhance with more logic later
        # For investigation tasks, might need to wait for current tasks
        if discovery.suggested_phase == WorkflowPhase.INVESTIGATION:
            # Check if there are in-progress investigation tasks
            in_progress_investigation = [
                t.id for t in context.recent_tasks
                if t.phase == WorkflowPhase.INVESTIGATION.value
                and t.status == "in_progress"
            ]
            return in_progress_investigation[:2]  # Limit to 2 blockers
        
        return []


# Singleton instance
_discovery_engine: Optional[DiscoveryEngine] = None


def get_discovery_engine() -> DiscoveryEngine:
    """Get or create discovery engine instance"""
    global _discovery_engine
    if _discovery_engine is None:
        _discovery_engine = DiscoveryEngine()
    return _discovery_engine

