# Tech Stack Research: Real-Time Agent Visualization Frontend

**Research Date**: 2025-11-21
**Focus**: Optimal technologies for real-time agent activity visualization with Next.js 15 + React 19

---

## 1. Real-Time Communication

### Technology Comparison

| Protocol | Latency | Overhead | Bidirectional | Auto-Reconnect | Use Case |
|----------|---------|----------|---------------|----------------|----------|
| **WebSocket** | Lowest | Minimal after handshake | ✅ Yes | Manual | Interactive, high-frequency updates |
| **SSE** | Low | Low (HTTP) | ❌ No (server→client) | ✅ Yes | One-way updates, mobile-friendly |
| **Long Polling** | Highest | High (repeated requests) | ❌ No | Manual | Legacy compatibility only |

### **Recommendation: WebSocket with SSE Fallback**

**Primary: WebSocket**
- Full-duplex needed for agent commands + status updates
- Minimal latency for hundreds of concurrent agent updates
- Native browser support, no polling overhead

**Fallback: SSE**
- Automatic reconnection for flaky connections
- Better mobile network handling
- Simpler for read-only dashboards

### Library Recommendations

**Socket.io** (Recommended for MVP)
```typescript
// Client-side
import { io } from 'socket.io-client';
const socket = io('ws://localhost:3000', {
  transports: ['websocket', 'polling'] // Auto fallback
});

socket.on('agent:update', (data) => {
  // Handle real-time agent state updates
});
```

**Advantages:**
- Auto-reconnection + fallback transports
- Room-based broadcasting (per-agent channels)
- TypeScript support with zod schemas
- Production-tested at scale

**Alternative: Native WebSocket + EventSource (SSE)**
```typescript
// For simpler needs, no library dependency
const ws = new WebSocket('ws://localhost:3000');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Process update
};
```

**Avoid:** Pusher/Ably (vendor lock-in, cost at scale)

---

## 2. State Management

### **Hybrid Approach: TanStack Query + Zustand**

Modern consensus (2025): **Separate server state from client state**

#### Server State → **TanStack Query v5**
```typescript
// Real-time agent data with optimistic updates
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const { data: agents } = useQuery({
  queryKey: ['agents'],
  queryFn: fetchAgents,
  refetchInterval: false, // Driven by WebSocket
});

// WebSocket integration
useEffect(() => {
  socket.on('agent:update', (update) => {
    queryClient.setQueryData(['agents', update.id], (old) => ({
      ...old,
      ...update
    }));
  });
}, []);
```

**Why TanStack Query:**
- Built-in caching + deduplication
- Optimistic updates for agent commands
- Suspense streaming with Next.js 15 RSC
- Background sync when tab refocuses

#### Client State → **Zustand**
```typescript
// UI state: filters, selections, view modes
import { create } from 'zustand';

const useAgentStore = create((set) => ({
  selectedAgentId: null,
  viewMode: 'grid',
  filters: [],
  setSelectedAgent: (id) => set({ selectedAgentId: id }),
  toggleFilter: (filter) => set((state) => ({
    filters: state.filters.includes(filter)
      ? state.filters.filter(f => f !== filter)
      : [...state.filters, filter]
  }))
}));
```

**Why Zustand over Jotai:**
- Simpler mental model for team collaboration
- Centralized store easier to debug
- Less re-render optimization needed vs Jotai's atomic approach
- Default choice for 2025 (TanStack Query + Zustand + nuqs)

**When to use Jotai:** If you need fine-grained reactivity with hundreds of independent agent widgets that update independently (atomic subscriptions minimize re-renders).

---

## 3. Next.js 15 + React 19 Architecture

### **RSC (React Server Components) + Streaming**

**Key Patterns:**

```typescript
// app/agents/page.tsx (Server Component)
import { Suspense } from 'react';

export default async function AgentsPage() {
  // Initial server-side data fetch
  const initialAgents = await fetchAgents();

  return (
    <Suspense fallback={<AgentsSkeleton />}>
      <AgentsDashboard initialData={initialAgents} />
    </Suspense>
  );
}
```

**Performance Benefits:**
- 50% smaller JS bundles (server components don't ship to client)
- 1.2s LCP (Largest Contentful Paint) with streaming
- Immediate HTML shell, progressive enhancement for dynamic data

**Real-Time Integration:**
```typescript
// components/AgentsDashboard.tsx (Client Component)
'use client';

export function AgentsDashboard({ initialData }) {
  // Hydrate TanStack Query with server data
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    initialData, // SSR data
  });

  // Connect WebSocket for live updates
  useRealtimeAgents();

  return <AgentGrid agents={agents} />;
}
```

**Critical:** Mark client components with `'use client'` only where needed (WebSocket, Zustand, animations). Keep as much as possible in RSC for performance.

---

## 4. Component Libraries

### **Recommendation: shadcn/ui**

```bash
npx shadcn@latest init
npx shadcn@latest add card badge chart
```

**Why shadcn/ui for dashboards:**
- Built on Radix UI primitives (accessibility + unstyled foundation)
- Pre-styled for SaaS/dashboard UIs (saves weeks of design)
- Copy-paste components (no runtime dependency, full control)
- Dashboard templates available (analytics, admin panels)
- Tailwind CSS integration (rapid iteration)

**Example: Agent Status Card**
```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

<Card>
  <CardHeader>
    <CardTitle>{agent.name}</CardTitle>
    <Badge variant={agent.status === 'active' ? 'success' : 'secondary'}>
      {agent.status}
    </Badge>
  </CardHeader>
  <CardContent>
    <AgentMetrics data={agent.metrics} />
  </CardContent>
</Card>
```

**When to use Radix UI directly:** If you need 100% custom design system with no default styles.

**Avoid:** Headless UI (better for Vue/Alpine), MUI (too heavy for real-time UIs).

---

## 5. Animation & Transitions

### **Recommendation: Framer Motion**

**Why Framer Motion for agent visualization:**
- Hybrid engine: native browser animations (120fps) + JS flexibility
- Layout animations (agent cards reordering)
- Gesture support (drag agents, swipe between views)
- SSR-compatible with Next.js
- Handles hundreds of elements efficiently (doesn't trigger React renders)

**Real-Time Animation Example:**
```typescript
import { motion, AnimatePresence } from 'framer-motion';

<AnimatePresence>
  {agents.map(agent => (
    <motion.div
      key={agent.id}
      layout // Smooth reordering when agents change state
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.2 }}
    >
      <AgentCard agent={agent} />
    </motion.div>
  ))}
</AnimatePresence>
```

**Performance Pattern: Motion Values**
```typescript
import { useMotionValue, useTransform } from 'framer-motion';

// Animate without React re-renders
const activity = useMotionValue(agent.activityLevel);
const scale = useTransform(activity, [0, 100], [0.95, 1.05]);

<motion.div style={{ scale }}>
  {/* Agent card pulses with activity */}
</motion.div>
```

**React Spring Alternative:** Better for physics-based animations (spring dynamics), but Framer Motion's hybrid engine + layout animations are superior for dashboard UIs.

---

## 6. Performance Optimization

### Handling Hundreds of Real-Time Updates

#### **A. Virtualization**
```typescript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={800}
  itemCount={agents.length}
  itemSize={120}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <AgentCard agent={agents[index]} />
    </div>
  )}
</FixedSizeList>
```

#### **B. Debouncing & Batching**
```typescript
// Batch WebSocket updates every 100ms
import { debounce } from 'lodash-es';

const batchedUpdate = debounce((updates) => {
  queryClient.setQueriesData(['agents'], (old) =>
    applyBatchUpdates(old, updates)
  );
}, 100);

socket.on('agent:update', (update) => {
  updateQueue.push(update);
  batchedUpdate(updateQueue);
});
```

#### **C. Memoization**
```typescript
import { memo } from 'react';

const AgentCard = memo(({ agent }) => {
  // Only re-render if agent data changed
  return <Card>{/* ... */}</Card>;
}, (prev, next) => prev.agent.id === next.agent.id && prev.agent.status === next.agent.status);
```

#### **D. Web Workers (Advanced)**
```typescript
// Offload heavy computation to worker thread
const worker = new Worker('/workers/agent-processor.js');
worker.postMessage({ agents: rawData });
worker.onmessage = (e) => {
  setProcessedAgents(e.data);
};
```

---

## Recommended Tech Stack Summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Framework** | Next.js 15 + React 19 | RSC, streaming, 50% smaller bundles |
| **Real-Time** | Socket.io (WebSocket) | Auto-reconnect, room-based, production-ready |
| **Server State** | TanStack Query v5 | Caching, optimistic updates, Suspense |
| **Client State** | Zustand | Simple, centralized, team-friendly |
| **UI Components** | shadcn/ui (Radix UI) | Pre-styled dashboard components, accessible |
| **Animation** | Framer Motion | 120fps, layout animations, no re-renders |
| **Virtualization** | react-window | Handle 1000+ agent list efficiently |
| **Styling** | Tailwind CSS | Rapid iteration, built into shadcn/ui |

---

## Implementation Priority

1. **P0**: Socket.io + TanStack Query (real-time foundation)
2. **P0**: Zustand (UI state management)
3. **P1**: shadcn/ui components (dashboard UI)
4. **P1**: Framer Motion (agent activity animations)
5. **P2**: react-window (if >100 agents)
6. **P2**: Batching/debouncing (performance tuning)

---

## Unresolved Questions

1. **Backend WebSocket Server**: Node.js/Bun vs. Go/Rust for socket server?
2. **Agent Data Schema**: Need TypeScript types for agent state (zod validation)?
3. **Authentication**: How to secure WebSocket connections (JWT in handshake)?
4. **Scaling**: Single WebSocket server vs. clustered with Redis pub/sub?
