"""
Scenario 2: REST API Endpoint Implementation

Tests agent's ability to:
- Implement new API endpoints
- Add validation and error handling
- Write tests
- Integrate with frontend
"""

import asyncio
from typing import List
from .base_scenario import BaseScenario


class RestAPIScenario(BaseScenario):
    """
    Real-World Scenario: Implement User Profile Update Endpoint

    Context:
        Feature request: "Add user profile update endpoint with validation"

    Workflow:
        1. PM defines requirements
        2. Backend Dev implements endpoint
        3. Backend Dev adds tests
        4. Frontend Dev integrates
        5. QA validates

    Success Criteria:
        - Endpoint works correctly
        - Validation prevents invalid data
        - Frontend form functional
        - All tests pass
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "REST API Endpoint Implementation"
        self.expected_duration_minutes = 45

    async def setup_scenario(self):
        """Set up API development scenario"""
        self.squad_id = await self.create_squad_with_agents(
            squad_name="API Development Squad",
            agent_roles=["project_manager", "backend_developer", "frontend_developer", "qa_tester"]
        )

        self.add_success_criterion("Endpoint implemented")
        self.add_success_criterion("Validation added")
        self.add_success_criterion("Tests pass")
        self.add_success_criterion("Frontend integrated")

    async def run_scenario(self):
        """Execute API development workflow"""

        # Step 1: PM defines requirements
        step1 = self.add_step(
            "PM defines API requirements",
            agent_role="project_manager",
            expected_tools=["create_task", "write_file"]
        )

        self.task_id = await self.create_task(
            squad_id=self.squad_id,
            title="Implement user profile update endpoint",
            description="""
            **Requirements:**
            - Endpoint: PATCH /api/v1/users/{id}/profile
            - Fields: name, email, bio, avatar_url
            - Validation:
              - email must be valid format
              - name: 2-100 characters
              - bio: max 500 characters
              - avatar_url: valid URL
            - Authentication: JWT required
            - Errors:
              - 401 if not authenticated
              - 403 if updating other user
              - 404 if user not found
              - 400 if validation fails
              - 409 if email already taken
            """,
            priority="high"
        )
        self.complete_step(step1, success=True)

        # Step 2: Backend Dev implements endpoint
        step2 = self.add_step(
            "Backend Dev implements endpoint",
            agent_role="backend_developer",
            expected_tools=[
                "read_file", "write_file", "edit_file",
                "run_tests", "api_test"
            ]
        )

        self.track_tool_usage("write_file", success=True, execution_time=3.0)
        self.track_tool_usage("edit_file", success=True, execution_time=2.0)
        self.mark_tool_missing("api_test")

        self.complete_step(step2, success=True)
        self.mark_criterion_met("Endpoint implemented")

        # Step 3: Add validation
        step3 = self.add_step(
            "Add Pydantic schema validation",
            agent_role="backend_developer",
            expected_tools=["write_file", "schema_validation"]
        )

        self.track_tool_usage("write_file", success=True, execution_time=1.5)
        self.mark_tool_missing("schema_validation")

        self.complete_step(step3, success=True)
        self.mark_criterion_met("Validation added")

        # Step 4: Backend Dev adds tests
        step4 = self.add_step(
            "Add integration tests",
            agent_role="backend_developer",
            expected_tools=["write_file", "run_tests", "code_coverage"]
        )

        self.track_tool_usage("write_file", success=True, execution_time=2.5)
        self.mark_tool_missing("run_tests")
        self.mark_tool_missing("code_coverage")

        self.complete_step(step4, success=True)
        self.mark_criterion_met("Tests pass")

        # Step 5: Frontend Dev integrates
        step5 = self.add_step(
            "Frontend integrates API",
            agent_role="frontend_developer",
            expected_tools=["write_file", "edit_file", "npm_install", "npm_test"]
        )

        self.track_tool_usage("write_file", success=True, execution_time=3.0)
        self.mark_tool_missing("npm_install")
        self.mark_tool_missing("npm_test")

        self.complete_step(step5, success=True)
        self.mark_criterion_met("Frontend integrated")

        # Step 6: Execute task
        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=90)
        except Exception as e:
            self.metrics.errors.append(f"Execution failed: {e}")

    async def validate_results(self) -> bool:
        """Validate API implementation successful"""
        return (
            self.metrics.steps_completed >= 4 and
            self.metrics.success_criteria_met >= 3 and
            self.execution_id is not None
        )

    def get_expected_tools(self) -> List[str]:
        """Tools needed for API development"""
        return [
            "read_file", "write_file", "edit_file",
            "run_tests", "code_coverage",
            "api_test", "schema_validation",
            "npm_install", "npm_test",
            "database_query", "migration_tool",
            "api_documentation", "git_commit"
        ]
