# Phase 07 - UI Enhancements

**Date:** 2025-11-21
**Priority:** P1 (Important)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** [Phase 06 - Frontend Integration](./phase-06-frontend-integration.md)
- **Related Docs:** [Design Guidelines](../../docs/design-guidelines.md)

## Overview

Polish UI with animations, live terminal logs, git progress indicators, PR notifications. Follow design guidelines (Framer Motion, cubic-bezier easing). Enhance Agent Work page with real-time sandbox activity.

**Key Features:**
- Live terminal output with auto-scroll
- Git operation progress bars (clone, push)
- Sandbox status badges with animations
- PR creation notifications (toast + card)
- Agent status transitions with easing
- Skeleton loaders during data fetch

## Key Insights

From design guidelines:
- Standard easing: `[0.22, 1, 0.36, 1]`
- Stagger children for list animations
- Error shake animation for failures
- Success spring animation for completions
- WhileHover/WhileTap for interactive elements

## Requirements

### Functional
- Display live terminal output in Agent Work page
- Show git operation progress (0-100%)
- Animate sandbox status changes
- Display PR creation with success animation
- Show agent status transitions
- Auto-scroll terminal to latest output
- Copy terminal output to clipboard
- Filter terminal by stream (stdout/stderr)

### Non-Functional
- Animations run at 60fps
- Terminal renders 1000+ lines without lag
- Progress updates visible within 500ms of SSE event
- No layout shift during animations
- Accessible animations (prefers-reduced-motion)
- Dark mode support

## Architecture

### Agent Work Page Layout

```
┌────────────────────────────────────────────────────┐
│  Agent Work Page                                   │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Sandbox      │  │ Task         │              │
│  │ Status: ●    │  │ Branch: ...  │              │
│  └──────────────┘  └──────────────┘              │
│                                                    │
│  Tabs: [Activity] [Terminal] [Git History]        │
│  ┌──────────────────────────────────────────────┐ │
│  │ Terminal                                     │ │
│  │ $ git clone https://github.com/...          │ │
│  │ Cloning... ████████████░░░░░░░░░░ 60%       │ │
│  │ $ npm install                                │ │
│  │ added 1247 packages in 34s                   │ │
│  │ █                                            │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### Component Structure

```
AgentWorkPage
├── SandboxStatusCard (animated badge)
├── TaskInfoCard (PR link, branch name)
├── Tabs (Activity, Terminal, Git History)
│   ├── TerminalTab
│   │   ├── TerminalOutput (virtualized list)
│   │   ├── ProgressBar (git operations)
│   │   └── CopyButton
│   ├── GitHistoryTab
│   │   └── CommitList (with avatars)
│   └── ActivityTab
└── PRNotification (toast on creation)
```

## Related Code Files

### New Files to Create
- `components/agent-work/TerminalOutput.tsx` - Live terminal display
- `components/agent-work/ProgressBar.tsx` - Git operation progress
- `components/agent-work/SandboxStatus.tsx` - Animated status badge
- `components/agent-work/PRNotification.tsx` - PR creation toast
- `components/agent-work/GitHistoryTab.tsx` - Commit history
- `components/ui/StatusBadge.tsx` - Reusable status badge
- `lib/hooks/useTerminalScroll.ts` - Auto-scroll hook

### Files to Modify
- `app/(dashboard)/agent-work/page.tsx` - Add new components
- `components/squads/KanbanBoard.tsx` - Add status animations
- `components/squads/TaskCard.tsx` - Show PR link badge

## Implementation Steps

1. **Create Terminal Output Component**
   - Use react-window for virtualization (1000+ lines)
   - Display stdout in white, stderr in red
   - Add auto-scroll to bottom on new output
   - Implement copy-to-clipboard button
   - Add timestamp per line (optional)
   - Support ANSI color codes (optional: ansi-to-react)

2. **Create Progress Bar Component**
   - Animated progress bar with Framer Motion
   - Show percentage (0-100%)
   - Color coding: blue (in progress), green (complete), red (error)
   - Smooth transitions with easing `[0.22, 1, 0.36, 1]`
   - Display operation name (Cloning, Pushing, etc.)

3. **Create Sandbox Status Badge**
   - Status colors: gray (creating), blue (running), green (completed), red (error)
   - Pulse animation for "creating" and "running"
   - Success spring animation on completion
   - Error shake animation on failure
   - Icon per status (Loader, CheckCircle, AlertCircle)

4. **Create PR Notification**
   - Toast notification on pr_created event
   - Include PR URL as clickable link
   - Success icon with spring animation
   - Auto-dismiss after 10 seconds
   - Click to view PR in new tab

5. **Update Agent Work Page**
   - Add TerminalOutput to Terminal tab
   - Connect to SSE command_output events
   - Add ProgressBar for git_operation events
   - Add SandboxStatus badge to header
   - Show PR link in TaskInfoCard when created

6. **Add Git History Tab**
   - Display commit list from API
   - Show commit SHA, message, author, timestamp
   - Add copy SHA button
   - Link to GitHub commit view
   - Animate list with stagger children

7. **Enhance KanbanBoard**
   - Add loading spinner overlay during task update
   - Animate task card movement with layoutId
   - Show success checkmark on successful assignment
   - Shake animation on assignment error

8. **Update Task Card**
   - Add PR link badge (GitHub icon)
   - Show git branch name below title
   - Animate PR badge entrance (spring)
   - Open PR in new tab on click

9. **Loading States**
   - Add skeleton loaders for terminal (shimmer effect)
   - Loading spinner for git operations
   - Pulsing status badge during transitions

10. **Accessibility**
    - Respect prefers-reduced-motion for animations
    - Add aria-live regions for terminal updates
    - Keyboard navigation for tabs
    - Screen reader announcements for status changes

11. **Dark Mode Support**
    - Terminal colors optimized for dark theme
    - Progress bar colors with proper contrast
    - Status badges readable in both themes

12. **Testing**
    - Test terminal with 1000+ lines (performance)
    - Test progress bar animations (60fps)
    - Test SSE event rendering
    - Test accessibility with screen reader

## Todo List

### P0 - Critical

- [ ] Create components/agent-work/TerminalOutput.tsx with virtualization
- [ ] Connect TerminalOutput to SSE command_output events
- [ ] Implement auto-scroll to bottom on new lines
- [ ] Create components/agent-work/ProgressBar.tsx with Framer Motion
- [ ] Connect ProgressBar to SSE git_operation events
- [ ] Show progress percentage and operation name
- [ ] Create components/agent-work/SandboxStatus.tsx with animated badge
- [ ] Implement status color coding and icons
- [ ] Add pulse animation for "running" status
- [ ] Update Agent Work page with new components
- [ ] Test terminal rendering with 100+ lines
- [ ] Test progress bar smooth transitions

### P1 - Important

- [ ] Create components/agent-work/PRNotification.tsx toast
- [ ] Trigger toast on pr_created SSE event
- [ ] Create components/agent-work/GitHistoryTab.tsx
- [ ] Fetch and display commit history from API
- [ ] Add copy-to-clipboard button for terminal
- [ ] Implement stdout/stderr filtering
- [ ] Add success spring animation for completed operations
- [ ] Add error shake animation for failures
- [ ] Update TaskCard to show PR link badge
- [ ] Add skeleton loaders for terminal
- [ ] Test accessibility with keyboard navigation
- [ ] Test dark mode appearance

### P2 - Nice to Have

- [ ] Add ANSI color code support (ansi-to-react)
- [ ] Implement terminal search functionality
- [ ] Add terminal export (download as .txt)
- [ ] Show git diff in Git History tab
- [ ] Add commit message editing (amend)
- [ ] Implement terminal line numbers
- [ ] Add syntax highlighting for code outputs
- [ ] Create terminal themes (Solarized, Monokai, etc.)

## Success Criteria

- [ ] Terminal displays live output with auto-scroll
- [ ] Git progress bars show 0-100% smoothly
- [ ] Sandbox status badge animates on transitions
- [ ] PR notification appears on PR creation
- [ ] Terminal renders 1000+ lines without lag
- [ ] Animations run at 60fps on modern browsers
- [ ] Dark mode looks consistent
- [ ] Keyboard navigation works for all components
- [ ] prefers-reduced-motion disables animations

## Risk Assessment

**High Risks:**
- Terminal performance with large outputs (>5000 lines)
- Animation jank on low-end devices
- Memory leaks from SSE event accumulation

**Medium Risks:**
- Layout shift during progress bar animations
- Auto-scroll conflicts with user scrolling
- Dark mode color contrast issues

**Mitigation:**
- Use react-window for terminal virtualization
- Limit terminal buffer to 5000 lines, clear older
- Test animations on low-end hardware, disable if <30fps detected
- Cleanup SSE listeners on component unmount
- Use Framer Motion's layoutId to prevent layout shift
- Disable auto-scroll when user manually scrolls up
- Test dark mode colors with contrast checker tools

## Security Considerations

- **XSS Prevention:** Sanitize terminal output before rendering (escape HTML)
- **ANSI Injection:** If supporting ANSI codes, validate sequences
- **Link Safety:** Validate PR URLs before rendering (must be GitHub)
- **Output Filtering:** Don't display tokens/secrets in terminal (filter patterns)

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 35 min | Component generation, animation setup |
| Senior Dev | 3-4 hrs | React optimization, virtualization |
| Junior Dev | 8-10 hrs | Framer Motion, performance tuning |

**Complexity:** Medium (React optimization, animations)

## Next Steps

After completion:
- [Phase 08 - Testing & Deployment](./phase-08-testing-deployment.md) - E2E tests, deployment

## Unresolved Questions

1. **Terminal Buffer:** Max lines before clearing? (5000? 10000?)
2. **ANSI Support:** Include ansi-to-react library? (+50KB bundle size)
3. **Virtualization:** Use react-window or @tanstack/react-virtual?
4. **Export Format:** Support multiple formats (.txt, .json, .html)?
5. **Real-time Throttling:** Throttle terminal updates if >100 lines/second?
6. **Notification Sounds:** Play sound on PR creation? (accessibility concern)
7. **Animation Performance:** Disable animations on devices with <4GB RAM?
