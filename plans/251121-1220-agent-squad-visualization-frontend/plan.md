# Agent Squad Visualization Frontend - Implementation Plan

**Plan Created**: 2025-11-21
**Status**: Planning
**Complexity**: Complex
**Estimated Duration**: 3-4 weeks

---

## Overview

Build a modern, mobile-first agent visualization frontend using Next.js 16 + React 19 in a monorepo structure. Provides squad management, task tracking, live agent activity monitoring, and conversation threading. Key features include Lovable-style agent work visualization, SSE-based real-time updates, and end-user focused UX (only top-level agents visible).

---

## Phases

| Phase | Description | Status | Priority |
|-------|-------------|--------|----------|
| [01](./phase-01-foundation-setup.md) | Foundation & Setup | Pending | P0 |
| [02](./phase-02-squad-task-visualization.md) | Squad & Task Visualization | Pending | P0 |
| [03](./phase-03-agent-work-visualization.md) | Agent Work Visualization (Lovable-style) | Pending | P0 |
| [04](./phase-04-conversation-system.md) | Conversation System & Threading | Pending | P0 |
| [05](./phase-05-polish-performance.md) | Polish & Performance | Pending | P1 |

---

## Tech Stack

### Core Framework
- **Next.js 16** - React Server Components, Streaming, App Router (latest stable)
- **React 19** - Enhanced Suspense, concurrent rendering
- **TypeScript** - Strict mode, full type safety
- **Monorepo** - Frontend in `/frontend` directory alongside backend

### Real-Time Communication
- **SSE (EventSource)** - Server-Sent Events via `/api/v1/sse` (primary)
- **Auto-reconnect** - Native EventSource reconnection + exponential backoff
- **Fallback** - Polling for environments where SSE blocked

### State Management
- **TanStack Query v5** - Server state caching, optimistic updates
- **Zustand** - Client state (UI filters, selections)

### UI & Styling
- **shadcn/ui** - Pre-styled dashboard components (Radix UI)
- **Tailwind CSS** - Utility-first styling, mobile-first breakpoints
- **Framer Motion** - 120fps animations, layout transitions
- **Mobile-First** - Design for 375px (iPhone SE) then scale up

### Authentication
- **HTTP-Only Cookies** - Secure token storage (XSS protection)
- **JWT** - Access + refresh token flow
- **CSRF Protection** - Double-submit cookie pattern

### Performance
- **react-window** - Virtualization for large lists
- **Debouncing** - Batch SSE updates (100ms)
- **Optimistic Updates** - Instant UI feedback via TanStack Query

---

## Key Architectural Decisions

### 1. Real-Time Strategy (SSE-First)
- **Primary**: SSE (Server-Sent Events) via EventSource API
- **Fallback**: Polling every 5s for restricted networks
- **Rationale**: Backend already has SSE, unidirectional is sufficient (server → client)
- **User Actions**: REST API (POST/PATCH) for commands
- **Pros**: Simpler, HTTP-based, mobile-friendly, auto-reconnect

### 2. State Management Split
- **Server State**: TanStack Query (agent data, tasks, messages)
- **Client State**: Zustand (view mode, filters, UI toggles)
- **Rationale**: Separate concerns, better caching, optimistic updates

### 3. End-User Only Focus
- **Visibility**: Only Project Manager + Tech Lead visible
- **No Developer Mode**: Internal agents (Backend Dev, QA, etc.) completely hidden
- **Message Filtering**: Backend enforces `visibility: PUBLIC` only
- **Rationale**: Simplified UX, prevent overwhelming non-technical users

### 4. Mobile-First Design
- **Breakpoints**: 375px (mobile) → 768px (tablet) → 1280px (desktop)
- **Touch-Optimized**: Large tap targets (44px min), swipe gestures
- **Progressive Enhancement**: Core features work on mobile, enhanced on desktop
- **Rationale**: Users will monitor agents on-the-go

### 5. Conversation Threading
- **Agent-to-agent**: Filtered out (internal only)
- **User-to-agent**: Direct chat with PM/Tech Lead
- **Format**: Chat interface (mobile) → side panel (desktop)
- **Rationale**: End users don't need to see internal agent coordination

---

## Monorepo Structure

```
agent-squad/
├── backend/              # Existing FastAPI backend
│   ├── api/
│   ├── agents/
│   ├── models/
│   └── services/
├── frontend/             # NEW - Next.js 16 app
│   ├── app/             # App router pages
│   ├── components/      # React components
│   ├── lib/             # Utils, API client, stores
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript types
│   └── public/          # Static assets
├── docs/                # Shared documentation
└── scripts/             # Build/deploy scripts
```

---

## Decisions Made (2025-11-21)

✅ **Monorepo**: Frontend in `/frontend` directory
✅ **Users**: End users only (no developer/admin modes)
✅ **Design**: Mobile-first (375px → 768px → 1280px)
✅ **Auth**: HTTP-only cookies for security
✅ **Real-Time**: SSE via EventSource (backend already has it)
✅ **Framework**: Next.js 16 (latest stable)

---

## Success Metrics

### Performance
- **LCP**: < 1.5s (Largest Contentful Paint)
- **FID**: < 100ms (First Input Delay)
- **Real-time latency**: < 200ms for agent updates
- **Bundle size**: < 300KB (gzipped)

### User Experience
- **Agent status updates**: < 1s visible delay
- **Conversation threading**: Clear hierarchy, no confusion
- **Task board updates**: Instant optimistic updates
- **Mobile responsive**: 100% features on tablet/mobile

### Technical
- **Type safety**: 100% TypeScript coverage
- **Test coverage**: > 80% for critical paths
- **Accessibility**: WCAG 2.1 AA compliance
- **Error handling**: Graceful degradation + retry logic

---

## Dependencies

### External Services
- **Backend API**: `http://localhost:8000/api/v1`
- **SSE Endpoints**: `/api/v1/sse/execution/{id}`, `/api/v1/sse/squad/{id}`
- **NATS**: Backend message bus (internal, not exposed)
- **PostgreSQL**: Backend database (not directly accessed)

### Authentication
- **JWT tokens**: Access + refresh tokens
- **Storage**: HTTP-only cookies or localStorage
- **Endpoints**: `/api/v1/auth/login`, `/api/v1/auth/refresh`

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Real-time scale (100+ updates/sec) | High | Debouncing, batching, virtualization |
| Browser compatibility (SSE/WebSocket) | Medium | Auto-fallback, feature detection |
| Complex conversation threading | High | Incremental rollout, user testing |
| Type safety with dynamic messages | Medium | Zod validation, runtime checks |
| Mobile performance | Medium | Progressive enhancement, lazy loading |

---

## Timeline Estimates

### By Executor

| Phase | Claude | Senior Dev | Junior Dev |
|-------|--------|------------|-----------|
| Phase 1 | 2 hrs | 1 day | 2-3 days |
| Phase 2 | 3 hrs | 2 days | 4-5 days |
| Phase 3 | 4 hrs | 3 days | 5-7 days |
| Phase 4 | 5 hrs | 3 days | 5-7 days |
| Phase 5 | 2 hrs | 2 days | 3-4 days |
| **Total** | **16 hrs** | **11 days** | **19-26 days** |

**Complexity**: Complex (multi-agent real-time system with advanced UX)

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Start Phase 1**: Foundation & Setup
3. **Set up repo**: Create `frontend/` directory in agent-squad repo
4. **Initialize project**: `bun create next-app@latest frontend --typescript --tailwind --app`
5. **Install dependencies**: shadcn/ui, Socket.io, TanStack Query, Zustand
6. **Begin implementation**: Follow phase-01-foundation-setup.md

---

## Unresolved Questions

1. **WebSocket server**: Will backend support Socket.io or only SSE?
2. **Authentication**: HTTP-only cookies or localStorage for tokens?
3. **Mobile priority**: Should we optimize for mobile-first or desktop-first?
4. **Agent data schema**: TypeScript types need to match backend Pydantic schemas
5. **Conversation UI**: How deep should conversation threads nest? (max 3 levels?)
6. **Performance targets**: Acceptable latency for 50+ agents updating simultaneously?
7. **Deployment**: Separate frontend repo or monorepo with backend?
