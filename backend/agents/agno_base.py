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
from agno.models.ollama import Ollama

from backend.core.agno_config import get_agno_db
from backend.core.config import settings
from backend.models.llm_cost_tracking import calculate_cost
from backend.models import LLMCostEntry
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Models (Clean Architecture - Entities)
# ============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"


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
            LLMProvider.OLLAMA: LLMProviderFactory._create_ollama,
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

    @staticmethod
    def _create_ollama(config: AgentConfig) -> Ollama:
        """Create Ollama model (local LLM)"""
        # Ollama doesn't require API key - runs locally
        # Temperature and other model parameters go in the options dict
        return Ollama(
            id=config.llm_model or settings.OLLAMA_MODEL,
            host=settings.OLLAMA_BASE_URL,
            options={
                "temperature": config.temperature,
                "num_predict": config.max_tokens if config.max_tokens else None,
            }
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

        Automatically initializes MCP tools based on agent role.
        Subclasses can override to add additional custom tools.

        Returns:
            List of tools (Agno-compatible functions)

        Design Pattern: Hook Method (Template Method pattern)
        """
        # Try to initialize MCP tools for this role
        try:
            from backend.services.agent_mcp_service import get_agent_mcp_service

            mcp_service = get_agent_mcp_service()

            # Get available tools for this role
            available_tools = mcp_service.mapper.get_all_tools_for_role(self.config.role)

            if not available_tools:
                logger.debug(f"No MCP tools configured for role '{self.config.role}'")
                return []

            # Create Agno-compatible tool functions
            tools = self._create_mcp_tool_functions(mcp_service, available_tools)

            logger.info(
                f"Prepared {len(tools)} MCP tools for role '{self.config.role}'"
            )

            return tools

        except Exception as e:
            logger.warning(
                f"Failed to initialize MCP tools for role '{self.config.role}': {e}"
            )
            # Non-fatal: agent works without tools
            return []

    def _create_mcp_tool_functions(
        self,
        mcp_service: Any,
        available_tools: Dict[str, List[str]]
    ) -> List[Callable]:
        """
        Create Agno-compatible tool functions from MCP tools.

        Args:
            mcp_service: AgentMCPService instance
            available_tools: Dict mapping server -> list of tool names

        Returns:
            List of callable tool functions
        """
        tools = []

        for server, tool_names in available_tools.items():
            for tool_name in tool_names:
                # Create wrapped function for this tool
                tool_func = self._create_tool_function(
                    mcp_service, server, tool_name
                )
                tools.append(tool_func)

        return tools

    def _create_tool_function(
        self,
        mcp_service: Any,
        server: str,
        tool_name: str
    ) -> Callable:
        """
        Create an Agno-compatible tool function for a specific MCP tool.

        Args:
            mcp_service: AgentMCPService instance
            server: MCP server name
            tool_name: Tool name

        Returns:
            Callable tool function
        """
        import asyncio
        from typing import Annotated
        import inspect

        # Create async wrapper that executes the MCP tool
        async def tool_wrapper(**kwargs) -> str:
            """
            Execute MCP tool via AgentMCPService.

            This function is dynamically created for each MCP tool
            and provides permission-checked execution.
            """
            try:
                # Initialize MCP servers if needed (first call)
                if not mcp_service.is_server_connected(self.config.role, server):
                    logger.debug(
                        f"Initializing MCP server '{server}' for role '{self.config.role}'"
                    )
                    await mcp_service.initialize_agent_tools(self.config.role)

                # Execute tool with permission checking
                result = await mcp_service.execute_tool(
                    role=self.config.role,
                    server=server,
                    tool=tool_name,
                    arguments=kwargs,
                    track_usage=True
                )

                # Track in agent history
                self.tool_execution_history.append(ToolResult(
                    success=True,
                    result=result,
                    error=None,
                    tool_name=f"{server}.{tool_name}",
                    execution_time=None
                ))

                # Return result as string (Agno expects string return)
                return str(result)

            except PermissionError as e:
                error_msg = f"Permission denied: {e}"
                logger.error(error_msg)

                # Track failure
                self.tool_execution_history.append(ToolResult(
                    success=False,
                    result=None,
                    error=error_msg,
                    tool_name=f"{server}.{tool_name}",
                    execution_time=None
                ))

                return error_msg

            except Exception as e:
                error_msg = f"Tool execution failed: {e}"
                logger.error(error_msg)

                # Track failure
                self.tool_execution_history.append(ToolResult(
                    success=False,
                    result=None,
                    error=error_msg,
                    tool_name=f"{server}.{tool_name}",
                    execution_time=None
                ))

                return error_msg

        # Set function metadata for Agno
        tool_wrapper.__name__ = f"{server}_{tool_name}"
        tool_wrapper.__doc__ = f"Execute {tool_name} on {server} MCP server"

        # Agno needs sync functions, so wrap async in sync
        def sync_wrapper(**kwargs) -> str:
            """Synchronous wrapper for async tool execution."""
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, we're in an async context
                # Create a task and wait for it
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        tool_wrapper(**kwargs)
                    )
                    return future.result()
            else:
                # No event loop, we can use asyncio.run
                return asyncio.run(tool_wrapper(**kwargs))

        # Copy metadata
        sync_wrapper.__name__ = tool_wrapper.__name__
        sync_wrapper.__doc__ = tool_wrapper.__doc__

        return sync_wrapper

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
        squad_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        task_execution_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        track_cost: bool = True,
        db: Optional[Any] = None,
    ) -> AgentResponse:
        """
        Process a message and return a response.

        This maintains compatibility with BaseSquadAgent while
        leveraging Agno's persistent history.

        Args:
            message: User message to process
            context: Additional context (task details, RAG results, etc.)
            conversation_history: Ignored (Agno manages history automatically)
            squad_id: Optional squad ID for cost tracking
            user_id: Optional user ID for cost tracking
            organization_id: Optional organization ID for cost tracking
            task_execution_id: Optional task execution ID for cost tracking
            conversation_id: Optional conversation ID for cost tracking
            track_cost: Whether to track LLM costs (default: True)
            db: Optional database session for cost tracking

        Returns:
            AgentResponse with content and metadata

        Design Pattern: Template Method
        """
        start_time = datetime.now()

        try:
            # Build enhanced message with context
            enhanced_message = self._build_message_with_context(message, context)

            # Run Agno agent
            agno_response = self.agent.run(enhanced_message)

            # Calculate response time
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Extract token usage from response (if available)
            prompt_tokens, completion_tokens = self._extract_token_usage(agno_response)

            # Track cost if requested and DB session provided
            if track_cost and db is not None:
                await self._track_llm_cost(
                    db=db,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time_ms=response_time_ms,
                    squad_id=squad_id,
                    user_id=user_id,
                    organization_id=organization_id,
                    task_execution_id=task_execution_id,
                    conversation_id=conversation_id,
                )

            # Convert to our response format (Adapter pattern)
            response = self._convert_agno_response(agno_response)

            # Add token usage to metadata
            response.metadata.update({
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "response_time_ms": response_time_ms,
            })

            logger.debug(
                f"Agent {self._format_agent_name()} processed message "
                f"(length: {len(message)}, tokens: {prompt_tokens + completion_tokens})"
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

    def _extract_token_usage(self, agno_response: Any) -> tuple[int, int]:
        """
        Extract token usage from Agno response.

        Different LLM providers return tokens differently.
        This method attempts to extract them from various response formats.

        Args:
            agno_response: Response from Agno agent

        Returns:
            Tuple of (prompt_tokens, completion_tokens)
        """
        prompt_tokens = 0
        completion_tokens = 0

        try:
            # Try to get metrics from response
            if hasattr(agno_response, 'metrics'):
                metrics = agno_response.metrics
                if metrics:
                    prompt_tokens = metrics.get('input_tokens', 0) or metrics.get('prompt_tokens', 0)
                    completion_tokens = metrics.get('output_tokens', 0) or metrics.get('completion_tokens', 0)

            # Try alternative attributes
            elif hasattr(agno_response, 'usage'):
                usage = agno_response.usage
                if usage:
                    prompt_tokens = getattr(usage, 'prompt_tokens', 0) or getattr(usage, 'input_tokens', 0)
                    completion_tokens = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0)

            # For Ollama (which doesn't report tokens), estimate
            # Average ~4 characters per token (rough estimate)
            if prompt_tokens == 0 and completion_tokens == 0 and self.config.llm_provider == LLMProvider.OLLAMA:
                # This is a rough estimate - Ollama doesn't provide actual token counts
                completion_tokens = len(agno_response.content) // 4

            logger.debug(f"Extracted tokens: prompt={prompt_tokens}, completion={completion_tokens}")

        except Exception as e:
            logger.warning(f"Could not extract token usage: {e}")
            # Return zeros if extraction fails
            pass

        return prompt_tokens, completion_tokens

    async def _track_llm_cost(
        self,
        db: Any,  # AsyncSession
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: int,
        squad_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        task_execution_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
    ) -> None:
        """
        Track LLM cost in database.

        Args:
            db: Database session (AsyncSession)
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            response_time_ms: Response time in milliseconds
            squad_id: Optional squad ID
            user_id: Optional user ID
            organization_id: Optional organization ID
            task_execution_id: Optional task execution ID
            conversation_id: Optional conversation ID
        """
        try:
            # Calculate cost
            total_tokens = prompt_tokens + completion_tokens
            cost_data = calculate_cost(
                provider=self.config.llm_provider.value,
                model=self.config.llm_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            # Create cost entry
            cost_entry = LLMCostEntry(
                id=uuid.uuid4(),
                provider=self.config.llm_provider.value,
                model=self.config.llm_model,
                squad_id=squad_id,
                agent_id=self.agent_id,
                user_id=user_id,
                organization_id=organization_id,
                task_execution_id=task_execution_id,
                conversation_id=conversation_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                prompt_cost_usd=cost_data["prompt_cost_usd"],
                completion_cost_usd=cost_data["completion_cost_usd"],
                total_cost_usd=cost_data["total_cost_usd"],
                prompt_price_per_1m=cost_data["prompt_price_per_1m"],
                completion_price_per_1m=cost_data["completion_price_per_1m"],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                finish_reason=None,  # Could be extracted from response
                response_time_ms=response_time_ms,
                extra_metadata={
                    "role": self.config.role,
                    "specialization": self.config.specialization,
                    "session_id": self.agent.session_id,
                    "framework": "agno",
                },
            )

            # Add to database
            db.add(cost_entry)
            await db.commit()

            logger.info(
                f"Tracked LLM cost: {self.config.llm_provider.value}/{self.config.llm_model} "
                f"- {total_tokens} tokens = ${cost_data['total_cost_usd']:.6f}"
            )

        except Exception as e:
            logger.error(f"Failed to track LLM cost: {e}", exc_info=True)
            # Don't raise - cost tracking failures shouldn't break agent execution
            try:
                await db.rollback()
            except Exception:
                pass

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

    # ============================================================================
    # Task Spawning Methods (Stream B: Agent Task Spawning Interface)
    # ============================================================================
    
    async def spawn_investigation_task(
        self,
        db: Any,  # AsyncSession
        execution_id: UUID,
        title: str,
        description: str,
        rationale: str,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> Any:  # DynamicTask
        """
        Spawn a new investigation phase task.
        
        Investigation tasks are for exploring, analyzing, and discovering.
        Used when agents find opportunities that need investigation.
        
        Example:
            "Analyze auth caching pattern - could apply to 12 other API routes for 40% speedup"
        
        Args:
            db: Database session (AsyncSession)
            execution_id: Parent task execution ID
            title: Task title
            description: Task description
            rationale: Why this task is being created (required for investigation)
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
            
        Raises:
            ValueError: If agent_id not configured or execution_id invalid
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to spawn tasks")
        
        from backend.agents.task_spawning.agent_task_spawner import get_agent_task_spawner
        
        spawner = get_agent_task_spawner()
        
        task = await spawner.spawn_investigation_task(
            db=db,
            agent_id=self.agent_id,
            execution_id=execution_id,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids,
        )
        
        logger.info(
            f"Agent {self._format_agent_name()} spawned investigation task: {task.id} - {title[:50]}"
        )
        
        return task
    
    async def spawn_building_task(
        self,
        db: Any,  # AsyncSession
        execution_id: UUID,
        title: str,
        description: str,
        rationale: Optional[str] = None,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> Any:  # DynamicTask
        """
        Spawn a new building/implementation phase task.
        
        Building tasks are for implementing, building, and creating.
        Used when agents need to implement something discovered or planned.
        
        Example:
            "Implement caching layer for auth routes"
        
        Args:
            db: Database session (AsyncSession)
            execution_id: Parent task execution ID
            title: Task title
            description: Task description
            rationale: Optional reason why this task was created
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
            
        Raises:
            ValueError: If agent_id not configured or execution_id invalid
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to spawn tasks")
        
        from backend.agents.task_spawning.agent_task_spawner import get_agent_task_spawner
        
        spawner = get_agent_task_spawner()
        
        task = await spawner.spawn_building_task(
            db=db,
            agent_id=self.agent_id,
            execution_id=execution_id,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids,
        )
        
        logger.info(
            f"Agent {self._format_agent_name()} spawned building task: {task.id} - {title[:50]}"
        )
        
        return task
    
    async def spawn_validation_task(
        self,
        db: Any,  # AsyncSession
        execution_id: UUID,
        title: str,
        description: str,
        rationale: Optional[str] = None,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> Any:  # DynamicTask
        """
        Spawn a new validation/testing phase task.
        
        Validation tasks are for testing, verifying, and validating.
        Used when agents need to test or verify work.
        
        Example:
            "Test API endpoints with new caching layer"
        
        Args:
            db: Database session (AsyncSession)
            execution_id: Parent task execution ID
            title: Task title
            description: Task description
            rationale: Optional reason why this task was created
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
            
        Raises:
            ValueError: If agent_id not configured or execution_id invalid
        """
        if not self.agent_id:
            raise ValueError("agent_id must be configured to spawn tasks")
        
        from backend.agents.task_spawning.agent_task_spawner import get_agent_task_spawner
        
        spawner = get_agent_task_spawner()
        
        task = await spawner.spawn_validation_task(
            db=db,
            agent_id=self.agent_id,
            execution_id=execution_id,
            title=title,
            description=description,
            rationale=rationale,
            blocking_task_ids=blocking_task_ids,
        )
        
        logger.info(
            f"Agent {self._format_agent_name()} spawned validation task: {task.id} - {title[:50]}"
        )
        
        return task

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
