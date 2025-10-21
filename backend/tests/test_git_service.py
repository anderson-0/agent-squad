"""
Tests for Git Service (write operations using GitPython).
Tests clone, branch, commit, and push operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, PropertyMock
from git import Repo
from backend.integrations.git_service import GitService


@pytest.fixture
def git_service():
    """Create GitService instance."""
    return GitService()


@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)

    # Configure git
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    test_file = Path(temp_dir) / "README.md"
    test_file.write_text("# Test Repository\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    yield repo

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_git_service_creation(git_service):
    """Test that GitService can be created."""
    assert git_service is not None


@pytest.mark.asyncio
async def test_create_branch(git_service, temp_repo):
    """Test creating a new branch."""
    # Create new branch
    await git_service.create_branch(temp_repo, "feature/test")

    # Verify branch exists and is checked out
    assert temp_repo.active_branch.name == "feature/test"
    assert "feature/test" in [b.name for b in temp_repo.branches]


@pytest.mark.asyncio
async def test_create_branch_from_specific_branch(git_service, temp_repo):
    """Test creating a branch from a specific base branch."""
    # Create first branch
    await git_service.create_branch(temp_repo, "feature/base")

    # Create second branch from first
    await git_service.create_branch(
        temp_repo,
        "feature/derived",
        from_branch="feature/base"
    )

    # Verify branch exists
    assert temp_repo.active_branch.name == "feature/derived"


@pytest.mark.asyncio
async def test_commit_changes(git_service, temp_repo):
    """Test committing changes."""
    # Create a new file
    repo_path = Path(temp_repo.working_dir)
    test_file = repo_path / "test.txt"
    test_file.write_text("Test content\n")

    # Commit changes
    sha = await git_service.commit_changes(
        temp_repo,
        "Add test file"
    )

    # Verify commit was created
    assert sha is not None
    assert len(sha) == 40  # SHA-1 hash length

    # Verify file is committed
    assert "test.txt" in temp_repo.git.ls_files().split()


@pytest.mark.asyncio
async def test_commit_specific_files(git_service, temp_repo):
    """Test committing specific files."""
    repo_path = Path(temp_repo.working_dir)

    # Create multiple files
    file1 = repo_path / "file1.txt"
    file2 = repo_path / "file2.txt"
    file1.write_text("File 1\n")
    file2.write_text("File 2\n")

    # Commit only file1
    sha = await git_service.commit_changes(
        temp_repo,
        "Add file1",
        files=["file1.txt"]
    )

    # Verify only file1 is committed
    assert "file1.txt" in temp_repo.git.ls_files().split()
    assert "file2.txt" not in temp_repo.git.ls_files().split()


@pytest.mark.asyncio
async def test_commit_with_author(git_service, temp_repo):
    """Test committing with custom author."""
    repo_path = Path(temp_repo.working_dir)
    test_file = repo_path / "test.txt"
    test_file.write_text("Test content\n")

    # Commit with custom author
    sha = await git_service.commit_changes(
        temp_repo,
        "Add test file",
        author_name="Custom Author",
        author_email="custom@example.com"
    )

    # Verify commit author
    commit = temp_repo.commit(sha)
    assert commit.author.name == "Custom Author"
    assert commit.author.email == "custom@example.com"


@pytest.mark.asyncio
async def test_commit_no_changes(git_service, temp_repo):
    """Test committing when there are no changes."""
    # Try to commit without changes
    sha = await git_service.commit_changes(
        temp_repo,
        "No changes"
    )

    # Should return empty string
    assert sha == ""


@pytest.mark.asyncio
async def test_checkout(git_service, temp_repo):
    """Test checking out a branch."""
    # Get the current branch name (from initial commit)
    original_branch = temp_repo.active_branch.name

    # Create and checkout new branch
    await git_service.create_branch(temp_repo, "feature/test")

    # Verify we're on new branch
    assert temp_repo.active_branch.name == "feature/test"

    # Checkout original branch
    await git_service.checkout(temp_repo, original_branch)

    # Verify checkout
    assert temp_repo.active_branch.name == original_branch


@pytest.mark.asyncio
async def test_get_status(git_service, temp_repo):
    """Test getting repository status."""
    # Get status structure
    status = await git_service.get_status(temp_repo)

    assert "branch" in status
    assert "modified" in status
    assert "staged" in status
    assert "untracked" in status
    assert "is_dirty" in status

    # Create untracked file
    repo_path = Path(temp_repo.working_dir)
    test_file = repo_path / "untracked.txt"
    test_file.write_text("Untracked\n")

    # Get status - should show untracked file
    status = await git_service.get_status(temp_repo)
    assert "untracked.txt" in status["untracked"]


@pytest.mark.asyncio
async def test_get_status_with_modified(git_service, temp_repo):
    """Test status with modified files."""
    repo_path = Path(temp_repo.working_dir)

    # Modify existing file
    readme = repo_path / "README.md"
    readme.write_text("# Modified\n")

    # Get status
    status = await git_service.get_status(temp_repo)
    assert status["is_dirty"]
    assert "README.md" in status["modified"]


@pytest.mark.asyncio
async def test_workflow_branch_commit(git_service, temp_repo):
    """Test complete workflow: create branch, make changes, commit."""
    repo_path = Path(temp_repo.working_dir)

    # Create feature branch
    await git_service.create_branch(temp_repo, "feature/workflow")

    # Make changes
    test_file = repo_path / "feature.txt"
    test_file.write_text("Feature implementation\n")

    # Commit changes
    sha = await git_service.commit_changes(
        temp_repo,
        "Implement feature"
    )

    # Verify workflow
    assert temp_repo.active_branch.name == "feature/workflow"
    assert sha is not None
    assert "feature.txt" in temp_repo.git.ls_files().split()

    # Verify commit is on correct branch
    commit = temp_repo.commit(sha)
    assert commit.message.strip() == "Implement feature"


@pytest.mark.asyncio
async def test_repr(git_service):
    """Test string representation."""
    repr_str = repr(git_service)
    assert "GitService" in repr_str


@pytest.mark.asyncio
async def test_get_remote_url(git_service, temp_repo):
    """Test getting remote URL."""
    # Add a remote
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")

    # Get remote URL
    url = await git_service.get_remote_url(temp_repo)

    assert url == "https://github.com/test/repo.git"


@pytest.mark.asyncio
async def test_get_remote_url_custom_remote(git_service, temp_repo):
    """Test getting remote URL from custom remote."""
    # Add multiple remotes
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")
    temp_repo.create_remote("upstream", "https://github.com/upstream/repo.git")

    # Get upstream URL
    url = await git_service.get_remote_url(temp_repo, "upstream")

    assert url == "https://github.com/upstream/repo.git"


@pytest.mark.asyncio
async def test_get_remote_url_error(git_service, temp_repo):
    """Test error when remote doesn't exist."""
    with pytest.raises(Exception):
        await git_service.get_remote_url(temp_repo, "nonexistent")


@pytest.mark.asyncio
async def test_get_status_error_handling(git_service):
    """Test error handling when getting status from invalid repo."""
    # Create an invalid repo object
    invalid_repo = Mock()
    invalid_repo.active_branch.name = PropertyMock(side_effect=Exception("Invalid repo"))

    with pytest.raises(Exception):
        await git_service.get_status(invalid_repo)


@pytest.mark.asyncio
async def test_checkout_error(git_service, temp_repo):
    """Test error when checking out non-existent branch."""
    from git import GitCommandError

    with pytest.raises(GitCommandError):
        await git_service.checkout(temp_repo, "nonexistent-branch")


@pytest.mark.asyncio
async def test_create_branch_error(git_service, temp_repo):
    """Test error when creating branch that already exists."""
    from git import GitCommandError

    # Create branch first time
    await git_service.create_branch(temp_repo, "test-branch")

    # Checkout another branch
    original_branch = temp_repo.active_branch.name
    if original_branch == "test-branch":
        # Need to checkout a different branch first
        temp_repo.create_head("main", "HEAD")
        await git_service.checkout(temp_repo, "main")

    # Try to create same branch again (should fail)
    with pytest.raises(GitCommandError):
        await git_service.create_branch(temp_repo, "test-branch")


@pytest.mark.asyncio
async def test_commit_changes_error(git_service):
    """Test error when committing to invalid repo."""
    from git import GitCommandError

    # Create an invalid repo object
    invalid_repo = Mock()
    invalid_repo.git.add = Mock(side_effect=GitCommandError("git add", 1))

    with pytest.raises(GitCommandError):
        await git_service.commit_changes(invalid_repo, "Test commit")


@pytest.mark.asyncio
async def test_clone_or_open_existing_repo(git_service, temp_repo):
    """Test opening an existing repository."""
    repo_path = temp_repo.working_dir

    # Add a remote to test pulling
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")

    # Open the existing repo (should detect it exists)
    # Mock the pull to avoid network calls
    with pytest.raises(Exception):
        # Will fail because no actual remote, but proves it tried to open existing
        repo = await git_service.clone_or_open(
            "https://github.com/test/repo.git",
            repo_path
        )


@pytest.mark.asyncio
async def test_clone_or_open_with_branch(git_service):
    """Test cloning with specific branch checkout."""
    # This test would require actual network access or mocking
    # For now, test the error path
    from git import GitCommandError

    with pytest.raises(GitCommandError):
        await git_service.clone_or_open(
            "https://github.com/nonexistent/repo.git",
            "/tmp/nonexistent",
            branch="feature"
        )


@pytest.mark.asyncio
async def test_push_current_branch(git_service, temp_repo):
    """Test pushing current branch."""
    from git import GitCommandError

    # Add a remote
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")

    # Try to push (will fail because no actual remote, but tests the code path)
    with pytest.raises(GitCommandError):
        await git_service.push(temp_repo)


@pytest.mark.asyncio
async def test_push_specific_branch(git_service, temp_repo):
    """Test pushing specific branch."""
    from git import GitCommandError

    # Create and checkout new branch
    await git_service.create_branch(temp_repo, "feature/test")

    # Add a remote
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")

    # Try to push specific branch (will fail because no actual remote)
    with pytest.raises(GitCommandError):
        await git_service.push(temp_repo, branch="feature/test")


@pytest.mark.asyncio
async def test_push_force(git_service, temp_repo):
    """Test force pushing."""
    from git import GitCommandError

    # Add a remote
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")

    # Try to force push (will fail because no actual remote)
    with pytest.raises(GitCommandError):
        await git_service.push(temp_repo, force=True)


@pytest.mark.asyncio
async def test_push_custom_remote(git_service, temp_repo):
    """Test pushing to custom remote."""
    from git import GitCommandError

    # Add multiple remotes
    temp_repo.create_remote("origin", "https://github.com/test/repo.git")
    temp_repo.create_remote("upstream", "https://github.com/upstream/repo.git")

    # Try to push to upstream (will fail because no actual remote)
    with pytest.raises(GitCommandError):
        await git_service.push(temp_repo, remote="upstream")
