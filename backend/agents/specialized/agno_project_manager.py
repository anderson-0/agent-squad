"""
Agno-Based Project Manager Agent

The PM agent is the orchestrator of the squad. It receives tickets via webhooks,
collaborates with the Tech Lead to review and estimate tasks, delegates work
to the team, and monitors progress.

This is the Agno-powered version that leverages persistent memory,
session management, and the Agno framework for enhanced performance.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    TaskAssignment,
    StatusRequest,
    Question,
    HumanInterventionRequired,
    Standup,
)


class TicketReview(Dict[str, Any]):
    """Result of PM + TL ticket review"""
    pass


class TaskBreakdown(Dict[str, Any]):
    """Task broken down into subtasks"""
    pass


class AgnoProjectManagerAgent(AgnoSquadAgent):
    """
    Agno-Powered Project Manager Agent - The Squad Orchestrator

    Responsibilities:
    - Receive webhook notifications from Jira/ClickUp
    - Collaborate with Tech Lead to review tickets
    - Estimate effort and complexity
    - Break down tasks into subtasks
    - Delegate tasks to appropriate team members
    - Monitor progress and conduct standups
    - Escalate blockers to humans
    - Communicate with stakeholders

    Enhancements with Agno:
    - Persistent memory of past decisions and patterns
    - Session resumption for long-running collaborations
    - Automatic conversation history management
    - Multi-model support (GPT-4, Claude, Groq)
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of PM capabilities

        Returns:
            List of capability names
        """
        return [
            "receive_webhook_notification",
            "review_ticket_with_tech_lead",
            "estimate_effort",
            "estimate_complexity",
            "break_down_task",
            "delegate_to_team",
            "monitor_progress",
            "conduct_standup",
            "check_team_status",
            "escalate_to_human",
            "provide_status_update",
            "communicate_with_stakeholder",
        ]

    async def receive_webhook_notification(
        self,
        ticket: Dict[str, Any],
        webhook_event: str,
    ) -> AgentResponse:
        """
        Process incoming webhook notification from Jira/ClickUp.

        Args:
            ticket: Ticket data from webhook
            webhook_event: Event type (issue_created, issue_updated, etc.)

        Returns:
            AgentResponse with initial assessment
        """
        context = {
            "ticket": ticket,
            "webhook_event": webhook_event,
            "action": "initial_assessment"
        }

        prompt = f"""
        A new webhook notification has arrived:

        Event: {webhook_event}
        Ticket ID: {ticket.get('id', 'N/A')}
        Title: {ticket.get('title', 'N/A')}
        Description: {ticket.get('description', 'N/A')}
        Priority: {ticket.get('priority', 'medium')}

        Please provide an initial assessment:
        1. Is this ticket well-written and actionable?
        2. What information is missing (if any)?
        3. Should we proceed with Tech Lead review or escalate to human?
        4. What is your initial impression of the scope?

        Respond in a structured format with clear sections.
        """

        return await self.process_message(prompt, context=context)

    async def review_ticket_with_tech_lead(
        self,
        ticket: Dict[str, Any],
        tech_lead_feedback: Optional[str] = None,
    ) -> TicketReview:
        """
        Collaborate with Tech Lead to review ticket quality and feasibility.

        This is a multi-turn conversation:
        1. PM analyzes ticket
        2. TL provides technical feedback
        3. PM + TL decide: Ready | Needs Improvement | Unclear

        Args:
            ticket: Ticket data
            tech_lead_feedback: Optional feedback from Tech Lead

        Returns:
            TicketReview with decision and recommendations
        """
        context = {
            "ticket": ticket,
            "tech_lead_feedback": tech_lead_feedback,
            "action": "ticket_review"
        }

        if tech_lead_feedback:
            # PM responds to TL feedback
            prompt = f"""
            The Tech Lead has reviewed the ticket and provided feedback:

            {tech_lead_feedback}

            Based on this technical feedback, please:
            1. Assess if the ticket is ready for implementation
            2. Identify any gaps in requirements
            3. Suggest improvements to the ticket if needed
            4. Make a decision: READY | NEEDS_IMPROVEMENT | UNCLEAR

            If UNCLEAR, we should escalate to the human stakeholder.
            If NEEDS_IMPROVEMENT, suggest specific improvements.
            If READY, confirm we can proceed with task breakdown.
            """
        else:
            # PM initiates review
            prompt = f"""
            Let's review this ticket before assigning it to the team:

            Ticket: {ticket.get('title')}
            Description: {ticket.get('description')}
            Acceptance Criteria: {ticket.get('acceptance_criteria', 'Not specified')}

            Please analyze:
            1. Are the requirements clear and complete?
            2. Is the scope well-defined?
            3. Are acceptance criteria specific and testable?
            4. What technical considerations should the Tech Lead review?
            5. What questions should we ask the Tech Lead?

            Prepare questions for the Tech Lead review.
            """

        response = await self.process_message(prompt, context=context)

        # Parse response into structured format
        return {
            "pm_assessment": response.content,
            "status": self._extract_status(response.content),
            "questions_for_tl": self._extract_questions(response.content),
            "improvements_needed": self._extract_improvements(response.content),
        }

    async def estimate_effort(
        self,
        ticket: Dict[str, Any],
        tech_lead_complexity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate effort in hours for the task.

        Works with Tech Lead's complexity estimate to determine hours.

        Args:
            ticket: Ticket data
            tech_lead_complexity: Optional complexity analysis from TL

        Returns:
            Dictionary with effort estimation
        """
        context = {
            "ticket": ticket,
            "tech_lead_complexity": tech_lead_complexity,
            "action": "effort_estimation"
        }

        complexity_info = ""
        if tech_lead_complexity:
            complexity_info = f"""
            Tech Lead Complexity Analysis:
            - Complexity Score: {tech_lead_complexity.get('score', 'N/A')}
            - Technical Challenges: {tech_lead_complexity.get('challenges', [])}
            - Dependencies: {tech_lead_complexity.get('dependencies', [])}
            """

        prompt = f"""
        Estimate the effort required for this task:

        Ticket: {ticket.get('title')}
        Description: {ticket.get('description')}
        {complexity_info}

        Please provide:
        1. Estimated hours for implementation
        2. Estimated hours for testing
        3. Estimated hours for code review
        4. Buffer for unknowns (%)
        5. Total estimated hours
        6. Confidence level (high/medium/low)

        Consider:
        - Task complexity
        - Team experience with similar tasks
        - Dependencies on other work
        - Testing requirements

        Provide estimates in a structured format.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "implementation_hours": self._extract_hours(response.content, "implementation"),
            "testing_hours": self._extract_hours(response.content, "testing"),
            "review_hours": self._extract_hours(response.content, "review"),
            "buffer_percentage": self._extract_buffer(response.content),
            "total_hours": self._extract_hours(response.content, "total"),
            "confidence": self._extract_confidence(response.content),
            "estimation_notes": response.content,
        }

    async def break_down_task(
        self,
        ticket: Dict[str, Any],
        squad_members: List[Dict[str, Any]],
    ) -> TaskBreakdown:
        """
        Break down a task into subtasks for delegation.

        Args:
            ticket: Ticket data
            squad_members: Available squad members

        Returns:
            TaskBreakdown with subtasks
        """
        context = {
            "ticket": ticket,
            "squad_members": squad_members,
            "action": "task_breakdown"
        }

        members_info = "\n".join([
            f"- {m.get('role')} ({m.get('specialization', 'general')})"
            for m in squad_members
        ])

        prompt = f"""
        Break down this task into subtasks for the team:

        Task: {ticket.get('title')}
        Description: {ticket.get('description')}
        Acceptance Criteria: {ticket.get('acceptance_criteria', [])}

        Available Team Members:
        {members_info}

        Please create a breakdown with:
        1. Subtasks in logical order
        2. Dependencies between subtasks
        3. Suggested assignee for each (by role)
        4. Estimated effort per subtask
        5. Critical path identification

        Format each subtask as:
        - Title
        - Description
        - Assignee role
        - Dependencies
        - Estimated hours
        """

        response = await self.process_message(prompt, context=context)

        return {
            "subtasks": self._parse_subtasks(response.content),
            "critical_path": self._extract_critical_path(response.content),
            "total_estimated_hours": self._extract_total_hours(response.content),
            "breakdown_notes": response.content,
        }

    async def delegate_task(
        self,
        subtask: Dict[str, Any],
        agent_id: UUID,
        agent_role: str,
        context: Dict[str, Any],
    ) -> TaskAssignment:
        """
        Create a task assignment for a team member.

        Args:
            subtask: Subtask to delegate
            agent_id: Target agent UUID
            agent_role: Role of the agent
            context: Additional context (RAG results, etc.)

        Returns:
            TaskAssignment message
        """
        # Format context for agent
        context_str = f"""
        Project Context:
        {context.get('project_info', 'N/A')}

        Related Code:
        {context.get('related_code', 'N/A')}

        Past Solutions:
        {context.get('past_solutions', 'N/A')}

        Architecture Decisions:
        {context.get('architecture', 'N/A')}
        """

        return TaskAssignment(
            recipient=agent_id,
            task_id=subtask.get('task_id'),
            description=subtask.get('description'),
            acceptance_criteria=subtask.get('acceptance_criteria', []),
            dependencies=subtask.get('dependencies', []),
            context=context_str,
            priority=subtask.get('priority', 'medium'),
            estimated_hours=subtask.get('estimated_hours'),
        )

    async def conduct_standup(
        self,
        squad_members: List[Dict[str, Any]],
        recent_updates: List[Dict[str, Any]],
    ) -> AgentResponse:
        """
        Conduct async standup - analyze team updates and identify issues.

        Args:
            squad_members: List of squad members
            recent_updates: Recent status updates from team

        Returns:
            AgentResponse with standup summary
        """
        context = {
            "squad_members": squad_members,
            "recent_updates": recent_updates,
            "action": "standup"
        }

        updates_str = "\n\n".join([
            f"Agent: {u.get('agent_role')}\n"
            f"Yesterday: {u.get('yesterday', 'N/A')}\n"
            f"Today: {u.get('today', 'N/A')}\n"
            f"Blockers: {u.get('blockers', [])}"
            for u in recent_updates
        ])

        prompt = f"""
        Daily Standup Summary:

        {updates_str}

        Please analyze and provide:
        1. Overall team progress
        2. Identified blockers and suggested solutions
        3. Team members who might need help
        4. Tasks at risk of delay
        5. Positive highlights
        6. Action items for the PM

        Keep it concise but actionable.
        """

        return await self.process_message(prompt, context=context)

    async def escalate_to_human(
        self,
        task_id: str,
        reason: str,
        details: str,
        attempted_solutions: List[str],
        urgency: str = "high",
    ) -> HumanInterventionRequired:
        """
        Create escalation message to human stakeholder.

        Args:
            task_id: Task identifier
            reason: Reason for escalation
            details: Detailed explanation
            attempted_solutions: What the team tried
            urgency: Urgency level

        Returns:
            HumanInterventionRequired message
        """
        return HumanInterventionRequired(
            task_id=task_id,
            reason=reason,
            details=details,
            attempted_solutions=attempted_solutions,
            urgency=urgency,
        )

    async def check_team_status(
        self,
        squad_members: List[UUID],
    ) -> List[StatusRequest]:
        """
        Request status updates from all team members.

        Args:
            squad_members: List of squad member UUIDs

        Returns:
            List of StatusRequest messages
        """
        # This will be sent via message bus to each agent
        return [
            StatusRequest(
                recipient=member_id,
                task_id="daily_update",
            )
            for member_id in squad_members
        ]

    # Helper methods for parsing LLM responses

    def _extract_status(self, content: str) -> str:
        """Extract ticket status from response"""
        content_upper = content.upper()
        if "READY" in content_upper and "NEEDS_IMPROVEMENT" not in content_upper:
            return "ready"
        elif "NEEDS_IMPROVEMENT" in content_upper or "NEEDS IMPROVEMENT" in content_upper:
            return "needs_improvement"
        elif "UNCLEAR" in content_upper:
            return "unclear"
        return "unknown"

    def _extract_questions(self, content: str) -> List[str]:
        """Extract questions from response"""
        # Simple extraction - in production, use more robust parsing
        questions = []
        lines = content.split('\n')
        for line in lines:
            if '?' in line and len(line) < 200:
                questions.append(line.strip())
        return questions[:5]  # Max 5 questions

    def _extract_improvements(self, content: str) -> List[str]:
        """Extract improvement suggestions from response"""
        improvements = []
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['improve', 'add', 'clarify', 'specify']):
                if len(line) < 200:
                    improvements.append(line.strip())
        return improvements[:10]

    def _extract_hours(self, content: str, hour_type: str) -> Optional[float]:
        """Extract hour estimates from response"""
        # Simple extraction - in production, use structured outputs
        import re
        pattern = rf"{hour_type}[:\s]+(\d+(?:\.\d+)?)\s*hours?"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def _extract_buffer(self, content: str) -> Optional[int]:
        """Extract buffer percentage from response"""
        import re
        pattern = r"buffer[:\s]+(\d+)\s*%"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 20  # Default 20% buffer

    def _extract_confidence(self, content: str) -> str:
        """Extract confidence level from response"""
        content_lower = content.lower()
        if "high confidence" in content_lower or "confidence: high" in content_lower:
            return "high"
        elif "low confidence" in content_lower or "confidence: low" in content_lower:
            return "low"
        return "medium"

    def _parse_subtasks(self, content: str) -> List[Dict[str, Any]]:
        """Parse subtasks from response"""
        # Simple parsing - in production, use structured outputs or better parsing
        subtasks = []
        # This is a placeholder - actual implementation would parse the LLM response
        # For now, return empty list
        return subtasks

    def _extract_critical_path(self, content: str) -> List[str]:
        """Extract critical path from response"""
        # Placeholder for critical path extraction
        return []

    def _extract_total_hours(self, content: str) -> Optional[float]:
        """Extract total hours from response"""
        return self._extract_hours(content, "total")
