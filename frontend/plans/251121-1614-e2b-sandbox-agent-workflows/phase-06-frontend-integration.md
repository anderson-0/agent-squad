# Phase 06 - Frontend Integration

**Date:** 2025-11-21
**Priority:** P0 (Critical)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:**
  - [Phase 01 - Backend Foundation](./phase-01-backend-foundation.md)
  - [Phase 05 - SSE Real-Time Updates](./phase-05-sse-realtime-updates.md)
- **Related Docs:**
  - [Scout Report](./scout/scout-01-architecture.md)
  - [Design Guidelines](../../docs/design-guidelines.md)

## Overview

Connect Next.js frontend to FastAPI backend. Replace mock data with real API calls. Implement SSE client for real-time updates. Update TypeScript types for E2B/Git fields. Create state management stores.

**Key Changes:**
- Extend Agent, Task interfaces
- Create Zustand stores (squads, sandboxes)
- Implement API client methods
- Connect EventSource for SSE
- Update KanbanBoard to trigger backend operations

## Key Insights

From scout report:
- API client already configured (`lib/api/client.ts`)
- Axios instance points to `localhost:8000/api/v1`
- Auto-refresh on 401 implemented
- No state management beyond auth store
- KanbanBoard has `onTaskUpdate` ready for integration

## Requirements

### Functional
- Fetch squads/agents/tasks from backend API
- Trigger sandbox creation on task assignment
- Update task status via API
- Display sandbox status in real-time
- Show git operation progress
- Display PR URLs when created
- Handle API errors gracefully
- Reconnect SSE on disconnect

### Non-Functional
- API response handling <200ms
- Optimistic UI updates
- Loading states for all operations
- Error toasts for failures
- SSE reconnection <5 seconds
- Type-safe API calls

## Architecture

### State Flow

```
User Action → Optimistic Update → API Call → SSE Event → Final Update
     ↓              ↓                  ↓          ↓            ↓
(drag task)   (update UI)      (backend creates) (status) (confirm UI)
                                     sandbox
```

### Store Architecture

```typescript
// lib/store/squads.ts
interface SquadsStore {
  squads: Squad[];
  selectedSquad: Squad | null;
  isLoading: boolean;
  error: string | null;

  fetchSquads: () => Promise<void>;
  selectSquad: (id: string) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<void>;
  assignTask: (taskId: string, agentId: string) => Promise<void>;
}

// lib/store/sandboxes.ts
interface SandboxesStore {
  sandboxes: Record<string, Sandbox>;
  isCreating: Record<string, boolean>;

  createSandbox: (agentId: string, taskId: string) => Promise<string>;
  destroySandbox: (sandboxId: string) => Promise<void>;
  updateSandboxStatus: (sandboxId: string, status: string) => void;
}
```

## Related Code Files

### New Files to Create
- `lib/store/squads.ts` - Squad/agent/task state management
- `lib/store/sandboxes.ts` - Sandbox state management
- `lib/hooks/useSSE.ts` - SSE connection hook
- `lib/api/squads.ts` - Squad API methods
- `lib/api/sandboxes.ts` - Sandbox API methods
- `lib/api/git.ts` - Git operation API methods
- `types/sandbox.ts` - Sandbox TypeScript types
- `types/git.ts` - Git operation types

### Files to Modify
- `types/squad.ts` - Extend Agent, Task interfaces
- `components/squads/KanbanBoard.tsx` - Connect to API
- `app/(dashboard)/squads/[id]/page.tsx` - Replace mock data
- `app/(dashboard)/agent-work/page.tsx` - Connect to SSE
- `lib/api/client.ts` - Add type exports

## Implementation Steps

1. **Extend TypeScript Types**
   - Add to Agent interface: `sandbox_id?: string`, `git_context?: GitContext`
   - Add to Task interface: `git_branch?: string`, `pull_request_url?: string`, `commit_history?: string[]`
   - Create Sandbox interface: `id, agent_id, task_id, status, repo_url, branch_name, created_at`
   - Create GitOperation interface: `id, operation_type, status, message, progress`

2. **Create Sandbox Types**
   - Define SandboxStatus enum: creating, running, stopped, error
   - Define GitContext interface: repo_url, branch, last_commit_sha
   - Define SSEEvent types for all event types from Phase 05

3. **Create Squads Store**
   - Implement fetchSquads (GET /api/v1/squads)
   - Implement updateTask (PATCH /api/v1/tasks/{id})
   - Implement assignTask (POST /api/v1/tasks/{id}/assign)
   - Add error handling and loading states
   - Persist selected squad ID

4. **Create Sandboxes Store**
   - Implement createSandbox (POST /api/v1/sandboxes)
   - Implement destroySandbox (DELETE /api/v1/sandboxes/{id})
   - Implement updateSandboxStatus (local state update from SSE)
   - Track creating state per agent

5. **Create API Client Methods**
   - `lib/api/squads.ts`: getSquads, getSquad, updateTask, assignTask
   - `lib/api/sandboxes.ts`: createSandbox, getSandbox, executeSandboxCommand, destroySandbox
   - `lib/api/git.ts`: cloneRepo, createBranch, commitChanges, pushBranch
   - All methods return typed responses

6. **Implement SSE Hook**
   - Create useSSE(agentId) hook
   - Connect to `NEXT_PUBLIC_SSE_URL`
   - Handle sandbox_status, git_operation, command_output, pr_created events
   - Auto-reconnect on disconnect (exponential backoff: 1s, 2s, 4s, 8s, max 30s)
   - Update stores on events

7. **Update KanbanBoard Component**
   - Replace handleTaskUpdate with API call
   - Trigger createSandbox when task moves to "In Progress"
   - Show loading spinner during assignment
   - Display error toast if assignment fails
   - Update local state optimistically, rollback on error

8. **Update Squad Detail Page**
   - Replace mock data with squads store
   - Call fetchSquads on mount
   - Show loading skeleton while fetching
   - Handle errors with error boundary or message

9. **Update Agent Work Page**
   - Connect to SSE via useSSE hook
   - Display live command outputs in terminal tab
   - Show git operation progress bars
   - Display PR links when created
   - Handle SSE connection errors

10. **Error Handling**
    - Implement axios interceptors for global errors
    - Show toast notifications for API errors
    - Retry logic for transient failures
    - Fallback UI for critical errors

11. **Loading States**
    - Skeleton loaders for squads list
    - Loading spinners for task updates
    - Progress indicators for sandbox creation
    - Disabled buttons during operations

12. **Testing**
    - Test API integration with backend
    - Test SSE connection and events
    - Test optimistic updates and rollbacks
    - Test error scenarios

## Todo List

### P0 - Critical

- [ ] Extend Agent interface with sandbox_id, git_context
- [ ] Extend Task interface with git_branch, pull_request_url
- [ ] Create types/sandbox.ts with Sandbox interface
- [ ] Create types/git.ts with GitOperation interface
- [ ] Create lib/store/squads.ts with Zustand store
- [ ] Implement fetchSquads, updateTask, assignTask in store
- [ ] Create lib/store/sandboxes.ts with Zustand store
- [ ] Implement createSandbox, destroySandbox in store
- [ ] Create lib/api/squads.ts with API methods
- [ ] Create lib/api/sandboxes.ts with API methods
- [ ] Create lib/hooks/useSSE.ts with EventSource connection
- [ ] Handle SSE events and update stores
- [ ] Update KanbanBoard to call assignTask on task drop
- [ ] Trigger createSandbox when task assigned to agent
- [ ] Update Squad Detail page to use squads store
- [ ] Update Agent Work page to connect to SSE
- [ ] Test end-to-end: drag task → sandbox created → SSE updates

### P1 - Important

- [ ] Create lib/api/git.ts with git operation methods
- [ ] Add optimistic updates for task status changes
- [ ] Implement SSE reconnection logic with backoff
- [ ] Add loading skeletons for data fetching
- [ ] Add error toasts for API failures
- [ ] Handle 401 errors with token refresh
- [ ] Add retry logic for failed API calls
- [ ] Display PR URL in task card when created
- [ ] Show git operation progress in Agent Work page
- [ ] Test SSE reconnection after network interruption

### P2 - Nice to Have

- [ ] Add request caching with React Query
- [ ] Implement infinite scroll for tasks list
- [ ] Add websocket fallback if SSE fails
- [ ] Create debug panel for SSE events
- [ ] Add API call metrics (timing, success rate)
- [ ] Implement offline mode detection
- [ ] Add optimistic UI animations (Framer Motion)

## Success Criteria

- [ ] Squads/agents/tasks loaded from backend API
- [ ] Task assignment triggers sandbox creation
- [ ] Sandbox status updates in real-time via SSE
- [ ] Git operations visible in Agent Work page
- [ ] PR URLs displayed when created
- [ ] Error messages shown for API failures
- [ ] SSE reconnects automatically after disconnect
- [ ] No mock data remaining in production code
- [ ] All API calls are type-safe

## Risk Assessment

**High Risks:**
- Backend API not ready (Phase 01 incomplete)
- SSE connection stability issues
- Type mismatches between frontend/backend
- Race conditions in optimistic updates

**Medium Risks:**
- Network latency affecting UX
- Memory leaks from unclosed SSE connections
- Store state inconsistencies

**Mitigation:**
- Ensure Phase 01 complete before starting
- Implement heartbeat monitoring for SSE
- Use shared Pydantic/TypeScript type generation (optional)
- Use Zustand's immer middleware for safe updates
- Add timeout limits for all API calls
- Cleanup SSE connections in useEffect cleanup
- Test store state with Zustand devtools

## Security Considerations

- **Token Storage:** Use HTTP-only cookies or localStorage (secure)
- **CORS:** Verify backend allows frontend origin
- **XSS Prevention:** Sanitize SSE event data before rendering
- **CSRF:** Use CSRF tokens for state-changing operations
- **Input Validation:** Validate user inputs before API calls
- **Error Messages:** Don't leak sensitive info in error toasts

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 40 min | Type generation, store setup, API methods |
| Senior Dev | 4-5 hrs | State management, SSE integration |
| Junior Dev | 10-12 hrs | React patterns, async state, testing |

**Complexity:** Medium (state management, async operations)

## Next Steps

After completion:
- [Phase 07 - UI Enhancements](./phase-07-ui-enhancements.md) - Polish UI with animations
- [Phase 08 - Testing & Deployment](./phase-08-testing-deployment.md) - E2E tests, deployment

## Unresolved Questions

1. **State Persistence:** Persist sandbox state to localStorage?
2. **SSE Auth:** Send JWT token in SSE URL query params or headers? (EventSource doesn't support headers)
3. **Error Retry:** How many retries before showing error to user? (3 attempts?)
4. **Optimistic UI:** Rollback strategy if API call fails after optimistic update?
5. **Store Structure:** Single store for all data or separate stores per domain?
6. **React Query:** Use React Query instead of Zustand for server state?
7. **Type Generation:** Use openapi-typescript to auto-generate types from FastAPI?
