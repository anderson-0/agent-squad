# Collaboration Patterns Module

## Overview

The `collaboration/` module implements structured patterns for multi-agent collaboration. These patterns enable agents to work together effectively on complex problems through well-defined interaction protocols.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Collaboration Patterns                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │     CollaborationPatternManager (Facade)           │    │
│  │     Unified interface for all patterns             │    │
│  └──────────┬──────────────┬──────────────┬───────────┘    │
│             │              │              │                 │
│             ▼              ▼              ▼                 │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────┐   │
│  │ Problem        │ │ Code Review  │ │    Standup     │   │
│  │ Solving        │ │   Pattern    │ │    Pattern     │   │
│  │ Pattern        │ │              │ │                │   │
│  │                │ │ Dev ↔ TL     │ │ PM → All       │   │
│  │ Broadcast Q&A  │ │ Iterative    │ │ Daily Updates  │   │
│  └────────────────┘ └──────────────┘ └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `patterns.py` - Pattern Manager

**Purpose**: Unified facade for all collaboration patterns

Provides convenience methods that delegate to specific pattern implementations.

**Key Methods**:
- `ask_team_for_help()`: Problem solving (Location: `patterns.py:53`)
- `request_code_review()`: Code review (Location: `patterns.py:165`)
- `conduct_daily_standup()`: Standup (Location: `patterns.py:251`)

---

### 2. `problem_solving.py` - Collaborative Q&A

**Purpose**: Enable agents to ask questions and get collaborative solutions from the team

**Pattern Flow**:
```
Agent A has a problem
↓
1. Broadcast question to relevant agents
   - Optional: Target specific roles
   - Optional: Set urgency level
↓
2. Agents respond with answers
   - Within time window (default: 60 seconds)
   - Provide solutions, suggestions, alternatives
↓
3. Synthesize responses
   - Aggregate all answers
   - Identify best solution
   - Combine complementary suggestions
↓
4. Return synthesized solution to Agent A
```

**Key Methods**:

#### `solve_problem_collaboratively()`
Main entry point for collaborative problem solving.

```python
solution = await problem_solving.solve_problem_collaboratively(
    db=db,
    asker_id=backend_dev_id,
    task_execution_id=execution_id,
    question="How should we implement caching?",
    context={
        "issue_description": "API response time is 2s",
        "attempted_solutions": ["Added indexes", "Optimized queries"],
        "why_stuck": "Still too slow for user requirements"
    },
    relevant_roles=["tech_lead", "backend_developer"]
)

# Returns:
# {
#     "question": "...",
#     "answers": [...],
#     "recommendation": "Use Redis for caching...",
#     "answer_count": 3,
#     "relevant_roles_responded": ["tech_lead", "backend_developer"]
# }
```

#### Workflow Methods:

```python
# 1. Broadcast question (async)
question_id = await problem_solving.broadcast_question(...)

# 2. Wait for answers (or continue working)
await asyncio.sleep(60)

# 3. Collect answers
answers = await problem_solving.collect_answers(...)

# 4. Synthesize solution
solution = await problem_solving.synthesize_solution(...)
```

**Business Rules**:
1. Questions can be broadcast or targeted to specific roles
2. Default wait time: 60 seconds for responses
3. Minimum 1 answer required for synthesis
4. Synthesis uses LLM to combine answers intelligently
5. Questions stored in message history

---

### 3. `code_review.py` - Code Review Pattern

**Purpose**: Structured code review cycle between Developer and Tech Lead

**Pattern Flow**:
```
Developer completes implementation
↓
1. Request Review
   - Dev submits PR with description
   - Self-review notes (optional)
   - Context: task, ACs, changes
↓
2. Tech Lead Reviews
   - Reviews code against ACs
   - Checks quality, security, performance
   - Provides detailed feedback
   - Decision: APPROVED | CHANGES_REQUESTED | COMMENTED
↓
3. Developer Responds
   - Addresses feedback
   - Makes changes
   - Requests re-review (if needed)
↓
4. Iterate until APPROVED
```

**Key Methods**:

#### `complete_review_cycle()`
Full review cycle from request to approval.

```python
review_result = await code_review.complete_review_cycle(
    db=db,
    developer_id=backend_dev_id,
    tech_lead_id=tech_lead_id,
    task_execution_id=execution_id,
    pr_url="https://github.com/org/repo/pull/123",
    pr_description="Implement user authentication",
    changes_summary="Added login API, JWT middleware, tests",
    code_diff="diff --git a/...",
    acceptance_criteria=[
        "User can login with email/password",
        "JWT token generated",
        "Tests pass"
    ],
    self_review_notes="Followed security best practices"
)

# Returns:
# {
#     "approval_status": "approved",
#     "review_feedback": {...},
#     "iterations": 1,
#     "comments": [...],
#     "final_decision": "approved"
# }
```

#### Individual Steps:

```python
# 1. Request review
review_id = await code_review.request_review(...)

# 2. Tech Lead performs review
review_feedback = await tech_lead.review_code(...)

# 3. Developer responds to feedback
action_plan = await developer.respond_to_review_feedback(...)

# 4. Make changes and re-request review
```

**Business Rules**:
1. All PRs MUST be reviewed by Tech Lead
2. Review checks: quality, security, performance, testing
3. Changes requested must be addressed before approval
4. Multiple review iterations supported
5. Review feedback stored in database

---

### 4. `standup.py` - Daily Standup Pattern

**Purpose**: Async daily standup for progress tracking and blocker identification

**Pattern Flow**:
```
PM initiates standup
↓
1. Request Updates
   - PM sends standup request to all agents
   - Agents respond with:
     * Yesterday's progress
     * Today's plan
     * Blockers
↓
2. Collect Updates
   - Wait for responses (default: 5 minutes)
   - Track who responded
↓
3. Analyze Updates
   - PM analyzes all responses
   - Identifies blockers
   - Identifies at-risk tasks
   - Identifies who needs help
   - Identifies highlights
↓
4. Broadcast Summary
   - PM shares analysis with team
   - Action items for PM
   - Follow-up needed
```

**Key Methods**:

#### `conduct_standup()`
Full standup cycle.

```python
standup_result = await standup.conduct_standup(
    db=db,
    pm_id=pm_id,
    squad_id=squad_id,
    task_execution_id=execution_id  # optional
)

# Returns:
# {
#     "standup_id": "...",
#     "updates_count": 4,
#     "blockers_identified": [
#         {"agent": "backend_dev", "blocker": "Waiting for API spec"}
#     ],
#     "at_risk_members": ["frontend_dev"],
#     "highlights": ["Backend API completed"],
#     "pm_action_items": [
#         "Follow up with frontend_dev on UI progress",
#         "Provide API spec to backend_dev"
#     ]
# }
```

#### Individual Steps:

```python
# 1. Request updates (async)
standup_id = await standup.request_updates(...)

# 2. Wait for responses
await asyncio.sleep(300)  # 5 minutes

# 3. Collect updates
updates = await standup.collect_updates(...)

# 4. Analyze
analysis = await standup.analyze_updates(...)

# 5. Broadcast summary
await standup.broadcast_summary(...)
```

**Standup Update Format**:
```python
{
    "agent_id": "...",
    "agent_role": "backend_developer",
    "yesterday": "Completed login API, wrote tests",
    "today": "Working on password reset feature",
    "blockers": ["Need password reset email template"],
    "progress_percentage": 70,
    "needs_help": False
}
```

**Business Rules**:
1. Standups conducted daily (or on-demand)
2. All squad members expected to respond
3. Non-responders flagged for follow-up
4. Blockers escalated immediately
5. Analysis shared with team

---

## Integration with Other Modules

### Communication
- All patterns use Message Bus for agent communication
- Pattern messages persist in conversation history
- SSE broadcasts pattern events to frontend

### Context
- Context Manager provides relevant information
- RAG retrieves similar past problems/solutions
- Memory stores pattern state

### Orchestration
- Patterns invoked at specific workflow states
- Code review in REVIEWING state
- Problem solving when agent is blocked
- Standup for IN_PROGRESS monitoring

---

## Common Pattern Scenarios

### Scenario 1: Developer Stuck on Implementation

```python
# Developer encounters problem
solution = await collaboration_manager.ask_team_for_help(
    db=db,
    asker_id=developer_id,
    task_execution_id=execution_id,
    question="How to implement rate limiting?",
    context={
        "issue_description": "Need to rate limit API endpoints",
        "attempted_solutions": ["Researched libraries"],
        "why_stuck": "Unclear which approach fits our architecture"
    },
    relevant_roles=["tech_lead", "backend_developer"]
)

# Tech Lead and other Backend Devs respond
# Solution synthesized and returned to developer
```

### Scenario 2: Code Review Cycle

```python
# Developer completes feature
review = await collaboration_manager.request_code_review(
    db=db,
    developer_id=developer_id,
    tech_lead_id=tech_lead_id,
    task_execution_id=execution_id,
    pr_url="...",
    pr_description="Implement rate limiting",
    changes_summary="Added middleware, tests, docs"
)

# Tech Lead reviews and requests changes
# Developer addresses feedback
# Re-review until approved
```

### Scenario 3: Daily Standup

```python
# PM conducts standup
standup = await collaboration_manager.conduct_daily_standup(
    db=db,
    pm_id=pm_id,
    squad_id=squad_id
)

# PM reviews results
# Identifies: frontend_dev is blocked
# Action: Provide needed resources to unblock
```

---

## Business Rules Summary

### Problem Solving
1. Questions broadcast to relevant roles or all agents
2. Wait time configurable (default: 60s)
3. Minimum 1 answer for synthesis
4. Best solution identified via LLM synthesis
5. Questions stored for future reference (RAG)

### Code Review
1. All PRs reviewed by Tech Lead before merge
2. Self-review encouraged but not required
3. Multiple review iterations supported
4. Approval required before deployment
5. Review feedback actionable and specific

### Standup
1. Daily or on-demand
2. All squad members participate
3. Non-responders tracked
4. Blockers escalated immediately
5. PM provides action items

---

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_problem_solving(db):
    pattern = ProblemSolvingPattern(message_bus, context_manager)

    solution = await pattern.solve_problem_collaboratively(
        db=db,
        asker_id=agent_id,
        task_execution_id=execution_id,
        question="Test question?",
        context={"issue": "test"},
        relevant_roles=["tech_lead"]
    )

    assert "recommendation" in solution

@pytest.mark.asyncio
async def test_code_review(db):
    pattern = CodeReviewPattern(message_bus)

    review_id = await pattern.request_review(
        db=db,
        developer_id=dev_id,
        tech_lead_id=tl_id,
        task_execution_id=execution_id,
        pr_url="...",
        pr_description="Test PR",
        changes_summary="Test changes"
    )

    assert review_id is not None

@pytest.mark.asyncio
async def test_standup(db):
    pattern = StandupPattern(message_bus)

    result = await pattern.conduct_standup(
        db=db,
        pm_id=pm_id,
        squad_id=squad_id
    )

    assert "standup_id" in result
    assert "blockers_identified" in result
```

---

## Performance Considerations

- **Problem Solving**: Wait time impacts response latency
- **Code Review**: LLM calls for review can be slow (3-10s)
- **Standup**: Collecting all responses takes time (5min default)

**Optimizations**:
- Parallel LLM calls where possible
- Cache common questions/answers
- Reduce wait times for urgent questions
- Pre-warm LLM connections

---

## Related Documentation

- See `../CLAUDE.md` for agent architecture
- See `../communication/CLAUDE.md` for message bus
- See `../orchestration/CLAUDE.md` for workflow integration
- See `../specialized/CLAUDE.md` for agent capabilities
