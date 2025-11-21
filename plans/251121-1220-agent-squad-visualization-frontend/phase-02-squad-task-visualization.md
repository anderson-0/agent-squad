# Phase 2: Squad & Task Visualization

**Status**: Pending
**Priority**: P0
**Dependencies**: Phase 1 (Foundation & Setup)
**Estimated Duration**: Claude (3 hrs) | Senior Dev (2 days) | Junior Dev (4-5 days)

---

## Context

Phase 2 builds the core visualization components for squads and tasks. This includes squad list/grid views, task boards (Kanban-style), agent cards with status indicators, and real-time updates via SSE/Socket.io. These components form the foundation for the agent visualization system.

**Related Files**:
- Research: `research/researcher-01-ux-patterns.md` (Asana boards, Figma multiplayer)
- Backend: `scout/scout-02-backend-api.md` (squads, tasks, SSE endpoints)
- Agent System: `scout/scout-03-agent-system.md` (agent roles, task states)

---

## Overview

**Goal**: Create interactive squad and task visualization with real-time updates.

**Key Deliverables**:
1. Squad list view with filters
2. Squad detail page with agent composition
3. Task board (Kanban columns: PENDING → COMPLETED)
4. Agent status cards with activity indicators
5. Real-time updates for task state changes
6. Optimistic updates for user actions

**Dates**:
- Start: TBD (after Phase 1)
- End: TBD
- **Status**: Pending

---

## Key Insights from Research

### From `researcher-01-ux-patterns.md`

**Asana Board Design**:
- Full-bleed card images, larger custom field pills
- Slide-in task pane (not modal) to keep context visible
- Drag-and-drop fluidity like sticky notes
- Multiple view modes: Kanban, List, Timeline

**Figma Multiplayer**:
- Real-time cursor positions with user avatars
- Selection outlines in user's color
- Allow "shadowing" an agent to watch their work

**Recommended Pattern for Agent Squad**:
- Kanban columns: Queued → In Progress → Review → Done
- Agent avatar on cards they're working on
- Real-time status updates without refresh
- Slide-in panel for task details

### From `scout-03-agent-system.md`

**Task States**:
```
PENDING → ANALYZING → PLANNING → DELEGATED → IN_PROGRESS → REVIEWING → TESTING → COMPLETED
                                     ↓                                        ↓
                                  BLOCKED ←──────────────────────────────────┘
```

**Agent Roles**:
- Project Manager (orchestrator)
- Tech Lead (technical oversight)
- Backend/Frontend Developers
- QA Tester, DevOps, Designer, etc.

**Squad Structure**:
- Squad has multiple members (agents)
- Each member has role, specialization, LLM config
- Status: active, paused, archived

---

## Requirements

### Functional Requirements

**FR-2.1**: Squad list view showing all user's squads
**FR-2.2**: Squad grid view with card layout
**FR-2.3**: Squad filters (status: active/paused/archived, search by name)
**FR-2.4**: Squad detail page showing squad info + agent members
**FR-2.5**: Agent composition chart (pie chart of roles)
**FR-2.6**: Create squad modal with form
**FR-2.7**: Task board (Kanban) with columns for each state
**FR-2.8**: Task cards showing title, description, assigned agent, status
**FR-2.9**: Drag-and-drop to move tasks between columns
**FR-2.10**: Slide-in task detail panel (not modal)
**FR-2.11**: Real-time updates when tasks change state
**FR-2.12**: Optimistic updates when user moves tasks

### Non-Functional Requirements

**NFR-2.1**: Smooth animations for card movements (60fps)
**NFR-2.2**: Virtualization for 100+ tasks
**NFR-2.3**: Mobile-responsive (stack columns vertically)
**NFR-2.4**: Loading skeletons for async data
**NFR-2.5**: Error states with retry buttons
**NFR-2.6**: Accessibility (keyboard navigation, screen readers)

---

## Architecture

### Component Hierarchy

```
Page: /squads
├── SquadList
│   ├── SquadFilters (search, status filter)
│   ├── ViewToggle (grid/list)
│   ├── SquadGrid (if grid view)
│   │   └── SquadCard (repeated)
│   └── SquadListTable (if list view)
│       └── SquadRow (repeated)
└── CreateSquadButton → CreateSquadDialog

Page: /squads/[id]
├── SquadHeader (name, status, actions)
├── SquadStats (agent count, active tasks, cost estimate)
├── AgentComposition (pie chart of roles)
├── AgentList
│   └── AgentCard (repeated)
│       ├── Avatar
│       ├── Role Badge
│       ├── Status Indicator (active/idle)
│       └── LLM Model Tag
└── AddAgentButton → AddAgentDialog

Page: /tasks
├── TaskFilters (squad, status, assigned agent)
├── TaskBoard (Kanban)
│   ├── Column (PENDING)
│   │   └── TaskCard (repeated)
│   ├── Column (ANALYZING)
│   │   └── TaskCard (repeated)
│   ├── Column (PLANNING)
│   │   └── TaskCard (repeated)
│   ├── Column (DELEGATED)
│   │   └── TaskCard (repeated)
│   ├── Column (IN_PROGRESS)
│   │   └── TaskCard (repeated)
│   ├── Column (REVIEWING)
│   │   └── TaskCard (repeated)
│   ├── Column (TESTING)
│   │   └── TaskCard (repeated)
│   └── Column (COMPLETED)
│       └── TaskCard (repeated)
└── TaskDetailPanel (slide-in, conditional)
    ├── TaskHeader
    ├── TaskDescription
    ├── TaskMetadata
    ├── AssignedAgent
    ├── ActivityTimeline
    └── TaskActions
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         UI Component (SquadList, TaskBoard)                  │
│         - Displays data                                      │
│         - Handles user actions                               │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         TanStack Query Hook (useSquads, useTasks)            │
│         - Fetches data from API                              │
│         - Caches results                                     │
│         - Manages loading/error states                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         API Client (squads.ts, tasks.ts)                     │
│         - Makes HTTP requests                                │
│         - Handles errors                                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         Backend API (/api/v1/squads, /api/v1/tasks)          │
└─────────────────────────────────────────────────────────────┘

Real-Time Updates Flow:
┌─────────────────────────────────────────────────────────────┐
│         Backend Event (task status changed)                  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         SSE Service (/api/v1/sse/execution/{id})             │
│         - Broadcasts event to connected clients              │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         useRealtime Hook (subscribes to SSE)                 │
│         - Receives event                                     │
│         - Parses event data                                  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         TanStack Query (invalidate/update cache)             │
│         - Updates cached data                                │
│         - Triggers component re-render                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│         UI Component (automatically re-renders)              │
└─────────────────────────────────────────────────────────────┘
```

### State Management

**Server State (TanStack Query)**:
- Squads list: `useQuery(['squads'])`
- Squad detail: `useQuery(['squad', id])`
- Squad agents: `useQuery(['squad', id, 'agents'])`
- Tasks: `useQuery(['tasks', { squadId, status }])`
- Task detail: `useQuery(['task', id])`

**Client State (Zustand)**:
- Selected squad ID
- View mode (grid/list)
- Active filters (status, search)
- Selected task ID (for detail panel)
- Drag-and-drop state

**Example Store**:
```typescript
interface UIState {
  // Squad view state
  squadViewMode: 'grid' | 'list';
  squadStatusFilter: 'all' | 'active' | 'paused' | 'archived';
  squadSearchQuery: string;

  // Task view state
  selectedTaskId: string | null;
  taskSquadFilter: string | null;
  taskStatusFilter: string | null;

  // Actions
  setSquadViewMode: (mode: 'grid' | 'list') => void;
  setSquadStatusFilter: (status: string) => void;
  setSquadSearchQuery: (query: string) => void;
  setSelectedTask: (id: string | null) => void;
}
```

### Real-Time Integration

```typescript
// hooks/useRealtimeTaskUpdates.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { sseService } from '@/lib/realtime/sse';

export function useRealtimeTaskUpdates(executionId: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = getAccessToken();
    const eventSource = sseService.connect(
      `${process.env.NEXT_PUBLIC_API_URL}/sse/execution/${executionId}`,
      token
    );

    // Handle status updates
    eventSource.addEventListener('status_update', (event) => {
      const data = JSON.parse(event.data);

      // Update task cache
      queryClient.setQueryData(['task', data.task_id], (old: any) => ({
        ...old,
        status: data.status,
        updated_at: data.timestamp,
      }));

      // Invalidate tasks list to re-fetch
      queryClient.invalidateQueries(['tasks']);
    });

    // Handle new messages
    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);

      // Append to messages cache
      queryClient.setQueryData(['task', data.task_id, 'messages'], (old: any[]) => [
        ...(old || []),
        data,
      ]);
    });

    return () => {
      sseService.disconnect();
    };
  }, [executionId, queryClient]);
}
```

---

## Related Code Files

### Files to Create

1. **Types**:
   - `types/squad.ts` (Squad, SquadMember, SquadCreate, SquadUpdate)
   - `types/task.ts` (Task, TaskExecution, TaskCreate, TaskUpdate)
   - `types/agent.ts` (Agent, AgentRole, AgentStatus)

2. **API Clients**:
   - `lib/api/squads.ts` (CRUD operations for squads)
   - `lib/api/squad-members.ts` (CRUD for squad members)
   - `lib/api/tasks.ts` (CRUD for tasks)
   - `lib/api/task-executions.ts` (Task execution operations)

3. **React Query Hooks**:
   - `lib/hooks/useSquads.ts`
   - `lib/hooks/useSquadDetail.ts`
   - `lib/hooks/useTasks.ts`
   - `lib/hooks/useTaskDetail.ts`
   - `lib/hooks/useRealtimeTaskUpdates.ts`

4. **Components - Squad**:
   - `components/squads/SquadList.tsx`
   - `components/squads/SquadGrid.tsx`
   - `components/squads/SquadCard.tsx`
   - `components/squads/SquadFilters.tsx`
   - `components/squads/CreateSquadDialog.tsx`

5. **Components - Agent**:
   - `components/agents/AgentCard.tsx`
   - `components/agents/AgentList.tsx`
   - `components/agents/AgentComposition.tsx`
   - `components/agents/AgentStatusIndicator.tsx`
   - `components/agents/AddAgentDialog.tsx`

6. **Components - Task**:
   - `components/tasks/TaskBoard.tsx`
   - `components/tasks/TaskColumn.tsx`
   - `components/tasks/TaskCard.tsx`
   - `components/tasks/TaskDetailPanel.tsx`
   - `components/tasks/TaskFilters.tsx`
   - `components/tasks/CreateTaskDialog.tsx`

7. **Pages**:
   - `app/(dashboard)/squads/page.tsx`
   - `app/(dashboard)/squads/[id]/page.tsx`
   - `app/(dashboard)/tasks/page.tsx`

8. **Store**:
   - `lib/store/ui.ts` (view modes, filters, selections)

---

## Implementation Steps

### Step 1: Create Type Definitions

```typescript
// types/squad.ts
export type SquadStatus = 'active' | 'paused' | 'archived';

export interface Squad {
  id: string;
  name: string;
  description: string;
  status: SquadStatus;
  organization_id: string;
  user_id: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SquadMember {
  id: string;
  squad_id: string;
  role: AgentRole;
  specialization?: string;
  llm_provider: 'openai' | 'anthropic' | 'groq' | 'ollama';
  llm_model: string;
  system_prompt?: string;
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

export type AgentRole =
  | 'project_manager'
  | 'tech_lead'
  | 'backend_developer'
  | 'frontend_developer'
  | 'qa_tester'
  | 'solution_architect'
  | 'devops_engineer'
  | 'ai_engineer'
  | 'designer';

export interface SquadWithAgents extends Squad {
  members: SquadMember[];
}

export interface SquadCreate {
  name: string;
  description: string;
  organization_id?: string;
}

export interface SquadUpdate {
  name?: string;
  description?: string;
  status?: SquadStatus;
}
```

```typescript
// types/task.ts
export type TaskStatus =
  | 'pending'
  | 'analyzing'
  | 'planning'
  | 'delegated'
  | 'in_progress'
  | 'reviewing'
  | 'testing'
  | 'completed'
  | 'blocked'
  | 'failed'
  | 'cancelled';

export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  project_id: string;
  external_id?: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskExecution {
  id: string;
  task_id: string;
  squad_id: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
  logs: string[];
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  project_id: string;
  title: string;
  description: string;
  priority?: TaskPriority;
}
```

### Step 2: Create API Clients

```typescript
// lib/api/squads.ts
import apiClient from './client';
import type { Squad, SquadWithAgents, SquadCreate, SquadUpdate } from '@/types/squad';

export const squadsApi = {
  list: async (params?: {
    organization_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<Squad[]> => {
    const response = await apiClient.get('/squads', { params });
    return response.data;
  },

  get: async (id: string): Promise<Squad> => {
    const response = await apiClient.get(`/squads/${id}`);
    return response.data;
  },

  getWithAgents: async (id: string): Promise<SquadWithAgents> => {
    const response = await apiClient.get(`/squads/${id}/details`);
    return response.data;
  },

  create: async (data: SquadCreate): Promise<Squad> => {
    const response = await apiClient.post('/squads', data);
    return response.data;
  },

  update: async (id: string, data: SquadUpdate): Promise<Squad> => {
    const response = await apiClient.put(`/squads/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/squads/${id}`);
  },

  updateStatus: async (id: string, status: string): Promise<Squad> => {
    const response = await apiClient.patch(`/squads/${id}/status`, { status });
    return response.data;
  },
};
```

```typescript
// lib/api/tasks.ts
import apiClient from './client';
import type { Task, TaskExecution, TaskCreate } from '@/types/task';

export const tasksApi = {
  list: async (params?: {
    squad_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<Task[]> => {
    const response = await apiClient.get('/tasks', { params });
    return response.data;
  },

  get: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  create: async (data: TaskCreate): Promise<Task> => {
    const response = await apiClient.post('/tasks', data);
    return response.data;
  },

  updateStatus: async (id: string, status: string): Promise<Task> => {
    const response = await apiClient.patch(`/tasks/${id}/status`, { status });
    return response.data;
  },
};

export const taskExecutionsApi = {
  start: async (taskId: string, squadId: string): Promise<TaskExecution> => {
    const response = await apiClient.post('/task-executions', {
      task_id: taskId,
      squad_id: squadId,
    });
    return response.data;
  },

  get: async (id: string): Promise<TaskExecution> => {
    const response = await apiClient.get(`/task-executions/${id}`);
    return response.data;
  },
};
```

### Step 3: Create React Query Hooks

```typescript
// lib/hooks/useSquads.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { squadsApi } from '@/lib/api/squads';
import type { SquadCreate, SquadUpdate } from '@/types/squad';

export function useSquads(params?: { status?: string }) {
  return useQuery({
    queryKey: ['squads', params],
    queryFn: () => squadsApi.list(params),
  });
}

export function useSquad(id: string) {
  return useQuery({
    queryKey: ['squad', id],
    queryFn: () => squadsApi.get(id),
    enabled: !!id,
  });
}

export function useSquadWithAgents(id: string) {
  return useQuery({
    queryKey: ['squad', id, 'agents'],
    queryFn: () => squadsApi.getWithAgents(id),
    enabled: !!id,
  });
}

export function useCreateSquad() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SquadCreate) => squadsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['squads']);
    },
  });
}

export function useUpdateSquad() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SquadUpdate }) =>
      squadsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['squad', variables.id]);
      queryClient.invalidateQueries(['squads']);
    },
  });
}
```

### Step 4: Create UI State Store

```typescript
// lib/store/ui.ts
import { create } from 'zustand';

interface UIState {
  // Squad view state
  squadViewMode: 'grid' | 'list';
  squadStatusFilter: 'all' | 'active' | 'paused' | 'archived';
  squadSearchQuery: string;

  // Task view state
  selectedTaskId: string | null;
  taskSquadFilter: string | null;
  taskStatusFilter: string | null;

  // Actions
  setSquadViewMode: (mode: 'grid' | 'list') => void;
  setSquadStatusFilter: (status: UIState['squadStatusFilter']) => void;
  setSquadSearchQuery: (query: string) => void;
  setSelectedTask: (id: string | null) => void;
  setTaskSquadFilter: (id: string | null) => void;
  setTaskStatusFilter: (status: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  squadViewMode: 'grid',
  squadStatusFilter: 'all',
  squadSearchQuery: '',
  selectedTaskId: null,
  taskSquadFilter: null,
  taskStatusFilter: null,

  setSquadViewMode: (mode) => set({ squadViewMode: mode }),
  setSquadStatusFilter: (status) => set({ squadStatusFilter: status }),
  setSquadSearchQuery: (query) => set({ squadSearchQuery: query }),
  setSelectedTask: (id) => set({ selectedTaskId: id }),
  setTaskSquadFilter: (id) => set({ taskSquadFilter: id }),
  setTaskStatusFilter: (status) => set({ taskStatusFilter: status }),
}));
```

### Step 5: Create Squad Components

```typescript
// components/squads/SquadCard.tsx
'use client';

import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users } from 'lucide-react';
import type { Squad } from '@/types/squad';

interface SquadCardProps {
  squad: Squad;
}

export function SquadCard({ squad }: SquadCardProps) {
  const statusColors = {
    active: 'bg-green-100 text-green-800',
    paused: 'bg-yellow-100 text-yellow-800',
    archived: 'bg-gray-100 text-gray-800',
  };

  return (
    <Link href={`/squads/${squad.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>{squad.name}</CardTitle>
              <CardDescription className="mt-1">
                {squad.description}
              </CardDescription>
            </div>
            <Badge className={statusColors[squad.status]}>
              {squad.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Users className="h-4 w-4" />
            <span>View agents</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
```

```typescript
// app/(dashboard)/squads/page.tsx
'use client';

import { useState } from 'react';
import { useSquads } from '@/lib/hooks/useSquads';
import { useUIStore } from '@/lib/store/ui';
import { SquadCard } from '@/components/squads/SquadCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Grid, List } from 'lucide-react';

export default function SquadsPage() {
  const squadStatusFilter = useUIStore((state) => state.squadStatusFilter);
  const setSquadStatusFilter = useUIStore((state) => state.setSquadStatusFilter);
  const squadSearchQuery = useUIStore((state) => state.squadSearchQuery);
  const setSquadSearchQuery = useUIStore((state) => state.setSquadSearchQuery);

  const { data: squads, isLoading } = useSquads({
    status: squadStatusFilter === 'all' ? undefined : squadStatusFilter,
  });

  const filteredSquads = squads?.filter((squad) =>
    squad.name.toLowerCase().includes(squadSearchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Squads</h1>
          <p className="text-gray-600 mt-1">Manage your agent squads</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Squad
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <Input
          placeholder="Search squads..."
          value={squadSearchQuery}
          onChange={(e) => setSquadSearchQuery(e.target.value)}
          className="max-w-xs"
        />
        <Tabs value={squadStatusFilter} onValueChange={(v: any) => setSquadStatusFilter(v)}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="paused">Paused</TabsTrigger>
            <TabsTrigger value="archived">Archived</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSquads?.map((squad) => (
            <SquadCard key={squad.id} squad={squad} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Step 6: Create Task Board Components

(Continue with TaskBoard, TaskColumn, TaskCard implementations using @dnd-kit for drag-and-drop)

### Step 7: Implement Real-Time Updates

(Implement SSE integration for task status updates)

### Step 8: Add Optimistic Updates

(Implement optimistic UI updates for task moves)

---

## Todo List

### P0 - Critical Path

- [ ] Create type definitions for Squad, Task, Agent
- [ ] Create API clients for squads, tasks, agents
- [ ] Create React Query hooks for data fetching
- [ ] Create UI state store (Zustand)
- [ ] Build SquadCard component
- [ ] Build SquadGrid component
- [ ] Build SquadList page with filters
- [ ] Build Squad detail page
- [ ] Build AgentCard component with status indicator
- [ ] Build AgentList component
- [ ] Build AgentComposition chart
- [ ] Build TaskBoard component
- [ ] Build TaskColumn component
- [ ] Build TaskCard component
- [ ] Implement drag-and-drop for tasks ([@dnd-kit/core](https://dndkit.com/))
- [ ] Build TaskDetailPanel (slide-in)
- [ ] Implement real-time task updates via SSE
- [ ] Add optimistic updates for task moves
- [ ] Test real-time updates with multiple clients
- [ ] Add loading skeletons for all async data

### P1 - Important

- [ ] Add Create Squad dialog
- [ ] Add Add Agent dialog
- [ ] Add Create Task dialog
- [ ] Implement squad status toggle (active/paused)
- [ ] Add task filters (squad, status, agent)
- [ ] Implement virtualization for 100+ tasks
- [ ] Add animations for card movements (Framer Motion)
- [ ] Add mobile-responsive layout
- [ ] Add error states with retry buttons
- [ ] Add keyboard navigation for task board

### P2 - Nice to Have

- [ ] Add squad cost estimate display
- [ ] Add bulk actions for tasks
- [ ] Add task priority indicators
- [ ] Add agent workload indicators
- [ ] Add task timeline view
- [ ] Add calendar view for tasks
- [ ] Add export squad data feature
- [ ] Add duplicate squad feature

---

## Success Criteria

### Functional Criteria
✅ Squad list displays all user's squads
✅ Squad filters work correctly
✅ Squad detail shows agents and composition
✅ Task board displays tasks in correct columns
✅ Drag-and-drop moves tasks between columns
✅ Task detail panel shows full task info
✅ Real-time updates reflect immediately
✅ Optimistic updates feel instant

### Technical Criteria
✅ All components use TypeScript with strict types
✅ TanStack Query caching reduces API calls
✅ Real-time updates via SSE working reliably
✅ Drag-and-drop smooth at 60fps
✅ Mobile responsive (tablet/phone)
✅ Loading states for all async operations
✅ Error boundaries handle failures gracefully

### Performance Criteria
✅ Squad list renders < 200ms
✅ Task board renders 100 tasks < 500ms
✅ Drag-and-drop latency < 16ms (60fps)
✅ Real-time update latency < 300ms

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Drag-and-drop performance | Medium | High | Use @dnd-kit, virtualization |
| Real-time sync conflicts | High | High | Optimistic updates + conflict resolution |
| Large task boards (500+ tasks) | Low | High | Virtualization, pagination |
| Mobile touch interactions | Medium | Medium | Test on real devices, adjust hit targets |
| SSE connection drops | High | Medium | Auto-reconnect, fallback to polling |

---

## Security Considerations

- Validate all task state transitions on backend
- Prevent unauthorized squad access (ownership check)
- Sanitize task descriptions (XSS prevention)
- Rate limit task creation/updates

---

## Next Steps

After completing Phase 2:
1. **Review**: Ensure all P0 todos completed
2. **Test**: Drag-and-drop, real-time updates
3. **Proceed**: Start Phase 3 (Agent Work Visualization)
