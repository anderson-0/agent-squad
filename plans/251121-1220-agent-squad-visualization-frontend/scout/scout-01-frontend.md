# Frontend Architecture

## Discovery Summary

IMPORTANT: This project does NOT have a traditional frontend directory. Based on code analysis:
- Frontend code references found in backend code (imports like `@/lib/store/auth`, `@/lib/api/squads`)
- These are likely from a REMOVED or SEPARATE frontend repository
- Current repository is BACKEND-ONLY

## Structure

### Backend-Only Architecture
```
agent-squad/
├── backend/           # Main backend codebase
│   ├── api/          # REST API endpoints
│   ├── agents/       # Agent implementations
│   ├── core/         # Core configuration
│   ├── models/       # Database models
│   ├── services/     # Business logic services
│   └── main.py       # FastAPI entry point
├── alembic/          # Database migrations
└── docs/             # Documentation
```

### No Frontend Directory Found
- Searched: `frontend/`, `web/`, `app/`, `src/`
- Result: No frontend directories exist
- Conclusion: Frontend must be separate repo OR removed

## Components

### Traces of Frontend Code (Likely Removed)
Based on grep analysis, these frontend patterns were referenced:

1. **Pages Structure** (Next.js App Router):
   - `app/(auth)/login/page.tsx`
   - `app/(auth)/register/page.tsx`
   - `app/(dashboard)/page.tsx`
   - `app/(dashboard)/squads/page.tsx`
   - `app/(dashboard)/tasks/page.tsx`
   - `app/(dashboard)/workflows/[executionId]/kanban/page.tsx`

2. **Components**:
   - `components/dashboard/Sidebar.tsx`
   - `components/kanban/KanbanBoard.tsx`
   - `components/kanban/TaskDetailModal.tsx`
   - `components/tasks/CreateTaskDialog.tsx`
   - `components/ui/*` (Radix UI primitives)

3. **Libraries Referenced**:
   - State: Zustand (`@/lib/store/auth`)
   - API: Axios (`@/lib/api/squads`, `@/lib/api/tasks`)
   - UI: Radix UI, Tailwind CSS
   - Forms: React Hook Form, Zod

## State Management

### Backend State (Current)
```python
# Backend manages state via:
1. PostgreSQL Database (persistent state)
2. SQLAlchemy ORM models
3. Pydantic schemas for validation
4. FastAPI dependency injection
```

### Frontend State (Removed/Separate)
From code analysis, frontend used:
```typescript
// Zustand store
import { useAuthStore } from '@/lib/store/auth'

const isAuthenticated = useAuthStore(state => state.isAuthenticated)
```

## Real-time

### Backend Real-time (Current)
```python
# Server-Sent Events (SSE) Implementation
Location: backend/services/sse_service.py
Location: backend/api/v1/endpoints/sse.py

Features:
- Per-execution subscriptions
- Per-squad subscriptions
- Automatic heartbeat (15s)
- Event types:
  * connected
  * message
  * status_update
  * log
  * progress
  * error
  * completed
  * heartbeat

# Usage
GET /api/v1/sse/execution/{execution_id}
GET /api/v1/sse/squad/{squad_id}
GET /api/v1/sse/stats
```

### Frontend Real-time (Removed/Separate)
From KanbanBoard.tsx analysis:
```typescript
// EventSource for SSE
const eventSource = new EventSource(
  `${apiUrl}/api/v1/sse/execution/${executionId}`,
  { withCredentials: true }
)

eventSource.addEventListener('task_spawned', () => {
  loadBoardData()
})

eventSource.addEventListener('task_status_updated', () => {
  loadBoardData()
})

// Fallback to polling if SSE fails
const interval = setInterval(loadBoardData, 5000)
```

## Key Files

### Backend API Files (Actual)
```
/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/sse.py
/home/anderson/Documents/git/anderson-0/agent-squad/backend/services/sse_service.py
/home/anderson/Documents/git/anderson-0/agent-squad/backend/main.py
/home/anderson/Documents/git/anderson-0/agent-squad/backend/core/database.py
```

### Frontend Files (Referenced but Missing)
These files were referenced in code but DO NOT EXIST:
```
frontend/app/layout.tsx
frontend/app/(dashboard)/layout.tsx
frontend/app/(dashboard)/page.tsx
frontend/components/kanban/KanbanBoard.tsx
frontend/lib/store/auth.ts
frontend/lib/api/client.ts
frontend/lib/api/squads.ts
frontend/lib/api/tasks.ts
```

## Recommendations

### For New Frontend Implementation

1. **Create Separate Frontend Repository**
   - Use Next.js 16 (referenced in package.json)
   - React 19 (referenced)
   - TypeScript with strict mode

2. **State Management**
   - Zustand for global state (auth, user)
   - React Query for server state (API data)
   - Local component state with useState/useReducer

3. **API Integration**
   - Axios client with interceptors
   - Base URL: `http://localhost:8000/api/v1`
   - JWT auth via Bearer token
   - Error handling with toast notifications

4. **Real-time Updates**
   - Primary: SSE (EventSource API)
   - Fallback: Polling (5-30 second intervals)
   - Event types: task_spawned, task_status_updated, execution_completed

5. **Components Architecture**
   ```
   frontend/
   ├── app/                    # Next.js App Router
   │   ├── (auth)/            # Auth pages (login, register)
   │   ├── (dashboard)/       # Protected dashboard pages
   │   └── layout.tsx         # Root layout
   ├── components/
   │   ├── dashboard/         # Dashboard-specific components
   │   ├── kanban/            # Kanban board components
   │   ├── tasks/             # Task management components
   │   └── ui/                # Reusable UI primitives
   ├── lib/
   │   ├── api/               # API clients
   │   ├── hooks/             # Custom React hooks
   │   ├── store/             # Zustand stores
   │   └── utils/             # Utility functions
   └── types/                 # TypeScript types
   ```

6. **UI Framework**
   - Radix UI for primitives
   - Tailwind CSS for styling
   - shadcn/ui patterns
   - Lucide React for icons

## Integration Points

### Backend API Endpoints (Available)
```
# Authentication
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh

# Squads
GET /api/v1/squads
POST /api/v1/squads
GET /api/v1/squads/{squad_id}
PUT /api/v1/squads/{squad_id}

# Tasks
GET /api/v1/tasks
POST /api/v1/tasks
GET /api/v1/tasks/{task_id}
PUT /api/v1/tasks/{task_id}

# Executions
GET /api/v1/executions
POST /api/v1/executions
GET /api/v1/executions/{execution_id}

# Real-time
GET /api/v1/sse/execution/{execution_id}
GET /api/v1/sse/squad/{squad_id}
GET /api/v1/sse/stats
```

### SSE Event Flow
```
Backend                     Frontend
   │                           │
   ├─ Execution starts ────────►│ EventSource connects
   │                           │
   ├─ Task spawned ────────────►│ Update UI (add task card)
   │                           │
   ├─ Status update ───────────►│ Update task status badge
   │                           │
   ├─ Log entry ───────────────►│ Append to log viewer
   │                           │
   ├─ Completion ──────────────►│ Show success notification
   │                           │
   └─ Heartbeat (15s) ─────────►│ Keep connection alive
```

## Conclusion

**Current State**: Backend-only repository with NO frontend code

**Next Steps**:
1. Decide: New frontend repo OR add frontend to this repo
2. If adding here: Create `frontend/` directory
3. Implement Next.js 16 + React 19 setup
4. Build API client using existing backend endpoints
5. Implement SSE integration for real-time updates
6. Create Kanban board visualization component

**Architecture Decision**:
- **Monorepo**: Add frontend/ directory here
- **Separate Repos**: Create new repo, deploy separately
- **Recommendation**: Monorepo for easier development, separate deployment
