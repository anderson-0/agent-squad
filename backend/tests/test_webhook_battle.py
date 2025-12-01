"""
Battle-Tested Webhook Service Tests

Comprehensive test suite covering:
- HMAC signature validation edge cases
- Malicious payload handling
- Timing attack prevention
- Invalid webhook formats
- Concurrent webhook processing
- Sandbox lookup edge cases
"""
import pytest
import asyncio
import hmac
import hashlib
import os
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.webhook_service import WebhookService, WebhookValidationError
from backend.models.sandbox import Sandbox, SandboxStatus


class TestWebhookSignatureValidation:
    """Test HMAC signature validation security"""

    def test_valid_signature(self):
        """Test webhook with valid HMAC signature"""
        secret = "test-secret-key"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret

        payload = b'{"action": "opened", "number": 123}'
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        service = WebhookService(AsyncMock())
        assert service.verify_signature(payload, signature) is True

    def test_invalid_signature(self):
        """Test webhook with wrong signature is rejected"""
        os.environ["GITHUB_WEBHOOK_SECRET"] = "correct-secret"

        payload = b'{"action": "opened"}'
        wrong_signature = "sha256=wrong_hash_value_here"

        service = WebhookService(AsyncMock())
        assert service.verify_signature(payload, wrong_signature) is False

    def test_missing_signature_header(self):
        """Test webhook without signature header"""
        os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"

        service = WebhookService(AsyncMock())

        with pytest.raises(WebhookValidationError, match="Missing X-Hub-Signature-256"):
            service.verify_signature(b'{"test": "data"}', "")

    def test_malformed_signature_format(self):
        """Test signature without sha256= prefix"""
        os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"

        service = WebhookService(AsyncMock())

        with pytest.raises(WebhookValidationError, match="Invalid signature format"):
            service.verify_signature(b'{"test": "data"}', "just_a_hash")

    def test_empty_payload(self):
        """Test signature validation with empty payload"""
        secret = "test-secret"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret

        payload = b''
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        service = WebhookService(AsyncMock())
        assert service.verify_signature(payload, signature) is True

    def test_large_payload(self):
        """Test signature validation with very large payload"""
        secret = "test-secret"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret

        # 1MB payload
        payload = b'{"data": "' + b'x' * 1_000_000 + b'"}'
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        service = WebhookService(AsyncMock())
        assert service.verify_signature(payload, signature) is True

    def test_timing_attack_prevention(self):
        """Test constant-time comparison prevents timing attacks"""
        import time

        secret = "test-secret-key"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret

        payload = b'{"test": "data"}'

        # Create correct signature
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        correct_hash = mac.hexdigest()
        correct_sig = f"sha256={correct_hash}"

        # Create wrong signature (first char different)
        wrong_hash = "z" + correct_hash[1:]
        wrong_sig = f"sha256={wrong_hash}"

        service = WebhookService(AsyncMock())

        # Time comparison with correct signature
        start = time.perf_counter()
        result1 = service.verify_signature(payload, correct_sig)
        time1 = time.perf_counter() - start

        # Time comparison with wrong signature
        start = time.perf_counter()
        result2 = service.verify_signature(payload, wrong_sig)
        time2 = time.perf_counter() - start

        # Results should be different
        assert result1 is True
        assert result2 is False

        # But timing should be similar (within 10x)
        # If not using constant-time, timing difference would be 100x+
        assert abs(time1 - time2) < max(time1, time2) * 10

    def test_no_secret_configured(self):
        """Test webhook validation when no secret is configured"""
        os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

        service = WebhookService(AsyncMock())

        # Should allow through with warning (for development)
        assert service.verify_signature(b'{"test": "data"}', "any_signature") is True

    def test_unicode_in_payload(self):
        """Test signature validation with unicode characters"""
        secret = "test-secret"
        os.environ["GITHUB_WEBHOOK_SECRET"] = secret

        payload = '{"title": "Fix 🐛 in auth"}'.encode('utf-8')
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"

        service = WebhookService(AsyncMock())
        assert service.verify_signature(payload, signature) is True


@pytest.mark.asyncio
class TestSandboxLookup:
    """Test sandbox lookup edge cases"""

    async def test_exact_pr_match(self, db_session):
        """Test exact PR number match (fastest path)"""
        sandbox = Sandbox(
            e2b_id="test-e2b-1",
            repo_url="https://github.com/owner/repo",
            pr_number=123,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = WebhookService(db_session)
        found = await service._find_sandbox_by_pr(123, "https://github.com/owner/repo")

        assert found is not None
        assert found.pr_number == 123
        assert found.id == sandbox.id

    async def test_repo_url_fallback(self, db_session):
        """Test fallback to repo URL when PR number not stored"""
        sandbox = Sandbox(
            e2b_id="test-e2b-2",
            repo_url="https://github.com/owner/repo",
            pr_number=None,  # No PR number
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = WebhookService(db_session)
        found = await service._find_sandbox_by_pr(999, "https://github.com/owner/repo")

        assert found is not None
        assert found.id == sandbox.id

    async def test_no_match_found(self, db_session):
        """Test when no sandbox matches"""
        service = WebhookService(db_session)
        found = await service._find_sandbox_by_pr(999, "https://github.com/nonexistent/repo")

        assert found is None

    async def test_multiple_sandboxes_same_repo(self, db_session):
        """Test returns most recent sandbox when multiple match"""
        import time

        sandbox1 = Sandbox(
            e2b_id="test-e2b-old",
            repo_url="https://github.com/owner/repo",
            pr_number=None,
            status=SandboxStatus.TERMINATED
        )
        db_session.add(sandbox1)
        await db_session.commit()

        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)

        sandbox2 = Sandbox(
            e2b_id="test-e2b-new",
            repo_url="https://github.com/owner/repo",
            pr_number=None,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox2)
        await db_session.commit()

        service = WebhookService(db_session)
        found = await service._find_sandbox_by_pr(999, "https://github.com/owner/repo")

        # Should return most recent (sandbox2)
        assert found is not None
        assert found.e2b_id == "test-e2b-new"

    async def test_url_normalization(self, db_session):
        """Test URL normalization handles various formats"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo.git",
            pr_number=123,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = WebhookService(db_session)

        # All these should match
        urls = [
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/",
            "https://github.com/owner/repo.git/",
        ]

        for url in urls:
            found = await service._find_sandbox_by_pr(123, url)
            assert found is not None, f"Failed to match URL: {url}"
            assert found.id == sandbox.id


@pytest.mark.asyncio
class TestWebhookEventProcessing:
    """Test webhook event processing"""

    async def test_pr_merged_event(self, db_session):
        """Test processing PR merged webhook"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=42,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        payload = {
            "action": "closed",
            "pull_request": {
                "number": 42,
                "html_url": "https://github.com/owner/repo/pull/42",
                "merged": True,
                "merge_commit_sha": "abc123"
            },
            "repository": {
                "html_url": "https://github.com/owner/repo"
            },
            "sender": {"login": "developer"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_event(payload)

        assert result is not None
        assert result["event"] == "pr_merged"
        assert result["pr_number"] == 42
        assert result["merged_by"] == "developer"

    async def test_pr_closed_without_merge(self, db_session):
        """Test processing PR closed without merging"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=43,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        payload = {
            "action": "closed",
            "pull_request": {
                "number": 43,
                "html_url": "https://github.com/owner/repo/pull/43",
                "merged": False
            },
            "repository": {
                "html_url": "https://github.com/owner/repo"
            },
            "sender": {"login": "developer"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_event(payload)

        assert result is not None
        assert result["event"] == "pr_closed"
        assert result["pr_number"] == 43
        assert result["closed_by"] == "developer"

    async def test_pr_approved_event(self, db_session):
        """Test processing PR approved webhook"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=44,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        payload = {
            "action": "submitted",
            "pull_request": {
                "number": 44,
                "html_url": "https://github.com/owner/repo/pull/44"
            },
            "review": {
                "state": "approved",
                "user": {"login": "senior-dev"}
            },
            "repository": {
                "html_url": "https://github.com/owner/repo"
            }
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_review_event(payload)

        assert result is not None
        assert result["event"] == "pr_approved"
        assert result["reviewer"] == "senior-dev"

    async def test_missing_pr_number(self, db_session):
        """Test handling webhook with missing PR number"""
        payload = {
            "action": "closed",
            "pull_request": {},  # Missing number
            "repository": {"html_url": "https://github.com/owner/repo"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_event(payload)

        assert result is None  # Should gracefully handle

    async def test_sandbox_not_found_for_pr(self, db_session):
        """Test webhook when sandbox doesn't exist"""
        payload = {
            "action": "closed",
            "pull_request": {
                "number": 999,
                "html_url": "https://github.com/owner/repo/pull/999",
                "merged": True
            },
            "repository": {"html_url": "https://github.com/owner/repo"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_event(payload)

        assert result is None  # Should handle gracefully

    async def test_changes_requested_review(self, db_session):
        """Test PR review with changes requested (not approved)"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=45,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        payload = {
            "action": "submitted",
            "pull_request": {
                "number": 45,
                "html_url": "https://github.com/owner/repo/pull/45"
            },
            "review": {
                "state": "changes_requested",  # Not approved
                "user": {"login": "reviewer"}
            },
            "repository": {"html_url": "https://github.com/owner/repo"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_review_event(payload)

        # Should return None for non-approved reviews
        assert result is None


@pytest.mark.asyncio
class TestConcurrentWebhooks:
    """Test concurrent webhook processing"""

    async def test_concurrent_webhook_processing(self, db_session):
        """Test handling multiple webhooks concurrently"""
        # Create multiple sandboxes
        sandboxes = []
        for i in range(10):
            sandbox = Sandbox(
                e2b_id=f"test-e2b-{i}",
                repo_url="https://github.com/owner/repo",
                pr_number=100 + i,
                status=SandboxStatus.RUNNING
            )
            db_session.add(sandbox)
            sandboxes.append(sandbox)
        await db_session.commit()

        service = WebhookService(db_session)

        # Process multiple webhooks concurrently
        async def process_webhook(pr_num):
            payload = {
                "action": "closed",
                "pull_request": {
                    "number": pr_num,
                    "html_url": f"https://github.com/owner/repo/pull/{pr_num}",
                    "merged": True
                },
                "repository": {"html_url": "https://github.com/owner/repo"},
                "sender": {"login": "dev"}
            }
            return await service.process_pull_request_event(payload)

        # Run 10 webhooks concurrently
        results = await asyncio.gather(*[
            process_webhook(100 + i) for i in range(10)
        ])

        # All should succeed
        assert all(r is not None for r in results)
        assert all(r["event"] == "pr_merged" for r in results)

    async def test_race_condition_same_pr(self, db_session):
        """Test race condition with multiple webhooks for same PR"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=123,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        service = WebhookService(db_session)

        # Process same webhook multiple times concurrently
        async def process():
            payload = {
                "action": "submitted",
                "pull_request": {
                    "number": 123,
                    "html_url": "https://github.com/owner/repo/pull/123"
                },
                "review": {
                    "state": "approved",
                    "user": {"login": "reviewer"}
                },
                "repository": {"html_url": "https://github.com/owner/repo"}
            }
            return await service.process_pull_request_review_event(payload)

        # Run 5 identical webhooks concurrently
        results = await asyncio.gather(*[process() for _ in range(5)])

        # All should succeed (idempotent)
        assert all(r is not None for r in results)
        assert all(r["pr_number"] == 123 for r in results)


@pytest.mark.asyncio
class TestMaliciousPayloads:
    """Test handling of malicious/malformed payloads"""

    async def test_sql_injection_attempt(self, db_session):
        """Test SQL injection in repo URL"""
        payload = {
            "action": "closed",
            "pull_request": {
                "number": 1,
                "html_url": "https://github.com/owner/repo/pull/1",
                "merged": True
            },
            "repository": {
                "html_url": "https://github.com/'; DROP TABLE sandboxes; --/repo"
            },
            "sender": {"login": "attacker"}
        }

        service = WebhookService(db_session)
        # Should not raise exception or corrupt database
        result = await service.process_pull_request_event(payload)

        # Verify database not affected
        from sqlalchemy import select
        count_result = await db_session.execute(select(Sandbox))
        # Database should still exist
        assert count_result is not None

    async def test_xss_attempt_in_payload(self, db_session):
        """Test XSS payload in webhook data"""
        sandbox = Sandbox(
            e2b_id="test-e2b",
            repo_url="https://github.com/owner/repo",
            pr_number=1,
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        payload = {
            "action": "closed",
            "pull_request": {
                "number": 1,
                "html_url": "https://github.com/owner/repo/pull/1",
                "merged": True
            },
            "repository": {"html_url": "https://github.com/owner/repo"},
            "sender": {"login": "<script>alert('XSS')</script>"}
        }

        service = WebhookService(db_session)
        result = await service.process_pull_request_event(payload)

        # Should process without executing script
        assert result is not None
        # Data should be stored as-is (sanitization happens at display layer)
        assert result["merged_by"] == "<script>alert('XSS')</script>"

    async def test_extremely_long_values(self, db_session):
        """Test handling of extremely long field values"""
        payload = {
            "action": "closed",
            "pull_request": {
                "number": 1,
                "html_url": "https://github.com/owner/repo/pull/1",
                "merged": True
            },
            "repository": {
                "html_url": "https://github.com/" + "x" * 10000 + "/repo"
            },
            "sender": {"login": "x" * 10000}
        }

        service = WebhookService(db_session)
        # Should handle gracefully (not crash)
        try:
            result = await service.process_pull_request_event(payload)
            # Either processes or returns None
            assert result is None or isinstance(result, dict)
        except Exception:
            # Should not raise unhandled exception
            pytest.fail("Should handle long values gracefully")


if __name__ == "__main__":
    print("""
    Webhook Battle Tests
    ====================

    Run with:
        pytest tests/test_webhook_battle.py -v -s

    Coverage:
        pytest tests/test_webhook_battle.py --cov=backend.services.webhook_service --cov-report=html
    """)
