# Phase 4: Terminal UI

**Date**: 2025-11-20
**Phase**: 4 of 6
**Priority**: P0 (Blocking)
**Status**: Pending

---

## Context

**Parent Plan**: [plan.md](./plan.md)
**Dependencies**: [phase-02-agent-base.md](./phase-02-agent-base.md)
**Next Phase**: [phase-05-main-demo.md](./phase-05-main-demo.md)

---

## Overview

Create Rich-based terminal visualization that displays agent messages, thinking processes, and hierarchy structure in real-time.

**Goal**: Beautiful, clear terminal output showing agent communication.

---

## Requirements

### Functional
- Display agent messages with colors
- Show hierarchy with indentation
- Display agent thinking process
- Timestamp each message
- Clear visual distinction between agents
- Show message types (delegation, response)

### Non-Functional
- Use Rich library only
- < 150 lines of code
- Fast rendering (< 10ms per message)
- Works in any terminal
- Clear, readable output

---

## Architecture

### UI Components

```
┌─────────────────────────────────────────────┐
│  Terminal UI                                 │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  AgentDisplay                          │ │
│  │  - Display single agent message        │ │
│  │  - Show thinking process               │ │
│  │  - Color-coded by role                 │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  MessageDisplay                        │ │
│  │  - Format message content              │ │
│  │  - Show metadata (type, timestamp)     │ │
│  │  - Hierarchy indentation               │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  HierarchyDisplay                      │ │
│  │  - Show full message flow              │ │
│  │  - Track message sequence              │ │
│  │  - Render all messages                 │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Color Scheme

```
Project Manager:  Bold Blue
Tech Lead:        Bold Green
Developer:        Bold Cyan
User:             Bold Magenta
Thinking:         Dim Yellow
Message Content:  White
Timestamps:       Dim White
```

### Output Format

```
[12:34:56] 👤 User → Project Manager
           Task: "Implement user authentication"

[12:34:56] 💭 Project Manager thinking:
           "Analyzing task: Implement user authentication.
            This requires technical analysis.
            Will delegate to Tech Lead."

[12:34:57] 📩 Project Manager → Tech Lead [DELEGATION]
           ├─ Task: "Implement user authentication"
           └─ Thinking: "Tech Lead has expertise in auth systems"

[12:34:57] 💭 Tech Lead thinking:
           "Technical analysis: Implement user authentication.
            Breaking down into implementation steps.
            Will delegate to Developer."

[12:34:58] 📩 Tech Lead → Developer [DELEGATION]
           ├─ Task: "Implement user authentication"
           └─ Thinking: "Developer will implement core logic"

[12:34:58] 💭 Developer thinking:
           "Understanding requirements: Implement user authentication.
            Planning implementation approach."

[12:34:59] 📩 Developer → Tech Lead [RESPONSE]
           ├─ Result: "# Pseudo-code for: Implement user authentication
              def solution():
                  validate_requirements()
                  implement_feature()
                  write_tests()
                  return 'Feature implemented successfully'"
           └─ Thinking: "Implemented solution using best practices."

[12:35:00] 📩 Tech Lead → Project Manager [RESPONSE]
           ├─ Result: "Implementation complete: [code]"
           └─ Thinking: "Developer implemented solution. Review: Code looks good."

[12:35:01] ✅ Task Complete!
```

---

## Related Files

**Files to Create**:
- `/agent-squad-simple/ui/terminal.py` - Terminal UI implementation

**Files to Reference**:
- Research: [research/researcher-02-terminal-ui.md](./research/researcher-02-terminal-ui.md)
- Rich docs: https://rich.readthedocs.io/

---

## Implementation Steps

1. **Import Rich components**
   - Console, Text, Panel, Rule
   - Syntax for code formatting
   - datetime for timestamps

2. **Create AgentDisplay class**
   - get_agent_color() - return color by role
   - get_agent_emoji() - return emoji by role
   - format_agent_name() - styled agent name

3. **Create MessageDisplay class**
   - format_thinking() - show agent reasoning
   - format_delegation() - show task delegation
   - format_response() - show result
   - format_timestamp() - show time

4. **Create HierarchyDisplay class**
   - __init__ with Rich Console
   - display_message() - render single message
   - display_thinking() - render thinking process
   - display_task_start() - render task header
   - display_task_complete() - render completion

5. **Add helper functions**
   - indent_text() - add hierarchy indentation
   - format_content() - truncate long content
   - get_message_type_emoji() - emoji by type

6. **Add main display function**
   - display_workflow() - render entire message flow
   - Takes message history
   - Renders in sequence

7. **Add styling configuration**
   - Define colors as constants
   - Define emojis as constants
   - Make customizable

8. **Test rendering**
   - Test each message type
   - Verify colors work
   - Check indentation

---

## Todo List

### P0: Critical (Must Complete)
- [ ] Import Rich components (Console, Text, Panel, Rule, Syntax)
- [ ] Create AgentDisplay class with color mapping
- [ ] Implement get_agent_color() method
- [ ] Implement get_agent_emoji() method
- [ ] Create MessageDisplay class
- [ ] Implement format_thinking() method
- [ ] Implement format_delegation() method
- [ ] Implement format_response() method
- [ ] Create HierarchyDisplay class with Console
- [ ] Implement display_message() method
- [ ] Implement display_thinking() method
- [ ] Implement display_task_start() method
- [ ] Implement display_task_complete() method
- [ ] Add timestamp formatting
- [ ] Test with sample messages

### P1: Important
- [ ] Add code syntax highlighting for pseudo-code
- [ ] Add indentation for hierarchy levels
- [ ] Add message type emojis
- [ ] Add Panel borders for sections
- [ ] Implement display_workflow() function

### P2: Nice to Have
- [ ] Add color configuration options
- [ ] Add verbose/quiet modes
- [ ] Add message filtering
- [ ] Add export to file option

---

## Success Criteria

### Must Have
- ✅ Messages display with colors
- ✅ Agent names color-coded by role
- ✅ Thinking process visible
- ✅ Timestamps on each message
- ✅ Clear visual hierarchy
- ✅ Message types distinguishable
- ✅ Code < 150 lines

### Should Have
- ✅ Code syntax highlighting
- ✅ Emojis for visual cues
- ✅ Panel borders for sections
- ✅ Indentation for delegation levels

### Nice to Have
- ✅ Configurable colors
- ✅ Verbose/quiet modes
- ✅ Export capability

---

## Code Example

```python
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from datetime import datetime
from agents.base import Message

# Color scheme
COLORS = {
    "project_manager": "bold blue",
    "tech_lead": "bold green",
    "developer": "bold cyan",
    "user": "bold magenta",
    "thinking": "dim yellow",
    "timestamp": "dim white"
}

EMOJIS = {
    "project_manager": "👔",
    "tech_lead": "🎯",
    "developer": "💻",
    "user": "👤",
    "thinking": "💭",
    "delegation": "📩",
    "response": "📤",
    "complete": "✅"
}

class AgentDisplay:
    """Display agent information with styling"""

    @staticmethod
    def get_agent_color(role: str) -> str:
        return COLORS.get(role, "white")

    @staticmethod
    def get_agent_emoji(role: str) -> str:
        return EMOJIS.get(role, "🤖")

    @staticmethod
    def format_agent_name(agent_name: str, role: str) -> Text:
        emoji = AgentDisplay.get_agent_emoji(role)
        color = AgentDisplay.get_agent_color(role)
        return Text(f"{emoji} {agent_name}", style=color)

class MessageDisplay:
    """Display messages with formatting"""

    @staticmethod
    def format_timestamp(dt: datetime) -> Text:
        time_str = dt.strftime("%H:%M:%S")
        return Text(f"[{time_str}]", style=COLORS["timestamp"])

    @staticmethod
    def format_thinking(thinking: str) -> Panel:
        content = Text(thinking, style=COLORS["thinking"])
        return Panel(content, title="💭 Thinking", border_style="yellow")

    @staticmethod
    def format_message_type(msg_type: str) -> Text:
        emoji = EMOJIS.get(msg_type, "📨")
        return Text(f"{emoji} {msg_type.upper()}", style="bold")

class HierarchyDisplay:
    """Display full agent hierarchy and message flow"""

    def __init__(self):
        self.console = Console()

    def display_task_start(self, task: str):
        """Display task start banner"""
        self.console.print()
        self.console.print(Panel(
            Text(task, style="bold white"),
            title="🚀 New Task",
            border_style="blue"
        ))
        self.console.print()

    def display_thinking(self, agent_name: str, role: str, thinking: str):
        """Display agent thinking process"""
        timestamp = MessageDisplay.format_timestamp(datetime.now())
        agent = AgentDisplay.format_agent_name(agent_name, role)

        self.console.print(timestamp, agent, "thinking:")
        self.console.print(f"  {thinking}", style=COLORS["thinking"])
        self.console.print()

    def display_message(self, message: Message):
        """Display a single message"""
        timestamp = MessageDisplay.format_timestamp(message.timestamp)
        msg_type = MessageDisplay.format_message_type(message.msg_type)

        self.console.print(
            timestamp,
            Text(message.from_agent, style="bold"),
            "→",
            Text(message.to_agent, style="bold"),
            msg_type
        )

        # Show content with indentation
        self.console.print(f"  ├─ Content: {message.content[:100]}...")

        # Show thinking if present
        if message.thinking:
            self.console.print(f"  └─ Thinking: {message.thinking[:100]}...")

        self.console.print()

    def display_task_complete(self):
        """Display task completion banner"""
        self.console.print(Panel(
            Text("Task completed successfully!", style="bold green"),
            title="✅ Complete",
            border_style="green"
        ))

    def display_workflow(self, messages: list[Message]):
        """Display entire workflow"""
        for msg in messages:
            self.display_message(msg)

# Example usage
display = HierarchyDisplay()
display.display_task_start("Implement user authentication")
# ... display messages ...
display.display_task_complete()
```

---

## Testing Plan

### Manual Tests

```python
from ui.terminal import HierarchyDisplay, MessageDisplay, AgentDisplay
from agents.base import Message
from datetime import datetime

# Test 1: Color mapping
assert AgentDisplay.get_agent_color("project_manager") == "bold blue"
assert AgentDisplay.get_agent_emoji("developer") == "💻"

# Test 2: Message display
display = HierarchyDisplay()
msg = Message(
    from_agent="PM",
    to_agent="TL",
    msg_type="delegation",
    content="Test task",
    thinking="Test thinking"
)
display.display_message(msg)  # Should render with colors

# Test 3: Workflow display
messages = [msg1, msg2, msg3]
display.display_workflow(messages)  # Should render sequence
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Terminal compatibility | Low | Low | Rich handles most terminals |
| Color rendering issues | Low | Medium | Use fallback colors |
| Long message truncation | Low | Medium | Implement smart truncation |
| Performance with many messages | Low | Low | Rich is fast, demo has few messages |

---

## Time Estimate

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 10 min | Straightforward Rich usage |
| Senior Dev | 45 min | Learning Rich, styling |
| Junior Dev | 2 hrs | Learning Rich, testing different terminals |

**Complexity**: Simple

---

## Notes

- **Rich is powerful**: Can do much more than we need
- **Keep it simple**: Focus on readability
- **Test in different terminals**: May render differently
- **Color fallbacks**: Some terminals don't support colors

---

## Next Steps

After completion:
1. Test rendering with sample messages
2. Verify colors work in different terminals
3. Mark all P0 todos as complete
4. Update plan.md Phase 4 status to "Complete"
5. Proceed to [phase-05-main-demo.md](./phase-05-main-demo.md)
