# Phase 3: Agent Framework Integration - Detailed Implementation Plan

## 🎯 Overview

**Timeline**: 2-3 weeks
**Status**: 🔨 In Progress
**Goal**: Build the core AI agent system that powers Agent Squad

This is the **most critical phase** - where we bring AI agents to life and enable them to collaborate on software development tasks.

## ✅ Progress So Far

**Days 1-2 COMPLETE** (Communication System):
- ✅ Message Bus (300 LOC) - Point-to-point & broadcast messaging
- ✅ A2A Protocol (280 LOC) - Structured message handling
- ✅ History Manager (350 LOC) - Conversation storage & retrieval
- ✅ BaseSquadAgent (300 LOC) - Multi-LLM support (OpenAI, Anthropic, Groq)
- ✅ AgentFactory foundation (200 LOC)

**Days 3-4 COMPLETE** (Specialized Agents):
- ✅ ProjectManagerAgent (400 LOC) - Webhook handling, PM+TL collaboration, effort estimation
- ✅ TechLeadAgent (450 LOC) - Technical review, complexity analysis, code review
- ✅ BackendDeveloperAgent (380 LOC) - Implementation planning, code review requests
- ✅ FrontendDeveloperAgent (380 LOC) - Component design, API integration, responsive design
- ✅ QATesterAgent (420 LOC) - Test planning, acceptance criteria verification, QA sign-off

**Days 5-6 COMPLETE** (Context & RAG):
- ✅ ContextManager (370 LOC) - Aggregates context from multiple sources
- ✅ RAGService (500 LOC) - Pinecone integration with namespaces
- ✅ MemoryStore (380 LOC) - Redis short-term memory

**Total**: ~4,910 lines of production code (~60% of Phase 3 complete)

## 🎯 Enhanced Requirements from User

### **Key Additions**:
1. **PM + Tech Lead Collaboration**: Ticket review, effort estimation, complexity analysis
2. **Webhook Integration**: Jira webhooks via Inngest trigger agent workflows
3. **MCP Integration Design**: Prepare interfaces for Phase 4 (Git, Jira, Confluence, Notion, Google Docs)
4. **Unified RAG**: Single Pinecone instance with namespaces for code, tickets, docs, conversations
5. **Effort Estimation**: PM + TL estimate complexity and hours for tasks

---

## 📋 Phase 3 Breakdown

### Week 1: Agent Core Infrastructure (Days 1-7)
### Week 2: Agent Collaboration & Orchestration (Days 8-14)
### Week 3: Testing, Integration & Polish (Days 15-21)

---

## 🗓️ Week 1: Agent Core Infrastructure

### Day 1-2: Foundation & Communication Protocol

#### ✅ Already Complete
- [x] Agent message schemas (A2A protocol)
- [x] BaseSquadAgent class with multi-LLM support
- [x] AgentFactory foundation

#### 🎯 Tasks for Days 1-2

**1. Complete Agent Communication System**
```python
backend/agents/communication/
├── __init__.py
├── message_bus.py       # Central message routing
├── protocol.py          # A2A protocol implementation
└── history_manager.py   # Conversation history tracking
```

**Files to Create:**

**`message_bus.py`** - Central hub for agent-to-agent messages
- In-memory message queue (later can be Redis/RabbitMQ)
- Message routing by recipient ID
- Broadcast messaging support
- Message persistence hooks
- **Lines**: ~200
- **Key Functions**:
  - `send_message(sender_id, recipient_id, message)`
  - `broadcast_message(sender_id, message)`
  - `get_messages(agent_id, since=None)`
  - `subscribe(agent_id, callback)`

**`protocol.py`** - A2A Protocol Implementation
- Parse structured messages (TaskAssignment, StatusUpdate, etc.)
- Validate message format
- Serialize/deserialize messages
- **Lines**: ~150
- **Key Functions**:
  - `parse_message(raw_message) -> MessagePayload`
  - `serialize_message(message_payload) -> str`
  - `validate_message(message) -> bool`

**`history_manager.py`** - Conversation History
- Store conversation history in database
- Retrieve history for context
- Summarization for long conversations
- **Lines**: ~180
- **Key Functions**:
  - `store_message(task_execution_id, message)`
  - `get_conversation_history(task_execution_id, limit=50)`
  - `summarize_conversation(task_execution_id)`

**Deliverables**:
- ✅ Message bus operational
- ✅ A2A protocol working
- ✅ Conversation history stored
- ✅ Unit tests for communication layer

---

### Day 3-4: Specialized Agent Classes

**2. Implement 9 Specialized Agent Types**

```python
backend/agents/specialized/
├── __init__.py
├── project_manager.py      # PM agent (most important)
├── backend_developer.py    # Backend dev agent
├── frontend_developer.py   # Frontend dev agent
├── qa_tester.py           # QA/testing agent
├── tech_lead.py           # Tech lead agent
├── solution_architect.py   # Solution architect agent
├── devops_engineer.py     # DevOps agent
├── ai_engineer.py         # AI/ML engineer agent
└── designer.py            # UI/UX designer agent
```

**Each Agent File Structure** (~150-200 lines each):
```python
class ProjectManagerAgent(BaseSquadAgent):
    """
    Project Manager agent - orchestrates the team
    """

    def get_capabilities(self) -> List[str]:
        """What this agent can do"""
        return [
            "task_analysis",
            "task_breakdown",
            "team_coordination",
            "status_tracking",
            "stakeholder_communication"
        ]

    async def analyze_task(self, task: Task) -> TaskAnalysis:
        """Analyze task and create execution plan"""
        pass

    async def delegate_task(
        self,
        task: Task,
        agent_id: UUID
    ) -> TaskAssignment:
        """Delegate task to team member"""
        pass

    async def check_status(self, task_id: str) -> StatusUpdate:
        """Check status of a task"""
        pass

    async def conduct_standup(
        self,
        squad_members: List[SquadMember]
    ) -> List[Standup]:
        """Conduct async standup"""
        pass
```

**Agent Priorities**:
1. **ProjectManagerAgent** (Day 3) - Most critical
2. **BackendDeveloperAgent** (Day 3)
3. **QATesterAgent** (Day 3)
4. **FrontendDeveloperAgent** (Day 4)
5. **TechLeadAgent** (Day 4)
6. **Remaining agents** (Day 4)

**Deliverables**:
- ✅ 5 specialized agent classes (PM, TL, Backend Dev, Frontend Dev, QA)
- ✅ Each agent has role-specific methods
- ✅ Agents work with A2A protocol
- ✅ PM + Tech Lead collaboration workflow implemented

**Note**: Remaining 4 agents (Solution Architect, DevOps, AI Engineer, Designer) can be added later as needed.

---

### Day 5-6: Context & RAG Integration ✅ COMPLETE

**3. Agent Context Management**

```python
backend/agents/context/
├── __init__.py              ✅
├── context_manager.py       ✅ (370 LOC)
├── rag_service.py          ✅ (500 LOC)
└── memory_store.py         ✅ (380 LOC)
```

**`context_manager.py`** ✅ - Agent Context Management
- Build context from multiple sources (RAG, memory, history, squad metadata)
- Specialized context builders for ticket review, implementation, code review
- Store context in memory and RAG
- **Lines**: 370
- **Key Functions**:
  - `build_context()` - General context building
  - `build_context_for_ticket_review()` - PM + TL collaboration
  - `build_context_for_implementation()` - Developer tasks
  - `build_context_for_code_review()` - Tech Lead review
  - `store_context_in_memory()` - Short-term storage
  - `update_rag_with_conversation()` - Long-term learning
  - `update_rag_with_decision()` - ADR storage

**`rag_service.py`** ✅ - RAG Integration (Pinecone)
- Unified Pinecone index with squad-isolated namespaces
- OpenAI embeddings (text-embedding-3-small)
- Namespace format: {squad_id}:{knowledge_type}
- Knowledge types: code, tickets, docs, conversations, decisions
- **Lines**: 500
- **Key Functions**:
  - `upsert()` - Store documents with embeddings
  - `query()` - Semantic search in namespace
  - `query_multiple_namespaces()` - Parallel queries
  - `delete()`, `delete_namespace()` - Cleanup
  - `index_code_file()` - Index repository code
  - `index_ticket()` - Index Jira tickets
  - `index_document()` - Index Confluence/Notion/Google Docs

**`memory_store.py`** ✅ - Short-term Memory
- Redis-backed working memory
- Agent-specific and task-specific keys
- Automatic TTL expiration
- Specialized memory operations
- **Lines**: 380
- **Key Functions**:
  - `store()`, `get()`, `delete()` - Basic operations
  - `get_all_keys()`, `get_context()` - Bulk retrieval
  - `clear()` - Cleanup
  - `store_decision()`, `get_last_decision()` - Decision tracking
  - `store_task_state()`, `get_task_state()` - State management
  - `store_blockers()`, `add_blocker()`, `get_blockers()` - Blocker tracking
  - `store_implementation_plan()`, `get_implementation_plan()` - Plan storage

**Deliverables**:
- ✅ Context manager working with multi-source aggregation
- ✅ RAG integrated with Pinecone (5 namespaces per squad)
- ✅ Short-term memory operational with Redis
- ✅ Specialized context builders for all workflows

---

### Day 7: Agent Services Layer

**4. Agent Business Logic Services**

```python
backend/services/
├── agent_service.py      # Agent CRUD operations
├── squad_service.py      # Squad management
└── task_execution_service.py  # Task execution logic
```

**`agent_service.py`** - Agent Service Layer
- Create/update/delete agents
- Load agent from database
- Initialize agent with factory
- **Lines**: ~200
- **Key Functions**:
  - `create_squad_member(squad_id, role, config) -> SquadMember`
  - `get_or_create_agent(squad_member_id) -> BaseSquadAgent`
  - `update_agent_config(squad_member_id, config)`
  - `deactivate_agent(squad_member_id)`

**`squad_service.py`** - Squad Management Service
- Create squads with members
- Validate squad composition
- Calculate costs
- **Lines**: ~250
- **Key Functions**:
  - `create_squad(user_id, name, members) -> Squad`
  - `validate_squad_size(plan_tier, num_members) -> bool`
  - `get_squad_with_agents(squad_id) -> SquadWithAgents`
  - `update_squad_config(squad_id, config)`

**`task_execution_service.py`** - Task Execution Service
- Start task execution
- Track progress
- Handle errors
- **Lines**: ~300
- **Key Functions**:
  - `start_task_execution(task_id, squad_id) -> TaskExecution`
  - `update_execution_status(execution_id, status, logs)`
  - `complete_execution(execution_id, result)`
  - `handle_execution_error(execution_id, error)`

**Deliverables**:
- ✅ Service layer complete
- ✅ CRUD operations working
- ✅ Business logic tested
- ✅ Database integration working

---

## 🗓️ Week 2: Agent Collaboration & Orchestration

### Day 8-9: Agent Orchestration Engine

**5. Task Orchestration System**

```python
backend/agents/orchestration/
├── __init__.py
├── orchestrator.py      # Main orchestration logic
├── workflow_engine.py   # Workflow execution
└── delegation_engine.py # Task delegation logic
```

**`orchestrator.py`** - Main Orchestration Engine
- Coordinate agent collaboration
- Manage task execution workflow
- Handle agent communication
- **Lines**: ~350
- **Key Components**:
  - `TaskOrchestrator` class
  - `execute_task(task_id, squad_id)`
  - `monitor_progress(execution_id)`
  - `handle_blockers(execution_id, blocker)`

**`workflow_engine.py`** - Workflow State Machine
- Define task workflow states
- State transitions
- Conditional logic
- **Lines**: ~200
- **States**: pending → analyzing → delegated → in_progress → review → completed/failed
- **Key Functions**:
  - `transition_state(execution_id, from_state, to_state)`
  - `get_valid_transitions(current_state)`
  - `execute_state_actions(execution_id, state)`

**`delegation_engine.py`** - Smart Task Delegation
- Analyze task requirements
- Match tasks to agents
- Load balancing
- **Lines**: ~180
- **Key Functions**:
  - `analyze_task_requirements(task) -> Requirements`
  - `find_best_agent(squad, requirements) -> SquadMember`
  - `delegate_to_agent(agent_id, subtask) -> TaskAssignment`

**Deliverables**:
- ✅ Orchestration engine working
- ✅ Workflow state machine operational
- ✅ Smart delegation implemented
- ✅ Integration tests

---

### Day 10-11: Agent Collaboration Patterns

**6. Implement Collaboration Patterns**

```python
backend/agents/collaboration/
├── __init__.py
├── patterns.py          # Collaboration patterns
├── standup.py          # Daily standup logic
├── code_review.py      # Code review flow
└── problem_solving.py  # Collaborative problem solving
```

**`patterns.py`** - Collaboration Patterns
- Question-Answer pattern
- Task Assignment pattern
- Status Check pattern
- Code Review pattern
- **Lines**: ~250

**`standup.py`** - Async Standup
- Collect updates from all agents
- Identify blockers
- Share insights
- **Lines**: ~150
- **Key Functions**:
  - `conduct_standup(squad_id, execution_id)`
  - `collect_updates(squad_members)`
  - `identify_blockers(updates)`
  - `broadcast_insights(insights)`

**`code_review.py`** - Code Review Flow
- Developer requests review
- Tech lead reviews code
- Feedback loop
- **Lines**: ~180
- **Key Functions**:
  - `request_review(pr_url, reviewer_id)`
  - `conduct_review(pr_url, code_diff)`
  - `provide_feedback(pr_url, comments)`
  - `approve_or_request_changes(pr_url, decision)`

**`problem_solving.py`** - Collaborative Problem Solving
- Agent asks questions
- Broadcast to relevant experts
- Collect answers
- Synthesize solution
- **Lines**: ~200
- **Key Functions**:
  - `broadcast_question(question, relevant_roles)`
  - `collect_answers(question_id, timeout=300)`
  - `synthesize_solution(question, answers)`

**Deliverables**:
- ✅ Collaboration patterns working
- ✅ Standup flow operational
- ✅ Code review flow working
- ✅ Problem-solving tested

---

### Day 12-13: API Endpoints for Agents

**7. Agent Management API**

```python
backend/api/v1/endpoints/
├── squads.py           # Squad CRUD
├── squad_members.py    # Agent management
├── task_executions.py  # Task execution endpoints
└── agent_messages.py   # Message viewing
```

**Squad Endpoints** (`squads.py`):
```python
POST   /api/v1/squads              # Create squad
GET    /api/v1/squads              # List user's squads
GET    /api/v1/squads/{id}         # Get squad details
PUT    /api/v1/squads/{id}         # Update squad
DELETE /api/v1/squads/{id}         # Delete squad
POST   /api/v1/squads/{id}/members # Add member
DELETE /api/v1/squads/{id}/members/{member_id} # Remove member
```

**Task Execution Endpoints** (`task_executions.py`):
```python
POST   /api/v1/task-executions                    # Start execution
GET    /api/v1/task-executions/{id}              # Get execution details
GET    /api/v1/task-executions/{id}/messages     # Get messages
GET    /api/v1/task-executions/{id}/stream       # SSE stream
POST   /api/v1/task-executions/{id}/intervention # Human intervention
POST   /api/v1/task-executions/{id}/cancel       # Cancel execution
```

**Agent Message Endpoints** (`agent_messages.py`):
```python
GET    /api/v1/agent-messages                   # List messages
POST   /api/v1/agent-messages                   # Send message (testing)
GET    /api/v1/agent-messages/{id}             # Get message details
```

**Deliverables**:
- ✅ 15+ API endpoints
- ✅ All endpoints documented (Swagger)
- ✅ Authentication/authorization
- ✅ API tests

---

### Day 14: Real-time Updates & SSE

**8. Server-Sent Events for Real-time Updates**

```python
backend/api/v1/endpoints/sse.py
backend/services/sse_service.py
```

**SSE Implementation**:
- Stream agent messages in real-time
- Execution status updates
- Error notifications
- **Lines**: ~200

**Key Features**:
- Connection management
- Heartbeat/keep-alive
- Reconnection support
- Message buffering

**Deliverables**:
- ✅ SSE endpoint working
- ✅ Real-time message streaming
- ✅ Frontend can subscribe
- ✅ Connection handling robust

---

## 🗓️ Week 3: Testing, Integration & Polish

### Day 15-16: Comprehensive Testing

**9. Test Suite for Agent System**

```python
backend/tests/
├── test_agents/
│   ├── test_base_agent.py         # Base agent tests
│   ├── test_factory.py            # Factory tests
│   ├── test_project_manager.py    # PM agent tests
│   ├── test_backend_developer.py  # Backend dev tests
│   └── test_communication.py      # Communication tests
├── test_orchestration/
│   ├── test_orchestrator.py       # Orchestration tests
│   ├── test_workflow.py           # Workflow tests
│   └── test_delegation.py         # Delegation tests
├── test_collaboration/
│   ├── test_patterns.py           # Pattern tests
│   ├── test_standup.py           # Standup tests
│   └── test_code_review.py       # Code review tests
└── test_integration/
    ├── test_full_workflow.py      # End-to-end tests
    ├── test_multi_agent.py        # Multi-agent tests
    └── test_rag_integration.py    # RAG tests
```

**Test Coverage Goals**:
- Unit tests: 80%+ coverage
- Integration tests: Key workflows
- E2E tests: Full task execution

**Test Scenarios**:
1. Single agent processes message
2. PM delegates to multiple agents
3. Agent asks question, receives answer
4. Code review flow
5. Task completion workflow
6. Error handling and recovery
7. Blocker escalation
8. RAG context retrieval

**Deliverables**:
- ✅ 50+ test cases
- ✅ 80%+ code coverage
- ✅ All critical paths tested
- ✅ CI/CD passing

---

### Day 17-18: Integration with Existing System

**10. Connect Agents to Application**

**Database Migrations**:
```bash
# Add any missing columns
alembic revision --autogenerate -m "phase_3_agent_tables"
alembic upgrade head
```

**Integration Points**:
1. **User Authentication** → Squad ownership
2. **Subscription Tiers** → Agent limits
3. **API Gateway** → Agent endpoints
4. **Database** → Agent persistence
5. **Redis** → Message queue & memory

**Services to Connect**:
- AuthService → SquadService (user can only access their squads)
- SquadService → AgentService (create agents with squad)
- TaskExecutionService → Orchestrator (start workflows)

**Deliverables**:
- ✅ All services integrated
- ✅ Authentication working
- ✅ Database migrations applied
- ✅ End-to-end flow working

---

### Day 19: Documentation

**11. Comprehensive Documentation**

```markdown
docs/
├── PHASE_3_COMPLETE.md          # Completion summary
├── AGENT_ARCHITECTURE.md        # Architecture doc
├── AGENT_USAGE_GUIDE.md         # How to use agents
├── A2A_PROTOCOL.md              # Protocol spec
├── ADDING_NEW_AGENTS.md         # How to add agents
└── TROUBLESHOOTING_AGENTS.md    # Common issues
```

**Documentation Content**:
1. **Architecture**: System design, components, flow diagrams
2. **Usage Guide**: How to create squads, execute tasks, monitor
3. **Protocol Spec**: A2A message formats, examples
4. **Extension Guide**: How to add new agent types
5. **Troubleshooting**: Common errors and solutions

**Deliverables**:
- ✅ 5 comprehensive docs
- ✅ Code examples
- ✅ Architecture diagrams
- ✅ API documentation updated

---

### Day 20-21: Polish & Demo

**12. Final Polish**

**Tasks**:
- Code review and refactoring
- Performance optimization
- Error message improvements
- Logging enhancements
- Demo preparation

**Demo Scenario**:
```
1. Create a squad (PM + 2 Backend Devs + QA)
2. Assign a task: "Implement user profile endpoint"
3. Watch PM analyze and delegate
4. See agents collaborate
5. Review code together
6. Complete and get feedback
```

**Deliverables**:
- ✅ Demo working perfectly
- ✅ Code polished
- ✅ Performance optimized
- ✅ Ready for Phase 4

---

## 📊 Phase 3 Complete - Success Metrics

### Functional Requirements ✅
- [ ] Create agents dynamically from database
- [ ] Agents can send/receive messages
- [ ] PM can analyze and delegate tasks
- [ ] Developers can ask questions
- [ ] Code review flow works
- [ ] Status tracking operational
- [ ] Context/RAG working
- [ ] Real-time updates streaming

### Technical Requirements ✅
- [ ] 80%+ test coverage
- [ ] All API endpoints documented
- [ ] Sub-second message latency
- [ ] Supports 100+ concurrent agents
- [ ] Graceful error handling
- [ ] Comprehensive logging

### Code Quality ✅
- [ ] Type hints everywhere
- [ ] Docstrings for all public methods
- [ ] Clean architecture (SOLID)
- [ ] No code smells
- [ ] Consistent style

---

## 📦 Deliverables Summary

### Code Modules (20 new files)
1. ✅ Agent communication system (3 files)
2. ✅ Specialized agents (9 files)
3. ✅ Context & RAG (3 files)
4. ✅ Services layer (3 files)
5. ✅ Orchestration (3 files)
6. ✅ Collaboration patterns (4 files)
7. ✅ API endpoints (4 files)
8. ✅ SSE streaming (2 files)

### Tests (15 new test files)
- Unit tests for all components
- Integration tests for workflows
- E2E tests for full scenarios

### Documentation (6 new docs)
- Architecture documentation
- Usage guides
- Protocol specifications
- Extension guides

### Database
- Alembic migrations
- Seed data for testing

---

## 🚀 Next Steps After Phase 3

**Phase 4: MCP Server Integration**
- Connect to external tools (Git, Jira, etc.)
- Enable agents to read/write code
- Integrate with development tools

**Phase 5: Workflow Orchestration (Inngest)**
- Async task processing
- Reliable retries
- Complex workflows
- Scheduled tasks

---

## 🎯 Key Success Factors

1. **PM Agent Quality**: This is the orchestrator - must be solid
2. **Message Protocol**: Must be clear, structured, extensible
3. **Context Management**: Agents need rich context to be effective
4. **Testing**: Can't skip this - agent behavior must be predictable
5. **Real-time Updates**: Users need to see agents working

---

## 💡 Tips for Implementation

1. **Start Simple**: Get 1 agent working end-to-end first
2. **Incremental**: Add features one at a time
3. **Test Early**: Don't wait until the end
4. **Mock LLMs**: Use mocked responses for faster testing
5. **Monitor Costs**: Track LLM token usage
6. **Logging**: Comprehensive logs for debugging
7. **Error Handling**: Agents will fail - handle gracefully

---

## 📈 Estimated Effort

| Component | Lines of Code | Time (days) |
|-----------|--------------|-------------|
| Communication | 530 | 2 |
| Agents | 1,800 | 3 |
| Context/RAG | 600 | 2 |
| Services | 750 | 1 |
| Orchestration | 730 | 2 |
| Collaboration | 780 | 2 |
| API Endpoints | 800 | 2 |
| SSE | 200 | 1 |
| Tests | 2,000 | 2 |
| Documentation | - | 1 |
| Integration & Polish | - | 3 |
| **TOTAL** | **~8,190 LOC** | **21 days** |

---

**Ready to build the most exciting part of Agent Squad! 🤖✨**
