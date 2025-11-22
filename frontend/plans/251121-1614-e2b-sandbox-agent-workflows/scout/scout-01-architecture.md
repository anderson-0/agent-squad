# Architecture Scout Report - E2B Sandbox Integration

**Date:** 2025-11-21
**Scope:** Current codebase architecture analysis for E2B sandbox integration

## Executive Summary

**Current State:** Frontend-only with mock data. No E2B integration exists. Backend API expected at `localhost:8000` (not implemented). Infrastructure ready for E2B integration.

**Key Finding:** System architecture supports E2B integration - needs backend implementation + frontend updates.

---

## 1. Type Definitions (`types/squad.ts`)

### Agent Interface
```typescript
export interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus; // 'idle' | 'thinking' | 'working' | 'completed' | 'error'
  current_task_id?: string; // ✅ Already tracks task assignment
  avatar_url?: string;
  stats: AgentStats;
}
```

**Extension Points for E2B:**
- Add `sandbox_id?: string` - Track E2B sandbox per agent
- Add `git_context?: GitContext` - Store branch, commit SHA, repo URL
- Extend `AgentStatus` with 'initializing' | 'cloning' | 'committing' | 'pushing'

### Task Interface
```typescript
export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus; // 'pending' | 'in_progress' | 'in_review' | 'done'
  priority: TaskPriority;
  assigned_agent_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  subtasks?: Subtask[];
  time_estimate_hours?: number;
  time_elapsed_hours?: number;
}
```

**Extension Points for E2B:**
- Add `git_branch?: string` - Track task-specific branch
- Add `pull_request_url?: string` - Link to GitHub PR
- Add `commit_history?: string[]` - Track commits made
- Add `sandbox_logs?: SandboxLog[]` - Execution logs

### Squad Interface
Well-structured with agents[], tasks[], achievements[] - no changes needed.

---

## 2. API & Backend Structure

### API Client (`lib/api/client.ts`)
```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true, // HTTP-only cookies
});
```

**Current State:**
- ✅ Axios configured
- ✅ Auto token refresh on 401
- ✅ Environment variable support
- ❌ Backend not implemented (returns 404)

**Environment Variables (`.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SSE_URL=http://localhost:8000/api/v1/sse
```

**No API Routes:** `app/api/` directory doesn't exist - all backend logic expected in separate service.

---

## 3. State Management (`lib/store/`)

### Current Stores
- `auth.ts` - Fake user for development (Zustand + persist)

**Missing Stores Needed:**
- `squads.ts` - Squad/agent/task state management
- `sandboxes.ts` - E2B sandbox lifecycle tracking
- `git.ts` - Git operations status (clone, commit, push progress)

**Pattern:** Zustand with persist middleware, follows same structure as auth.ts

---

## 4. Mock Data (`lib/mock-data/squads.ts`)

### Current Structure
- 3 squads with 4 agents each
- Tasks with subtasks, time estimates, priorities
- Agent stats tracking (tasks_completed, success_rate, total_time_hours)
- `current_task_id` already links agents to tasks ✅

**Key Pattern:**
```typescript
{
  id: 'agent-1',
  status: 'working',
  current_task_id: 'task-2', // ✅ Already tracks assignment
}
```

**Extension:** Mock data ready to add sandbox_id, git_branch fields.

---

## 5. Frontend Pages & Components

### Squad Detail Page (`app/(dashboard)/squads/[id]/page.tsx`)
**Task Update Handler:**
```typescript
const handleTaskUpdate = (taskId: string, status: TaskStatus, feedback?: string) => {
  console.log(`Task ${taskId} moved to ${status}`, feedback);
  // In real implementation, this would call an API
};
```

**Current:** Logs only, no API call. Ready for integration.

### KanbanBoard (`components/squads/KanbanBoard.tsx`)
**Features:**
- 4 columns: Pending → In Progress → In Review → Done
- WIP limits based on available agents
- Drag-and-drop with modals
- Agent availability checking: `agents.filter(a => !a.current_task_id)`

**Extension Point:** When task moves to "In Progress", trigger:
1. Create E2B sandbox
2. Clone repository
3. Create branch `task-{taskId}`
4. Update agent status to 'working'

### Agent Work Page (`app/(dashboard)/agent-work/page.tsx`)
**Real-time Infrastructure:**
- Split-pane Lovable-style interface
- Activity, Conversations, Thoughts tabs
- Currently mock data with plans for SSE

**Extension:** Connect to `NEXT_PUBLIC_SSE_URL` for live sandbox logs.

---

## 6. Real-Time Update Patterns

### Planned (Not Implemented)
```typescript
// From .env.local
NEXT_PUBLIC_SSE_URL=http://localhost:8000/api/v1/sse
```

**No SSE client exists** - needs implementation for:
- Sandbox creation/destruction events
- Git operation progress (clone, commit, push)
- Agent status updates
- Code execution logs

**Recommendation:** Use EventSource API or React hooks for SSE.

---

## 7. Dependencies (`package.json`)

### Relevant for E2B Integration
- ✅ `axios` (1.13.2) - API client
- ✅ `@tanstack/react-query` (5.90.10) - Server state management
- ✅ `zustand` (5.0.8) - Client state
- ✅ `framer-motion` (12.23.24) - Animations for status transitions

### Missing Dependencies
- ❌ No Git library (backend will handle via E2B)
- ❌ No E2B SDK (backend integration)
- ❌ No SSE/EventSource wrapper

---

## 8. Existing Workflow Patterns

### Task Assignment Flow (Current)
1. User drags task to "In Progress"
2. Check agent availability
3. Show WIP modal if no agents
4. Update task status locally
5. Call `onTaskUpdate(taskId, status, feedback?)`

### Agent Status Transitions
```
idle → thinking → working → completed/error
```

**Extension for E2B:**
```
idle → initializing → cloning → working → committing → pushing → completed/error
          ↓             ↓          ↓           ↓          ↓
     Create sandbox  Clone repo  Execute   Commit    Push & PR
```

---

## 9. Extension Points Summary

### Backend (To Build)
1. **E2B Sandbox Service**
   - Create/destroy sandboxes per agent
   - Execute commands in sandbox
   - File upload/download
   - Lifecycle management

2. **Git Operations Service**
   - Clone repo into sandbox
   - Create task branches
   - Commit with conventional commits
   - Push to GitHub
   - Create PR via GitHub API

3. **SSE Event Stream**
   - Broadcast sandbox status
   - Stream execution logs
   - Send git operation progress
   - Agent status updates

4. **API Endpoints**
   ```
   POST /agents/{id}/start-task
   POST /agents/{id}/sandbox/create
   POST /agents/{id}/git/clone
   POST /agents/{id}/git/commit
   POST /agents/{id}/git/push
   POST /agents/{id}/pull-request
   DELETE /agents/{id}/sandbox
   ```

### Frontend (To Extend)
1. **Type Extensions**
   - Add E2B fields to Agent, Task interfaces
   - Create GitContext, SandboxLog types

2. **State Management**
   - Create squads store
   - Create sandboxes store
   - SSE connection hook

3. **UI Components**
   - Sandbox status indicator
   - Git operation progress
   - Live terminal logs
   - PR creation confirmation

4. **Real-time Updates**
   - SSE client implementation
   - Event handling for sandbox lifecycle
   - Live log streaming to Agent Work page

---

## Unresolved Questions

1. **Backend Stack:** Python (FastAPI) or Node.js (NestJS/Express)?
2. **Database:** PostgreSQL for task/agent persistence?
3. **Repository Config:** Where stored? (env var, DB, per-squad setting?)
4. **GitHub Auth:** App vs PAT? How to store securely?
5. **E2B Pricing:** Which tier? Concurrent sandbox limits?
6. **Error Recovery:** Sandbox crash handling? Git operation failures?
7. **Cleanup Strategy:** When to destroy sandboxes? (immediate after task or keep alive?)
8. **Multi-repo:** Support multiple repos per squad?
