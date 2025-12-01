"""
GitHub Webhook Service

Handles GitHub webhook verification and event processing with SSE broadcasting.
"""
import hmac
import hashlib
import os
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.sandbox import Sandbox
from backend.schemas.webhook_events import (
    PRApprovedEvent,
    PRMergedEvent,
    PRClosedEvent,
    PRReopenedEvent,
    WebhookValidationError,
)

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for processing GitHub webhooks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify GitHub webhook signature using HMAC-SHA256

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value (format: "sha256=...")

        Returns:
            True if signature is valid, False otherwise

        Raises:
            WebhookValidationError: If signature format is invalid
        """
        if not self.webhook_secret:
            logger.warning("GITHUB_WEBHOOK_SECRET not set - skipping signature verification")
            return True  # Allow in development, but warn

        if not signature:
            raise WebhookValidationError("Missing X-Hub-Signature-256 header")

        # GitHub sends signature as "sha256=<hash>"
        if not signature.startswith("sha256="):
            raise WebhookValidationError("Invalid signature format (expected sha256=...)")

        # Extract hash part
        expected_hash = signature[7:]  # Remove "sha256=" prefix

        # Calculate HMAC-SHA256
        mac = hmac.new(
            self.webhook_secret.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        )
        calculated_hash = mac.hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(calculated_hash, expected_hash)

    async def _find_sandbox_by_pr(self, pr_number: int, repo_url: str) -> Optional[Sandbox]:
        """
        Find sandbox by PR number and repository URL

        Args:
            pr_number: GitHub PR number
            repo_url: Repository URL (e.g., "https://github.com/owner/repo")

        Returns:
            Sandbox if found, None otherwise
        """
        # Normalize repo URL (remove .git, trailing slash, etc.)
        normalized_url = repo_url.rstrip('/').rstrip('.git')

        # First try: Exact match by PR number (fastest, most accurate)
        result = await self.db.execute(
            select(Sandbox).where(Sandbox.pr_number == pr_number)
        )
        sandbox = result.scalars().first()
        if sandbox:
            logger.info(f"Found sandbox {sandbox.id} by exact PR match #{pr_number}")
            return sandbox

        # Fallback: Match by repo URL (less accurate, for backward compatibility)
        result = await self.db.execute(
            select(Sandbox).where(Sandbox.repo_url.like(f"%{normalized_url}%"))
            .order_by(Sandbox.created_at.desc())  # Most recent first
        )
        sandbox = result.scalars().first()
        if sandbox:
            logger.warning(
                f"Found sandbox {sandbox.id} by repo URL (no PR number stored). "
                f"Consider updating sandbox to store PR number."
            )
            return sandbox

        return None

    async def _broadcast_event(self, event: Dict[str, Any], sandbox: Sandbox):
        """
        Broadcast webhook event via SSE

        Events are sent to both execution and squad channels if available.
        """
        try:
            from backend.services.sse_service import sse_manager
            from backend.models.task import Task
            from backend.models.agent import Agent

            # Get execution_id from task if available
            if sandbox.task_id:
                result = await self.db.execute(
                    select(Task).where(Task.id == sandbox.task_id)
                )
                task = result.scalars().first()
                if task and task.execution_id:
                    await sse_manager.broadcast_to_execution(
                        task.execution_id,
                        event['event'],
                        event
                    )
                    logger.info(f"Broadcasted {event['event']} to execution {task.execution_id}")

            # Get squad_id from agent if available
            if sandbox.agent_id:
                result = await self.db.execute(
                    select(Agent).where(Agent.id == sandbox.agent_id)
                )
                agent = result.scalars().first()
                if agent and agent.squad_id:
                    await sse_manager.broadcast_to_squad(
                        agent.squad_id,
                        event['event'],
                        event
                    )
                    logger.info(f"Broadcasted {event['event']} to squad {agent.squad_id}")

        except Exception as e:
            logger.warning(f"Failed to broadcast webhook event: {e}")

    async def process_pull_request_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process pull_request webhook event

        Handles: opened, closed, reopened actions

        Args:
            payload: GitHub webhook payload

        Returns:
            Event dict if processed, None if ignored
        """
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_url = pr.get("html_url")
        repo_url = payload.get("repository", {}).get("html_url")
        merged = pr.get("merged", False)
        sender = payload.get("sender", {}).get("login", "unknown")

        if not pr_number or not repo_url:
            logger.warning("Missing PR number or repo URL in webhook payload")
            return None

        # Find associated sandbox
        sandbox = await self._find_sandbox_by_pr(pr_number, repo_url)
        if not sandbox:
            logger.warning(f"No sandbox found for PR #{pr_number} in {repo_url}")
            return None

        # Process based on action
        if action == "closed" and merged:
            # PR was merged
            event = PRMergedEvent(
                sandbox_id=sandbox.id,
                pr_number=pr_number,
                pr_url=pr_url,
                merged_by=sender,
                merge_commit_sha=pr.get("merge_commit_sha", "")
            )
            await self._broadcast_event(event.dict(), sandbox)
            return event.dict()

        elif action == "closed" and not merged:
            # PR was closed without merging
            event = PRClosedEvent(
                sandbox_id=sandbox.id,
                pr_number=pr_number,
                pr_url=pr_url,
                closed_by=sender
            )
            await self._broadcast_event(event.dict(), sandbox)
            return event.dict()

        elif action == "reopened":
            # PR was reopened
            event = PRReopenedEvent(
                sandbox_id=sandbox.id,
                pr_number=pr_number,
                pr_url=pr_url,
                reopened_by=sender
            )
            await self._broadcast_event(event.dict(), sandbox)
            return event.dict()

        return None

    async def process_pull_request_review_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process pull_request_review webhook event

        Handles: submitted action with state=approved

        Args:
            payload: GitHub webhook payload

        Returns:
            Event dict if processed, None if ignored
        """
        action = payload.get("action")
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_url = pr.get("html_url")
        repo_url = payload.get("repository", {}).get("html_url")
        review_state = review.get("state", "").lower()
        reviewer = review.get("user", {}).get("login", "unknown")

        if action != "submitted":
            return None

        if not pr_number or not repo_url:
            logger.warning("Missing PR number or repo URL in review webhook payload")
            return None

        # Find associated sandbox
        sandbox = await self._find_sandbox_by_pr(pr_number, repo_url)
        if not sandbox:
            logger.warning(f"No sandbox found for PR #{pr_number} in {repo_url}")
            return None

        # Only broadcast for approved reviews
        if review_state == "approved":
            event = PRApprovedEvent(
                sandbox_id=sandbox.id,
                pr_number=pr_number,
                pr_url=pr_url,
                reviewer=reviewer,
                review_state=review_state
            )
            await self._broadcast_event(event.dict(), sandbox)
            return event.dict()

        return None
