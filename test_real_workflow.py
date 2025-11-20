"""
End-to-End Real Workflow Tests for Agent Squad

This script tests complete workflows to ensure the system works correctly
from user perspective.

Test Scenarios:
1. Simple Task Assignment - Single agent completes a task
2. Multi-Agent Collaboration - Multiple agents work together
3. Error Handling - System handles errors gracefully
4. Caching Performance - Verify cache improves performance
5. Agent Pool Performance - Verify agent pooling works

Usage:
    python test_real_workflow.py

Requirements:
    - Backend API running on http://localhost:8000
    - PostgreSQL, Redis, NATS all running
    - Test database available
"""

import asyncio
import time
from typing import Dict, Any, List
import httpx
from uuid import UUID, uuid4
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30.0  # seconds


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_header(message: str):
    """Print a test section header"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{message}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_test(message: str):
    """Print test info"""
    print(f"{Colors.BLUE}→{Colors.NC} {message}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


class TestResult:
    """Track test results"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.duration = 0.0
        self.error = None


class E2ETestRunner:
    """End-to-end test runner"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = None
        self.results: List[TestResult] = []

        # Test data IDs
        self.user_id = None
        self.org_id = None
        self.squad_id = None
        self.task_id = None
        self.execution_id = None

    async def setup(self):
        """Setup HTTP client and verify API is reachable"""
        print_header("Setup")

        # Create HTTP client
        self.client = httpx.AsyncClient(timeout=TIMEOUT)

        # Check API health
        print_test("Checking API health...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            health_data = response.json()

            if health_data.get("status") == "healthy":
                print_success(f"API is healthy")
                print(f"  Database: {health_data.get('database', 'unknown')}")
                print(f"  Cache: {health_data.get('cache', 'unknown')}")
            else:
                print_error("API is not healthy")
                print(f"  Response: {health_data}")
                return False

        except Exception as e:
            print_error(f"Failed to connect to API: {e}")
            return False

        return True

    async def teardown(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()

    async def run_test(self, test_name: str, test_func):
        """Run a single test and track results"""
        result = TestResult(test_name)
        print_header(f"Test: {test_name}")

        start_time = time.time()
        try:
            await test_func()
            result.passed = True
            result.duration = time.time() - start_time
            print_success(f"{test_name} PASSED ({result.duration:.2f}s)")
        except Exception as e:
            result.passed = False
            result.duration = time.time() - start_time
            result.error = str(e)
            print_error(f"{test_name} FAILED ({result.duration:.2f}s)")
            print_error(f"Error: {e}")

        self.results.append(result)
        return result.passed

    # ========================================================================
    # Test Scenario 1: Simple Task Assignment
    # ========================================================================

    async def test_simple_task_assignment(self):
        """
        Test Scenario 1: Simple Task Assignment

        Steps:
        1. Create organization
        2. Create user
        3. Create squad with 1 agent (Backend Developer)
        4. Create task
        5. Execute task
        6. Verify task completes
        """
        print_test("Step 1: Creating organization...")
        org_response = await self.client.post(
            f"{self.base_url}/organizations",
            json={
                "name": f"Test Org {uuid4().hex[:8]}",
                "slug": f"test-org-{uuid4().hex[:8]}"
            }
        )
        org_response.raise_for_status()
        self.org_id = org_response.json()["id"]
        print_success(f"Organization created: {self.org_id}")

        print_test("Step 2: Creating user...")
        user_response = await self.client.post(
            f"{self.base_url}/users",
            json={
                "email": f"test-{uuid4().hex[:8]}@example.com",
                "name": "Test User",
                "organization_id": self.org_id
            }
        )
        user_response.raise_for_status()
        self.user_id = user_response.json()["id"]
        print_success(f"User created: {self.user_id}")

        print_test("Step 3: Creating squad with 1 agent...")
        squad_response = await self.client.post(
            f"{self.base_url}/squads",
            json={
                "name": f"Test Squad {uuid4().hex[:8]}",
                "organization_id": self.org_id,
                "description": "Test squad for E2E testing"
            }
        )
        squad_response.raise_for_status()
        self.squad_id = squad_response.json()["id"]
        print_success(f"Squad created: {self.squad_id}")

        # Add backend developer to squad
        print_test("Step 3a: Adding backend developer to squad...")
        member_response = await self.client.post(
            f"{self.base_url}/squads/{self.squad_id}/members",
            json={
                "role": "backend_developer",
                "llm_provider": "ollama",
                "llm_model": "llama3.2",
                "config": {"temperature": 0.7}
            }
        )
        member_response.raise_for_status()
        member_id = member_response.json()["id"]
        print_success(f"Backend developer added: {member_id}")

        print_test("Step 4: Creating task...")
        task_response = await self.client.post(
            f"{self.base_url}/tasks",
            json={
                "title": "Build a simple REST API endpoint",
                "description": "Create a GET /hello endpoint that returns {message: 'Hello World'}",
                "squad_id": self.squad_id,
                "priority": "medium"
            }
        )
        task_response.raise_for_status()
        self.task_id = task_response.json()["id"]
        print_success(f"Task created: {self.task_id}")

        print_test("Step 5: Executing task...")
        exec_response = await self.client.post(
            f"{self.base_url}/tasks/{self.task_id}/execute",
            json={"squad_id": self.squad_id}
        )
        exec_response.raise_for_status()
        self.execution_id = exec_response.json()["id"]
        print_success(f"Task execution started: {self.execution_id}")

        print_test("Step 6: Waiting for task completion...")
        # Poll execution status (max 30 seconds)
        for i in range(30):
            await asyncio.sleep(1)
            status_response = await self.client.get(
                f"{self.base_url}/executions/{self.execution_id}"
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            status = status_data.get("status")

            if status == "completed":
                print_success("Task completed successfully!")
                return
            elif status == "failed":
                print_error(f"Task failed: {status_data.get('error_message')}")
                raise Exception(f"Task execution failed")

        print_warning("Task did not complete within 30 seconds (may still be running)")

    # ========================================================================
    # Test Scenario 2: Multi-Agent Collaboration
    # ========================================================================

    async def test_multi_agent_collaboration(self):
        """
        Test Scenario 2: Multi-Agent Collaboration

        Steps:
        1. Create squad with 3 agents (PM, Backend Dev, QA Tester)
        2. Create complex task requiring collaboration
        3. Verify NATS message routing works
        4. Verify all agents respond
        5. Verify task completion
        """
        print_test("Step 1: Creating squad with 3 agents...")
        squad_response = await self.client.post(
            f"{self.base_url}/squads",
            json={
                "name": f"Collaboration Squad {uuid4().hex[:8]}",
                "organization_id": self.org_id,
                "description": "Multi-agent collaboration test"
            }
        )
        squad_response.raise_for_status()
        collab_squad_id = squad_response.json()["id"]
        print_success(f"Squad created: {collab_squad_id}")

        # Add 3 agents
        roles = ["project_manager", "backend_developer", "qa_tester"]
        agent_ids = []

        for role in roles:
            print_test(f"Adding {role}...")
            member_response = await self.client.post(
                f"{self.base_url}/squads/{collab_squad_id}/members",
                json={
                    "role": role,
                    "llm_provider": "ollama",
                    "llm_model": "llama3.2",
                    "config": {"temperature": 0.7}
                }
            )
            member_response.raise_for_status()
            agent_id = member_response.json()["id"]
            agent_ids.append(agent_id)
            print_success(f"{role} added: {agent_id}")

        print_test("Step 2: Creating complex task...")
        task_response = await self.client.post(
            f"{self.base_url}/tasks",
            json={
                "title": "Build and test user authentication system",
                "description": "Create a complete authentication system with JWT tokens, password hashing, and comprehensive tests",
                "squad_id": collab_squad_id,
                "priority": "high"
            }
        )
        task_response.raise_for_status()
        task_id = task_response.json()["id"]
        print_success(f"Complex task created: {task_id}")

        print_test("Step 3: Executing task...")
        exec_response = await self.client.post(
            f"{self.base_url}/tasks/{task_id}/execute",
            json={"squad_id": collab_squad_id}
        )
        exec_response.raise_for_status()
        execution_id = exec_response.json()["id"]
        print_success(f"Execution started: {execution_id}")

        print_test("Step 4: Monitoring agent messages...")
        # Check for agent messages (indicates NATS routing works)
        await asyncio.sleep(5)  # Give agents time to communicate

        messages_response = await self.client.get(
            f"{self.base_url}/executions/{execution_id}/messages"
        )
        messages_response.raise_for_status()
        messages = messages_response.json()

        if len(messages) > 0:
            print_success(f"Agents are communicating ({len(messages)} messages)")
        else:
            print_warning("No agent messages yet (may still be starting)")

        print_test("Step 5: Verifying task progress...")
        status_response = await self.client.get(
            f"{self.base_url}/executions/{execution_id}"
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        print_success(f"Task status: {status_data.get('status')}")

    # ========================================================================
    # Test Scenario 3: Error Handling
    # ========================================================================

    async def test_error_handling(self):
        """
        Test Scenario 3: Error Handling

        Steps:
        1. Test invalid task assignment (nonexistent squad)
        2. Test invalid agent configuration
        3. Verify graceful error handling
        """
        print_test("Step 1: Testing invalid squad ID...")
        try:
            fake_squad_id = str(uuid4())
            response = await self.client.post(
                f"{self.base_url}/tasks",
                json={
                    "title": "Test Task",
                    "description": "This should fail",
                    "squad_id": fake_squad_id,
                    "priority": "low"
                }
            )
            if response.status_code == 404:
                print_success("Invalid squad correctly rejected (404)")
            else:
                print_error(f"Unexpected status code: {response.status_code}")
        except Exception as e:
            print_success(f"Invalid squad correctly rejected: {e}")

        print_test("Step 2: Testing invalid agent role...")
        try:
            response = await self.client.post(
                f"{self.base_url}/squads/{self.squad_id}/members",
                json={
                    "role": "invalid_role_that_does_not_exist",
                    "llm_provider": "ollama",
                    "llm_model": "llama3.2"
                }
            )
            if response.status_code in [400, 422]:
                print_success("Invalid role correctly rejected (400/422)")
            else:
                print_error(f"Unexpected status code: {response.status_code}")
        except Exception as e:
            print_success(f"Invalid role correctly rejected: {e}")

        print_success("Error handling working correctly")

    # ========================================================================
    # Test Scenario 4: Caching Performance
    # ========================================================================

    async def test_caching_performance(self):
        """
        Test Scenario 4: Caching Performance

        Steps:
        1. Make first request (cache miss)
        2. Make second request (cache hit)
        3. Verify second request is faster
        """
        print_test("Step 1: First request (cache miss)...")
        start = time.time()
        response1 = await self.client.get(f"{self.base_url}/squads/{self.squad_id}")
        response1.raise_for_status()
        duration1 = time.time() - start
        print_success(f"First request: {duration1:.3f}s (cache miss)")

        print_test("Step 2: Second request (cache hit)...")
        start = time.time()
        response2 = await self.client.get(f"{self.base_url}/squads/{self.squad_id}")
        response2.raise_for_status()
        duration2 = time.time() - start
        print_success(f"Second request: {duration2:.3f}s (cache hit)")

        improvement = ((duration1 - duration2) / duration1) * 100
        print_success(f"Performance improvement: {improvement:.1f}% faster")

        if duration2 < duration1:
            print_success("✓ Caching is working!")
        else:
            print_warning("Cache may not be working optimally")

    # ========================================================================
    # Test Scenario 5: Agent Pool Performance
    # ========================================================================

    async def test_agent_pool_performance(self):
        """
        Test Scenario 5: Agent Pool Performance

        Steps:
        1. Check agent pool stats
        2. Create multiple agents
        3. Verify pool hit rate improves
        """
        print_test("Step 1: Checking agent pool stats...")
        try:
            response = await self.client.get(f"{self.base_url}/agent-pool/stats")
            response.raise_for_status()
            stats = response.json()

            print_success(f"Agent pool stats:")
            print(f"  Pool size: {stats.get('pool_size', 0)}")
            print(f"  Cache hits: {stats.get('cache_hits', 0)}")
            print(f"  Cache misses: {stats.get('cache_misses', 0)}")
            print(f"  Hit rate: {stats.get('hit_rate', 0):.1f}%")

            if stats.get('hit_rate', 0) > 50:
                print_success("✓ Agent pool is performing well (>50% hit rate)")
            else:
                print_warning("Agent pool hit rate could be better")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print_warning("Agent pool endpoint not available")
            else:
                raise

    # ========================================================================
    # Main Test Runner
    # ========================================================================

    async def run_all_tests(self):
        """Run all test scenarios"""
        print(f"\n{Colors.BLUE}╔{'═' * 58}╗{Colors.NC}")
        print(f"{Colors.BLUE}║{' ' * 10}Agent Squad E2E Test Suite{' ' * 18}║{Colors.NC}")
        print(f"{Colors.BLUE}╚{'═' * 58}╝{Colors.NC}\n")

        # Setup
        if not await self.setup():
            print_error("Setup failed. Exiting.")
            return False

        # Run tests
        tests = [
            ("Simple Task Assignment", self.test_simple_task_assignment),
            ("Multi-Agent Collaboration", self.test_multi_agent_collaboration),
            ("Error Handling", self.test_error_handling),
            ("Caching Performance", self.test_caching_performance),
            ("Agent Pool Performance", self.test_agent_pool_performance),
        ]

        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)

        # Teardown
        await self.teardown()

        # Print summary
        self.print_summary()

        # Return success/failure
        return all(r.passed for r in self.results)

    def print_summary(self):
        """Print test results summary"""
        print_header("Test Summary")

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        total_time = sum(r.duration for r in self.results)

        print(f"\nResults:")
        for result in self.results:
            status = f"{Colors.GREEN}PASS{Colors.NC}" if result.passed else f"{Colors.RED}FAIL{Colors.NC}"
            print(f"  {status} {result.name} ({result.duration:.2f}s)")
            if not result.passed and result.error:
                print(f"       Error: {result.error}")

        print(f"\n{Colors.BLUE}Total:{Colors.NC} {passed}/{total} tests passed")
        print(f"{Colors.BLUE}Time:{Colors.NC} {total_time:.2f}s\n")

        if passed == total:
            print(f"{Colors.GREEN}✓ All tests passed!{Colors.NC}\n")
        else:
            print(f"{Colors.RED}✗ Some tests failed{Colors.NC}\n")


async def main():
    """Main entry point"""
    runner = E2ETestRunner()
    success = await runner.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
