# Phase 4.5: Agno Migration - Week 2, Day 6-7
## System Integration

> **Goal:** Integrate Agno agents with existing infrastructure
> **Duration:** 2 days (16 hours)
> **Output:** Full system integration with Agno agents

---

## 📋 Day 6-7 Checklist

- [ ] Complete AgentFactory migration
- [ ] Integrate with Context Manager
- [ ] Update Message Bus integration
- [ ] Update Delegation Engine
- [ ] Update Orchestrator
- [ ] Test end-to-end workflows
- [ ] Document integration patterns

---

## 🏭 Part 1: Complete AgentFactory (Day 6, 3 hours)

### 1.1 Feature Flags for Gradual Rollout

```python
# backend/core/config.py (UPDATE)
"""
Configuration - Add Agno feature flag
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings

    # Agno Migration
    USE_AGNO_AGENTS: bool = True  # Global flag to enable/disable Agno
    AGNO_ENABLED_ROLES: list[str] = [
        "project_manager",
        "tech_lead",
        "backend_developer",
        "frontend_developer",
        "tester",
        "solution_architect",
        "devops_engineer",
        "ai_engineer",
        "designer",
    ]  # Which roles use Agno (allows gradual rollout)

    class Config:
        env_file = ".env"


settings = Settings()
```

### 1.2 Enhanced AgentFactory

```python
# backend/agents/factory.py (COMPLETE UPDATE)
"""
Agent Factory - Production-ready with feature flags
"""
from typing import Dict, Optional, Union
from uuid import UUID
import logging

from backend.core.config import settings
from backend.agents.base_agent import BaseSquadAgent, AgentConfig as CustomConfig
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig as AgnoConfig

# Import all agents
from backend.agents.specialized.project_manager import ProjectManagerAgent
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
# ... (import all other agents)

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating AI agents.

    Supports both custom and Agno agents with feature flags
    for gradual rollout and A/B testing.
    """

    _agents: Dict[str, Union[BaseSquadAgent, AgnoSquadAgent]] = {}

    @staticmethod
    def create_agent(
        agent_id: UUID,
        role: str,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        specialization: Optional[str] = None,
        system_prompt: Optional[str] = None,
        mcp_client=None,
        force_agno: Optional[bool] = None,  # Override feature flag
        session_id: Optional[str] = None,
    ) -> Union[BaseSquadAgent, AgnoSquadAgent]:
        """
        Create an agent instance.

        Args:
            agent_id: Unique identifier
            role: Agent role
            llm_provider: LLM provider (openai, anthropic, groq)
            llm_model: LLM model name
            temperature: Temperature (0.0-1.0)
            specialization: Optional specialization
            system_prompt: Optional custom system prompt
            mcp_client: Optional MCP client for tool execution
            force_agno: Force use of Agno (overrides feature flag)
            session_id: Optional session ID for Agno agent resumption

        Returns:
            Agent instance (BaseSquadAgent or AgnoSquadAgent)

        Raises:
            ValueError: If role is not supported
        """
        # Determine whether to use Agno
        use_agno = AgentFactory._should_use_agno(role, force_agno)

        logger.info(
            f"Creating agent: {role} (id={agent_id}, framework={'Agno' if use_agno else 'Custom'})"
        )

        if use_agno:
            agent = AgentFactory._create_agno_agent(
                agent_id=agent_id,
                role=role,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature,
                specialization=specialization,
                system_prompt=system_prompt,
                mcp_client=mcp_client,
                session_id=session_id,
            )
        else:
            agent = AgentFactory._create_custom_agent(
                agent_id=agent_id,
                role=role,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature,
                specialization=specialization,
                system_prompt=system_prompt,
                mcp_client=mcp_client,
            )

        # Store agent
        AgentFactory._agents[str(agent_id)] = agent

        logger.info(f"Agent created successfully: {agent}")

        return agent

    @staticmethod
    def _should_use_agno(role: str, force_agno: Optional[bool]) -> bool:
        """Determine if Agno should be used for this agent"""
        # Explicit override
        if force_agno is not None:
            return force_agno

        # Feature flag disabled globally
        if not settings.USE_AGNO_AGENTS:
            return False

        # Check if role is in enabled list
        return role in settings.AGNO_ENABLED_ROLES

    @staticmethod
    def _create_agno_agent(
        agent_id: UUID,
        role: str,
        llm_provider: str,
        llm_model: str,
        temperature: float,
        specialization: Optional[str],
        system_prompt: Optional[str],
        mcp_client,
        session_id: Optional[str],
    ) -> AgnoSquadAgent:
        """Create Agno agent"""
        from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
        from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
        from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
        from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
        from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
        from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
        from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
        from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
        from backend.agents.specialized.agno_designer import AgnoDesignerAgent

        AGNO_REGISTRY = {
            "project_manager": AgnoProjectManagerAgent,
            "tech_lead": AgnoTechLeadAgent,
            "backend_developer": AgnoBackendDeveloperAgent,
            "frontend_developer": AgnoFrontendDeveloperAgent,
            "tester": AgnoQATesterAgent,
            "solution_architect": AgnoSolutionArchitectAgent,
            "devops_engineer": AgnoDevOpsEngineerAgent,
            "ai_engineer": AgnoAIEngineerAgent,
            "designer": AgnoDesignerAgent,
        }

        agent_class = AGNO_REGISTRY.get(role)
        if not agent_class:
            raise ValueError(f"No Agno agent found for role: {role}")

        config = AgnoConfig(
            role=role,
            specialization=specialization,
            llm_provider=llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            system_prompt=system_prompt
        )

        return agent_class(
            config=config,
            mcp_client=mcp_client,
            session_id=session_id
        )

    @staticmethod
    def _create_custom_agent(
        agent_id: UUID,
        role: str,
        llm_provider: str,
        llm_model: str,
        temperature: float,
        specialization: Optional[str],
        system_prompt: Optional[str],
        mcp_client,
    ) -> BaseSquadAgent:
        """Create custom agent (backward compatibility)"""
        from backend.agents.specialized.project_manager import ProjectManagerAgent
        from backend.agents.specialized.tech_lead import TechLeadAgent
        # ... import other custom agents

        CUSTOM_REGISTRY = {
            "project_manager": ProjectManagerAgent,
            "tech_lead": TechLeadAgent,
            # ... other custom agents
        }

        agent_class = CUSTOM_REGISTRY.get(role)
        if not agent_class:
            raise ValueError(f"No custom agent found for role: {role}")

        config = CustomConfig(
            role=role,
            specialization=specialization,
            llm_provider=llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            system_prompt=system_prompt
        )

        return agent_class(config=config, mcp_client=mcp_client)

    @staticmethod
    def get_agent(agent_id: UUID) -> Optional[Union[BaseSquadAgent, AgnoSquadAgent]]:
        """Get existing agent by ID"""
        return AgentFactory._agents.get(str(agent_id))

    @staticmethod
    def remove_agent(agent_id: UUID):
        """Remove agent from registry"""
        agent_id_str = str(agent_id)
        if agent_id_str in AgentFactory._agents:
            logger.info(f"Removing agent: {agent_id}")
            del AgentFactory._agents[agent_id_str]

    @staticmethod
    def get_all_agents() -> Dict[str, Union[BaseSquadAgent, AgnoSquadAgent]]:
        """Get all active agents"""
        return AgentFactory._agents.copy()

    @staticmethod
    def get_supported_roles() -> list[str]:
        """Get all supported roles"""
        return [
            "project_manager",
            "tech_lead",
            "backend_developer",
            "frontend_developer",
            "tester",
            "solution_architect",
            "devops_engineer",
            "ai_engineer",
            "designer",
        ]

    @staticmethod
    def clear_all_agents():
        """Clear all agents (for testing)"""
        logger.warning("Clearing all agents")
        AgentFactory._agents = {}

    @staticmethod
    def get_agent_stats() -> Dict[str, int]:
        """Get statistics about active agents"""
        agno_count = sum(1 for agent in AgentFactory._agents.values() if isinstance(agent, AgnoSquadAgent))
        custom_count = sum(1 for agent in AgentFactory._agents.values() if isinstance(agent, BaseSquadAgent))

        return {
            "total": len(AgentFactory._agents),
            "agno": agno_count,
            "custom": custom_count,
        }
```

---

## 🧠 Part 2: Context Manager Integration (Day 6, 4 hours)

### 2.1 Update Context Manager for Agno

```python
# backend/agents/context/context_manager.py (UPDATE)
"""
Context Manager - Updated to work with both Custom and Agno agents
"""
from typing import Dict, Any, Optional, Union
from uuid import UUID
import logging

from backend.agents.base_agent import BaseSquadAgent
from backend.agents.agno_base import AgnoSquadAgent
from backend.agents.context.rag_service import RAGService
from backend.agents.context.memory_store import MemoryStore

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Aggregates context from multiple sources for agents.

    Context sources:
    - RAG (vector search for similar code/solutions)
    - Memory (short-term Redis cache)
    - Conversation history (from agent or database)
    - Task details
    - Squad information
    """

    def __init__(
        self,
        rag_service: RAGService,
        memory_store: MemoryStore,
    ):
        self.rag_service = rag_service
        self.memory_store = memory_store

    async def build_context_for_implementation(
        self,
        agent: Union[BaseSquadAgent, AgnoSquadAgent],
        task: Dict[str, Any],
        squad_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Build context for implementation tasks.

        Args:
            agent: Agent instance (Custom or Agno)
            task: Task details
            squad_id: Squad identifier
            task_execution_id: Optional execution ID

        Returns:
            Aggregated context dictionary
        """
        logger.info(f"Building implementation context for task: {task.get('title')}")

        context = {
            "task": task,
            "squad_id": str(squad_id),
            "task_execution_id": str(task_execution_id) if task_execution_id else None,
        }

        # 1. RAG: Similar code and solutions
        if task.get("description"):
            try:
                rag_results = await self.rag_service.search_similar_code(
                    query=task["description"],
                    limit=5
                )
                context["related_code"] = rag_results
            except Exception as e:
                logger.error(f"RAG search failed: {e}")
                context["related_code"] = []

        # 2. Memory: Recent relevant information
        try:
            memory_key = f"task:{task.get('id')}:context"
            memory = await self.memory_store.get(memory_key)
            context["memory"] = memory or {}
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            context["memory"] = {}

        # 3. Conversation history
        # Handle both Custom and Agno agents
        if isinstance(agent, AgnoSquadAgent):
            # Agno: History is automatic, but we can add session info
            context["agent_session_id"] = agent.session_id
            context["agent_framework"] = "agno"
        else:
            # Custom: Get conversation history
            context["conversation_history"] = agent.get_conversation_history()
            context["agent_framework"] = "custom"

        # 4. Agent capabilities
        context["agent_capabilities"] = agent.get_capabilities()

        logger.info(f"Context built: {len(context)} sections")

        return context

    async def build_context_for_review(
        self,
        agent: Union[BaseSquadAgent, AgnoSquadAgent],
        code_changes: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build context for code review tasks"""
        logger.info("Building code review context")

        context = {
            "task": task,
            "code_changes": code_changes[:10000],  # Limit size
        }

        # RAG: Similar code reviews
        try:
            rag_results = await self.rag_service.search_similar_reviews(
                code=code_changes,
                limit=3
            )
            context["similar_reviews"] = rag_results
        except Exception as e:
            logger.error(f"RAG search for reviews failed: {e}")
            context["similar_reviews"] = []

        # Coding standards from memory
        try:
            standards = await self.memory_store.get("coding_standards")
            context["coding_standards"] = standards or {}
        except Exception as e:
            logger.error(f"Failed to get coding standards: {e}")
            context["coding_standards"] = {}

        return context

    async def save_to_memory(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,  # 1 hour default
    ):
        """
        Save information to short-term memory.

        Args:
            key: Memory key
            value: Value to store
            ttl: Time to live in seconds
        """
        try:
            await self.memory_store.set(key, value, ttl=ttl)
            logger.debug(f"Saved to memory: {key}")
        except Exception as e:
            logger.error(f"Failed to save to memory: {e}")

    async def get_from_memory(self, key: str) -> Optional[Any]:
        """
        Retrieve information from short-term memory.

        Args:
            key: Memory key

        Returns:
            Stored value or None
        """
        try:
            value = await self.memory_store.get(key)
            logger.debug(f"Retrieved from memory: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to get from memory: {e}")
            return None
```

---

## 📨 Part 3: Message Bus Integration (Day 6, 3 hours)

### 3.1 Update Message Bus

The Message Bus should work seamlessly with both agent types since it uses agent IDs, not agent instances.

```python
# backend/agents/communication/message_bus.py (VERIFY/UPDATE)
"""
Message Bus - Already compatible with Agno agents

No changes needed if message bus uses agent IDs only.
Verify that it doesn't depend on agent internal structure.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Message Bus for agent-to-agent communication.

    Note: This should be framework-agnostic (works with both Custom and Agno agents).
    """

    async def send_message(
        self,
        sender_id: UUID,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        task_execution_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send message between agents.

        This method doesn't need agent instances, only IDs,
        so it works with both Custom and Agno agents.
        """
        logger.info(
            f"Message: {sender_id} → {recipient_id or 'broadcast'} "
            f"(type: {message_type})"
        )

        # Store in database
        # Broadcast via SSE
        # ... existing implementation

        pass

    async def get_messages(
        self,
        recipient_id: UUID,
        message_type: Optional[str] = None,
        unread_only: bool = True,
    ):
        """
        Get messages for an agent.

        Works with both agent types.
        """
        # ... existing implementation
        pass


# Singleton instance
_message_bus_instance = None


def get_message_bus() -> MessageBus:
    """Get message bus singleton"""
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()
    return _message_bus_instance
```

**Key Point:** Message Bus should be framework-agnostic. As long as it uses agent IDs and doesn't rely on agent internal structure, it works with both Custom and Agno agents!

---

## 🎯 Part 4: Delegation Engine Integration (Day 7, 3 hours)

### 4.1 Update Delegation Engine

```python
# backend/agents/orchestration/delegation_engine.py (UPDATE)
"""
Delegation Engine - Updated to work with both agent types
"""
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import logging

from backend.agents.factory import AgentFactory
from backend.agents.base_agent import BaseSquadAgent
from backend.agents.agno_base import AgnoSquadAgent

logger = logging.getLogger(__name__)


class DelegationEngine:
    """
    Intelligent task delegation to squad members.

    Matches tasks to agents based on:
    - Role requirements
    - Specialization
    - Current workload
    - Past performance
    """

    async def delegate_task(
        self,
        task: Dict[str, Any],
        squad_members: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[UUID]:
        """
        Delegate task to most suitable agent.

        Args:
            task: Task to delegate
            squad_members: Available squad members
            context: Additional context for delegation

        Returns:
            Selected agent ID or None if no suitable agent
        """
        logger.info(f"Delegating task: {task.get('title')}")

        # Find best match
        best_agent_id = self._find_best_agent(task, squad_members)

        if not best_agent_id:
            logger.warning("No suitable agent found for task")
            return None

        # Get agent (works with both Custom and Agno)
        agent = AgentFactory.get_agent(best_agent_id)

        if not agent:
            logger.error(f"Agent not found: {best_agent_id}")
            return None

        # Verify agent has required capabilities
        required_capability = self._get_required_capability(task)
        if required_capability not in agent.get_capabilities():
            logger.warning(
                f"Agent {best_agent_id} lacks capability: {required_capability}"
            )
            return None

        logger.info(f"Task delegated to: {best_agent_id} ({agent.config.role})")

        return best_agent_id

    def _find_best_agent(
        self,
        task: Dict[str, Any],
        squad_members: List[Dict[str, Any]],
    ) -> Optional[UUID]:
        """Find best agent for task"""
        required_role = task.get("required_role", "backend_developer")

        # Find agents with matching role
        candidates = [
            member for member in squad_members
            if member.get("role") == required_role
        ]

        if not candidates:
            logger.warning(f"No agents with role: {required_role}")
            return None

        # For now, return first candidate
        # TODO: Consider workload, performance, specialization
        return candidates[0].get("agent_id")

    def _get_required_capability(self, task: Dict[str, Any]) -> str:
        """Determine required capability for task"""
        task_type = task.get("type", "implementation")

        capability_map = {
            "implementation": "analyze_task",
            "review": "review_code",
            "testing": "create_test_plan",
            "deployment": "manage_deployments",
        }

        return capability_map.get(task_type, "analyze_task")
```

---

## 🎭 Part 5: Orchestrator Integration (Day 7, 3 hours)

### 5.1 Update Orchestrator

```python
# backend/agents/orchestration/orchestrator.py (UPDATE)
"""
Task Orchestrator - Updated to work with Agno agents
"""
from typing import Dict, Any, Optional, Union
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.factory import AgentFactory
from backend.agents.context.context_manager import ContextManager
from backend.agents.orchestration.delegation_engine import DelegationEngine
from backend.agents.orchestration.workflow_engine import WorkflowEngine
from backend.agents.communication.message_bus import get_message_bus
from backend.agents.base_agent import BaseSquadAgent
from backend.agents.agno_base import AgnoSquadAgent

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """
    Orchestrates multi-agent workflows.

    Coordinates:
    - Task delegation
    - Workflow state management
    - Agent collaboration
    - Progress monitoring
    """

    def __init__(
        self,
        context_manager: ContextManager,
        delegation_engine: DelegationEngine,
        workflow_engine: WorkflowEngine,
    ):
        self.context_manager = context_manager
        self.delegation_engine = delegation_engine
        self.workflow_engine = workflow_engine
        self.message_bus = get_message_bus()

    async def orchestrate_task(
        self,
        db: AsyncSession,
        task: Dict[str, Any],
        squad_id: UUID,
        task_execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Orchestrate task execution.

        This works with both Custom and Agno agents because:
        - Uses AgentFactory to get agents
        - Uses agent.get_capabilities() interface
        - Uses Context Manager (framework-agnostic)
        - Uses Message Bus (framework-agnostic)

        Args:
            db: Database session
            task: Task to orchestrate
            squad_id: Squad identifier
            task_execution_id: Execution identifier

        Returns:
            Orchestration result
        """
        logger.info(f"Orchestrating task: {task.get('title')}")

        try:
            # 1. Get PM agent (could be Custom or Agno)
            pm_agent = await self._get_pm_agent(db, squad_id)
            if not pm_agent:
                raise ValueError("Project Manager not found")

            # 2. Build context
            context = await self.context_manager.build_context_for_implementation(
                agent=pm_agent,
                task=task,
                squad_id=squad_id,
                task_execution_id=task_execution_id,
            )

            # 3. PM breaks down task
            breakdown = await pm_agent.break_down_task(
                ticket=task,
                squad_members=[],  # TODO: Get from database
            )

            # 4. Delegate subtasks
            for subtask in breakdown.get("subtasks", []):
                agent_id = await self.delegation_engine.delegate_task(
                    task=subtask,
                    squad_members=[],  # TODO: Get from database
                    context=context,
                )

                if agent_id:
                    # Send task assignment message
                    await self.message_bus.send_message(
                        sender_id=pm_agent.config.role,  # Use role as ID
                        recipient_id=agent_id,
                        content=f"Task assigned: {subtask.get('title')}",
                        message_type="task_assignment",
                        task_execution_id=task_execution_id,
                    )

            return {
                "status": "delegated",
                "breakdown": breakdown,
                "execution_id": str(task_execution_id),
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
            }

    async def _get_pm_agent(
        self,
        db: AsyncSession,
        squad_id: UUID,
    ) -> Optional[Union[BaseSquadAgent, AgnoSquadAgent]]:
        """Get Project Manager agent for squad"""
        # TODO: Query database for PM agent ID
        # For now, assume PM is in factory
        all_agents = AgentFactory.get_all_agents()

        for agent_id, agent in all_agents.items():
            if agent.config.role == "project_manager":
                return agent

        return None
```

---

## ✅ Day 6-7 Completion Checklist

- [ ] AgentFactory completed with feature flags
- [ ] Context Manager integrated
- [ ] Message Bus verified/updated
- [ ] Delegation Engine integrated
- [ ] Orchestrator integrated
- [ ] End-to-end test passing
- [ ] Integration tests created
- [ ] Documentation updated

---

## 🧪 Part 6: Integration Testing (Day 7, 3 hours)

### 6.1 End-to-End Integration Test

```python
# backend/tests/test_agno_integration.py
"""
Integration tests for Agno agents with full system
"""
import pytest
import asyncio
from uuid import uuid4

from backend.agents.factory import AgentFactory
from backend.agents.agno_base import AgentConfig


@pytest.mark.asyncio
async def test_factory_creates_agno_agent():
    """Test factory creates Agno agent when enabled"""
    agent_id = uuid4()

    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider="anthropic",
        llm_model="claude-sonnet-4",
        force_agno=True,  # Force Agno
    )

    assert agent is not None
    assert hasattr(agent, "session_id")  # Agno has session_id
    print(f"✅ Factory created Agno agent: {agent}")


@pytest.mark.asyncio
async def test_factory_feature_flag():
    """Test feature flag controls agent type"""
    from backend.core.config import settings

    agent_id = uuid4()

    # Should use Agno if enabled
    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider="anthropic",
        llm_model="claude-sonnet-4",
    )

    if settings.USE_AGNO_AGENTS and "project_manager" in settings.AGNO_ENABLED_ROLES:
        assert hasattr(agent, "session_id")
        print("✅ Feature flag: Using Agno")
    else:
        assert not hasattr(agent, "session_id")
        print("✅ Feature flag: Using Custom")


@pytest.mark.asyncio
async def test_context_manager_with_agno():
    """Test Context Manager works with Agno agents"""
    from backend.agents.context.context_manager import ContextManager
    from backend.agents.context.rag_service import RAGService
    from backend.agents.context.memory_store import MemoryStore

    # Create mocks
    rag_service = RAGService()  # Mock
    memory_store = MemoryStore()  # Mock
    context_manager = ContextManager(rag_service, memory_store)

    # Create Agno agent
    agent_id = uuid4()
    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        force_agno=True,
    )

    # Build context
    task = {
        "title": "Test task",
        "description": "Test description"
    }
    context = await context_manager.build_context_for_implementation(
        agent=agent,
        task=task,
        squad_id=uuid4(),
    )

    assert context is not None
    assert "agent_framework" in context
    assert context["agent_framework"] == "agno"
    print("✅ Context Manager works with Agno")


@pytest.mark.asyncio
async def test_pm_delegates_to_backend_dev():
    """Test PM can delegate to Backend Dev (both Agno)"""
    pm_id = uuid4()
    dev_id = uuid4()

    # Create PM
    pm = AgentFactory.create_agent(
        agent_id=pm_id,
        role="project_manager",
        force_agno=True,
    )

    # Create Backend Dev
    dev = AgentFactory.create_agent(
        agent_id=dev_id,
        role="backend_developer",
        force_agno=True,
    )

    # PM breaks down task
    ticket = {
        "title": "Add user authentication",
        "description": "Implement JWT-based auth",
        "acceptance_criteria": ["Users can login", "JWT tokens generated"]
    }

    breakdown = await pm.break_down_task(
        ticket=ticket,
        squad_members=[
            {"agent_id": dev_id, "role": "backend_developer"}
        ]
    )

    assert breakdown is not None
    assert "subtasks" in breakdown
    print(f"✅ PM delegated task (breakdown: {len(breakdown.get('subtasks', []))} subtasks)")


if __name__ == "__main__":
    asyncio.run(test_factory_creates_agno_agent())
    asyncio.run(test_factory_feature_flag())
    asyncio.run(test_context_manager_with_agno())
    asyncio.run(test_pm_delegates_to_backend_dev())
```

---

## 📊 Integration Verification

### What Should Work Now

✅ **Agent Creation**
- Factory creates Agno agents when enabled
- Feature flags control rollout
- Both frameworks can coexist

✅ **Context Management**
- Context Manager works with both agent types
- RAG results provided to agents
- Memory (Redis) integrated

✅ **Communication**
- Message Bus sends messages between agents
- Works with agent IDs (framework-agnostic)
- SSE broadcasts work

✅ **Orchestration**
- Orchestrator coordinates workflows
- Delegation Engine assigns tasks
- Workflow state managed

---

## 🚨 Troubleshooting

### Issue: Agent creation fails
```python
# Check feature flags
from backend.core.config import settings
print(f"USE_AGNO_AGENTS: {settings.USE_AGNO_AGENTS}")
print(f"AGNO_ENABLED_ROLES: {settings.AGNO_ENABLED_ROLES}")

# Check factory stats
stats = AgentFactory.get_agent_stats()
print(f"Agent stats: {stats}")
```

### Issue: Context building fails
```python
# Check agent type
print(f"Agent type: {type(agent)}")
print(f"Has session_id: {hasattr(agent, 'session_id')}")

# Check context structure
print(f"Context keys: {context.keys()}")
```

---

## 🎯 Next Steps (Week 2 Remaining)

**Days 8-10:**
- Update Collaboration Patterns
- Update API endpoints
- Update test suite
- Performance testing

---

**End of Day 6-7**

Great integration work! Agno agents now work with the entire system!

**Next:** [Week 2, Day 8-10: Collaboration & API →](./06_week2_day8-10_implementation.md)
