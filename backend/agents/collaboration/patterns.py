"""
Collaboration Pattern Manager

Central manager for all agent collaboration patterns.
Provides unified interface for problem solving, code review, and standups.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.communication.message_bus import MessageBus
from backend.agents.context.context_manager import ContextManager
from backend.agents.collaboration.problem_solving import ProblemSolvingPattern
from backend.agents.collaboration.code_review import CodeReviewPattern
from backend.agents.collaboration.standup import StandupPattern


class CollaborationPatternManager:
    """
    Collaboration Pattern Manager

    Provides unified access to all collaboration patterns:
    - Problem Solving: Collaborative Q&A and troubleshooting
    - Code Review: Developer ↔ Tech Lead review cycles
    - Standup: Daily progress updates and coordination

    This is the main interface for agent collaboration.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        context_manager: ContextManager,
    ):
        """
        Initialize collaboration pattern manager

        Args:
            message_bus: Message bus for agent communication
            context_manager: Context manager for RAG/memory
        """
        self.message_bus = message_bus
        self.context_manager = context_manager

        # Initialize patterns
        self.problem_solving = ProblemSolvingPattern(message_bus, context_manager)
        self.code_review = CodeReviewPattern(message_bus)
        self.standup = StandupPattern(message_bus)

    # Problem Solving Pattern Methods

    async def ask_team_for_help(
        self,
        db: AsyncSession,
        asker_id: UUID,
        task_execution_id: UUID,
        question: str,
        context: Dict[str, Any],
        relevant_roles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Agent asks team for help with a problem.

        This is the main entry point for collaborative problem solving.

        Args:
            db: Database session
            asker_id: Agent asking for help
            task_execution_id: Task execution ID
            question: Question text
            context: Context with issue_description, attempted_solutions, why_stuck
            relevant_roles: Optional list of relevant roles

        Returns:
            Solution synthesized from team responses
        """
        return await self.problem_solving.solve_problem_collaboratively(
            db=db,
            asker_id=asker_id,
            task_execution_id=task_execution_id,
            question=question,
            context=context,
            relevant_roles=relevant_roles,
        )

    async def broadcast_question(
        self,
        db: AsyncSession,
        asker_id: UUID,
        task_execution_id: UUID,
        question: str,
        context: Dict[str, Any],
        relevant_roles: Optional[List[str]] = None,
    ) -> str:
        """
        Broadcast question to team (async, returns question ID for tracking).

        Args:
            db: Database session
            asker_id: Agent asking
            task_execution_id: Task execution ID
            question: Question text
            context: Question context
            relevant_roles: Optional relevant roles

        Returns:
            Question ID
        """
        return await self.problem_solving.broadcast_question(
            db=db,
            asker_id=asker_id,
            task_execution_id=task_execution_id,
            question=question,
            context=context,
            relevant_roles=relevant_roles,
        )

    async def collect_and_synthesize_answers(
        self,
        db: AsyncSession,
        asker_id: UUID,
        task_execution_id: UUID,
        question_id: str,
        question: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Collect answers and synthesize solution.

        Args:
            db: Database session
            asker_id: Agent who asked
            task_execution_id: Task execution ID
            question_id: Question ID
            question: Original question
            context: Question context

        Returns:
            Synthesized solution
        """
        answers = await self.problem_solving.collect_answers(
            db=db,
            task_execution_id=task_execution_id,
            question_id=question_id,
        )

        if not answers:
            return {
                "question": question,
                "answer_count": 0,
                "recommendation": "No responses received",
            }

        return await self.problem_solving.synthesize_solution(
            db=db,
            asker_id=asker_id,
            question=question,
            answers=answers,
            context=context,
        )

    # Code Review Pattern Methods

    async def request_code_review(
        self,
        db: AsyncSession,
        developer_id: UUID,
        tech_lead_id: UUID,
        task_execution_id: UUID,
        pr_url: str,
        pr_description: str,
        changes_summary: str,
        self_review_notes: Optional[str] = None,
    ) -> str:
        """
        Developer requests code review from Tech Lead.

        Args:
            db: Database session
            developer_id: Developer agent ID
            tech_lead_id: Tech Lead agent ID
            task_execution_id: Task execution ID
            pr_url: Pull request URL
            pr_description: PR description
            changes_summary: Summary of changes
            self_review_notes: Optional self-review

        Returns:
            Review request ID
        """
        return await self.code_review.request_review(
            db=db,
            developer_id=developer_id,
            tech_lead_id=tech_lead_id,
            task_execution_id=task_execution_id,
            pr_url=pr_url,
            pr_description=pr_description,
            changes_summary=changes_summary,
            self_review_notes=self_review_notes,
        )

    async def complete_code_review_cycle(
        self,
        db: AsyncSession,
        developer_id: UUID,
        tech_lead_id: UUID,
        task_execution_id: UUID,
        pr_url: str,
        pr_description: str,
        changes_summary: str,
        code_diff: str,
        acceptance_criteria: List[str],
        self_review_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete full code review cycle: request → review → feedback → action plan.

        This is the main entry point for code review collaboration.

        Args:
            db: Database session
            developer_id: Developer agent ID
            tech_lead_id: Tech Lead agent ID
            task_execution_id: Task execution ID
            pr_url: Pull request URL
            pr_description: PR description
            changes_summary: Summary of changes
            code_diff: Git diff
            acceptance_criteria: Acceptance criteria
            self_review_notes: Optional self-review

        Returns:
            Complete review result with approval status
        """
        return await self.code_review.complete_review_cycle(
            db=db,
            developer_id=developer_id,
            tech_lead_id=tech_lead_id,
            task_execution_id=task_execution_id,
            pr_url=pr_url,
            pr_description=pr_description,
            changes_summary=changes_summary,
            code_diff=code_diff,
            acceptance_criteria=acceptance_criteria,
            self_review_notes=self_review_notes,
        )

    # Standup Pattern Methods

    async def conduct_daily_standup(
        self,
        db: AsyncSession,
        pm_id: UUID,
        squad_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Conduct daily standup: request updates → collect → analyze → broadcast.

        This is the main entry point for standup collaboration.

        Args:
            db: Database session
            pm_id: PM agent ID
            squad_id: Squad ID
            task_execution_id: Optional task execution ID

        Returns:
            Standup results with analysis
        """
        return await self.standup.conduct_standup(
            db=db,
            pm_id=pm_id,
            squad_id=squad_id,
            task_execution_id=task_execution_id,
        )

    async def request_standup_updates(
        self,
        db: AsyncSession,
        pm_id: UUID,
        squad_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> str:
        """
        PM requests standup updates from team (async, returns standup ID).

        Args:
            db: Database session
            pm_id: PM agent ID
            squad_id: Squad ID
            task_execution_id: Optional task execution ID

        Returns:
            Standup session ID
        """
        return await self.standup.request_updates(
            db=db,
            pm_id=pm_id,
            squad_id=squad_id,
            task_execution_id=task_execution_id,
        )

    async def analyze_standup_updates(
        self,
        db: AsyncSession,
        pm_id: UUID,
        task_execution_id: UUID,
        standup_id: str,
    ) -> Dict[str, Any]:
        """
        Collect and analyze standup updates.

        Args:
            db: Database session
            pm_id: PM agent ID
            task_execution_id: Task execution ID
            standup_id: Standup session ID

        Returns:
            Analysis with blockers, at-risk members, action items
        """
        updates = await self.standup.collect_updates(
            db=db,
            task_execution_id=task_execution_id,
            standup_id=standup_id,
        )

        if not updates:
            return {
                "standup_id": standup_id,
                "status": "no_updates",
                "message": "No updates received yet",
            }

        return await self.standup.analyze_updates(
            db=db,
            pm_id=pm_id,
            updates=updates,
        )

    # Utility Methods

    async def get_collaboration_summary(
        self,
        db: AsyncSession,
        task_execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get summary of all collaboration activities for a task.

        Args:
            db: Database session
            task_execution_id: Task execution ID

        Returns:
            Collaboration summary
        """
        from backend.services.task_execution_service import TaskExecutionService

        messages = await TaskExecutionService.get_execution_messages(
            db, task_execution_id
        )

        # Count message types
        message_counts = {}
        for msg in messages:
            msg_type = msg.message_type
            message_counts[msg_type] = message_counts.get(msg_type, 0) + 1

        return {
            "total_messages": len(messages),
            "message_types": message_counts,
            "questions_asked": message_counts.get("question", 0),
            "answers_provided": message_counts.get("answer", 0),
            "code_reviews": message_counts.get("code_review_request", 0),
            "standups": message_counts.get("standup", 0),
            "status_updates": message_counts.get("status_update", 0),
        }
