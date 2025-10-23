"""
Agno-based Agent Foundation

This module provides the base class for all Agno-powered agents,
following Clean Architecture, SOLID principles, and enterprise design patterns.

Architecture Patterns:
- Template Method Pattern: Base class defines structure, subclasses implement specifics
- Strategy Pattern: Multiple LLM provider strategies
- Factory Method Pattern: Agent creation
- Adapter Pattern: Agno framework adaptation to our interface
- Dependency Injection: External dependencies injected via constructor
"""
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable, Callable
from abc import ABC, abstractmethod
from uuid import UUID
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from agno.agent import Agent as AgnoAgent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq

from backend.core.agno_config import get_agno_db
from backend.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Models (Clean Architecture - Entities)
# ============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class AgentConfig(BaseModel):
    """
    Agent configuration value object.

    Immutable configuration for agent creation.
    Follows Value Object pattern from DDD.
    """
    role: str = Field(..., description="Agent role (e.g., 'project_manager')")
    specialization: Optional[str] = Field(None, description="Agent specialization")
    llm_provider: LLMProvider = Field(LLMProvider.OPENAI, description="LLM provider")
    llm_model: str = Field("gpt-4o-mini", description="LLM model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, ge=1, description="Max tokens per response")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        """Ensure temperature is in valid range"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    model_config = {"frozen": True}  # Immutable value object (Pydantic v2)


class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """
    Response from an agent.

    Follows Response DTO pattern.
    """
    content: str = Field(..., description="Response content")
    thinking: Optional[str] = Field(None, description="Agent's reasoning (if available)")
    action_items: List[str] = Field(default_factory=list, description="Extracted action items")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools called")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolResult(BaseModel):
    """Result from a tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    tool_name: str
    execution_time: Optional[float] = None


# ============================================================================
# Protocols / Interfaces (Clean Architecture - Use Case Boundaries)
# ============================================================================

@runtime_checkable
class ILLMProvider(Protocol):
    """
    Interface for LLM provider implementations.

    Follows Interface Segregation Principle (SOLID).
    """
    def create_model(self, config: AgentConfig) -> Any:
        """Create LLM model instance"""
        ...


@runtime_checkable
class IPromptLoader(Protocol):
    """Interface for loading system prompts"""
    def load_prompt(self, role: str, specialization: Optional[str]) -> str:
        """Load system prompt for role"""
        ...


# ============================================================================
# LLM Provider Strategies (Strategy Pattern)
# ============================================================================

class LLMProviderFactory:
    """
    Factory for creating LLM providers.

    Follows Factory Pattern + Strategy Pattern.
    """

    @staticmethod
    def create_model(config: AgentConfig) -> Any:
        """
        Create appropriate LLM model based on configuration.

        Args:
            config: Agent configuration

        Returns:
            Agno model instance

        Raises:
            ValueError: If provider is unsupported

        Design Pattern: Factory Method + Strategy
        """
        providers = {
            LLMProvider.ANTHROPIC: LLMProviderFactory._create_claude,
            LLMProvider.OPENAI: LLMProviderFactory._create_openai,
            LLMProvider.GROQ: LLMProviderFactory._create_groq,
        }

        creator = providers.get(config.llm_provider)
        if not creator:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

        return creator(config)

    @staticmethod
    def _create_claude(config: AgentConfig) -> Claude:
        """Create Anthropic Claude model"""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        return Claude(
            id=config.llm_model,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=config.temperature,
            max_tokens=config.max_tokens or 4096,
        )

    @staticmethod
    def _create_openai(config: AgentConfig) -> OpenAIChat:
        """Create OpenAI model"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        return OpenAIChat(
            id=config.llm_model,
            api_key=settings.OPENAI_API_KEY,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    @staticmethod
    def _create_groq(config: AgentConfig) -> Groq:
        """Create Groq model"""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")

        return Groq(
            id=config.llm_model,
            api_key=settings.GROQ_API_KEY,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


# ============================================================================
# System Prompt Loader (Single Responsibility Principle)
# ============================================================================

class FileSystemPromptLoader:
    """
    Loads system prompts from filesystem.

    Follows Single Responsibility Principle (SOLID).
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize prompt loader.

        Args:
            base_path: Base directory for prompts (defaults to roles/)
        """
        self.base_path = base_path or (Path(__file__).parent.parent.parent / "roles")

    def load_prompt(self, role: str, specialization: Optional[str] = None) -> str:
        """
        Load system prompt for role and specialization.

        Args:
            role: Agent role
            specialization: Optional specialization

        Returns:
            System prompt text

        Raises:
            FileNotFoundError: If no prompt file found
        """
        role_path = self.base_path / role

        # Try specialization file first
        if specialization:
            spec_file = role_path / f"{specialization}.md"
            if spec_file.exists():
                logger.debug(f"Loading specialized prompt: {spec_file}")
                return spec_file.read_text()

        # Fall back to default prompt
        default_file = role_path / "default_prompt.md"
        if default_file.exists():
            logger.debug(f"Loading default prompt: {default_file}")
            return default_file.read_text()

        # Fallback to basic prompt
        logger.warning(f"No prompt file found for role '{role}', using basic prompt")
        return f"You are a {role} agent in a software development team."


# ============================================================================
# Base Agent Class (Template Method Pattern)
# ============================================================================

class AgnoSquadAgent(ABC):
    """
    Base class for all Agno-powered squad agents.

    This class provides the foundation for all specialized agents,
    following Clean Architecture, SOLID principles, and enterprise patterns.

    Architecture Patterns:
    - Template Method: Defines agent lifecycle structure
    - Strategy: LLM provider selection
    - Adapter: Adapts Agno to our interface
    - Dependency Injection: Dependencies injected via constructor

    SOLID Principles:
    - Single Responsibility: Focused on agent lifecycle
    - Open/Closed: Extensible via subclassing, closed for modification
    - Liskov Substitution: Subclasses can replace base class
    - Interface Segregation: Minimal interface required
    - Dependency Inversion: Depends on abstractions (ILLMProvider, IPromptLoader)
    """

    def __init__(
        self,
        config: AgentConfig,
        agent_id: Optional[UUID] = None,
        mcp_client: Optional[Any] = None,
        session_id: Optional[str] = None,
        prompt_loader: Optional[IPromptLoader] = None,
    ):
        """
        Initialize Agno-based agent.

        Args:
            config: Agent configuration (value object)
            agent_id: Optional agent UUID for message bus identification
            mcp_client: Optional MCP client (backward compatibility)
            session_id: Optional session ID for resuming conversations
            prompt_loader: Optional custom prompt loader (dependency injection)

        Design Pattern: Dependency Injection
        """
        # Validate configuration
        self._validate_config(config)

        # Store configuration (immutable)
        self.config = config
        self.agent_id = agent_id  # For message bus identification

        # Legacy compatibility
        self.mcp_client = mcp_client
        self.tool_execution_history: List[ToolResult] = []

        # Token tracking (for monitoring)
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        # Dependency injection
        self._prompt_loader = prompt_loader or FileSystemPromptLoader()

        # Load system prompt if not provided
        if not config.system_prompt:
            loaded_prompt = self._load_system_prompt()
            # Pydantic v2: use model_copy with update
            self.config = config.model_copy(
                update={"system_prompt": loaded_prompt}
            )

        # Create Agno agent
        self.agent = self._create_agno_agent(session_id)

        session_info = self.session_id[:8] + "..." if self.session_id else "new"
        logger.info(
            f"Created AgnoSquadAgent: {self._format_agent_name()} "
            f"(ID: {str(agent_id)[:8] if agent_id else 'None'}..., session: {session_info})"
        )

    def _validate_config(self, config: AgentConfig) -> None:
        """
        Validate agent configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not config.role:
            raise ValueError("Agent role is required")

        if not config.llm_model:
            raise ValueError("LLM model is required")

    def _load_system_prompt(self) -> str:
        """
        Load system prompt using injected loader.

        Returns:
            System prompt text

        Design Pattern: Strategy via Dependency Injection
        """
        return self._prompt_loader.load_prompt(
            role=self.config.role,
            specialization=self.config.specialization
        )

    def _create_agno_agent(self, session_id: Optional[str]) -> AgnoAgent:
        """
        Create underlying Agno agent.

        Args:
            session_id: Optional session ID for resumption

        Returns:
            Configured Agno agent

        Design Pattern: Factory Method
        """
        # Create LLM model (Strategy pattern)
        model = LLMProviderFactory.create_model(self.config)

        # Get database (Singleton pattern)
        db = get_agno_db()

        # Prepare tools (if any)
        tools = self._prepare_tools()

        # Create Agno agent
        agent = AgnoAgent(
            name=self._format_agent_name(),
            role=self._format_agent_role(),
            model=model,
            db=db,
            description=self.config.system_prompt,
            add_history_to_context=True,
            num_history_runs=10,  # Number of previous runs to include in context
            session_id=session_id,
            tools=tools,
            debug_mode=False,  # Set to True for debugging
        )

        return agent

    def _prepare_tools(self) -> List[Any]:
        """
        Prepare tools for agent.

        Override in subclasses to add specific tools.

        Returns:
            List of tools

        Design Pattern: Hook Method (Template Method pattern)
        """
        # Base implementation: no tools
        # Subclasses can override to add MCP tools, etc.
        return []

    def _format_agent_name(self) -> str:
        """Format agent name for Agno"""
        role = self.config.role.replace("_", " ").title()
        if self.config.specialization:
            return f"{role} ({self.config.specialization})"
        return role

    def _format_agent_role(self) -> str:
        """
        Format agent role description.

        Returns:
            Human-readable role description
        """
        role_descriptions = {
            "project_manager": "Orchestrate software development squad and manage tasks",
            "tech_lead": "Provide technical leadership and code review",
            "backend_developer": "Implement backend features and APIs",
            "frontend_developer": "Implement frontend UI and user experience",
            "tester": "Ensure quality through comprehensive testing",
            "solution_architect": "Design system architecture and technical solutions",
            "devops_engineer": "Manage infrastructure and deployments",
            "ai_engineer": "Develop and integrate AI/ML capabilities",
            "designer": "Create user interfaces and user experiences",
        }
        return role_descriptions.get(
            self.config.role,
            f"{self.config.role} specialist"
        )

    # ============================================================================
    # Public API (Interface)
    # ============================================================================

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
    ) -> AgentResponse:
        """
        Process a message and return a response.

        This maintains compatibility with BaseSquadAgent while
        leveraging Agno's persistent history.

        Args:
            message: User message to process
            context: Additional context (task details, RAG results, etc.)
            conversation_history: Ignored (Agno manages history automatically)

        Returns:
            AgentResponse with content and metadata

        Design Pattern: Template Method
        """
        try:
            # Build enhanced message with context
            enhanced_message = self._build_message_with_context(message, context)

            # Run Agno agent
            agno_response = self.agent.run(enhanced_message)

            # Convert to our response format (Adapter pattern)
            response = self._convert_agno_response(agno_response)

            logger.debug(
                f"Agent {self._format_agent_name()} processed message "
                f"(length: {len(message)})"
            )

            return response

        except Exception as e:
            logger.error(
                f"Error processing message in {self._format_agent_name()}: {e}",
                exc_info=True
            )
            raise

    def _build_message_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Enhance message with context information.

        Args:
            message: Original message
            context: Additional context

        Returns:
            Enhanced message with context

        Design Pattern: Builder Pattern
        """
        if not context:
            return message

        context_parts = [message]

        # Add ticket context
        if "ticket" in context:
            ticket = context["ticket"]
            context_parts.append("\n\n**Ticket Context:**")
            if "title" in ticket:
                context_parts.append(f"- Title: {ticket['title']}")
            if "description" in ticket:
                context_parts.append(f"- Description: {ticket['description']}")

        # Add action context
        if "action" in context:
            context_parts.append(f"\n\n**Action:** {context['action']}")

        # Add RAG context
        if "related_code" in context and context["related_code"]:
            context_parts.append("\n\n**Related Code:**")
            context_parts.append(str(context["related_code"])[:500])  # Limit size

        return "\n".join(context_parts)

    def _convert_agno_response(self, agno_response: Any) -> AgentResponse:
        """
        Convert Agno response to our response format.

        Args:
            agno_response: Response from Agno agent

        Returns:
            AgentResponse

        Design Pattern: Adapter Pattern
        """
        # Get message count safely
        messages_count = 0
        try:
            if self.agent.session_id:
                session_messages = self.agent.get_messages_for_session(self.agent.session_id)
                messages_count = len(session_messages) if session_messages else 0
        except Exception:
            pass  # If we can't get messages, just use 0

        return AgentResponse(
            content=agno_response.content,
            thinking=None,  # Agno doesn't separate thinking
            action_items=[],  # Could parse from content
            tool_calls=[],  # Track if tools were used
            metadata={
                "session_id": self.agent.session_id,
                "messages_count": messages_count,
                "framework": "agno",
                "agent_role": self.config.role,
            }
        )

    # ============================================================================
    # Message Bus Integration (Inter-Agent Communication)
    # ============================================================================

    async def send_message(
        self,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_execution_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        db: Optional[Any] = None,
    ) -> Any:
        """
        Send a message to another agent via the message bus.

        Args:
            recipient_id: ID of receiving agent (None for broadcast)
            content: Message content
            message_type: Type of message (task_assignment, question, etc.)
            metadata: Optional metadata dict
            task_execution_id: Optional task execution context
            conversation_id: Optional conversation context
            db: Optional database session for enriched metadata

        Returns:
            AgentMessageResponse

        Raises:
            ValueError: If agent_id not configured
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to send messages")

        # Lazy import to avoid circular dependency
        from backend.agents.communication.message_bus import get_message_bus

        message_bus = get_message_bus()

        # Add framework metadata
        message_metadata = metadata or {}
        message_metadata.update({
            "framework": "agno",
            "session_id": self.agent.session_id,
            "agent_role": self.config.role,
        })

        message = await message_bus.send_message(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            metadata=message_metadata,
            task_execution_id=task_execution_id,
            conversation_id=conversation_id,
            db=db,
        )

        logger.debug(
            f"Agent {self._format_agent_name()} sent {message_type} message to "
            f"{'broadcast' if recipient_id is None else str(recipient_id)[:8]}"
        )

        return message

    async def broadcast_message(
        self,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_execution_id: Optional[UUID] = None,
        db: Optional[Any] = None,
    ) -> Any:
        """
        Broadcast a message to all agents.

        Args:
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
            task_execution_id: Optional task execution context
            db: Optional database session

        Returns:
            AgentMessageResponse
        """
        return await self.send_message(
            recipient_id=None,  # None means broadcast
            content=content,
            message_type=message_type,
            metadata=metadata,
            task_execution_id=task_execution_id,
            db=db,
        )

    async def receive_messages(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
    ) -> List[Any]:
        """
        Receive messages from the message bus.

        Args:
            since: Only get messages after this time
            limit: Maximum number of messages
            message_type: Filter by message type

        Returns:
            List of AgentMessageResponse

        Raises:
            ValueError: If agent_id not configured
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to receive messages")

        # Lazy import to avoid circular dependency
        from backend.agents.communication.message_bus import get_message_bus

        message_bus = get_message_bus()

        messages = await message_bus.get_messages(
            agent_id=self.agent_id,
            since=since,
            limit=limit,
            message_type=message_type,
        )

        logger.debug(
            f"Agent {self._format_agent_name()} received {len(messages)} messages"
        )

        return messages

    async def subscribe_to_messages(
        self,
        callback: Callable[[Any], None]
    ) -> str:
        """
        Subscribe to real-time messages.

        Args:
            callback: Async function to call when message arrives

        Returns:
            Subscription ID

        Raises:
            ValueError: If agent_id not configured
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to subscribe")

        # Lazy import to avoid circular dependency
        from backend.agents.communication.message_bus import get_message_bus

        message_bus = get_message_bus()

        subscription_id = await message_bus.subscribe(
            agent_id=self.agent_id,
            callback=callback
        )

        logger.info(
            f"Agent {self._format_agent_name()} subscribed to messages "
            f"(subscription: {subscription_id})"
        )

        return subscription_id

    async def unsubscribe_from_messages(self, callback: Callable) -> bool:
        """
        Unsubscribe from messages.

        Args:
            callback: Callback function to remove

        Returns:
            True if unsubscribed, False if not found

        Raises:
            ValueError: If agent_id not configured
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to unsubscribe")

        # Lazy import to avoid circular dependency
        from backend.agents.communication.message_bus import get_message_bus

        message_bus = get_message_bus()

        unsubscribed = await message_bus.unsubscribe(
            agent_id=self.agent_id,
            callback=callback
        )

        if unsubscribed:
            logger.info(f"Agent {self._format_agent_name()} unsubscribed from messages")

        return unsubscribed

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def reset_conversation(self) -> None:
        """
        Reset conversation history by creating new session.

        Note: With Agno, this creates a new session.
        Old session remains in database for historical reference.
        """
        old_session_id = self.agent.session_id
        old_session_str = old_session_id[:8] + "..." if old_session_id else "None"

        # Create new agent with fresh session
        self.agent = self._create_agno_agent(session_id=None)

        new_session_str = self.agent.session_id[:8] + "..." if self.agent.session_id else "None"
        logger.info(
            f"Conversation reset: {old_session_str} → {new_session_str}"
        )

    def get_conversation_history(self) -> List[ConversationMessage]:
        """
        Get current conversation history.

        Returns:
            List of conversation messages

        Design Pattern: Adapter (converts Agno format to our format)
        """
        history = []
        try:
            if self.agent.session_id:
                messages = self.agent.get_messages_for_session(self.agent.session_id)
                if messages:
                    for msg in messages:
                        history.append(ConversationMessage(
                            role=msg.get("role", "assistant"),
                            content=msg.get("content", ""),
                            metadata={}
                        ))
        except Exception:
            pass  # Return empty history if we can't get messages
        return history

    def get_token_usage(self) -> Dict[str, int]:
        """Get token usage statistics"""
        return self.token_usage.copy()

    def has_mcp_client(self) -> bool:
        """Check if this agent has an MCP client configured"""
        return len(self.agent.tools) > 0 or self.mcp_client is not None

    @property
    def session_id(self) -> str:
        """Get current Agno session ID"""
        return self.agent.session_id

    # ============================================================================
    # Abstract Methods (Template Method Pattern)
    # ============================================================================

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent has.

        Must be implemented by subclasses.

        Returns:
            List of capability names

        Design Pattern: Template Method
        """
        pass

    # ============================================================================
    # String Representation
    # ============================================================================

    def __repr__(self) -> str:
        """String representation of agent"""
        session_str = self.session_id[:8] + "..." if self.session_id else "pending"
        return (
            f"<AgnoSquadAgent "
            f"role={self.config.role} "
            f"provider={self.config.llm_provider.value} "
            f"model={self.config.llm_model} "
            f"session={session_str}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self._format_agent_name()} (Agno-powered)"
