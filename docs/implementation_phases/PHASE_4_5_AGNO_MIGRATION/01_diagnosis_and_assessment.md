# Phase 4.5: Agno Framework Migration
## Part 1: Diagnosis and Assessment

> **Status:** Migration Planning
> **Duration:** 1.5-2 weeks
> **Priority:** High - Foundation for future development

---

## 📊 Executive Summary

### Current State
We built a custom agent framework from scratch with ~2,000 lines of code across 43 files. While functional, it requires ongoing maintenance and lacks the ecosystem benefits of an established framework.

### Desired State
Migrate to [Agno](https://github.com/agno-agi/agno) - a battle-tested, high-performance multi-agent framework with persistent memory, built-in tools, and extensive integrations.

### Why Migrate Now?
1. **Before Phase 5:** Repository digestion will benefit from Agno's built-in memory and context management
2. **Reduce Maintenance:** ~2,000 lines of custom code → Framework handles it
3. **Better Performance:** Agno is significantly faster (3μs instantiation vs our current milliseconds)
4. **Ecosystem:** Access to 100+ built-in toolkits and 20+ vector stores
5. **Future-Proof:** Active development and community support

---

## 🔍 Current Architecture Diagnosis

### 1. Agent Foundation (`base_agent.py`)

**Current Implementation:** 909 lines of custom code

```python
class BaseSquadAgent(ABC):
    """Custom base class for all AI agents"""

    def __init__(self, config: AgentConfig, mcp_client=None):
        self.config = config
        self.conversation_history = []  # In-memory only
        self.token_usage = {}
        self.mcp_client = mcp_client
        self.llm_client = self._init_llm_client()  # Manual LLM setup
```

**What It Provides:**
- ✅ Multi-LLM support (OpenAI, Anthropic, Groq)
- ✅ Conversation history (in-memory only)
- ✅ Token tracking
- ✅ MCP tool integration
- ✅ Streaming responses
- ⚠️ No persistent memory
- ⚠️ No persistent conversation history
- ⚠️ Manual context management
- ⚠️ Limited tool ecosystem

**Impact:** HIGH - This is the foundation for all 9 specialized agents

---

### 2. Specialized Agents (9 files)

**Agents Affected:**
1. `project_manager.py` (461 lines)
2. `tech_lead.py` (449 lines)
3. `backend_developer.py` (468 lines)
4. `frontend_developer.py` (463 lines)
5. `qa_tester.py` (441 lines)
6. `solution_architect.py` (276 lines)
7. `devops_engineer.py` (268 lines)
8. `ai_engineer.py` (252 lines)
9. `designer.py` (245 lines)

**Total:** 3,323 lines

**Current Pattern:**
```python
class ProjectManagerAgent(BaseSquadAgent):
    def get_capabilities(self) -> List[str]:
        return ["receive_webhook_notification", "delegate_to_team", ...]

    async def receive_webhook_notification(self, ticket, webhook_event):
        # Uses self.process_message() from BaseSquadAgent
        response = await self.process_message(
            message=f"Review this ticket: {ticket}",
            context={"ticket": ticket, "event": webhook_event}
        )
        return response
```

**Impact:** HIGH - All specialized agents must be updated

---

### 3. Agent Factory (`factory.py`)

**Current Implementation:** 248 lines

```python
class AgentFactory:
    _agents: Dict[str, BaseSquadAgent] = {}  # In-memory registry

    @staticmethod
    def create_agent(agent_id, role, llm_provider, ...):
        # Manual agent instantiation
        agent_class = AGENT_REGISTRY.get(role)
        config = AgentConfig(...)
        agent = agent_class(config, mcp_client)
        AgentFactory._agents[str(agent_id)] = agent
        return agent
```

**Impact:** MEDIUM - Factory must work with Agno agents

---

### 4. Communication Layer (5 files)

**Files:**
- `message_bus.py` (328 lines) - Pub/sub message routing
- `protocol.py` (87 lines) - Message schemas
- `history_manager.py` (195 lines) - Conversation persistence
- `nats_message_bus.py` (285 lines) - NATS integration
- `message_utils.py` (149 lines) - Utilities

**Total:** 1,044 lines

**Current Pattern:**
```python
class MessageBus:
    async def send_message(self, sender_id, recipient_id, content, message_type):
        # Custom routing logic
        # Stores in database
        # Broadcasts via SSE
```

**Integration Point:** Agents use message bus for inter-agent communication

**Impact:** MEDIUM - Must integrate with Agno's agent communication

---

### 5. Context Management (3 files)

**Files:**
- `context_manager.py` (412 lines) - Aggregates context from all sources
- `rag_service.py` (256 lines) - Vector search (Pinecone)
- `memory_store.py` (178 lines) - Short-term memory (Redis)

**Total:** 846 lines

**Current Pattern:**
```python
class ContextManager:
    async def build_context_for_implementation(self, agent_id, task, squad_id):
        # Manually aggregates:
        # - RAG results
        # - Memory
        # - Conversation history
        # - Task details
        return context_dict
```

**Agno Equivalent:** Agno has built-in memory and dynamic context injection

**Impact:** MEDIUM - Can leverage Agno's context features, but need custom RAG

---

### 6. Collaboration Patterns (4 files)

**Files:**
- `patterns.py` (175 lines) - Pattern manager
- `problem_solving.py` (268 lines) - Collaborative Q&A
- `code_review.py` (315 lines) - Code review cycles
- `standup.py` (292 lines) - Daily standups

**Total:** 1,050 lines

**Current Pattern:**
```python
class ProblemSolvingPattern:
    async def solve_problem_collaboratively(self, asker_id, question, relevant_roles):
        # Broadcasts question
        # Collects answers
        # Synthesizes solution
```

**Impact:** LOW - These are high-level patterns that can work with any agent implementation

---

### 7. Orchestration (3 files)

**Files:**
- `orchestrator.py` (487 lines) - Main orchestration
- `workflow_engine.py` (318 lines) - State machine
- `delegation_engine.py` (236 lines) - Task delegation

**Total:** 1,041 lines

**Impact:** LOW - Orchestration is agent-agnostic

---

### 8. Interaction Layer (8 files)

**Files:** Message handlers, routing, escalation, timeouts, Celery tasks

**Total:** ~800 lines

**Impact:** LOW - Interaction layer uses agents via factory

---

## 📈 Impact Analysis

### Files Requiring Changes

| Category | Files | Lines | Impact | Migration Effort |
|----------|-------|-------|--------|------------------|
| **Core Agent** | 1 | 909 | 🔴 Critical | 3 days |
| **Specialized Agents** | 9 | 3,323 | 🔴 Critical | 4 days |
| **Factory** | 1 | 248 | 🟡 High | 1 day |
| **Context Management** | 3 | 846 | 🟡 High | 2 days |
| **Communication** | 5 | 1,044 | 🟡 Medium | 2 days |
| **Collaboration** | 4 | 1,050 | 🟢 Low | 1 day |
| **Orchestration** | 3 | 1,041 | 🟢 Low | 0.5 days |
| **Interaction** | 8 | ~800 | 🟢 Low | 0.5 days |
| **API Endpoints** | ~10 | ~500 | 🟢 Low | 1 day |
| **Tests** | ~20 | ~1,500 | 🟡 Medium | 2 days |
| **TOTAL** | **64** | **~11,261** | | **17 days** |

### Breakdown by Priority

**🔴 Critical (Must Change):**
- `base_agent.py`
- All 9 specialized agent files
- `factory.py`

**🟡 High (Significant Changes):**
- Context management (integrate with Agno memory)
- Communication layer (adapt to Agno agents)
- Test suite (update for new framework)

**🟢 Low (Minor Changes):**
- Collaboration patterns (mostly unchanged)
- Orchestration (agent-agnostic)
- API endpoints (use factory, no direct agent access)

---

## 🎯 Agno Framework Capabilities

### What Agno Provides Out-of-the-Box

#### 1. Agent Creation
```python
from agno import Agent
from agno.models import Claude

agno_agent = Agent(
    name="Project Manager",
    role="Orchestrate software development squad",
    model=Claude(id="claude-sonnet-4"),
    tools=[...],  # MCP tools
    add_history_to_context=True,  # Auto-includes conversation history
    db=SqliteDb(db_file="agno.db"),  # Persistent storage
    culture=shared_culture  # Collective memory across agents
)
```

**vs Our Current:**
```python
agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    llm_provider="anthropic",
    llm_model="claude-3-sonnet-20240229"
)
```

#### 2. Built-In Features

| Feature | Agno | Our Custom | Benefit |
|---------|------|------------|---------|
| **Persistent Memory** | ✅ Built-in | ❌ Redis + custom | Auto-managed |
| **Conversation History** | ✅ Built-in | ⚠️ In-memory only | Persisted across sessions |
| **Multi-Model Support** | ✅ 20+ models | ⚠️ 3 models | More options |
| **Tool Integration** | ✅ 100+ toolkits | ⚠️ MCP only | Broader ecosystem |
| **Vector Stores** | ✅ 20+ stores | ⚠️ Pinecone only | Flexibility |
| **Performance** | ✅ 3μs instantiation | ⚠️ Milliseconds | 100x faster |
| **Memory Footprint** | ✅ 6.6 KiB | ⚠️ Unknown | More efficient |
| **Context Injection** | ✅ Dynamic | ⚠️ Manual | Easier |
| **Human-in-Loop** | ✅ Built-in | ❌ Custom | Better UX |
| **Guardrails** | ✅ Built-in | ❌ None | Security |

#### 3. Multi-Agent Teams

```python
# Agno Team
from agno import Team

team = Team(
    agents=[pm_agent, tech_lead, backend_dev],
    step=False,  # Collaborative mode
    shared_state=True  # Share context
)

# vs Our Current
# Manual message bus orchestration
# Custom squad management
```

#### 4. Persistent Storage

```python
# Agno - Auto-persisted
agent.run("Review this ticket")
# History saved to database automatically

# Our Current - Manual
await message_bus.save_to_database(message)
await history_manager.save_conversation(conversation)
```

---

## 🔄 Migration Complexity Assessment

### Easy Wins (Low Complexity)

1. **Agent Instantiation**
   - Current: `AgentFactory.create_agent()`
   - Agno: `Agent(name=..., model=..., tools=...)`
   - **Complexity:** 🟢 Low (1-2 days)

2. **Tool Integration**
   - Current: Custom MCP client
   - Agno: Built-in MCP support via `tools=[MCPTools(...)]`
   - **Complexity:** 🟢 Low (1 day)

3. **Memory/Context**
   - Current: Manual memory management
   - Agno: `add_history_to_context=True`
   - **Complexity:** 🟢 Low (1-2 days)

### Medium Complexity

1. **Specialized Agent Methods**
   - Current: Custom methods on each agent
   - Agno: Convert to tool functions or prompts
   - **Complexity:** 🟡 Medium (3-4 days)

2. **Message Bus Integration**
   - Current: Custom pub/sub
   - Agno: Adapt to work with Agno agents
   - **Complexity:** 🟡 Medium (2 days)

3. **Context Manager**
   - Current: Custom RAG + memory
   - Agno: Use Agno memory + keep custom RAG
   - **Complexity:** 🟡 Medium (2 days)

### High Complexity

1. **Database Schema Changes**
   - Current: PostgreSQL with custom schema
   - Agno: Needs own tables for sessions, memory, culture
   - **Complexity:** 🔴 High (2-3 days)

2. **Test Suite Updates**
   - Current: Tests assume custom agent structure
   - Agno: Update all agent tests
   - **Complexity:** 🔴 High (2-3 days)

3. **Backward Compatibility**
   - Need migration path for existing conversations
   - Need data migration scripts
   - **Complexity:** 🔴 High (2 days)

---

## 💡 Key Migration Decisions

### Decision 1: Full Migration vs Hybrid

**Option A: Full Migration (Recommended)**
- Replace ALL custom agents with Agno
- Update entire codebase at once
- **Pros:** Clean break, no tech debt
- **Cons:** Longer migration, more risk

**Option B: Hybrid Approach**
- Keep custom agents for some roles
- Use Agno for new agents
- **Pros:** Gradual migration
- **Cons:** Maintain two systems, complexity

**Recommendation:** Full migration - cleaner long-term

---

### Decision 2: Database Strategy

**Option A: Agno-Managed Database**
- Let Agno manage its own tables
- Keep our existing tables for business logic
- **Pros:** Simple, Agno handles complexity
- **Cons:** Two sources of truth

**Option B: Custom Database Integration**
- Extend Agno to use our PostgreSQL schema
- **Pros:** Single source of truth
- **Cons:** Complex, may break Agno updates

**Recommendation:** Option A - Let Agno manage its tables

---

### Decision 3: Conversation History

**Option A: Migrate to Agno**
- Move all conversation history to Agno's format
- **Pros:** Consistent with new system
- **Cons:** Complex migration script

**Option B: Keep Parallel**
- Keep existing history in our tables
- New conversations in Agno
- **Pros:** No migration needed
- **Cons:** Two systems to query

**Recommendation:** Option A for new conversations, keep old history as-is

---

## 📊 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes during migration | High | High | Feature flags, gradual rollout |
| Performance degradation | Low | High | Benchmark before/after |
| Data loss | Low | Critical | Backup database before migration |
| API compatibility issues | Medium | Medium | Update tests, versioning |
| Team learning curve | Medium | Low | Documentation, training |
| Agno bugs/issues | Low | Medium | Active community, fallback plan |

---

## 📅 Estimated Timeline

**Total Duration:** 2-3 weeks (10-15 working days)

### Week 1: Foundation (5 days)
- Day 1: Setup Agno, proof of concept
- Day 2-3: Migrate `base_agent.py` and 1 specialized agent
- Day 4-5: Migrate remaining 8 specialized agents

### Week 2: Integration (5 days)
- Day 6-7: Update factory, context manager, message bus
- Day 8: Update collaboration patterns
- Day 9: Update API endpoints
- Day 10: Update test suite

### Week 3: Stabilization (3-5 days)
- Day 11-12: Integration testing
- Day 13: Performance testing, optimization
- Day 14: Data migration (if needed)
- Day 15: Documentation, training

---

## ✅ Success Criteria

1. **All agents migrated to Agno**
   - ✅ 9 specialized agents use Agno framework
   - ✅ No custom BaseSquadAgent code

2. **Feature Parity**
   - ✅ All existing features work with Agno
   - ✅ No regression in functionality

3. **Performance**
   - ✅ Agent creation ≤ 10ms (vs current ~50ms)
   - ✅ Message processing time unchanged or better
   - ✅ Memory usage reduced

4. **Tests Passing**
   - ✅ All existing tests updated and passing
   - ✅ New Agno-specific tests added
   - ✅ Integration tests passing

5. **Documentation**
   - ✅ Migration guide created
   - ✅ New architecture documented
   - ✅ Team trained on Agno

---

## 🚦 Next Steps

1. Review this diagnosis with team
2. Approve migration plan
3. Create detailed implementation plan (Part 2)
4. Set up development environment with Agno
5. Begin Week 1 implementation

---

> **Navigation:** [Part 2: Migration Strategy →](./02_migration_strategy.md)
