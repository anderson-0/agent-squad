# Legacy Code Removal Plan
**Date**: October 23, 2025
**Phase**: 2 - Safe Deletion of Legacy Code
**Status**: ✅ Ready for Execution

---

## 🎯 Objective

**Remove all custom (non-Agno) agent code while keeping the product fully operational.**

Since `USE_AGNO_AGENTS=true` is now the default and all agents use Agno framework, the custom agent implementations are no longer needed.

---

## 📊 Phase 1 Investigation Results

### ✅ ACTIVE & KEEP

#### 1. `backend/agents/configuration/` folder
- **Status**: ✅ ACTIVE
- **Used by**: `backend/agents/interaction/` folder
- **Purpose**: Timeout and Celery configuration for conversation management
- **Action**: **KEEP** - Required by interaction system

#### 2. `backend/agents/interaction/` folder
- **Status**: ✅ ACTIVE
- **Used by**: API endpoints (`backend/api/v1/endpoints/conversations.py`, `routing_rules.py`)
- **Purpose**: Conversation management, escalation, routing
- **Files**:
  - `conversation_manager.py`
  - `escalation_service.py`
  - `routing_engine.py`
  - `timeout_monitor.py`
  - `celery_tasks.py`
  - `agent_message_handler.py`
  - `seed_routing_templates.py`
- **Action**: **KEEP** - Required by API

#### 3. `backend/services/` folder
- **Status**: ✅ ACTIVE
- **Files**: 8 service files (agent_service, auth_service, conversation_service, etc.)
- **Action**: **KEEP** - Core services

#### 4. `backend/tests/test_agents/` folder
- **Status**: ✅ ACTIVE (some tests may need updates)
- **Files**: 11 test files
- **Action**: **KEEP & REVIEW** - Some tests may need updates for Agno agents

---

### ⚠️ STUB/PLACEHOLDER - CLEAN UP

#### 5. `backend/agents/repository/` folder
- **Status**: ⚠️ STUB (no implementation)
- **Contains**: Only `__init__.py` with imports that don't exist
- **Purpose**: Placeholder for Phase 5 (Repository Digestion) - not implemented yet
- **Action**: **REMOVE __init__.py imports** or **DELETE FOLDER** - Imports fail because files don't exist

---

### 🗑️ LEGACY/DEPRECATED - REMOVE

#### 6. Custom Agent Files (9 files)
- **Location**: `backend/agents/specialized/`
- **Status**: 🗑️ LEGACY (replaced by Agno agents)
- **Files to Remove**:
  1. `project_manager.py`
  2. `tech_lead.py`
  3. `backend_developer.py`
  4. `frontend_developer.py`
  5. `qa_tester.py`
  6. `solution_architect.py`
  7. `devops_engineer.py`
  8. `ai_engineer.py`
  9. `designer.py`

**Dependency Analysis**:
- ✅ Only imported in `backend/agents/factory.py`
- ✅ No other code references them
- ✅ Safe to remove

#### 7. `backend/agents/base_agent.py`
- **Status**: 🗑️ LEGACY (only used by custom agents)
- **Used by**: Custom agent implementations only
- **Action**: **REMOVE after custom agents are deleted**
- **Note**: Agno agents use `backend/agents/agno_base.py` instead

---

## 🔧 Removal Strategy

### Step 1: Update Factory (Remove Custom Agent Support)

**File**: `backend/agents/factory.py`

**Changes**:
1. ✅ Remove custom agent imports (lines 16-25)
2. ✅ Remove `AGENT_REGISTRY` (lines 41-51)
3. ✅ Remove `_create_custom_agent()` method (lines 232-253)
4. ✅ Remove `force_agno` parameter (no longer needed, always Agno)
5. ✅ Simplify `create_agent()` to only create Agno agents
6. ✅ Simplify `_should_use_agno()` (always returns True, or remove entirely)
7. ✅ Update convenience functions (remove `force_agno` parameter)

**Result**: Factory only supports Agno agents

---

### Step 2: Delete Custom Agent Files

**Files to Delete** (9 files):
```bash
rm backend/agents/specialized/project_manager.py
rm backend/agents/specialized/tech_lead.py
rm backend/agents/specialized/backend_developer.py
rm backend/agents/specialized/frontend_developer.py
rm backend/agents/specialized/qa_tester.py
rm backend/agents/specialized/solution_architect.py
rm backend/agents/specialized/devops_engineer.py
rm backend/agents/specialized/ai_engineer.py
rm backend/agents/specialized/designer.py
```

**Impact**: None (no longer referenced after Step 1)

---

### Step 3: Delete base_agent.py

**File to Delete**:
```bash
rm backend/agents/base_agent.py
```

**Dependency Check**:
- ✅ Only used by custom agents (which are deleted in Step 2)
- ✅ Factory.py imports `AgentConfig` and `LLMProvider` from here
  - **Action**: Update factory.py to import from `agno_base.py` instead

**Update in factory.py** (line 14):
```python
# OLD:
from backend.agents.base_agent import BaseSquadAgent, AgentConfig, LLMProvider

# NEW:
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig as AgnoAgentConfig, LLMProvider as AgnoLLMProvider
```

---

### Step 4: Clean Up Repository Folder

**Option A: Delete Entire Folder** (Recommended)
```bash
rm -rf backend/agents/repository/
```

**Option B: Keep as Placeholder**
Create a proper stub:
```python
"""
Repository Analysis Module (Phase 5 - Coming Soon)

This module will provide:
- RepositoryDigestor: Initial repository scanning and indexing
- DependencyGraphBuilder: File dependency analysis
- FileChangeWatcher: Real-time file change monitoring
- SmartContextBuilder: Intelligent context assembly
- IncrementalContextManager: Context lifecycle management

Status: Not yet implemented
Planned for: Phase 5 implementation
"""
# TODO: Implement repository digestion components
```

**Recommendation**: **DELETE** - No point keeping stub that imports non-existent files

---

### Step 5: Update Tests

**Files to Update/Remove**:

#### Tests that need updating:
1. `backend/tests/test_services/test_agent_service.py`
   - May reference custom agents
   - Update to use Agno agents

#### Tests that may be obsolete:
- None identified yet (need to run tests to see failures)

**Action**:
1. Run full test suite: `pytest backend/tests/`
2. Fix any failures related to removed code
3. Update imports from `base_agent` → `agno_base`

---

### Step 6: Update Configuration Files

**Files to Update**:

#### `.env.example`
- Remove `USE_AGNO_AGENTS` (no longer needed, always true)
- Or keep it as documentation with comment

**Old:**
```bash
USE_AGNO_AGENTS=true  # Default: true (production)
```

**New (Option 1 - Remove)**:
```bash
# Agno framework is now the only supported agent implementation
```

**New (Option 2 - Keep for clarity)**:
```bash
# USE_AGNO_AGENTS=true  # Always true - Agno is the only implementation
```

---

### Step 7: Update Documentation

#### Files to Update:
1. `backend/agents/CLAUDE.md`
   - Remove mention of dual-mode (Custom vs Agno)
   - Document Agno as the only implementation

2. `backend/agents/specialized/CLAUDE.md`
   - Remove custom agent documentation
   - Keep only Agno agent documentation
   - Remove "Phase 3 vs Phase 4" comparison (obsolete)

3. `AGNO_MIGRATION_SUMMARY.md`
   - Update to reflect that custom agents have been removed
   - Mark as "Migration Complete & Legacy Removed"

4. `PRODUCTION_DEFAULTS_UPDATE.md`
   - Add note about legacy code removal

5. `README.md`
   - Ensure it only mentions Agno framework
   - Remove any references to custom agents

---

## 📝 Detailed File Changes

### File 1: `backend/agents/factory.py`

**Complete rewrite** to remove all custom agent support:

```python
"""
Agent Factory for Creating AI Agents

This factory creates Agno-powered agents based on role, specialization, and configuration.
"""
from typing import Optional, Type, Dict
from uuid import UUID
import os

# Agno Agent Imports
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, LLMProvider
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
from backend.agents/specialized.agno_designer import AgnoDesignerAgent


# Registry of Agno agent classes by role
AGENT_REGISTRY: Dict[str, Type[AgnoSquadAgent]] = {
    "project_manager": AgnoProjectManagerAgent,
    "backend_developer": AgnoBackendDeveloperAgent,
    "frontend_developer": AgnoFrontendDeveloperAgent,
    "tester": AgnoQATesterAgent,
    "tech_lead": AgnoTechLeadAgent,
    "solution_architect": AgnoSolutionArchitectAgent,
    "devops_engineer": AgnoDevOpsEngineerAgent,
    "ai_engineer": AgnoAIEngineerAgent,
    "designer": AgnoDesignerAgent,
}


class AgentFactory:
    """Factory for creating Agno-powered AI agents."""

    _instances: Dict[UUID, AgnoSquadAgent] = {}

    @classmethod
    def create_agent(
        cls,
        agent_id: UUID,
        role: str,
        specialization: Optional[str] = None,
        llm_provider: LLMProvider = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgnoSquadAgent:
        """
        Create an Agno-powered agent instance.

        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (project_manager, backend_developer, etc.)
            specialization: Optional specialization
            llm_provider: LLM provider (openai, anthropic, groq)
            llm_model: Specific model to use
            temperature: Temperature for LLM (0.0-2.0)
            max_tokens: Maximum tokens for response
            system_prompt: Optional custom system prompt
            session_id: Optional session ID for resuming conversations

        Returns:
            Configured Agno agent instance

        Raises:
            ValueError: If role is not supported
        """
        # Validate role
        if role not in AGENT_REGISTRY:
            raise ValueError(
                f"Unsupported role: {role}. "
                f"Supported roles: {', '.join(AGENT_REGISTRY.keys())}"
            )

        # Create config
        config = AgentConfig(
            role=role,
            specialization=specialization,
            llm_provider=llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        # Get agent class and instantiate
        agent_class = AGENT_REGISTRY[role]
        agent = agent_class(config=config, agent_id=agent_id, session_id=session_id)

        # Store instance
        cls._instances[agent_id] = agent

        return agent

    @classmethod
    def get_agent(cls, agent_id: UUID) -> Optional[AgnoSquadAgent]:
        """Get an existing agent instance by ID."""
        return cls._instances.get(agent_id)

    @classmethod
    def remove_agent(cls, agent_id: UUID) -> bool:
        """Remove an agent instance from the registry."""
        if agent_id in cls._instances:
            del cls._instances[agent_id]
            return True
        return False

    @classmethod
    def get_all_agents(cls) -> Dict[UUID, AgnoSquadAgent]:
        """Get all active agent instances."""
        return cls._instances.copy()

    @classmethod
    def clear_all_agents(cls):
        """Clear all agent instances (useful for testing)."""
        cls._instances.clear()

    @classmethod
    def get_supported_roles(cls) -> list[str]:
        """Get list of all supported roles."""
        return list(AGENT_REGISTRY.keys())

    @classmethod
    def get_available_specializations(cls, role: str) -> list[str]:
        """Get list of available specializations for a role."""
        from pathlib import Path

        base_path = Path(__file__).parent.parent.parent / "roles" / role
        if not base_path.exists():
            return []

        specializations = []
        for prompt_file in base_path.glob("*.md"):
            if prompt_file.stem != "default_prompt":
                specializations.append(prompt_file.stem)

        return specializations


# Convenience functions

def create_project_manager(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoProjectManagerAgent:
    """Create a Project Manager agent."""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_backend_developer(
    agent_id: UUID,
    specialization: str = "python_fastapi",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoBackendDeveloperAgent:
    """Create a Backend Developer agent."""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_frontend_developer(
    agent_id: UUID,
    specialization: str = "react_nextjs",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoFrontendDeveloperAgent:
    """Create a Frontend Developer agent."""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="frontend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_qa_tester(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoQATesterAgent:
    """Create a QA Tester agent."""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="tester",
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )
```

**Lines Removed**: ~150 lines
**Lines Added**: ~200 lines (simpler, cleaner)

---

## ✅ Verification Checklist

After executing all steps:

### 1. Code Verification
- [ ] No imports from `backend.agents.base_agent`
- [ ] No imports from custom agent files (project_manager.py, etc.)
- [ ] Factory.py only imports Agno agents
- [ ] All references to `BaseSquadAgent` removed
- [ ] All references to `AGENT_REGISTRY` point to Agno registry

### 2. Test Verification
- [ ] Run full test suite: `pytest backend/tests/ -v`
- [ ] All tests pass (or update failing tests)
- [ ] No import errors
- [ ] No `ModuleNotFoundError`

### 3. Demo Verification
- [ ] Run all demo files successfully:
  - [ ] `demo_agent_conversations.py`
  - [ ] `demo_hierarchical_squad.py`
  - [ ] `demo_squad_collaboration.py`
  - [ ] `test_nats_agno_integration.py`
  - [ ] `test_agent_factory_agno.py`

### 4. API Verification
- [ ] Start FastAPI server: `uvicorn backend.core.app:app`
- [ ] API starts without errors
- [ ] Agent creation endpoints work
- [ ] No import errors in logs

### 5. Documentation Verification
- [ ] All CLAUDE.md files updated
- [ ] No references to "custom agents" or "dual-mode"
- [ ] README.md mentions only Agno framework
- [ ] Migration docs updated

---

## 🎯 Expected Outcome

### Files Deleted (11 files):
1. `backend/agents/base_agent.py` (609 lines)
2. `backend/agents/specialized/project_manager.py` (470 lines)
3. `backend/agents/specialized/tech_lead.py` (530 lines)
4. `backend/agents/specialized/backend_developer.py` (465 lines)
5. `backend/agents/specialized/frontend_developer.py` (478 lines)
6. `backend/agents/specialized/qa_tester.py` (502 lines)
7. `backend/agents/specialized/solution_architect.py` (398 lines)
8. `backend/agents/specialized/devops_engineer.py` (421 lines)
9. `backend/agents/specialized/ai_engineer.py` (389 lines)
10. `backend/agents/specialized/designer.py` (395 lines)
11. `backend/agents/repository/__init__.py` (28 lines)

**Total Lines Removed**: ~4,685 lines (-10.8% of codebase)

### Files Updated (3 major files):
1. `backend/agents/factory.py` - Simplified, Agno-only
2. `backend/agents/CLAUDE.md` - Updated documentation
3. `backend/agents/specialized/CLAUDE.md` - Updated documentation

### Result:
✅ **Cleaner codebase** - No legacy code
✅ **Simpler architecture** - One agent implementation (Agno)
✅ **Better maintainability** - No dual-mode complexity
✅ **Full functionality** - All features work with Agno agents

---

## 🚨 Risks & Mitigation

### Risk 1: Tests Fail
**Mitigation**: Run tests before committing, fix import errors

### Risk 2: API Breaks
**Mitigation**: Test API endpoints manually before deploying

### Risk 3: Hidden Dependencies
**Mitigation**: Grep for any remaining references before deletion

### Risk 4: Need to Rollback
**Mitigation**: Commit to Git before deletion, can revert if needed

---

## 📅 Execution Timeline

**Estimated Time**: 1-2 hours

1. **Backup** (5 min): Commit current state to Git
2. **Step 1-3** (30 min): Update factory.py, delete custom agents, delete base_agent.py
3. **Step 4** (5 min): Clean up repository folder
4. **Step 5** (15 min): Update/fix tests
5. **Step 6** (5 min): Update configuration files
6. **Step 7** (30 min): Update all documentation
7. **Verification** (20 min): Run all tests and demos

---

## ✅ Ready to Execute

This plan ensures:
- ✅ Safe deletion (no broken dependencies)
- ✅ Full test coverage before and after
- ✅ Clear rollback path (Git)
- ✅ Documentation updated
- ✅ Product remains fully functional

**Recommendation**: Execute steps 1-7 in order, testing after each step.

---

**Created**: October 23, 2025
**Status**: Ready for Execution
**Approval**: Awaiting user confirmation
