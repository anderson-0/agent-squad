# Phase 4.5: Agno Migration - Week 1, Day 4-5
## Migrate Remaining 8 Specialized Agents

> **Goal:** Migrate all remaining specialized agents to Agno framework
> **Duration:** 2 days (16 hours)
> **Output:** All 9 specialized agents using Agno

---

## 📋 Day 4-5 Checklist

- [ ] Migrate Tech Lead Agent
- [ ] Migrate Backend Developer Agent
- [ ] Migrate Frontend Developer Agent
- [ ] Migrate QA Tester Agent
- [ ] Migrate Solution Architect Agent
- [ ] Migrate DevOps Engineer Agent
- [ ] Migrate AI Engineer Agent
- [ ] Migrate Designer Agent
- [ ] Update AgentFactory to support both frameworks
- [ ] Create migration utilities
- [ ] Test all agents
- [ ] Document migration patterns

---

## 🎯 Migration Strategy

### Pattern Established (from PM migration)

We've proven that migrating agents is straightforward:

**Steps:**
1. Create new file `agno_{agent_name}.py`
2. Change parent class: `BaseSquadAgent` → `AgnoSquadAgent`
3. Keep all methods and capabilities
4. Test with existing capabilities
5. Update factory registration

**Time per agent:** ~1.5-2 hours
**Total for 8 agents:** ~12-16 hours

---

## 🔧 Part 1: Migrate Tech Lead Agent (Day 4, 2 hours)

### 1.1 Create AgnoTechLeadAgent

```python
# backend/agents/specialized/agno_tech_lead.py
"""
Tech Lead Agent (Agno-based)

Provides technical leadership, code review, complexity assessment,
and architectural guidance.
"""
from typing import List, Dict, Any, Optional

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoTechLeadAgent(AgnoSquadAgent):
    """
    Tech Lead Agent (Agno-based) - Technical Leadership

    Responsibilities:
    - Technical feasibility assessment
    - Complexity estimation
    - Code review
    - Architecture guidance
    - Technical decision making
    - Risk identification
    - Developer mentorship
    """

    def get_capabilities(self) -> List[str]:
        """Return list of Tech Lead capabilities"""
        return [
            "review_ticket_technical",
            "estimate_complexity",
            "review_code",
            "review_pull_request",
            "provide_architecture_guidance",
            "make_technical_decision",
            "identify_technical_risks",
            "mentor_developer",
            "answer_technical_question",
        ]

    async def review_ticket_technical(
        self,
        ticket: Dict[str, Any],
        pm_questions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Review ticket from technical perspective.

        Args:
            ticket: Ticket data
            pm_questions: Questions from Project Manager

        Returns:
            Technical review with feasibility assessment
        """
        context = {
            "ticket": ticket,
            "pm_questions": pm_questions,
            "action": "technical_review"
        }

        questions_section = ""
        if pm_questions:
            questions_section = f"""
            Project Manager has specific questions:
            {chr(10).join(f'- {q}' for q in pm_questions)}
            """

        prompt = f"""
        Review this ticket from a technical perspective:

        Ticket: {ticket.get('title')}
        Description: {ticket.get('description')}
        Acceptance Criteria: {ticket.get('acceptance_criteria', [])}
        {questions_section}

        Please provide:
        1. Technical feasibility assessment
        2. Key technical challenges
        3. Required technical expertise
        4. Technology stack considerations
        5. Integration points
        6. Security considerations
        7. Performance implications
        8. Testing approach
        9. Decision: APPROVED | NEEDS_CLARIFICATION | NOT_FEASIBLE

        Be specific and actionable.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "technical_assessment": response.content,
            "decision": self._extract_decision(response.content),
            "challenges": self._extract_challenges(response.content),
            "recommendations": self._extract_recommendations(response.content),
        }

    async def estimate_complexity(
        self,
        ticket: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Estimate technical complexity (1-10 scale).

        Args:
            ticket: Ticket data

        Returns:
            Complexity estimation with breakdown
        """
        context = {
            "ticket": ticket,
            "action": "complexity_estimation"
        }

        prompt = f"""
        Estimate the technical complexity of this task:

        Ticket: {ticket.get('title')}
        Description: {ticket.get('description')}

        Provide complexity score (1-10):
        - 1-2: Simple (basic CRUD, configuration)
        - 3-5: Moderate (business logic, integrations)
        - 6-8: Complex (architecture changes, performance)
        - 9-10: Very Complex (system-wide changes, new paradigms)

        Include:
        1. Complexity score (1-10)
        2. Reasoning for the score
        3. Technical challenges
        4. Dependencies on other systems
        5. Required expertise level
        6. Potential risks

        Format your response with clear sections.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "complexity_score": self._extract_complexity_score(response.content),
            "reasoning": response.content,
            "challenges": self._extract_challenges(response.content),
            "dependencies": self._extract_dependencies(response.content),
            "risks": self._extract_risks(response.content),
        }

    async def review_code(
        self,
        code_changes: str,
        acceptance_criteria: List[str],
        pr_description: str,
    ) -> Dict[str, Any]:
        """
        Perform detailed code review.

        Args:
            code_changes: Code diff or changes
            acceptance_criteria: Requirements to verify
            pr_description: Description of changes

        Returns:
            Code review with feedback and approval status
        """
        context = {
            "code_changes": code_changes,
            "acceptance_criteria": acceptance_criteria,
            "action": "code_review"
        }

        prompt = f"""
        Review this code change:

        PR Description: {pr_description}

        Acceptance Criteria:
        {chr(10).join(f'- {ac}' for ac in acceptance_criteria)}

        Code Changes:
        {code_changes[:5000]}  # Limit for context

        Review for:
        1. **Code Quality**: Clean code, readability, maintainability
        2. **Best Practices**: Design patterns, SOLID principles
        3. **Performance**: Bottlenecks, N+1 queries, caching
        4. **Security**: Input validation, SQL injection, XSS, auth
        5. **Testing**: Coverage, test quality, edge cases
        6. **Acceptance Criteria**: All requirements met

        Provide:
        - Specific feedback for each issue found
        - Severity (critical, major, minor, suggestion)
        - Suggestions for improvement
        - Status: APPROVED | CHANGES_REQUESTED | COMMENTED

        Be thorough but constructive.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "review_feedback": response.content,
            "status": self._extract_review_status(response.content),
            "issues": self._parse_issues(response.content),
            "approval": self._extract_review_status(response.content) == "approved",
        }

    async def provide_architecture_guidance(
        self,
        question: str,
        context_info: Dict[str, Any],
    ) -> AgentResponse:
        """
        Provide architecture guidance to team members.

        Args:
            question: Technical question
            context_info: Additional context

        Returns:
            AgentResponse with guidance
        """
        context = {
            "question": question,
            "context_info": context_info,
            "action": "architecture_guidance"
        }

        prompt = f"""
        A team member needs architecture guidance:

        Question: {question}

        Context:
        - Current Architecture: {context_info.get('current_architecture', 'N/A')}
        - Technologies: {context_info.get('technologies', 'N/A')}
        - Constraints: {context_info.get('constraints', 'N/A')}

        Provide:
        1. Clear explanation of architectural concepts
        2. Pros and cons of different approaches
        3. Recommended solution with reasoning
        4. Implementation considerations
        5. Potential pitfalls to avoid
        6. Resources for further learning

        Focus on being educational - explain the WHY, not just the WHAT.
        """

        return await self.process_message(prompt, context=context)

    async def make_technical_decision(
        self,
        decision_needed: str,
        options: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Make technical decision when team needs guidance.

        Args:
            decision_needed: What needs to be decided
            options: Available options with pros/cons

        Returns:
            Technical decision with reasoning
        """
        context = {
            "decision_needed": decision_needed,
            "options": options,
            "action": "technical_decision"
        }

        options_text = "\n\n".join([
            f"**Option {i+1}: {opt.get('name')}**\n"
            f"Pros: {', '.join(opt.get('pros', []))}\n"
            f"Cons: {', '.join(opt.get('cons', []))}"
            for i, opt in enumerate(options)
        ])

        prompt = f"""
        Make a technical decision:

        Decision Needed: {decision_needed}

        Options:
        {options_text}

        Provide:
        1. Recommended option
        2. Detailed reasoning
        3. Trade-offs considered
        4. Implementation guidance
        5. Success criteria
        6. Should we create an ADR (Architecture Decision Record)? Yes/No

        Make the decision considering:
        - Long-term maintainability
        - Team expertise
        - Project timeline
        - Technical debt
        - Scalability
        """

        response = await self.process_message(prompt, context=context)

        return {
            "decision": self._extract_decision_choice(response.content),
            "reasoning": response.content,
            "should_create_adr": "yes" in response.content.lower() and "adr" in response.content.lower(),
        }

    # Helper methods
    def _extract_decision(self, content: str) -> str:
        """Extract technical decision from response"""
        content_upper = content.upper()
        if "APPROVED" in content_upper and "NOT" not in content_upper:
            return "approved"
        elif "NEEDS_CLARIFICATION" in content_upper or "NEEDS CLARIFICATION" in content_upper:
            return "needs_clarification"
        elif "NOT_FEASIBLE" in content_upper or "NOT FEASIBLE" in content_upper:
            return "not_feasible"
        return "unknown"

    def _extract_complexity_score(self, content: str) -> int:
        """Extract complexity score (1-10)"""
        import re
        pattern = r"complexity[:\s]+(\d+)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 5  # Default medium

    def _extract_review_status(self, content: str) -> str:
        """Extract code review status"""
        content_upper = content.upper()
        if "APPROVED" in content_upper and "CHANGES" not in content_upper:
            return "approved"
        elif "CHANGES_REQUESTED" in content_upper or "CHANGES REQUESTED" in content_upper:
            return "changes_requested"
        elif "COMMENTED" in content_upper:
            return "commented"
        return "unknown"

    def _extract_challenges(self, content: str) -> List[str]:
        """Extract technical challenges"""
        # Simple extraction - could be enhanced
        return []

    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations"""
        return []

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies"""
        return []

    def _extract_risks(self, content: str) -> List[str]:
        """Extract risks"""
        return []

    def _parse_issues(self, content: str) -> List[Dict[str, Any]]:
        """Parse code review issues"""
        return []

    def _extract_decision_choice(self, content: str) -> str:
        """Extract which option was chosen"""
        return "option_1"  # Placeholder
```

---

## 🔧 Part 2: Batch Migrate Developer Agents (Day 4, 4 hours)

Since Backend and Frontend developers have similar structure, we can migrate them together.

### 2.1 Backend Developer Agent

```python
# backend/agents/specialized/agno_backend_developer.py
"""
Backend Developer Agent (Agno-based)
"""
from typing import List, Dict, Any, Optional

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoBackendDeveloperAgent(AgnoSquadAgent):
    """Backend Developer Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
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
            "troubleshoot_issue",
            "complete_task",
        ]

    async def analyze_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze task and create implementation plan.

        Args:
            task: Task details
            context: RAG results, related code, etc.

        Returns:
            Analysis with implementation approach
        """
        ctx = {
            "task": task,
            "context": context,
            "action": "task_analysis"
        }

        prompt = f"""
        Analyze this backend development task:

        Task: {task.get('title')}
        Description: {task.get('description')}
        Acceptance Criteria: {task.get('acceptance_criteria', [])}

        Context:
        - Related Code: {context.get('related_code', 'N/A')}
        - Past Solutions: {context.get('past_solutions', 'N/A')}

        Provide:
        1. Understanding of requirements
        2. Technical approach
        3. Files to create/modify
        4. Database changes needed
        5. API endpoints to add/update
        6. Testing strategy
        7. Estimated time breakdown
        8. Questions or clarifications needed

        Be specific and actionable.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "analysis": response.content,
            "approach": self._extract_approach(response.content),
            "files_needed": self._extract_files(response.content),
            "questions": self._extract_questions(response.content),
        }

    async def plan_implementation(
        self,
        task: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create detailed implementation plan.

        Args:
            task: Task details
            analysis: Previous analysis

        Returns:
            Detailed implementation plan
        """
        ctx = {
            "task": task,
            "analysis": analysis,
            "action": "implementation_planning"
        }

        prompt = f"""
        Create a detailed implementation plan for this backend task:

        Task: {task.get('title')}
        Previous Analysis: {analysis.get('analysis', '')}

        Create a step-by-step plan including:

        1. **Files to Create/Modify**
           - Path, purpose, key changes

        2. **Database Changes**
           - Models, migrations, indexes

        3. **API Endpoints**
           - Routes, methods, request/response schemas

        4. **Business Logic**
           - Services, algorithms, edge cases

        5. **Testing Strategy**
           - Unit tests, integration tests, test data

        6. **Dependencies**
           - New packages, external services

        7. **Implementation Order**
           - Step 1, Step 2, etc.

        8. **Definition of Done**
           - All tests passing
           - Code reviewed
           - Documentation updated

        Be thorough and specific.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "implementation_plan": response.content,
            "steps": self._extract_steps(response.content),
            "estimated_time": self._extract_time(response.content),
        }

    async def ask_question(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """Ask question to team (usually PM or TL)"""
        ctx = {
            "question": question,
            "context": context,
            "action": "question"
        }

        prompt = f"""
        Formulate a clear question for the team:

        Question: {question}
        Context: {context.get('issue', '')}

        Structure your question with:
        1. What you're trying to accomplish
        2. What you've tried so far
        3. Specific question or clarification needed
        4. Why you're stuck
        5. Urgency level

        Keep it concise but provide enough context.
        """

        return await self.process_message(prompt, context=ctx)

    async def provide_status_update(
        self,
        task: Dict[str, Any],
        progress: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Provide status update to PM"""
        ctx = {
            "task": task,
            "progress": progress,
            "action": "status_update"
        }

        prompt = f"""
        Provide a status update on your task:

        Task: {task.get('title')}
        Progress: {progress.get('percentage', 0)}%

        Yesterday: {progress.get('yesterday', 'Started task')}
        Today: {progress.get('today', 'Working on...')}
        Blockers: {progress.get('blockers', [])}

        Structure your update:
        1. What's been completed
        2. Current work in progress
        3. What's next
        4. Any blockers or concerns
        5. Estimated completion
        6. Do you need help? Yes/No

        Be honest and specific.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "status_update": response.content,
            "needs_help": "yes" in response.content.lower() and "help" in response.content.lower(),
        }

    async def request_code_review(
        self,
        pr_url: str,
        changes_summary: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Request code review from Tech Lead"""
        ctx = {
            "pr_url": pr_url,
            "changes_summary": changes_summary,
            "task": task,
            "action": "code_review_request"
        }

        prompt = f"""
        Request code review for your PR:

        PR: {pr_url}
        Task: {task.get('title')}
        Changes: {changes_summary}

        Provide:
        1. Summary of changes
        2. How you addressed each acceptance criterion
        3. Testing performed
        4. Areas where you'd like specific feedback
        5. Known limitations or technical debt
        6. Self-review notes

        Help the reviewer understand your changes.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "review_request": response.content,
        }

    # Helper methods
    def _extract_approach(self, content: str) -> str:
        return ""

    def _extract_files(self, content: str) -> List[str]:
        return []

    def _extract_questions(self, content: str) -> List[str]:
        questions = []
        lines = content.split('\n')
        for line in lines:
            if '?' in line:
                questions.append(line.strip())
        return questions[:5]

    def _extract_steps(self, content: str) -> List[str]:
        return []

    def _extract_time(self, content: str) -> Optional[float]:
        return None
```

### 2.2 Frontend Developer Agent

```python
# backend/agents/specialized/agno_frontend_developer.py
"""
Frontend Developer Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoFrontendDeveloperAgent(AgnoSquadAgent):
    """Frontend Developer Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "analyze_task",
            "plan_implementation",
            "design_ui_components",
            "write_code",  # Phase 4: via MCP
            "write_tests",  # Phase 4: via MCP
            "create_pull_request",  # Phase 4: via MCP
            "ask_question",
            "provide_status_update",
            "request_code_review",
            "respond_to_review_feedback",
            "complete_task",
        ]

    async def analyze_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze frontend task"""
        ctx = {
            "task": task,
            "context": context,
            "action": "task_analysis"
        }

        prompt = f"""
        Analyze this frontend development task:

        Task: {task.get('title')}
        Description: {task.get('description')}
        Acceptance Criteria: {task.get('acceptance_criteria', [])}

        Design Context:
        - Wireframes: {context.get('wireframes', 'N/A')}
        - Design System: {context.get('design_system', 'N/A')}

        Provide:
        1. UI components needed
        2. State management approach
        3. API integration points
        4. Responsive design considerations
        5. Accessibility requirements
        6. Testing strategy
        7. Browser compatibility

        Be specific about React/Vue/Angular patterns.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "analysis": response.content,
        }

    async def design_ui_components(
        self,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Design UI component structure"""
        ctx = {
            "requirements": requirements,
            "action": "ui_design"
        }

        prompt = f"""
        Design UI components for this feature:

        Requirements: {requirements.get('description')}

        Provide:
        1. Component hierarchy
        2. Props and state for each component
        3. Component responsibilities
        4. Reusable patterns
        5. Styling approach
        6. Responsive breakpoints

        Follow component design best practices.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "component_design": response.content,
        }
```

---

## 🔧 Part 3: Batch Migrate Support Agents (Day 5, 6 hours)

### 3.1 QA Tester Agent

```python
# backend/agents/specialized/agno_qa_tester.py
"""
QA Tester Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoQATesterAgent(AgnoSquadAgent):
    """QA Tester Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "review_acceptance_criteria",
            "create_test_plan",
            "execute_manual_tests",
            "execute_automated_tests",  # Phase 4: via MCP
            "create_bug_report",
            "verify_bug_fix",
            "regression_testing",
            "approve_deployment",
        ]

    async def create_test_plan(
        self,
        task: Dict[str, Any],
        acceptance_criteria: List[str],
    ) -> Dict[str, Any]:
        """Create comprehensive test plan"""
        ctx = {
            "task": task,
            "acceptance_criteria": acceptance_criteria,
            "action": "test_planning"
        }

        prompt = f"""
        Create a comprehensive test plan:

        Task: {task.get('title')}
        Acceptance Criteria:
        {chr(10).join(f'- {ac}' for ac in acceptance_criteria)}

        Provide test plan including:
        1. **Functional Tests**: Verify each AC
        2. **Integration Tests**: Component interactions
        3. **Edge Cases**: Boundary conditions, errors
        4. **Performance Tests**: Load, response time
        5. **Security Tests**: Auth, input validation
        6. **Accessibility Tests**: WCAG compliance
        7. **Browser/Device Tests**: Compatibility matrix

        For each test:
        - Test ID
        - Description
        - Steps
        - Expected result
        - Priority (high/medium/low)
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "test_plan": response.content,
            "test_count": self._count_tests(response.content),
        }

    async def create_bug_report(
        self,
        bug_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create detailed bug report"""
        ctx = {
            "bug_details": bug_details,
            "action": "bug_report"
        }

        prompt = f"""
        Create a detailed bug report:

        Bug: {bug_details.get('summary')}
        Severity: {bug_details.get('severity', 'medium')}

        Provide:
        1. **Summary**: One-line description
        2. **Steps to Reproduce**: Detailed steps
        3. **Expected Behavior**: What should happen
        4. **Actual Behavior**: What actually happens
        5. **Environment**: Browser, OS, version
        6. **Screenshots/Logs**: Describe what to attach
        7. **Severity**: Critical/Major/Minor/Trivial
        8. **Priority**: High/Medium/Low

        Be specific and actionable.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "bug_report": response.content,
            "severity": self._extract_severity(response.content),
        }

    def _count_tests(self, content: str) -> int:
        return 0

    def _extract_severity(self, content: str) -> str:
        return "medium"
```

### 3.2 Solution Architect Agent

```python
# backend/agents/specialized/agno_solution_architect.py
"""
Solution Architect Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoSolutionArchitectAgent(AgnoSquadAgent):
    """Solution Architect Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "design_system_architecture",
            "create_adr",
            "review_technical_approach",
            "identify_scalability_issues",
            "recommend_tech_stack",
            "design_database_schema",
            "design_api_contracts",
        ]

    async def design_system_architecture(
        self,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Design system architecture"""
        ctx = {
            "requirements": requirements,
            "action": "architecture_design"
        }

        prompt = f"""
        Design system architecture for:

        Requirements: {requirements.get('description')}
        Scale: {requirements.get('scale', 'medium')}
        Constraints: {requirements.get('constraints', [])}

        Provide:
        1. **High-level Architecture**: Components, layers
        2. **Technology Stack**: Rationale for each choice
        3. **Data Flow**: How data moves through system
        4. **Integration Points**: External systems
        5. **Scalability Strategy**: Horizontal/vertical
        6. **Security Architecture**: Auth, encryption
        7. **Deployment Architecture**: Infrastructure
        8. **Trade-offs**: What was considered and why

        Create detailed, production-ready architecture.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "architecture_design": response.content,
        }

    async def create_adr(
        self,
        decision: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create Architecture Decision Record"""
        ctx = {
            "decision": decision,
            "context": context,
            "action": "adr_creation"
        }

        prompt = f"""
        Create an Architecture Decision Record (ADR):

        Decision: {decision}
        Context: {context.get('background', '')}

        Use ADR format:
        1. **Title**: Short noun phrase
        2. **Status**: Proposed/Accepted/Deprecated/Superseded
        3. **Context**: What forces are at play?
        4. **Decision**: What is the decision?
        5. **Consequences**: What becomes easier or harder?

        Be thorough and include trade-offs.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "adr": response.content,
        }
```

### 3.3 DevOps Engineer Agent

```python
# backend/agents/specialized/agno_devops_engineer.py
"""
DevOps Engineer Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoDevOpsEngineerAgent(AgnoSquadAgent):
    """DevOps Engineer Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "setup_ci_cd",
            "provision_infrastructure",
            "configure_monitoring",
            "manage_deployments",
            "optimize_performance",
            "ensure_security",
            "manage_databases",
            "incident_response",
        ]

    async def setup_ci_cd(
        self,
        project_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Set up CI/CD pipeline"""
        ctx = {
            "project_info": project_info,
            "action": "cicd_setup"
        }

        prompt = f"""
        Design CI/CD pipeline for:

        Project: {project_info.get('name')}
        Tech Stack: {project_info.get('tech_stack', [])}
        Deployment Target: {project_info.get('deployment', 'AWS')}

        Provide:
        1. **Pipeline Stages**: Build, test, deploy
        2. **Tools**: GitHub Actions / GitLab CI / Jenkins
        3. **Testing Strategy**: Unit, integration, E2E
        4. **Build Process**: Docker, artifacts
        5. **Deployment Strategy**: Blue-green, canary
        6. **Rollback Plan**: How to revert
        7. **Configuration**: YAML/config file structure

        Be specific with examples.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "cicd_design": response.content,
        }

    async def configure_monitoring(
        self,
        services: List[str],
    ) -> Dict[str, Any]:
        """Configure monitoring and alerting"""
        ctx = {
            "services": services,
            "action": "monitoring_setup"
        }

        prompt = f"""
        Configure monitoring for:

        Services: {', '.join(services)}

        Provide:
        1. **Metrics to Track**: CPU, memory, requests, errors
        2. **Monitoring Tools**: Prometheus, Grafana, DataDog
        3. **Dashboards**: What to visualize
        4. **Alerts**: What triggers alerts
        5. **Alert Routing**: Who gets notified
        6. **Logging Strategy**: What to log, retention
        7. **APM**: Application performance monitoring

        Include severity levels and thresholds.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "monitoring_config": response.content,
        }
```

### 3.4 AI Engineer Agent

```python
# backend/agents/specialized/agno_ai_engineer.py
"""
AI Engineer Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoAIEngineerAgent(AgnoSquadAgent):
    """AI Engineer Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "design_ai_solution",
            "train_model",
            "evaluate_model",
            "deploy_model",
            "optimize_prompts",
            "integrate_ai_service",
            "monitor_ai_performance",
        ]

    async def design_ai_solution(
        self,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Design AI/ML solution"""
        ctx = {
            "requirements": requirements,
            "action": "ai_design"
        }

        prompt = f"""
        Design AI/ML solution for:

        Requirements: {requirements.get('description')}
        Type: {requirements.get('type', 'classification')}

        Provide:
        1. **Approach**: ML model vs LLM vs hybrid
        2. **Model Selection**: Which model/architecture
        3. **Data Requirements**: Training data needed
        4. **Features**: Input features to use
        5. **Training Strategy**: How to train
        6. **Evaluation Metrics**: How to measure success
        7. **Deployment**: API, edge, batch
        8. **Monitoring**: Performance tracking

        Consider cost, latency, and accuracy trade-offs.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "ai_design": response.content,
        }

    async def optimize_prompts(
        self,
        task: str,
        current_prompt: str,
        issues: List[str],
    ) -> Dict[str, Any]:
        """Optimize LLM prompts"""
        ctx = {
            "task": task,
            "current_prompt": current_prompt,
            "issues": issues,
            "action": "prompt_optimization"
        }

        prompt = f"""
        Optimize this LLM prompt:

        Task: {task}

        Current Prompt:
        {current_prompt}

        Issues:
        {chr(10).join(f'- {issue}' for issue in issues)}

        Provide:
        1. **Optimized Prompt**: Improved version
        2. **Changes Made**: What you changed and why
        3. **Prompt Engineering Techniques**: Applied techniques
        4. **Expected Improvements**: What should improve
        5. **Testing Strategy**: How to validate

        Use best practices like few-shot examples, clear instructions.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "optimized_prompt": response.content,
        }
```

### 3.5 Designer Agent

```python
# backend/agents/specialized/agno_designer.py
"""
Designer Agent (Agno-based)
"""
from typing import List, Dict, Any

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse


class AgnoDesignerAgent(AgnoSquadAgent):
    """Designer Agent (Agno-based)"""

    def get_capabilities(self) -> List[str]:
        return [
            "create_wireframes",
            "design_ui_components",
            "create_design_system",
            "review_ui_implementation",
            "conduct_ux_research",
            "create_prototypes",
        ]

    async def create_wireframes(
        self,
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create wireframes for feature"""
        ctx = {
            "requirements": requirements,
            "action": "wireframe_creation"
        }

        prompt = f"""
        Create wireframes for:

        Feature: {requirements.get('title')}
        Description: {requirements.get('description')}
        User Stories: {requirements.get('user_stories', [])}

        Provide:
        1. **Layout Structure**: Header, content, footer
        2. **Key UI Elements**: Buttons, forms, lists
        3. **Navigation Flow**: How users move through UI
        4. **Responsive Breakpoints**: Mobile, tablet, desktop
        5. **Accessibility Considerations**: ARIA, keyboard nav
        6. **Design Rationale**: Why these choices

        Describe wireframes in detail (text-based for now).
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "wireframes": response.content,
        }

    async def create_design_system(
        self,
        brand_guidelines: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create design system"""
        ctx = {
            "brand_guidelines": brand_guidelines,
            "action": "design_system"
        }

        prompt = f"""
        Create design system for:

        Brand: {brand_guidelines.get('name')}
        Colors: {brand_guidelines.get('colors', [])}
        Typography: {brand_guidelines.get('typography', {})}

        Provide:
        1. **Color Palette**: Primary, secondary, neutrals
        2. **Typography Scale**: Headings, body, captions
        3. **Spacing System**: 4px/8px grid
        4. **Component Library**: Button, input, card variants
        5. **Iconography**: Style and usage
        6. **Accessibility**: Contrast ratios, text sizes
        7. **Usage Guidelines**: When to use what

        Create a scalable, consistent system.
        """

        response = await self.process_message(prompt, context=ctx)

        return {
            "design_system": response.content,
        }
```

---

## 🏭 Part 4: Update AgentFactory (Day 5, 2 hours)

### 4.1 Support Both Custom and Agno Agents

```python
# backend/agents/factory.py (UPDATE)
"""
Agent Factory - Updated to support both Custom and Agno agents
"""
from typing import Dict, Optional, Literal
from uuid import UUID

from backend.agents.base_agent import BaseSquadAgent, AgentConfig as CustomConfig
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig as AgnoConfig

# Custom agents
from backend.agents.specialized.project_manager import ProjectManagerAgent
from backend.agents.specialized.tech_lead import TechLeadAgent
# ... other custom agents

# Agno agents
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
from backend.agents.specialized.agno_designer import AgnoDesignerAgent


# Custom agent registry
AGENT_REGISTRY = {
    "project_manager": ProjectManagerAgent,
    "tech_lead": TechLeadAgent,
    # ... other custom agents
}

# Agno agent registry
AGNO_AGENT_REGISTRY = {
    "project_manager": AgnoProjectManagerAgent,
    "tech_lead": AgnoTechLeadAgent,
    "backend_developer": AgnoBackendDeveloperAgent,
    "frontend_developer": AgnoFrontendDeveloperAgent,
    "tester": AgnoQATesterAgent,
    "solution_architect": AgnoSolutionArchitectAgent,
    "devops_engineer": AgnoDevOpsEngineerAgent,
    "ai_engineer": AgnoAIEngineerAgent,
    "designer": AgnoDesignerAgent,
}


class AgentFactory:
    """Factory for creating AI agents (supports both custom and Agno)"""

    _agents: Dict[str, BaseSquadAgent | AgnoSquadAgent] = {}

    @staticmethod
    def create_agent(
        agent_id: UUID,
        role: str,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        specialization: Optional[str] = None,
        system_prompt: Optional[str] = None,
        mcp_client=None,
        use_agno: bool = True,  # Default to Agno!
        session_id: Optional[str] = None,
    ):
        """
        Create an agent instance.

        Args:
            agent_id: Unique identifier
            role: Agent role
            llm_provider: LLM provider
            llm_model: LLM model
            temperature: Temperature
            specialization: Optional specialization
            system_prompt: Optional custom system prompt
            mcp_client: Optional MCP client
            use_agno: Use Agno agents (default: True)
            session_id: Optional session ID (Agno only)

        Returns:
            Agent instance
        """
        if use_agno:
            # Use Agno agent
            agent_class = AGNO_AGENT_REGISTRY.get(role)
            if not agent_class:
                raise ValueError(f"No Agno agent found for role: {role}")

            config = AgnoConfig(
                role=role,
                specialization=specialization,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature,
                system_prompt=system_prompt
            )

            agent = agent_class(
                config=config,
                mcp_client=mcp_client,
                session_id=session_id
            )
        else:
            # Use custom agent (backward compatibility)
            agent_class = AGENT_REGISTRY.get(role)
            if not agent_class:
                raise ValueError(f"No custom agent found for role: {role}")

            config = CustomConfig(
                role=role,
                specialization=specialization,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature,
                system_prompt=system_prompt
            )

            agent = agent_class(config=config, mcp_client=mcp_client)

        # Store agent
        AgentFactory._agents[str(agent_id)] = agent

        return agent

    @staticmethod
    def get_agent(agent_id: UUID):
        """Get existing agent by ID"""
        return AgentFactory._agents.get(str(agent_id))

    @staticmethod
    def remove_agent(agent_id: UUID):
        """Remove agent from registry"""
        if str(agent_id) in AgentFactory._agents:
            del AgentFactory._agents[str(agent_id)]

    @staticmethod
    def get_supported_roles() -> list[str]:
        """Get all supported roles"""
        # Return union of both registries
        return list(set(list(AGENT_REGISTRY.keys()) + list(AGNO_AGENT_REGISTRY.keys())))

    @staticmethod
    def clear_all_agents():
        """Clear all agents (for testing)"""
        AgentFactory._agents = {}
```

---

## ✅ Day 4-5 Completion Checklist

- [ ] All 8 agents migrated to Agno
- [ ] AgentFactory supports both frameworks
- [ ] Tests created for each agent
- [ ] All agents tested with capabilities
- [ ] Migration utilities created
- [ ] Documentation updated
- [ ] Performance benchmarks for all agents

---

## 🎯 Migration Summary

**Agents Migrated:**
1. ✅ Project Manager (Day 2-3)
2. ✅ Tech Lead (Day 4)
3. ✅ Backend Developer (Day 4)
4. ✅ Frontend Developer (Day 4)
5. ✅ QA Tester (Day 5)
6. ✅ Solution Architect (Day 5)
7. ✅ DevOps Engineer (Day 5)
8. ✅ AI Engineer (Day 5)
9. ✅ Designer (Day 5)

**Total: 9/9 Specialized Agents on Agno! 🎉**

---

## 📊 Expected Results

**Code Reduction:**
- Custom base agent: 909 lines
- Custom specialized agents: 3,323 lines
- **Total custom code: 4,232 lines**

**Agno Implementation:**
- AgnoSquadAgent wrapper: ~300 lines
- Agno specialized agents: ~2,800 lines (less code due to Agno features)
- **Total Agno code: 3,100 lines**

**Reduction: ~1,100 lines (26% less code!)**

**Benefits:**
- ✅ Persistent conversation history
- ✅ Persistent memory
- ✅ Session resumption
- ✅ Faster agent creation (14x)
- ✅ Better multi-turn conversations
- ✅ Less maintenance

---

## 🚀 Next Steps (Week 2)

**Days 6-7:**
- Integrate Agno agents with Context Manager
- Update Message Bus to work with both frameworks
- Migrate Delegation Engine

**Days 8-10:**
- Update Collaboration Patterns
- Update API endpoints
- Update test suite

---

**End of Week 1**

Amazing progress! All 9 specialized agents now use Agno framework!

**Next:** [Week 2, Day 6-7: Integration →](./05_week2_day6-7_implementation.md)
