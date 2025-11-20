"""
AI/ML Project Manager Agent

The AI/ML Project Manager agent specializes in managing AI/ML projects,
coordinating data science teams, and understanding ML-specific workflows
and challenges.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse
from backend.agents.specialized.agno_project_manager import (
    AgnoProjectManagerAgent,
    TicketReview,
    TaskBreakdown,
)
from backend.schemas.agent_message import (
    TaskAssignment,
    StatusRequest,
    Question,
    HumanInterventionRequired,
    Standup,
)


class AgnoAIMLProjectManagerAgent(AgnoProjectManagerAgent):
    """
    AI/ML Project Manager Agent (Agno-Powered) - Specialized ML Project Orchestrator

    Extends the base Project Manager with AI/ML-specific capabilities:
    - Understands ML project lifecycle (research → development → deployment)
    - Coordinates data scientists, data engineers, and ML engineers
    - Manages ML-specific workflows (experiments, model training, deployment)
    - Handles ML project challenges (data quality, model performance, drift)
    - Coordinates with specialized AI/ML roles
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of AI/ML PM capabilities (includes base PM + ML-specific)

        Returns:
            List of capability names
        """
        base_capabilities = super().get_capabilities()
        
        ml_specific_capabilities = [
            # ML-specific orchestration
            "manage_ml_project_lifecycle",
            "coordinate_ml_experiments",
            "manage_model_deployment",
            "handle_data_quality_issues",
            "coordinate_feature_engineering",
            "manage_model_performance",
            "handle_model_drift",
            "coordinate_ml_team",
            "estimate_ml_task_complexity",
            "plan_ml_infrastructure",
        ]
        
        return base_capabilities + ml_specific_capabilities

    async def manage_ml_project_lifecycle(
        self,
        project_phase: str,
        team_composition: List[Dict[str, Any]],
        current_status: Dict[str, Any],
    ) -> AgentResponse:
        """
        Manage ML project through its lifecycle phases.

        Args:
            project_phase: Current phase (research, development, deployment, monitoring)
            team_composition: Available team members
            current_status: Current project status

        Returns:
            AgentResponse with lifecycle management plan
        """
        context = {
            "phase": project_phase,
            "team": team_composition,
            "status": current_status,
            "action": "ml_lifecycle_management"
        }

        team_str = "\n".join([
            f"- {m.get('role')} ({m.get('specialization', 'general')})"
            for m in team_composition
        ])

        prompt = f"""
        Manage ML project lifecycle:

        Current Phase: {project_phase}
        Team Composition:
        {team_str}
        Current Status: {current_status}

        Please provide:

        1. **Phase Assessment**:
           - Are we on track for this phase?
           - What's needed to complete this phase?
           - Risks and blockers

        2. **Team Coordination**:
           - Tasks for data scientists
           - Tasks for data engineers
           - Tasks for ML engineers
           - Dependencies between roles

        3. **Next Phase Preparation**:
           - What's needed for next phase?
           - Prerequisites to complete
           - Resource requirements

        4. **ML-Specific Considerations**:
           - Experiment tracking needs
           - Model versioning requirements
           - Data pipeline dependencies
           - Infrastructure needs

        5. **Timeline & Milestones**:
           - Phase completion timeline
           - Key milestones
           - Critical path items

        6. **Risk Management**:
           - ML-specific risks
           - Mitigation strategies
           - Contingency plans

        Understand ML project nuances.
        """

        return await self.process_message(prompt, context=context)

    async def coordinate_ml_experiments(
        self,
        experiment_goals: List[str],
        available_resources: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Coordinate ML experiments across the team.

        Args:
            experiment_goals: Goals for experiments
            available_resources: Available compute/data resources
            constraints: Optional constraints

        Returns:
            AgentResponse with experiment coordination plan
        """
        context = {
            "goals": experiment_goals,
            "resources": available_resources,
            "constraints": constraints,
            "action": "experiment_coordination"
        }

        prompt = f"""
        Coordinate ML experiments:

        Experiment Goals:
        {chr(10).join([f'- {g}' for g in experiment_goals])}

        Available Resources: {available_resources}
        Constraints: {constraints if constraints else 'None'}

        Please provide:

        1. **Experiment Planning**:
           - Experiment priorities
           - Resource allocation
           - Timeline

        2. **Team Assignment**:
           - Which data scientists for which experiments
           - Collaboration needs
           - Parallel vs. sequential experiments

        3. **Resource Management**:
           - Compute resource allocation
           - Data access coordination
           - Experiment tracking setup

        4. **Coordination Strategy**:
           - How to avoid duplicate work
           - Knowledge sharing approach
           - Result synthesis plan

        5. **Success Criteria**:
           - How to evaluate experiments
           - Decision criteria
           - Next steps based on results

        Optimize for learning and efficiency.
        """

        return await self.process_message(prompt, context=context)

    async def manage_model_deployment(
        self,
        model_info: Dict[str, Any],
        deployment_requirements: Dict[str, Any],
        team_members: List[Dict[str, Any]],
    ) -> AgentResponse:
        """
        Manage model deployment process.

        Args:
            model_info: Model information
            deployment_requirements: Deployment requirements
            team_members: Available team members

        Returns:
            AgentResponse with deployment management plan
        """
        context = {
            "model": model_info,
            "requirements": deployment_requirements,
            "team": team_members,
            "action": "deployment_management"
        }

        prompt = f"""
        Manage model deployment:

        Model Info: {model_info}
        Deployment Requirements: {deployment_requirements}
        Team: {[m.get('role') for m in team_members]}

        Please provide:

        1. **Deployment Plan**:
           - Deployment stages
           - Team responsibilities
           - Timeline

        2. **Coordination Needs**:
           - Data engineer tasks (data pipeline)
           - ML engineer tasks (infrastructure, serving)
           - Data scientist tasks (validation, monitoring)

        3. **Risk Assessment**:
           - Deployment risks
           - Rollback plan
           - Monitoring needs

        4. **Success Criteria**:
           - Deployment success metrics
           - Performance benchmarks
           - Acceptance criteria

        5. **Post-Deployment**:
           - Monitoring setup
           - Team handoff
           - Documentation needs

        Ensure smooth deployment coordination.
        """

        return await self.process_message(prompt, context=context)

    async def handle_data_quality_issues(
        self,
        quality_issue: Dict[str, Any],
        impact_assessment: Dict[str, Any],
    ) -> AgentResponse:
        """
        Handle data quality issues that affect ML projects.

        Args:
            quality_issue: Description of quality issue
            impact_assessment: Impact on ML project

        Returns:
            AgentResponse with issue resolution plan
        """
        context = {
            "issue": quality_issue,
            "impact": impact_assessment,
            "action": "data_quality_management"
        }

        prompt = f"""
        Handle data quality issue:

        Issue: {quality_issue}
        Impact: {impact_assessment}

        Please provide:

        1. **Issue Assessment**:
           - Severity and urgency
           - Affected components
           - Root cause analysis

        2. **Resolution Plan**:
           - Immediate actions
           - Data engineer tasks
           - Data scientist validation
           - Timeline

        3. **Impact Mitigation**:
           - How to minimize project impact
           - Workarounds
           - Alternative data sources

        4. **Prevention**:
           - How to prevent recurrence
           - Process improvements
           - Monitoring enhancements

        5. **Communication**:
           - Stakeholder updates
           - Timeline adjustments
           - Risk communication

        Minimize project disruption.
        """

        return await self.process_message(prompt, context=context)

    async def estimate_ml_task_complexity(
        self,
        task_description: str,
        task_type: str,
        data_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate complexity for ML-specific tasks.

        Args:
            task_description: Task description
            task_type: Type of ML task (modeling, data pipeline, deployment, etc.)
            data_context: Optional data context

        Returns:
            Dictionary with complexity estimate
        """
        context = {
            "task": task_description,
            "type": task_type,
            "data": data_context,
            "action": "ml_complexity_estimation"
        }

        prompt = f"""
        Estimate ML task complexity:

        Task: {task_description}
        Task Type: {task_type}
        Data Context: {data_context if data_context else 'Not provided'}

        Please provide:

        1. **Complexity Factors**:
           - Data complexity
           - Model complexity
           - Infrastructure complexity
           - Integration complexity

        2. **Effort Estimation**:
           - Data preparation time
           - Development time
           - Testing time
           - Deployment time
           - Total estimate

        3. **Risk Assessment**:
           - Technical risks
           - Data risks
           - Timeline risks

        4. **Resource Requirements**:
           - Team members needed
           - Compute resources
           - Data access needs

        5. **Dependencies**:
           - Prerequisites
           - Blocking tasks
           - External dependencies

        Consider ML-specific challenges.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "complexity_score": self._extract_complexity_score(response.content),
            "effort_estimate": self._extract_effort(response.content),
            "risks": self._extract_risks(response.content),
            "dependencies": self._extract_dependencies(response.content),
            "analysis": response.content,
        }

    async def coordinate_ml_team(
        self,
        project_goals: List[str],
        team_members: List[Dict[str, Any]],
        current_tasks: List[Dict[str, Any]],
    ) -> AgentResponse:
        """
        Coordinate ML team members effectively.

        Args:
            project_goals: Project goals
            team_members: Team member information
            current_tasks: Current active tasks

        Returns:
            AgentResponse with team coordination plan
        """
        context = {
            "goals": project_goals,
            "team": team_members,
            "tasks": current_tasks,
            "action": "ml_team_coordination"
        }

        team_str = "\n".join([
            f"- {m.get('role')}: {m.get('specialization', 'general')} - {m.get('status', 'available')}"
            for m in team_members
        ])

        prompt = f"""
        Coordinate ML team:

        Project Goals:
        {chr(10).join([f'- {g}' for g in project_goals])}

        Team Members:
        {team_str}

        Current Tasks: {len(current_tasks)} active tasks

        Please provide:

        1. **Team Assessment**:
           - Current workload
           - Skill utilization
           - Bottlenecks

        2. **Task Assignment**:
           - Optimal task assignments
           - Collaboration opportunities
           - Parallel work streams

        3. **Communication Plan**:
           - Regular syncs needed
           - Knowledge sharing
           - Decision points

        4. **Resource Optimization**:
           - Compute resource sharing
           - Data access coordination
           - Tool standardization

        5. **Team Development**:
           - Learning opportunities
           - Cross-training needs
           - Skill gaps

        Optimize team productivity and collaboration.
        """

        return await self.process_message(prompt, context=context)

    # Helper methods for ML-specific parsing

    def _extract_complexity_score(self, content: str) -> Optional[float]:
        """Extract complexity score from response"""
        import re
        pattern = r'complexity[:\s]+(\d+(?:\.\d+)?)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def _extract_effort(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract effort estimates from response"""
        # Simple extraction - in production, use structured outputs
        return {
            "total_hours": None,
            "breakdown": {}
        }

    def _extract_risks(self, content: str) -> List[str]:
        """Extract risks from response"""
        risks = []
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['risk', 'challenge', 'concern']):
                if len(line) < 200:
                    risks.append(line.strip())
        return risks[:5]

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from response"""
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

