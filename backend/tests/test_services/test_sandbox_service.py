"""
Unit tests for SandboxService - E2B Sandbox and Git Operations

Test Coverage:
- Sandbox lifecycle (create, get, terminate)
- Git operations (clone, branch, commit, push)
- GitHub PR creation
- Conventional commit validation
- Error handling and edge cases
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from uuid import uuid4
from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import Sandbox, SandboxStatus


class TestSandboxLifecycle:
    """Test sandbox creation, connection, and termination"""

    @pytest.mark.asyncio
    async def test_create_sandbox_with_template(self):
        """Test creating sandbox with custom template"""
        db = AsyncMock()

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            mock_sb = MagicMock()
            mock_sb.sandbox_id = "test-sandbox-id"
            MockE2B.create.return_value = mock_sb

            with patch.dict('os.environ', {
                'E2B_API_KEY': 'test-key',
                'GITHUB_TOKEN': 'gh-token',
                'E2B_TEMPLATE_ID': 'custom-template'
            }):
                service = SandboxService(db)

                sandbox = await service.create_sandbox(
                    agent_id=uuid4(),
                    task_id=uuid4(),
                    repo_url=None
                )

                assert sandbox.e2b_id == "test-sandbox-id"
                assert sandbox.status == SandboxStatus.RUNNING
                db.add.assert_called_once()
                db.commit.assert_called()
                MockE2B.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sandbox_with_repo(self):
        """Test creating sandbox and cloning repo"""
        db = AsyncMock()
        repo_url = "https://github.com/owner/repo.git"

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            mock_sb = MagicMock()
            mock_sb.sandbox_id = "test-sandbox-id"
            mock_sb.commands = MagicMock()
            mock_sb.commands.run.return_value = Mock(
                stdout="",
                stderr="",
                exit_code=0
            )
            MockE2B.create.return_value = mock_sb
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                # Mock get_sandbox for clone_repo call
                async def mock_execute(*args, **kwargs):
                    mock_result = MagicMock()
                    sandbox = Sandbox(
                        id=uuid4(),
                        e2b_id="test-sandbox-id",
                        status=SandboxStatus.RUNNING
                    )
                    mock_result.scalars.return_value.first.return_value = sandbox
                    return mock_result

                db.execute = AsyncMock(side_effect=mock_execute)

                sandbox = await service.create_sandbox(
                    agent_id=uuid4(),
                    task_id=uuid4(),
                    repo_url=repo_url
                )

                assert sandbox.repo_url == repo_url
                # Verify git clone was attempted
                mock_sb.commands.run.assert_called()

    @pytest.mark.asyncio
    async def test_create_sandbox_missing_api_key(self):
        """Test creating sandbox without API key raises error"""
        db = AsyncMock()

        with patch('backend.services.sandbox_service.E2BSandbox'):
            with patch.dict('os.environ', {}, clear=True):
                service = SandboxService(db)

                with pytest.raises(RuntimeError, match="E2B_API_KEY not configured"):
                    await service.create_sandbox()

    @pytest.mark.asyncio
    async def test_get_sandbox(self):
        """Test retrieving sandbox by ID"""
        db = AsyncMock()
        sandbox_id = uuid4()

        expected_sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = expected_sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)
        sandbox = await service.get_sandbox(sandbox_id)

        assert sandbox == expected_sandbox

    @pytest.mark.asyncio
    async def test_get_running_sandbox_by_task(self):
        """Test finding running sandbox for a task"""
        db = AsyncMock()
        task_id = uuid4()

        expected_sandbox = Sandbox(
            id=uuid4(),
            e2b_id="test-sb",
            task_id=task_id,
            status=SandboxStatus.RUNNING
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = expected_sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)
        sandbox = await service.get_running_sandbox_by_task(task_id)

        assert sandbox == expected_sandbox
        assert sandbox.task_id == task_id

    @pytest.mark.asyncio
    async def test_terminate_sandbox_success(self):
        """Test successfully terminating a sandbox"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

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

    @pytest.mark.asyncio
    async def test_terminate_sandbox_already_terminated(self):
        """Test terminating an already terminated sandbox"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.TERMINATED
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)
        result = await service.terminate_sandbox(sandbox_id)

        assert result is True
        # Should not attempt to kill again
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_terminate_sandbox_not_found(self):
        """Test terminating a non-existent sandbox"""
        db = AsyncMock()

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)
        result = await service.terminate_sandbox(uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_terminate_sandbox_e2b_not_found_error(self):
        """Test terminating sandbox when E2B says not found"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.kill.side_effect = Exception("Sandbox not found")

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key'}):
                service = SandboxService(db)

                result = await service.terminate_sandbox(sandbox_id)

                # Should still mark as terminated
                assert result is True
                assert sandbox.status == SandboxStatus.TERMINATED


class TestGitOperations:
    """Test Git operations in sandbox"""

    @pytest.mark.asyncio
    async def test_clone_repo_new(self):
        """Test cloning a new repository"""
        db = AsyncMock()
        sandbox_id = uuid4()
        repo_url = "https://github.com/owner/repo.git"

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        # Repo doesn't exist
        mock_sb.commands.run.side_effect = [
            Mock(stdout="", exit_code=0),  # test -d check
            Mock(stdout="", stderr="", exit_code=0)  # git clone
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                path = await service.clone_repo(sandbox_id, repo_url)

                assert path == "/home/user/repo"
                assert mock_sb.commands.run.call_count == 2

    @pytest.mark.asyncio
    async def test_clone_repo_existing(self):
        """Test cloning when repo already exists (pulls instead)"""
        db = AsyncMock()
        sandbox_id = uuid4()
        repo_url = "https://github.com/owner/repo.git"

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        # Repo exists
        mock_sb.commands.run.side_effect = [
            Mock(stdout="exists", exit_code=0),  # test -d check
            Mock(stdout="", stderr="", exit_code=0)  # git pull
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                path = await service.clone_repo(sandbox_id, repo_url)

                assert path == "/home/user/repo"

    @pytest.mark.asyncio
    async def test_clone_repo_failure(self):
        """Test clone failure handling"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="", exit_code=0),  # test -d check
            Mock(stdout="", stderr="fatal: repository not found", exit_code=128)
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                with pytest.raises(RuntimeError, match="Clone failed"):
                    await service.clone_repo(sandbox_id, "https://github.com/invalid/repo.git")

    @pytest.mark.asyncio
    async def test_create_branch_new(self):
        """Test creating a new branch"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="repo/\n", exit_code=0),  # ls -d */
            Mock(stdout="", stderr="", exit_code=0),  # git fetch
            Mock(stdout="", stderr="", exit_code=0),  # git checkout + pull
            Mock(stdout="", stderr="", exit_code=0)  # git checkout -b
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                branch = await service.create_branch(
                    sandbox_id,
                    "feature-123",
                    "main"
                )

                assert branch == "feature-123"

    @pytest.mark.asyncio
    async def test_create_branch_already_exists(self):
        """Test creating branch when it already exists"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="repo/\n", exit_code=0),  # ls -d */
            Mock(stdout="", stderr="", exit_code=0),  # git fetch
            Mock(stdout="", stderr="", exit_code=0),  # git checkout + pull
            Mock(stdout="", stderr="already exists", exit_code=128),  # git checkout -b fails
            Mock(stdout="", stderr="", exit_code=0)  # git checkout existing
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                branch = await service.create_branch(
                    sandbox_id,
                    "feature-123",
                    "main"
                )

                assert branch == "feature-123"

    @pytest.mark.asyncio
    async def test_commit_changes_success(self):
        """Test committing changes with conventional commit"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="repo/\n", exit_code=0),  # ls -d */
            Mock(stdout="[main abc123] feat: add feature", stderr="", exit_code=0)
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                output = await service.commit_changes(
                    sandbox_id,
                    "feat: add new feature"
                )

                assert "feat: add feature" in output

    @pytest.mark.asyncio
    async def test_commit_changes_nothing_to_commit(self):
        """Test committing when there are no changes"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="repo/\n", exit_code=0),  # ls -d */
            Mock(stdout="nothing to commit", stderr="", exit_code=0)
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                output = await service.commit_changes(
                    sandbox_id,
                    "fix: some fix"
                )

                assert "nothing to commit" in output

    @pytest.mark.asyncio
    async def test_push_changes_success(self):
        """Test pushing changes to remote"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.side_effect = [
            Mock(stdout="repo/\n", exit_code=0),  # ls -d */
            Mock(stdout="To github.com:owner/repo.git", stderr="", exit_code=0)
        ]

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                output = await service.push_changes(
                    sandbox_id,
                    "feature-123"
                )

                assert "github.com" in output


class TestConventionalCommits:
    """Test conventional commit message validation"""

    def test_validate_conventional_commit_valid(self):
        """Test valid conventional commit messages"""
        service = SandboxService(AsyncMock())

        valid_messages = [
            "feat: add new feature",
            "fix: resolve bug in authentication",
            "chore: update dependencies",
            "docs: update README",
            "style: format code",
            "refactor: simplify logic",
            "test: add unit tests",
            "build: update build script",
            "ci: fix CI pipeline",
            "perf: improve performance",
            "revert: revert previous commit",
            "feat(auth): add OAuth support",
            "fix(api): handle null values"
        ]

        for msg in valid_messages:
            assert service._validate_conventional_commit(msg), f"Failed for: {msg}"

    def test_validate_conventional_commit_invalid(self):
        """Test invalid conventional commit messages"""
        service = SandboxService(AsyncMock())

        invalid_messages = [
            "add new feature",  # No type
            "Feature: add new feature",  # Invalid type
            "feat:",  # No description
            "feat: ",  # Empty description
            "FEAT: add feature",  # Wrong case
        ]

        for msg in invalid_messages:
            assert not service._validate_conventional_commit(msg), f"Should fail for: {msg}"

    @pytest.mark.asyncio
    async def test_commit_with_invalid_message(self):
        """Test that invalid commit message raises error"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)

        with pytest.raises(ValueError, match="Commit message must follow conventional commits"):
            await service.commit_changes(
                sandbox_id,
                "invalid commit message"
            )


class TestGitHubPRCreation:
    """Test GitHub Pull Request creation"""

    @pytest.mark.asyncio
    async def test_create_pr_with_repo_owner_name(self):
        """Test creating PR with explicit repo owner/name"""
        db = AsyncMock()
        sandbox_id = uuid4()

        with patch('backend.services.sandbox_service.GitHubService') as MockGH:
            mock_gh_instance = AsyncMock()
            mock_gh_instance.create_pull_request.return_value = {
                "number": 123,
                "html_url": "https://github.com/owner/repo/pull/123"
            }
            MockGH.return_value = mock_gh_instance

            with patch.dict('os.environ', {'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                pr = await service.create_pr(
                    sandbox_id,
                    "Add new feature",
                    "This PR adds...",
                    "feature-123",
                    "main",
                    "owner/repo"
                )

                assert pr["number"] == 123
                mock_gh_instance.create_pull_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pr_infer_from_sandbox(self):
        """Test creating PR by inferring repo from sandbox"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING,
            repo_url="https://github.com/owner/repo.git"
        )

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.GitHubService') as MockGH:
            mock_gh_instance = AsyncMock()
            mock_gh_instance.create_pull_request.return_value = {
                "number": 456,
                "html_url": "https://github.com/owner/repo/pull/456"
            }
            MockGH.return_value = mock_gh_instance

            with patch.dict('os.environ', {'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                pr = await service.create_pr(
                    sandbox_id,
                    "Fix bug",
                    "This PR fixes...",
                    "fix-bug",
                    "main"
                )

                assert pr["number"] == 456

    @pytest.mark.asyncio
    async def test_create_pr_missing_github_token(self):
        """Test creating PR without GitHub token"""
        db = AsyncMock()

        with patch.dict('os.environ', {}, clear=True):
            service = SandboxService(db)

            with pytest.raises(RuntimeError, match="GITHUB_TOKEN not configured"):
                await service.create_pr(
                    uuid4(),
                    "Title",
                    "Body",
                    "head",
                    "main",
                    "owner/repo"
                )


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_get_e2b_connection_not_running(self):
        """Test connecting to non-running sandbox"""
        db = AsyncMock()

        sandbox = Sandbox(
            id=uuid4(),
            e2b_id="test-sb",
            status=SandboxStatus.TERMINATED
        )

        with patch.dict('os.environ', {'E2B_API_KEY': 'test-key'}):
            service = SandboxService(db)

            with pytest.raises(RuntimeError, match="is not running"):
                await service._get_e2b_connection(sandbox)

    @pytest.mark.asyncio
    async def test_get_e2b_connection_failure(self):
        """Test E2B connection failure"""
        db = AsyncMock()

        sandbox = Sandbox(
            id=uuid4(),
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.side_effect = Exception("Connection failed")

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key'}):
                service = SandboxService(db)

                with pytest.raises(Exception, match="Connection failed"):
                    await service._get_e2b_connection(sandbox)

                # Verify status updated to ERROR
                await db.commit.assert_called()
                assert sandbox.status == SandboxStatus.ERROR

    @pytest.mark.asyncio
    async def test_clone_repo_sandbox_not_found(self):
        """Test cloning when sandbox doesn't exist"""
        db = AsyncMock()

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = SandboxService(db)

        with pytest.raises(ValueError, match="Sandbox not found"):
            await service.clone_repo(uuid4(), "https://github.com/owner/repo.git")

    @pytest.mark.asyncio
    async def test_create_branch_no_repos(self):
        """Test creating branch when no repos exist in sandbox"""
        db = AsyncMock()
        sandbox_id = uuid4()

        sandbox = Sandbox(
            id=sandbox_id,
            e2b_id="test-sb",
            status=SandboxStatus.RUNNING
        )

        mock_sb = MagicMock()
        mock_sb.commands = MagicMock()
        mock_sb.commands.run.return_value = Mock(stdout="", exit_code=0)  # ls returns empty

        async def mock_execute(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = sandbox
            return mock_result

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch('backend.services.sandbox_service.E2BSandbox') as MockE2B:
            MockE2B.connect.return_value = mock_sb

            with patch.dict('os.environ', {'E2B_API_KEY': 'test-key', 'GITHUB_TOKEN': 'gh-token'}):
                service = SandboxService(db)

                with pytest.raises(RuntimeError, match="No repositories found"):
                    await service.create_branch(sandbox_id, "feature-123")
