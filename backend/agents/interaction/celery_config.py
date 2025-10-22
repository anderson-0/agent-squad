"""
Celery Configuration for Agent Interactions

Configures Celery for periodic timeout monitoring and other
agent interaction background tasks.
"""
from celery import Celery
from celery.schedules import crontab
import asyncio

from backend.agents.configuration.interaction_config import get_interaction_config

# Get configuration
config = get_interaction_config()

# Initialize Celery app
celery_app = Celery(
    'agent_interactions',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes

    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks

    # Beat schedule (periodic tasks)
    beat_schedule={
        'check-conversation-timeouts': {
            'task': 'backend.agents.interaction.celery_tasks.check_timeouts_task',
            'schedule': config.celery.timeout_check_interval,  # Every 60 seconds by default
            'options': {
                'expires': config.celery.timeout_check_interval - 5,  # Expire before next run
            }
        },
    },

    # Task routes
    task_routes={
        'backend.agents.interaction.celery_tasks.*': {'queue': 'agent_interactions'},
    },
)


def run_async_task(coro):
    """
    Helper to run async tasks in Celery (which is synchronous)

    Args:
        coro: Async coroutine to run

    Returns:
        Result of the coroutine
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Health check task
@celery_app.task(name='backend.agents.interaction.celery_tasks.health_check')
def health_check_task():
    """
    Simple health check task to verify Celery is running

    Returns:
        Dictionary with health status
    """
    return {
        "status": "healthy",
        "service": "agent_interactions_celery",
        "timestamp": asyncio.run(get_current_timestamp())
    }


async def get_current_timestamp():
    """Get current UTC timestamp"""
    from datetime import datetime
    return datetime.utcnow().isoformat()


if __name__ == '__main__':
    # Run celery worker
    celery_app.start()
