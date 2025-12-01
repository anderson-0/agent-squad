"""
Test SSE broadcasting for sandbox events

This test verifies that sandbox operations correctly broadcast SSE events
to both execution and squad channels.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.sandbox_service import SandboxService
from backend.schemas.sandbox_events import (
    SandboxCreatedEvent,
    GitOperationEvent,
    PRCreatedEvent,
    SandboxTerminatedEvent,
)


@pytest.mark.asyncio
async def test_sandbox_created_broadcasts_sse():
    """Test that create_sandbox broadcasts sandbox_created event"""
    execution_id = uuid4()
    squad_id = uuid4()

    # Mock database session
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Mock SSE manager
    with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
        mock_sse.broadcast_to_execution = AsyncMock()
        mock_sse.broadcast_to_squad = AsyncMock()

        # Mock E2B API
        with patch('backend.services.sandbox_service.Sandbox') as mock_sandbox_class:
            mock_sandbox_instance = AsyncMock()
            mock_sandbox_instance.id = "test-sandbox-123"
            mock_sandbox_class.return_value = mock_sandbox_instance

            # Create service with execution_id and squad_id
            service = SandboxService(mock_db, execution_id=execution_id, squad_id=squad_id)

            # Mock the actual E2B sandbox creation
            with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
                mock_e2b.return_value = mock_sandbox_instance

                # Create sandbox
                sandbox = await service.create_sandbox(
                    task_id=uuid4(),
                    agent_id=uuid4(),
                    repo_url="https://github.com/test/repo.git"
                )

                # Verify SSE broadcasts were called
                assert mock_sse.broadcast_to_execution.called
                assert mock_sse.broadcast_to_squad.called

                # Verify event data
                execution_call = mock_sse.broadcast_to_execution.call_args
                assert execution_call[0][0] == execution_id
                assert execution_call[0][1] == "sandbox_created"

                squad_call = mock_sse.broadcast_to_squad.call_args
                assert squad_call[0][0] == squad_id
                assert squad_call[0][1] == "sandbox_created"


@pytest.mark.asyncio
async def test_git_operation_broadcasts_sse():
    """Test that clone_repo broadcasts git_operation events"""
    execution_id = uuid4()
    sandbox_id = uuid4()

    mock_db = AsyncMock()

    with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
        mock_sse.broadcast_to_execution = AsyncMock()

        service = SandboxService(mock_db, execution_id=execution_id)

        # Mock sandbox lookup
        with patch.object(service, '_get_sandbox') as mock_get_sandbox:
            mock_sandbox = MagicMock()
            mock_sandbox.e2b_id = "e2b-123"
            mock_get_sandbox.return_value = mock_sandbox

            # Mock E2B process execution
            with patch('backend.services.sandbox_service.Sandbox') as mock_sandbox_class:
                mock_sandbox_instance = AsyncMock()
                mock_process = MagicMock()
                mock_process.stdout = "Cloning into 'repo'...\ndone."
                mock_process.stderr = ""
                mock_process.exit_code = 0
                mock_sandbox_instance.process.start_and_wait = AsyncMock(return_value=mock_process)
                mock_sandbox_class.return_value = mock_sandbox_instance

                # Clone repo
                await service.clone_repo(sandbox_id, "https://github.com/test/repo.git")

                # Verify SSE broadcasts for started and completed
                calls = mock_sse.broadcast_to_execution.call_args_list
                assert len(calls) >= 2  # started + completed

                # Check started event
                started_event = calls[0][0][2]
                assert started_event['event'] == 'git_operation'
                assert started_event['operation'] == 'clone'
                assert started_event['status'] == 'started'

                # Check completed event
                completed_event = calls[-1][0][2]
                assert completed_event['event'] == 'git_operation'
                assert completed_event['operation'] == 'clone'
                assert completed_event['status'] == 'completed'


@pytest.mark.asyncio
async def test_terminate_broadcasts_runtime():
    """Test that terminate_sandbox broadcasts runtime_seconds"""
    execution_id = uuid4()
    sandbox_id = uuid4()

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
        mock_sse.broadcast_to_execution = AsyncMock()

        service = SandboxService(mock_db, execution_id=execution_id)

        # Mock sandbox with creation time
        from datetime import datetime, timedelta
        with patch.object(service, '_get_sandbox') as mock_get_sandbox:
            mock_sandbox = MagicMock()
            mock_sandbox.e2b_id = "e2b-123"
            mock_sandbox.created_at = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago
            mock_get_sandbox.return_value = mock_sandbox

            # Mock E2B API
            with patch('backend.services.sandbox_service.Sandbox') as mock_sandbox_class:
                mock_sandbox_instance = AsyncMock()
                mock_sandbox_instance.kill = AsyncMock()
                mock_sandbox_class.return_value = mock_sandbox_instance

                # Terminate sandbox
                await service.terminate_sandbox(sandbox_id)

                # Verify SSE broadcast with runtime
                call_args = mock_sse.broadcast_to_execution.call_args
                event_data = call_args[0][2]

                assert event_data['event'] == 'sandbox_terminated'
                assert 'runtime_seconds' in event_data
                assert event_data['runtime_seconds'] > 0


def test_sandbox_service_initialization():
    """Test that SandboxService accepts execution_id and squad_id"""
    mock_db = AsyncMock()
    execution_id = uuid4()
    squad_id = uuid4()

    service = SandboxService(mock_db, execution_id=execution_id, squad_id=squad_id)

    assert service.execution_id == execution_id
    assert service.squad_id == squad_id


def test_sandbox_service_without_sse_context():
    """Test that SandboxService works without execution_id/squad_id (no SSE)"""
    mock_db = AsyncMock()

    service = SandboxService(mock_db)

    assert service.execution_id is None
    assert service.squad_id is None
