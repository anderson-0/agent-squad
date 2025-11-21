# Implementation Decisions - Agent Squad Visualization Frontend

**Date**: 2025-11-21
**Status**: Ready for Implementation

---

## ✅ Decisions Finalized

### 1. **Deployment Structure**
- **Decision**: Monorepo
- **Implementation**: Frontend in `/frontend` directory alongside existing `/backend`
- **Rationale**: Easier code sharing, single repository, unified deployments

### 2. **User Audience**
- **Decision**: End users only
- **Visibility**: Only Project Manager + Tech Lead agents
- **No Developer Mode**: Internal agents (Backend Dev, QA, DevOps, etc.) completely hidden
- **Rationale**: Simplified UX, prevent overwhelming non-technical users

### 3. **Design Priority**
- **Decision**: Mobile-first
- **Breakpoints**:
  - Mobile: 375px (iPhone SE)
  - Tablet: 768px (iPad)
  - Desktop: 1280px+
- **Touch-Optimized**: 44px minimum tap targets, swipe gestures
- **Rationale**: Users will monitor agents on mobile devices

### 4. **Authentication**
- **Decision**: HTTP-only cookies
- **Implementation**:
  - Access token: 30min expiry
  - Refresh token: 7 days expiry
  - CSRF protection via double-submit cookie
- **Rationale**: XSS protection, more secure than localStorage

### 5. **Real-Time Communication** ⭐
- **Decision**: SSE (Server-Sent Events) - Primary
- **Fallback**: Polling every 5s for restricted networks
- **Backend**: Already implemented at `/api/v1/sse`
- **Rationale**:
  - ✅ Backend already has SSE working
  - ✅ Unidirectional (server → client) sufficient for this use case
  - ✅ HTTP-based, mobile-friendly, better battery life
  - ✅ Auto-reconnect built into EventSource API
  - ✅ Simpler than WebSocket (no separate server)
  - ✅ Works through proxies/firewalls

### 6. **Framework Version**
- **Decision**: Next.js 16 (just released)
- **React**: React 19
- **Rationale**: Latest stable, better performance, new features

---

## 🔄 WebSocket vs SSE Analysis

### SSE (Server-Sent Events) - ✅ RECOMMENDED

**Pros**:
- Backend already has `/api/v1/sse` endpoints working
- Simpler architecture (HTTP-based, no separate server)
- Auto-reconnect built into EventSource API
- Mobile-friendly (lighter, better battery)
- Works through proxies/firewalls
- Sufficient for one-way updates (server → client)

**Cons**:
- One-directional only (server → client)
- No native binary support (JSON only)

**Use Cases Covered**:
- ✅ Agent status updates (ACTIVE, IDLE, THINKING)
- ✅ Task progress (0-100%)
- ✅ New messages from PM/Tech Lead
- ✅ Task state changes (PENDING → COMPLETED)
- ✅ Real-time notifications

**User Actions** (client → server):
- Via REST API: POST/PATCH/DELETE
- Examples: Send message, create task, update status

---

### WebSocket - ❌ NOT NEEDED (Yet)

**When WebSocket Would Be Better**:
- Real-time collaborative editing (multiple users, same doc)
- Low-latency bidirectional gaming
- Live cursors/presence (like Figma multiplayer)
- P2P communication between clients

**Current Project**:
- No collaborative editing needed
- Single user viewing their squads
- User actions → REST API → Backend processes → SSE updates all clients
- **Conclusion**: SSE is sufficient, WebSocket would be over-engineering

---

## 🏗️ Updated Architecture

### Real-Time Flow

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Next.js 16)                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. User Action (e.g., "Create Task")              │
│     └─> POST /api/v1/task-executions               │
│         └─> Backend creates task                   │
│             └─> Backend emits SSE event            │
│                                                     │
│  2. SSE Connection (EventSource)                   │
│     └─> GET /api/v1/sse/executions/{id}           │
│         └─> Receives: task_spawned, status_update │
│             └─> TanStack Query cache invalidation  │
│                 └─> React re-renders UI            │
│                                                     │
│  3. Fallback (if SSE fails)                        │
│     └─> Poll GET /api/v1/task-executions/{id}     │
│         └─> Every 5 seconds                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Component Architecture

```
app/
├── (auth)/              # Auth pages (login, register)
│   ├── login/
│   └── register/
├── (dashboard)/         # Protected dashboard routes
│   ├── squads/         # Squad list/detail
│   ├── tasks/          # Task board (Kanban)
│   ├── agent-work/     # Lovable-style work view
│   └── chat/           # User ↔ PM/Tech Lead
└── api/                # API route handlers (auth)

components/
├── squads/             # SquadCard, SquadGrid
├── tasks/              # TaskBoard, TaskCard, KanbanColumn
├── agents/             # AgentCard, AgentActivity, AgentStatus
├── chat/               # ChatPanel, MessageThread, ChatInput
├── work-view/          # FileTree, CodeViewer, Terminal (Lovable-style)
└── ui/                 # shadcn/ui components

lib/
├── api/                # API client (fetch + auth)
├── sse/                # SSE service (EventSource wrapper)
├── stores/             # Zustand stores (client state)
└── utils/              # Helpers, formatters

hooks/
├── useSSE.ts           # SSE hook with auto-reconnect
├── useSquads.ts        # TanStack Query hooks
├── useTasks.ts
└── useAuth.ts
```

---

## 📱 Mobile-First Design Principles

### Breakpoints

```typescript
// tailwind.config.ts
const screens = {
  'xs': '375px',   // iPhone SE (smallest)
  'sm': '640px',   // Mobile landscape
  'md': '768px',   // Tablets
  'lg': '1024px',  // Small desktop
  'xl': '1280px',  // Desktop
  '2xl': '1536px', // Large desktop
}
```

### Touch Targets

- **Minimum**: 44px × 44px (Apple HIG, WCAG)
- **Comfortable**: 48px × 48px (Material Design)
- **Spacing**: 8px minimum between targets

### Progressive Enhancement

**Mobile (375px)**:
- Stack vertically
- Bottom sheet for details
- Swipe gestures (dismiss, actions)
- Hamburger menu

**Tablet (768px)**:
- Side-by-side layouts
- Floating panels
- Hover states enabled

**Desktop (1280px)**:
- Multi-column layouts
- Persistent sidebars
- Keyboard shortcuts

---

## 🔐 Security Implementation

### HTTP-Only Cookies

```typescript
// Set-Cookie headers (backend)
Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Max-Age=1800
Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
Set-Cookie: csrf_token=<random>; Secure; SameSite=Strict; Max-Age=1800
```

### CSRF Protection

```typescript
// Frontend sends CSRF token in header
headers: {
  'X-CSRF-Token': getCookie('csrf_token')
}
```

### XSS Prevention

- `HttpOnly` cookies (JavaScript can't access)
- Sanitize all user input
- CSP headers (Content-Security-Policy)

---

## 📊 Success Metrics

### Performance (Mobile-First)

- **LCP**: < 2.5s on 4G (< 1.5s on WiFi)
- **FID**: < 100ms
- **CLS**: < 0.1
- **TTI**: < 5s on 4G
- **Bundle**: < 200KB initial (< 300KB total)

### Real-Time

- **SSE Latency**: < 200ms from backend event to UI update
- **Reconnect**: < 2s after disconnect
- **Fallback**: Poll every 5s if SSE fails

### UX

- **Touch Targets**: 100% ≥ 44px
- **Accessibility**: WCAG 2.1 AA
- **Offline**: Graceful degradation
- **Loading**: Skeleton screens < 100ms

---

## 🚀 Next Steps

1. ✅ **Plan approved** - All decisions finalized
2. **Initialize project**: Create `/frontend` directory with Next.js 16
3. **Phase 1**: Foundation (auth, API client, SSE service)
4. **Phase 2**: Squad & task visualization
5. **Phase 3**: Lovable-style agent work view
6. **Phase 4**: Chat with PM/Tech Lead
7. **Phase 5**: Polish & performance

---

## ❓ Remaining Open Questions

None! All decisions have been made. Ready to implement.

---

**Updated**: 2025-11-21
**Ready for**: `/code` command to start Phase 1
