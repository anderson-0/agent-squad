# Phase 5: Main Demo Entry Point

**Date**: 2025-11-20
**Phase**: 5 of 6
**Priority**: P0 (Blocking)
**Status**: Pending

---

## Context

**Parent Plan**: [plan.md](./plan.md)
**Dependencies**:
- [phase-03-specialized-agents.md](./phase-03-specialized-agents.md)
- [phase-04-terminal-ui.md](./phase-04-terminal-ui.md)
**Next Phase**: [phase-06-documentation.md](./phase-06-documentation.md)

---

## Overview

Create main.py entry point that demonstrates the full agent hierarchy in action with multiple example workflows.

**Goal**: Runnable demo showing agent collaboration with beautiful terminal output.

---

## Requirements

### Functional
- main() function as entry point
- Create agent hierarchy (PM → TL → Dev)
- Run example workflows
- Display all messages with UI
- Show completion summary

### Non-Functional
- < 100 lines of code
- Runs with `python main.py`
- Completes in < 1 second
- Clear, impressive output

---

## Architecture

### Workflow Flow

```
1. Initialize agents
   ├─ Create Developer
   ├─ Create TechLead (with Developer)
   └─ Create ProjectManager (with TechLead)

2. Initialize UI
   └─ Create HierarchyDisplay

3. Run example workflow
   ├─ Display task start
   ├─ PM processes task
   ├─ Display thinking at each level
   ├─ Display all messages
   └─ Display completion

4. Show summary
   ├─ Total messages exchanged
   ├─ Agents involved
   └─ Execution time
```

### Example Workflows

1. **Basic Authentication Task**
   - "Implement user authentication with OAuth2"
   - Shows full delegation chain
   - Developer returns implementation

2. **Feature Request**
   - "Add real-time notifications to dashboard"
   - Shows technical analysis
   - Developer breaks down into steps

3. **Bug Fix**
   - "Fix memory leak in user session management"
   - Shows debugging approach
   - Developer identifies root cause

---

## Related Files

**Files to Create**:
- `/agent-squad-simple/main.py` - Main entry point

**Files to Use**:
- `/agent-squad-simple/agents/project_manager.py`
- `/agent-squad-simple/agents/tech_lead.py`
- `/agent-squad-simple/agents/developer.py`
- `/agent-squad-simple/ui/terminal.py`

---

## Implementation Steps

1. **Import required modules**
   - Import agent classes
   - Import UI display
   - Import time for execution tracking

2. **Create setup_agents() function**
   - Initialize Developer
   - Initialize TechLead with Developer
   - Initialize ProjectManager with TechLead
   - Return agent hierarchy

3. **Create run_workflow() function**
   - Takes PM, display, task description
   - Display task start banner
   - Process task through PM
   - Collect all messages from history
   - Display workflow with UI
   - Return result

4. **Create display_summary() function**
   - Count total messages
   - List agents involved
   - Show execution time
   - Display statistics

5. **Create main() function**
   - Setup agents
   - Initialize display
   - Run multiple example workflows
   - Display summary for each
   - Show completion banner

6. **Add example workflows**
   - Define 2-3 example tasks
   - Each demonstrates different aspect
   - Clear, realistic scenarios

7. **Add __main__ guard**
   - Run main() when executed directly
   - Handle KeyboardInterrupt gracefully

8. **Add execution timing**
   - Track start/end time
   - Display execution duration

---

## Todo List

### P0: Critical (Must Complete)
- [ ] Import agent classes (ProjectManager, TechLead, Developer)
- [ ] Import UI display (HierarchyDisplay)
- [ ] Import time module for execution tracking
- [ ] Create setup_agents() function
- [ ] Initialize Developer agent
- [ ] Initialize TechLead agent with Developer
- [ ] Initialize ProjectManager agent with TechLead
- [ ] Create run_workflow() function
- [ ] Display task start banner
- [ ] Process task through PM
- [ ] Collect message history
- [ ] Display workflow with UI
- [ ] Create display_summary() function
- [ ] Create main() function
- [ ] Define example workflow 1 (authentication)
- [ ] Define example workflow 2 (feature request)
- [ ] Add __main__ guard
- [ ] Test execution with `python main.py`

### P1: Important
- [ ] Add execution timing
- [ ] Add summary statistics
- [ ] Add graceful error handling
- [ ] Add workflow separator (visual)
- [ ] Define example workflow 3 (bug fix)

### P2: Nice to Have
- [ ] Add command-line arguments (optional workflows)
- [ ] Add verbose mode flag
- [ ] Add interactive mode (user input)
- [ ] Add export results option

---

## Success Criteria

### Must Have
- ✅ Runs with `python main.py`
- ✅ Shows full agent hierarchy in action
- ✅ Displays all messages with colors
- ✅ Shows agent thinking processes
- ✅ Completes in < 1 second
- ✅ At least 2 example workflows
- ✅ Code < 100 lines

### Should Have
- ✅ Execution timing displayed
- ✅ Summary statistics
- ✅ Clear visual separation between workflows
- ✅ Impressive terminal output

### Nice to Have
- ✅ Command-line arguments
- ✅ Interactive mode
- ✅ Export capability

---

## Code Example

```python
#!/usr/bin/env python3
"""
Agent Hierarchy Demo - Main Entry Point

Demonstrates PM → Tech Lead → Developer hierarchy
with visible message passing and thinking processes.
"""

import time
from agents.project_manager import ProjectManager
from agents.tech_lead import TechLead
from agents.developer import Developer
from ui.terminal import HierarchyDisplay

def setup_agents():
    """Initialize agent hierarchy"""
    # Create agents from bottom up
    developer = Developer("Alice (Developer)")
    tech_lead = TechLead("Bob (Tech Lead)", developer)
    project_manager = ProjectManager("Carol (PM)", tech_lead)

    return project_manager, tech_lead, developer

def run_workflow(pm: ProjectManager, display: HierarchyDisplay, task: str):
    """Run a single workflow and display results"""
    # Display task start
    display.display_task_start(task)

    # Track execution time
    start_time = time.time()

    # Process task through hierarchy
    result = pm.process_task(task)

    # Calculate duration
    duration = time.time() - start_time

    # Get all messages from all agents
    all_messages = []
    for agent in [pm, pm.tech_lead, pm.tech_lead.developer]:
        all_messages.extend(agent.message_history)

    # Sort by timestamp
    all_messages.sort(key=lambda m: m.timestamp)

    # Display workflow
    for msg in all_messages:
        # Display thinking if present
        if msg.thinking:
            display.display_thinking(
                msg.from_agent,
                get_role_from_message(msg),
                msg.thinking
            )

        # Display message
        display.display_message(msg)

    # Display completion
    display.display_task_complete()

    return result, all_messages, duration

def get_role_from_message(msg):
    """Helper to determine role from message"""
    if "PM" in msg.from_agent or "Manager" in msg.from_agent:
        return "project_manager"
    elif "Lead" in msg.from_agent:
        return "tech_lead"
    elif "Developer" in msg.from_agent:
        return "developer"
    return "user"

def display_summary(messages, duration):
    """Display workflow summary statistics"""
    display = HierarchyDisplay()

    stats = f"""
    Messages Exchanged: {len(messages)}
    Agents Involved: 3 (PM, Tech Lead, Developer)
    Execution Time: {duration:.3f}s
    Delegations: {sum(1 for m in messages if m.msg_type == 'delegation')}
    Responses: {sum(1 for m in messages if m.msg_type == 'response')}
    """

    display.console.print(Panel(
        Text(stats, style="cyan"),
        title="📊 Workflow Summary",
        border_style="cyan"
    ))
    display.console.print()

def main():
    """Main entry point"""
    # Setup
    display = HierarchyDisplay()
    display.console.print(Panel(
        Text("Agent Hierarchy Demo", style="bold white", justify="center"),
        subtitle="PM → Tech Lead → Developer",
        border_style="bold blue"
    ))
    display.console.print()

    pm, tl, dev = setup_agents()

    # Example workflows
    workflows = [
        "Implement user authentication with OAuth2",
        "Add real-time notifications to dashboard",
        # "Fix memory leak in user session management",  # Optional 3rd
    ]

    # Run each workflow
    for i, task in enumerate(workflows, 1):
        display.console.print(f"\n{'='*60}")
        display.console.print(f"Workflow {i} of {len(workflows)}", style="bold yellow")
        display.console.print(f"{'='*60}\n")

        result, messages, duration = run_workflow(pm, display, task)
        display_summary(messages, duration)

        # Clear history for next workflow
        pm.message_history.clear()
        tl.message_history.clear()
        dev.message_history.clear()

    # Final banner
    display.console.print(Panel(
        Text("All workflows completed! 🎉", style="bold green", justify="center"),
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
```

---

## Testing Plan

### Manual Execution Tests

```bash
# Test 1: Basic execution
cd agent-squad-simple
python main.py
# Expected: Beautiful colored output showing hierarchy

# Test 2: Check execution time
time python main.py
# Expected: < 1 second

# Test 3: Verify output structure
python main.py | head -20
# Expected: Task start banner, agent messages

# Test 4: Interrupt handling
python main.py
# Press Ctrl+C mid-execution
# Expected: Graceful exit message
```

### Output Verification

Expected output should include:
- ✅ Title banner with hierarchy
- ✅ Task start banners
- ✅ Agent thinking displays
- ✅ Colored message exchanges
- ✅ Delegation chain visible
- ✅ Summary statistics
- ✅ Completion banner

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Import errors | High | Low | Test imports, verify structure |
| Long execution time | Medium | Low | Keep workflows simple |
| Terminal rendering issues | Low | Medium | Test in multiple terminals |
| Message ordering issues | Medium | Low | Sort by timestamp |

---

## Time Estimate

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 5 min | Straightforward integration |
| Senior Dev | 30 min | Wire everything together |
| Junior Dev | 1 hr | Testing, debugging |

**Complexity**: Simple

---

## Example Output Preview

```
╭──────────────────────────────────────────────╮
│       Agent Hierarchy Demo                   │
│       PM → Tech Lead → Developer             │
╰──────────────────────────────────────────────╯

============================================================
Workflow 1 of 2
============================================================

╭─────────────────────────────────────────────╮
│ 🚀 New Task                                  │
│ Implement user authentication with OAuth2    │
╰─────────────────────────────────────────────╯

[12:34:56] 💭 Carol (PM) thinking:
           "Analyzing task: Implement user authentication with OAuth2.
            This requires technical analysis. Will delegate to Tech Lead."

[12:34:56] 👔 Carol (PM) → 🎯 Bob (Tech Lead) 📩 DELEGATION
           ├─ Content: Implement user authentication with OAuth2
           └─ Thinking: Tech Lead has expertise in auth systems

[12:34:56] 💭 Bob (Tech Lead) thinking:
           "Technical analysis: Implement user authentication with OAuth2.
            Breaking down into implementation steps. Will delegate to Developer."

[12:34:57] 🎯 Bob (Tech Lead) → 💻 Alice (Developer) 📩 DELEGATION
           ├─ Content: Implement user authentication with OAuth2
           └─ Thinking: Developer will implement core logic

[12:34:57] 💭 Alice (Developer) thinking:
           "Understanding requirements: Implement user authentication with OAuth2.
            Planning implementation approach."

[12:34:58] 💻 Alice (Developer) → 🎯 Bob (Tech Lead) 📤 RESPONSE
           ├─ Content: # Pseudo-code implementation...
           └─ Thinking: Implemented solution using best practices.

╭─────────────────────────────────────────────╮
│ ✅ Complete                                  │
│ Task completed successfully!                 │
╰─────────────────────────────────────────────╯

╭─────────────────────────────────────────────╮
│ 📊 Workflow Summary                          │
│   Messages Exchanged: 6                      │
│   Agents Involved: 3 (PM, Tech Lead, Dev)    │
│   Execution Time: 0.032s                     │
│   Delegations: 3                             │
│   Responses: 3                               │
╰─────────────────────────────────────────────╯
```

---

## Notes

- **Keep it fast**: No delays, instant execution
- **Visual impact**: Rich output should impress
- **Clear hierarchy**: Indentation and colors show structure
- **Reusable**: Easy to add more workflows

---

## Next Steps

After completion:
1. Run `python main.py` and verify output
2. Test in different terminals
3. Mark all P0 todos as complete
4. Update plan.md Phase 5 status to "Complete"
5. Proceed to [phase-06-documentation.md](./phase-06-documentation.md)
