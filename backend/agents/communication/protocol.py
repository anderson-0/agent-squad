"""
Agent-to-Agent (A2A) Communication Protocol

Handles parsing, validation, and serialization of structured messages
between agents following the A2A protocol specification.
"""
from typing import Dict, Any, Optional, Union
import json
from pydantic import ValidationError

from backend.schemas.agent_message import (
    TaskAssignment,
    StatusRequest,
    StatusUpdate,
    Question,
    Answer,
    HumanInterventionRequired,
    CodeReviewRequest,
    CodeReviewResponse,
    TaskCompletion,
    Standup,
    MessagePayload,
)


# Map action types to their corresponding classes
MESSAGE_TYPE_MAP: Dict[str, type] = {
    "task_assignment": TaskAssignment,
    "status_request": StatusRequest,
    "status_update": StatusUpdate,
    "question": Question,
    "answer": Answer,
    "human_intervention_required": HumanInterventionRequired,
    "code_review_request": CodeReviewRequest,
    "code_review_response": CodeReviewResponse,
    "task_completion": TaskCompletion,
    "standup": Standup,
}


class A2AProtocol:
    """
    Agent-to-Agent communication protocol handler.

    Provides methods to:
    - Parse raw JSON messages into structured objects
    - Validate message format and content
    - Serialize messages to JSON
    - Extract metadata from messages
    """

    @staticmethod
    def parse_message(raw_message: Union[str, Dict[str, Any]]) -> MessagePayload:
        """
        Parse a raw message into a structured message object.

        Args:
            raw_message: Raw JSON string or dictionary

        Returns:
            Parsed message object (TaskAssignment, StatusUpdate, etc.)

        Raises:
            ValueError: If message format is invalid
            ValidationError: If message validation fails
        """
        # Parse JSON if string
        if isinstance(raw_message, str):
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            data = raw_message

        # Validate required fields
        if not isinstance(data, dict):
            raise ValueError("Message must be a dictionary")

        if "action" not in data:
            raise ValueError("Message must have 'action' field")

        action = data.get("action")

        # Get corresponding message class
        message_class = MESSAGE_TYPE_MAP.get(action)
        if not message_class:
            raise ValueError(
                f"Unknown action type: {action}. "
                f"Supported: {', '.join(MESSAGE_TYPE_MAP.keys())}"
            )

        # Parse and validate
        try:
            message = message_class(**data)
            return message
        except ValidationError as e:
            raise ValueError(f"Message validation failed: {e}")

    @staticmethod
    def serialize_message(message: MessagePayload) -> str:
        """
        Serialize a message object to JSON string.

        Args:
            message: Structured message object

        Returns:
            JSON string representation
        """
        return message.model_dump_json(indent=2)

    @staticmethod
    def serialize_message_dict(message: MessagePayload) -> Dict[str, Any]:
        """
        Serialize a message object to dictionary.

        Args:
            message: Structured message object

        Returns:
            Dictionary representation
        """
        return message.model_dump()

    @staticmethod
    def validate_message(raw_message: Union[str, Dict[str, Any]]) -> bool:
        """
        Validate a message without parsing it fully.

        Args:
            raw_message: Raw JSON string or dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            A2AProtocol.parse_message(raw_message)
            return True
        except (ValueError, ValidationError):
            return False

    @staticmethod
    def extract_metadata(message: MessagePayload) -> Dict[str, Any]:
        """
        Extract metadata from a message.

        Args:
            message: Structured message object

        Returns:
            Dictionary with metadata
        """
        metadata = {
            "action": message.action,
            "message_class": message.__class__.__name__,
        }

        # Add common fields
        if hasattr(message, "task_id"):
            metadata["task_id"] = message.task_id

        if hasattr(message, "recipient"):
            metadata["recipient"] = str(message.recipient)

        if hasattr(message, "urgency"):
            metadata["urgency"] = message.urgency

        if hasattr(message, "priority"):
            metadata["priority"] = message.priority

        return metadata

    @staticmethod
    def get_message_type(raw_message: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Get the action/message type from a raw message.

        Args:
            raw_message: Raw JSON string or dictionary

        Returns:
            Action type string or None if invalid
        """
        try:
            if isinstance(raw_message, str):
                data = json.loads(raw_message)
            else:
                data = raw_message

            return data.get("action")
        except (json.JSONDecodeError, AttributeError):
            return None

    @staticmethod
    def create_task_assignment(
        recipient: str,
        task_id: str,
        description: str,
        acceptance_criteria: list[str],
        context: str,
        priority: str = "medium",
        dependencies: Optional[list[str]] = None,
        estimated_hours: Optional[float] = None,
    ) -> TaskAssignment:
        """
        Helper to create a TaskAssignment message.

        Args:
            recipient: Agent ID to assign to
            task_id: Task identifier
            description: Task description
            acceptance_criteria: List of acceptance criteria
            context: Task context
            priority: Priority level
            dependencies: List of dependencies
            estimated_hours: Estimated hours

        Returns:
            TaskAssignment message
        """
        from uuid import UUID
        return TaskAssignment(
            recipient=UUID(recipient) if isinstance(recipient, str) else recipient,
            task_id=task_id,
            description=description,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies or [],
            context=context,
            priority=priority,
            estimated_hours=estimated_hours,
        )

    @staticmethod
    def create_status_update(
        task_id: str,
        status: str,
        progress_percentage: int,
        details: str,
        blockers: Optional[list[str]] = None,
        next_steps: Optional[str] = None,
    ) -> StatusUpdate:
        """
        Helper to create a StatusUpdate message.

        Args:
            task_id: Task identifier
            status: Current status
            progress_percentage: Progress (0-100)
            details: Status details
            blockers: List of blockers
            next_steps: Next steps

        Returns:
            StatusUpdate message
        """
        return StatusUpdate(
            task_id=task_id,
            status=status,
            progress_percentage=progress_percentage,
            details=details,
            blockers=blockers or [],
            next_steps=next_steps,
        )

    @staticmethod
    def create_question(
        task_id: str,
        question: str,
        context: str,
        recipient: Optional[str] = None,
        urgency: str = "normal",
    ) -> Question:
        """
        Helper to create a Question message.

        Args:
            task_id: Task identifier
            question: Question text
            context: Question context
            recipient: Optional recipient (None for broadcast)
            urgency: Urgency level

        Returns:
            Question message
        """
        from uuid import UUID
        return Question(
            task_id=task_id,
            question=question,
            context=context,
            recipient=UUID(recipient) if recipient else None,
            urgency=urgency,
        )

    @staticmethod
    def create_human_intervention(
        task_id: str,
        reason: str,
        details: str,
        attempted_solutions: list[str],
        urgency: str = "high",
    ) -> HumanInterventionRequired:
        """
        Helper to create a HumanInterventionRequired message.

        Args:
            task_id: Task identifier
            reason: Reason for escalation
            details: Detailed explanation
            attempted_solutions: What was tried
            urgency: Urgency level

        Returns:
            HumanInterventionRequired message
        """
        return HumanInterventionRequired(
            task_id=task_id,
            reason=reason,
            details=details,
            attempted_solutions=attempted_solutions,
            urgency=urgency,
        )


# Convenience functions

def parse_message(raw: Union[str, Dict]) -> MessagePayload:
    """Parse a raw message"""
    return A2AProtocol.parse_message(raw)


def serialize_message(message: MessagePayload) -> str:
    """Serialize a message to JSON"""
    return A2AProtocol.serialize_message(message)


def validate_message(raw: Union[str, Dict]) -> bool:
    """Validate a message"""
    return A2AProtocol.validate_message(raw)
