"""
Inngest configuration and client for background job processing

This module provides the Inngest client for executing workflows asynchronously.
Enables instant API responses by moving agent execution to background workers.

Key Features:
- Durable workflow execution (survives crashes)
- Automatic retries (configurable per step)
- Built-in monitoring (Inngest dashboard)
- Independent scaling (workers separate from API)

Usage:
    from backend.core.inngest import inngest

    # Send event to trigger workflow
    await inngest.send(
        event="agent/workflow.execute",
        data={"execution_id": "..."}
    )
"""
from inngest import Inngest
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Inngest client
# If keys are not set, Inngest will run in dev mode (local)
inngest = Inngest(
    app_id="agent-squad",
    event_key=settings.INNGEST_EVENT_KEY or None,  # None = dev mode
    signing_key=settings.INNGEST_SIGNING_KEY or None,
    logger=logger,
)

logger.info(
    f"Inngest initialized: app_id=agent-squad, "
    f"mode={'production' if settings.INNGEST_EVENT_KEY else 'development'}"
)

# Export for use in other modules
__all__ = ["inngest"]
