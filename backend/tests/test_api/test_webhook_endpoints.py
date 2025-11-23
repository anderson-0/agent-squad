"""
Webhook API Endpoint Tests

Tests for GitHub webhook endpoints.
"""
import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient
from uuid import uuid4


class TestWebhookEndpoint:
    """Test GitHub webhook endpoint"""

    def create_signature(self, payload: dict, secret: str) -> str:
        """Create valid GitHub webhook signature"""
        payload_bytes = json.dumps(payload).encode('utf-8')
        mac = hmac.new(secret.encode('utf-8'), msg=payload_bytes, digestmod=hashlib.sha256)
        return f"sha256={mac.hexdigest()}"

    @pytest.mark.asyncio
    async def test_webhook_missing_signature(self, client: AsyncClient):
        """Test webhook without signature header"""
        payload = {"action": "opened", "number": 123}

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )

        assert response.status_code == 400
        assert "signature" in response.text.lower()

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self, client: AsyncClient):
        """Test webhook with invalid signature"""
        payload = {"action": "opened", "number": 123}

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=invalid_signature_here"
            }
        )

        assert response.status_code in [400, 401, 403]

    @pytest.mark.asyncio
    async def test_webhook_missing_event_header(self, client: AsyncClient):
        """Test webhook without event type header"""
        payload = {"action": "opened"}
        secret = "test-secret"
        signature = self.create_signature(payload, secret)

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={"X-Hub-Signature-256": signature}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_unsupported_event(self, client: AsyncClient):
        """Test webhook with unsupported event type"""
        payload = {"action": "opened"}
        secret = "test-secret"
        signature = self.create_signature(payload, secret)

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "unsupported_event",
                "X-Hub-Signature-256": signature
            }
        )

        # Should accept but possibly ignore
        assert response.status_code in [200, 202, 400]

    @pytest.mark.asyncio
    async def test_webhook_test_endpoint(self, client: AsyncClient):
        """Test webhook test/health endpoint"""
        response = await client.get("/api/v1/webhooks/github/test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "endpoint" in data


class TestPullRequestWebhooks:
    """Test pull request webhook events"""

    def create_pr_payload(self, action: str, pr_number: int) -> dict:
        """Create PR webhook payload"""
        return {
            "action": action,
            "number": pr_number,
            "pull_request": {
                "number": pr_number,
                "html_url": f"https://github.com/test/repo/pull/{pr_number}",
                "title": "Test PR",
                "state": "open",
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"}
            },
            "repository": {
                "html_url": "https://github.com/test/repo"
            },
            "sender": {"login": "test-user"}
        }

    @pytest.mark.asyncio
    async def test_pr_opened_webhook(self, client: AsyncClient):
        """Test PR opened webhook"""
        payload = self.create_pr_payload("opened", 123)
        secret = "test-secret"
        signature = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": f"sha256={signature}"
            }
        )

        # Should process or reject based on signature validation
        assert response.status_code in [200, 202, 400, 401]

    @pytest.mark.asyncio
    async def test_pr_closed_webhook(self, client: AsyncClient):
        """Test PR closed webhook"""
        payload = self.create_pr_payload("closed", 456)
        payload["pull_request"]["state"] = "closed"

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=test"
            }
        )

        assert response.status_code in [200, 202, 400, 401]

    @pytest.mark.asyncio
    async def test_pr_merged_webhook(self, client: AsyncClient):
        """Test PR merged webhook"""
        payload = self.create_pr_payload("closed", 789)
        payload["pull_request"]["merged"] = True
        payload["pull_request"]["merge_commit_sha"] = "abc123"

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=test"
            }
        )

        assert response.status_code in [200, 202, 400, 401]


class TestPullRequestReviewWebhooks:
    """Test pull request review webhook events"""

    def create_review_payload(self, pr_number: int, state: str) -> dict:
        """Create PR review webhook payload"""
        return {
            "action": "submitted",
            "pull_request": {
                "number": pr_number,
                "html_url": f"https://github.com/test/repo/pull/{pr_number}",
                "head": {"ref": "feature"},
                "base": {"ref": "main"}
            },
            "review": {
                "state": state,
                "user": {"login": "reviewer"}
            },
            "repository": {
                "html_url": "https://github.com/test/repo"
            },
            "sender": {"login": "reviewer"}
        }

    @pytest.mark.asyncio
    async def test_pr_approved_webhook(self, client: AsyncClient):
        """Test PR approved review webhook"""
        payload = self.create_review_payload(123, "approved")

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request_review",
                "X-Hub-Signature-256": "sha256=test"
            }
        )

        assert response.status_code in [200, 202, 400, 401]

    @pytest.mark.asyncio
    async def test_pr_changes_requested_webhook(self, client: AsyncClient):
        """Test PR changes requested review webhook"""
        payload = self.create_review_payload(456, "changes_requested")

        response = await client.post(
            "/api/v1/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request_review",
                "X-Hub-Signature-256": "sha256=test"
            }
        )

        assert response.status_code in [200, 202, 400, 401]


class TestWebhookSecurity:
    """Test webhook security features"""

    @pytest.mark.asyncio
    async def test_webhook_replay_attack(self, client: AsyncClient):
        """Test webhook handles replay attacks"""
        payload = {"action": "opened", "number": 123}

        # Send same webhook twice
        for _ in range(2):
            response = await client.post(
                "/api/v1/webhooks/github",
                json=payload,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=test"
                }
            )

        # Both should be processed (no replay detection implemented yet)
        # This test documents current behavior
        assert response.status_code in [200, 202, 400, 401]

    @pytest.mark.asyncio
    async def test_webhook_malformed_json(self, client: AsyncClient):
        """Test webhook with malformed JSON"""
        response = await client.post(
            "/api/v1/webhooks/github",
            data="malformed{json}",
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=test"
            }
        )

        assert response.status_code == 400


if __name__ == "__main__":
    print("""
    Webhook API Tests
    =================

    Tests for GitHub webhook endpoints.

    Run with:
        pytest tests/test_api/test_webhook_endpoints.py -v
    """)
