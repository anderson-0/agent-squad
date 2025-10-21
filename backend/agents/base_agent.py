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

    def _build_messages(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        history: List[ConversationMessage]
    ) -> List[Dict[str, str]]:
        """Build message list for LLM (enhanced with tool information)"""
        messages = []

        # System message with tools
        system_content = self.config.system_prompt

        # Add tool information if MCP client is available
        if self.has_mcp_client():
            tools_info = self._format_tools_for_prompt()
            if tools_info:
                system_content += f"\n\n{tools_info}"

        # Add context
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
