# Research: Modern UX Patterns for Multi-Agent Visualization

**Date**: 2025-11-21
**Researcher**: Claude (Haiku 4.5)
**Scope**: Agent visualization, real-time collaboration, task boards, threading, access control

---

## 1. Agent Visualization Patterns

### AI Development Tools (Lovable, Cursor, v0, Bolt)

**Chat-Based Interface + Live Preview**
- All tools use chat as primary interaction model
- Split-pane layout: chat on left, live preview on right
- Instant visual feedback as agent generates code
- File tree shows what's being modified in real-time

**Visual Editor Mode (Lovable)**
- Figma-like interface for clicking and tweaking elements visually
- Changes sync to underlying code (JSX, Tailwind)
- Solves "prompt fatigue" for fine-tuning designs
- **Actionable**: Implement dual-mode interface (chat + visual canvas)

**Code Generation Philosophy**
- Lovable/Bolt/v0: Rapid prototyping, full-stack generation
- Cursor: Enhances existing workflows, clean code focus
- **Key Pattern**: Show different "modes" based on user type (builder vs developer)

**URLs**:
- https://techpoint.africa/guide/lovable-vs-bolt-vs-cursor/
- https://www.sidetool.co/post/cursor-bolt-and-lovable-ai-compared-find-your-perfect-development-tool/

---

## 2. Real-Time Collaboration UI

### VSCode Live Share

**Core Patterns**:
- **Presence indicators**: Show who's in session with colored cursors
- **Shared context**: Terminal, debug sessions, file tree all sync
- **Host-centric model**: One person shares, others join
- **No setup friction**: Instant join via URL, no config syncing
- **Bidirectional editing**: Everyone uses their own tools/settings

**Visual Elements**:
- Colored cursor trails with user names
- Activity sidebar showing collaborators
- Shared terminal with command history
- Follow mode (auto-scroll to host's view)

**Actionable**:
- Show agent "cursors" moving through files
- Display which agent is editing what file
- Shared terminal output for all agents

**URLs**:
- https://visualstudio.microsoft.com/services/live-share/
- https://code.visualstudio.com/blogs/2017/11/15/live-share

### Figma Multiplayer

**Design Philosophy**:
- "Multiplayer is how all productivity tools should work"
- Eliminates export/sync/email workflow
- More people participate (copywriters, devs, not just designers)

**Technical Implementation**:
- Custom multiplayer system (not traditional OT)
- Simpler to implement than operational transforms
- Real-time cursor positions with user avatars
- Selection outlines in user's color

**Actionable**:
- Show agent avatars with activity states
- Highlight what each agent is working on
- Allow "shadowing" an agent to watch their work

**URL**: https://www.figma.com/blog/how-figmas-multiplayer-technology-works/

---

## 3. Task Board UX

### Asana Modern Board Design

**Visual Evolution**:
- **Full-bleed images**: Pushed to card edges (not inset)
- **Larger custom field pills**: Less truncation, better readability
- **Slide-in task pane**: Replaces modals, keeps context visible
- **Drag-and-drop fluidity**: Like sticky notes on Kanban

**Real-Time Features**:
- Changes reflected across all projects instantly
- Live embeds update automatically (no manual refresh)
- Teams collaborate synchronously or asynchronously

**Multiple View Modes**:
- Switch between Kanban, List, Timeline, Calendar, Gantt
- Single click to change views
- Work stages shown as columns

**Actionable for Agent Squad**:
- Kanban columns: Queued → In Progress → Review → Done
- Agent avatar on cards they're working on
- Real-time status updates without refresh
- Slide-in panel for task details (keep board visible)

**URLs**:
- https://asana.com/inside-asana/introducing-boards
- https://medium.com/asana-design/better-boards-ab72cc2fa25e

---

## 4. Conversation Threading

### Slack Threads

**Pattern**:
- Reply to message opens thread in side panel
- Threads kept horizontally narrow (sometimes too narrow)
- Threads "buried" at surface level (click to expand)
- Good for support channels, less so for long discussions

**Pros**: Keeps main channel clean
**Cons**: Easy to miss updates in threads

### Discord Threads

**Pattern**:
- Heavyweight: Must be named with expiration
- Creates subchannel in sidebar under parent
- Full UI width (more pleasant than Slack)
- Thread name becomes stale as conversation wanders

**Pros**: Full UI, easy navigation
**Cons**: Overhead of naming, less organic

### Intercom

**Pattern**:
- "Conversations" contain "Conversation Parts"
- Mirrors Slack threading (attachments, rich format)
- Context stays clear across platforms
- Perfect sync between Intercom and Slack

### Alternative: Tree Threading (Heim)

**Pattern**:
- Any message can have nested replies
- Subthreads display inline in tree structure
- True branching conversations

**Actionable for Agent Squad**:
- Agent-to-agent comms: Inline tree threads
- Agent-to-user: Slack-style side panel threads
- Show "thinking" indicator when agent typing
- Collapse/expand threads to manage noise

**URLs**:
- https://www.brainonfire.net/blog/2021/11/28/chat-conversation-splitting/
- https://medium.com/slack-developer-blog/rendering-content-in-both-intercom-and-slack-c3a880e5feb0

---

## 5. Access Control UX

### Frontend Visibility Patterns

**Conditional Rendering**:
- UI adjusts based on user role/permissions
- Only relevant elements visible (buttons, forms, pages)
- Frontend aligns with backend permissions
- Maintains consistent user experience

**Page/Module Visibility**:
- Control which pages/modules each role sees
- Separate desktop/mobile visibility rules
- Visual configuration (no code required)

### Dashboard Access Patterns

**Unified Interface**:
- Single frontend tool for all users
- Users see only what they need for their tasks
- Source data remains unaltered
- Minimize exposure to irrelevant data

**Design Flow**: User Identity → Page Access → Data Operations → Dynamic Rules

### Kubernetes Dashboard Example

**UI Components**:
- "Access Control" nav item in admin section
- Shows existing Roles/Bindings with key details
- Create new Role/Binding inline
- Visual representation of permissions

**Actionable for Agent Squad**:
- **Admin View**: See all agents, all conversations, all tasks
- **Developer View**: See work-related agents, hide meta-orchestration
- **End User View**: Only see user-facing agents (hide Hephaestus, Researcher, etc.)
- **Toggle Controls**: "Show Internal Agents" checkbox for power users
- **Visual Indicators**: Badge/icon showing which agents are internal vs user-facing

**URLs**:
- https://www.osohq.com/learn/rbac-role-based-access-control
- https://github.com/kubernetes/dashboard/blob/master/docs/design/access-control.md

---

## Synthesis: Recommended Patterns for Agent Squad

### 1. Primary Interface Layout
```
┌────────────────────────────────────────────────┐
│ [Agent Squad Dashboard]           [@user]      │
├──────────────┬─────────────────────────────────┤
│ Agent Panel  │  Main Work Area                 │
│              │                                  │
│ 🤖 Antigrav  │  ┌─────────────────────────┐   │
│ 🔨 Hephaest  │  │ Task Board (Kanban)     │   │
│ 🔍 Researc   │  │                         │   │
│ 💻 Code      │  │ [Queued][Progress][Done]│   │
│              │  └─────────────────────────┘   │
│ [Show All]   │                                  │
└──────────────┴─────────────────────────────────┘
```

### 2. Agent Activity Visualization
- Colored status dots (green=active, yellow=thinking, gray=idle)
- Mini-avatars on task cards showing assigned agent
- Live cursor trails when agent editing files
- "Currently working on..." text under agent name

### 3. Real-Time Updates
- No page refresh required
- WebSocket for instant updates
- Optimistic UI (show action before server confirms)
- Toast notifications for major events (task complete, agent handoff)

### 4. Conversation Threading
- Main conversation: Agent-to-user (top-level)
- Threads: Agent-to-agent communication (collapsible)
- Tree-based replies for branching discussions
- Typing indicators with agent name

### 5. Access Control
- Role-based visibility toggle
- "Developer Mode" shows internal agents
- End users only see public-facing agents
- Visual badge for internal/system agents

---

## Unresolved Questions
1. How to handle 5+ agents working simultaneously without UI chaos?
2. Should we show agent "thought process" or only final output?
3. How granular should task updates be? (per-file? per-function? per-line?)
4. Mobile responsiveness for multi-agent dashboard?
