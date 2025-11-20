"""
Base Scenario Framework for Real-World Testing

Provides base classes and utilities for implementing and running real-world scenarios.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from uuid import UUID, uuid4

import httpx


class ToolStatus(str, Enum):
    """Status of a tool during scenario execution"""
    AVAILABLE = "available"      # Tool exists and was used
    MISSING = "missing"          # Tool needed but not available
    UNUSED = "unused"            # Tool available but not used
    FAILED = "failed"            # Tool used but failed


class ScenarioStatus(str, Enum):
    """Status of scenario execution"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PARTIAL = "partial"          # Partially completed


@dataclass
class ToolUsage:
    """Track usage of a specific tool"""
    tool_name: str
    status: ToolStatus
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_time_seconds: float = 0.0
    first_used_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    error_messages: List[str] = field(default_factory=list)


@dataclass
class ScenarioMetrics:
    """Metrics collected during scenario execution"""
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Status
    status: ScenarioStatus = ScenarioStatus.NOT_STARTED
    completion_percentage: float = 0.0

    # Quality
    steps_completed: int = 0
    steps_total: int = 0
    success_criteria_met: int = 0
    success_criteria_total: int = 0
    quality_score: float = 0.0  # 0-100

    # Errors
    error_count: int = 0
    errors: List[str] = field(default_factory=list)

    # Tool Usage
    tools_used: Dict[str, ToolUsage] = field(default_factory=dict)
    tools_needed: Set[str] = field(default_factory=set)
    tools_missing: Set[str] = field(default_factory=set)

    # Agent Activity
    agents_involved: List[str] = field(default_factory=list)
    messages_sent: int = 0
    tasks_created: int = 0

    # Results
    output_artifacts: Dict[str, Any] = field(default_factory=dict)

    def calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        if self.success_criteria_total == 0:
            return 0.0

        # Success criteria weight: 60%
        criteria_score = (self.success_criteria_met / self.success_criteria_total) * 60

        # Completion weight: 30%
        completion_score = self.completion_percentage * 30

        # Error penalty: 10%
        error_score = max(0, 10 - (self.error_count * 2))

        return criteria_score + completion_score + error_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting"""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "completion_percentage": self.completion_percentage,
            "steps": {
                "completed": self.steps_completed,
                "total": self.steps_total,
                "percentage": (self.steps_completed / self.steps_total * 100) if self.steps_total > 0 else 0
            },
            "success_criteria": {
                "met": self.success_criteria_met,
                "total": self.success_criteria_total,
                "percentage": (self.success_criteria_met / self.success_criteria_total * 100) if self.success_criteria_total > 0 else 0
            },
            "quality_score": self.quality_score,
            "errors": {
                "count": self.error_count,
                "messages": self.errors
            },
            "tools": {
                "used": len(self.tools_used),
                "needed": len(self.tools_needed),
                "missing": len(self.tools_missing),
                "available_percentage": ((len(self.tools_needed) - len(self.tools_missing)) / len(self.tools_needed) * 100) if len(self.tools_needed) > 0 else 100
            },
            "agents": {
                "involved": self.agents_involved,
                "count": len(self.agents_involved)
            },
            "activity": {
                "messages_sent": self.messages_sent,
                "tasks_created": self.tasks_created
            }
        }


@dataclass
class ScenarioStep:
    """A single step in a scenario workflow"""
    step_number: int
    description: str
    agent_role: Optional[str] = None
    expected_tools: List[str] = field(default_factory=list)
    completed: bool = False
    success: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class BaseScenario(ABC):
    """
    Base class for all real-world scenarios.

    Provides common functionality for:
    - Setup and teardown
    - Metrics tracking
    - Tool usage monitoring
    - Step execution
    - Results validation
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000/api/v1",
        timeout: int = 300  # 5 minutes default
    ):
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

        # Test data
        self.org_id: Optional[UUID] = None
        self.user_id: Optional[UUID] = None
        self.squad_id: Optional[UUID] = None
        self.task_id: Optional[UUID] = None
        self.execution_id: Optional[UUID] = None

        # Metrics
        self.metrics = ScenarioMetrics(started_at=datetime.utcnow())
        self.steps: List[ScenarioStep] = []

        # Configuration
        self.scenario_name = self.__class__.__name__
        self.scenario_description = ""
        self.expected_duration_minutes = 0

    # ========================================================================
    # Abstract Methods (Must be implemented by scenarios)
    # ========================================================================

    @abstractmethod
    async def setup_scenario(self):
        """
        Set up scenario-specific resources.

        This is called before run_scenario() and should:
        - Create test data
        - Configure environment
        - Set up dependencies
        """
        pass

    @abstractmethod
    async def run_scenario(self):
        """
        Execute the scenario workflow.

        This is the main scenario logic. Should:
        - Execute workflow steps
        - Track tool usage
        - Update metrics
        - Validate results
        """
        pass

    @abstractmethod
    async def validate_results(self) -> bool:
        """
        Validate scenario completed successfully.

        Returns:
            True if scenario met success criteria
        """
        pass

    @abstractmethod
    def get_expected_tools(self) -> List[str]:
        """
        Return list of tools expected to be needed.

        This helps identify tool gaps when tools are missing.
        """
        pass

    # ========================================================================
    # Lifecycle Methods
    # ========================================================================

    async def setup(self):
        """Set up HTTP client and common resources"""
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # Create organization
        org_response = await self.client.post(
            f"{self.api_base_url}/organizations",
            json={
                "name": f"Test Org {uuid4().hex[:8]}",
                "slug": f"test-org-{uuid4().hex[:8]}"
            }
        )
        org_response.raise_for_status()
        self.org_id = UUID(org_response.json()["id"])

        # Create user
        user_response = await self.client.post(
            f"{self.api_base_url}/users",
            json={
                "email": f"test-{uuid4().hex[:8]}@example.com",
                "name": "Test User",
                "organization_id": str(self.org_id)
            }
        )
        user_response.raise_for_status()
        self.user_id = UUID(user_response.json()["id"])

        # Call scenario-specific setup
        await self.setup_scenario()

    async def teardown(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()

    async def execute(self) -> ScenarioMetrics:
        """
        Execute complete scenario lifecycle.

        Returns:
            ScenarioMetrics with results
        """
        self.metrics.status = ScenarioStatus.RUNNING
        self.metrics.started_at = datetime.utcnow()

        try:
            # Setup
            await self.setup()

            # Initialize expected tools
            self.metrics.tools_needed = set(self.get_expected_tools())

            # Run scenario
            start_time = time.time()
            await self.run_scenario()
            self.metrics.duration_seconds = time.time() - start_time

            # Validate results
            success = await self.validate_results()

            # Update status
            if success:
                self.metrics.status = ScenarioStatus.COMPLETED
            elif self.metrics.steps_completed > 0:
                self.metrics.status = ScenarioStatus.PARTIAL
            else:
                self.metrics.status = ScenarioStatus.FAILED

            # Calculate completion percentage
            if self.metrics.steps_total > 0:
                self.metrics.completion_percentage = (
                    self.metrics.steps_completed / self.metrics.steps_total
                )

            # Calculate quality score
            self.metrics.quality_score = self.metrics.calculate_quality_score()

            # Identify missing tools
            self.identify_missing_tools()

        except asyncio.TimeoutError:
            self.metrics.status = ScenarioStatus.TIMEOUT
            self.metrics.errors.append(f"Scenario timed out after {self.timeout}s")
            self.metrics.error_count += 1

        except Exception as e:
            self.metrics.status = ScenarioStatus.FAILED
            self.metrics.errors.append(str(e))
            self.metrics.error_count += 1

        finally:
            self.metrics.completed_at = datetime.utcnow()
            await self.teardown()

        return self.metrics

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def add_step(
        self,
        description: str,
        agent_role: Optional[str] = None,
        expected_tools: Optional[List[str]] = None
    ) -> ScenarioStep:
        """Add a step to the scenario"""
        step = ScenarioStep(
            step_number=len(self.steps) + 1,
            description=description,
            agent_role=agent_role,
            expected_tools=expected_tools or []
        )
        self.steps.append(step)
        self.metrics.steps_total += 1
        return step

    def complete_step(
        self,
        step: ScenarioStep,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Mark a step as completed"""
        step.completed = True
        step.success = success
        step.completed_at = datetime.utcnow()

        if step.started_at:
            step.duration_seconds = (
                step.completed_at - step.started_at
            ).total_seconds()

        if success:
            self.metrics.steps_completed += 1
        else:
            step.error_message = error_message
            if error_message:
                self.metrics.errors.append(
                    f"Step {step.step_number} failed: {error_message}"
                )
                self.metrics.error_count += 1

    def track_tool_usage(
        self,
        tool_name: str,
        success: bool = True,
        execution_time: float = 0.0,
        error_message: Optional[str] = None
    ):
        """Track usage of a tool"""
        if tool_name not in self.metrics.tools_used:
            self.metrics.tools_used[tool_name] = ToolUsage(
                tool_name=tool_name,
                status=ToolStatus.AVAILABLE,
                first_used_at=datetime.utcnow()
            )

        tool = self.metrics.tools_used[tool_name]
        tool.usage_count += 1
        tool.last_used_at = datetime.utcnow()
        tool.total_time_seconds += execution_time

        if success:
            tool.success_count += 1
        else:
            tool.failure_count += 1
            tool.status = ToolStatus.FAILED
            if error_message:
                tool.error_messages.append(error_message)

    def mark_tool_missing(self, tool_name: str):
        """Mark a tool as needed but missing"""
        self.metrics.tools_missing.add(tool_name)
        if tool_name not in self.metrics.tools_used:
            self.metrics.tools_used[tool_name] = ToolUsage(
                tool_name=tool_name,
                status=ToolStatus.MISSING
            )

    def identify_missing_tools(self):
        """Identify which expected tools were not used"""
        for tool_name in self.metrics.tools_needed:
            if tool_name not in self.metrics.tools_used:
                self.metrics.tools_missing.add(tool_name)

    def add_success_criterion(self, description: str):
        """Add a success criterion to be checked"""
        self.metrics.success_criteria_total += 1

    def mark_criterion_met(self, description: str):
        """Mark a success criterion as met"""
        self.metrics.success_criteria_met += 1

    async def create_squad_with_agents(
        self,
        squad_name: str,
        agent_roles: List[str]
    ) -> UUID:
        """Helper to create squad with agents"""
        # Create squad
        squad_response = await self.client.post(
            f"{self.api_base_url}/squads",
            json={
                "name": squad_name,
                "organization_id": str(self.org_id),
                "description": f"Squad for {self.scenario_name}"
            }
        )
        squad_response.raise_for_status()
        squad_id = UUID(squad_response.json()["id"])

        # Add agents
        for role in agent_roles:
            member_response = await self.client.post(
                f"{self.api_base_url}/squads/{squad_id}/members",
                json={
                    "role": role,
                    "llm_provider": "ollama",
                    "llm_model": "llama3.2",
                    "config": {"temperature": 0.7}
                }
            )
            member_response.raise_for_status()
            self.metrics.agents_involved.append(role)

        return squad_id

    async def create_task(
        self,
        squad_id: UUID,
        title: str,
        description: str,
        priority: str = "medium"
    ) -> UUID:
        """Helper to create a task"""
        task_response = await self.client.post(
            f"{self.api_base_url}/tasks",
            json={
                "title": title,
                "description": description,
                "squad_id": str(squad_id),
                "priority": priority
            }
        )
        task_response.raise_for_status()
        task_id = UUID(task_response.json()["id"])
        self.metrics.tasks_created += 1
        return task_id

    async def execute_task(self, task_id: UUID, squad_id: UUID) -> UUID:
        """Helper to execute a task"""
        exec_response = await self.client.post(
            f"{self.api_base_url}/tasks/{task_id}/execute",
            json={"squad_id": str(squad_id)}
        )
        exec_response.raise_for_status()
        execution_id = UUID(exec_response.json()["id"])
        return execution_id

    async def wait_for_execution(
        self,
        execution_id: UUID,
        timeout_seconds: int = 60,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for execution to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            response = await self.client.get(
                f"{self.api_base_url}/executions/{execution_id}"
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status")
            if status in ["completed", "failed"]:
                return data

            await asyncio.sleep(poll_interval)

        raise asyncio.TimeoutError(
            f"Execution {execution_id} did not complete within {timeout_seconds}s"
        )
