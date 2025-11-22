import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import Sandbox, SandboxStatus

@pytest.mark.asyncio
async def test_create_sandbox():
    # Mock DB session
    db = AsyncMock()
    
    # Mock E2B
    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        mock_sb = MagicMock()
        mock_sb.sandbox_id = "test-sandbox-id"
        MockE2B.create.return_value = mock_sb
        
        # Mock env vars
        with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
            service = SandboxService(db)
            
            # Test creation
            sandbox = await service.create_sandbox(
                agent_id=uuid4(),
                task_id=uuid4(),
                repo_url="https://github.com/owner/repo.git"
            )
            
            assert sandbox.e2b_id == "test-sandbox-id"
            assert sandbox.status == SandboxStatus.RUNNING
            assert sandbox.repo_url == "https://github.com/owner/repo.git"
            
            # Verify DB add
            db.add.assert_called_once()
            db.commit.assert_called()

@pytest.mark.asyncio
async def test_terminate_sandbox():
    db = AsyncMock()
    sandbox_id = uuid4()
    
    # Mock existing sandbox
    sandbox = Sandbox(
        id=sandbox_id,
        e2b_id="test-sb",
        status=SandboxStatus.RUNNING
    )
    
    # Mock get_sandbox
    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result
    
    db.execute = AsyncMock(side_effect=mock_execute)
    
    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        with patch.dict('os.environ', {'E2B_API_KEY': 'test-key'}):
            service = SandboxService(db)
            
            result = await service.terminate_sandbox(sandbox_id)
            
            assert result is True
            assert sandbox.status == SandboxStatus.TERMINATED
            MockE2B.kill.assert_called_with("test-sb", "test-key")
            db.commit.assert_called()
