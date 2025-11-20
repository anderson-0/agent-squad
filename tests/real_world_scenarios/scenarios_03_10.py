"""
Scenarios 3-10: Real-World Test Implementations

All remaining scenarios in one file for efficiency.
Each scenario tests specific agent capabilities and identifies tool gaps.
"""

import asyncio
from typing import List
from .base_scenario import BaseScenario


# ============================================================================
# Scenario 3: Third-Party API Integration
# ============================================================================

class ThirdPartyAPIScenario(BaseScenario):
    """Scenario 3: Integrate Stripe payment processing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Third-Party API Integration (Stripe)"
        self.expected_duration_minutes = 60

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Payment Integration Squad",
            ["project_manager", "backend_developer", "frontend_developer", "devops_engineer", "qa_tester"]
        )
        self.add_success_criterion("Stripe SDK integrated")
        self.add_success_criterion("Payment flow works")
        self.add_success_criterion("Webhooks configured")
        self.add_success_criterion("Error handling added")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Integrate Stripe payment processing",
            "Implement complete Stripe integration with payment intents, webhooks, and error handling"
        )

        steps = [
            ("PM researches Stripe API", "project_manager", ["web_search", "read_docs", "api_explorer"]),
            ("Backend installs Stripe SDK", "backend_developer", ["pip_install", "package_manager"]),
            ("Backend implements payment service", "backend_developer", ["write_file", "api_client", "env_vars"]),
            ("Backend implements webhooks", "backend_developer", ["write_file", "webhook_validator"]),
            ("Frontend integrates Stripe.js", "frontend_developer", ["npm_install", "write_file", "api_client"]),
            ("DevOps configures environment", "devops_engineer", ["env_config", "secret_manager"]),
            ("QA tests payment flow", "qa_tester", ["api_test", "webhook_test", "mock_stripe"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["pip_install", "npm_install", "package_manager", "webhook_test", "mock_stripe", "secret_manager"]:
                    self.mark_tool_missing(tool)
                else:
                    self.track_tool_usage(tool, success=True, execution_time=1.0)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=120)
            self.mark_criterion_met("Payment flow works")
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 5 and self.metrics.success_criteria_met >= 2

    def get_expected_tools(self) -> List[str]:
        return [
            "pip_install", "npm_install", "package_manager",
            "write_file", "edit_file", "read_file",
            "api_client", "http_request", "webhook_test",
            "env_config", "secret_manager", "env_vars",
            "api_test", "mock_stripe", "web_search", "read_docs"
        ]


# ============================================================================
# Scenario 4: Database Schema Migration
# ============================================================================

class DatabaseMigrationScenario(BaseScenario):
    """Scenario 4: Add user preferences table with data migration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Database Schema Migration"
        self.expected_duration_minutes = 40

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Database Migration Squad",
            ["backend_developer", "devops_engineer", "qa_tester"]
        )
        self.add_success_criterion("Migration created")
        self.add_success_criterion("Data migrated")
        self.add_success_criterion("Rollback works")
        self.add_success_criterion("Tests pass")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Add user_preferences table",
            "Create migration to add user preferences table and migrate existing data"
        )

        steps = [
            ("Plan migration strategy", "backend_developer", ["database_inspect", "query_analyzer"]),
            ("Create Alembic migration", "backend_developer", ["alembic_revision", "write_file"]),
            ("Implement upgrade()", "backend_developer", ["write_file", "sql_query"]),
            ("Implement downgrade()", "backend_developer", ["write_file", "sql_query"]),
            ("Test migration on dev DB", "backend_developer", ["alembic_upgrade", "database_query"]),
            ("Update models", "backend_developer", ["edit_file", "sqlalchemy_model"]),
            ("Add tests", "backend_developer", ["write_file", "run_tests"]),
            ("QA validates data", "qa_tester", ["database_query", "data_validator"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["database_inspect", "query_analyzer", "alembic_revision", "alembic_upgrade", "sqlalchemy_model", "data_validator"]:
                    self.mark_tool_missing(tool)
                elif tool in ["write_file", "edit_file"]:
                    self.track_tool_usage(tool, success=True, execution_time=1.0)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=90)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 6 and self.metrics.success_criteria_met >= 2

    def get_expected_tools(self) -> List[str]:
        return [
            "database_inspect", "database_query", "sql_query",
            "query_analyzer", "query_explain",
            "alembic_revision", "alembic_upgrade", "alembic_downgrade",
            "sqlalchemy_model", "write_file", "edit_file",
            "run_tests", "data_validator", "backup_restore"
        ]


# ============================================================================
# Scenario 5: Performance Optimization
# ============================================================================

class PerformanceOptimizationScenario(BaseScenario):
    """Scenario 5: Optimize slow dashboard (5s → <1s)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Performance Optimization"
        self.expected_duration_minutes = 90

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Performance Squad",
            ["backend_developer", "frontend_developer", "qa_tester"]
        )
        self.add_success_criterion("Bottleneck identified")
        self.add_success_criterion("Backend optimized")
        self.add_success_criterion("Frontend optimized")
        self.add_success_criterion("Target met (<1s)")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Optimize slow dashboard page",
            "Dashboard loads in 5s, need to optimize to <1s. Profile, identify bottlenecks, optimize."
        )

        steps = [
            ("Profile endpoint", "backend_developer", ["profiler", "query_profiler", "benchmark"]),
            ("Identify N+1 query", "backend_developer", ["query_analyzer", "database_inspect"]),
            ("Fix N+1 with selectinload", "backend_developer", ["edit_file", "sqlalchemy_optimize"]),
            ("Add database index", "backend_developer", ["database_index", "alembic_revision"]),
            ("Add Redis caching", "backend_developer", ["edit_file", "redis_client"]),
            ("Frontend bundle analysis", "frontend_developer", ["bundle_analyzer", "webpack_analyzer"]),
            ("Add code splitting", "frontend_developer", ["edit_file", "lazy_loading"]),
            ("Optimize images", "frontend_developer", ["image_optimizer", "webp_converter"]),
            ("Benchmark improvements", "qa_tester", ["benchmark", "load_test", "lighthouse"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["edit_file"]:
                    self.track_tool_usage(tool, success=True, execution_time=1.5)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=180)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 7 and self.metrics.success_criteria_met >= 2

    def get_expected_tools(self) -> List[str]:
        return [
            "profiler", "query_profiler", "benchmark", "load_test",
            "query_analyzer", "database_inspect", "database_index",
            "sqlalchemy_optimize", "edit_file", "redis_client",
            "bundle_analyzer", "webpack_analyzer", "lazy_loading",
            "image_optimizer", "webp_converter", "lighthouse",
            "monitoring_dashboard", "metrics_collector"
        ]


# ============================================================================
# Scenario 6: Security Vulnerability Remediation
# ============================================================================

class SecurityVulnerabilityScenario(BaseScenario):
    """Scenario 6: Fix SQL injection vulnerability"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Security Vulnerability Remediation"
        self.expected_duration_minutes = 60

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Security Squad",
            ["backend_developer", "solution_architect", "qa_tester"]
        )
        self.add_success_criterion("Vulnerability identified")
        self.add_success_criterion("Fix implemented")
        self.add_success_criterion("Similar patterns fixed")
        self.add_success_criterion("Security tests added")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Fix SQL injection in search endpoint",
            "Security scan reports SQL injection vulnerability in search endpoint. Fix and prevent recurrence.",
            priority="critical"
        )

        steps = [
            ("Analyze vulnerable code", "backend_developer", ["read_file", "code_search", "security_scanner"]),
            ("Find similar patterns", "backend_developer", ["code_search", "grep_pattern", "ast_analyzer"]),
            ("Implement fix (parameterized queries)", "backend_developer", ["edit_file", "sqlalchemy_query"]),
            ("Add input validation", "backend_developer", ["edit_file", "input_validator"]),
            ("Add security tests", "backend_developer", ["write_file", "security_test", "penetration_test"]),
            ("Architect reviews", "solution_architect", ["code_review", "security_review"]),
            ("Run security scan", "qa_tester", ["bandit", "safety", "security_scanner"]),
            ("Validate fix", "qa_tester", ["penetration_test", "sql_injection_test"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["read_file", "code_search", "edit_file", "write_file"]:
                    self.track_tool_usage(tool, success=True, execution_time=1.0)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=120)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 6 and self.metrics.success_criteria_met >= 3

    def get_expected_tools(self) -> List[str]:
        return [
            "security_scanner", "bandit", "safety", "sast",
            "code_search", "grep_pattern", "ast_analyzer",
            "read_file", "edit_file", "write_file",
            "input_validator", "sqlalchemy_query",
            "security_test", "penetration_test", "sql_injection_test",
            "code_review", "security_review", "vulnerability_scanner"
        ]


# ============================================================================
# Scenario 7: Legacy Code Refactoring
# ============================================================================

class LegacyRefactoringScenario(BaseScenario):
    """Scenario 7: Refactor 500-line God class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Legacy Code Refactoring"
        self.expected_duration_minutes = 120

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Refactoring Squad",
            ["tech_lead", "backend_developer", "qa_tester"]
        )
        self.add_success_criterion("Code analyzed")
        self.add_success_criterion("Services split")
        self.add_success_criterion("Tests pass")
        self.add_success_criterion("Coverage improved")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Refactor UserService God class",
            "Split 500-line UserService into AuthService, ProfileService, NotificationService"
        )

        steps = [
            ("Analyze UserService", "tech_lead", ["read_file", "code_metrics", "complexity_analyzer"]),
            ("Map dependencies", "tech_lead", ["dependency_graph", "call_graph"]),
            ("Plan refactoring", "tech_lead", ["refactoring_tool", "impact_analyzer"]),
            ("Create AuthService", "backend_developer", ["write_file", "extract_methods"]),
            ("Create ProfileService", "backend_developer", ["write_file", "extract_methods"]),
            ("Create NotificationService", "backend_developer", ["write_file", "extract_methods"]),
            ("Update UserService", "backend_developer", ["edit_file", "delegate_methods"]),
            ("Update all callers", "backend_developer", ["code_search", "edit_file", "refactor_imports"]),
            ("Add unit tests", "backend_developer", ["write_file", "run_tests"]),
            ("Check coverage", "backend_developer", ["code_coverage", "coverage_report"]),
            ("Run regression tests", "qa_tester", ["run_tests", "integration_test"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["read_file", "write_file", "edit_file", "code_search"]:
                    self.track_tool_usage(tool, success=True, execution_time=2.0)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=240)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 8 and self.metrics.success_criteria_met >= 3

    def get_expected_tools(self) -> List[str]:
        return [
            "code_metrics", "complexity_analyzer", "coupling_analyzer",
            "dependency_graph", "call_graph", "refactoring_tool",
            "impact_analyzer", "extract_methods", "delegate_methods",
            "read_file", "write_file", "edit_file", "code_search",
            "refactor_imports", "run_tests", "code_coverage",
            "coverage_report", "integration_test"
        ]


# ============================================================================
# Scenario 8: CI/CD Pipeline Setup
# ============================================================================

class CICDPipelineScenario(BaseScenario):
    """Scenario 8: Set up GitHub Actions pipeline"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "CI/CD Pipeline Setup"
        self.expected_duration_minutes = 90

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "DevOps Squad",
            ["devops_engineer", "backend_developer", "qa_tester"]
        )
        self.add_success_criterion("Pipeline created")
        self.add_success_criterion("Tests run in CI")
        self.add_success_criterion("Deploy to staging")
        self.add_success_criterion("Secrets configured")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Set up GitHub Actions CI/CD",
            "Create pipeline for lint, test, build, deploy (staging on PR, prod on merge)"
        )

        steps = [
            ("Plan pipeline", "devops_engineer", ["yaml_editor", "github_actions_docs"]),
            ("Create workflow file", "devops_engineer", ["write_file", "yaml_validator"]),
            ("Add lint step", "devops_engineer", ["yaml_editor", "linter_config"]),
            ("Add test step", "devops_engineer", ["yaml_editor", "test_runner"]),
            ("Add build step", "devops_engineer", ["yaml_editor", "docker_build"]),
            ("Add deploy step", "devops_engineer", ["yaml_editor", "deployment_tool"]),
            ("Configure secrets", "devops_engineer", ["secret_manager", "github_secrets"]),
            ("Add env protection", "devops_engineer", ["github_api", "approval_workflow"]),
            ("Backend adds tests", "backend_developer", ["write_file", "run_tests"]),
            ("QA validates pipeline", "qa_tester", ["git_push", "pr_create", "ci_monitor"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["write_file", "yaml_editor"]:
                    self.track_tool_usage(tool, success=True, execution_time=1.5)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=180)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 7 and self.metrics.success_criteria_met >= 3

    def get_expected_tools(self) -> List[str]:
        return [
            "yaml_editor", "yaml_validator", "github_actions_docs",
            "linter_config", "test_runner", "docker_build",
            "deployment_tool", "secret_manager", "github_secrets",
            "github_api", "approval_workflow", "write_file",
            "run_tests", "git_push", "pr_create", "ci_monitor"
        ]


# ============================================================================
# Scenario 9: Documentation Generation
# ============================================================================

class DocumentationGenerationScenario(BaseScenario):
    """Scenario 9: Generate complete API documentation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Documentation Generation"
        self.expected_duration_minutes = 150

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Documentation Squad",
            ["project_manager", "backend_developer", "frontend_developer", "qa_tester"]
        )
        self.add_success_criterion("OpenAPI generated")
        self.add_success_criterion("Guides written")
        self.add_success_criterion("Examples added")
        self.add_success_criterion("Hosted documentation")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Generate complete API documentation",
            "Generate OpenAPI schema, write guides, add examples, host documentation"
        )

        steps = [
            ("Generate OpenAPI", "backend_developer", ["openapi_generator", "schema_extractor"]),
            ("Add docstrings", "backend_developer", ["edit_file", "docstring_generator"]),
            ("Add examples", "backend_developer", ["edit_file", "example_generator"]),
            ("Write auth guide", "backend_developer", ["write_file", "markdown_editor"]),
            ("Write workflow guide", "backend_developer", ["write_file", "markdown_editor"]),
            ("Write error guide", "backend_developer", ["write_file", "markdown_editor"]),
            ("Add JS examples", "frontend_developer", ["write_file", "code_example_generator"]),
            ("Add React examples", "frontend_developer", ["write_file", "component_example"]),
            ("Generate diagrams", "project_manager", ["diagram_generator", "mermaid", "plantuml"]),
            ("Set up MkDocs", "backend_developer", ["mkdocs_install", "mkdocs_config"]),
            ("Deploy docs", "backend_developer", ["docs_hosting", "netlify_deploy"]),
            ("QA reviews docs", "qa_tester", ["link_checker", "docs_validator"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["write_file", "edit_file", "markdown_editor"]:
                    self.track_tool_usage(tool, success=True, execution_time=3.0)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=300)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 9 and self.metrics.success_criteria_met >= 3

    def get_expected_tools(self) -> List[str]:
        return [
            "openapi_generator", "schema_extractor", "docstring_generator",
            "example_generator", "code_example_generator", "component_example",
            "write_file", "edit_file", "markdown_editor",
            "diagram_generator", "mermaid", "plantuml",
            "mkdocs_install", "mkdocs_config", "docs_hosting",
            "netlify_deploy", "link_checker", "docs_validator"
        ]


# ============================================================================
# Scenario 10: Multi-Service Feature
# ============================================================================

class MultiServiceFeatureScenario(BaseScenario):
    """Scenario 10: Implement notification system across microservices"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario_description = "Multi-Service Feature Implementation"
        self.expected_duration_minutes = 240

    async def setup_scenario(self):
        self.squad_id = await self.create_squad_with_agents(
            "Microservices Squad",
            ["solution_architect", "backend_developer", "frontend_developer", "devops_engineer", "qa_tester"]
        )
        self.add_success_criterion("System designed")
        self.add_success_criterion("Services implemented")
        self.add_success_criterion("NATS configured")
        self.add_success_criterion("End-to-end works")

    async def run_scenario(self):
        self.task_id = await self.create_task(
            self.squad_id,
            "Implement notification system",
            "Build notification system with notification service, email service, queue (NATS)"
        )

        steps = [
            ("Design system", "solution_architect", ["architecture_diagram", "sequence_diagram"]),
            ("Create notification service", "backend_developer", ["write_file", "fastapi_app", "nats_subscribe"]),
            ("Create email service", "backend_developer", ["write_file", "fastapi_app", "sendgrid_client"]),
            ("Update main API", "backend_developer", ["edit_file", "nats_publish", "event_emitter"]),
            ("Configure NATS topics", "devops_engineer", ["nats_config", "jetstream_config"]),
            ("Update docker-compose", "devops_engineer", ["edit_file", "docker_compose"]),
            ("Add to docker-compose", "devops_engineer", ["edit_file", "service_config"]),
            ("Build notification UI", "frontend_developer", ["write_file", "react_component"]),
            ("Add preferences UI", "frontend_developer", ["write_file", "react_form"]),
            ("Test notifications", "qa_tester", ["api_test", "nats_inspector", "email_test"]),
            ("Test end-to-end", "qa_tester", ["integration_test", "distributed_trace"])
        ]

        for desc, role, tools in steps:
            step = self.add_step(desc, agent_role=role, expected_tools=tools)
            for tool in tools:
                if tool in ["write_file", "edit_file"]:
                    self.track_tool_usage(tool, success=True, execution_time=4.0)
                else:
                    self.mark_tool_missing(tool)
            self.complete_step(step, success=True)

        try:
            self.execution_id = await self.execute_task(self.task_id, self.squad_id)
            await self.wait_for_execution(self.execution_id, timeout_seconds=480)
        except Exception as e:
            self.metrics.errors.append(str(e))

    async def validate_results(self) -> bool:
        return self.metrics.steps_completed >= 9 and self.metrics.success_criteria_met >= 3

    def get_expected_tools(self) -> List[str]:
        return [
            "architecture_diagram", "sequence_diagram", "write_file", "edit_file",
            "fastapi_app", "nats_subscribe", "nats_publish", "nats_config",
            "jetstream_config", "event_emitter", "sendgrid_client",
            "docker_compose", "service_config", "react_component", "react_form",
            "api_test", "nats_inspector", "email_test", "integration_test",
            "distributed_trace", "service_orchestration", "api_gateway"
        ]
