# Phase 2: Agent Base Class

**Date**: 2025-11-20
**Phase**: 2 of 6
**Priority**: P0 (Blocking)
**Status**: Pending

---

## Context

**Parent Plan**: [plan.md](./plan.md)
**Dependencies**: [phase-01-project-setup.md](./phase-01-project-setup.md)
**Next Phase**: [phase-03-specialized-agents.md](./phase-03-specialized-agents.md)

---

## Overview

Create a minimal BaseAgent class that all agents inherit from. Handles message passing, thinking process, and basic agent behavior.

**Goal**: Reusable agent foundation with clear message passing interface.

---

## Requirements

### Functional
- BaseAgent class with name, role properties
- Send/receive message methods
- Track thinking process (reasoning)
- Message history for debugging
- Simple delegation interface

### Non-Functional
- < 100 lines of code
- No external dependencies (except typing)
- Clear, documented interface
- Easy to subclass

---

## Architecture

### BaseAgent Class Design

```python
class BaseAgent:
    """
    Base class for all agents in hierarchy.

    Attributes:
        name: Agent's display name
        role: Agent's role (pm, tech_lead, developer)
        message_history: List of sent/received messages
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.message_history: List[Message] = []

    def think(self, context: str) -> str:
        """Agent's internal reasoning process"""
        pass  # Override in subclasses

    def receive(self, message: Message) -> Message:
        """Receive and process message"""
        pass  # Override in subclasses

    def send(self, to_agent: "BaseAgent", content: str,
             msg_type: str = "message") -> Message:
        """Send message to another agent"""
        pass

    def delegate(self, to_agent: "BaseAgent", task: str) -> Message:
        """Delegate task to another agent"""
        pass
```

### Message Data Structure

```python
@dataclass
class Message:
    """Message passed between agents"""
    id: str                    # Unique identifier
    timestamp: datetime        # When sent
    from_agent: str           # Sender name
    to_agent: str             # Recipient name
    msg_type: str             # "delegation", "response", "question"
    content: str              # Message content
    thinking: Optional[str]   # Agent's reasoning (optional)
    metadata: Dict[str, Any]  # Additional data
```

### Message Flow

```
PM receives task
  ↓
PM.think("How to approach this?")
  ↓
PM.delegate(tech_lead, task)
  ↓
TL.receive(message)
  ↓
TL.think("Need to break this down")
  ↓
TL.delegate(developer, subtask)
  ↓
Dev.receive(message)
  ↓
Dev.think("Implementation approach")
  ↓
Dev.send(tech_lead, result, "response")
```

---

## Related Files

**Files to Modify**:
- `/agent-squad-simple/agents/base.py` - Implement BaseAgent and Message

**Files to Reference**:
- Research: [research/researcher-01-hierarchy-patterns.md](./research/researcher-01-hierarchy-patterns.md)
- Agent-squad reference: `/Users/anderson/Documents/anderson-0/agent-squad/backend/agents/agno_base.py`

---

## Implementation Steps

1. **Define Message dataclass**
   - Import dataclass, datetime, typing
   - Create Message with all required fields
   - Add helper methods (to_dict, from_dict)

2. **Create BaseAgent class**
   - __init__ with name, role
   - Initialize message_history list

3. **Implement think() method**
   - Abstract method (raises NotImplementedError)
   - Subclasses must override
   - Returns reasoning string

4. **Implement send() method**
   - Create Message object
   - Add to sender's history
   - Add to recipient's history
   - Log to terminal (via print for now)
   - Return message

5. **Implement receive() method**
   - Abstract method
   - Subclasses process message
   - Returns response message

6. **Implement delegate() method**
   - Wrapper around send()
   - Sets msg_type="delegation"
   - Calls recipient.receive()
   - Returns response

7. **Add utility methods**
   - get_message_history()
   - clear_history()
   - __repr__() for debugging

8. **Add docstrings and comments**
   - Explain each method
   - Document expected behavior
   - Add usage examples

---

## Todo List

### P0: Critical (Must Complete)
- [ ] Import required modules (dataclass, datetime, typing, uuid)
- [ ] Define Message dataclass with all fields
- [ ] Create BaseAgent class skeleton
- [ ] Implement `__init__()` method
- [ ] Implement `think()` as abstract method
- [ ] Implement `send()` method with message creation
- [ ] Implement `receive()` as abstract method
- [ ] Implement `delegate()` method
- [ ] Add message to history in send()
- [ ] Test basic agent creation and message passing

### P1: Important
- [ ] Add Message.to_dict() helper
- [ ] Add BaseAgent.get_message_history()
- [ ] Add BaseAgent.__repr__() for debugging
- [ ] Add comprehensive docstrings
- [ ] Add type hints throughout

### P2: Nice to Have
- [ ] Add message validation
- [ ] Add error handling for invalid messages
- [ ] Add agent state tracking (idle, thinking, working)

---

## Success Criteria

### Must Have
- ✅ BaseAgent class with name, role
- ✅ Message dataclass with all fields
- ✅ send() creates and logs messages
- ✅ delegate() calls recipient.receive()
- ✅ think() is abstract (subclasses override)
- ✅ Message history tracked
- ✅ Code < 100 lines

### Should Have
- ✅ Clear docstrings and comments
- ✅ Type hints throughout
- ✅ Helper methods (to_dict, __repr__)

### Nice to Have
- ✅ Message validation
- ✅ Error handling

---

## Code Structure

```
agents/base.py (~80 lines)
├── Imports (5 lines)
├── Message dataclass (15 lines)
├── BaseAgent class (60 lines)
│   ├── __init__ (5 lines)
│   ├── think() (3 lines)
│   ├── send() (15 lines)
│   ├── receive() (3 lines)
│   ├── delegate() (10 lines)
│   └── helpers (10 lines)
└── Docstrings throughout
```

---

## Testing Plan

### Unit Tests (Manual for now)

```python
# Test 1: Agent creation
pm = BaseAgent("Project Manager", "pm")
assert pm.name == "Project Manager"
assert pm.role == "pm"
assert len(pm.message_history) == 0

# Test 2: Message creation
dev = BaseAgent("Developer", "developer")
msg = pm.send(dev, "Build login feature", "delegation")
assert msg.from_agent == "Project Manager"
assert msg.to_agent == "Developer"
assert msg.msg_type == "delegation"

# Test 3: Message history
assert len(pm.message_history) == 1
assert len(dev.message_history) == 1
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Circular imports | Medium | Low | Keep agents/ structure flat |
| Message format changes | Low | Medium | Use dataclass for flexibility |
| Performance issues | Low | Low | Minimal history (demo only) |
| Missing abstraction | Medium | Low | Clear interface design |

---

## Time Estimate

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 10 min | Straightforward class implementation |
| Senior Dev | 30 min | Design + implementation |
| Junior Dev | 1-2 hrs | Learning dataclasses, architecture |

**Complexity**: Simple

---

## Implementation Example

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

@dataclass
class Message:
    """Message exchanged between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    from_agent: str = ""
    to_agent: str = ""
    msg_type: str = "message"  # delegation, response, question
    content: str = ""
    thinking: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.msg_type,
            "content": self.content,
            "thinking": self.thinking,
            "metadata": self.metadata
        }

class BaseAgent:
    """Base class for all agents in the hierarchy"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.message_history: List[Message] = []

    def think(self, context: str) -> str:
        """Override in subclasses to implement thinking logic"""
        raise NotImplementedError("Subclasses must implement think()")

    def send(self, to_agent: "BaseAgent", content: str,
             msg_type: str = "message", thinking: Optional[str] = None) -> Message:
        """Send message to another agent"""
        msg = Message(
            from_agent=self.name,
            to_agent=to_agent.name,
            msg_type=msg_type,
            content=content,
            thinking=thinking
        )

        # Add to both histories
        self.message_history.append(msg)
        to_agent.message_history.append(msg)

        return msg

    def receive(self, message: Message) -> Message:
        """Override in subclasses to process messages"""
        raise NotImplementedError("Subclasses must implement receive()")

    def delegate(self, to_agent: "BaseAgent", task: str) -> Message:
        """Delegate task to another agent"""
        thinking = self.think(f"Delegating: {task}")
        msg = self.send(to_agent, task, msg_type="delegation", thinking=thinking)
        response = to_agent.receive(msg)
        return response

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name} ({self.role})>"
```

---

## Notes

- **Keep it simple**: No complex state management
- **No UI yet**: UI integration happens in Phase 4
- **Message history**: In-memory only (demo purposes)
- **No persistence**: Messages not saved to disk

---

## Next Steps

After completion:
1. Test agent creation and message passing
2. Mark all P0 todos as complete
3. Update plan.md Phase 2 status to "Complete"
4. Proceed to [phase-03-specialized-agents.md](./phase-03-specialized-agents.md)
