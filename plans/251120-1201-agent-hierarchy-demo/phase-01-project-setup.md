# Phase 1: Project Setup

**Date**: 2025-11-20
**Phase**: 1 of 6
**Priority**: P0 (Blocking)
**Status**: Pending

---

## Context

**Parent Plan**: [plan.md](./plan.md)
**Dependencies**: None
**Next Phase**: [phase-02-agent-base.md](./phase-02-agent-base.md)

---

## Overview

Set up brand new project structure for agent-squad-simple with minimal dependencies and clear organization.

**Goal**: Create clean project skeleton ready for implementation.

---

## Requirements

### Functional
- Create new directory `agent-squad-simple/`
- Set up Python package structure
- Install Rich dependency only
- Create basic README with project description

### Non-Functional
- Python 3.10+ compatible
- Simple directory layout
- No unnecessary files
- Clear separation: agents/ and ui/

---

## Architecture

### Directory Structure
```
agent-squad-simple/
├── README.md                    # Project description, usage
├── requirements.txt             # Rich only
├── .gitignore                   # Python defaults
├── main.py                      # Entry point (empty for now)
├── agents/
│   ├── __init__.py             # Package marker
│   ├── base.py                  # (empty for now)
│   ├── project_manager.py       # (empty for now)
│   ├── tech_lead.py             # (empty for now)
│   └── developer.py             # (empty for now)
└── ui/
    ├── __init__.py             # Package marker
    └── terminal.py              # (empty for now)
```

### Dependencies
```txt
# requirements.txt
rich==13.7.0  # Terminal UI library
```

### Initial README Content
- Project description
- What it demonstrates
- Installation instructions
- Quick start (python main.py)
- Architecture overview

---

## Related Files

**New Files to Create**:
- `/agent-squad-simple/README.md`
- `/agent-squad-simple/requirements.txt`
- `/agent-squad-simple/.gitignore`
- `/agent-squad-simple/main.py`
- `/agent-squad-simple/agents/__init__.py`
- `/agent-squad-simple/agents/base.py`
- `/agent-squad-simple/agents/project_manager.py`
- `/agent-squad-simple/agents/tech_lead.py`
- `/agent-squad-simple/agents/developer.py`
- `/agent-squad-simple/ui/__init__.py`
- `/agent-squad-simple/ui/terminal.py`

---

## Implementation Steps

1. **Create project root directory**
   - Location: `/Users/anderson/Documents/anderson-0/agent-squad-simple/`
   - Verify it's outside agent-squad project

2. **Create directory structure**
   - agents/ package with __init__.py
   - ui/ package with __init__.py

3. **Create requirements.txt**
   - Add Rich dependency only
   - Pin version for reproducibility

4. **Create .gitignore**
   - Python defaults: __pycache__, *.pyc, .venv/, etc.

5. **Create placeholder files**
   - main.py with "TODO" comment
   - All agent files empty
   - terminal.py empty

6. **Create README.md**
   - Project title and description
   - What it demonstrates (hierarchy)
   - Installation steps
   - Usage example
   - Architecture diagram (simple)

7. **Verify structure**
   - Check all files exist
   - Verify packages import correctly

---

## Todo List

### P0: Critical (Must Complete)
- [ ] Create project root directory at `/Users/anderson/Documents/anderson-0/agent-squad-simple/`
- [ ] Create `agents/` package with `__init__.py`
- [ ] Create `ui/` package with `__init__.py`
- [ ] Create `requirements.txt` with Rich dependency
- [ ] Create `.gitignore` with Python defaults
- [ ] Create placeholder `main.py`
- [ ] Create empty agent files (base.py, project_manager.py, tech_lead.py, developer.py)
- [ ] Create empty `ui/terminal.py`
- [ ] Create `README.md` with project description and installation instructions

### P1: Important
- [ ] Add architecture diagram to README
- [ ] Add usage examples to README
- [ ] Verify structure with simple Python import test

### P2: Nice to Have
- [ ] Add LICENSE file (if applicable)
- [ ] Add contributing guidelines (optional)

---

## Success Criteria

### Must Have
- ✅ Directory structure matches specification
- ✅ All files created successfully
- ✅ requirements.txt contains Rich only
- ✅ README has clear installation/usage instructions
- ✅ .gitignore covers Python artifacts

### Should Have
- ✅ README includes architecture overview
- ✅ Clean, simple structure (no extra files)

### Nice to Have
- ✅ Project imports work correctly (test with `python -c "import agents; import ui"`)

---

## Testing Plan

### Manual Verification
```bash
# Check directory structure
ls -R agent-squad-simple/

# Verify Python packages
cd agent-squad-simple
python3 -c "import agents; import ui; print('OK')"

# Check requirements
cat requirements.txt
```

### Expected Output
```
agent-squad-simple/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── project_manager.py
│   ├── tech_lead.py
│   └── developer.py
└── ui/
    ├── __init__.py
    └── terminal.py
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Directory already exists | Low | Low | Check before creating, use unique name |
| Import errors | Low | Low | Create proper __init__.py files |
| Missing dependencies | Low | Low | requirements.txt with pinned version |

---

## Time Estimate

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 5 min | Direct file creation |
| Senior Dev | 10 min | Quick setup |
| Junior Dev | 20 min | Learning project structure |

**Complexity**: Simple

---

## Notes

- **Keep it minimal**: No setup.py, no tox.ini, no pytest config yet
- **No virtual environment**: User can create their own
- **Location**: Outside agent-squad directory (brand new project)
- **Git**: User can init git repo if desired

---

## Next Steps

After completion:
1. Mark all P0 todos as complete
2. Update plan.md Phase 1 status to "Complete"
3. Proceed to [phase-02-agent-base.md](./phase-02-agent-base.md)
