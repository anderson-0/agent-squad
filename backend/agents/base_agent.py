"""
Base Agent Class for Agent Squad

This module provides the foundation for all AI agents in the system,
with support for multiple LLM providers (OpenAI, Anthropic, etc.)
and MCP (Model Context Protocol) tool integration.
"""
from typing import List, Dict, Any, Optional, Literal
from abc import ABC, abstractmethod
import json
from pathlib import Path
import logging
import asyncio

from pydantic import BaseModel

logger = logging.getLogger(__name__)


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
    tool_calls: List[Dict[str, Any]] = []  # Track tool calls made during response
    metadata: Dict[str, Any] = {}


class ToolCall(BaseModel):
    """Represents a tool call request"""
    tool_name: str
    arguments: Dict[str, Any]
    server_name: str = "git"  # Default to git server


class ToolResult(BaseModel):
    """Result from a tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    tool_name: str
    execution_time: Optional[float] = None


class BaseSquadAgent(ABC):
    """
    Base class for all AI agents in Agent Squad.

    Provides:
    - Multi-LLM provider support
    - Conversation history management
    - System prompt loading
    - Token usage tracking
    - Structured response handling
    - MCP tool integration and execution
    """

    def __init__(self, config: AgentConfig, mcp_client=None):
        self.config = config
        self.conversation_history: List[ConversationMessage] = []
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.mcp_client = mcp_client  # Optional MCP client for tool execution
        self.tool_execution_history: List[ToolResult] = []  # Track all tool executions

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

    async def process_message_streaming(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        on_token: Optional[callable] = None
    ) -> AgentResponse:
        """
        Process a message with streaming response support.

        Args:
            message: The user message to process
            context: Additional context
            conversation_history: Optional conversation history
            on_token: Callback function called for each token (str) -> None

        Returns:
            AgentResponse with complete content
        """
        # Use provided history or internal history
        history = conversation_history if conversation_history is not None else self.conversation_history

        # Build messages for LLM
        messages = self._build_messages(message, context, history)

        # Call appropriate LLM with streaming
        response = await self._call_llm_streaming(messages, on_token)

        # Update conversation history
        if conversation_history is None:
            self.conversation_history.append(ConversationMessage(role="user", content=message))
            self.conversation_history.append(
                ConversationMessage(role="assistant", content=response.content)
            )

        return response

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

    async def _call_llm_streaming(
        self,
        messages: List[Dict[str, str]],
        on_token: Optional[callable] = None
    ) -> AgentResponse:
        """Call the configured LLM provider with streaming support"""
        if self.config.llm_provider == "openai":
            return await self._call_openai_streaming(messages, on_token)
        elif self.config.llm_provider == "anthropic":
            return await self._call_anthropic_streaming(messages, on_token)
        elif self.config.llm_provider == "groq":
            return await self._call_groq_streaming(messages, on_token)
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

    # ===== Streaming Methods =====

    async def _call_openai_streaming(
        self,
        messages: List[Dict[str, str]],
        on_token: Optional[callable] = None
    ) -> AgentResponse:
        """Call OpenAI API with streaming support"""
        full_response = ""
        finish_reason = None
        model_name = None

        stream = await self.llm_client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                # Get token if available
                if hasattr(delta, 'content') and delta.content:
                    token = delta.content
                    full_response += token

                    # Call callback if provided
                    if on_token:
                        try:
                            if asyncio.iscoroutinefunction(on_token):
                                await on_token(token)
                            else:
                                on_token(token)
                        except Exception as e:
                            logger.error(f"Error in on_token callback: {e}")

                # Get finish reason
                if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            # Get model name
            if hasattr(chunk, 'model'):
                model_name = chunk.model

        # Note: Token usage not available in streaming mode for OpenAI
        # Would need to estimate or make separate API call

        return AgentResponse(
            content=full_response,
            metadata={
                "model": model_name or self.config.llm_model,
                "finish_reason": finish_reason,
                "streaming": True,
                "usage": self.token_usage.copy()
            }
        )

    async def _call_anthropic_streaming(
        self,
        messages: List[Dict[str, str]],
        on_token: Optional[callable] = None
    ) -> AgentResponse:
        """Call Anthropic Claude API with streaming support"""
        # Anthropic requires system message to be separate
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        conversation_messages = [m for m in messages if m["role"] != "system"]

        full_response = ""
        stop_reason = None
        input_tokens = 0
        output_tokens = 0

        async with self.llm_client.messages.stream(
            model=self.config.llm_model,
            max_tokens=self.config.max_tokens or 4096,
            temperature=self.config.temperature,
            system=system_message,
            messages=conversation_messages
        ) as stream:
            async for text in stream.text_stream:
                full_response += text

                # Call callback if provided
                if on_token:
                    try:
                        if asyncio.iscoroutinefunction(on_token):
                            await on_token(text)
                        else:
                            on_token(text)
                    except Exception as e:
                        logger.error(f"Error in on_token callback: {e}")

            # Get final message to extract usage
            final_message = await stream.get_final_message()
            if final_message:
                stop_reason = final_message.stop_reason
                if hasattr(final_message, 'usage'):
                    input_tokens = final_message.usage.input_tokens
                    output_tokens = final_message.usage.output_tokens

        # Update token usage
        self.token_usage["prompt_tokens"] += input_tokens
        self.token_usage["completion_tokens"] += output_tokens
        self.token_usage["total_tokens"] += input_tokens + output_tokens

        return AgentResponse(
            content=full_response,
            metadata={
                "model": self.config.llm_model,
                "stop_reason": stop_reason,
                "streaming": True,
                "usage": self.token_usage.copy()
            }
        )

    async def _call_groq_streaming(
        self,
        messages: List[Dict[str, str]],
        on_token: Optional[callable] = None
    ) -> AgentResponse:
        """Call Groq API with streaming support (OpenAI-compatible)"""
        full_response = ""
        finish_reason = None
        model_name = None

        stream = await self.llm_client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                # Get token if available
                if hasattr(delta, 'content') and delta.content:
                    token = delta.content
                    full_response += token

                    # Call callback if provided
                    if on_token:
                        try:
                            if asyncio.iscoroutinefunction(on_token):
                                await on_token(token)
                            else:
                                on_token(token)
                        except Exception as e:
                            logger.error(f"Error in on_token callback: {e}")

                # Get finish reason
                if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            # Get model name
            if hasattr(chunk, 'model'):
                model_name = chunk.model

        return AgentResponse(
            content=full_response,
            metadata={
                "model": model_name or self.config.llm_model,
                "finish_reason": finish_reason,
                "streaming": True,
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

    # ===== MCP Tool Integration Methods =====

    def has_mcp_client(self) -> bool:
        """Check if this agent has an MCP client configured"""
        return self.mcp_client is not None

    def get_available_tools(self, server_name: Optional[str] = None) -> Dict[str, Dict]:
        """
        Get list of available MCP tools.

        Args:
            server_name: Optional server name to filter tools (e.g., "git", "jira")

        Returns:
            Dictionary of available tools with their schemas
        """
        if not self.has_mcp_client():
            return {}

        return self.mcp_client.get_available_tools(server_name)

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: str = "git"
    ) -> ToolResult:
        """
        Execute an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            server_name: Name of the MCP server (default: "git")

        Returns:
            ToolResult with success status and result/error
        """
        if not self.has_mcp_client():
            logger.error("Cannot execute tool: No MCP client configured")
            return ToolResult(
                success=False,
                result=None,
                error="No MCP client configured for this agent",
                tool_name=tool_name
            )

        import time
        start_time = time.time()

        try:
            logger.info(f"Executing tool '{tool_name}' on server '{server_name}' with args: {arguments}")
            result = await self.mcp_client.call_tool(server_name, tool_name, arguments)

            execution_time = time.time() - start_time

            tool_result = ToolResult(
                success=True,
                result=result,
                error=None,
                tool_name=tool_name,
                execution_time=execution_time
            )

            # Track execution
            self.tool_execution_history.append(tool_result)
            logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")

            return tool_result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool execution failed: {tool_name}: {e}")

            tool_result = ToolResult(
                success=False,
                result=None,
                error=str(e),
                tool_name=tool_name,
                execution_time=execution_time
            )

            # Track failed execution
            self.tool_execution_history.append(tool_result)

            return tool_result

    def get_tool_execution_history(self) -> List[ToolResult]:
        """Get history of all tool executions"""
        return self.tool_execution_history.copy()

    def _format_tools_for_prompt(self, server_name: Optional[str] = None) -> str:
        """
        Format available tools as a string for inclusion in system prompt.

        Args:
            server_name: Optional server name to filter tools

        Returns:
            Formatted string describing available tools
        """
        if not self.has_mcp_client():
            return ""

        tools = self.get_available_tools(server_name)
        if not tools:
            return ""

        tool_descriptions = ["## Available Tools\n"]
        tool_descriptions.append("You have access to the following tools:\n")

        for server, server_tools in tools.items():
            if not server_tools:
                continue

            tool_descriptions.append(f"\n### {server.upper()} Tools:\n")
            for tool_name, tool_info in server_tools.items():
                description = tool_info.get("description", "No description")
                tool_descriptions.append(f"- **{tool_name}**: {description}")

                # Add input schema if available
                input_schema = tool_info.get("input_schema")
                if input_schema and "properties" in input_schema:
                    props = input_schema["properties"]
                    if props:
                        tool_descriptions.append(f"  - Parameters: {', '.join(props.keys())}")

        tool_descriptions.append("\n**To use a tool**, respond with a JSON object in this format:")
        tool_descriptions.append('```json')
        tool_descriptions.append('{')
        tool_descriptions.append('  "action": "use_tool",')
        tool_descriptions.append('  "tool": "tool_name",')
        tool_descriptions.append('  "server": "server_name",')
        tool_descriptions.append('  "arguments": {...}')
        tool_descriptions.append('}')
        tool_descriptions.append('```\n')

        return "\n".join(tool_descriptions)

    def _build_contextual_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build system prompt enhanced with conversation context.

        This method creates a more intelligent, role-aware system prompt by:
        - Including the agent's role and specialization
        - Adding question type awareness
        - Noting escalation level (if escalated from lower levels)
        - Formatting context naturally for better LLM understanding

        Args:
            context: Context dictionary from conversation

        Returns:
            Enhanced system prompt string
        """
        prompt_parts = [self.config.system_prompt]

        if not context:
            return self.config.system_prompt

        # Add role-specific context
        agent_role = context.get("agent_role")
        agent_specialization = context.get("agent_specialization")

        if agent_role:
            prompt_parts.append(f"\n## Your Role\nYou are a {agent_role.replace('_', ' ').title()}")
            if agent_specialization and agent_specialization != "default":
                prompt_parts.append(f" specialized in {agent_specialization}")
            prompt_parts.append(".")

        # Add question type context
        question_type = context.get("question_type")
        if question_type:
            type_guidance = {
                "implementation": "Focus on practical implementation details, code examples, and best practices.",
                "architecture": "Focus on system design, scalability, trade-offs, and architectural patterns.",
                "debugging": "Focus on identifying issues, root cause analysis, and debugging strategies.",
                "review": "Focus on code quality, potential bugs, performance, and maintainability.",
                "general": "Provide clear, concise answers appropriate to the question."
            }
            guidance = type_guidance.get(question_type, type_guidance["general"])
            prompt_parts.append(f"\n## Question Type: {question_type.title()}\n{guidance}")

        # Add escalation context
        escalation_level = context.get("escalation_level", 0)
        if escalation_level > 0:
            prompt_parts.append(
                f"\n## Important: Escalated Question (Level {escalation_level})\n"
                "This question was escalated to you because previous responders needed "
                "higher-level expertise. Provide authoritative, expert-level guidance. "
                "If you're uncertain, be honest about limitations rather than guessing."
            )

        # Add conversation state context
        conversation_state = context.get("conversation_state")
        if conversation_state:
            prompt_parts.append(f"\n## Conversation State: {conversation_state}")

        # Add conversation events context (for multi-turn awareness)
        conversation_events = context.get("conversation_events", [])
        if conversation_events and len(conversation_events) > 0:
            prompt_parts.append(
                f"\n## Conversation History\n"
                f"This is part of an ongoing conversation with {len(conversation_events)} previous event(s). "
                "Keep the conversation context in mind when responding."
            )

        # Add any additional relevant context (but format it better than raw JSON)
        conversation_metadata = context.get("conversation_metadata", {})
        if conversation_metadata:
            relevant_metadata = {k: v for k, v in conversation_metadata.items()
                               if k not in ["conversation_id", "agent_role", "agent_specialization",
                                           "question_type", "escalation_level", "conversation_state"]}
            if relevant_metadata:
                prompt_parts.append(f"\n## Additional Context\n{json.dumps(relevant_metadata, indent=2)}")

        return "".join(prompt_parts)

    def _build_messages(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        history: List[ConversationMessage]
    ) -> List[Dict[str, str]]:
        """Build message list for LLM (enhanced with tool information and intelligent context)"""
        messages = []

        # Build enhanced system prompt with context
        system_content = self._build_contextual_prompt(context)

        # Add tool information if MCP client is available
        if self.has_mcp_client():
            tools_info = self._format_tools_for_prompt()
            if tools_info:
                system_content += f"\n\n{tools_info}"

        messages.append({"role": "system", "content": system_content})

        # Conversation history
        for msg in history:
            if msg.role != "system":  # Skip system messages from history
                messages.append({"role": msg.role, "content": msg.content})

        # Current message
        messages.append({"role": "user", "content": message})

        return messages

    async def process_message_with_tools(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        max_tool_iterations: int = 5
    ) -> AgentResponse:
        """
        Process a message with automatic tool execution support.

        This method will:
        1. Send message to LLM
        2. Check if LLM wants to use a tool
        3. Execute tool if requested
        4. Send tool result back to LLM
        5. Repeat until LLM provides final response (up to max_tool_iterations)

        Args:
            message: The user message to process
            context: Additional context
            max_tool_iterations: Maximum number of tool execution iterations

        Returns:
            AgentResponse with final content and metadata including tool calls
        """
        if not self.has_mcp_client():
            # No MCP client, fall back to regular processing
            return await self.process_message(message, context)

        tool_calls_made = []
        iteration = 0

        # Initial message
        current_message = message
        current_context = context or {}

        while iteration < max_tool_iterations:
            iteration += 1

            # Get response from LLM
            response = await self.process_message(current_message, current_context)

            # Check if response contains tool use request
            tool_call = self._parse_tool_call_from_response(response.content)

            if not tool_call:
                # No tool call, return final response
                response.tool_calls = tool_calls_made
                return response

            # Execute tool
            logger.info(f"Iteration {iteration}: Executing tool {tool_call.tool_name}")
            tool_result = await self.execute_tool(
                tool_call.tool_name,
                tool_call.arguments,
                tool_call.server_name
            )

            # Track tool call
            tool_calls_made.append({
                "tool": tool_call.tool_name,
                "server": tool_call.server_name,
                "arguments": tool_call.arguments,
                "success": tool_result.success,
                "result": str(tool_result.result)[:200] if tool_result.result else None,
                "error": tool_result.error
            })

            # Prepare next message with tool result
            if tool_result.success:
                current_message = (
                    f"Tool '{tool_call.tool_name}' executed successfully.\n\n"
                    f"Result:\n{json.dumps(tool_result.result, indent=2)}\n\n"
                    f"Please continue with your task."
                )
            else:
                current_message = (
                    f"Tool '{tool_call.tool_name}' execution failed.\n\n"
                    f"Error: {tool_result.error}\n\n"
                    f"Please try a different approach or report the error."
                )

        # Max iterations reached
        logger.warning(f"Max tool iterations ({max_tool_iterations}) reached")
        return AgentResponse(
            content="Maximum tool execution iterations reached. Please try breaking down your request into smaller steps.",
            tool_calls=tool_calls_made,
            metadata={"max_iterations_reached": True}
        )

    def _parse_tool_call_from_response(self, response_content: str) -> Optional[ToolCall]:
        """
        Parse tool call request from LLM response.

        Looks for JSON blocks with format:
        {
            "action": "use_tool",
            "tool": "tool_name",
            "server": "server_name",
            "arguments": {...}
        }

        Args:
            response_content: The response from the LLM

        Returns:
            ToolCall object if found, None otherwise
        """
        import re

        # Look for JSON code blocks
        json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_pattern, response_content, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and data.get("action") == "use_tool":
                    return ToolCall(
                        tool_name=data.get("tool", ""),
                        arguments=data.get("arguments", {}),
                        server_name=data.get("server", "git")
                    )
            except json.JSONDecodeError:
                continue

        # Also try parsing the entire response as JSON (in case no code block)
        try:
            data = json.loads(response_content)
            if isinstance(data, dict) and data.get("action") == "use_tool":
                return ToolCall(
                    tool_name=data.get("tool", ""),
                    arguments=data.get("arguments", {}),
                    server_name=data.get("server", "git")
                )
        except json.JSONDecodeError:
            pass

        return None

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent has.
        Must be implemented by subclasses.
        """
        pass

    def __repr__(self) -> str:
        mcp_status = "with MCP" if self.has_mcp_client() else "no MCP"
        return (
            f"<{self.__class__.__name__} "
            f"role={self.config.role} "
            f"provider={self.config.llm_provider} "
            f"model={self.config.llm_model} "
            f"{mcp_status}>"
        )
