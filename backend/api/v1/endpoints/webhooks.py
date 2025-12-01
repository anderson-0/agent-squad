"""
GitHub Webhooks API Endpoint

Receives and processes GitHub webhook events for PR status updates.
"""
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.services.webhook_service import WebhookService
from backend.schemas.webhook_events import WebhookValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    db: AsyncSession = Depends(get_db)
):
    """
    GitHub webhook endpoint

    Receives webhook events from GitHub for PR status updates.
    Validates HMAC signature and broadcasts events via SSE.

    Required Headers:
    - X-Hub-Signature-256: HMAC signature for payload verification
    - X-GitHub-Event: Event type (pull_request, pull_request_review, etc.)

    Supported Events:
    - pull_request (actions: opened, closed, reopened)
    - pull_request_review (action: submitted with state=approved)

    Returns:
        200: Event processed successfully
        400: Invalid payload or signature
        500: Internal server error
    """
    # Read raw body for signature verification
    body = await request.body()

    # Initialize webhook service
    service = WebhookService(db)

    # Verify signature
    try:
        if not service.verify_signature(body, x_hub_signature_256):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
    except WebhookValidationError as e:
        logger.warning(f"Webhook validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Log webhook event
    logger.info(f"Received GitHub webhook: {x_github_event} - {payload.get('action')}")

    # Process event based on type
    event_result = None
    try:
        if x_github_event == "pull_request":
            event_result = await service.process_pull_request_event(payload)
        elif x_github_event == "pull_request_review":
            event_result = await service.process_pull_request_review_event(payload)
        else:
            logger.info(f"Ignoring unsupported event type: {x_github_event}")
            return {"status": "ignored", "event_type": x_github_event}

        if event_result:
            logger.info(f"Processed webhook event: {event_result['event']}")
            return {
                "status": "processed",
                "event": event_result
            }
        else:
            return {
                "status": "ignored",
                "reason": "Event did not match processing criteria"
            }

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.get("/github/test")
async def test_webhook_endpoint():
    """
    Test endpoint to verify webhook route is accessible

    Returns basic info about the webhook configuration.
    """
    import os
    webhook_secret_set = bool(os.environ.get("GITHUB_WEBHOOK_SECRET"))

    return {
        "status": "ok",
        "endpoint": "/api/v1/webhooks/github",
        "webhook_secret_configured": webhook_secret_set,
        "supported_events": [
            "pull_request (actions: opened, closed, reopened)",
            "pull_request_review (action: submitted)"
        ]
    }
