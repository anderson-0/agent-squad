# Specialized Agents

## Overview

The `specialized/` folder contains Agno-powered implementations of specialized AI agents that work together as a software development squad. Each agent has a specific role, capabilities, and responsibilities that mirror a real software development team.

**All agents use the Agno framework** providing enterprise-grade features like persistent sessions, automatic memory management, and production-ready architecture.

## Team Structure

```
┌──────────────────────────────────────────────────────────────┐
│                    Specialized Agents                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐         ┌────────────────┐              │
│  │ Project Manager│◄───────►│   Tech Lead    │              │
│  │  (Orchestrator)│         │  (Technical    │              │
│  │                │         │   Leadership)  │              │
│  └───────┬────────┘         └────────┬───────┘              │
│          │                           │                       │
│          │    Delegates Tasks        │  Reviews Code        │
│          ▼                           ▼                       │
│  ┌───────────────────────────────────────────────────┐      │
│  │            Development Team                        │      │
│  ├───────────────────────────────────────────────────┤      │
│  │  Backend Dev  │  Frontend Dev  │  DevOps  │  AI   │      │
│  │               │                 │          │       │      │
│  └───────────────────────────────────────────────────┘      │
│          │                           │                       │
│          │                           │                       │
│          ▼                           ▼                       │
│  ┌──────────────┐         ┌──────────────────┐             │
│  │   QA Tester  │         │  Solution         │             │
│  │              │         │  Architect        │             │
│  └──────────────┘         └──────────────────┘             │
│                                                               │
│  ┌───────────────────────────────┐                          │
│  │       Support Roles           │                          │
│  ├───────────────────────────────┤                          │
│  │  Designer  (UX/UI)            │                          │
│  └───────────────────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

## Agent Roles

### 1. Project Manager (`project_manager.py`)

**Role**: Squad orchestrator and stakeholder interface

**Capabilities**:
- `receive_webhook_notification`: Process Jira/ClickUp webhooks
- `review_ticket_with_tech_lead`: Collaborate on ticket review
- `estimate_effort`: Estimate hours required
- `break_down_task`: Break tasks into subtasks
- `delegate_to_team`: Assign work to appropriate agents
- `monitor_progress`: Track team progress
- `conduct_standup`: Run daily standups
- `escalate_to_human`: Escalate blockers to humans
- `communicate_with_stakeholder`: Status updates

**Key Methods**:
- `receive_webhook_notification()`: Entry point for new tickets (location: `project_manager.py:68`)
- `review_ticket_with_tech_lead()`: Collaborative ticket review (location: `project_manager.py:109`)
- `estimate_effort()`: Hours estimation with TL input (location: `project_manager.py:181`)
- `break_down_task()`: Task decomposition (location: `project_manager.py:249`)
- `delegate_task()`: Create task assignments (location: `project_manager.py:309`)
- `conduct_standup()`: Analyze team updates (location: `project_manager.py:354`)
- `escalate_to_human()`: Human intervention (location: `project_manager.py:401`)

**Business Rules**:
1. PM is the ONLY agent that receives webhook notifications from Jira/ClickUp
2. PM MUST collaborate with Tech Lead before finalizing task breakdown
3. PM makes the final decision on task priority and delegation
4. PM conducts async standups to monitor progress
5. PM escalates to humans when squad cannot proceed
6. Ticket status: `READY | NEEDS_IMPROVEMENT | UNCLEAR`

**Workflow**:
1. Receive webhook notification
2. Collaborate with Tech Lead to review ticket
3. Estimate effort and complexity (with TL)
4. Break down into subtasks
5. Delegate to team members
6. Monitor progress via standups
7. Escalate blockers if needed

---

### 2. Tech Lead (`tech_lead.py`)

**Role**: Technical leadership and code quality

**Capabilities**:
- `review_ticket_technical`: Technical feasibility assessment
- `estimate_complexity`: Complexity scoring (1-10)
- `review_code`: Code review
- `review_pull_request`: PR review with approval
- `provide_architecture_guidance`: Answer arch questions
- `make_technical_decision`: Make tech decisions
- `identify_technical_risks`: Risk assessment
- `mentor_developer`: Provide guidance

**Key Methods**:
- `review_ticket_technical()`: Technical review (location: `tech_lead.py:55`)
- `estimate_complexity()`: Complexity 1-10 (location: `tech_lead.py:143`)
- `review_code()`: Code review with detailed feedback (location: `tech_lead.py:229`)
- `provide_architecture_guidance()`: Educational guidance (location: `tech_lead.py:321`)
- `make_technical_decision()`: Decision making (location: `tech_lead.py:360`)
- `answer_technical_question()`: Answer team questions (location: `tech_lead.py:421`)

**Business Rules**:
1. Complexity scoring: 1-2 (Simple), 3-5 (Moderate), 6-8 (Complex), 9-10 (Very Complex)
2. Code review status: `APPROVED | CHANGES_REQUESTED | COMMENTED`
3. Technical review decision: `APPROVED | NEEDS_CLARIFICATION | NOT_FEASIBLE`
4. TL provides educational feedback (explains WHY, not just WHAT)
5. TL can recommend creating ADRs (Architecture Decision Records)
6. All PRs MUST be reviewed by Tech Lead before merge

**Code Review Criteria**:
1. Code Quality (clean code, readability, maintainability)
2. Best Practices (patterns, SOLID, framework conventions)
3. Performance (bottlenecks, N+1 queries, caching)
4. Security (input validation, SQL injection, XSS, auth)
5. Testing (coverage, test quality, edge cases)
6. Acceptance Criteria compliance

---

### 3. Backend Developer (`backend_developer.py`)

**Role**: Backend implementation specialist

**Capabilities**:
- `analyze_task`: Analyze task and create implementation plan
- `plan_implementation`: Detailed implementation planning
- `write_code`: Write backend code (Phase 4: via MCP)
- `write_tests`: Write unit/integration tests (Phase 4: via MCP)
- `create_pull_request`: Create PRs (Phase 4: via MCP)
- `ask_question`: Ask technical questions
- `provide_status_update`: Progress updates
- `request_code_review`: Request TL review
- `respond_to_review_feedback`: Process review feedback
- `troubleshoot_issue`: Debug and troubleshoot

**Key Methods**:
- `analyze_task()`: Task analysis and planning (location: `backend_developer.py:57`)
- `plan_implementation()`: Detailed plan (location: `backend_developer.py:130`)
- `ask_question()`: Ask for help (location: `backend_developer.py:216`)
- `provide_status_update()`: Status to PM (location: `backend_developer.py:251`)
- `request_code_review()`: Request review (location: `backend_developer.py:283`)
- `respond_to_review_feedback()`: Address feedback (location: `backend_developer.py:315`)
- `troubleshoot_issue()`: Systematic troubleshooting (location: `backend_developer.py:377`)
- `complete_task()`: Mark as done (location: `backend_developer.py:450`)

**Implementation Plan Includes**:
1. Files to Create/Modify
2. Database Changes (models, migrations, indexes)
3. API Endpoints (routes, schemas, validation)
4. Business Logic (services, algorithms, edge cases)
5. Testing Strategy (unit tests, integration tests, test data)
6. Dependencies (packages, external services)
7. Implementation Order (step-by-step)
8. Definition of Done (tests passing, reviewed, documented)

**Business Rules**:
1. Backend Dev analyzes task BEFORE implementation
2. Must ask questions when requirements are unclear
3. Must provide regular status updates to PM
4. Must request code review before marking task complete
5. Must write tests for all code changes
6. Must update documentation when applicable

---

### 4. Frontend Developer (`frontend_developer.py`)

**Role**: Frontend implementation specialist

**Capabilities**:
Similar to Backend Developer but focused on:
- UI component development
- State management
- API integration
- Responsive design
- Accessibility
- User experience
- Frontend testing (Jest, Cypress)

**Specializations**:
- `react_nextjs`: React/Next.js specialist
- `vue_nuxt`: Vue/Nuxt specialist
- `angular`: Angular specialist

**Business Rules**:
1. Must ensure responsive design (mobile, tablet, desktop)
2. Must follow accessibility standards (WCAG)
3. Must implement proper state management
4. Must write unit and E2E tests
5. Must collaborate with Designer on UX/UI

---

### 5. QA Tester (`qa_tester.py`)

**Role**: Quality assurance and testing

**Capabilities**:
- `review_acceptance_criteria`: Review ACs for testability
- `create_test_plan`: Create comprehensive test plan
- `execute_manual_tests`: Manual testing
- `execute_automated_tests`: Run automation (Phase 4: via MCP)
- `create_bug_report`: Document bugs
- `verify_bug_fix`: Verify fixes
- `regression_testing`: Regression test suite
- `approve_deployment`: Approve for release

**Test Types**:
1. Functional Testing (features work as expected)
2. Integration Testing (components work together)
3. Regression Testing (no breaking changes)
4. Performance Testing (load, stress, scalability)
5. Security Testing (vulnerabilities, auth)
6. Accessibility Testing (WCAG compliance)
7. User Acceptance Testing (business requirements)

**Business Rules**:
1. QA tests AFTER code review approval
2. QA creates detailed bug reports with reproduction steps
3. QA verifies ALL bugs are fixed before approval
4. QA maintains regression test suite
5. QA approves deployment only after ALL tests pass

---

### 6. Solution Architect (`solution_architect.py`)

**Role**: High-level architecture and system design

**Capabilities**:
- `design_system_architecture`: Design system architecture
- `create_adr`: Create Architecture Decision Records
- `review_technical_approach`: Review tech approach
- `identify_scalability_issues`: Scalability analysis
- `recommend_tech_stack`: Technology recommendations
- `design_database_schema`: Database design
- `design_api_contracts`: API design

**Business Rules**:
1. Architect is consulted for:
   - Major architecture changes
   - New technology adoption
   - Scalability concerns
   - System integration
2. Architect creates ADRs for significant decisions
3. Architect reviews database schema designs
4. Architect ensures alignment with enterprise architecture

---

### 7. DevOps Engineer (`devops_engineer.py`)

**Role**: Infrastructure, deployment, and operations

**Capabilities**:
- `setup_ci_cd`: Configure CI/CD pipelines
- `provision_infrastructure`: Infrastructure as code
- `configure_monitoring`: Set up monitoring/alerting
- `manage_deployments`: Deploy to environments
- `optimize_performance`: Performance optimization
- `ensure_security`: Security hardening
- `manage_databases`: Database administration
- `incident_response`: Handle production incidents

**Business Rules**:
1. DevOps manages ALL deployments (staging, production)
2. DevOps sets up monitoring BEFORE production deployment
3. DevOps ensures automated backups
4. DevOps implements security best practices
5. DevOps participates in incident response

---

### 8. AI Engineer (`ai_engineer.py`)

**Role**: AI/ML model development and integration

**Capabilities**:
- `train_model`: Train ML models
- `evaluate_model`: Model evaluation
- `deploy_model`: Model deployment
- `optimize_prompts`: LLM prompt engineering
- `integrate_ai_service`: Integrate AI services
- `monitor_ai_performance`: AI performance monitoring

**Use Cases**:
- LLM integration (OpenAI, Anthropic, Groq)
- ML model development
- RAG implementation
- Prompt engineering
- AI feature development

**Business Rules**:
1. AI Engineer evaluates models before production
2. AI Engineer monitors AI performance and costs
3. AI Engineer optimizes prompts for best results
4. AI Engineer ensures responsible AI practices

---

### 9. Designer (`designer.py`)

**Role**: UX/UI design and user experience

**Capabilities**:
- `create_wireframes`: Create wireframes/mockups
- `design_ui_components`: Design UI components
- `create_design_system`: Build design systems
- `review_ui_implementation`: Review frontend implementation
- `conduct_ux_research`: User research
- `create_prototypes`: Interactive prototypes

**Business Rules**:
1. Designer reviews UI/UX before implementation
2. Designer creates design system for consistency
3. Designer ensures accessibility standards
4. Designer conducts user research for major features
5. Designer approves final UI implementation

---

## Common Patterns Across All Agents

### Message Types
All agents can send/receive these message types (defined in `backend/schemas/agent_message.py`):
- `TaskAssignment`: PM → Developer
- `StatusUpdate`: Developer → PM
- `Question`: Any → Any (or broadcast)
- `Answer`: Responder → Asker
- `CodeReviewRequest`: Developer → Tech Lead
- `CodeReviewResponse`: Tech Lead → Developer
- `TaskCompletion`: Developer → PM
- `HumanInterventionRequired`: PM → Human
- `Standup`: PM → All

### Base Capabilities
All agents inherit from `AgnoSquadAgent` (Agno framework) and have:
- ✅ **Persistent Sessions**: Conversations survive restarts
- ✅ **Automatic Memory**: Agno manages history & context
- ✅ **LLM Integration**: OpenAI, Anthropic, Groq support
- ✅ **Message Bus Integration**: NATS JetStream for communication
- ✅ **MCP Tool Execution**: Git, Jira, GitHub tools (Phase 4)
- ✅ **Context Awareness**: RAG, memory, conversation history

### Response Parsing
All specialized agents implement helper methods to parse LLM responses:
- `_extract_*()` methods: Extract structured data from text responses
- `_parse_*()` methods: Parse complex structures
- Regular expressions for pattern matching
- Fallback to default values when parsing fails

---

## Integration with Other Modules

### Communication
All agents communicate via **Message Bus** (`communication/message_bus.py`):
```python
await message_bus.send_message(
    sender_id=agent_id,
    recipient_id=recipient_id,  # or None for broadcast
    content="Message content",
    message_type="task_assignment",
    task_execution_id=execution_id
)
```

### Context
Agents access context via **Context Manager** (`context/context_manager.py`):
```python
context = await context_manager.build_context_for_implementation(
    agent_id=agent_id,
    squad_id=squad_id,
    task=task_data,
    task_execution_id=execution_id
)
```

### Orchestration
Agents are orchestrated by **Task Orchestrator** (`orchestration/orchestrator.py`):
- Workflow state management
- Task delegation
- Progress monitoring
- Blocker handling

### Collaboration
Agents collaborate via **Collaboration Patterns** (`collaboration/patterns.py`):
- Problem Solving: Collaborative Q&A
- Code Review: Developer ↔ Tech Lead
- Standup: Daily progress updates

---

## Creating Custom Specialized Agents

All agents are built on the Agno framework. To create a custom agent:

```python
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig
from typing import List
from uuid import UUID

class CustomAgent(AgnoSquadAgent):
    """Custom specialized agent powered by Agno"""

    def get_capabilities(self) -> List[str]:
        return [
            "custom_capability_1",
            "custom_capability_2",
        ]

    async def custom_method(self, data):
        """Custom method implementation"""
        response = await self.process_message(
            message=f"Process this: {data}",
            context={"type": "custom"}
        )
        return response

# Register in factory.py
from backend.agents.factory import AGENT_REGISTRY
AGENT_REGISTRY["custom_role"] = CustomAgent
```

**Agno Benefits**:
- Persistent sessions (conversations survive restarts)
- Automatic memory management
- Production-ready architecture
- Built-in message bus integration

---

## Testing Specialized Agents

```python
import pytest
from backend.agents.factory import AgentFactory
from uuid import uuid4

@pytest.mark.asyncio
async def test_project_manager_ticket_review():
    pm = AgentFactory.create_agent(
        agent_id=uuid4(),
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="Test prompt"  # Override file-based prompt
    )

    result = await pm.receive_webhook_notification(
        ticket={"title": "Test ticket", "description": "Test"},
        webhook_event="issue_created"
    )

    assert result.content is not None
    assert len(result.content) > 0
```

---

## Performance Considerations

1. **Token Usage**: Each agent call consumes LLM tokens
   - Project Manager: High token usage (analysis, planning, delegation)
   - Tech Lead: High token usage (code review, complexity analysis)
   - Developers: Medium token usage (implementation planning)
   - QA: Low-Medium token usage (test planning, bug reports)

2. **Response Time**:
   - OpenAI GPT-4: 3-10 seconds per response
   - Anthropic Claude: 2-8 seconds per response
   - Groq Llama: 1-3 seconds per response (faster, lower quality)

3. **Cost Optimization**:
   - Use GPT-3.5 for simple tasks
   - Use GPT-4 for complex analysis
   - Use Groq for speed-critical, simple tasks
   - Cache common prompts and responses

---

## Common Questions

**Q: How do agents know which other agents exist?**
A: Agents are registered in the database (Squad model) and can be queried by role.

**Q: Can agents call each other directly?**
A: No, all communication goes through the Message Bus for tracking and coordination.

**Q: What happens if an agent makes a mistake?**
A: The Tech Lead and QA catch issues during review and testing. PM can escalate to humans.

**Q: Can I have multiple agents with the same role?**
A: Yes, multiple Backend Developers or Frontend Developers can be in a squad.

**Q: How are agents assigned tasks?**
A: PM uses Delegation Engine to match tasks to agents based on role, specialization, and availability.

---

## Related Documentation

- See `../CLAUDE.md` for base agent architecture
- See `../communication/CLAUDE.md` for message bus protocol
- See `../orchestration/CLAUDE.md` for workflow orchestration
- See `../collaboration/CLAUDE.md` for collaboration patterns
- See `/backend/schemas/agent_message.py` for message schemas
