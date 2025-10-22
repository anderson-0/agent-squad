# Orchestration Module

## Overview

The `orchestration/` module coordinates agent collaboration through workflow state management, task delegation, and progress monitoring. It's the "conductor" that ensures all agents work together harmoniously.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Orchestration                          │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │           TaskOrchestrator (Main Entry)            │  │
│  │  - Execute tasks                                   │  │
│  │  - Monitor progress                                │  │
│  │  - Handle blockers                                 │  │
│  │  - Escalate to humans                              │  │
│  └─────────┬──────────────────┬──────────────────────┘  │
│            │                  │                          │
│            ▼                  ▼                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ WorkflowEngine   │  │ DelegationEngine │            │
│  │ (State Machine)  │  │ (Task Routing)   │            │
│  │                  │  │                  │            │
│  │ - State          │  │ - Match agents   │            │
│  │   transitions    │  │   to tasks       │            │
│  │ - Validation     │  │ - Load balancing │            │
│  │ - Progress       │  │ - Priority       │            │
│  └──────────────────┘  └──────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `workflow_engine.py` - State Machine

**Purpose**: Manages task execution lifecycle through state transitions

**Workflow States** (Location: `workflow_engine.py:17`):
```
PENDING → ANALYZING → PLANNING → DELEGATED → IN_PROGRESS → REVIEWING → TESTING → COMPLETED
              ↓           ↓           ↓            ↓            ↓           ↓
           BLOCKED/FAILED (can transition back or to FAILED)
```

**State Descriptions**:
- `PENDING`: Task received, queued
- `ANALYZING`: PM analyzing requirements
- `PLANNING`: Creating implementation plan
- `DELEGATED`: Task assigned to agents
- `IN_PROGRESS`: Active development
- `REVIEWING`: Code review
- `TESTING`: QA testing
- `BLOCKED`: Blocked by dependency/issue
- `COMPLETED`: Successfully finished
- `FAILED`: Task failed

**Valid Transitions** (Location: `workflow_engine.py:40`):

Rules enforced by state machine to prevent invalid state changes.

**Key Methods**:

#### `transition_state()`
Location: `workflow_engine.py:141`

```python
success = await workflow_engine.transition_state(
    db=db,
    execution_id=execution_id,
    from_state=WorkflowState.IN_PROGRESS,
    to_state=WorkflowState.REVIEWING,
    reason="Implementation complete, requesting review",
    metadata={"pr_url": "..."}
)
# Raises ValueError if transition invalid
```

#### `get_workflow_progress()`
Location: `workflow_engine.py:230`

```python
progress = workflow_engine.get_workflow_progress(
    current_state=WorkflowState.IN_PROGRESS
)
# Returns:
# {
#     "state": "in_progress",
#     "progress_percentage": 62,
#     "is_terminal": False,
#     "is_blocked": False
# }
```

#### `get_workflow_metrics()`
Location: `workflow_engine.py:322`

```python
metrics = workflow_engine.get_workflow_metrics(
    state_history=[
        {"state": "pending", "timestamp": "..."},
        {"state": "analyzing", "timestamp": "..."},
        ...
    ]
)
# Returns:
# {
#     "total_transitions": 7,
#     "time_in_each_state_seconds": {...},
#     "total_duration_seconds": 3600,
#     "average_time_per_state_seconds": 514
# }
```

**Business Rules**:
1. Only valid transitions allowed (enforced by state machine)
2. State actions auto-executed on transition
3. All transitions logged to database
4. Progress calculated based on state order
5. Terminal states: COMPLETED, FAILED

---

### 2. `orchestrator.py` - Task Orchestrator

**Purpose**: Main orchestration logic coordinating all aspects of task execution

**Key Responsibilities**:
- Execute tasks from start to finish
- Monitor progress
- Handle blockers
- Escalate to humans
- Coordinate state transitions

**Main Workflow** (Location: `orchestrator.py:69`):

```python
# 1. Execute task
execution_id = await orchestrator.execute_task(
    db=db,
    task=task,
    squad_id=squad_id
)
# State: PENDING → ANALYZING

# 2. Monitor progress
progress = await orchestrator.monitor_progress(
    db=db,
    execution_id=execution_id
)

# 3. Handle blocker (if needed)
await orchestrator.handle_blocker(
    db=db,
    execution_id=execution_id,
    blocker_description="Waiting for API spec",
    blocker_metadata={"severity": "high"}
)
# State: * → BLOCKED

# 4. Resolve blocker
await orchestrator.resolve_blocker(
    db=db,
    execution_id=execution_id,
    resolution="API spec received",
    next_state=WorkflowState.IN_PROGRESS
)
# State: BLOCKED → IN_PROGRESS

# 5. Complete task
await orchestrator.complete_task(
    db=db,
    execution_id=execution_id,
    result={"pr_url": "...", "tests_passing": True}
)
# State: * → COMPLETED
```

**State Action Handlers** (Location: `orchestrator.py:296`):

Auto-executed when entering specific states:

```python
# Registered in __init__
workflow_engine.register_state_action(
    WorkflowState.ANALYZING,
    orchestrator._on_analyzing_state
)

# Handler auto-called on transition to ANALYZING
async def _on_analyzing_state(db, execution_id, context):
    # PM analyzes task
    # Auto-transitions to PLANNING when done
    pass
```

**Escalation** (Location: `orchestrator.py:223`):

```python
escalation = await orchestrator.escalate_to_human(
    db=db,
    execution_id=execution_id,
    reason="Cannot proceed without product decision",
    details="Need clarification on user flow",
    attempted_solutions=[
        "Reviewed documentation",
        "Asked team",
        "Researched competitors"
    ]
)
```

**Business Rules**:
1. Only one execution per task at a time
2. State actions executed synchronously in transaction
3. Blockers logged with metadata
4. Human escalation triggers notification (Phase 4)
5. Progress percentage based on state position (0-100%)

---

### 3. `delegation_engine.py` - Task Delegation

**Purpose**: Match tasks to appropriate agents based on role, specialization, and availability

**Key Responsibilities**:
- Analyze task requirements
- Find best-fit agent for each subtask
- Consider agent availability and workload
- Prioritize assignments

**Delegation Strategy**:
1. **Role Matching**: Match task type to agent role
2. **Specialization**: Prefer specialists (e.g., `python_fastapi` backend dev)
3. **Availability**: Check agent current workload
4. **Priority**: Higher priority tasks assigned first
5. **Load Balancing**: Distribute work evenly

**Example Flow**:
```
Task: "Implement user authentication"
↓
Break down into subtasks:
  1. Backend API (role: backend_developer)
  2. Frontend UI (role: frontend_developer)
  3. Tests (role: tester)
↓
Find matching agents from squad
↓
Assign based on availability & specialization
```

**Business Rules**:
1. Tasks delegated by Project Manager
2. Delegation engine suggests, PM approves
3. Agent can refuse/request reassignment
4. Critical path tasks prioritized
5. Dependencies tracked and enforced

---

## Integration with Other Modules

### Communication
- Orchestrator uses Message Bus for agent coordination
- State transitions broadcast to team
- Escalations sent via human intervention messages

### Context
- Context Manager provides task context for agents
- RAG retrieves similar past tasks
- Memory stores task state

### Collaboration
- Collaboration patterns invoked during workflow
- Code review triggered in REVIEWING state
- Standups conducted to monitor IN_PROGRESS

---

## Workflow Progression Example

```
User creates task: "Implement user login"
↓
1. PENDING (task created)
   - Task queued in database
↓
2. ANALYZING (PM reviewing)
   - PM reviews ticket
   - Collaborates with Tech Lead
   - Assesses complexity
↓
3. PLANNING (creating plan)
   - PM breaks down into subtasks
   - Tech Lead estimates complexity
   - Create implementation plan
↓
4. DELEGATED (assigning work)
   - Backend dev: API endpoints
   - Frontend dev: Login UI
   - QA: Test plan
↓
5. IN_PROGRESS (implementation)
   - Devs working in parallel
   - Regular status updates
   - Blockers tracked
↓
6. REVIEWING (code review)
   - Tech Lead reviews PRs
   - Provides feedback
   - Devs address comments
↓
7. TESTING (QA testing)
   - QA executes test plan
   - Reports bugs
   - Verifies fixes
↓
8. COMPLETED (done!)
   - All ACs met
   - Tests passing
   - Documentation updated
```

---

## Business Rules Summary

### Workflow Engine
1. Only valid transitions allowed
2. State actions executed atomically
3. All transitions logged
4. Terminal states final (no transitions out)
5. Blocked state can return to multiple states

### Task Orchestrator
1. Single execution per task
2. Progress monitored continuously
3. Blockers resolved before proceeding
4. Human escalation for unresolvable issues
5. Execution summary available at all times

### Delegation Engine
1. PM initiates delegation
2. Role + specialization matching
3. Availability considered
4. Load balancing applied
5. Dependencies tracked

---

## Testing

```python
import pytest
from backend.agents.orchestration import WorkflowEngine, TaskOrchestrator, WorkflowState

def test_valid_transition():
    engine = WorkflowEngine()
    assert engine.is_valid_transition(
        WorkflowState.PENDING,
        WorkflowState.ANALYZING
    ) == True

def test_invalid_transition():
    engine = WorkflowEngine()
    assert engine.is_valid_transition(
        WorkflowState.PENDING,
        WorkflowState.COMPLETED  # Cannot skip states
    ) == False

@pytest.mark.asyncio
async def test_execute_task(db, task, squad_id):
    orchestrator = TaskOrchestrator(message_bus, context_manager)

    execution_id = await orchestrator.execute_task(
        db=db,
        task=task,
        squad_id=squad_id
    )

    # Verify execution created and in ANALYZING state
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    assert execution.status == WorkflowState.ANALYZING.value
```

---

## Performance Considerations

- **State Transitions**: Database writes (moderate cost)
- **State Actions**: Can be slow (LLM calls)
- **Progress Monitoring**: Lightweight (database read)
- **Metrics Calculation**: CPU-intensive for long histories

---

## Troubleshooting

**Q: Invalid state transition error?**
- Check VALID_TRANSITIONS map in workflow_engine.py:40
- Verify current state before transition
- Review workflow state diagram

**Q: State action not executing?**
- Verify action registered in orchestrator._register_state_actions()
- Check for exceptions in action handler
- Review logs for state entry

**Q: Task stuck in BLOCKED?**
- Call resolve_blocker() with appropriate next state
- Review blocker metadata
- Consider human escalation

---

## Related Documentation

- See `../CLAUDE.md` for agent architecture
- See `../communication/CLAUDE.md` for message bus
- See `../collaboration/CLAUDE.md` for collaboration patterns
- See `/backend/services/task_execution_service.py` for database operations
