"""
Code Review Pattern

Implements the code review workflow between developers and tech lead:
1. Developer completes implementation and requests review
2. Tech Lead reviews code with feedback
3. Developer addresses feedback
4. Iterate until approved
5. Move to QA testing
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.communication.message_bus import MessageBus
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService
from backend.schemas.agent_message import CodeReviewRequest, CodeReviewResponse


class CodeReviewPattern:
    """
    Code Review Collaboration Pattern

    Workflow:
    1. Developer requests review from Tech Lead
    2. Tech Lead conducts review (quality, performance, security, tests)
    3. Tech Lead provides feedback (approved/changes_requested/commented)
    4. If changes requested, developer addresses and re-submits
    5. Once approved, move to testing phase
    """

    def __init__(self, message_bus: MessageBus):
        """
        Initialize code review pattern

        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus

    async def request_review(
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
            self_review_notes: Optional self-review notes

        Returns:
            Review request ID
        """
        # Get developer details
        developer = await AgentService.get_squad_member(db, developer_id)
        if not developer:
            raise ValueError(f"Developer {developer_id} not found")

        # Get tech lead details
        tech_lead = await AgentService.get_squad_member(db, tech_lead_id)
        if not tech_lead:
            raise ValueError(f"Tech Lead {tech_lead_id} not found")

        # Format review request
        request_content = f"""
**Code Review Request from {developer.role}**

**Pull Request**: {pr_url}

**Description**:
{pr_description}

**Changes Summary**:
{changes_summary}

{f'**Self-Review Notes**:{chr(10)}{self_review_notes}' if self_review_notes else ''}

**Checklist for Review**:
- [ ] Code quality (clean, readable, maintainable)
- [ ] Best practices followed
- [ ] Performance considerations
- [ ] Security considerations
- [ ] Tests included and passing
- [ ] Documentation updated
- [ ] Acceptance criteria met
        """

        # Create review request ID
        review_id = f"review_{task_execution_id}_{developer_id}_{datetime.utcnow().timestamp()}"

        # Send to Tech Lead
        await self.message_bus.send_message(
            sender_id=developer_id,
            recipient_id=tech_lead_id,
            content=request_content,
            message_type="code_review_request",
            metadata={
                "review_id": review_id,
                "pr_url": pr_url,
                "changes_summary": changes_summary,
            },
            task_execution_id=task_execution_id,
        )

        # Log the request
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message=f"{developer.role} requested code review from {tech_lead.role}",
            metadata={
                "review_id": review_id,
                "pr_url": pr_url,
            },
        )

        return review_id

    async def conduct_review(
        self,
        db: AsyncSession,
        tech_lead_id: UUID,
        review_id: str,
        task_execution_id: UUID,
        code_diff: str,
        pr_description: str,
        acceptance_criteria: List[str],
    ) -> Dict[str, Any]:
        """
        Tech Lead conducts code review.

        Args:
            db: Database session
            tech_lead_id: Tech Lead agent ID
            review_id: Review request ID
            task_execution_id: Task execution ID
            code_diff: Git diff of changes
            pr_description: PR description
            acceptance_criteria: Original acceptance criteria

        Returns:
            Review result with approval status and comments
        """
        # Get Tech Lead agent
        tech_lead_agent = await AgentService.get_or_create_agent(db, tech_lead_id)

        # Conduct review using Tech Lead's review_code method
        review_result = await tech_lead_agent.review_code(
            code_diff=code_diff,
            pr_description=pr_description,
            acceptance_criteria=acceptance_criteria,
        )

        # Log the review
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message=f"Code review completed: {review_result.get('approval_status', 'unknown')}",
            metadata={
                "review_id": review_id,
                "approval_status": review_result.get("approval_status"),
                "comment_count": len(review_result.get("comments", [])),
            },
        )

        return review_result

    async def provide_feedback(
        self,
        db: AsyncSession,
        tech_lead_id: UUID,
        developer_id: UUID,
        task_execution_id: UUID,
        review_id: str,
        review_result: Dict[str, Any],
    ) -> None:
        """
        Tech Lead provides feedback to developer.

        Args:
            db: Database session
            tech_lead_id: Tech Lead agent ID
            developer_id: Developer agent ID
            task_execution_id: Task execution ID
            review_id: Review request ID
            review_result: Review result from conduct_review
        """
        approval_status = review_result.get("approval_status", "commented")
        comments = review_result.get("comments", [])
        summary = review_result.get("summary", "")

        # Format feedback
        feedback_content = f"""
**Code Review Feedback**

**Status**: {approval_status.upper()}

**Summary**:
{summary}

**Specific Comments** ({len(comments)} comments):
{chr(10).join([f'- {c}' for c in comments[:10]])}  # Limit to 10

**Next Steps**:
"""

        if approval_status == "approved":
            feedback_content += """
✅ Code approved! Ready for QA testing.
- All quality standards met
- Tests passing
- Documentation updated
"""
        elif approval_status == "changes_requested":
            feedback_content += """
⚠️ Changes requested before approval.
- Please address the comments above
- Update tests if needed
- Request re-review when ready
"""
        else:
            feedback_content += """
💬 Comments provided for consideration.
- Review the feedback
- Implement if you agree
- Let me know if you have questions
"""

        # Send feedback to developer
        await self.message_bus.send_message(
            sender_id=tech_lead_id,
            recipient_id=developer_id,
            content=feedback_content,
            message_type="code_review_response",
            metadata={
                "review_id": review_id,
                "approval_status": approval_status,
                "comment_count": len(comments),
            },
            task_execution_id=task_execution_id,
        )

        # Log feedback sent
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message=f"Review feedback sent to developer: {approval_status}",
            metadata={
                "review_id": review_id,
                "approval_status": approval_status,
            },
        )

    async def address_feedback(
        self,
        db: AsyncSession,
        developer_id: UUID,
        task_execution_id: UUID,
        review_feedback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Developer creates action plan to address review feedback.

        Args:
            db: Database session
            developer_id: Developer agent ID
            task_execution_id: Task execution ID
            review_feedback: Feedback from Tech Lead

        Returns:
            Action plan for addressing feedback
        """
        # Get developer agent
        developer_agent = await AgentService.get_or_create_agent(db, developer_id)

        # Create action plan using developer's respond_to_review_feedback method
        action_plan = await developer_agent.respond_to_review_feedback(
            review_feedback=review_feedback,
            task_id=str(task_execution_id),
        )

        # Log action plan
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message="Developer created action plan to address review feedback",
            metadata={
                "approval_status": review_feedback.get("approval_status"),
            },
        )

        return {
            "action_plan": action_plan.content,
            "estimated_time": self._extract_estimated_time(action_plan.content),
            "next_steps": self._extract_next_steps(action_plan.content),
        }

    async def approve_and_move_forward(
        self,
        db: AsyncSession,
        task_execution_id: UUID,
        review_id: str,
    ) -> None:
        """
        Approve code and prepare for next phase (QA testing).

        Args:
            db: Database session
            task_execution_id: Task execution ID
            review_id: Review request ID
        """
        # Log approval
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message="Code review approved, ready for QA testing",
            metadata={
                "review_id": review_id,
                "next_phase": "testing",
            },
        )

    async def complete_review_cycle(
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
        Complete one cycle of code review: request → review → feedback.

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
            acceptance_criteria: Acceptance criteria to verify
            self_review_notes: Optional self-review notes

        Returns:
            Complete review result with approval status and action plan
        """
        # Step 1: Request review
        review_id = await self.request_review(
            db=db,
            developer_id=developer_id,
            tech_lead_id=tech_lead_id,
            task_execution_id=task_execution_id,
            pr_url=pr_url,
            pr_description=pr_description,
            changes_summary=changes_summary,
            self_review_notes=self_review_notes,
        )

        # Step 2: Conduct review
        review_result = await self.conduct_review(
            db=db,
            tech_lead_id=tech_lead_id,
            review_id=review_id,
            task_execution_id=task_execution_id,
            code_diff=code_diff,
            pr_description=pr_description,
            acceptance_criteria=acceptance_criteria,
        )

        # Step 3: Provide feedback
        await self.provide_feedback(
            db=db,
            tech_lead_id=tech_lead_id,
            developer_id=developer_id,
            task_execution_id=task_execution_id,
            review_id=review_id,
            review_result=review_result,
        )

        # Step 4: Developer addresses feedback (if changes requested)
        action_plan = None
        if review_result.get("approval_status") == "changes_requested":
            action_plan = await self.address_feedback(
                db=db,
                developer_id=developer_id,
                task_execution_id=task_execution_id,
                review_feedback=review_result,
            )

        # Step 5: If approved, move forward
        if review_result.get("approval_status") == "approved":
            await self.approve_and_move_forward(
                db=db,
                task_execution_id=task_execution_id,
                review_id=review_id,
            )

        return {
            "review_id": review_id,
            "approval_status": review_result.get("approval_status"),
            "summary": review_result.get("summary"),
            "comments": review_result.get("comments", []),
            "action_plan": action_plan,
            "approved": review_result.get("approval_status") == "approved",
            "needs_rework": review_result.get("approval_status") == "changes_requested",
        }

    # Helper methods

    def _extract_estimated_time(self, content: str) -> Optional[str]:
        """Extract estimated time from action plan"""
        import re
        pattern = r"estimated time[:\s]+([\w\s]+)"
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_next_steps(self, content: str) -> List[str]:
        """Extract next steps from action plan"""
        lines = content.split('\n')
        in_section = False
        steps = []

        for line in lines:
            if 'next steps' in line.lower() or 'action plan' in line.lower():
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                steps.append(line.strip()[1:].strip())
            elif in_section and line.strip() and not line.strip().startswith('-'):
                if line.strip().startswith('#'):
                    break

        return steps[:5]  # Max 5 steps
