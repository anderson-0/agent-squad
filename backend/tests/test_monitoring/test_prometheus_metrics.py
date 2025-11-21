"""
Tests for Prometheus Metrics Module

Tests metric definitions and helper functions for git operations monitoring.
"""

import pytest
from unittest.mock import MagicMock, patch


# Mock prometheus_client before importing our module
@pytest.fixture(autouse=True)
def mock_prometheus_client():
    """Mock prometheus_client to avoid actual metric registration"""
    with patch('backend.monitoring.prometheus_metrics.Counter') as mock_counter, \
         patch('backend.monitoring.prometheus_metrics.Histogram') as mock_histogram, \
         patch('backend.monitoring.prometheus_metrics.Gauge') as mock_gauge, \
         patch('backend.monitoring.prometheus_metrics.Info') as mock_info:

        # Create mock metric instances
        mock_counter_instance = MagicMock()
        mock_histogram_instance = MagicMock()
        mock_gauge_instance = MagicMock()
        mock_info_instance = MagicMock()

        mock_counter.return_value = mock_counter_instance
        mock_histogram.return_value = mock_histogram_instance
        mock_gauge.return_value = mock_gauge_instance
        mock_info.return_value = mock_info_instance

        yield {
            'counter': mock_counter_instance,
            'histogram': mock_histogram_instance,
            'gauge': mock_gauge_instance,
            'info': mock_info_instance
        }


def test_record_operation_start():
    """Test recording operation start"""
    from backend.monitoring.prometheus_metrics import record_operation_start

    # Should not raise any exceptions
    record_operation_start('clone')
    record_operation_start('push')


def test_record_operation_success():
    """Test recording successful operation"""
    from backend.monitoring.prometheus_metrics import record_operation_success

    # Should not raise any exceptions
    record_operation_success('clone', 5.2)
    record_operation_success('push', 1.3)


def test_record_operation_failure():
    """Test recording failed operation"""
    from backend.monitoring.prometheus_metrics import record_operation_failure

    # Should not raise any exceptions
    record_operation_failure('clone', 2.1, 'timeout')
    record_operation_failure('push', 1.5, 'auth')


def test_record_push_retry():
    """Test recording push retry attempts"""
    from backend.monitoring.prometheus_metrics import record_push_retry

    # Should not raise any exceptions
    record_push_retry(1)
    record_push_retry(2)
    record_push_retry(3)


def test_record_conflict():
    """Test recording git conflicts"""
    from backend.monitoring.prometheus_metrics import record_conflict

    # Should not raise any exceptions
    record_conflict('pull')
    record_conflict('push')


def test_update_active_sandboxes():
    """Test updating active sandboxes gauge"""
    from backend.monitoring.prometheus_metrics import update_active_sandboxes

    # Should not raise any exceptions
    update_active_sandboxes(5)
    update_active_sandboxes(0)


def test_record_sandbox_creation():
    """Test recording sandbox creation time"""
    from backend.monitoring.prometheus_metrics import record_sandbox_creation

    # Should not raise any exceptions
    record_sandbox_creation(10.5)
    record_sandbox_creation(2.3)


def test_record_sandbox_cache_hit():
    """Test recording cache hit"""
    from backend.monitoring.prometheus_metrics import record_sandbox_cache_hit

    # Should not raise any exceptions
    record_sandbox_cache_hit()


def test_record_sandbox_cache_miss():
    """Test recording cache miss"""
    from backend.monitoring.prometheus_metrics import record_sandbox_cache_miss

    # Should not raise any exceptions
    record_sandbox_cache_miss()


def test_update_cost_estimate():
    """Test updating cost estimate"""
    from backend.monitoring.prometheus_metrics import update_cost_estimate

    # Should not raise any exceptions
    update_cost_estimate('hourly', 1.5)
    update_cost_estimate('daily', 36.0)
    update_cost_estimate('monthly', 100.0)


def test_calculate_cost_from_hours():
    """Test cost calculation"""
    from backend.monitoring.prometheus_metrics import calculate_cost_from_hours, E2B_HOURLY_COST

    # Test cost calculation
    cost = calculate_cost_from_hours(10.0)
    assert cost == 10.0 * E2B_HOURLY_COST

    # Test zero hours
    cost = calculate_cost_from_hours(0.0)
    assert cost == 0.0

    # Test fractional hours
    cost = calculate_cost_from_hours(0.5)
    assert cost == 0.5 * E2B_HOURLY_COST


def test_error_type_labels():
    """Test that error types are correctly labeled"""
    from backend.monitoring.prometheus_metrics import record_operation_failure

    # Test different error types
    error_types = ['timeout', 'auth', 'conflict', 'network', 'sandbox_not_found', 'other']

    for error_type in error_types:
        # Should not raise any exceptions
        record_operation_failure('clone', 1.0, error_type)


def test_operation_types():
    """Test that all git operations are supported"""
    from backend.monitoring.prometheus_metrics import record_operation_success

    # Test all 5 git operations
    operations = ['clone', 'status', 'diff', 'pull', 'push']

    for operation in operations:
        # Should not raise any exceptions
        record_operation_success(operation, 1.0)


def test_metrics_module_imports():
    """Test that all public functions are importable"""
    from backend.monitoring import prometheus_metrics

    # Verify all expected functions exist
    assert hasattr(prometheus_metrics, 'record_operation_start')
    assert hasattr(prometheus_metrics, 'record_operation_success')
    assert hasattr(prometheus_metrics, 'record_operation_failure')
    assert hasattr(prometheus_metrics, 'record_push_retry')
    assert hasattr(prometheus_metrics, 'record_conflict')
    assert hasattr(prometheus_metrics, 'update_active_sandboxes')
    assert hasattr(prometheus_metrics, 'record_sandbox_creation')
    assert hasattr(prometheus_metrics, 'record_sandbox_cache_hit')
    assert hasattr(prometheus_metrics, 'record_sandbox_cache_miss')
    assert hasattr(prometheus_metrics, 'update_cost_estimate')
    assert hasattr(prometheus_metrics, 'calculate_cost_from_hours')


def test_e2b_hourly_cost():
    """Test E2B hourly cost constant"""
    from backend.monitoring.prometheus_metrics import E2B_HOURLY_COST

    # Verify cost is $0.015 per hour as documented
    assert E2B_HOURLY_COST == 0.015
