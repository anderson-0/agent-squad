"""
QA Tester Agent

The QA Tester agent is responsible for testing, verification, bug reporting,
and ensuring quality standards are met before tasks are marked complete.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.base_agent import BaseSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    StatusUpdate,
    Question,
    TaskCompletion,
)


class QATesterAgent(BaseSquadAgent):
    """
    QA Tester Agent - Quality Assurance Specialist

    Responsibilities:
    - Create test plans
    - Write and execute tests (unit, integration, E2E)
    - Verify acceptance criteria
    - Report bugs and issues
    - Perform regression testing
    - Test API endpoints
    - Test UI functionality
    - Ensure accessibility standards
    - Verify performance requirements
    - Sign off on completed work

    Note: In Phase 4, this agent will use MCP servers to actually
    run tests and access the codebase. For Phase 3, it plans and reviews.
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of QA Tester capabilities

        Returns:
            List of capability names
        """
        return [
            "create_test_plan",
            "write_test_cases",
            "execute_tests",  # Phase 4: via MCP
            "verify_acceptance_criteria",
            "report_bug",
            "test_api_endpoints",
            "test_ui_functionality",
            "test_accessibility",
            "test_performance",
            "regression_testing",
            "sign_off_task",
        ]

    async def create_test_plan(
        self,
        task: Dict[str, Any],
        implementation_details: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create comprehensive test plan for a task.

        Args:
            task: Task details with acceptance criteria
            implementation_details: Optional implementation details

        Returns:
            Dictionary with test plan
        """
        context = {
            "task": task,
            "implementation": implementation_details,
            "action": "test_planning"
        }

        impl_info = ""
        if implementation_details:
            impl_info = f"""
            Implementation Details:
            {implementation_details}
            """

        prompt = f"""
        Create a comprehensive test plan for this task:

        Task: {task.get('title')}
        Description: {task.get('description')}

        Acceptance Criteria:
        {chr(10).join([f'- {c}' for c in task.get('acceptance_criteria', [])])}

        {impl_info}

        Please create a test plan covering:

        1. **Test Strategy**:
           - What types of tests are needed?
           - Test pyramid (unit, integration, E2E)
           - Priority (P0, P1, P2)

        2. **Unit Tests**:
           - Functions/methods to test
           - Test cases for each
           - Edge cases to cover
           - Mocking strategy

        3. **Integration Tests**:
           - Integration points to test
           - Test scenarios
           - Data setup needed

        4. **API Tests** (if applicable):
           - Endpoints to test
           - Request variations
           - Expected responses
           - Error cases (400, 401, 403, 404, 500)

        5. **UI Tests** (if applicable):
           - User flows to test
           - Interactions to verify
           - Responsive behavior
           - Cross-browser testing

        6. **Acceptance Criteria Verification**:
           - How to verify each criterion
           - Test cases mapped to criteria

        7. **Edge Cases**:
           - Boundary conditions
           - Error scenarios
           - Race conditions
           - Invalid inputs

        8. **Performance Tests** (if needed):
           - Load testing
           - Response times
           - Resource usage

        9. **Accessibility Tests** (if UI):
           - Keyboard navigation
           - Screen reader compatibility
           - ARIA labels
           - Color contrast

        10. **Test Data**:
            - Required test data
            - Data setup/teardown

        Be specific and comprehensive.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "test_plan": response.content,
            "test_types": self._extract_test_types(response.content),
            "priority_tests": self._extract_priority_tests(response.content),
            "test_count_estimate": self._estimate_test_count(response.content),
        }

    async def verify_acceptance_criteria(
        self,
        task: Dict[str, Any],
        implementation: Dict[str, Any],
        test_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify all acceptance criteria are met.

        Args:
            task: Original task with acceptance criteria
            implementation: What was implemented
            test_results: Optional test execution results

        Returns:
            Dictionary with verification results
        """
        context = {
            "task": task,
            "implementation": implementation,
            "test_results": test_results,
            "action": "criteria_verification"
        }

        test_info = ""
        if test_results:
            test_info = f"""
            Test Results:
            - Total Tests: {test_results.get('total', 0)}
            - Passed: {test_results.get('passed', 0)}
            - Failed: {test_results.get('failed', 0)}
            - Failures: {test_results.get('failures', [])}
            """

        prompt = f"""
        Verify acceptance criteria for this task:

        Task: {task.get('title')}

        Acceptance Criteria:
        {chr(10).join([f'{i+1}. {c}' for i, c in enumerate(task.get('acceptance_criteria', []))])}

        What Was Implemented:
        {implementation.get('summary', 'N/A')}

        {test_info}

        For each acceptance criterion, verify:

        1. **Criterion 1**: [restate criterion]
           - Met: Yes/No
           - Evidence: How it was verified
           - Test coverage: Which tests cover this
           - Notes: Any concerns or edge cases

        2. **Criterion 2**: ...
           (Continue for all criteria)

        **Overall Assessment**:
        - All criteria met: Yes/No
        - Criteria met: X/Y
        - Blockers: List any blockers
        - Additional testing needed: Yes/No

        **Sign-off Decision**: APPROVED | NEEDS_FIXES | BLOCKED

        Be thorough and objective.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "verification_result": response.content,
            "all_criteria_met": self._check_all_criteria_met(response.content),
            "criteria_status": self._extract_criteria_status(response.content),
            "sign_off_decision": self._extract_sign_off(response.content),
            "blockers": self._extract_blockers(response.content),
        }

    async def report_bug(
        self,
        title: str,
        description: str,
        steps_to_reproduce: List[str],
        expected_behavior: str,
        actual_behavior: str,
        severity: str,
        developer_id: Optional[UUID] = None,
    ) -> Question:
        """
        Report a bug found during testing.

        Args:
            title: Bug title
            description: Bug description
            steps_to_reproduce: Steps to reproduce
            expected_behavior: What should happen
            actual_behavior: What actually happens
            severity: critical, high, medium, low
            developer_id: Optional developer to notify

        Returns:
            Question message (bug report)
        """
        bug_report = f"""
        **Bug Report**

        **Title**: {title}

        **Severity**: {severity}

        **Description**:
        {description}

        **Steps to Reproduce**:
        {chr(10).join([f'{i+1}. {step}' for i, step in enumerate(steps_to_reproduce)])}

        **Expected Behavior**:
        {expected_behavior}

        **Actual Behavior**:
        {actual_behavior}

        **Environment**:
        - Browser: [if applicable]
        - OS: [if applicable]
        - API version: [if applicable]

        **Suggested Fix** (if any):
        [Optional suggestions]

        Please investigate and fix this issue.
        """

        return Question(
            task_id=f"bug_{title[:30]}",
            question=bug_report,
            context=description,
            recipient=developer_id,
            urgency="high" if severity in ["critical", "high"] else "normal",
        )

    async def test_api_endpoints(
        self,
        endpoints: List[Dict[str, Any]],
        base_url: str,
    ) -> AgentResponse:
        """
        Create API test plan.

        Args:
            endpoints: List of endpoints to test
            base_url: API base URL

        Returns:
            AgentResponse with API test plan
        """
        context = {
            "endpoints": endpoints,
            "base_url": base_url,
            "action": "api_testing"
        }

        endpoints_str = "\n".join([
            f"- {ep.get('method')} {ep.get('path')} - {ep.get('description', '')}"
            for ep in endpoints
        ])

        prompt = f"""
        Create API test plan for these endpoints:

        Base URL: {base_url}

        Endpoints:
        {endpoints_str}

        For each endpoint, create test cases for:

        1. **Happy Path**:
           - Valid request
           - Expected response
           - Status code

        2. **Validation Tests**:
           - Missing required fields
           - Invalid data types
           - Out of range values
           - Malformed requests

        3. **Authentication Tests**:
           - No token (401)
           - Invalid token (401)
           - Expired token (401)
           - Insufficient permissions (403)

        4. **Error Cases**:
           - Not found (404)
           - Conflict (409)
           - Server error (500)

        5. **Edge Cases**:
           - Empty arrays/objects
           - Very large payloads
           - Special characters
           - SQL injection attempts
           - XSS attempts

        6. **Performance**:
           - Response time < 500ms
           - Handles concurrent requests

        Provide curl examples for key test cases.
        """

        return await self.process_message(prompt, context=context)

    async def test_ui_functionality(
        self,
        feature: str,
        user_flows: List[str],
    ) -> AgentResponse:
        """
        Create UI test plan.

        Args:
            feature: Feature name
            user_flows: User flows to test

        Returns:
            AgentResponse with UI test plan
        """
        context = {
            "feature": feature,
            "user_flows": user_flows,
            "action": "ui_testing"
        }

        flows_str = "\n".join([f"- {flow}" for flow in user_flows])

        prompt = f"""
        Create UI test plan for this feature:

        Feature: {feature}

        User Flows:
        {flows_str}

        Create test cases for:

        1. **Functional Tests**:
           For each user flow:
           - Step-by-step interactions
           - Expected UI changes
           - Data displayed correctly
           - Navigation works

        2. **Form Tests** (if applicable):
           - Field validation
           - Error messages
           - Success messages
           - Submit button states (disabled/enabled)

        3. **Interactive Elements**:
           - Buttons clickable
           - Links navigate correctly
           - Dropdowns work
           - Modals open/close
           - Tooltips appear

        4. **Responsive Tests**:
           - Mobile (320px, 375px, 425px)
           - Tablet (768px, 1024px)
           - Desktop (1440px, 1920px)

        5. **Cross-browser** (if needed):
           - Chrome
           - Firefox
           - Safari
           - Edge

        6. **Loading States**:
           - Spinners shown
           - Skeleton UI
           - Error boundaries

        7. **Accessibility**:
           - Keyboard navigation
           - Tab order logical
           - Focus indicators visible
           - ARIA labels present
           - Screen reader compatible

        8. **Visual Regression**:
           - Compare screenshots
           - No layout shifts

        Provide specific test scenarios.
        """

        return await self.process_message(prompt, context=context)

    async def sign_off_task(
        self,
        task_id: str,
        pm_id: UUID,
        verification_summary: str,
        all_tests_passed: bool,
        acceptance_criteria_met: bool,
        notes: Optional[str] = None,
    ) -> TaskCompletion:
        """
        Sign off on completed task after QA verification.

        Args:
            task_id: Task identifier
            pm_id: PM agent ID
            verification_summary: Summary of verification
            all_tests_passed: Whether all tests passed
            acceptance_criteria_met: Whether criteria met
            notes: Optional additional notes

        Returns:
            TaskCompletion message (QA sign-off)
        """
        sign_off_summary = f"""
        QA Verification Complete

        {verification_summary}

        Status:
        - All Tests Passed: {'✓' if all_tests_passed else '✗'}
        - Acceptance Criteria Met: {'✓' if acceptance_criteria_met else '✗'}

        {f'Notes: {notes}' if notes else ''}

        QA Sign-off: {'APPROVED' if all_tests_passed and acceptance_criteria_met else 'NOT APPROVED'}
        """

        return TaskCompletion(
            recipient=pm_id,
            task_id=task_id,
            completion_summary=sign_off_summary,
            deliverables=["QA verification complete"],
            tests_passed=all_tests_passed,
            documentation_updated=True,
            notes=notes,
        )

    # Helper methods

    def _extract_test_types(self, content: str) -> List[str]:
        """Extract test types from plan"""
        types = []
        for test_type in ["unit", "integration", "e2e", "api", "ui", "performance", "accessibility"]:
            if test_type in content.lower():
                types.append(test_type)
        return types

    def _extract_priority_tests(self, content: str) -> List[str]:
        """Extract P0/P1 tests"""
        import re
        pattern = r'(P0|P1)[:\s]+(.*?)(?:\n|$)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return [f"{priority}: {test}" for priority, test in matches][:10]

    def _estimate_test_count(self, content: str) -> int:
        """Estimate number of tests"""
        # Count test case mentions
        import re
        test_mentions = len(re.findall(r'test case|test\s+\d+', content, re.IGNORECASE))
        return max(test_mentions, 5)  # At least 5 tests

    def _check_all_criteria_met(self, content: str) -> bool:
        """Check if all criteria met"""
        content_lower = content.lower()
        return "all criteria met: yes" in content_lower or "all met" in content_lower

    def _extract_criteria_status(self, content: str) -> Dict[str, bool]:
        """Extract status for each criterion"""
        # Simple extraction - look for "Met: Yes/No"
        import re
        pattern = r'criterion\s+(\d+).*?met:\s*(yes|no)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        return {f"criterion_{num}": status.lower() == "yes" for num, status in matches}

    def _extract_sign_off(self, content: str) -> str:
        """Extract sign-off decision"""
        content_upper = content.upper()
        if "APPROVED" in content_upper and "NOT" not in content_upper:
            return "approved"
        elif "NEEDS_FIXES" in content_upper or "NEEDS FIXES" in content_upper:
            return "needs_fixes"
        elif "BLOCKED" in content_upper:
            return "blocked"
        return "unknown"

    def _extract_blockers(self, content: str) -> List[str]:
        """Extract blockers from content"""
        blockers = []
        lines = content.split('\n')
        in_blockers = False
        for line in lines:
            if 'blocker' in line.lower() and ':' in line:
                in_blockers = True
                continue
            if in_blockers and line.strip().startswith('-'):
                blockers.append(line.strip()[1:].strip())
            elif in_blockers and not line.strip().startswith('-'):
                in_blockers = False
        return blockers[:10]
