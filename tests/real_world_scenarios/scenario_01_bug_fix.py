"""
Scenario 1: Bug Fix with Root Cause Analysis

Tests agent's ability to:
- Investigate production bugs
- Analyze logs and stack traces
- Identify root causes
- Implement fixes
- Add tests to prevent regression
"""

import asyncio
from typing import List
from .base_scenario import BaseScenario, ScenarioStatus


class BugFixScenario(BaseScenario):
    """
    Real-World Scenario: Production Login Bug

    Context:
        Production bug reported: "User login fails intermittently with 500 error"

    Workflow:
        1. PM triages bug, creates task
        2. Backend Dev investigates (reads logs, code)
        3. Backend Dev identifies root cause (race condition in Redis)
        4. Backend Dev implements fix (Redis lock mechanism)
        5. QA Tester validates fix and tests edge cases

    Success Criteria:
        - Root cause identified correctly
        - Fix implemented
        - Tests added
        - No new bugs introduced
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Bug Fix with Root Cause Analysis"
        self.expected_duration_minutes = 30

    async def setup_scenario(self):
        """Set up bug fix scenario"""
        # Create squad with PM, Backend Dev, QA Tester
        self.squad_id = await self.create_squad_with_agents(
            squad_name="Bug Fix Squad",
            agent_roles=["project_manager", "backend_developer", "qa_tester"]
        )

        # Define success criteria
        self.add_success_criterion("Root cause identified")
        self.add_success_criterion("Fix implemented")
        self.add_success_criterion("Tests added")
        self.add_success_criterion("Fix validated")

    async def run_scenario(self):
        """Execute bug fix workflow"""

        # Step 1: PM creates bug task
        step1 = self.add_step(
            description="PM triages bug and creates task",
            agent_role="project_manager",
            expected_tools=["create_task"]
        )
        step1.started_at = asyncio.get_event_loop().time()

        try:
            self.task_id = await self.create_task(
                squad_id=self.squad_id,
                title="Fix: User login fails intermittently with 500 error",
                description="""
                **Bug Report:**
                - Issue: User login fails intermittently
                - Error: HTTP 500 Internal Server Error
                - Frequency: ~5% of login attempts
                - Suspected cause: Race condition in authentication flow

                **Steps to Reproduce:**
                1. Multiple users try to login simultaneously
                2. Some requests fail with 500 error
                3. Retry usually succeeds

                **Expected:**
                - All login attempts should succeed or return proper error (401)

                **Investigation Needed:**
                - Review authentication code
                - Check Redis cache usage
                - Analyze error logs
                - Identify race condition

                **Fix Required:**
                - Implement proper locking mechanism
                - Add error handling
                - Add tests for concurrent logins
                """,
                priority="high"
            )
            self.complete_step(step1, success=True)
            self.mark_criterion_met("Task created")
        except Exception as e:
            self.complete_step(step1, success=False, error_message=str(e))
            return

        # Step 2: Backend Dev investigates
        step2 = self.add_step(
            description="Backend Dev investigates bug",
            agent_role="backend_developer",
            expected_tools=[
                "read_file",          # Read source code
                "grep_logs",          # Search logs
                "code_search",        # Find related code
                "execute_code"        # Run code to reproduce
            ]
        )
        step2.started_at = asyncio.get_event_loop().time()

        # Track expected tool usage (simulated)
        self.track_tool_usage("read_file", success=True, execution_time=0.5)
        self.track_tool_usage("code_search", success=True, execution_time=1.2)

        # Mark missing tools
        self.mark_tool_missing("grep_logs")
        self.mark_tool_missing("execute_code")

        self.complete_step(step2, success=True)

        # Step 3: Backend Dev identifies root cause
        step3 = self.add_step(
            description="Identify root cause (race condition in Redis cache)",
            agent_role="backend_developer",
            expected_tools=[
                "analyze_code",       # Code analysis
                "redis_inspect",      # Check Redis state
                "debugger"            # Debug race condition
            ]
        )
        step3.started_at = asyncio.get_event_loop().time()

        # Mark missing advanced tools
        self.mark_tool_missing("redis_inspect")
        self.mark_tool_missing("debugger")

        self.complete_step(step3, success=True)
        self.mark_criterion_met("Root cause identified")

        # Step 4: Backend Dev implements fix
        step4 = self.add_step(
            description="Implement fix (add Redis lock mechanism)",
            agent_role="backend_developer",
            expected_tools=[
                "edit_file",          # Edit source code
                "write_file",         # Create new files
                "git_commit"          # Commit changes
            ]
        )
        step4.started_at = asyncio.get_event_loop().time()

        self.track_tool_usage("edit_file", success=True, execution_time=2.0)
        self.mark_tool_missing("git_commit")

        self.complete_step(step4, success=True)
        self.mark_criterion_met("Fix implemented")

        # Step 5: Backend Dev adds tests
        step5 = self.add_step(
            description="Add tests to prevent regression",
            agent_role="backend_developer",
            expected_tools=[
                "write_file",         # Create test file
                "run_tests",          # Run tests
                "code_coverage"       # Check coverage
            ]
        )
        step5.started_at = asyncio.get_event_loop().time()

        self.track_tool_usage("write_file", success=True, execution_time=1.5)
        self.mark_tool_missing("run_tests")
        self.mark_tool_missing("code_coverage")

        self.complete_step(step5, success=True)
        self.mark_criterion_met("Tests added")

        # Step 6: Execute task (run the workflow)
        step6 = self.add_step(
            description="Execute bug fix task with agents",
            expected_tools=["task_execution"]
        )
        step6.started_at = asyncio.get_event_loop().time()

        try:
            self.execution_id = await self.execute_task(
                task_id=self.task_id,
                squad_id=self.squad_id
            )

            # Wait up to 60 seconds for execution
            execution_data = await self.wait_for_execution(
                execution_id=self.execution_id,
                timeout_seconds=60
            )

            if execution_data.get("status") == "completed":
                self.complete_step(step6, success=True)
            else:
                self.complete_step(
                    step6,
                    success=False,
                    error_message=f"Execution status: {execution_data.get('status')}"
                )

        except asyncio.TimeoutError:
            self.complete_step(step6, success=False, error_message="Execution timed out")
        except Exception as e:
            self.complete_step(step6, success=False, error_message=str(e))

        # Step 7: QA validates fix
        step7 = self.add_step(
            description="QA validates fix works",
            agent_role="qa_tester",
            expected_tools=[
                "run_tests",          # Run test suite
                "load_test",          # Test race condition
                "api_test"            # Test login endpoint
            ]
        )
        step7.started_at = asyncio.get_event_loop().time()

        self.mark_tool_missing("load_test")
        self.mark_tool_missing("api_test")

        self.complete_step(step7, success=True)
        self.mark_criterion_met("Fix validated")

    async def validate_results(self) -> bool:
        """Validate scenario completed successfully"""
        # Check if all critical steps completed
        critical_steps_completed = self.metrics.steps_completed >= 5

        # Check if key criteria met
        criteria_met = self.metrics.success_criteria_met >= 3

        # Check execution completed
        execution_completed = self.execution_id is not None

        return (
            critical_steps_completed and
            criteria_met and
            execution_completed
        )

    def get_expected_tools(self) -> List[str]:
        """Return list of tools expected to be needed"""
        return [
            # File operations
            "read_file",
            "write_file",
            "edit_file",

            # Code operations
            "code_search",
            "grep_logs",
            "execute_code",

            # Testing
            "run_tests",
            "code_coverage",
            "load_test",
            "api_test",

            # Debugging
            "debugger",
            "redis_inspect",

            # Git operations
            "git_commit",
            "git_push",

            # Task execution
            "task_execution"
        ]
