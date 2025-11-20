# Phase 3: Specialized Agents

**Date**: 2025-11-20
**Phase**: 3 of 6
**Priority**: P0 (Blocking)
**Status**: Pending

---

## Context

**Parent Plan**: [plan.md](./plan.md)
**Dependencies**: [phase-02-agent-base.md](./phase-02-agent-base.md)
**Next Phase**: [phase-04-terminal-ui.md](./phase-04-terminal-ui.md)

---

## Overview

Implement three specialized agents (ProjectManager, TechLead, Developer) that inherit from BaseAgent. Each agent has specific thinking patterns and delegation logic.

**Goal**: Working hierarchy with realistic agent behaviors.

---

## Requirements

### Functional
- ProjectManager: Receives tasks, delegates to TechLead
- TechLead: Analyzes tasks, delegates to Developer
- Developer: Implements tasks, returns results
- Each agent has unique thinking process
- Realistic task processing flow

### Non-Functional
- Each agent < 80 lines
- Total < 240 lines for all three
- Clear role separation
- Hardcoded logic (no LLM for demo)

---

## Architecture

### Agent Hierarchy

```
┌──────────────────┐
│ Project Manager  │  - Receives external tasks
│                  │  - Validates requirements
│                  │  - Delegates to Tech Lead
└────────┬─────────┘
         │ delegates
         ↓
┌──────────────────┐
│   Tech Lead      │  - Analyzes complexity
│                  │  - Breaks down into subtasks
│                  │  - Delegates to Developer
└────────┬─────────┘
         │ delegates
         ↓
┌──────────────────┐
│   Developer      │  - Implements solution
│                  │  - Returns result
│                  │  - Reports back to Tech Lead
└──────────────────┘
```

### Agent Responsibilities

**ProjectManager**:
- Validate task is clear
- Assess priority and scope
- Delegate to TechLead
- Monitor progress (for demo: just receive response)

**TechLead**:
- Analyze technical approach
- Break down into implementation steps
- Delegate to Developer
- Review and approve work

**Developer**:
- Understand requirements
- Implement solution
- Write pseudo-code (for demo)
- Return completed work

---

## Related Files

**Files to Create**:
- `/agent-squad-simple/agents/project_manager.py` - ProjectManager class
- `/agent-squad-simple/agents/tech_lead.py` - TechLead class
- `/agent-squad-simple/agents/developer.py` - Developer class

**Files to Reference**:
- Base class: `/agent-squad-simple/agents/base.py`
- Agent-squad PM: `/Users/anderson/Documents/anderson-0/agent-squad/backend/agents/specialized/agno_project_manager.py`

---

## Implementation Steps

### ProjectManager Agent

1. **Create ProjectManager class**
   - Inherit from BaseAgent
   - __init__ with tech_lead reference

2. **Implement think() method**
   - Analyze task description
   - Determine priority
   - Assess if task is clear
   - Return reasoning string

3. **Implement receive() method**
   - Process incoming task
   - Call think() to reason
   - Delegate to tech_lead
   - Return response

4. **Add process_task() helper**
   - Entry point for external tasks
   - Creates Message object
   - Calls receive()

### TechLead Agent

1. **Create TechLead class**
   - Inherit from BaseAgent
   - __init__ with developer reference

2. **Implement think() method**
   - Analyze technical complexity
   - Identify implementation approach
   - Break down into steps
   - Return reasoning string

3. **Implement receive() method**
   - Process delegation from PM
   - Call think() to analyze
   - Delegate to developer
   - Review developer's response
   - Return result to PM

4. **Add review_work() helper**
   - Simulate code review
   - Validate solution
   - Return approval message

### Developer Agent

1. **Create Developer class**
   - Inherit from BaseAgent
   - No sub-agents (leaf node)

2. **Implement think() method**
   - Understand requirements
   - Plan implementation
   - Consider edge cases
   - Return reasoning string

3. **Implement receive() method**
   - Process delegation from TL
   - Call think() to plan
   - Implement solution (pseudo-code)
   - Return result to TL

4. **Add implement() helper**
   - Generate pseudo-code
   - Simulate work
   - Return implementation result

---

## Todo List

### P0: Critical (Must Complete)

**ProjectManager**:
- [ ] Create ProjectManager class inheriting BaseAgent
- [ ] Implement __init__ with tech_lead parameter
- [ ] Implement think() with task validation logic
- [ ] Implement receive() to handle messages
- [ ] Implement process_task() as entry point
- [ ] Add delegation logic to tech_lead

**TechLead**:
- [ ] Create TechLead class inheriting BaseAgent
- [ ] Implement __init__ with developer parameter
- [ ] Implement think() with complexity analysis
- [ ] Implement receive() to handle PM delegation
- [ ] Implement review_work() helper
- [ ] Add delegation logic to developer

**Developer**:
- [ ] Create Developer class inheriting BaseAgent
- [ ] Implement __init__ (no sub-agents)
- [ ] Implement think() with implementation planning
- [ ] Implement receive() to handle TL delegation
- [ ] Implement implement() helper with pseudo-code generation
- [ ] Add response logic back to TL

### P1: Important
- [ ] Add docstrings to all classes and methods
- [ ] Add type hints throughout
- [ ] Add realistic thinking patterns
- [ ] Test full hierarchy flow (PM → TL → Dev → TL → PM)

### P2: Nice to Have
- [ ] Add validation logic for messages
- [ ] Add error handling for edge cases
- [ ] Add more detailed thinking processes
- [ ] Add task complexity estimation

---

## Success Criteria

### Must Have
- ✅ Three agents: ProjectManager, TechLead, Developer
- ✅ Each inherits from BaseAgent
- ✅ Each implements think() and receive()
- ✅ Full delegation chain works (PM → TL → Dev)
- ✅ Responses flow back up (Dev → TL → PM)
- ✅ Total code < 240 lines

### Should Have
- ✅ Realistic thinking patterns
- ✅ Clear docstrings and comments
- ✅ Type hints throughout
- ✅ Helper methods for clarity

### Nice to Have
- ✅ Validation logic
- ✅ Error handling
- ✅ Detailed reasoning

---

## Code Examples

### ProjectManager

```python
from agents.base import BaseAgent, Message

class ProjectManager(BaseAgent):
    """
    Project Manager agent - top of hierarchy.
    Receives tasks, validates, and delegates to Tech Lead.
    """

    def __init__(self, name: str, tech_lead: "TechLead"):
        super().__init__(name, "project_manager")
        self.tech_lead = tech_lead

    def think(self, context: str) -> str:
        """Analyze task and plan delegation"""
        # Simulate PM thinking process
        return f"Analyzing task: {context}. This requires technical analysis. Will delegate to Tech Lead."

    def receive(self, message: Message) -> Message:
        """Process incoming message"""
        thinking = self.think(message.content)

        # Delegate to tech lead
        response = self.delegate(self.tech_lead, message.content)

        # Return final result
        return self.send(
            message.from_agent,
            f"Task completed: {response.content}",
            msg_type="response",
            thinking=f"Tech Lead completed task. Result looks good."
        )

    def process_task(self, task_description: str) -> Message:
        """Entry point for external tasks"""
        # Create incoming message
        msg = Message(
            from_agent="User",
            to_agent=self.name,
            msg_type="task",
            content=task_description
        )

        # Process and return result
        return self.receive(msg)
```

### TechLead

```python
from agents.base import BaseAgent, Message

class TechLead(BaseAgent):
    """
    Tech Lead agent - middle of hierarchy.
    Analyzes tasks, breaks down work, delegates to Developer.
    """

    def __init__(self, name: str, developer: "Developer"):
        super().__init__(name, "tech_lead")
        self.developer = developer

    def think(self, context: str) -> str:
        """Analyze technical approach"""
        return f"Technical analysis: {context}. Breaking down into implementation steps. Will delegate to Developer."

    def receive(self, message: Message) -> Message:
        """Process delegation from PM"""
        thinking = self.think(message.content)

        # Delegate to developer
        response = self.delegate(self.developer, message.content)

        # Review work
        review = self.review_work(response.content)

        # Return to PM
        return self.send(
            message.from_agent,
            f"Implementation complete: {response.content}",
            msg_type="response",
            thinking=f"Developer implemented solution. Review: {review}"
        )

    def review_work(self, work: str) -> str:
        """Simulate code review"""
        return "Code looks good. Tests passed. Ready for deployment."
```

### Developer

```python
from agents.base import BaseAgent, Message

class Developer(BaseAgent):
    """
    Developer agent - bottom of hierarchy.
    Implements tasks and returns results.
    """

    def __init__(self, name: str):
        super().__init__(name, "developer")

    def think(self, context: str) -> str:
        """Plan implementation"""
        return f"Understanding requirements: {context}. Planning implementation approach."

    def receive(self, message: Message) -> Message:
        """Process delegation from TL"""
        thinking = self.think(message.content)

        # Implement solution
        implementation = self.implement(message.content)

        # Return to TL
        return self.send(
            message.from_agent,
            implementation,
            msg_type="response",
            thinking=f"Implemented solution using best practices."
        )

    def implement(self, task: str) -> str:
        """Generate pseudo-code implementation"""
        # Simulate implementation
        return f"""
        # Pseudo-code for: {task}
        def solution():
            # Step 1: Validate input
            validate_requirements()

            # Step 2: Implement core logic
            implement_feature()

            # Step 3: Add tests
            write_tests()

            # Step 4: Return result
            return "Feature implemented successfully"
        """
```

---

## Testing Plan

### Integration Test

```python
# Create agent hierarchy
developer = Developer("Alice")
tech_lead = TechLead("Bob", developer)
project_manager = ProjectManager("Carol", tech_lead)

# Process task
task = "Implement user authentication with OAuth2"
result = project_manager.process_task(task)

# Verify message flow
assert len(project_manager.message_history) > 0
assert len(tech_lead.message_history) > 0
assert len(developer.message_history) > 0

# Verify result
assert "implemented successfully" in result.content.lower()
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Circular dependencies | High | Low | Import at runtime if needed |
| Overly complex thinking | Low | Medium | Keep thinking simple, focused |
| Missing delegation logic | Medium | Low | Test full flow thoroughly |
| Type annotation issues | Low | Low | Use forward references |

---

## Time Estimate

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 15 min | Straightforward implementations |
| Senior Dev | 45 min | Design + implementation |
| Junior Dev | 2-3 hrs | Learning patterns, testing |

**Complexity**: Simple

---

## Notes

- **No LLM calls**: All logic is hardcoded for demo
- **Realistic behavior**: Simulate real agent thinking
- **Clear separation**: Each agent has distinct responsibilities
- **Forward references**: Use strings for type hints to avoid circular imports

---

## Next Steps

After completion:
1. Test each agent individually
2. Test full hierarchy flow (PM → TL → Dev → TL → PM)
3. Mark all P0 todos as complete
4. Update plan.md Phase 3 status to "Complete"
5. Proceed to [phase-04-terminal-ui.md](./phase-04-terminal-ui.md)
