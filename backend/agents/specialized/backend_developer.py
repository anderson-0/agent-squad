"""
Backend Developer Agent

The Backend Developer agent implements backend features, writes tests,
creates pull requests, and collaborates with the team on technical tasks.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.base_agent import BaseSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    StatusUpdate,
    Question,
    CodeReviewRequest,
    TaskCompletion,
)


class BackendDeveloperAgent(BaseSquadAgent):
    """
    Backend Developer Agent - Implementation Specialist

    Responsibilities:
    - Implement backend features (APIs, services, database)
    - Write unit and integration tests
    - Create pull requests
    - Ask technical questions when blocked
    - Follow best practices and patterns
    - Update documentation
    - Collaborate with team on technical issues

    Note: In Phase 4, this agent will use MCP servers to actually
    read/write code. For Phase 3, it plans and provides guidance.
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of Backend Developer capabilities

        Returns:
            List of capability names
        """
        return [
            "analyze_task",
            "plan_implementation",
            "write_code",  # Phase 4: via MCP
            "write_tests",  # Phase 4: via MCP
            "create_pull_request",  # Phase 4: via MCP
            "ask_question",
            "provide_status_update",
            "request_code_review",
            "respond_to_review_feedback",
            "update_documentation",
            "troubleshoot_issue",
        ]

    async def analyze_task(
        self,
        task_assignment: Dict[str, Any],
        code_context: Optional[str] = None,
    ) -> AgentResponse:
        """
        Analyze assigned task and create implementation plan.

        Args:
            task_assignment: Task assignment from PM
            code_context: Relevant code from RAG

        Returns:
            AgentResponse with analysis and plan
        """
        context = {
            "task": task_assignment,
            "code_context": code_context,
            "action": "task_analysis"
        }

        code_info = ""
        if code_context:
            code_info = f"""
            Relevant Existing Code:
            {code_context[:2000]}
            """

        prompt = f"""
        You've been assigned a backend development task:

        Task: {task_assignment.get('description')}
        Acceptance Criteria:
        {chr(10).join([f'- {c}' for c in task_assignment.get('acceptance_criteria', [])])}

        Dependencies: {task_assignment.get('dependencies', [])}
        Estimated Hours: {task_assignment.get('estimated_hours', 'N/A')}

        Context:
        {task_assignment.get('context', 'N/A')}
        {code_info}

        Please analyze and create an implementation plan:

        1. **Understanding**:
           - Summarize what needs to be built
           - Identify key requirements

        2. **Technical Approach**:
           - Which files/modules to modify/create
           - Design patterns to use
           - Database changes needed (if any)
           - API endpoints to create/modify

        3. **Implementation Steps**:
           - Step-by-step breakdown
           - Order of implementation
           - Testing approach

        4. **Questions/Clarifications**:
           - What's unclear?
           - What do you need from Tech Lead?
           - Any risks or concerns?

        5. **Estimated Time**:
           - Breakdown by step
           - Buffer for unknowns

        Be specific and actionable.
        """

        return await self.process_message(prompt, context=context)

    async def plan_implementation(
        self,
        task: Dict[str, Any],
        architecture_guidance: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create detailed implementation plan.

        Args:
            task: Task details
            architecture_guidance: Optional guidance from Tech Lead

        Returns:
            Dictionary with implementation plan
        """
        context = {
            "task": task,
            "architecture_guidance": architecture_guidance,
            "action": "implementation_planning"
        }

        guidance_info = ""
        if architecture_guidance:
            guidance_info = f"""
            Tech Lead Guidance:
            {architecture_guidance}
            """

        prompt = f"""
        Create a detailed implementation plan:

        Task: {task.get('description')}
        {guidance_info}

        Please provide:

        1. **Files to Create/Modify**:
           - List each file with purpose
           - Estimate lines of code

        2. **Database Changes** (if any):
           - Models to add/modify
           - Migrations needed
           - Indexes to create

        3. **API Endpoints** (if any):
           - Route definitions
           - Request/response schemas
           - Validation rules

        4. **Business Logic**:
           - Service layer methods
           - Key algorithms
           - Edge cases to handle

        5. **Testing Strategy**:
           - Unit tests needed
           - Integration tests needed
           - Test data requirements

        6. **Dependencies**:
           - New packages needed
           - Services to integrate with

        7. **Implementation Order**:
           - Step 1, 2, 3...
           - Why this order?

        8. **Definition of Done**:
           - All tests passing
           - Code reviewed
           - Documentation updated
           - Ready for deployment

        Be thorough and specific.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "implementation_plan": response.content,
            "files_affected": self._extract_files(response.content),
            "estimated_loc": self._estimate_loc(response.content),
            "dependencies": self._extract_dependencies(response.content),
        }

    async def ask_question(
        self,
        question: str,
        task_id: str,
        context: Dict[str, Any],
        recipient_role: Optional[str] = None,
    ) -> Question:
        """
        Ask a technical question to Tech Lead or team.

        Args:
            question: The question
            task_id: Current task ID
            context: Question context
            recipient_role: Target role (tech_lead, pm, etc.) or None for broadcast

        Returns:
            Question message
        """
        # In Phase 3, we prepare the question
        # In Phase 4, this will be sent via message bus

        recipient_id = None
        if recipient_role:
            # Would look up agent by role
            recipient_id = context.get(f'{recipient_role}_id')

        return Question(
            task_id=task_id,
            question=question,
            context=str(context),
            recipient=UUID(recipient_id) if recipient_id else None,
            urgency=context.get('urgency', 'normal'),
        )

    async def provide_status_update(
        self,
        task_id: str,
        status: str,
        progress_percentage: int,
        details: str,
        blockers: Optional[List[str]] = None,
        next_steps: Optional[str] = None,
    ) -> StatusUpdate:
        """
        Provide status update to PM.

        Args:
            task_id: Task identifier
            status: Current status
            progress_percentage: Progress (0-100)
            details: Status details
            blockers: Optional list of blockers
            next_steps: Optional next steps

        Returns:
            StatusUpdate message
        """
        return StatusUpdate(
            task_id=task_id,
            status=status,
            progress_percentage=progress_percentage,
            details=details,
            blockers=blockers or [],
            next_steps=next_steps,
        )

    async def request_code_review(
        self,
        task_id: str,
        pr_url: str,
        description: str,
        changes_summary: str,
        tech_lead_id: UUID,
        self_review_notes: Optional[str] = None,
    ) -> CodeReviewRequest:
        """
        Request code review from Tech Lead.

        Args:
            task_id: Task identifier
            pr_url: Pull request URL
            description: PR description
            changes_summary: Summary of changes
            tech_lead_id: Tech Lead agent ID
            self_review_notes: Optional self-review notes

        Returns:
            CodeReviewRequest message
        """
        return CodeReviewRequest(
            recipient=tech_lead_id,
            task_id=task_id,
            pull_request_url=pr_url,
            description=description,
            changes_summary=changes_summary,
            self_review_notes=self_review_notes,
        )

    async def respond_to_review_feedback(
        self,
        review_feedback: Dict[str, Any],
        task_id: str,
    ) -> AgentResponse:
        """
        Process code review feedback and plan fixes.

        Args:
            review_feedback: Feedback from Tech Lead
            task_id: Task identifier

        Returns:
            AgentResponse with action plan
        """
        context = {
            "review_feedback": review_feedback,
            "task_id": task_id,
            "action": "respond_to_feedback"
        }

        approval_status = review_feedback.get('approval_status')
        comments = review_feedback.get('comments', [])
        summary = review_feedback.get('summary', '')

        comments_str = "\n".join([
            f"- {c.get('file')}:{c.get('line')} - {c.get('comment')}"
            for c in comments
        ])

        prompt = f"""
        Code review feedback received:

        Status: {approval_status}
        Summary: {summary}

        Specific Comments:
        {comments_str}

        Please analyze and respond:

        1. **Understanding Feedback**:
           - Summarize the key issues
           - Prioritize by importance

        2. **Action Plan**:
           - How to address each comment
           - Changes needed
           - Estimated time to fix

        3. **Questions** (if any):
           - Need clarification on any feedback?

        4. **Response**:
           - Draft response to reviewer
           - Professional and constructive

        Show you understand the feedback and have a plan.
        """

        return await self.process_message(prompt, context=context)

    async def troubleshoot_issue(
        self,
        issue_description: str,
        error_message: Optional[str] = None,
        code_context: Optional[str] = None,
    ) -> AgentResponse:
        """
        Troubleshoot a technical issue.

        Args:
            issue_description: Description of the issue
            error_message: Optional error message
            code_context: Optional relevant code

        Returns:
            AgentResponse with troubleshooting analysis
        """
        context = {
            "issue": issue_description,
            "error": error_message,
            "code": code_context,
            "action": "troubleshooting"
        }

        error_info = ""
        if error_message:
            error_info = f"""
            Error Message:
            {error_message}
            """

        code_info = ""
        if code_context:
            code_info = f"""
            Relevant Code:
            {code_context[:1000]}
            """

        prompt = f"""
        Troubleshoot this issue:

        Issue: {issue_description}
        {error_info}
        {code_info}

        Please analyze:

        1. **Root Cause**:
           - What's causing this?
           - Why is it happening?

        2. **Potential Solutions**:
           - Option 1, 2, 3...
           - Pros/cons of each

        3. **Recommended Fix**:
           - Best approach
           - Steps to implement
           - How to test

        4. **Prevention**:
           - How to prevent similar issues?
           - Tests to add?

        5. **Need Help?**:
           - Should escalate to Tech Lead?
           - Need more information?

        Be systematic and thorough.
        """

        return await self.process_message(prompt, context=context)

    async def complete_task(
        self,
        task_id: str,
        pm_id: UUID,
        completion_summary: str,
        deliverables: List[str],
        tests_passed: bool,
        documentation_updated: bool,
        notes: Optional[str] = None,
    ) -> TaskCompletion:
        """
        Mark task as complete and notify PM.

        Args:
            task_id: Task identifier
            pm_id: PM agent ID
            completion_summary: Summary of work done
            deliverables: List of deliverables
            tests_passed: Whether tests are passing
            documentation_updated: Whether docs updated
            notes: Optional additional notes

        Returns:
            TaskCompletion message
        """
        return TaskCompletion(
            recipient=pm_id,
            task_id=task_id,
            completion_summary=completion_summary,
            deliverables=deliverables,
            tests_passed=tests_passed,
            documentation_updated=documentation_updated,
            notes=notes,
        )

    # Helper methods

    def _extract_files(self, content: str) -> List[str]:
        """Extract file names from implementation plan"""
        import re
        # Look for common file patterns
        pattern = r'[\w/]+\.(py|js|ts|tsx|jsx|json|yaml|yml)'
        matches = re.findall(pattern, content)
        return list(set(matches))[:20]  # Max 20 files

    def _estimate_loc(self, content: str) -> Optional[int]:
        """Estimate lines of code from plan"""
        import re
        pattern = r'(\d+)\s*lines'
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            return sum(int(m) for m in matches)
        return None

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from plan"""
        deps = []
        lines = content.split('\n')
        in_deps_section = False
        for line in lines:
            if 'dependenc' in line.lower() and ':' in line:
                in_deps_section = True
                continue
            if in_deps_section and line.strip().startswith('-'):
                deps.append(line.strip()[1:].strip())
            elif in_deps_section and not line.strip().startswith('-') and line.strip():
                in_deps_section = False
        return deps[:10]
