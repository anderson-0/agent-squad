# Claude Code - Complete Guide

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Responsibilities

Your role is to analyze user requirements, plan and execute tasks systematically, and ensure cohesive delivery of features that meet specifications and architectural standards.

## Critical Rules

**MUST FOLLOW:**
- Before planning any implementation, always read `./README.md` first for context
- Follow development rules in `./.claude/workflows/development-rules.md`
- Analyze the skills catalog and activate needed skills for each task
- For `YYMMDD` dates, use `bash -c 'date +%y%m%d'` (or PowerShell: `Get-Date -UFormat "%y%m%d"`)
- Sacrifice grammar for concision in reports
- List unresolved questions at the end of reports

## Workflows

Reference these workflow files for specific protocols:
- Primary workflow: `./.claude/workflows/primary-workflow.md`
- Development rules: `./.claude/workflows/development-rules.md`
- Orchestration protocols: `./.claude/workflows/orchestration-protocol.md`
- Documentation management: `./.claude/workflows/documentation-management.md`
- Other workflows: `./.claude/workflows/*`

---

## Task Management Workflow

When the user gives you a task, follow this workflow:

### 2. Select Plan Command
- Ask the user which plan command to use for the task
- Present the options:
  ```
  Which plan command should I use?

  - `/plan:fast` - Quick analysis, no research (simple/familiar tasks)
  - `/plan:hard` - Full research + analysis (complex/new tasks)
  - `/plan:two` - Create 2 alternative approaches (when trade-offs matter)
  - `/plan:ci` - Analyze CI/CD failures (Github Actions issues)
  - `/plan:cro` - Conversion rate optimization plan
  - `/plan` - Let me decide based on complexity
  ```
- Once the user selects a command, execute it with the user's original request
- **Exception**: For urgent bug fixes or simple tasks, you can skip this and proceed directly

### 3. Review Plan Output
- The plan command creates a directory: `plans/YYYYMMDD-HHmm-plan-name/`
- Review the generated `plan.md` (overview) and phase files
- Each phase file contains:
  - Requirements and architecture
  - Implementation steps
  - **Todo list with checkboxes** (P0/P1/P2 prioritized)
  - Success criteria and risk assessment
- Wait for user confirmation before proceeding to implementation
- **Exception**: For simple tasks, proceed directly if approach is straightforward

### 4. Execute and Update Progress
- Work on the task systematically, **starting with P0 items**
- **Update the phase file checkboxes as you complete each item**
- Mark items as completed: `- [x] Completed task`
- Add notes for partial completion or blockers
- Update the `plan.md` overview status for each phase
- This ensures progress is tracked even if the session is lost
- **When fixing tests**: Always read the actual implementation first, then update tests to match reality (not the other way around)

### 5. Completion and Cleanup
- When all work is done, provide a summary of what was accomplished
- Update phase statuses in `plan.md` to "Complete"
- Ask the user:
  - "The task is complete! May I delete the plan directory (`plans/YYYYMMDD-HHmm-plan-name/`)?"
- If user confirms, delete the directory
- If user wants to keep it, leave it in the `plans` folder for reference

---

## Time Estimation Format

All plans should include time estimates with three perspectives:

```markdown
## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | X min/hrs | Automated execution, parallel processing |
| Senior Dev | Y hrs/days | Familiar with patterns, minimal research |
| Junior Dev | Z hrs/days | Learning curve, requires guidance |

**Complexity**: Simple / Medium / Complex
```

**Example:**
```markdown
## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 15 min | Direct file edits, no debugging needed |
| Senior Dev | 1-2 hrs | Knows the codebase, quick implementation |
| Junior Dev | 4-6 hrs | Needs to understand existing patterns |

**Complexity**: Medium
```

---

## Session Recovery Protocol

When starting a new session or recovering from a crash:

1. **Check for existing plans**: `ls plans/`
2. **Read the plan files** to understand:
   - Review `plan.md` for overall status
   - Check phase files for incomplete checkboxes `- [ ]`
   - Identify blockers or notes
3. **Resume from where you left off** - don't restart from scratch
4. **Inform the user** of the current state before continuing

---

## File Organization

### Plan Documentation
```
/plans/
  └── YYYYMMDD-HHmm-plan-name/
      ├── plan.md                    # Overview with phase status
      ├── phase-01-*.md              # Phase with checkboxes
      ├── phase-02-*.md
      ├── research/                  # Research reports (if /plan:hard)
      └── reports/                   # Scout/analysis reports
```

### Project Documentation
```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```

---

## Testing Best Practices

### When Writing or Fixing Tests:
1. **Always read the actual implementation first** - Don't assume how it works
2. **Match the implementation, not your expectations** - Tests should reflect reality
3. **Look for POJOs vs Models** - Modern code often uses plain objects instead of classes with getters/setters
4. **Check for direct property access** - Use `object.property` not `object.getProperty()`
5. **Verify all mocks are set up** - Missing mocks cause undefined errors
6. **Remove obsolete tests** - If functionality was removed, delete those tests
7. **Run tests individually first** - Fix one test at a time, verify it passes, then move to the next
8. **Check error messages carefully** - They tell you exactly what's wrong

## Code Review Best Practices

When doing code reviews:
1. **Fix compilation errors first** (P0)
2. **Fix test failures second** (P0)
3. **Address security issues** (P1)
4. **Review performance concerns** (P1)
5. **Consider code cleanup** (P2)

---

## Important Notes

- Always use plan commands (`/plan:fast`, `/plan:hard`, etc.) for new tasks
- **Update phase checkboxes in real-time** as you complete items
- Keep the user informed of progress
- Maintain clear documentation in plan phase files
- **Read before you write** - Always check actual implementation before fixing tests
- **Prioritize critical issues** - Focus on P0 items that block deployment
- **Provide context in phase files** - Help the next session (or user) understand what was done

---

## CLAUDE.md Directory Documentation

This project includes detailed documentation in various `CLAUDE.md` files:
- `/CLAUDE.md` - This file (task management workflow)

**Always check these files** when working in unfamiliar parts of the codebase to understand established patterns.

---

## Communication Style

- Be concise and clear
- Provide summaries after completing major milestones
- Use checkboxes and priority indicators in phase files for visual clarity
- When blocked, explain the issue and suggest next steps
- Report progress regularly, especially for long-running tasks
- List unresolved questions at the end of reports
