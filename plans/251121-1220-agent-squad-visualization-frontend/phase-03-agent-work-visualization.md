# Phase 3: Agent Work Visualization (Lovable-style)

**Status**: Pending
**Priority**: P0 (User Requirement: MUST HAVE)
**Dependencies**: Phase 1, Phase 2
**Estimated Duration**: Claude (4 hrs) | Senior Dev (3 days) | Junior Dev (5-7 days)

---

## Context

Phase 3 implements the **"Lovable-style" agent work visualization** - the most critical UX feature. This shows live agent activity similar to Lovable IDE, where users can watch agents work in real-time with file changes, code generation, terminal output, and progress indicators. This creates transparency and builds trust in the AI system.

**Related Files**:
- Research: `research/researcher-01-ux-patterns.md` (Lovable, Cursor, v0 patterns)
- Backend: `scout/scout-02-backend-api.md` (SSE messages, logs)
- Agent System: `scout/scout-03-agent-system.md` (agent messages, task execution)

---

## Overview

**Goal**: Create immersive visualization of agent work activity with live updates.

**Key Deliverables**:
1. Split-pane layout (task list + agent work area)
2. Live agent activity feed (what agent is doing right now)
3. File/code changes visualization
4. Terminal output display
5. Progress indicators per task phase
6. Agent "cursor" showing active file/location
7. Thinking/reasoning display (agent thoughts)

**Dates**:
- Start: TBD (after Phase 2)
- End: TBD
- **Status**: Pending

---

## Key Insights from Research

### From `researcher-01-ux-patterns.md`

**Lovable/Bolt/v0 Pattern**:
- **Split-pane layout**: Chat/task list on left, live preview on right
- **Instant visual feedback**: See code being generated in real-time
- **File tree**: Shows what's being modified with highlights
- **Terminal output**: Live logs from agent actions

**VSCode Live Share Pattern**:
- **Colored cursors**: Show where each agent is working
- **Activity sidebar**: List of collaborators and their status
- **Follow mode**: Auto-scroll to agent's view
- **Shared terminal**: Command history visible

**Figma Multiplayer Pattern**:
- **Real-time cursor positions**: User avatars move with activity
- **Selection outlines**: Highlight what agent is working on
- **Shadowing**: Watch specific agent's work

**Actionable for Agent Squad**:
- Show agent "cursors" moving through files
- Display which agent is editing what file
- Live activity feed: "Backend Dev is implementing auth..."
- Progress bars for task phases (analyzing 25%, planning 50%, etc.)

### From `scout-03-agent-system.md`

**Agent Message Types**:
- `task_assignment`: PM assigns task
- `status_update`: Developer updates progress
- `question`: Agent asks question
- `code_review_request`: Request review
- `task_completion`: Task done

**Task Execution Flow**:
```
PENDING (0%) → ANALYZING (12%) → PLANNING (25%) → DELEGATED (37%) →
IN_PROGRESS (62%) → REVIEWING (75%) → TESTING (87%) → COMPLETED (100%)
```

**Available Data from Backend**:
- Agent messages with timestamps
- Status updates with progress %
- Log entries (info/warning/error)
- File changes (if tracked)
- Terminal output

---

## Requirements

### Functional Requirements

**FR-3.1**: Split-pane layout with resizable divider
**FR-3.2**: Task list panel (left) showing active tasks
**FR-3.3**: Agent work area panel (right) showing selected task activity
**FR-3.4**: Live activity feed showing agent actions in chronological order
**FR-3.5**: Agent status indicator (active/thinking/idle) with avatar
**FR-3.6**: Progress bar for task phases with % completion
**FR-3.7**: File tree showing modified files with diff indicators
**FR-3.8**: Code viewer with syntax highlighting
**FR-3.9**: Terminal output window with scrolling logs
**FR-3.10**: Agent "cursor" indicator showing active file/line
**FR-3.11**: Thinking/reasoning display (agent internal thoughts)
**FR-3.12**: Time since last update ("2 minutes ago")
**FR-3.13**: Auto-scroll to latest activity (with pause button)

### Non-Functional Requirements

**NFR-3.1**: Real-time updates < 300ms latency
**NFR-3.2**: Smooth scroll animations (60fps)
**NFR-3.3**: Handle 100+ activity events without lag
**NFR-3.4**: Syntax highlighting for 20+ languages
**NFR-3.5**: Terminal output supports ANSI colors
**NFR-3.6**: Responsive layout (collapse to tabs on mobile)

---

## Architecture

### Component Hierarchy

```
Page: /tasks/[id]/activity
├── SplitPane (left: 40%, right: 60%, resizable)
│   ├── LeftPanel
│   │   ├── TaskHeader (title, status, assigned agent)
│   │   ├── TaskProgress (phase bar with %)
│   │   └── ActivityFeed
│   │       └── ActivityItem (repeated)
│   │           ├── AgentAvatar
│   │           ├── ActionDescription
│   │           ├── Timestamp
│   │           └── StatusBadge
│   └── RightPanel
│       ├── TabBar (Files, Terminal, Thoughts)
│       ├── FileTab (if selected)
│       │   ├── FileTree
│       │   │   └── FileNode (repeated, with diff indicator)
│       │   └── CodeViewer
│       │       ├── SyntaxHighlighter
│       │       ├── AgentCursor (animated)
│       │       └── DiffHighlight
│       ├── TerminalTab (if selected)
│       │   ├── TerminalOutput (virtualized)
│       │   └── AutoScrollToggle
│       └── ThoughtsTab (if selected)
│           └── ThoughtItem (repeated)
│               ├── AgentAvatar
│               ├── ThoughtContent
│               └── Timestamp
└── FloatingActions
    ├── FollowAgentButton
    └── PauseUpdatesButton
```

### Activity Feed Data Structure

```typescript
interface ActivityEvent {
  id: string;
  timestamp: string;
  agent_id: string;
  agent_name: string;
  agent_role: AgentRole;
  action_type:
    | 'analyzing'
    | 'planning'
    | 'coding'
    | 'reviewing'
    | 'testing'
    | 'thinking'
    | 'asking'
    | 'completing';
  description: string;
  metadata?: {
    file_path?: string;
    line_number?: number;
    diff?: {
      added: number;
      removed: number;
    };
    error?: string;
  };
}
```

### Real-Time Data Flow

```
Backend Agent Action (e.g., Backend Dev writes code)
    ↓
Agent sends message to NATS
    ↓
Backend SSE Service broadcasts event
    ↓
Frontend SSE Client receives event
    ↓
Parse event → Create ActivityEvent
    ↓
Update TanStack Query cache
    ↓
ActivityFeed component re-renders
    ↓
New activity item appears with animation
    ↓
Auto-scroll to latest (if enabled)
```

### Layout Design

```
┌─────────────────────────────────────────────────────────────┐
│  Task: Implement User Authentication                        │
│  ● Backend Developer (Active)           Progress: 62% ▓▓▓░░ │
├──────────────────────┬──────────────────────────────────────┤
│  Activity Feed       │  Files | Terminal | Thoughts         │
│                      │                                       │
│  ● Backend Dev       │  src/                                │
│  Analyzing task...   │  ├─ auth/                            │
│  2 minutes ago       │  │  ├─ login.ts         +45 -12     │
│                      │  │  ├─ register.ts      +38 -5      │
│  ● Backend Dev       │  │  └─ jwt.ts           +22 -0      │
│  Creating auth       │  └─ tests/                           │
│  module              │     └─ auth.test.ts     +67 -3      │
│  1 minute ago        │                                       │
│                      │  ┌─────────────────────────────────┐ │
│  ● Backend Dev       │  │ // src/auth/login.ts            │ │
│  Writing login.ts    │  │ import { verify } from 'jsonweb'│ │
│  30 seconds ago      │  │                                 │ │
│                      │  │ export async function login(█   │ │
│  ● Backend Dev       │  │   email: string,                │ │
│  Running tests...    │  │   password: string              │ │
│  5 seconds ago       │  │ ) {                             │ │
│  ✓ Success           │  │   const user = await findUser   │ │
│                      │  │   // Verifying credentials...   │ │
│  [Auto-scroll ⏸]    │  └─────────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────────┘
         40%                          60%
```

---

## Related Code Files

### Files to Create

1. **Types**:
   - `types/activity.ts` (ActivityEvent, ActivityType, AgentAction)
   - `types/file-change.ts` (FileChange, DiffSummary)

2. **API/Hooks**:
   - `lib/hooks/useActivityFeed.ts` (fetch + real-time updates)
   - `lib/hooks/useFileTree.ts` (file structure)
   - `lib/hooks/useTerminalOutput.ts` (logs)
   - `lib/hooks/useAgentThoughts.ts` (thinking process)

3. **Components - Layout**:
   - `components/activity/SplitPane.tsx`
   - `components/activity/LeftPanel.tsx`
   - `components/activity/RightPanel.tsx`

4. **Components - Activity Feed**:
   - `components/activity/ActivityFeed.tsx`
   - `components/activity/ActivityItem.tsx`
   - `components/activity/AgentAvatar.tsx`
   - `components/activity/ActionIcon.tsx`

5. **Components - Work Area**:
   - `components/activity/FileTree.tsx`
   - `components/activity/FileNode.tsx`
   - `components/activity/CodeViewer.tsx`
   - `components/activity/AgentCursor.tsx`
   - `components/activity/TerminalOutput.tsx`
   - `components/activity/ThoughtItem.tsx`

6. **Components - Progress**:
   - `components/activity/TaskProgressBar.tsx`
   - `components/activity/PhaseIndicator.tsx`

7. **Pages**:
   - `app/(dashboard)/tasks/[id]/activity/page.tsx`

8. **Utils**:
   - `lib/utils/syntax-highlighting.ts`
   - `lib/utils/file-icon.ts`
   - `lib/utils/ansi-to-html.ts` (terminal colors)

---

## Implementation Steps

### Step 1: Create Activity Types

```typescript
// types/activity.ts
export type ActivityType =
  | 'analyzing'
  | 'planning'
  | 'coding'
  | 'reviewing'
  | 'testing'
  | 'thinking'
  | 'asking'
  | 'completing'
  | 'error';

export interface ActivityEvent {
  id: string;
  timestamp: string;
  agent_id: string;
  agent_name: string;
  agent_role: AgentRole;
  activity_type: ActivityType;
  description: string;
  metadata?: {
    file_path?: string;
    line_number?: number;
    code_snippet?: string;
    diff?: {
      added: number;
      removed: number;
    };
    error_message?: string;
    log_level?: 'info' | 'warning' | 'error';
  };
}

export interface FileChange {
  path: string;
  type: 'added' | 'modified' | 'deleted';
  diff: {
    added: number;
    removed: number;
  };
  content?: string;
}

export interface AgentThought {
  id: string;
  agent_id: string;
  agent_name: string;
  timestamp: string;
  content: string;
  type: 'reasoning' | 'planning' | 'decision';
}
```

### Step 2: Create Activity Feed Hook

```typescript
// lib/hooks/useActivityFeed.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { sseService } from '@/lib/realtime/sse';
import { getAccessToken } from '@/lib/store/auth';
import type { ActivityEvent } from '@/types/activity';

export function useActivityFeed(executionId: string) {
  const queryClient = useQueryClient();

  // Fetch initial activity events
  const { data: events, isLoading } = useQuery<ActivityEvent[]>({
    queryKey: ['activity', executionId],
    queryFn: async () => {
      // Fetch from /api/v1/task-executions/{id}/messages
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/task-executions/${executionId}/messages`,
        {
          headers: { Authorization: `Bearer ${getAccessToken()}` },
        }
      );
      const messages = await response.json();

      // Transform messages to ActivityEvents
      return messages.map(transformMessageToActivity);
    },
  });

  // Subscribe to real-time updates
  useEffect(() => {
    const token = getAccessToken();
    const eventSource = sseService.connect(
      `${process.env.NEXT_PUBLIC_API_URL}/sse/execution/${executionId}`,
      token
    );

    // Handle new messages
    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      const activityEvent = transformMessageToActivity(data);

      queryClient.setQueryData<ActivityEvent[]>(
        ['activity', executionId],
        (old = []) => [...old, activityEvent]
      );
    });

    // Handle status updates
    eventSource.addEventListener('status_update', (event) => {
      const data = JSON.parse(event.data);
      const activityEvent: ActivityEvent = {
        id: `status-${Date.now()}`,
        timestamp: data.timestamp,
        agent_id: data.agent_id || 'system',
        agent_name: data.agent_name || 'System',
        agent_role: 'project_manager',
        activity_type: 'thinking',
        description: `Status changed to ${data.status}`,
        metadata: {},
      };

      queryClient.setQueryData<ActivityEvent[]>(
        ['activity', executionId],
        (old = []) => [...old, activityEvent]
      );
    });

    // Handle log entries
    eventSource.addEventListener('log', (event) => {
      const data = JSON.parse(event.data);
      const activityEvent: ActivityEvent = {
        id: `log-${Date.now()}`,
        timestamp: data.timestamp,
        agent_id: data.agent_id || 'system',
        agent_name: data.agent_name || 'System',
        agent_role: 'project_manager',
        activity_type: data.level === 'error' ? 'error' : 'thinking',
        description: data.message,
        metadata: {
          log_level: data.level,
        },
      };

      queryClient.setQueryData<ActivityEvent[]>(
        ['activity', executionId],
        (old = []) => [...old, activityEvent]
      );
    });

    return () => {
      sseService.disconnect();
    };
  }, [executionId, queryClient]);

  return { events: events || [], isLoading };
}

function transformMessageToActivity(message: any): ActivityEvent {
  const activityTypeMap: Record<string, ActivityType> = {
    task_assignment: 'analyzing',
    status_update: 'thinking',
    question: 'asking',
    code_review_request: 'reviewing',
    task_completion: 'completing',
  };

  return {
    id: message.id,
    timestamp: message.created_at,
    agent_id: message.sender_id,
    agent_name: message.sender_name || 'Unknown',
    agent_role: message.sender_role || 'project_manager',
    activity_type: activityTypeMap[message.message_type] || 'thinking',
    description: message.content,
    metadata: message.message_metadata || {},
  };
}
```

### Step 3: Create Split Pane Layout

```typescript
// components/activity/SplitPane.tsx
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultLeftWidth?: number; // percentage
}

export function SplitPane({ left, right, defaultLeftWidth = 40 }: SplitPaneProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    const container = e.currentTarget as HTMLElement;
    const rect = container.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - rect.left) / rect.width) * 100;

    // Constrain between 20% and 80%
    if (newLeftWidth >= 20 && newLeftWidth <= 80) {
      setLeftWidth(newLeftWidth);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div
      className="flex h-full"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        className="border-r bg-white overflow-y-auto"
        style={{ width: `${leftWidth}%` }}
      >
        {left}
      </div>

      <div
        className="w-1 cursor-col-resize bg-gray-200 hover:bg-blue-500 transition-colors"
        onMouseDown={handleMouseDown}
      />

      <div
        className="bg-gray-50 overflow-y-auto"
        style={{ width: `${100 - leftWidth}%` }}
      >
        {right}
      </div>
    </div>
  );
}
```

### Step 4: Create Activity Feed

```typescript
// components/activity/ActivityFeed.tsx
'use client';

import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ActivityItem } from './ActivityItem';
import { Button } from '@/components/ui/button';
import { Pause, Play } from 'lucide-react';
import type { ActivityEvent } from '@/types/activity';

interface ActivityFeedProps {
  events: ActivityEvent[];
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <h3 className="font-semibold">Activity Feed</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setAutoScroll(!autoScroll)}
        >
          {autoScroll ? (
            <>
              <Pause className="h-4 w-4 mr-1" />
              Pause
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-1" />
              Resume
            </>
          )}
        </Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence initial={false}>
          {events.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <ActivityItem event={event} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

### Step 5: Create Activity Item

```typescript
// components/activity/ActivityItem.tsx
'use client';

import { formatDistanceToNow } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { AgentAvatar } from './AgentAvatar';
import { ActionIcon } from './ActionIcon';
import type { ActivityEvent } from '@/types/activity';

interface ActivityItemProps {
  event: ActivityEvent;
}

export function ActivityItem({ event }: ActivityItemProps) {
  const activityColors: Record<string, string> = {
    analyzing: 'bg-blue-100 text-blue-800',
    planning: 'bg-purple-100 text-purple-800',
    coding: 'bg-green-100 text-green-800',
    reviewing: 'bg-yellow-100 text-yellow-800',
    testing: 'bg-orange-100 text-orange-800',
    thinking: 'bg-gray-100 text-gray-800',
    asking: 'bg-pink-100 text-pink-800',
    completing: 'bg-emerald-100 text-emerald-800',
    error: 'bg-red-100 text-red-800',
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <AgentAvatar
        name={event.agent_name}
        role={event.agent_role}
        size="sm"
        status={event.activity_type === 'coding' ? 'active' : 'idle'}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm">{event.agent_name}</span>
          <Badge className={`text-xs ${activityColors[event.activity_type]}`}>
            {event.activity_type}
          </Badge>
        </div>

        <p className="text-sm text-gray-700">{event.description}</p>

        {event.metadata?.file_path && (
          <div className="mt-1 text-xs text-gray-500 font-mono">
            {event.metadata.file_path}
            {event.metadata.line_number && `:${event.metadata.line_number}`}
          </div>
        )}

        {event.metadata?.diff && (
          <div className="mt-1 text-xs space-x-2">
            <span className="text-green-600">
              +{event.metadata.diff.added}
            </span>
            <span className="text-red-600">
              -{event.metadata.diff.removed}
            </span>
          </div>
        )}

        <div className="mt-1 text-xs text-gray-400">
          {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
        </div>
      </div>

      <ActionIcon type={event.activity_type} />
    </div>
  );
}
```

### Step 6: Create Agent Avatar with Status

```typescript
// components/activity/AgentAvatar.tsx
'use client';

import { motion } from 'framer-motion';
import type { AgentRole } from '@/types/squad';

interface AgentAvatarProps {
  name: string;
  role: AgentRole;
  size?: 'sm' | 'md' | 'lg';
  status?: 'active' | 'thinking' | 'idle';
}

export function AgentAvatar({ name, role, size = 'md', status = 'idle' }: AgentAvatarProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  };

  const roleColors: Record<AgentRole, string> = {
    project_manager: 'bg-purple-500',
    tech_lead: 'bg-blue-500',
    backend_developer: 'bg-green-500',
    frontend_developer: 'bg-cyan-500',
    qa_tester: 'bg-orange-500',
    solution_architect: 'bg-indigo-500',
    devops_engineer: 'bg-red-500',
    ai_engineer: 'bg-pink-500',
    designer: 'bg-yellow-500',
  };

  const statusIndicator = {
    active: 'bg-green-400',
    thinking: 'bg-yellow-400',
    idle: 'bg-gray-400',
  };

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="relative">
      <div
        className={`${sizeClasses[size]} ${roleColors[role]} rounded-full flex items-center justify-center text-white font-semibold`}
      >
        {initials}
      </div>

      {status !== 'idle' && (
        <motion.div
          className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${statusIndicator[status]}`}
          animate={
            status === 'active'
              ? {
                  scale: [1, 1.2, 1],
                  opacity: [1, 0.7, 1],
                }
              : {}
          }
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </div>
  );
}
```

### Step 7: Create Code Viewer with Agent Cursor

```typescript
// components/activity/CodeViewer.tsx
'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { motion } from 'framer-motion';

interface CodeViewerProps {
  code: string;
  language: string;
  agentCursorLine?: number;
}

export function CodeViewer({ code, language, agentCursorLine }: CodeViewerProps) {
  return (
    <div className="relative">
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        showLineNumbers
        wrapLines
        lineProps={(lineNumber) => {
          const style: any = { display: 'block', position: 'relative' };

          // Highlight agent cursor line
          if (lineNumber === agentCursorLine) {
            style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
          }

          return { style };
        }}
      >
        {code}
      </SyntaxHighlighter>

      {agentCursorLine && (
        <motion.div
          className="absolute right-0 w-1 h-6 bg-blue-500"
          style={{ top: `${(agentCursorLine - 1) * 24}px` }}
          animate={{
            opacity: [1, 0.3, 1],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </div>
  );
}
```

### Step 8: Create Progress Bar

```typescript
// components/activity/TaskProgressBar.tsx
'use client';

import { motion } from 'framer-motion';
import type { TaskStatus } from '@/types/task';

interface TaskProgressBarProps {
  status: TaskStatus;
}

const PROGRESS_MAP: Record<TaskStatus, number> = {
  pending: 0,
  analyzing: 12,
  planning: 25,
  delegated: 37,
  in_progress: 62,
  reviewing: 75,
  testing: 87,
  completed: 100,
  blocked: 50,
  failed: 0,
  cancelled: 0,
};

export function TaskProgressBar({ status }: TaskProgressBarProps) {
  const progress = PROGRESS_MAP[status] || 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium capitalize">{status.replace('_', ' ')}</span>
        <span className="text-gray-500">{progress}%</span>
      </div>

      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-blue-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}
```

### Step 9: Create Activity Page

```typescript
// app/(dashboard)/tasks/[id]/activity/page.tsx
'use client';

import { useParams } from 'next/navigation';
import { useActivityFeed } from '@/lib/hooks/useActivityFeed';
import { useTaskDetail } from '@/lib/hooks/useTaskDetail';
import { SplitPane } from '@/components/activity/SplitPane';
import { ActivityFeed } from '@/components/activity/ActivityFeed';
import { TaskProgressBar } from '@/components/activity/TaskProgressBar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function TaskActivityPage() {
  const params = useParams();
  const taskId = params.id as string;

  const { task, isLoading: taskLoading } = useTaskDetail(taskId);
  const { events, isLoading: eventsLoading } = useActivityFeed(taskId);

  if (taskLoading || eventsLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="h-[calc(100vh-64px)]">
      <SplitPane
        left={
          <div className="p-4 space-y-4">
            <div>
              <h2 className="text-2xl font-bold">{task?.title}</h2>
              <p className="text-gray-600 mt-1">{task?.description}</p>
            </div>

            <TaskProgressBar status={task?.status || 'pending'} />

            <ActivityFeed events={events} />
          </div>
        }
        right={
          <div className="h-full">
            <Tabs defaultValue="files" className="h-full flex flex-col">
              <TabsList className="m-4">
                <TabsTrigger value="files">Files</TabsTrigger>
                <TabsTrigger value="terminal">Terminal</TabsTrigger>
                <TabsTrigger value="thoughts">Thoughts</TabsTrigger>
              </TabsList>

              <TabsContent value="files" className="flex-1 overflow-y-auto m-4">
                <div>File tree and code viewer coming soon...</div>
              </TabsContent>

              <TabsContent value="terminal" className="flex-1 overflow-y-auto m-4">
                <div>Terminal output coming soon...</div>
              </TabsContent>

              <TabsContent value="thoughts" className="flex-1 overflow-y-auto m-4">
                <div>Agent thoughts coming soon...</div>
              </TabsContent>
            </Tabs>
          </div>
        }
      />
    </div>
  );
}
```

---

## Todo List

### P0 - Critical Path

- [ ] Create activity event types
- [ ] Create useActivityFeed hook with SSE integration
- [ ] Build SplitPane component with resize
- [ ] Build ActivityFeed component with auto-scroll
- [ ] Build ActivityItem component
- [ ] Build AgentAvatar with status indicator
- [ ] Build ActionIcon component
- [ ] Build TaskProgressBar with animations
- [ ] Create activity page layout
- [ ] Implement real-time event streaming
- [ ] Add timestamp formatting (relative time)
- [ ] Test with multiple simultaneous agents
- [ ] Add pause/resume auto-scroll
- [ ] Handle SSE reconnection gracefully

### P1 - Important

- [ ] Build FileTree component
- [ ] Build CodeViewer with syntax highlighting
- [ ] Add agent cursor animation in code
- [ ] Build TerminalOutput component
- [ ] Add ANSI color support for terminal
- [ ] Build ThoughtItem component
- [ ] Add file diff indicators (+/-)
- [ ] Implement "follow agent" mode
- [ ] Add virtualization for 100+ events
- [ ] Add search/filter for activity feed
- [ ] Add export activity log feature

### P2 - Nice to Have

- [ ] Add agent workload chart
- [ ] Add time-based activity heatmap
- [ ] Add playback speed control
- [ ] Add bookmark favorite activities
- [ ] Add share activity link
- [ ] Add dark mode for code viewer
- [ ] Add minimap for long files
- [ ] Add collaborative cursor for multiple agents

---

## Success Criteria

### Functional Criteria
✅ Activity feed shows all agent actions in chronological order
✅ Real-time updates appear within 300ms
✅ Progress bar reflects task phase accurately
✅ Agent avatars show correct status (active/thinking/idle)
✅ Split pane is resizable and remembers size
✅ Auto-scroll can be paused/resumed
✅ File paths and line numbers display correctly
✅ Code syntax highlighting works for major languages

### Technical Criteria
✅ SSE connection handles reconnection
✅ Activity feed handles 100+ events without lag
✅ Animations run at 60fps
✅ Component re-renders optimized with memo
✅ TypeScript types match backend schemas

### Performance Criteria
✅ Activity item render < 16ms (60fps)
✅ Real-time event latency < 300ms
✅ Syntax highlighting < 100ms for 1000 lines
✅ Smooth scroll without jank

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SSE event flooding (100+ events/sec) | Medium | High | Debouncing, batching, virtualization |
| Syntax highlighting performance | Low | Medium | Lazy load, virtualize code viewer |
| Agent cursor synchronization lag | Medium | Medium | Optimistic updates, interpolation |
| Mobile layout complexity | High | Medium | Stack panels vertically, simplified view |
| Memory leak from event accumulation | Low | High | Limit event history, cleanup old events |

---

## Security Considerations

- Sanitize activity descriptions (XSS prevention)
- Validate file paths (prevent path traversal display)
- Limit event history to prevent memory exhaustion

---

## Next Steps

After completing Phase 3:
1. **Review**: Ensure all P0 todos completed
2. **Test**: Real-time updates with multiple agents
3. **Proceed**: Start Phase 4 (Conversation System)
