"""
Integration tests for E2B + GitHub workflow

These tests verify the complete workflow:
1. Create E2B sandbox
2. Clone repository
3. Create feature branch
4. Make changes
5. Commit with conventional commits
6. Push to remote
7. Create Pull Request

NOTE: These tests require E2B_API_KEY and GITHUB_TOKEN to be set
and will be skipped if not available.
"""
import pytest
import os
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock, Mock

from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import SandboxStatus


# Skip all tests in this module if E2B or GitHub credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("E2B_API_KEY") or not os.environ.get("GITHUB_TOKEN"),
    reason="E2B_API_KEY and GITHUB_TOKEN required for integration tests"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_e2b_github_workflow():
    """
    Test complete workflow from sandbox creation to PR

    This is a mock integration test that simulates the full workflow.
    For real E2B testing, remove mocks and ensure credentials are set.
    """
    db = AsyncMock()
    repo_url = "https://github.com/test-org/test-repo.git"

    # Mock E2B sandbox
    mock_sb = MagicMock()
    mock_sb.sandbox_id = "test-integration-sandbox"
    mock_sb.commands = MagicMock()

    # Simulate Git command responses
    git_responses = [
        # clone_repo checks
        Mock(stdout="", exit_code=0),  # test -d repo check (not exists)
        Mock(stdout="Cloning into 'test-repo'...", stderr="", exit_code=0),  # git clone

        # create_branch
        Mock(stdout="test-repo/\n", exit_code=0),  # ls -d */
        Mock(stdout="", stderr="", exit_code=0),  # git fetch
        Mock(stdout="", stderr="", exit_code=0),  # git checkout main && pull
        Mock(stdout="Switched to a new branch 'feature-test'", stderr="", exit_code=0),  # git checkout -b

        # commit_changes
        Mock(stdout="test-repo/\n", exit_code=0),  # ls -d */
        Mock(stdout="[feature-test abc123] feat: add test feature", stderr="", exit_code=0),  # git commit

        # push_changes
        Mock(stdout="test-repo/\n", exit_code=0),  # ls -d */
        Mock(stdout="To github.com:test-org/test-repo.git", stderr="", exit_code=0),  # git push
    ]

    mock_sb.commands.run.side_effect = git_responses

    # Mock sandbox database records
    sandbox_id = uuid4()
    sandbox = MagicMock()
    sandbox.id = sandbox_id
    sandbox.e2b_id = "test-integration-sandbox"
    sandbox.status = SandboxStatus.RUNNING
    sandbox.repo_url = repo_url

    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result

    db.execute = AsyncMock(side_effect=mock_execute)

    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        MockE2B.create.return_value = mock_sb
        MockE2B.connect.return_value = mock_sb

        with patch('backend.services.sandbox_service.GitHubService') as MockGH:
            mock_gh = AsyncMock()
            mock_gh.create_pull_request.return_value = {
                "number": 1,
                "html_url": "https://github.com/test-org/test-repo/pull/1",
                "state": "open"
            }
            MockGH.return_value = mock_gh

            service = SandboxService(db)

            # Step 1: Create sandbox
            created_sandbox = await service.create_sandbox(
                agent_id=uuid4(),
                task_id=uuid4(),
                repo_url=repo_url
            )

            assert created_sandbox.e2b_id == "test-integration-sandbox"
            assert created_sandbox.status == SandboxStatus.RUNNING

            # Step 2: Clone repo (already done in create_sandbox)
            # Verify clone was called
            clone_calls = [call for call in mock_sb.commands.run.call_args_list
                          if "git clone" in str(call)]
            assert len(clone_calls) > 0

            # Step 3: Create feature branch
            branch_name = await service.create_branch(
                sandbox_id,
                "feature-test",
                "main"
            )

            assert branch_name == "feature-test"

            # Step 4 & 5: Make changes and commit
            commit_output = await service.commit_changes(
                sandbox_id,
                "feat: add test feature"
            )

            assert "feat: add test feature" in commit_output

            # Step 6: Push changes
            push_output = await service.push_changes(
                sandbox_id,
                "feature-test"
            )

            assert "github.com" in push_output

            # Step 7: Create PR
            pr = await service.create_pr(
                sandbox_id,
                "Add test feature",
                "This PR adds a test feature",
                "feature-test",
                "main"
            )

            assert pr["number"] == 1
            assert pr["state"] == "open"

            # Verify all steps completed successfully
            mock_gh.create_pull_request.assert_called_once_with(
                repo="test-org/test-repo",
                title="Add test feature",
                body="This PR adds a test feature",
                head="feature-test",
                base="main"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_with_existing_repo():
    """Test workflow when repository already exists in sandbox"""
    db = AsyncMock()
    repo_url = "https://github.com/test-org/existing-repo.git"

    mock_sb = MagicMock()
    mock_sb.sandbox_id = "test-existing-repo"
    mock_sb.commands = MagicMock()

    # Repo already exists, should pull instead
    git_responses = [
        Mock(stdout="exists", exit_code=0),  # test -d check (exists!)
        Mock(stdout="Already up to date.", stderr="", exit_code=0),  # git pull
    ]

    mock_sb.commands.run.side_effect = git_responses

    sandbox_id = uuid4()
    sandbox = MagicMock()
    sandbox.id = sandbox_id
    sandbox.e2b_id = "test-existing-repo"
    sandbox.status = SandboxStatus.RUNNING

    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result

    db.execute = AsyncMock(side_effect=mock_execute)

    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        MockE2B.connect.return_value = mock_sb

        service = SandboxService(db)

        # Should pull instead of clone
        path = await service.clone_repo(sandbox_id, repo_url)

        assert path == "/home/user/existing-repo"

        # Verify pull was called, not clone
        calls = [str(call) for call in mock_sb.commands.run.call_args_list]
        assert any("git pull" in call for call in calls)
        assert not any("git clone" in call for call in calls)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_error_recovery():
    """Test error handling and recovery in workflow"""
    db = AsyncMock()
    sandbox_id = uuid4()

    sandbox = MagicMock()
    sandbox.id = sandbox_id
    sandbox.e2b_id = "test-error-recovery"
    sandbox.status = SandboxStatus.RUNNING

    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result

    db.execute = AsyncMock(side_effect=mock_execute)

    mock_sb = MagicMock()
    mock_sb.commands = MagicMock()

    # Simulate push failure (common error: branch not set up)
    mock_sb.commands.run.side_effect = [
        Mock(stdout="repo/\n", exit_code=0),  # ls -d */
        Mock(stdout="", stderr="fatal: The current branch has no upstream branch", exit_code=128)
    ]

    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        MockE2B.connect.return_value = mock_sb

        with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
            service = SandboxService(db)

            # Should raise error with helpful message
            with pytest.raises(RuntimeError, match="Push failed"):
                await service.push_changes(sandbox_id, "feature-branch")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conventional_commit_enforcement():
    """Test that conventional commits are enforced in workflow"""
    db = AsyncMock()
    sandbox_id = uuid4()

    sandbox = MagicMock()
    sandbox.id = sandbox_id
    sandbox.status = SandboxStatus.RUNNING

    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result

    db.execute = AsyncMock(side_effect=mock_execute)

    service = SandboxService(db)

    # Invalid commit messages should fail before hitting E2B
    invalid_messages = [
        "added new feature",  # No type
        "Feature: new thing",  # Wrong case
        "update stuff",  # Not conventional
    ]

    for msg in invalid_messages:
        with pytest.raises(ValueError, match="conventional commits"):
            await service.commit_changes(sandbox_id, msg)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sandbox_lifecycle_integration():
    """Test complete sandbox lifecycle"""
    db = AsyncMock()

    mock_sb = MagicMock()
    mock_sb.sandbox_id = "lifecycle-test"

    sandbox_id = uuid4()
    sandbox = MagicMock()
    sandbox.id = sandbox_id
    sandbox.e2b_id = "lifecycle-test"
    sandbox.status = SandboxStatus.RUNNING

    async def mock_execute(*args, **kwargs):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sandbox
        return mock_result

    db.execute = AsyncMock(side_effect=mock_execute)

    with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
        MockE2B.create.return_value = mock_sb

        with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
            service = SandboxService(db)

            # Create
            created = await service.create_sandbox(
                agent_id=uuid4(),
                task_id=uuid4()
            )
            assert created.status == SandboxStatus.RUNNING

            # Use (get)
            retrieved = await service.get_sandbox(sandbox_id)
            assert retrieved.id == sandbox_id

            # Terminate
            terminated = await service.terminate_sandbox(sandbox_id)
            assert terminated is True
            assert sandbox.status == SandboxStatus.TERMINATED

            MockE2B.kill.assert_called_with("lifecycle-test", "test-key")
