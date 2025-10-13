"""
Base Agent Class for Agent Squad

This module provides the foundation for all AI agents in the system,
with support for multiple LLM providers (OpenAI, Anthropic, etc.)
"""
from typing import List, Dict, Any, Optional, Literal
from abc import ABC, abstractmethod
import json
from pathlib import Path

from pydantic import BaseModel


# LLM Provider Configurations
LLMProvider = Literal["openai", "anthropic", "groq", "local"]


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    role: str
    specialization: Optional[str] = None
    llm_provider: LLMProvider = "openai"
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: Literal["system", "user", "assistant"]
    content: str
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response from an agent"""
    content: str
    thinking: Optional[str] = None
    action_items: List[str] = []
    metadata: Dict[str, Any] = {}


class BaseSquadAgent(ABC):
    """
    Base class for all AI agents in Agent Squad.

    Provides:
    - Multi-LLM provider support
    - Conversation history management
    - System prompt loading
    - Token usage tracking
    - Structured response handling
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.conversation_history: List[ConversationMessage] = []
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # Load system prompt if not provided
        if not config.system_prompt:
            self.config.system_prompt = self._load_system_prompt()

        # Initialize LLM client
        self.llm_client = self._init_llm_client()

    def _load_system_prompt(self) -> str:
        """
        Load system prompt from file based on role and specialization.

        File path pattern:
        - roles/{role}/{specialization}.md
        - roles/{role}/default_prompt.md
        """
        base_path = Path(__file__).parent.parent.parent / "roles" / self.config.role

        # Try specialization file first
        if self.config.specialization:
            spec_file = base_path / f"{self.config.specialization}.md"
            if spec_file.exists():
                return spec_file.read_text()

        # Fall back to default prompt
        default_file = base_path / "default_prompt.md"
        if default_file.exists():
            return default_file.read_text()

        raise FileNotFoundError(
            f"No prompt file found for role '{self.config.role}' "
            f"with specialization '{self.config.specialization}'"
        )

    def _init_llm_client(self):
        """Initialize the appropriate LLM client based on provider"""
        if self.config.llm_provider == "openai":
            from openai import AsyncOpenAI
            from backend.core.config import settings
            return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        elif self.config.llm_provider == "anthropic":
            from anthropic import AsyncAnthropic
            from backend.core.config import settings
            return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        elif self.config.llm_provider == "groq":
            from groq import AsyncGroq
            from backend.core.config import settings
            return AsyncGroq(api_key=settings.GROQ_API_KEY)

        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> AgentResponse:
        """
        Process a message and return a response.

        Args:
            message: The user message to process
            context: Additional context (e.g., task details, project info, RAG results)
            conversation_history: Optional conversation history to use instead of internal history

        Returns:
            AgentResponse with content and metadata
        """
        # Use provided history or internal history
        history = conversation_history if conversation_history is not None else self.conversation_history

        # Build messages for LLM
        messages = self._build_messages(message, context, history)

        # Call appropriate LLM
        response = await self._call_llm(messages)

        # Update conversation history
        if conversation_history is None:
            self.conversation_history.append(ConversationMessage(role="user", content=message))
            self.conversation_history.append(
                ConversationMessage(role="assistant", content=response.content)
            )

        return response

    def _build_messages(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        history: List[ConversationMessage]
    ) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        messages = []

        # System message
        system_content = self.config.system_prompt
        if context:
            system_content += f"\n\n## Current Context\n{json.dumps(context, indent=2)}"

        messages.append({"role": "system", "content": system_content})

        # Conversation history
        for msg in history:
            if msg.role != "system":  # Skip system messages from history
                messages.append({"role": msg.role, "content": msg.content})

        # Current message
        messages.append({"role": "user", "content": message})

        return messages

    async def _call_llm(self, messages: List[Dict[str, str]]) -> AgentResponse:
        """Call the configured LLM provider"""
        if self.config.llm_provider == "openai":
            return await self._call_openai(messages)
        elif self.config.llm_provider == "anthropic":
            return await self._call_anthropic(messages)
        elif self.config.llm_provider == "groq":
            return await self._call_groq(messages)
        else:
            raise ValueError(f"Unsupported provider: {self.config.llm_provider}")

    async def _call_openai(self, messages: List[Dict[str, str]]) -> AgentResponse:
        """Call OpenAI API"""
        response = await self.llm_client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Update token usage
        if response.usage:
            self.token_usage["prompt_tokens"] += response.usage.prompt_tokens
            self.token_usage["completion_tokens"] += response.usage.completion_tokens
            self.token_usage["total_tokens"] += response.usage.total_tokens

        content = response.choices[0].message.content

        return AgentResponse(
            content=content,
            metadata={
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": self.token_usage.copy()
            }
        )

    async def _call_anthropic(self, messages: List[Dict[str, str]]) -> AgentResponse:
        """Call Anthropic Claude API"""
        # Anthropic requires system message to be separate
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        conversation_messages = [m for m in messages if m["role"] != "system"]

        response = await self.llm_client.messages.create(
            model=self.config.llm_model,
            max_tokens=self.config.max_tokens or 4096,
            temperature=self.config.temperature,
            system=system_message,
            messages=conversation_messages
        )

        # Update token usage
        if response.usage:
            self.token_usage["prompt_tokens"] += response.usage.input_tokens
            self.token_usage["completion_tokens"] += response.usage.output_tokens
            self.token_usage["total_tokens"] += response.usage.input_tokens + response.usage.output_tokens

        content = response.content[0].text

        return AgentResponse(
            content=content,
            metadata={
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": self.token_usage.copy()
            }
        )

    async def _call_groq(self, messages: List[Dict[str, str]]) -> AgentResponse:
        """Call Groq API (OpenAI-compatible)"""
        response = await self.llm_client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Update token usage
        if response.usage:
            self.token_usage["prompt_tokens"] += response.usage.prompt_tokens
            self.token_usage["completion_tokens"] += response.usage.completion_tokens
            self.token_usage["total_tokens"] += response.usage.total_tokens

        content = response.choices[0].message.content

        return AgentResponse(
            content=content,
            metadata={
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": self.token_usage.copy()
            }
        )

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

    def get_conversation_history(self) -> List[ConversationMessage]:
        """Get current conversation history"""
        return self.conversation_history.copy()

    def get_token_usage(self) -> Dict[str, int]:
        """Get token usage statistics"""
        return self.token_usage.copy()

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent has.
        Must be implemented by subclasses.
        """
        pass

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"role={self.config.role} "
            f"provider={self.config.llm_provider} "
            f"model={self.config.llm_model}>"
        )
