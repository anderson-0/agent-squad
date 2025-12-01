# Phase 1: Foundation & Setup

**Status**: Pending
**Priority**: P0
**Dependencies**: None
**Estimated Duration**: Claude (2 hrs) | Senior Dev (1 day) | Junior Dev (2-3 days)

---

## Context

Phase 1 establishes the foundational architecture for the agent visualization frontend. This includes Next.js 15 setup, authentication integration, API client configuration, real-time service setup, and base routing structure. This phase must be completed before any UI components can be built.

**Related Files**:
- Research: `research/researcher-01-ux-patterns.md`, `research/researcher-02-tech-stack.md`
- Backend API: `scout/scout-02-backend-api.md`

---

## Overview

**Goal**: Create production-ready Next.js 15 + React 19 foundation with authentication, API integration, and real-time communication.

**Key Deliverables**:
1. Next.js 15 project with TypeScript + App Router
2. Authentication system (JWT tokens)
3. API client with TanStack Query
4. Socket.io/SSE service integration
5. Base layout with navigation
6. Route structure

**Dates**:
- Start: TBD
- End: TBD
- **Status**: Pending

---

## Key Insights from Research

### From `researcher-02-tech-stack.md`

**Real-Time Communication**:
- Socket.io recommended for bidirectional WebSocket with auto-reconnect
- SSE (EventSource) as fallback for read-only dashboards
- Backend already has SSE at `/api/v1/sse/execution/{id}`

**State Management**:
- TanStack Query v5 for server state (agent data, caching, optimistic updates)
- Zustand for client state (UI filters, view modes)
- Separation of concerns: server vs client state

**Next.js 15 Architecture**:
- React Server Components reduce bundle size by 50%
- Streaming Suspense for progressive loading
- Mark client components with `'use client'` only where needed

**Performance**:
- Debouncing WebSocket updates (100ms batching)
- Memoization for agent cards (React.memo)
- Virtualization with react-window for 100+ agents

---

## Requirements

### Functional Requirements

**FR-1.1**: Next.js 15 project initialized with TypeScript, Tailwind CSS, App Router
**FR-1.2**: Authentication flow (login, register, token refresh, logout)
**FR-1.3**: Protected routes with middleware (redirect to /login if unauthenticated)
**FR-1.4**: API client configured with JWT token injection
**FR-1.5**: Socket.io client for real-time updates
**FR-1.6**: SSE fallback implementation
**FR-1.7**: Base layout with sidebar navigation
**FR-1.8**: Route structure: `/`, `/squads`, `/squads/[id]`, `/tasks`, `/agents`

### Non-Functional Requirements

**NFR-1.1**: TypeScript strict mode enabled
**NFR-1.2**: Code splitting and lazy loading configured
**NFR-1.3**: Environment variables for API URLs
**NFR-1.4**: Error boundary for graceful error handling
**NFR-1.5**: Loading states for all async operations
**NFR-1.6**: SEO metadata configuration

---

## Architecture

### Directory Structure

```
frontend/
├── app/
│   ├── (auth)/                    # Auth layout group
│   │   ├── login/
│   │   │   └── page.tsx           # Login page
│   │   ├── register/
│   │   │   └── page.tsx           # Register page
│   │   └── layout.tsx             # Auth layout (no sidebar)
│   ├── (dashboard)/               # Protected layout group
│   │   ├── squads/
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx       # Squad detail page
│   │   │   └── page.tsx           # Squad list page
│   │   ├── tasks/
│   │   │   └── page.tsx           # Task board page
│   │   ├── agents/
│   │   │   └── page.tsx           # Agent dashboard page
│   │   ├── layout.tsx             # Dashboard layout (with sidebar)
│   │   └── page.tsx               # Dashboard home
│   ├── layout.tsx                 # Root layout
│   └── providers.tsx              # Global providers
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx          # Login form
│   │   └── RegisterForm.tsx       # Register form
│   ├── layout/
│   │   ├── Sidebar.tsx            # Main sidebar navigation
│   │   ├── Header.tsx             # Header with user menu
│   │   └── Footer.tsx             # Footer
│   └── ui/                        # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       └── ...
├── lib/
│   ├── api/
│   │   ├── client.ts              # Axios client configuration
│   │   ├── auth.ts                # Auth API calls
│   │   ├── squads.ts              # Squads API calls
│   │   ├── tasks.ts               # Tasks API calls
│   │   └── agents.ts              # Agents API calls
│   ├── hooks/
│   │   ├── useAuth.ts             # Auth hook
│   │   ├── useRealtime.ts         # Real-time hook
│   │   └── useSocket.ts           # Socket.io hook
│   ├── store/
│   │   ├── auth.ts                # Auth Zustand store
│   │   └── ui.ts                  # UI state Zustand store
│   ├── realtime/
│   │   ├── socket.ts              # Socket.io client
│   │   └── sse.ts                 # SSE client
│   └── utils/
│       ├── cn.ts                  # Tailwind utility
│       └── format.ts              # Formatting utilities
├── types/
│   ├── auth.ts                    # Auth types
│   ├── squad.ts                   # Squad types
│   ├── task.ts                    # Task types
│   ├── agent.ts                   # Agent types
│   └── message.ts                 # Message types
├── middleware.ts                  # Auth middleware
├── next.config.js                 # Next.js config
├── tailwind.config.ts             # Tailwind config
├── tsconfig.json                  # TypeScript config
└── package.json                   # Dependencies
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│                     User                                 │
└────────────┬──────────────────────────────────┬─────────┘
             │                                   │
             ▼                                   ▼
    ┌─────────────────┐                ┌─────────────────┐
    │  Login Page     │                │  Dashboard      │
    │  /login         │                │  (Protected)    │
    └────────┬────────┘                └────────▲────────┘
             │                                   │
             │ 1. Submit credentials             │ 4. Access granted
             ▼                                   │
    ┌─────────────────────────────────────────┐ │
    │  POST /api/v1/auth/login                │ │
    │  Returns: { access_token, refresh_token}│ │
    └────────┬────────────────────────────────┘ │
             │                                   │
             │ 2. Store tokens                   │
             ▼                                   │
    ┌─────────────────────────────────────────┐ │
    │  localStorage/cookies                   │ │
    │  - access_token (30 min)                │ │
    │  - refresh_token (7 days)               │ │
    └────────┬────────────────────────────────┘ │
             │                                   │
             │ 3. Middleware validates token     │
             └───────────────────────────────────┘

Token Refresh Flow:
┌─────────────────────────────────────────────────────────┐
│  Request with expired access_token                       │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  401 Unauthorized│
    └────────┬────────┘
             │
             │ Intercept 401
             ▼
    ┌─────────────────────────────────────────┐
    │  POST /api/v1/auth/refresh              │
    │  Body: { refresh_token }                │
    │  Returns: { access_token }              │
    └────────┬────────────────────────────────┘
             │
             │ Retry original request
             ▼
    ┌─────────────────┐
    │  Success        │
    └─────────────────┘
```

### API Client Architecture

```typescript
// lib/api/client.ts
import axios from 'axios';
import { getAccessToken, refreshAccessToken } from '@/lib/store/auth';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const newToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### Real-Time Service Architecture

```typescript
// lib/realtime/socket.ts
import { io, Socket } from 'socket.io-client';

class SocketService {
  private socket: Socket | null = null;

  connect(token: string) {
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
      auth: { token },
      transports: ['websocket', 'polling'], // Auto-fallback
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('Socket connected:', this.socket?.id);
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    return this.socket;
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  on(event: string, callback: (...args: any[]) => void) {
    this.socket?.on(event, callback);
  }

  off(event: string, callback?: (...args: any[]) => void) {
    this.socket?.off(event, callback);
  }

  emit(event: string, data: any) {
    this.socket?.emit(event, data);
  }
}

export const socketService = new SocketService();
```

```typescript
// lib/realtime/sse.ts
class SSEService {
  private eventSource: EventSource | null = null;

  connect(url: string, token: string) {
    // Note: EventSource doesn't support custom headers
    // Token must be in URL or use alternative authentication
    const urlWithToken = `${url}?token=${token}`;

    this.eventSource = new EventSource(urlWithToken);

    this.eventSource.onopen = () => {
      console.log('SSE connected');
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      this.eventSource?.close();
    };

    return this.eventSource;
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  }

  on(event: string, callback: (event: MessageEvent) => void) {
    this.eventSource?.addEventListener(event, callback);
  }

  off(event: string, callback: (event: MessageEvent) => void) {
    this.eventSource?.removeEventListener(event, callback);
  }
}

export const sseService = new SSEService();
```

---

## Related Code Files

### Files to Create

1. **Project Initialization**:
   - `frontend/package.json`
   - `frontend/next.config.js`
   - `frontend/tsconfig.json`
   - `frontend/tailwind.config.ts`

2. **Authentication**:
   - `frontend/lib/store/auth.ts` (Zustand store)
   - `frontend/lib/api/auth.ts` (API calls)
   - `frontend/components/auth/LoginForm.tsx`
   - `frontend/components/auth/RegisterForm.tsx`
   - `frontend/app/(auth)/login/page.tsx`
   - `frontend/app/(auth)/register/page.tsx`
   - `frontend/middleware.ts` (route protection)

3. **API Client**:
   - `frontend/lib/api/client.ts` (Axios config)
   - `frontend/lib/hooks/useAuth.ts`
   - `frontend/types/auth.ts`

4. **Real-Time Services**:
   - `frontend/lib/realtime/socket.ts`
   - `frontend/lib/realtime/sse.ts`
   - `frontend/lib/hooks/useSocket.ts`
   - `frontend/lib/hooks/useRealtime.ts`

5. **Layout & Navigation**:
   - `frontend/app/layout.tsx` (root layout)
   - `frontend/app/providers.tsx` (global providers)
   - `frontend/app/(dashboard)/layout.tsx` (dashboard layout)
   - `frontend/components/layout/Sidebar.tsx`
   - `frontend/components/layout/Header.tsx`

6. **Configuration**:
   - `frontend/.env.local` (environment variables)
   - `frontend/.env.example` (template)

---

## Implementation Steps

### Step 1: Initialize Next.js Project

```bash
# Navigate to project root
cd /home/anderson/Documents/git/anderson-0/agent-squad

# Create frontend directory
mkdir -p frontend
cd frontend

# Initialize Next.js 15 with Bun
bun create next-app@latest . --typescript --tailwind --app --src-dir=false --import-alias="@/*"
```

### Step 2: Install Dependencies

```bash
# Core dependencies
bun add @tanstack/react-query socket.io-client zustand axios
bun add framer-motion react-window zod

# shadcn/ui setup
bunx shadcn@latest init
bunx shadcn@latest add button card input label form toast dialog

# Dev dependencies
bun add -D @types/node @types/react @types/react-dom
```

### Step 3: Configure Environment Variables

```bash
# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
EOF

# Create .env.example
cat > .env.example << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
EOF
```

### Step 4: Create Type Definitions

Create TypeScript types matching backend Pydantic schemas:

```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}
```

### Step 5: Create Auth Store (Zustand)

```typescript
// lib/store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  updateAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, isAuthenticated: true }),
      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
      updateAccessToken: (token) => set({ accessToken: token }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export const getAccessToken = () => useAuthStore.getState().accessToken;
export const getRefreshToken = () => useAuthStore.getState().refreshToken;
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token');

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) throw new Error('Token refresh failed');

  const data = await response.json();
  useAuthStore.getState().updateAccessToken(data.access_token);
  return data.access_token;
};
```

### Step 6: Create API Client

Implement the architecture from "API Client Architecture" section above.

### Step 7: Create Auth API Calls

```typescript
// lib/api/auth.ts
import apiClient from './client';
import type { LoginRequest, LoginResponse, RegisterRequest } from '@/types/auth';

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  logout: async () => {
    await apiClient.post('/auth/logout');
  },

  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};
```

### Step 8: Create Real-Time Services

Implement Socket.io and SSE services from "Real-Time Service Architecture" section.

### Step 9: Create Auth Middleware

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const authCookie = request.cookies.get('auth-storage');
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') ||
                     request.nextUrl.pathname.startsWith('/register');
  const isProtectedPage = request.nextUrl.pathname.startsWith('/squads') ||
                          request.nextUrl.pathname.startsWith('/tasks') ||
                          request.nextUrl.pathname.startsWith('/agents') ||
                          request.nextUrl.pathname === '/';

  // Redirect to login if accessing protected page without auth
  if (isProtectedPage && !authCookie) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect to dashboard if accessing auth page while authenticated
  if (isAuthPage && authCookie) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/', '/squads/:path*', '/tasks/:path*', '/agents/:path*', '/login', '/register'],
};
```

### Step 10: Create Base Layouts

```typescript
// app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Agent Squad',
  description: 'Multi-agent collaboration platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

```typescript
// app/providers.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Step 11: Create Login Page

```typescript
// app/(auth)/login/page.tsx
import { LoginForm } from '@/components/auth/LoginForm';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>Sign in to your account to continue</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </div>
  );
}
```

```typescript
// components/auth/LoginForm.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/store/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const { toast } = useToast();

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token);
      router.push('/');
    },
    onError: (error: any) => {
      toast({
        title: 'Login failed',
        description: error.response?.data?.detail || 'Invalid credentials',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ email, password });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
        {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
      </Button>
    </form>
  );
}
```

### Step 12: Create Dashboard Layout

```typescript
// app/(dashboard)/layout.tsx
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">{children}</main>
      </div>
    </div>
  );
}
```

### Step 13: Create Navigation Components

```typescript
// components/layout/Sidebar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils/cn';
import { Users, ClipboardList, Bot } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: ClipboardList },
  { name: 'Squads', href: '/squads', icon: Users },
  { name: 'Tasks', href: '/tasks', icon: ClipboardList },
  { name: 'Agents', href: '/agents', icon: Bot },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 flex-col border-r bg-white">
      <div className="flex h-16 items-center px-6 font-bold text-xl">
        Agent Squad
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

---

## Todo List

### P0 - Critical Path

- [ ] Initialize Next.js 15 project with TypeScript and Tailwind
- [ ] Install core dependencies (TanStack Query, Socket.io, Zustand, shadcn/ui)
- [ ] Configure environment variables (.env.local, .env.example)
- [ ] Create TypeScript type definitions matching backend schemas
- [ ] Implement Auth Zustand store with persistence
- [ ] Create API client with Axios and interceptors
- [ ] Implement token refresh logic in API client
- [ ] Create auth API calls (login, register, logout, getMe)
- [ ] Build Socket.io service with auto-reconnect
- [ ] Build SSE service as fallback
- [ ] Create auth middleware for route protection
- [ ] Implement root layout with global providers
- [ ] Create TanStack Query provider
- [ ] Build login page and LoginForm component
- [ ] Build register page and RegisterForm component
- [ ] Create dashboard layout with sidebar
- [ ] Implement Sidebar navigation component
- [ ] Implement Header component with user menu
- [ ] Test authentication flow end-to-end
- [ ] Verify token refresh on 401 errors
- [ ] Test protected route redirects

### P1 - Important

- [ ] Add loading states for all async operations
- [ ] Create error boundary component
- [ ] Add toast notifications for errors
- [ ] Implement logout functionality
- [ ] Create useAuth custom hook
- [ ] Create useSocket custom hook
- [ ] Add TypeScript strict mode enforcement
- [ ] Configure Next.js for optimal bundle size
- [ ] Add SEO metadata to all pages
- [ ] Test SSE fallback when WebSocket fails

### P2 - Nice to Have

- [ ] Add dark mode support
- [ ] Create skeleton loading components
- [ ] Add accessibility improvements (ARIA labels)
- [ ] Implement password reset flow
- [ ] Add email verification flow
- [ ] Create onboarding tour for new users
- [ ] Add analytics integration
- [ ] Implement remember me functionality
- [ ] Add biometric authentication support

---

## Success Criteria

### Functional Criteria
✅ User can register new account
✅ User can login with credentials
✅ JWT tokens stored securely
✅ Protected routes redirect to login when unauthenticated
✅ Token refresh works automatically on 401
✅ User can logout and tokens are cleared
✅ Navigation sidebar displays correctly
✅ Dashboard layout renders with header and content area

### Technical Criteria
✅ TypeScript strict mode enabled with no errors
✅ All API calls use Axios client with interceptors
✅ TanStack Query configured with proper defaults
✅ Socket.io client connects successfully
✅ SSE fallback works when WebSocket unavailable
✅ Environment variables configured correctly
✅ Code splitting and lazy loading working
✅ Bundle size < 300KB gzipped

### Performance Criteria
✅ Login response < 500ms
✅ Page load time < 2s
✅ Real-time connection established < 1s
✅ Token refresh < 200ms

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Backend API changes schema | Medium | High | Use Zod validation, runtime checks |
| Token expiration during requests | High | Medium | Implement queue for pending requests |
| WebSocket connection failures | Medium | Medium | Implement SSE fallback, retry logic |
| CORS issues in development | Low | Low | Configure Next.js rewrites |
| Type mismatches with backend | High | Medium | Generate types from OpenAPI spec |
| Performance issues with large bundles | Low | Medium | Code splitting, lazy loading |

---

## Security Considerations

### Authentication Security
- **Token Storage**: Consider HTTP-only cookies instead of localStorage (XSS protection)
- **Token Refresh**: Refresh tokens should be rotated on each use
- **HTTPS Only**: Enforce HTTPS in production
- **CSRF Protection**: Add CSRF tokens for state-changing operations

### API Security
- **Input Validation**: Validate all user inputs with Zod
- **Error Handling**: Don't expose sensitive error details to client
- **Rate Limiting**: Implement client-side rate limiting for API calls

### Real-Time Security
- **WebSocket Auth**: Authenticate WebSocket connections with JWT
- **Message Validation**: Validate all incoming real-time messages
- **Connection Limits**: Limit concurrent connections per user

---

## Next Steps

After completing Phase 1:
1. **Review**: Ensure all P0 todos completed
2. **Test**: Run full authentication flow
3. **Document**: Update any deviations from plan
4. **Proceed**: Start Phase 2 (Squad & Task Visualization)

---

## Unresolved Questions

1. **Token Storage**: Should we use HTTP-only cookies or localStorage?
   - **Recommendation**: HTTP-only cookies for better XSS protection
   - **Trade-off**: More complex CORS configuration

2. **WebSocket Server**: Will backend support Socket.io or only SSE?
   - **Current State**: Backend has SSE at `/api/v1/sse/*`
   - **Action**: Confirm if Socket.io will be added or use SSE only

3. **Type Generation**: Should we generate TypeScript types from backend OpenAPI spec?
   - **Recommendation**: Yes, use `openapi-typescript` for type safety
   - **Action**: Set up automated type generation

4. **Environment**: Should frontend be in monorepo or separate repo?
   - **Current**: Adding to existing repo as `frontend/` directory
   - **Future**: Consider splitting if deployment needs differ

5. **Authentication Method**: JWT in header vs. cookies?
   - **Current Plan**: Bearer token in Authorization header
   - **Alternative**: HTTP-only cookies with CSRF protection
