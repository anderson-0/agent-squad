"""
Interaction Configuration

Configuration for hierarchical agent-to-agent interactions including:
- Timeout settings
- Message templates
- Celery task settings
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class TimeoutConfig:
    """Timeout configuration for agent conversations"""

    # Initial timeout after question is asked (in seconds)
    initial_timeout_seconds: int = 300  # 5 minutes

    # Retry timeout after follow-up message (in seconds)
    retry_timeout_seconds: int = 120  # 2 minutes

    # Maximum number of retries before escalation
    max_retries: int = 1

    # Timeout for acknowledgment response (in seconds)
    acknowledgment_timeout_seconds: int = 30  # 30 seconds


@dataclass
class MessageTemplates:
    """Message templates for automated responses"""

    # Acknowledgment message
    acknowledgment: str = (
        "I received your question. Let me think about this, please wait..."
    )

    # Follow-up message after timeout
    follow_up: str = (
        "Are you still there? I'm still waiting for a response to my question."
    )

    # Escalation notification to original asker
    escalation_notification: str = (
        "I haven't received a response from {previous_responder}. "
        "I'm escalating this to {new_responder} for assistance."
    )

    # Escalation context for new responder
    escalation_context: str = (
        "This question was originally asked to {previous_responder} but no response was received. "
        "Please help with the following:\n\n{original_question}"
    )

    # Can't help routing message
    cant_help_routing: str = (
        "I don't have expertise in this area. Let me route this to {expert_role} who can help better."
    )


@dataclass
class CeleryConfig:
    """Celery configuration for background tasks"""

    # How often to check for timeouts (in seconds)
    timeout_check_interval: int = 60  # Check every minute

    # Task name for timeout monitoring
    timeout_task_name: str = "agents.interaction.check_conversation_timeouts"

    # Task retry settings
    task_max_retries: int = 3
    task_retry_delay: int = 60  # seconds


@dataclass
class InteractionConfig:
    """
    Main configuration class for agent interactions

    This class centralizes all configuration related to hierarchical
    agent-to-agent interactions including timeouts, message templates,
    and Celery task settings.
    """

    timeouts: TimeoutConfig = None
    messages: MessageTemplates = None
    celery: CeleryConfig = None

    def __post_init__(self):
        """Initialize nested configs if not provided"""
        if self.timeouts is None:
            self.timeouts = TimeoutConfig()
        if self.messages is None:
            self.messages = MessageTemplates()
        if self.celery is None:
            self.celery = CeleryConfig()

    def get_timeout_for_state(self, state: str) -> int:
        """
        Get the appropriate timeout for a conversation state

        Args:
            state: Current conversation state

        Returns:
            Timeout in seconds
        """
        if state == "waiting":
            return self.timeouts.initial_timeout_seconds
        elif state == "follow_up":
            return self.timeouts.retry_timeout_seconds
        else:
            return self.timeouts.initial_timeout_seconds

    def get_message_template(self, template_name: str, **kwargs) -> str:
        """
        Get a message template with optional formatting

        Args:
            template_name: Name of the template (acknowledgment, follow_up, etc.)
            **kwargs: Variables to format the template with

        Returns:
            Formatted message string
        """
        template = getattr(self.messages, template_name, None)
        if template is None:
            raise ValueError(f"Unknown message template: {template_name}")

        if kwargs:
            return template.format(**kwargs)
        return template


# Default configuration instance
default_interaction_config = InteractionConfig()


# Configuration getter for dependency injection
def get_interaction_config() -> InteractionConfig:
    """
    Get the interaction configuration

    This function can be overridden for testing or to provide
    environment-specific configuration.

    Returns:
        InteractionConfig instance
    """
    return default_interaction_config
