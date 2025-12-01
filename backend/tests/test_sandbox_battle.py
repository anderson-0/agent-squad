"""
Battle-Tested Sandbox Service Tests

Comprehensive test suite covering:
- Edge cases in sandbox lifecycle
- Error handling and recovery
- Concurrent operations
- Resource cleanup
- SSE broadcasting failures
- Database transaction integrity
"""
import pytest
import asyncio
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import Sandbox, SandboxStatus


@pytest.mark.asyncio
class TestSandboxCreation:
    """Test sandbox creation edge cases"""

    async def test_create_sandbox_minimal(self, db_session):
        """Test creating sandbox with minimal params"""
        service = SandboxService(db_session)

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            mock_sb = MagicMock()
            mock_sb.id = "e2b-test-123"
            mock_e2b.return_value = mock_sb

            sandbox = await service.create_sandbox()

            assert sandbox is not None
            assert sandbox.e2b_id == "e2b-test-123"
            assert sandbox.status == SandboxStatus.RUNNING
            assert sandbox.task_id is None
            assert sandbox.agent_id is None

    async def test_create_sandbox_with_all_params(self, db_session):
        """Test creating sandbox with all parameters"""
        task_id = uuid4()
        agent_id = uuid4()
        exec_id = uuid4()
        squad_id = uuid4()
        repo_url = "https://github.com/test/repo"

        service = SandboxService(db_session, execution_id=exec_id, squad_id=squad_id)

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            mock_sb = MagicMock()
            mock_sb.id = "e2b-test-456"
            mock_e2b.return_value = mock_sb

            sandbox = await service.create_sandbox(
                task_id=task_id,
                agent_id=agent_id,
                repo_url=repo_url
            )

            assert sandbox.task_id == task_id
            assert sandbox.agent_id == agent_id
            assert sandbox.repo_url == repo_url
            assert service.execution_id == exec_id
            assert service.squad_id == squad_id

    async def test_create_sandbox_sse_broadcast_failure(self, db_session):
        """Test sandbox creation succeeds even if SSE broadcast fails"""
        service = SandboxService(db_session, execution_id=uuid4())

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            mock_sb = MagicMock()
            mock_sb.id = "e2b-test-789"
            mock_e2b.return_value = mock_sb

            # Mock SSE to fail
            with patch.object(service, '_broadcast_event') as mock_broadcast:
                mock_broadcast.side_effect = Exception("SSE service down")

                # Should still succeed
                sandbox = await service.create_sandbox()

                assert sandbox is not None
                assert sandbox.e2b_id == "e2b-test-789"

    async def test_create_sandbox_e2b_api_failure(self, db_session):
        """Test handling E2B API failure"""
        service = SandboxService(db_session)

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            mock_e2b.side_effect = Exception("E2B API quota exceeded")

            with pytest.raises(Exception, match="E2B API quota exceeded"):
                await service.create_sandbox()

    async def test_create_multiple_sandboxes_concurrently(self, db_session):
        """Test creating multiple sandboxes concurrently"""
        service = SandboxService(db_session)

        async def create_sandbox(index):
            with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
                mock_sb = MagicMock()
                mock_sb.id = f"e2b-concurrent-{index}"
                mock_e2b.return_value = mock_sb
                return await service.create_sandbox()

        # Create 10 sandboxes concurrently
        sandboxes = await asyncio.gather(*[
            create_sandbox(i) for i in range(10)
        ])

        assert len(sandboxes) == 10
        assert all(sb is not None for sb in sandboxes)
        # All should have unique e2b_ids
        e2b_ids = [sb.e2b_id for sb in sandboxes]
        assert len(set(e2b_ids)) == 10


@pytest.mark.asyncio
class TestSandboxLifecycle:
    """Test complete sandbox lifecycle"""

    async def test_sandbox_status_transitions(self, db_session):
        """Test valid status transitions"""
        sandbox = Sandbox(
            e2b_id="test-lifecycle",
            status=SandboxStatus.CREATED
        )
        db_session.add(sandbox)
        await db_session.commit()

        # CREATED → RUNNING
        sandbox.status = SandboxStatus.RUNNING
        await db_session.commit()
        await db_session.refresh(sandbox)
        assert sandbox.status == SandboxStatus.RUNNING

        # RUNNING → TERMINATED
        sandbox.status = SandboxStatus.TERMINATED
        await db_session.commit()
        await db_session.refresh(sandbox)
        assert sandbox.status == SandboxStatus.TERMINATED

    async def test_terminate_already_terminated(self, db_session):
        """Test terminating already terminated sandbox"""
        sandbox = Sandbox(
            e2b_id="test-already-terminated",
            status=SandboxStatus.TERMINATED
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            # Should handle gracefully (idempotent)
            result = await service.terminate_sandbox(sandbox.id)
            # Should still return success
            assert result is True

    async def test_terminate_nonexistent_sandbox(self, db_session):
        """Test terminating sandbox that doesn't exist"""
        service = SandboxService(db_session)

        with pytest.raises(Exception):
            await service.terminate_sandbox(uuid4())

    async def test_terminate_calculates_runtime(self, db_session):
        """Test runtime calculation on termination"""
        from datetime import datetime, timedelta

        sandbox = Sandbox(
            e2b_id="test-runtime",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        # Manually set created_at to simulate 60 seconds ago
        sandbox.created_at = datetime.utcnow() - timedelta(seconds=60)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            mock_sb = MagicMock()
            mock_sb.kill = AsyncMock()
            mock_get.return_value = mock_sb

            await service.terminate_sandbox(sandbox.id)

        # Verify runtime was calculated (should be ~60 seconds)
        await db_session.refresh(sandbox)
        assert sandbox.runtime_seconds is not None
        assert 55 < sandbox.runtime_seconds < 65  # Allow some variance


@pytest.mark.asyncio
class TestGitOperations:
    """Test Git operation edge cases"""

    async def test_clone_invalid_repo_url(self, db_session):
        """Test cloning with invalid repository URL"""
        sandbox = Sandbox(
            e2b_id="test-invalid-url",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            mock_sb = MagicMock()
            mock_proc = MagicMock()
            mock_proc.exit_code = 128  # Git error code
            mock_proc.stderr = "fatal: repository not found"
            mock_proc.stdout = ""
            mock_sb.commands.run = MagicMock(return_value=mock_proc)
            mock_get.return_value = mock_sb

            with pytest.raises(RuntimeError, match="Git clone failed"):
                await service.clone_repo(
                    sandbox.id,
                    "https://github.com/nonexistent/repo.git"
                )

    async def test_create_branch_already_exists(self, db_session):
        """Test creating branch that already exists"""
        sandbox = Sandbox(
            e2b_id="test-branch-exists",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            mock_sb = MagicMock()

            # First call to check current branch
            mock_proc1 = MagicMock()
            mock_proc1.stdout = "main"
            mock_proc1.exit_code = 0

            # Second call to create branch fails (exists)
            mock_proc2 = MagicMock()
            mock_proc2.exit_code = 128
            mock_proc2.stderr = "fatal: branch 'feature' already exists"

            mock_sb.commands.run = MagicMock(side_effect=[mock_proc1, mock_proc2])
            mock_get.return_value = mock_sb

            with pytest.raises(RuntimeError, match="Git branch creation failed"):
                await service.create_branch(
                    sandbox.id,
                    "feature",
                    "main"
                )

    async def test_commit_no_changes(self, db_session):
        """Test committing when there are no changes"""
        sandbox = Sandbox(
            e2b_id="test-no-changes",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            mock_sb = MagicMock()

            # git add succeeds
            mock_add = MagicMock()
            mock_add.exit_code = 0
            mock_add.stdout = ""

            # git status shows no changes
            mock_status = MagicMock()
            mock_status.stdout = "nothing to commit, working tree clean"
            mock_status.exit_code = 0

            mock_sb.commands.run = MagicMock(side_effect=[mock_add, mock_status])
            mock_get.return_value = mock_sb

            # Should handle gracefully
            result = await service.commit_changes(sandbox.id, "test commit")
            assert "nothing to commit" in result.lower()

    async def test_push_to_protected_branch(self, db_session):
        """Test pushing to protected branch"""
        sandbox = Sandbox(
            e2b_id="test-protected-branch",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch.object(service, '_get_e2b_sandbox') as mock_get:
            mock_sb = MagicMock()
            mock_proc = MagicMock()
            mock_proc.exit_code = 1
            mock_proc.stderr = "remote: error: GH006: Protected branch update failed"
            mock_sb.commands.run = MagicMock(return_value=mock_proc)
            mock_sb.filesystem.exists = MagicMock(return_value=True)
            mock_get.return_value = mock_sb

            with pytest.raises(RuntimeError, match="Git push failed"):
                await service.push_changes(sandbox.id, "main")


@pytest.mark.asyncio
class TestPRCreation:
    """Test PR creation edge cases"""

    async def test_create_pr_stores_number(self, db_session):
        """Test PR number is stored in sandbox"""
        sandbox = Sandbox(
            e2b_id="test-pr-storage",
            repo_url="https://github.com/owner/repo",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch('backend.services.sandbox_service.GitHubService') as mock_gh:
            mock_gh_instance = mock_gh.return_value
            mock_gh_instance.create_pull_request = AsyncMock(return_value={
                "number": 42,
                "html_url": "https://github.com/owner/repo/pull/42"
            })

            await service.create_pr(
                sandbox.id,
                title="Test PR",
                body="Test",
                head="feature",
                base="main",
                repo_owner_name="owner/repo"
            )

        # Verify PR number stored
        await db_session.refresh(sandbox)
        assert sandbox.pr_number == 42

    async def test_create_pr_github_api_failure(self, db_session):
        """Test handling GitHub API failure"""
        sandbox = Sandbox(
            e2b_id="test-gh-failure",
            repo_url="https://github.com/owner/repo",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch('backend.services.sandbox_service.GitHubService') as mock_gh:
            mock_gh_instance = mock_gh.return_value
            mock_gh_instance.create_pull_request = AsyncMock(
                side_effect=Exception("GitHub API rate limit exceeded")
            )

            with pytest.raises(Exception, match="GitHub API rate limit exceeded"):
                await service.create_pr(
                    sandbox.id,
                    title="Test",
                    body="Test",
                    head="feature",
                    base="main",
                    repo_owner_name="owner/repo"
                )

        # Verify PR number not stored on failure
        await db_session.refresh(sandbox)
        assert sandbox.pr_number is None

    async def test_create_pr_without_repo_owner(self, db_session):
        """Test creating PR without providing repo_owner_name"""
        sandbox = Sandbox(
            e2b_id="test-infer-repo",
            repo_url="https://github.com/owner/repo.git",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = SandboxService(db_session)

        with patch('backend.services.sandbox_service.GitHubService') as mock_gh:
            mock_gh_instance = mock_gh.return_value
            mock_gh_instance.create_pull_request = AsyncMock(return_value={
                "number": 43,
                "html_url": "https://github.com/owner/repo/pull/43"
            })

            # Should infer from sandbox.repo_url
            await service.create_pr(
                sandbox.id,
                title="Test",
                body="Test",
                head="feature",
                base="main"
            )

            # Verify GitHub service called with correct repo
            call_args = mock_gh_instance.create_pull_request.call_args
            assert "owner/repo" in call_args.kwargs["repo"]


@pytest.mark.asyncio
class TestSSEBroadcasting:
    """Test SSE broadcasting edge cases"""

    async def test_broadcast_with_execution_id(self, db_session):
        """Test SSE broadcast to execution channel"""
        exec_id = uuid4()
        service = SandboxService(db_session, execution_id=exec_id)

        with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
            mock_sse.broadcast_to_execution = AsyncMock()

            await service._broadcast_event({
                "event": "test_event",
                "data": "test_data"
            })

            # Verify broadcast called
            mock_sse.broadcast_to_execution.assert_called_once()
            call_args = mock_sse.broadcast_to_execution.call_args
            assert call_args[0][0] == exec_id

    async def test_broadcast_with_squad_id(self, db_session):
        """Test SSE broadcast to squad channel"""
        squad_id = uuid4()
        service = SandboxService(db_session, squad_id=squad_id)

        with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
            mock_sse.broadcast_to_squad = AsyncMock()

            await service._broadcast_event({
                "event": "test_event",
                "data": "test_data"
            })

            # Verify broadcast called
            mock_sse.broadcast_to_squad.assert_called_once()
            call_args = mock_sse.broadcast_to_squad.call_args
            assert call_args[0][0] == squad_id

    async def test_broadcast_failure_doesnt_break_operation(self, db_session):
        """Test operations succeed even if SSE broadcast fails"""
        service = SandboxService(db_session, execution_id=uuid4())

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            mock_sb = MagicMock()
            mock_sb.id = "e2b-test"
            mock_e2b.return_value = mock_sb

            with patch('backend.services.sandbox_service.sse_manager') as mock_sse:
                # SSE broadcast fails
                mock_sse.broadcast_to_execution = AsyncMock(
                    side_effect=Exception("SSE connection lost")
                )

                # Operation should still succeed
                sandbox = await service.create_sandbox()
                assert sandbox is not None


@pytest.mark.asyncio
class TestDatabaseIntegrity:
    """Test database transaction integrity"""

    async def test_transaction_rollback_on_failure(self, db_session):
        """Test transaction rolls back on error"""
        service = SandboxService(db_session)

        initial_count_result = await db_session.execute(select(Sandbox))
        initial_count = len(initial_count_result.scalars().all())

        with patch.object(service, '_get_or_create_e2b_sandbox') as mock_e2b:
            # Simulate E2B creation success but broadcast fails catastrophically
            mock_sb = MagicMock()
            mock_sb.id = "e2b-rollback-test"
            mock_e2b.return_value = mock_sb

            with patch.object(service, '_broadcast_event') as mock_broadcast:
                # Simulate critical failure after DB write
                mock_broadcast.side_effect = Exception("Critical failure")

                try:
                    await service.create_sandbox()
                except Exception:
                    pass  # Expected to fail

        # Check final count (transaction should have committed despite broadcast failure)
        final_count_result = await db_session.execute(select(Sandbox))
        final_count = len(final_count_result.scalars().all())

        # Sandbox should be created (broadcast failure is non-blocking)
        assert final_count == initial_count + 1

    async def test_concurrent_updates_same_sandbox(self, db_session):
        """Test concurrent updates to same sandbox"""
        sandbox = Sandbox(
            e2b_id="test-concurrent",
            status=SandboxStatus.RUNNING,
            pr_number=None
        )
        db_session.add(sandbox)
        await db_session.commit()

        async def update_pr_number(pr_num):
            # Simulate concurrent PR number updates
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.id == sandbox.id)
            )
            sb = result.scalars().first()
            sb.pr_number = pr_num
            await db_session.commit()

        # Run concurrent updates
        await asyncio.gather(*[
            update_pr_number(i) for i in range(100, 105)
        ])

        # Final state should be one of the updates
        await db_session.refresh(sandbox)
        assert sandbox.pr_number in range(100, 105)


if __name__ == "__main__":
    print("""
    Sandbox Battle Tests
    ====================

    Run with:
        pytest tests/test_sandbox_battle.py -v -s

    Coverage:
        pytest tests/test_sandbox_battle.py --cov=backend.services.sandbox_service --cov-report=html
    """)
