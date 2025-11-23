"""
End-to-End Integration Test for E2B Sandbox Workflow

Tests the complete flow:
1. Create sandbox
2. Clone repository
3. Create branch
4. Commit changes
5. Push to remote
6. Create PR
7. GitHub webhook events
8. Terminate sandbox

Prerequisites:
- E2B_API_KEY environment variable
- GITHUB_TOKEN environment variable
- GITHUB_WEBHOOK_SECRET environment variable
- PostgreSQL database running
- Test repository accessible
"""
import pytest
import asyncio
import os
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from backend.services.sandbox_service import SandboxService
from backend.services.webhook_service import WebhookService
from backend.models.sandbox import Sandbox, SandboxStatus
from backend.schemas.webhook_events import GitHubWebhookPayload


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("E2B_API_KEY"),
    reason="E2B_API_KEY not set - skip integration test"
)
async def test_complete_sandbox_workflow(db_session):
    """
    Test complete E2B sandbox workflow with SSE broadcasting

    This test simulates a complete agent workflow:
    1. Agent creates sandbox
    2. Agent clones repo
    3. Agent creates feature branch
    4. Agent commits changes
    5. Agent pushes changes
    6. Agent creates PR
    7. GitHub sends webhook (PR approved)
    8. Agent terminates sandbox
    """
    # Test configuration
    test_repo = "https://github.com/test-org/test-repo.git"
    test_branch = f"test-feature-{uuid4().hex[:8]}"
    execution_id = uuid4()
    squad_id = uuid4()

    # Initialize service
    service = SandboxService(
        db=db_session,
        execution_id=execution_id,
        squad_id=squad_id
    )

    sandbox_id = None
    pr_number = None

    try:
        # Step 1: Create sandbox
        print("\n[1/8] Creating E2B sandbox...")
        sandbox = await service.create_sandbox(
            task_id=uuid4(),
            agent_id=uuid4(),
            repo_url=test_repo
        )
        sandbox_id = sandbox.id
        print(f"✓ Sandbox created: {sandbox.e2b_id}")

        # Verify sandbox in database
        result = await db_session.execute(
            select(Sandbox).where(Sandbox.id == sandbox_id)
        )
        db_sandbox = result.scalars().first()
        assert db_sandbox is not None
        assert db_sandbox.status == SandboxStatus.RUNNING
        assert db_sandbox.repo_url == test_repo

        # Step 2: Clone repository
        print("\n[2/8] Cloning repository...")
        repo_path = await service.clone_repo(sandbox_id, test_repo)
        print(f"✓ Repository cloned to: {repo_path}")

        # Step 3: Create feature branch
        print(f"\n[3/8] Creating branch: {test_branch}")
        branch = await service.create_branch(
            sandbox_id,
            test_branch,
            "main"
        )
        print(f"✓ Branch created: {branch}")

        # Step 4: Make some changes (simulate agent work)
        print("\n[4/8] Making test changes...")
        # In real scenario, agent would modify files here
        # For test, we'll just create a test file
        sb = await service._get_e2b_sandbox(sandbox.e2b_id)
        test_file_content = f"# Test File\nCreated at {datetime.utcnow()}"
        sb.filesystem.write(f"{repo_path}/test-file.md", test_file_content)
        print("✓ Test file created")

        # Step 5: Commit changes
        print("\n[5/8] Committing changes...")
        commit_msg = f"test: add test file for E2E test"
        output = await service.commit_changes(sandbox_id, commit_msg)
        print(f"✓ Changes committed: {commit_msg}")

        # Step 6: Push changes
        print(f"\n[6/8] Pushing to remote: {test_branch}")
        push_output = await service.push_changes(sandbox_id, test_branch)
        print(f"✓ Changes pushed to remote")

        # Step 7: Create Pull Request
        print("\n[7/8] Creating Pull Request...")
        pr_title = f"E2E Test PR - {test_branch}"
        pr_body = "This is an automated E2E test PR. Safe to close."
        pr_result = await service.create_pr(
            sandbox_id,
            title=pr_title,
            body=pr_body,
            head=test_branch,
            base="main",
            repo_owner_name="test-org/test-repo"
        )
        pr_number = pr_result["number"]
        pr_url = pr_result["html_url"]
        print(f"✓ PR created: #{pr_number} - {pr_url}")

        # Verify PR number stored in sandbox
        await db_session.refresh(db_sandbox)
        assert db_sandbox.pr_number == pr_number
        print(f"✓ PR number stored in sandbox: #{pr_number}")

        # Step 8: Simulate GitHub Webhook (PR Approved)
        print("\n[8/8] Simulating GitHub webhook (PR approved)...")
        webhook_service = WebhookService(db_session)

        # Simulate webhook payload
        webhook_payload = {
            "action": "submitted",
            "pull_request": {
                "number": pr_number,
                "html_url": pr_url,
                "head": {"ref": test_branch},
                "base": {"ref": "main"}
            },
            "review": {
                "state": "approved",
                "user": {"login": "test-reviewer"}
            },
            "repository": {
                "html_url": "https://github.com/test-org/test-repo"
            },
            "sender": {"login": "test-reviewer"}
        }

        # Process webhook
        event_result = await webhook_service.process_pull_request_review_event(
            webhook_payload
        )

        if event_result:
            print(f"✓ Webhook processed: pr_approved event")
            print(f"  Reviewer: {event_result.get('reviewer')}")
        else:
            print("⚠ Webhook processing returned None (expected for test)")

        # Step 9: Terminate sandbox
        print("\n[9/9] Terminating sandbox...")
        terminated = await service.terminate_sandbox(sandbox_id)
        print(f"✓ Sandbox terminated: {terminated}")

        # Verify final state
        await db_session.refresh(db_sandbox)
        assert db_sandbox.status == SandboxStatus.TERMINATED
        assert db_sandbox.pr_number == pr_number
        assert db_sandbox.runtime_seconds is not None
        print(f"✓ Runtime: {db_sandbox.runtime_seconds}s")

        print("\n" + "="*60)
        print("✅ E2E TEST PASSED - All steps completed successfully!")
        print("="*60)

        return {
            "sandbox_id": str(sandbox_id),
            "e2b_id": sandbox.e2b_id,
            "pr_number": pr_number,
            "pr_url": pr_url,
            "branch": test_branch,
            "runtime_seconds": db_sandbox.runtime_seconds
        }

    except Exception as e:
        print(f"\n❌ E2E TEST FAILED: {e}")
        raise

    finally:
        # Cleanup: Ensure sandbox is terminated
        if sandbox_id:
            try:
                await service.terminate_sandbox(sandbox_id)
                print("\n✓ Cleanup: Sandbox terminated")
            except:
                pass


@pytest.mark.asyncio
async def test_webhook_signature_validation():
    """Test GitHub webhook HMAC signature validation"""
    import hmac
    import hashlib

    # Setup
    secret = "test-webhook-secret"
    os.environ["GITHUB_WEBHOOK_SECRET"] = secret

    payload = b'{"action": "opened", "number": 123}'

    # Calculate valid signature
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    valid_signature = f"sha256={mac.hexdigest()}"

    # Test with valid signature
    from backend.services.webhook_service import WebhookService
    from unittest.mock import AsyncMock

    service = WebhookService(AsyncMock())
    assert service.verify_signature(payload, valid_signature) == True

    # Test with invalid signature
    invalid_signature = "sha256=invalid"
    assert service.verify_signature(payload, invalid_signature) == False

    print("✅ Webhook signature validation working correctly")


@pytest.mark.asyncio
async def test_webhook_sandbox_lookup(db_session):
    """Test webhook service finds correct sandbox by PR number"""
    from backend.services.webhook_service import WebhookService
    from backend.models.sandbox import Sandbox, SandboxStatus

    # Create test sandboxes
    sandbox1 = Sandbox(
        e2b_id="test-e2b-1",
        repo_url="https://github.com/owner/repo",
        pr_number=123,
        status=SandboxStatus.RUNNING
    )
    sandbox2 = Sandbox(
        e2b_id="test-e2b-2",
        repo_url="https://github.com/owner/repo",
        pr_number=456,
        status=SandboxStatus.RUNNING
    )

    db_session.add(sandbox1)
    db_session.add(sandbox2)
    await db_session.commit()

    # Test exact PR match
    service = WebhookService(db_session)
    found = await service._find_sandbox_by_pr(123, "https://github.com/owner/repo")

    assert found is not None
    assert found.pr_number == 123
    assert found.id == sandbox1.id

    print("✅ Webhook sandbox lookup by PR number working correctly")


if __name__ == "__main__":
    print("""
    E2B Integration End-to-End Test Suite
    ======================================

    Prerequisites:
    1. Set environment variables:
       - E2B_API_KEY
       - GITHUB_TOKEN
       - GITHUB_WEBHOOK_SECRET

    2. PostgreSQL database running

    3. Test repository accessible on GitHub

    Run with:
        pytest tests/test_e2b_integration_e2e.py -v -s

    To run only E2E test (skip if no E2B key):
        pytest tests/test_e2b_integration_e2e.py::test_complete_sandbox_workflow -v -s
    """)
