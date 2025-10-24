# Agent Squad - Agents Module

## Overview

The `agents/` module is the core of the Agent Squad system, containing all AI agent implementations, their communication mechanisms, collaboration patterns, context management, and orchestration logic.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agents Module                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌────────────────┐      ┌─────────────┐ │
│  │  Base Agent  │─────▶│ Agent Factory  │─────▶│ Specialized │ │
│  │  (Abstract)  │      │   (Registry)   │      │   Agents    │ │
│  └──────────────┘      └────────────────┘      └─────────────┘ │
│         │                                              │         │
│         │                                              │         │
│         ▼                                              ▼         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Communication Layer                          │  │
│  │  - Message Bus (Pub/Sub)                                 │  │
│  │  - Protocol (Message Types)                              │  │
│  │  - History Manager                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                          │                            │
│         ▼                          ▼                            │
│  ┌─────────────┐          ┌──────────────┐                    │
│  │   Context   │          │ Orchestration │                    │
│  │  Management │          │   & Workflow  │                    │
│  │             │          │               │                    │
│  │ - RAG       │          │ - Orchestrator│                    │
│  │ - Memory    │          │ - Workflow    │                    │
│  │ - Context   │          │ - Delegation  │                    │
│  └─────────────┘          └──────────────┘                    │
│         │                          │                            │
│         └────────────┬─────────────┘                            │
│                      ▼                                          │
│            ┌──────────────────┐                                │
│            │  Collaboration   │                                │
│            │    Patterns      │                                │
│            │                  │                                │
│            │ - Problem Solving│                                │
│            │ - Code Review    │                                │
│            │ - Standup        │                                │
│            └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files

### `agno_base.py`

**Purpose**: Foundation for all AI agents using the Agno framework (enterprise-grade).

**Key Components**:
- `AgnoSquadAgent` (Abstract Base Class): Base class that all specialized agents inherit from
- `AgentConfig`: Configuration for agents (role, LLM provider, model, temperature, etc.)
- `ConversationMessage`: Single message in a conversation
- `AgentResponse`: Response from an agent with content, thinking, action items
- `ToolCall` & `ToolResult`: MCP (Model Context Protocol) tool integration

**Agno Framework Features**:
- ✅ **Persistent Sessions**: Sessions stored in PostgreSQL, survive restarts
- ✅ **Built-in Memory**: Agno manages conversation history automatically
- ✅ **Session Resumption**: Resume conversations by passing `session_id`
- ✅ **Production-Ready**: Battle-tested framework with proven architecture

**LLM Provider Support**:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Groq (Llama, Mixtral)

**Key Methods**:
- `process_message()`: Main entry point for processing user messages
- `send_message()`: Send message to another agent via message bus
- `broadcast_message()`: Broadcast message to all agents
- `get_capabilities()`: Abstract method implemented by each agent
- `execute_tool()`: Execute MCP tools (Git, Jira, etc.)

**Business Rules**:
1. All agents must implement `get_capabilities()` method
2. System prompts are loaded from `roles/{role}/{specialization}.md` files
3. Sessions are lazy-loaded (created on first `process_message()` call)
4. Token usage is tracked per agent
5. Conversation history is automatically persisted by Agno
6. Tool execution is limited to max 5 iterations to prevent loops

**Location**: `/backend/agents/agno_base.py:1`

---

### `factory.py`

**Purpose**: Factory pattern for creating and managing AI agent instances.

**Key Components**:
- `AgentFactory`: Static factory class
- `AGENT_REGISTRY`: Dictionary mapping roles to agent classes

**Supported Roles** (All Agno-Powered):
- `project_manager`: AgnoProjectManagerAgent
- `backend_developer`: AgnoBackendDeveloperAgent
- `frontend_developer`: AgnoFrontendDeveloperAgent
- `tester`: AgnoQATesterAgent
- `tech_lead`: AgnoTechLeadAgent
- `solution_architect`: AgnoSolutionArchitectAgent
- `devops_engineer`: AgnoDevOpsEngineerAgent
- `ai_engineer`: AgnoAIEngineerAgent
- `designer`: AgnoDesignerAgent

**Key Methods**:
- `create_agent()`: Create a new agent instance
- `get_agent()`: Retrieve existing agent by ID
- `remove_agent()`: Remove agent from registry
- `get_supported_roles()`: Get list of all supported roles
- `get_available_specializations()`: Get specializations for a role

**Business Rules**:
1. Each agent instance is tracked by UUID
2. Agents are singleton per UUID (one instance per ID)
3. System prompts can be overridden with custom prompts
4. Default temperature is 0.7, default provider is OpenAI
5. Agents are stored in memory (can be upgraded to Redis/DB)

**Location**: `/backend/agents/factory.py:1`

---

## Module Structure

```
agents/
├── CLAUDE.md                    # This file
├── __init__.py                  # Module initialization
├── agno_base.py                 # Agno base agent class (enterprise-grade)
├── factory.py                   # Agent factory (Agno-only, 331 lines)
│
├── specialized/                 # Specialized Agno agent implementations
│   ├── CLAUDE.md
│   ├── agno_project_manager.py       # PM agent - orchestrates squad
│   ├── agno_tech_lead.py             # TL agent - technical decisions
│   ├── agno_backend_developer.py     # Backend dev agent
│   ├── agno_frontend_developer.py    # Frontend dev agent
│   ├── agno_qa_tester.py             # QA agent
│   ├── agno_solution_architect.py    # Architect agent
│   ├── agno_devops_engineer.py       # DevOps agent
│   ├── agno_ai_engineer.py           # AI/ML engineer agent
│   └── agno_designer.py              # Designer agent
│
├── communication/               # Agent-to-agent communication
│   ├── CLAUDE.md
│   ├── message_bus.py           # Central message routing
│   ├── protocol.py              # Message types & schemas
│   └── history_manager.py       # Conversation history
│
├── context/                     # Context management & RAG
│   ├── CLAUDE.md
│   ├── context_manager.py       # Aggregates context from all sources
│   ├── rag_service.py           # Vector search (Pinecone)
│   └── memory_store.py          # Short-term memory (Redis)
│
├── orchestration/               # Task orchestration & workflows
│   ├── CLAUDE.md
│   ├── orchestrator.py          # Main orchestration logic
│   ├── workflow_engine.py       # State machine for workflows
│   └── delegation_engine.py     # Task delegation logic
│
└── collaboration/               # Collaboration patterns
    ├── CLAUDE.md
    ├── patterns.py              # Pattern manager
    ├── problem_solving.py       # Collaborative problem solving
    ├── code_review.py           # Code review pattern
    └── standup.py               # Daily standup pattern
```

## How It Works

### 1. Agent Creation & Initialization

```python
from backend.agents.factory import AgentFactory
from uuid import uuid4

# Create a project manager agent
agent_id = uuid4()
pm_agent = AgentFactory.create_agent(
    agent_id=agent_id,
    role="project_manager",
    llm_provider="anthropic",
    llm_model="claude-3-sonnet-20240229",
    temperature=0.7
)

# System prompt is automatically loaded from:
# /roles/project_manager/default_prompt.md
```

### 2. Processing Messages

```python
# Simple message processing
response = await pm_agent.process_message(
    message="Review this ticket and create a plan",
    context={
        "ticket": ticket_data,
        "project": project_info
    }
)

print(response.content)  # Agent's response
print(response.thinking) # Agent's reasoning (if available)
print(response.action_items) # Extracted action items
```

### 3. Tool Execution (MCP Integration)

```python
# Process message with automatic tool execution
response = await pm_agent.process_message_with_tools(
    message="Create a new branch for this feature",
    context={"feature_name": "user-authentication"},
    max_tool_iterations=5
)

# Agent will automatically:
# 1. Determine which tool to use (git)
# 2. Call the tool with appropriate arguments
# 3. Process the result
# 4. Continue or provide final response
```

### 4. Multi-Agent Collaboration

Agents communicate via the **Message Bus** (Pub/Sub pattern):

```python
from backend.agents.communication.message_bus import get_message_bus

message_bus = get_message_bus()

# Agent A sends message to Agent B
await message_bus.send_message(
    sender_id=agent_a_id,
    recipient_id=agent_b_id,
    content="Can you review this code?",
    message_type="code_review_request",
    task_execution_id=execution_id
)

# Agent B receives messages
messages = await message_bus.get_messages(agent_b_id)
```

## Business Rules & Constraints

### Agent Lifecycle
1. Agents are created via `AgentFactory.create_agent()`
2. Agents are stored in memory registry by UUID
3. Each agent maintains its own conversation history
4. Agents can be removed from registry with `remove_agent()`

### LLM Provider Configuration
1. Supported providers: OpenAI, Anthropic, Groq
2. API keys must be configured in `backend/core/config.py`
3. Each agent can use a different provider/model
4. Token usage is tracked per agent instance

### System Prompts
1. Prompts are loaded from `/roles/{role}/` directory
2. Specialization prompts take precedence over default
3. Custom prompts can override file-based prompts
4. Prompts are loaded once at agent creation

### Tool Execution (MCP)
1. Agents can execute external tools via MCP protocol
2. Tools are provided by MCP servers (Git, Jira, GitHub, etc.)
3. Tool execution is tracked in `tool_execution_history`
4. Maximum 5 tool iterations per message to prevent loops
5. Tool calls must be in specific JSON format

### Conversation Management
1. Each agent maintains conversation history
2. History is stored in `conversation_history` list
3. History can be cleared with `reset_conversation()`
4. External conversation history can be provided

## Integration Points

### Database Integration
- Agents interact with database via services (not directly)
- `task_execution_service.py` handles task state
- `agent_service.py` handles agent CRUD operations

### Message Bus Integration
- All inter-agent communication goes through message bus
- Message bus supports point-to-point and broadcast
- Messages are persisted and sent via SSE to frontend

### Context Manager Integration
- Agents request context via `ContextManager`
- Context includes RAG results, memory, conversation history
- Different methods for different contexts (ticket review, implementation, code review)

### Orchestration Integration
- `TaskOrchestrator` coordinates multi-agent workflows
- `WorkflowEngine` manages state transitions
- `DelegationEngine` assigns tasks to appropriate agents

## Testing Considerations

When testing agents:
1. Use `AgentFactory.clear_all_agents()` to reset registry
2. Mock MCP client for tool execution tests
3. Provide custom system prompts to avoid file dependencies
4. Track token usage to verify LLM calls
5. Use conversation history to verify multi-turn interactions

## Performance Considerations

1. **Token Usage**: Each LLM call consumes tokens and costs money
2. **Conversation History**: Long conversations increase token usage
3. **Tool Execution**: Tool calls add latency
4. **Message Bus**: In-memory queue (upgrade to Redis for production scale)
5. **Agent Registry**: In-memory storage (upgrade to database for production)

## Future Enhancements

- [ ] Persistent agent state (Redis/Database)
- [ ] Agent memory across sessions
- [ ] Streaming responses for real-time updates
- [ ] Agent performance metrics
- [ ] Cost tracking per agent
- [ ] Multi-modal support (images, files)
- [ ] Agent-to-agent direct communication (no message bus)
- [ ] Agent learning from past interactions

## Related Documentation

- See `specialized/CLAUDE.md` for specialized agent details
- See `communication/CLAUDE.md` for message bus protocol
- See `context/CLAUDE.md` for RAG and context management
- See `orchestration/CLAUDE.md` for workflow orchestration
- See `collaboration/CLAUDE.md` for collaboration patterns

## Common Patterns

### Creating a Custom Agno Agent

```python
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig
from uuid import UUID

class CustomAgent(AgnoSquadAgent):
    def get_capabilities(self) -> List[str]:
        return ["custom_capability_1", "custom_capability_2"]

    async def custom_method(self, data):
        response = await self.process_message(
            message=f"Process this: {data}",
            context={"custom_context": True}
        )
        return response

# Register in factory.py
from backend.agents.factory import AGENT_REGISTRY
AGENT_REGISTRY["custom_role"] = CustomAgent
```

### Error Handling

```python
try:
    response = await agent.process_message(message)
except ValueError as e:
    # Invalid configuration or unsupported provider
    handle_config_error(e)
except Exception as e:
    # LLM API error or tool execution error
    handle_runtime_error(e)
```

## Questions & Troubleshooting

**Q: Agent is not responding?**
- Check LLM API keys in config
- Verify internet connectivity
- Check rate limits on LLM provider

**Q: System prompt not loading?**
- Verify file exists at `/roles/{role}/{specialization}.md`
- Check file permissions
- Provide custom prompt as fallback

**Q: Tool execution failing?**
- Verify MCP client is configured
- Check tool is available in MCP server
- Review tool execution history for errors

**Q: High token usage?**
- Limit conversation history length
- Use smaller models (GPT-3.5 vs GPT-4)
- Reduce context size in prompts
