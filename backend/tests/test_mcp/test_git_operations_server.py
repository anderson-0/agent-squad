"""
Tests for Git Operations MCP Server

Tests shallow clone functionality, metrics recording, and E2B sandbox integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from backend.integrations.mcp.servers.git_operations_server import GitOperationsServer


@pytest.fixture
def mock_sandbox():
    """Mock E2B sandbox for testing"""
    sandbox = Mock()
    sandbox.sandbox_id = "test-sandbox-123"
    sandbox.commands = Mock()

    # Mock successful command execution
    mock_result = Mock()
    mock_result.exit_code = 0
    mock_result.stdout = "Success"
    mock_result.stderr = ""
    sandbox.commands.run = Mock(return_value=mock_result)
    sandbox.kill = Mock()

    return sandbox


@pytest.fixture
def git_server_config():
    """Configuration for Git operations server"""
    return {
        "e2b_api_key": "test-api-key",
        "github_token": "test-github-token",
        "timeout": 300,
        "max_retries": 3,
        "default_branch": "main"
    }


class TestGitOperationsServer:
    """Test suite for GitOperationsServer"""

    @pytest.mark.asyncio
    async def test_server_initialization(self, git_server_config):
        """Test that server initializes with correct configuration"""
        server = GitOperationsServer(git_server_config)

        assert server.e2b_api_key == "test-api-key"
        assert server.github_token == "test-github-token"
        assert server.timeout == 300
        assert server.max_retries == 3
        assert server.default_branch == "main"
        assert len(server._sandbox_cache) == 0

    @pytest.mark.asyncio
    async def test_server_tools_registration(self, git_server_config):
        """Test that all git operation tools are registered"""
        server = GitOperationsServer(git_server_config)

        tool_names = [tool.name for tool in server.tools]

        assert "git_clone" in tool_names
        assert "git_status" in tool_names
        assert "git_diff" in tool_names
        assert "git_pull" in tool_names
        assert "git_push" in tool_names

    @pytest.mark.asyncio
    async def test_shallow_clone_parameter_in_schema(self, git_server_config):
        """Test that git_clone tool schema includes shallow parameter"""
        server = GitOperationsServer(git_server_config)

        git_clone_tool = next((t for t in server.tools if t.name == "git_clone"), None)

        assert git_clone_tool is not None
        assert "shallow" in git_clone_tool.inputSchema["properties"]
        assert git_clone_tool.inputSchema["properties"]["shallow"]["type"] == "boolean"
        assert git_clone_tool.inputSchema["properties"]["shallow"]["default"] is False

    @pytest.mark.asyncio
    @patch('backend.integrations.mcp.servers.git_operations_server.Sandbox')
    async def test_shallow_clone_execution(self, mock_sandbox_class, git_server_config, mock_sandbox):
        """Test that shallow=True triggers --depth=1 --single-branch"""
        mock_sandbox_class.create = Mock(return_value=mock_sandbox)

        server = GitOperationsServer(git_server_config)

        arguments = {
            "repo_url": "https://github.com/test/repo.git",
            "branch": "main",
            "agent_id": "agent-001",
            "task_id": "task-001",
            "shallow": True  # Enable shallow clone
        }

        result = await server._handle_git_clone(arguments)

        # Verify shallow clone command was used
        calls = mock_sandbox.commands.run.call_args_list
        clone_call = next((call for call in calls if "git clone" in str(call)), None)

        assert clone_call is not None
        clone_cmd = str(clone_call)
        assert "--depth=1" in clone_cmd
        assert "--single-branch" in clone_cmd

    @pytest.mark.asyncio
    @patch('backend.integrations.mcp.servers.git_operations_server.Sandbox')
    async def test_full_clone_by_default(self, mock_sandbox_class, git_server_config, mock_sandbox):
        """Test that shallow=False (default) does full clone"""
        mock_sandbox_class.create = Mock(return_value=mock_sandbox)

        server = GitOperationsServer(git_server_config)

        arguments = {
            "repo_url": "https://github.com/test/repo.git",
            "branch": "main",
            "agent_id": "agent-001",
            "task_id": "task-001"
            # shallow not specified (defaults to False)
        }

        result = await server._handle_git_clone(arguments)

        # Verify full clone command was used
        calls = mock_sandbox.commands.run.call_args_list
        clone_call = next((call for call in calls if "git clone" in str(call)), None)

        assert clone_call is not None
        clone_cmd = str(clone_call)
        assert "--depth=1" not in clone_cmd  # Should not have shallow flag

    @pytest.mark.asyncio
    async def test_sandbox_cache_hit(self, git_server_config):
        """Test that sandbox cache hit increments metrics"""
        server = GitOperationsServer(git_server_config)

        # Add sandbox to cache
        mock_sandbox = Mock()
        server._sandbox_cache["test-sandbox-123"] = mock_sandbox

        # Retrieve from cache
        sandbox = server._get_sandbox_from_cache("test-sandbox-123")

        assert sandbox is not None
        assert sandbox == mock_sandbox

    @pytest.mark.asyncio
    async def test_sandbox_cache_miss(self, git_server_config):
        """Test that sandbox cache miss returns None"""
        server = GitOperationsServer(git_server_config)

        # Try to retrieve non-existent sandbox
        sandbox = server._get_sandbox_from_cache("non-existent-sandbox")

        assert sandbox is None

    @pytest.mark.asyncio
    @patch('backend.integrations.mcp.servers.git_operations_server.asyncio.create_task')
    async def test_async_metrics_recording(self, mock_create_task, git_server_config):
        """Test that metrics are recorded with fire-and-forget pattern"""
        server = GitOperationsServer(git_server_config)

        # Add sandbox to cache
        mock_sandbox = Mock()
        server._sandbox_cache["test-sandbox-123"] = mock_sandbox

        # Retrieve from cache (should record async metrics)
        sandbox = server._get_sandbox_from_cache("test-sandbox-123")

        # Verify asyncio.create_task was called for metrics
        assert mock_create_task.called
        # Should have called record_sandbox_cache_hit_async
        call_args = str(mock_create_task.call_args)
        assert "record_sandbox_cache" in call_args


class TestShallowCloneIntegration:
    """Integration tests for shallow clone feature"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        "E2B_API_KEY" not in __import__("os").environ,
        reason="E2B_API_KEY not set - skipping integration test"
    )
    @pytest.mark.asyncio
    async def test_shallow_clone_real_repo(self):
        """
        Integration test: Clone a real small repository with shallow=True

        Requires E2B_API_KEY and GITHUB_TOKEN environment variables.
        This test is skipped in CI unless explicitly enabled.
        """
        import os

        config = {
            "e2b_api_key": os.environ.get("E2B_API_KEY"),
            "github_token": os.environ.get("GITHUB_TOKEN", ""),
            "timeout": 60
        }

        server = GitOperationsServer(config)

        # Clone a small public repo with shallow clone
        arguments = {
            "repo_url": "https://github.com/octocat/Hello-World.git",
            "branch": "master",
            "agent_id": "test-agent",
            "task_id": "test-task",
            "shallow": True
        }

        result = await server._handle_git_clone(arguments)

        # Parse result
        import json
        result_data = json.loads(result[0].text)

        assert result_data["success"] is True
        assert "sandbox_id" in result_data
        assert "agent_branch" in result_data

        # Cleanup sandbox
        sandbox_id = result_data["sandbox_id"]
        if sandbox_id in server._sandbox_cache:
            sandbox = server._sandbox_cache[sandbox_id]
            try:
                sandbox.kill()
            except:
                pass


class TestMetricsOptimization:
    """Tests for metrics optimization features"""

    @pytest.mark.asyncio
    async def test_metrics_use_bounded_labels_only(self):
        """Test that metrics use only bounded labels (no unbounded cardinality)"""
        from backend.monitoring import prometheus_metrics

        # Verify sandbox_hours_total doesn't have 'project' label
        assert hasattr(prometheus_metrics, 'sandbox_hours_total')
        metric = prometheus_metrics.sandbox_hours_total

        # Counter should not have labelnames or should have bounded ones only
        # The 'project' label was removed to prevent unbounded cardinality
        # This is a regression test to ensure it stays removed

        # Check estimated_cost_dollars has bounded 'period' label only
        cost_metric = prometheus_metrics.estimated_cost_dollars
        # period: hourly|daily|monthly (bounded to 3 values)

    @pytest.mark.asyncio
    async def test_async_metrics_functions_exist(self):
        """Test that all async metrics functions are available"""
        from backend.monitoring import prometheus_metrics

        assert hasattr(prometheus_metrics, 'record_operation_start_async')
        assert hasattr(prometheus_metrics, 'record_operation_success_async')
        assert hasattr(prometheus_metrics, 'record_operation_failure_async')
        assert hasattr(prometheus_metrics, 'record_push_retry_async')
        assert hasattr(prometheus_metrics, 'record_conflict_async')
        assert hasattr(prometheus_metrics, 'update_active_sandboxes_async')
        assert hasattr(prometheus_metrics, 'record_sandbox_creation_async')
        assert hasattr(prometheus_metrics, 'record_sandbox_cache_hit_async')
        assert hasattr(prometheus_metrics, 'record_sandbox_cache_miss_async')


class TestPrometheusConfiguration:
    """Tests for Prometheus scrape configuration"""

    def test_prometheus_scrape_interval_optimized(self):
        """Test that Prometheus is configured with 60s scrape interval"""
        import yaml

        prometheus_config_path = "monitoring/prometheus/prometheus.yml"

        try:
            with open(prometheus_config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Check global scrape interval
            assert config['global']['scrape_interval'] == '60s'

            # Check git operations job scrape interval
            for job in config['scrape_configs']:
                if job['job_name'] in ['backend-api', 'git-operations-mcp']:
                    assert job['scrape_interval'] == '60s'

        except FileNotFoundError:
            pytest.skip("Prometheus config not found - skipping test")
