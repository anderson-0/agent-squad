"""
Delegation Engine

Analyzes tasks and intelligently delegates work to the most appropriate agents.
Handles load balancing, skill matching, and task breakdown.
"""
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.squad import SquadMember
from backend.services.agent_service import AgentService


class DelegationEngine:
    """
    Smart Task Delegation Engine

    Analyzes task requirements and delegates to the best-suited agents.
    Considers agent roles, specializations, current workload, and task complexity.
    """

    # Role priorities for different task types
    TASK_TYPE_PRIORITIES = {
        "api_endpoint": ["backend_developer", "tech_lead", "qa_tester"],
        "ui_component": ["frontend_developer", "designer", "qa_tester"],
        "database_schema": ["backend_developer", "solution_architect", "tech_lead"],
        "bug_fix": ["backend_developer", "frontend_developer", "tech_lead"],
        "refactoring": ["tech_lead", "backend_developer", "frontend_developer"],
        "testing": ["qa_tester", "backend_developer", "frontend_developer"],
        "documentation": ["tech_lead", "solution_architect"],
        "deployment": ["devops_engineer", "backend_developer"],
        "ai_feature": ["ai_engineer", "backend_developer", "data_scientist"],
        "design": ["designer", "frontend_developer"],
    }

    def __init__(self):
        """Initialize delegation engine"""
        pass

    async def analyze_task_requirements(
        self,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze task to determine requirements.

        Args:
            task: Task dictionary with title, description, acceptance_criteria

        Returns:
            Dictionary with task requirements
        """
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()
        acceptance_criteria = [c.lower() for c in task.get("acceptance_criteria", [])]

        # Combine all text for analysis
        full_text = f"{title} {description} {' '.join(acceptance_criteria)}"

        # Detect task type based on keywords
        task_type = self._detect_task_type(full_text)

        # Detect required skills
        required_skills = self._detect_required_skills(full_text)

        # Estimate complexity (1-10)
        complexity = self._estimate_complexity(task, full_text)

        # Detect if frontend or backend work
        has_frontend = self._has_frontend_work(full_text)
        has_backend = self._has_backend_work(full_text)
        has_testing = self._has_testing_work(full_text)

        return {
            "task_type": task_type,
            "required_skills": required_skills,
            "complexity": complexity,
            "has_frontend": has_frontend,
            "has_backend": has_backend,
            "has_testing": has_testing,
            "requires_design": self._requires_design(full_text),
            "requires_database": self._requires_database(full_text),
            "requires_devops": self._requires_devops(full_text),
            "estimated_subtasks": self._estimate_subtask_count(complexity, has_frontend, has_backend),
        }

    async def find_best_agent(
        self,
        db: AsyncSession,
        squad_id: UUID,
        requirements: Dict[str, Any],
        exclude_ids: Optional[List[UUID]] = None,
    ) -> Optional[SquadMember]:
        """
        Find the best agent for the task requirements.

        Args:
            db: Database session
            squad_id: Squad UUID
            requirements: Task requirements from analyze_task_requirements
            exclude_ids: Optional list of agent IDs to exclude

        Returns:
            Best matching squad member or None
        """
        # Get all active squad members
        members = await AgentService.get_squad_members(db, squad_id, active_only=True)

        if not members:
            return None

        # Filter out excluded agents
        if exclude_ids:
            members = [m for m in members if m.id not in exclude_ids]

        # Get required roles based on task type
        task_type = requirements.get("task_type", "general")
        preferred_roles = self.TASK_TYPE_PRIORITIES.get(task_type, [])

        # Score each agent
        scored_agents = []
        for member in members:
            score = self._score_agent(member, requirements, preferred_roles)
            scored_agents.append((member, score))

        # Sort by score (descending)
        scored_agents.sort(key=lambda x: x[1], reverse=True)

        # Return best agent
        if scored_agents:
            return scored_agents[0][0]

        return None

    async def delegate_to_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        subtask: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create task delegation for a specific agent.

        Args:
            db: Database session
            agent_id: Agent UUID
            subtask: Subtask details
            context: Task context (from RAG, etc.)

        Returns:
            Delegation details
        """
        agent = await AgentService.get_squad_member(db, agent_id)

        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        delegation = {
            "agent_id": str(agent_id),
            "agent_role": agent.role,
            "subtask": subtask,
            "context": context,
            "delegated_at": None,  # Will be set when message is sent
            "status": "delegated",
        }

        return delegation

    async def break_down_task(
        self,
        task: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Break down a complex task into subtasks.

        Args:
            task: Original task
            requirements: Task requirements

        Returns:
            List of subtasks
        """
        subtasks = []

        # Always start with planning
        subtasks.append({
            "title": f"Plan implementation for: {task.get('title')}",
            "description": "Analyze requirements and create implementation plan",
            "type": "planning",
            "priority": "high",
            "dependencies": [],
        })

        # Add backend subtasks if needed
        if requirements.get("has_backend"):
            subtasks.append({
                "title": f"Implement backend for: {task.get('title')}",
                "description": "Implement API endpoints, services, and business logic",
                "type": "backend_implementation",
                "priority": "high",
                "dependencies": ["planning"],
            })

        # Add frontend subtasks if needed
        if requirements.get("has_frontend"):
            subtasks.append({
                "title": f"Implement frontend for: {task.get('title')}",
                "description": "Implement UI components and integrate with backend",
                "type": "frontend_implementation",
                "priority": "high",
                "dependencies": ["planning", "backend_implementation"] if requirements.get("has_backend") else ["planning"],
            })

        # Add testing subtask if needed
        if requirements.get("has_testing") or requirements.get("complexity", 0) >= 5:
            subtasks.append({
                "title": f"Test: {task.get('title')}",
                "description": "Create and execute test plan, verify acceptance criteria",
                "type": "testing",
                "priority": "high",
                "dependencies": ["backend_implementation", "frontend_implementation"] if requirements.get("has_frontend") else ["backend_implementation"],
            })

        # Add code review subtask
        subtasks.append({
            "title": f"Code review for: {task.get('title')}",
            "description": "Review implementation and provide feedback",
            "type": "code_review",
            "priority": "medium",
            "dependencies": [s["type"] for s in subtasks if s["type"].endswith("_implementation")],
        })

        return subtasks

    # Helper methods

    def _detect_task_type(self, text: str) -> str:
        """Detect task type from text"""
        keywords_map = {
            "api_endpoint": ["api", "endpoint", "route", "rest", "graphql"],
            "ui_component": ["component", "ui", "interface", "button", "form", "page"],
            "database_schema": ["database", "schema", "migration", "table", "model"],
            "bug_fix": ["bug", "fix", "issue", "error", "broken"],
            "refactoring": ["refactor", "cleanup", "improve", "optimize"],
            "testing": ["test", "testing", "qa", "quality"],
            "documentation": ["document", "docs", "readme", "guide"],
            "deployment": ["deploy", "deployment", "ci/cd", "pipeline"],
            "ai_feature": ["ai", "ml", "machine learning", "model", "prediction"],
            "design": ["design", "mockup", "wireframe", "figma"],
        }

        for task_type, keywords in keywords_map.items():
            if any(keyword in text for keyword in keywords):
                return task_type

        return "general"

    def _detect_required_skills(self, text: str) -> List[str]:
        """Detect required skills from text"""
        skills = []

        skill_keywords = {
            "python": ["python", "fastapi", "django", "flask"],
            "javascript": ["javascript", "typescript", "js", "ts"],
            "react": ["react", "next.js", "nextjs"],
            "database": ["sql", "postgres", "mysql", "mongodb"],
            "api": ["api", "rest", "graphql"],
            "testing": ["test", "pytest", "jest", "cypress"],
            "devops": ["docker", "kubernetes", "k8s", "ci/cd"],
            "design": ["figma", "design", "ui/ux"],
        }

        for skill, keywords in skill_keywords.items():
            if any(keyword in text for keyword in keywords):
                skills.append(skill)

        return skills

    def _estimate_complexity(self, task: Dict[str, Any], text: str) -> int:
        """Estimate task complexity (1-10)"""
        complexity = 3  # Default medium complexity

        # Increase for multiple acceptance criteria
        criteria_count = len(task.get("acceptance_criteria", []))
        if criteria_count > 5:
            complexity += 2
        elif criteria_count > 3:
            complexity += 1

        # Increase for complex keywords
        complex_keywords = ["architecture", "migration", "refactor", "integration", "complex"]
        if any(keyword in text for keyword in complex_keywords):
            complexity += 2

        # Increase if multiple areas involved
        areas = [
            self._has_frontend_work(text),
            self._has_backend_work(text),
            self._requires_database(text),
            self._requires_devops(text),
        ]
        complexity += sum(areas) - 1  # Subtract 1 so single area doesn't add

        return min(max(complexity, 1), 10)  # Clamp to 1-10

    def _has_frontend_work(self, text: str) -> bool:
        """Check if task involves frontend work"""
        keywords = ["ui", "component", "page", "frontend", "react", "next.js", "interface", "button", "form"]
        return any(keyword in text for keyword in keywords)

    def _has_backend_work(self, text: str) -> bool:
        """Check if task involves backend work"""
        keywords = ["api", "endpoint", "backend", "server", "database", "service", "logic"]
        return any(keyword in text for keyword in keywords)

    def _has_testing_work(self, text: str) -> bool:
        """Check if task explicitly mentions testing"""
        keywords = ["test", "testing", "qa", "verify", "validation"]
        return any(keyword in text for keyword in keywords)

    def _requires_design(self, text: str) -> bool:
        """Check if task requires design work"""
        keywords = ["design", "mockup", "wireframe", "figma", "prototype"]
        return any(keyword in text for keyword in keywords)

    def _requires_database(self, text: str) -> bool:
        """Check if task requires database work"""
        keywords = ["database", "schema", "migration", "table", "model", "sql"]
        return any(keyword in text for keyword in keywords)

    def _requires_devops(self, text: str) -> bool:
        """Check if task requires devops work"""
        keywords = ["deploy", "deployment", "ci/cd", "docker", "kubernetes", "pipeline"]
        return any(keyword in text for keyword in keywords)

    def _estimate_subtask_count(self, complexity: int, has_frontend: bool, has_backend: bool) -> int:
        """Estimate number of subtasks"""
        count = 1  # Base

        if complexity >= 7:
            count += 2
        elif complexity >= 4:
            count += 1

        if has_frontend:
            count += 1
        if has_backend:
            count += 1

        return count

    def _score_agent(
        self,
        agent: SquadMember,
        requirements: Dict[str, Any],
        preferred_roles: List[str],
    ) -> float:
        """
        Score an agent for task suitability.

        Args:
            agent: Squad member
            requirements: Task requirements
            preferred_roles: Preferred roles for task

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Role match (highest priority)
        if agent.role in preferred_roles:
            role_index = preferred_roles.index(agent.role)
            # First preferred role gets 10 points, decreasing by 2 for each subsequent role
            score += 10 - (role_index * 2)

        # Specialization match
        required_skills = requirements.get("required_skills", [])
        if agent.specialization:
            spec_lower = agent.specialization.lower()
            for skill in required_skills:
                if skill in spec_lower:
                    score += 2

        # Task type specific bonuses
        task_type = requirements.get("task_type", "general")
        role_task_match = {
            "backend_developer": ["api_endpoint", "database_schema", "backend", "bug_fix"],
            "frontend_developer": ["ui_component", "frontend", "design"],
            "qa_tester": ["testing", "bug_fix"],
            "tech_lead": ["refactoring", "code_review", "architecture"],
            "devops_engineer": ["deployment", "ci/cd"],
        }

        matching_tasks = role_task_match.get(agent.role, [])
        if task_type in matching_tasks:
            score += 5

        return score
