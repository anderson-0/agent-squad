# Agent Hierarchy Demo - Implementation Plan (CrewAI)

**Date**: 2025-11-20
**Plan ID**: 251120-1201-agent-hierarchy-demo
**Status**: Ready for Implementation
**Framework**: CrewAI (Hierarchical Process)
**Presentation**: Demo-ready with diagrams

---

## Overview

Create a minimal, standalone demonstration of agent hierarchy (PM → Tech Lead → Developer) using **CrewAI's hierarchical process**. Runnable in terminal with visible message passing and agent thinking processes.

**Goal**: Demonstrate CrewAI agent hierarchy in ~300 lines with Rich terminal UI and presentation-ready documentation.

**Why CrewAI?**
- ✅ Native hierarchical process (PM → TL → Dev)
- ✅ Built-in task delegation
- ✅ Automatic agent communication logging
- ✅ Production-ready framework
- ✅ Excellent for learning and demos

---

## Project Context

**Source**: Agent-Squad (production multi-agent system)
- Uses Agno framework, NATS, PostgreSQL, Redis
- Complex orchestration with 9+ agent roles
- Discovery-driven workflows with task spawning

**Target**: agent-squad-simple (CrewAI Edition)
- Minimal infrastructure (CrewAI framework only)
- 3 agents: PM, Tech Lead, Developer
- CrewAI hierarchical process + Rich for terminal UI
- Focus: demonstrate hierarchy AND learn CrewAI
- Presentation-ready with diagrams

---

## Research Findings

1. **Hierarchy Patterns** ([research/researcher-01-hierarchy-patterns.md](./research/researcher-01-hierarchy-patterns.md))
   - Minimal delegation pattern recommended
   - Avoid heavy frameworks for demo
   - Clear chain of command with visible message passing

2. **Terminal UI** ([research/researcher-02-terminal-ui.md](./research/researcher-02-terminal-ui.md))
   - Rich library recommended (simple, powerful)
   - Color-coded agent states
   - Hierarchical indentation for messages

---

## Architecture Decisions

### Core Principles
- **CrewAI First**: Leverage built-in hierarchical process
- **Demo-Ready**: Presentation diagrams and documentation
- **Learning-Focused**: Clear examples of CrewAI concepts
- **Production-Inspired**: Real patterns but simplified

### Technology Stack
- **Framework**: CrewAI (hierarchical process)
- **Language**: Python 3.10+
- **UI**: Rich (terminal formatting)
- **LLM**: Mock responses (or optional OpenAI)
- **Communication**: CrewAI's built-in agent communication

### CrewAI Architecture
```
┌─────────────────────────────────────────┐
│         CrewAI Hierarchical Crew         │
├─────────────────────────────────────────┤
│                                          │
│  Manager Agent (Project Manager)        │
│         ↓ (delegates via CrewAI)        │
│  Agent: Tech Lead                        │
│         ↓ (delegates via CrewAI)        │
│  Agent: Developer                        │
│                                          │
│  Process: Process.hierarchical          │
└─────────────────────────────────────────┘
```

### Project Structure
```
agent-squad-simple/
├── README.md                    # Presentation-ready docs
├── ARCHITECTURE.md              # CrewAI architecture diagrams
├── requirements.txt             # CrewAI + Rich
├── main.py                      # Entry point with CrewAI Crew
├── agents/
│   ├── __init__.py
│   ├── project_manager.py       # CrewAI Agent (PM)
│   ├── tech_lead.py             # CrewAI Agent (TL)
│   └── developer.py             # CrewAI Agent (Dev)
├── tasks/
│   ├── __init__.py
│   └── definitions.py           # CrewAI Task definitions
└── ui/
    ├── __init__.py
    └── terminal.py              # Rich UI wrapper
```

---

## Implementation Phases

### Phase 1: Project Setup ⏱️ Claude: 3 min
- [phase-01-project-setup.md](./phase-01-project-setup.md)
- Create project structure, requirements.txt with CrewAI
- **Dependencies**: None
- **Status**: Pending

### Phase 2: CrewAI Agents ⏱️ Claude: 8 min
- [phase-02-crewai-agents.md](./phase-02-crewai-agents.md)
- Define PM, Tech Lead, Developer as CrewAI Agents
- **Dependencies**: Phase 1
- **Status**: Pending

### Phase 3: Tasks & Crew ⏱️ Claude: 7 min
- [phase-03-tasks-and-crew.md](./phase-03-tasks-and-crew.md)
- Create Task definitions and hierarchical Crew
- **Dependencies**: Phase 2
- **Status**: Pending

### Phase 4: Terminal UI ⏱️ Claude: 8 min
- [phase-04-terminal-ui.md](./phase-04-terminal-ui.md)
- Rich UI wrapper for CrewAI output
- **Dependencies**: Phase 2
- **Status**: Pending

### Phase 5: Main Demo ⏱️ Claude: 4 min
- [phase-05-main-demo.md](./phase-05-main-demo.md)
- Entry point with demo workflows
- **Dependencies**: Phases 3, 4
- **Status**: Pending

### Phase 6: Presentation Docs ⏱️ Claude: 10 min
- [phase-06-presentation-docs.md](./phase-06-presentation-docs.md)
- README, ARCHITECTURE.md, diagrams for demo
- **Dependencies**: Phase 5
- **Status**: Pending

---

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 40 min | CrewAI reduces code, faster implementation |
| Senior Dev | 1.5-2 hrs | Learning CrewAI API, quick integration |
| Junior Dev | 4-5 hrs | Learning CrewAI + agent concepts |

**Complexity**: Simple (CrewAI simplifies significantly)

---

## Success Criteria

### Functional Requirements
- ✅ PM receives task, delegates to Tech Lead
- ✅ Tech Lead analyzes, delegates to Developer
- ✅ Developer implements, returns result
- ✅ All messages visible in terminal
- ✅ Agent "thinking" process shown

### Technical Requirements
- ✅ Total code ~300 lines (CrewAI handles complexity)
- ✅ Runs with `python main.py`
- ✅ No external infrastructure (DB, Redis, NATS)
- ✅ Dependencies: CrewAI, Rich
- ✅ Executes in < 5 seconds (includes LLM calls)

### Quality Requirements
- ✅ Clear terminal output with colors
- ✅ Easy to understand code structure
- ✅ README with usage examples
- ✅ Comments explaining CrewAI concepts
- ✅ **Architecture diagrams for presentation**
- ✅ **Comparison with agent-squad (Agno)**
- ✅ **Demo-ready for live presentation**

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rich learning curve | Low | Rich is simple, well-documented |
| Code complexity creep | Medium | Strict 500-line limit, code reviews |
| Unclear demonstrations | Medium | Clear examples in README |
| Missing agent thinking | Low | Explicit logging in each agent |

---

## Key Implementation Notes

1. **CrewAI Hierarchical Process**:
   ```python
   crew = Crew(
       agents=[pm, tech_lead, developer],
       tasks=[task],
       process=Process.hierarchical,  # ← Key!
       manager_agent=pm,
       verbose=True
   )
   ```

2. **Agent Definition** (CrewAI):
   ```python
   pm = Agent(
       role="Project Manager",
       goal="Delegate and coordinate tasks",
       backstory="Experienced PM...",
       verbose=True,  # Shows thinking
       allow_delegation=True  # ← Enables hierarchy
   )
   ```

3. **Terminal Output**:
   - CrewAI logs all agent communication
   - Rich wraps output with colors/formatting
   - Timestamps and hierarchy visualization

4. **LLM Integration**:
   - Optional: Mock LLM for demo (fast)
   - Optional: Real OpenAI for realistic demo
   - CrewAI handles all LLM communication

---

## Next Steps

1. **Review this plan** with user
2. **Confirm approach** and priorities
3. **Execute Phase 1** (project setup)
4. **Iterate through phases** sequentially
5. **Update phase checkboxes** as work completes

---

## Unresolved Questions

None - plan is ready for execution.

---

**Phase Completion Status:**
- Phase 1: ⏸️ Pending
- Phase 2: ⏸️ Pending
- Phase 3: ⏸️ Pending
- Phase 4: ⏸️ Pending
- Phase 5: ⏸️ Pending
- Phase 6: ⏸️ Pending
