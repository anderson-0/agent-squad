"""
Tech Lead Agent

The Tech Lead agent provides technical leadership, reviews code, estimates
complexity, makes architecture decisions, and collaborates with the PM on
ticket review and technical feasibility.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.base_agent import BaseSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    CodeReviewRequest,
    CodeReviewResponse,
    Question,
    Answer,
)


class TechLeadAgent(BaseSquadAgent):
    """
    Tech Lead Agent - Technical Leadership

    Responsibilities:
    - Review tickets for technical feasibility
    - Estimate complexity scores
    - Review code and pull requests
    - Make architecture decisions
    - Provide technical guidance
    - Mentor developers
    - Identify technical risks
    - Suggest best practices
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of Tech Lead capabilities

        Returns:
            List of capability names
        """
        return [
            "review_ticket_technical",
            "estimate_complexity",
            "review_code",
            "review_pull_request",
            "provide_architecture_guidance",
            "make_technical_decision",
            "identify_technical_risks",
            "suggest_improvements",
            "mentor_developer",
            "answer_technical_question",
        ]

    async def review_ticket_technical(
        self,
        ticket: Dict[str, Any],
        pm_assessment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Review ticket from technical perspective.

        Collaborates with PM to assess:
        - Technical feasibility
        - Complexity
        - Risks
        - Architecture considerations

        Args:
            ticket: Ticket data
            pm_assessment: Optional PM's initial assessment

        Returns:
            Dictionary with technical review
        """
        context = {
            "ticket": ticket,
            "pm_assessment": pm_assessment,
            "action": "technical_review"
        }

        pm_info = ""
        if pm_assessment:
            pm_info = f"""
            PM's Assessment:
            {pm_assessment}
            """

        prompt = f"""
        Please review this ticket from a technical perspective:

        Ticket: {ticket.get('title')}
        Description: {ticket.get('description')}
        Acceptance Criteria: {ticket.get('acceptance_criteria', [])}
        {pm_info}

        Provide a technical review covering:

        1. **Technical Feasibility**:
           - Is this technically achievable with current stack?
           - Are there any technical blockers?

        2. **Architecture Impact**:
           - Does this align with current architecture?
           - Are there architecture changes needed?
           - Should we create an ADR?

        3. **Technical Risks**:
           - What could go wrong?
           - Performance implications?
           - Security considerations?
           - Scalability concerns?

        4. **Dependencies**:
           - What other systems/services are affected?
           - Are there API changes needed?
           - Database migrations required?

        5. **Implementation Approach**:
           - Suggested technical approach
           - Which patterns/practices to use
           - Testing strategy

        6. **Questions for PM or Stakeholder**:
           - What technical details need clarification?

        7. **Decision**: APPROVED | NEEDS_CLARIFICATION | NOT_FEASIBLE

        Be specific and actionable in your feedback.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "technical_feedback": response.content,
            "decision": self._extract_decision(response.content),
            "risks": self._extract_risks(response.content),
            "architecture_impact": self._extract_architecture_impact(response.content),
            "questions": self._extract_questions(response.content),
            "suggested_approach": self._extract_approach(response.content),
        }

    async def estimate_complexity(
        self,
        ticket: Dict[str, Any],
        code_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Estimate technical complexity of the task.

        Uses a scoring system:
        - 1-2: Simple (well-known patterns, minimal changes)
        - 3-5: Moderate (some new patterns, multiple files)
        - 6-8: Complex (architecture changes, many dependencies)
        - 9-10: Very Complex (major refactoring, high risk)

        Args:
            ticket: Ticket data
            code_context: Optional relevant code from RAG

        Returns:
            Dictionary with complexity analysis
        """
        context = {
            "ticket": ticket,
            "code_context": code_context,
            "action": "complexity_estimation"
        }

        code_info = ""
        if code_context:
            code_info = f"""
            Relevant Code Context:
            {code_context[:1000]}  # Truncate to keep context reasonable
            """

        prompt = f"""
        Estimate the technical complexity of this task:

        Task: {ticket.get('title')}
        Description: {ticket.get('description')}
        {code_info}

        Please analyze and provide:

        1. **Complexity Score** (1-10):
           - Consider: code changes, architecture impact, unknowns, risks

        2. **Complexity Factors**:
           - Number of files affected
           - New vs existing code
           - Pattern complexity
           - Testing requirements
           - Integration points

        3. **Technical Challenges**:
           - What makes this complex?
           - What are the unknowns?
           - What could cause delays?

        4. **Dependencies**:
           - External services
           - Other features
           - Database changes
           - API changes

        5. **Recommended Approach**:
           - How to tackle this complexity?
           - Should we break it down further?
           - Proof of concept needed?

        6. **Confidence Level**: High/Medium/Low

        Provide score and detailed reasoning.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "complexity_score": self._extract_complexity_score(response.content),
            "complexity_factors": self._extract_factors(response.content),
            "challenges": self._extract_challenges(response.content),
            "dependencies": self._extract_dependencies(response.content),
            "recommended_approach": self._extract_approach(response.content),
            "confidence": self._extract_confidence(response.content),
            "analysis": response.content,
        }

    async def review_code(
        self,
        code_diff: str,
        pr_description: str,
        acceptance_criteria: List[str],
    ) -> Dict[str, Any]:
        """
        Review code changes in a pull request.

        Args:
            code_diff: Git diff of changes
            pr_description: PR description
            acceptance_criteria: Original acceptance criteria

        Returns:
            Dictionary with code review
        """
        context = {
            "code_diff": code_diff,
            "pr_description": pr_description,
            "acceptance_criteria": acceptance_criteria,
            "action": "code_review"
        }

        criteria_str = "\n".join([f"- {c}" for c in acceptance_criteria])

        prompt = f"""
        Please review this pull request:

        PR Description:
        {pr_description}

        Acceptance Criteria:
        {criteria_str}

        Code Changes:
        ```
        {code_diff[:3000]}  # Limit for context
        ```

        Review for:

        1. **Code Quality**:
           - Clean code principles
           - Readability
           - Maintainability
           - DRY violations

        2. **Best Practices**:
           - Design patterns
           - SOLID principles
           - Framework conventions
           - Error handling

        3. **Performance**:
           - Potential bottlenecks
           - N+1 queries
           - Memory usage
           - Caching opportunities

        4. **Security**:
           - Input validation
           - SQL injection risks
           - XSS vulnerabilities
           - Authentication/authorization

        5. **Testing**:
           - Test coverage
           - Test quality
           - Edge cases covered

        6. **Acceptance Criteria**:
           - All criteria met?
           - Any gaps?

        7. **Specific Comments**:
           - File: line: issue

        8. **Decision**: APPROVED | CHANGES_REQUESTED | COMMENTED

        Provide constructive, actionable feedback.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "approval_status": self._extract_approval_status(response.content),
            "comments": self._parse_code_comments(response.content),
            "summary": self._extract_summary(response.content),
            "full_review": response.content,
        }

    async def provide_architecture_guidance(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Provide architecture guidance to the team.

        Args:
            question: Architecture question from team member
            context: Relevant context (project, current arch, etc.)

        Returns:
            AgentResponse with guidance
        """
        prompt = f"""
        A team member has an architecture question:

        Question: {question}

        Project Context:
        {context.get('project_info', 'N/A')}

        Current Architecture:
        {context.get('current_architecture', 'N/A')}

        Please provide guidance that:
        1. Answers the question clearly
        2. Explains the reasoning (why, not just what)
        3. Provides examples if helpful
        4. Considers alternatives
        5. References best practices
        6. Considers project constraints

        Be educational - help them understand the principles.
        """

        return await self.process_message(prompt, context=context)

    async def make_technical_decision(
        self,
        decision_needed: str,
        options: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make a technical decision when team needs direction.

        Args:
            decision_needed: What needs to be decided
            options: Available options with pros/cons
            context: Relevant context

        Returns:
            Dictionary with decision and reasoning
        """
        options_str = "\n\n".join([
            f"Option {i+1}: {opt.get('name')}\n"
            f"Pros: {opt.get('pros', [])}\n"
            f"Cons: {opt.get('cons', [])}\n"
            f"Effort: {opt.get('effort', 'N/A')}"
            for i, opt in enumerate(options)
        ])

        prompt = f"""
        The team needs a technical decision:

        Decision Needed:
        {decision_needed}

        Options:
        {options_str}

        Project Context:
        {context.get('project_info', 'N/A')}

        Constraints:
        {context.get('constraints', 'N/A')}

        Please analyze and decide:
        1. Which option is best?
        2. Why? (detailed reasoning)
        3. Trade-offs accepted
        4. Implementation notes
        5. Risks and mitigation
        6. Should this be documented as an ADR?

        Make a clear, confident decision with solid reasoning.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "decision": self._extract_decision_choice(response.content),
            "reasoning": response.content,
            "should_document_adr": self._should_create_adr(response.content),
            "implementation_notes": self._extract_implementation_notes(response.content),
            "risks": self._extract_risks(response.content),
        }

    async def answer_technical_question(
        self,
        question: str,
        asker_role: str,
        context: Dict[str, Any],
    ) -> Answer:
        """
        Answer a technical question from a team member.

        Args:
            question: The question
            asker_role: Role of person asking
            context: Relevant context

        Returns:
            Answer message
        """
        guidance = await self.provide_architecture_guidance(question, context)

        return Answer(
            recipient=UUID(context.get('asker_id')),
            task_id=context.get('task_id', 'general'),
            question_id=context.get('question_id', ''),
            answer=guidance.content,
            confidence="high",  # TL should be confident
        )

    # Helper methods for parsing

    def _extract_decision(self, content: str) -> str:
        """Extract decision from response"""
        content_upper = content.upper()
        if "APPROVED" in content_upper and "NOT" not in content_upper:
            return "approved"
        elif "NEEDS_CLARIFICATION" in content_upper or "NEEDS CLARIFICATION" in content_upper:
            return "needs_clarification"
        elif "NOT_FEASIBLE" in content_upper or "NOT FEASIBLE" in content_upper:
            return "not_feasible"
        return "unknown"

    def _extract_complexity_score(self, content: str) -> Optional[int]:
        """Extract complexity score (1-10)"""
        import re
        pattern = r"complexity[:\s]+(\d+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            return min(max(score, 1), 10)  # Clamp to 1-10
        return None

    def _extract_risks(self, content: str) -> List[str]:
        """Extract risks from response"""
        risks = []
        lines = content.split('\n')
        in_risks_section = False
        for line in lines:
            if 'risk' in line.lower() and ':' in line:
                in_risks_section = True
                continue
            if in_risks_section and line.strip() and line.strip().startswith('-'):
                risks.append(line.strip()[1:].strip())
            elif in_risks_section and not line.strip().startswith('-'):
                in_risks_section = False
        return risks[:10]

    def _extract_architecture_impact(self, content: str) -> str:
        """Extract architecture impact description"""
        # Simple extraction - look for architecture section
        lines = content.split('\n')
        impact_lines = []
        in_section = False
        for line in lines:
            if 'architecture' in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section:
                if line.strip() and not line.strip().startswith('#'):
                    impact_lines.append(line.strip())
                else:
                    break
        return ' '.join(impact_lines[:5])

    def _extract_questions(self, content: str) -> List[str]:
        """Extract questions from response"""
        questions = []
        lines = content.split('\n')
        for line in lines:
            if '?' in line and len(line) < 200:
                questions.append(line.strip())
        return questions[:5]

    def _extract_approach(self, content: str) -> str:
        """Extract suggested approach"""
        lines = content.split('\n')
        approach_lines = []
        in_section = False
        for line in lines:
            if 'approach' in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section:
                if line.strip():
                    approach_lines.append(line.strip())
                    if len(approach_lines) >= 5:
                        break
        return ' '.join(approach_lines)

    def _extract_factors(self, content: str) -> List[str]:
        """Extract complexity factors"""
        return self._extract_list_items(content, "factor")

    def _extract_challenges(self, content: str) -> List[str]:
        """Extract technical challenges"""
        return self._extract_list_items(content, "challenge")

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies"""
        return self._extract_list_items(content, "dependenc")

    def _extract_confidence(self, content: str) -> str:
        """Extract confidence level"""
        content_lower = content.lower()
        if "high confidence" in content_lower or "confidence: high" in content_lower:
            return "high"
        elif "low confidence" in content_lower or "confidence: low" in content_lower:
            return "low"
        return "medium"

    def _extract_approval_status(self, content: str) -> str:
        """Extract code review approval status"""
        content_upper = content.upper()
        if "APPROVED" in content_upper and "CHANGES" not in content_upper:
            return "approved"
        elif "CHANGES_REQUESTED" in content_upper or "CHANGES REQUESTED" in content_upper:
            return "changes_requested"
        return "commented"

    def _parse_code_comments(self, content: str) -> List[Dict[str, str]]:
        """Parse specific code comments"""
        # Placeholder - would parse file:line:comment format
        return []

    def _extract_summary(self, content: str) -> str:
        """Extract review summary"""
        lines = content.split('\n')
        return ' '.join(lines[:3])  # First 3 lines as summary

    def _extract_decision_choice(self, content: str) -> str:
        """Extract which option was chosen"""
        import re
        pattern = r"option\s+(\d+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return f"option_{match.group(1)}"
        return "unclear"

    def _should_create_adr(self, content: str) -> bool:
        """Check if ADR should be created"""
        content_lower = content.lower()
        return "adr" in content_lower or "architecture decision record" in content_lower

    def _extract_implementation_notes(self, content: str) -> str:
        """Extract implementation notes"""
        return self._extract_section(content, "implementation")

    def _extract_section(self, content: str, section_name: str) -> str:
        """Generic section extraction"""
        lines = content.split('\n')
        section_lines = []
        in_section = False
        for line in lines:
            if section_name in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section:
                if line.strip():
                    section_lines.append(line.strip())
                    if len(section_lines) >= 5:
                        break
        return ' '.join(section_lines)

    def _extract_list_items(self, content: str, keyword: str) -> List[str]:
        """Extract list items related to keyword"""
        items = []
        lines = content.split('\n')
        in_section = False
        for line in lines:
            if keyword in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                items.append(line.strip()[1:].strip())
            elif in_section and not line.strip().startswith('-') and line.strip():
                in_section = False
        return items[:10]
