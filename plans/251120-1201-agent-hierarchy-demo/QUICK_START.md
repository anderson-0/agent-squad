# Agent Hierarchy Demo - Quick Start Guide

**Time to Demo**: 40 minutes
**Framework**: CrewAI
**Complexity**: Simple

---

## 🚀 Fast Track to Demo

### Option 1: I'll Build It (40 min)

**Say:** "Yes, build it now!"

I'll execute all 6 phases sequentially:
1. ✅ Phase 1: Project setup (3 min)
2. ✅ Phase 2: CrewAI agents (8 min)
3. ✅ Phase 3: Tasks & Crew (7 min)
4. ✅ Phase 4: Terminal UI (8 min)
5. ✅ Phase 5: Main demo (4 min)
6. ✅ Phase 6: Documentation (10 min)

**Result**: Fully working demo + presentation docs

---

### Option 2: Review Plan First (10 min review + 40 min build)

**Say:** "Let me review the plan details first"

I'll walk you through:
- Updated plan with CrewAI architecture
- Phase-by-phase breakdown
- Code examples and structure
- Then build with your approval

---

## 📊 What You'll Get

### Code Structure
```
agent-squad-simple/
├── README.md                 # How to run, examples
├── ARCHITECTURE.md           # Diagrams, concepts
├── requirements.txt          # CrewAI + Rich
├── main.py                   # Demo entry point (~80 lines)
├── agents/
│   ├── project_manager.py    # PM agent (~60 lines)
│   ├── tech_lead.py          # TL agent (~60 lines)
│   └── developer.py          # Dev agent (~60 lines)
├── tasks/
│   └── definitions.py        # Task templates (~40 lines)
└── ui/
    └── terminal.py           # Rich UI wrapper (~50 lines)
```

**Total**: ~350 lines of clean, documented code

---

### Documentation
1. **README.md** - Quick start, usage examples
2. **ARCHITECTURE.md** - Diagrams, CrewAI concepts
3. **DEMO_PRESENTATION.md** - Presentation script (already created! ✅)
4. **Code comments** - Explain CrewAI patterns

---

### Demo Output
```
🎯 Agent Squad - Hierarchy Demo (CrewAI)

📋 Task: Implement user authentication

👔 Project Manager delegating...
  🔧 Tech Lead analyzing...
    💻 Developer implementing...

✅ Complete in 2.3 seconds!
```

---

## 🎯 Demo Scenarios

### Scenario 1: Authentication System
**Input**: "Implement user authentication with OAuth2"
**Flow**: PM → TL → Dev
**Duration**: ~3 seconds
**Shows**: Full hierarchy, technical analysis, implementation plan

### Scenario 2: API Endpoint
**Input**: "Create REST API for user management"
**Flow**: PM → TL → Dev
**Duration**: ~2 seconds
**Shows**: Faster task, clear delegation

### Scenario 3: Bug Fix
**Input**: "Fix the login timeout issue"
**Flow**: PM → TL → Dev
**Duration**: ~2 seconds
**Shows**: Problem-solving, simpler workflow

---

## 💡 Key CrewAI Concepts Demonstrated

### 1. Hierarchical Process
```python
process=Process.hierarchical  # Built-in delegation chain
```

### 2. Agent Roles
```python
pm = Agent(role="Project Manager", allow_delegation=True)
tl = Agent(role="Tech Lead", allow_delegation=True)
dev = Agent(role="Developer", allow_delegation=False)  # End of chain
```

### 3. Task Flow
```python
task = Task(
    description="Implement feature X",
    agent=pm  # Starts at top of hierarchy
)
```

### 4. Verbose Output
```python
verbose=True  # Shows agent thinking and communication
```

---

## 🔧 Technical Details

### Dependencies
```
crewai>=0.11.0
rich>=13.0.0
python-dotenv>=1.0.0  # For optional OpenAI key
```

### Optional: Real LLM
```bash
# .env file (optional)
OPENAI_API_KEY=sk-...

# Without key: uses mock responses (fast)
# With key: uses real LLM (realistic but slower)
```

---

## 📈 Comparison: Agno vs CrewAI

| Feature | agent-squad (Agno) | agent-squad-simple (CrewAI) |
|---------|-------------------|----------------------------|
| **Agents** | 9 specialized | 3 core (PM, TL, Dev) |
| **Infrastructure** | PostgreSQL, Redis, NATS | None |
| **Lines of Code** | ~15,000 | ~350 |
| **Hierarchy** | Custom delegation logic | Built-in Process.hierarchical |
| **Setup Time** | Hours (Docker, etc.) | Minutes (pip install) |
| **Purpose** | Production | Demo/Learning |
| **Complexity** | High | Low |

**Both are production-ready frameworks - different use cases**

---

## 🎬 What Happens During Build

### Phase 1: Project Setup (3 min)
```bash
mkdir agent-squad-simple
cd agent-squad-simple
# Create directory structure
# Generate requirements.txt
```

### Phase 2: CrewAI Agents (8 min)
```python
# Create agents/project_manager.py
pm = Agent(
    role="Project Manager",
    goal="Coordinate team and delegate tasks",
    backstory="...",
    allow_delegation=True
)
```

### Phase 3: Tasks & Crew (7 min)
```python
# Create tasks/definitions.py
task = Task(description="...", agent=pm)

# Create hierarchical crew
crew = Crew(
    agents=[pm, tl, dev],
    tasks=[task],
    process=Process.hierarchical,
    manager_agent=pm
)
```

### Phase 4: Terminal UI (8 min)
```python
# Create ui/terminal.py with Rich
console = Console()
console.print("[blue]PM delegating...[/blue]")
```

### Phase 5: Main Demo (4 min)
```python
# Create main.py
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
```

### Phase 6: Documentation (10 min)
- README.md with examples
- ARCHITECTURE.md with diagrams
- Inline code comments

---

## ✅ Acceptance Criteria

**Functional:**
- [ ] PM receives task and delegates
- [ ] TL analyzes and delegates
- [ ] Dev implements and returns result
- [ ] All agent communication visible
- [ ] Thinking process shown

**Technical:**
- [ ] Runs with `python main.py`
- [ ] No errors or warnings
- [ ] Colored terminal output
- [ ] ~350 lines total
- [ ] Executes in < 5 seconds

**Documentation:**
- [ ] README explains how to run
- [ ] ARCHITECTURE shows diagrams
- [ ] DEMO_PRESENTATION ready for demo
- [ ] Code has helpful comments

---

## 🚦 Decision Point

**Ready to proceed?**

**Option A**: "Build it now" → I'll execute all phases
**Option B**: "Show me Phase X first" → I'll detail specific phase
**Option C**: "Change something" → Tell me what to adjust

**Your call!** 🎯

---

**Current Status**: Plan updated ✅ | Presentation ready ✅ | Awaiting build approval ⏸️

