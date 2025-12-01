# Phase 5: Polish & Performance

**Status**: Pending
**Priority**: P1
**Dependencies**: Phase 1, 2, 3, 4
**Estimated Duration**: Claude (2 hrs) | Senior Dev (2 days) | Junior Dev (3-4 days)

---

## Context

Phase 5 focuses on polish, performance optimization, and production readiness. This includes animations, virtualization, optimistic updates, error handling, testing, and deployment preparation. This phase ensures the application is smooth, fast, and reliable for production use.

**Related Files**:
- Research: `research/researcher-02-tech-stack.md` (performance patterns)
- All previous phases (optimization targets)

---

## Overview

**Goal**: Optimize performance, add polish, and prepare for production deployment.

**Key Deliverables**:
1. Smooth animations and transitions (Framer Motion)
2. Virtualization for large lists (react-window)
3. Optimistic updates for instant feedback
4. Error handling and retry logic
5. Loading states and skeletons
6. Performance monitoring
7. Bundle size optimization
8. Accessibility improvements (WCAG 2.1 AA)
9. Testing (unit, integration, e2e)
10. Deployment configuration

**Dates**:
- Start: TBD (after Phase 4)
- End: TBD
- **Status**: Pending

---

## Key Insights from Research

### From `researcher-02-tech-stack.md`

**Performance Optimization**:
- **Virtualization**: react-window for 1000+ items
- **Debouncing**: Batch WebSocket updates (100ms)
- **Memoization**: React.memo for expensive components
- **Web Workers**: Offload heavy computation

**Animation**:
- **Framer Motion**: 120fps hybrid engine, layout animations
- **Motion Values**: Animate without React re-renders
- **AnimatePresence**: Smooth enter/exit transitions

**Bundle Optimization**:
- **Code Splitting**: Dynamic imports for routes
- **Tree Shaking**: Remove unused code
- **Target**: < 300KB gzipped

---

## Requirements

### Functional Requirements

**FR-5.1**: Smooth animations for all transitions (60fps)
**FR-5.2**: Virtualized lists for 1000+ items
**FR-5.3**: Optimistic updates for user actions
**FR-5.4**: Error boundaries for graceful failures
**FR-5.5**: Retry logic for failed requests
**FR-5.6**: Loading skeletons for all async operations
**FR-5.7**: Toast notifications for success/errors
**FR-5.8**: Keyboard shortcuts for common actions
**FR-5.9**: Accessibility improvements (ARIA labels, focus management)
**FR-5.10**: Performance monitoring dashboard

### Non-Functional Requirements

**NFR-5.1**: LCP < 1.5s (Largest Contentful Paint)
**NFR-5.2**: FID < 100ms (First Input Delay)
**NFR-5.3**: CLS < 0.1 (Cumulative Layout Shift)
**NFR-5.4**: Bundle size < 300KB gzipped
**NFR-5.5**: Real-time latency < 200ms
**NFR-5.6**: WCAG 2.1 AA compliance
**NFR-5.7**: Test coverage > 80% for critical paths

---

## Architecture

### Performance Optimization Strategies

```
1. Code Splitting
   ├─ Route-based splitting (Next.js automatic)
   ├─ Component lazy loading (React.lazy)
   └─ Library chunking (webpack config)

2. Data Optimization
   ├─ TanStack Query caching (dedupe requests)
   ├─ Optimistic updates (instant feedback)
   ├─ Debouncing (batch updates)
   └─ Virtualization (render visible only)

3. Rendering Optimization
   ├─ React.memo (expensive components)
   ├─ useMemo (expensive calculations)
   ├─ useCallback (stable references)
   └─ React Server Components (reduce JS)

4. Network Optimization
   ├─ Prefetching (anticipate navigation)
   ├─ Parallel requests (Promise.all)
   ├─ Request batching (GraphQL-style)
   └─ Service Worker (offline support)

5. Animation Optimization
   ├─ Framer Motion (GPU-accelerated)
   ├─ transform/opacity only (avoid layout)
   ├─ will-change (hint browser)
   └─ requestAnimationFrame (smooth)
```

### Error Handling Architecture

```typescript
Error Boundary (App Level)
    ↓
Error Boundary (Page Level)
    ↓
Error Boundary (Component Level)
    ↓
Try/Catch (Function Level)
    ↓
Error Logging Service (Sentry, etc.)
```

### Monitoring Architecture

```
Performance Monitoring
├─ Web Vitals (LCP, FID, CLS)
├─ Custom Metrics (API latency, SSE latency)
├─ Error Tracking (Sentry)
├─ Analytics (user behavior)
└─ Real User Monitoring (RUM)
```

---

## Related Code Files

### Files to Create

1. **Performance**:
   - `lib/performance/monitoring.ts` (Web Vitals tracking)
   - `lib/performance/optimization.ts` (optimization utilities)
   - `lib/utils/debounce.ts`
   - `lib/utils/throttle.ts`

2. **Error Handling**:
   - `components/errors/ErrorBoundary.tsx`
   - `components/errors/ErrorFallback.tsx`
   - `lib/errors/error-handler.ts`
   - `lib/errors/error-logger.ts`

3. **Loading States**:
   - `components/loading/Skeleton.tsx`
   - `components/loading/SquadSkeleton.tsx`
   - `components/loading/TaskSkeleton.tsx`
   - `components/loading/MessageSkeleton.tsx`

4. **Animations**:
   - `lib/animations/variants.ts` (Framer Motion variants)
   - `lib/animations/transitions.ts`

5. **Accessibility**:
   - `lib/utils/accessibility.ts`
   - `components/a11y/SkipToContent.tsx`
   - `components/a11y/ScreenReaderOnly.tsx`

6. **Testing**:
   - `__tests__/components/SquadCard.test.tsx`
   - `__tests__/hooks/useSquads.test.tsx`
   - `e2e/auth.spec.ts`
   - `e2e/squads.spec.ts`

7. **Configuration**:
   - `.env.production`
   - `next.config.js` (production optimizations)
   - `sentry.config.js`

---

## Implementation Steps

### Step 1: Add Virtualization

```typescript
// components/tasks/VirtualizedTaskBoard.tsx
'use client';

import { FixedSizeList } from 'react-window';
import { TaskCard } from './TaskCard';
import type { Task } from '@/types/task';

interface VirtualizedTaskBoardProps {
  tasks: Task[];
}

export function VirtualizedTaskBoard({ tasks }: VirtualizedTaskBoardProps) {
  const CARD_HEIGHT = 120;
  const CONTAINER_HEIGHT = 800;

  return (
    <FixedSizeList
      height={CONTAINER_HEIGHT}
      itemCount={tasks.length}
      itemSize={CARD_HEIGHT}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <TaskCard task={tasks[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

### Step 2: Implement Optimistic Updates

```typescript
// lib/hooks/useUpdateTaskStatus.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/lib/api/tasks';
import type { Task } from '@/types/task';

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      tasksApi.updateStatus(id, status),

    // Optimistic update
    onMutate: async ({ id, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(['tasks']);

      // Snapshot previous value
      const previousTasks = queryClient.getQueryData<Task[]>(['tasks']);

      // Optimistically update
      queryClient.setQueryData<Task[]>(['tasks'], (old = []) =>
        old.map((task) =>
          task.id === id ? { ...task, status: status as any } : task
        )
      );

      return { previousTasks };
    },

    // Rollback on error
    onError: (err, variables, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks);
      }
    },

    // Refetch on success
    onSettled: () => {
      queryClient.invalidateQueries(['tasks']);
    },
  });
}
```

### Step 3: Add Debouncing for Real-Time Updates

```typescript
// lib/utils/debounce.ts
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

// Usage in real-time hook
import { debounce } from '@/lib/utils/debounce';

const updateQueue: ActivityEvent[] = [];

const batchedUpdate = debounce((events: ActivityEvent[]) => {
  queryClient.setQueryData<ActivityEvent[]>(
    ['activity', executionId],
    (old = []) => [...old, ...events]
  );
  updateQueue.length = 0;
}, 100);

socket.on('agent:update', (update) => {
  updateQueue.push(update);
  batchedUpdate(updateQueue);
});
```

### Step 4: Create Error Boundary

```typescript
// components/errors/ErrorBoundary.tsx
'use client';

import React from 'react';
import { ErrorFallback } from './ErrorFallback';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // Log to error tracking service (Sentry, etc.)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <ErrorFallback
            error={this.state.error}
            reset={() => this.setState({ hasError: false })}
          />
        )
      );
    }

    return this.props.children;
  }
}
```

```typescript
// components/errors/ErrorFallback.tsx
'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

interface ErrorFallbackProps {
  error?: Error;
  reset: () => void;
}

export function ErrorFallback({ error, reset }: ErrorFallbackProps) {
  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <Card className="max-w-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <h2 className="text-2xl font-bold">Something went wrong</h2>
        </div>

        <p className="text-gray-600 mb-4">
          We're sorry, but something unexpected happened. Please try again.
        </p>

        {error && (
          <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto mb-4">
            {error.message}
          </pre>
        )}

        <Button onClick={reset} className="w-full">
          Try again
        </Button>
      </Card>
    </div>
  );
}
```

### Step 5: Add Loading Skeletons

```typescript
// components/loading/Skeleton.tsx
'use client';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={{ animationDuration: '1.5s' }}
    />
  );
}
```

```typescript
// components/loading/SquadSkeleton.tsx
import { Skeleton } from './Skeleton';

export function SquadSkeleton() {
  return (
    <div className="p-4 border rounded-lg space-y-3">
      <Skeleton className="h-6 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  );
}
```

### Step 6: Add Animation Variants

```typescript
// lib/animations/variants.ts
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 },
};

export const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3 },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 },
  transition: { duration: 0.2 },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const listItem = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};
```

### Step 7: Performance Monitoring

```typescript
// lib/performance/monitoring.ts
import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals';

export function reportWebVitals() {
  onCLS(console.log); // Cumulative Layout Shift
  onFID(console.log); // First Input Delay
  onLCP(console.log); // Largest Contentful Paint
  onFCP(console.log); // First Contentful Paint
  onTTFB(console.log); // Time to First Byte
}

// Custom metrics
export function trackCustomMetric(name: string, value: number) {
  if (typeof window !== 'undefined' && 'performance' in window) {
    performance.mark(name);
    console.log(`[Metric] ${name}: ${value}ms`);
  }
}

// Usage in components
export function usePerformanceTracker(name: string) {
  useEffect(() => {
    const start = performance.now();

    return () => {
      const duration = performance.now() - start;
      trackCustomMetric(name, duration);
    };
  }, [name]);
}
```

### Step 8: Bundle Size Optimization

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Webpack optimizations
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Split large libraries into separate chunks
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // Vendor chunk for node_modules
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // Common chunk for shared code
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
        },
      };
    }

    return config;
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },

  // Experimental features
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
};

module.exports = nextConfig;
```

### Step 9: Accessibility Improvements

```typescript
// components/a11y/SkipToContent.tsx
export function SkipToContent() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-500 focus:text-white focus:rounded"
    >
      Skip to main content
    </a>
  );
}

// Add to layout
<SkipToContent />
<main id="main-content">
  {children}
</main>
```

```typescript
// Keyboard shortcuts
import { useEffect } from 'react';

export function useKeyboardShortcut(key: string, callback: () => void) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === key && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        callback();
      }
    };

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [key, callback]);
}

// Usage
useKeyboardShortcut('k', () => {
  // Open command palette
});
```

### Step 10: Testing Setup

```typescript
// __tests__/components/SquadCard.test.tsx
import { render, screen } from '@testing-library/react';
import { SquadCard } from '@/components/squads/SquadCard';

describe('SquadCard', () => {
  const mockSquad = {
    id: '1',
    name: 'Test Squad',
    description: 'Test description',
    status: 'active' as const,
    organization_id: 'org-1',
    user_id: 'user-1',
    config: {},
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  };

  it('renders squad name and description', () => {
    render(<SquadCard squad={mockSquad} />);

    expect(screen.getByText('Test Squad')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('displays correct status badge', () => {
    render(<SquadCard squad={mockSquad} />);

    const badge = screen.getByText('active');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-green-100');
  });
});
```

```typescript
// e2e/auth.spec.ts (Playwright)
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Login failed')).toBeVisible();
  });
});
```

---

## Todo List

### P0 - Critical Path

- [ ] Add virtualization for task board (100+ tasks)
- [ ] Implement optimistic updates for task moves
- [ ] Add debouncing for real-time updates
- [ ] Create ErrorBoundary components
- [ ] Create loading skeleton components
- [ ] Add error handling with retry logic
- [ ] Configure bundle size optimization
- [ ] Add Web Vitals monitoring
- [ ] Test performance (LCP, FID, CLS)
- [ ] Add accessibility improvements (ARIA labels)

### P1 - Important

- [ ] Add Framer Motion animations
- [ ] Create animation variants library
- [ ] Add keyboard shortcuts
- [ ] Add skip-to-content link
- [ ] Create unit tests for components
- [ ] Create integration tests for hooks
- [ ] Set up e2e tests (Playwright)
- [ ] Add error logging (Sentry)
- [ ] Configure production environment
- [ ] Add service worker for offline support

### P2 - Nice to Have

- [ ] Add performance dashboard
- [ ] Add bundle analyzer
- [ ] Add lighthouse CI
- [ ] Add visual regression testing
- [ ] Add load testing
- [ ] Add A/B testing framework
- [ ] Add feature flags
- [ ] Add analytics integration

---

## Success Criteria

### Performance Criteria
✅ LCP < 1.5s
✅ FID < 100ms
✅ CLS < 0.1
✅ Bundle size < 300KB gzipped
✅ Task board renders 1000 tasks < 500ms
✅ Real-time updates < 200ms latency

### Quality Criteria
✅ Test coverage > 80% for critical paths
✅ Zero console errors in production
✅ All animations run at 60fps
✅ WCAG 2.1 AA compliance
✅ Works on Chrome, Firefox, Safari, Edge

### User Experience Criteria
✅ Smooth transitions and animations
✅ Instant feedback for user actions
✅ Graceful error handling
✅ Clear loading states
✅ Keyboard accessible

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Performance degradation at scale | Medium | High | Load testing, virtualization |
| Animation jank on low-end devices | Low | Medium | Reduce animation complexity, feature detect |
| Bundle size bloat | Medium | Medium | Tree shaking, code splitting, analyzer |
| Accessibility regressions | Low | Medium | Automated testing, manual audits |

---

## Security Considerations

- Remove console.log in production
- Sanitize error messages (no sensitive data)
- Rate limit error reporting (prevent spam)

---

## Deployment Checklist

### Pre-Deployment
- [ ] Run production build
- [ ] Test in production mode locally
- [ ] Check bundle size
- [ ] Run lighthouse audit
- [ ] Test on real devices (mobile, tablet)
- [ ] Verify environment variables

### Deployment
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Deploy to production
- [ ] Verify deployment

### Post-Deployment
- [ ] Monitor Web Vitals
- [ ] Monitor error logs
- [ ] Check analytics
- [ ] Gather user feedback

---

## Next Steps

After completing Phase 5:
1. **Final Review**: All phases complete
2. **Documentation**: Update README, API docs
3. **Handoff**: Transfer to team
4. **Monitoring**: Set up alerts
5. **Iteration**: Plan next features

---

## Unresolved Questions

1. **Error Logging**: Which service? (Sentry, LogRocket, Datadog)
2. **Analytics**: Which platform? (Google Analytics, Mixpanel, Amplitude)
3. **Performance Budget**: Acceptable thresholds for production?
4. **Testing Coverage**: Target % for different test types?
5. **Deployment**: CI/CD pipeline setup (GitHub Actions, Vercel, AWS)?
