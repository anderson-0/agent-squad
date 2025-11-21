# Authentication Component Architecture

## Component Hierarchy

```
app/(auth)/
│
├── layout.tsx                    [Auth Layout]
│   └── Centered container with gradient background
│       ├── Mobile: Full width with padding
│       ├── Tablet+: max-w-md (28rem)
│       └── Gradient: from-background via-background to-muted/20
│
├── login/page.tsx                [Login Page]
│   └── Suspense boundary
│       ├── fallback: <LoginSkeleton />
│       └── Card wrapper
│           └── <LoginForm />
│
└── register/page.tsx             [Register Page]
    └── Suspense boundary
        ├── fallback: <RegisterSkeleton />
        └── Card wrapper
            └── <RegisterForm />
```

## Component Details

### LoginForm Component

```
<LoginForm>
│
├── Container (motion.div)
│   ├── Variants: containerVariants
│   └── Stagger children with 0.1s delay
│
├── Header (motion.div)
│   ├── Title: "Welcome back"
│   └── Description: "Sign in to your account"
│
├── Form (motion.div with shake)
│   ├── Email Field (motion.div)
│   │   ├── Label: "Email"
│   │   ├── Icon: <Mail />
│   │   └── Input (with focus animation)
│   │
│   ├── Password Field (motion.div)
│   │   ├── Label: "Password"
│   │   ├── Icon: <Lock />
│   │   ├── Input (with focus animation)
│   │   └── Toggle: <Eye /> / <EyeOff />
│   │
│   └── Submit Button (motion.div)
│       ├── Hover: scale(1.02)
│       ├── Tap: scale(0.98)
│       └── Loading: <Loader2 /> + "Signing in..."
│
└── Footer (motion.div)
    └── Link: "Don't have an account? Sign up"
```

### RegisterForm Component

```
<RegisterForm>
│
├── Container (motion.div)
│   ├── Variants: containerVariants
│   └── Stagger children with 0.08s delay
│
├── Header (motion.div)
│   ├── Title: "Create an account"
│   └── Description: "Join Agent Squad"
│
├── Form (motion.div with shake)
│   ├── Name Field (motion.div)
│   │   ├── Label: "Name"
│   │   ├── Icon: <User />
│   │   └── Input (with focus animation)
│   │
│   ├── Email Field (motion.div)
│   │   ├── Label: "Email"
│   │   ├── Icon: <Mail />
│   │   └── Input (with focus animation)
│   │
│   ├── Password Field (motion.div)
│   │   ├── Label: "Password"
│   │   ├── Icon: <Lock />
│   │   ├── Input (with focus animation)
│   │   └── Toggle: <Eye /> / <EyeOff />
│   │
│   ├── Confirm Password Field (motion.div)
│   │   ├── Label: "Confirm Password"
│   │   ├── Icon: <Lock />
│   │   ├── Input (with focus animation)
│   │   └── Toggle: <Eye /> / <EyeOff />
│   │
│   └── Submit Button (motion.div)
│       ├── Hover: scale(1.02)
│       ├── Tap: scale(0.98)
│       └── Loading: <Loader2 /> + "Creating account..."
│
└── Footer (motion.div)
    └── Link: "Already have an account? Sign in"
```

## Data Flow

```
User Interaction
      ↓
Form Input (React Hook Form)
      ↓
Validation (Zod Schema)
      ├─ Invalid → Display errors + shake animation
      └─ Valid
            ↓
Submit (TanStack Query mutation)
      ↓
API Call (authApi.login/register)
      ├─ Loading
      │     ├─ Disable inputs
      │     ├─ Show spinner in button
      │     └─ Display loading text
      │
      ├─ Success
      │     ├─ Store user in Zustand (useAuthStore)
      │     ├─ Show success toast with checkmark
      │     └─ Redirect to "/" (useRouter)
      │
      └─ Error
            ├─ Trigger shake animation
            ├─ Show error toast
            └─ Keep form interactive
```

## State Management

### Local State (useState)
```typescript
// LoginForm & RegisterForm
const [showPassword, setShowPassword] = useState(false);
const [showConfirmPassword, setShowConfirmPassword] = useState(false); // Register only
const [shouldShake, setShouldShake] = useState(false);
```

### Form State (React Hook Form)
```typescript
const form = useForm<FormValues>({
  resolver: zodResolver(schema),
  defaultValues: { /* ... */ },
});
```

### API State (TanStack Query)
```typescript
const mutation = useMutation({
  mutationFn: authApi.login,
  onSuccess: (data) => {
    setUser(data.user);           // Zustand store
    toast.success('Welcome!');     // Sonner toast
    router.push('/');              // Next.js router
  },
  onError: (error) => {
    setShouldShake(true);
    toast.error('Failed');
  },
});
```

### Global State (Zustand)
```typescript
const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      clearAuth: () => set({ user: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);
```

## Animation Timeline

### Page Load (Login/Register)
```
0ms:    Initial state (opacity: 0, y: 20)
        ↓
0-500ms: Container fades in + slides up
        ↓
0-100ms: Header appears
        ↓
100-200ms: First field appears (stagger delay)
        ↓
200-300ms: Second field appears
        ↓
300-400ms: Third field appears (register only)
        ↓
400-500ms: Fourth field appears (register only)
        ↓
500-600ms: Button + footer appear
```

### Form Interaction
```
Input Focus:
- Scale: 1 → 1.01 (200ms)

Button Hover:
- Scale: 1 → 1.02 (200ms)

Button Click:
- Scale: 1 → 0.98 (200ms)

Link Hover:
- Scale: 1 → 1.05 (200ms)
```

### Error State
```
Validation Error:
- Shake: x = [-10, 10, -10, 10, 0] (400ms)
- Error message slides in
- Border turns red
```

### Success State
```
Registration Success:
- Checkmark: scale 0 → 1, rotate -180° → 0° (spring)
- Toast slides in from bottom
- Page redirects after 1s
```

## Validation Schema

### Login Schema (Zod)
```typescript
z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(8, 'Min 8 characters'),
})
```

### Register Schema (Zod)
```typescript
z.object({
  name: z.string().min(2, 'Min 2 characters'),
  email: z.string().email('Valid email required'),
  password: z
    .string()
    .min(8, 'Min 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Must contain uppercase, lowercase, number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})
```

## API Integration

### Login Flow
```
POST /auth/login
Body: { email, password }

Success (200):
{
  access_token: string,
  refresh_token: string,
  token_type: "bearer",
  user: {
    id: string,
    email: string,
    name: string,
    created_at: string
  }
}

Cookies Set:
- access_token (HTTP-only)
- refresh_token (HTTP-only)
```

### Register Flow
```
POST /auth/register
Body: { name, email, password }

Success (200):
{
  access_token: string,
  refresh_token: string,
  token_type: "bearer",
  user: {
    id: string,
    email: string,
    name: string,
    created_at: string
  }
}

Cookies Set:
- access_token (HTTP-only)
- refresh_token (HTTP-only)
```

## Accessibility Tree

### Login Form
```
<form>
  <div> [group] Email
    <label> Email
    <input> [textbox] you@example.com
      [aria-invalid="false"]
      [aria-describedby="email-error"]
    <span> [alert] Error message (if invalid)

  <div> [group] Password
    <label> Password
    <input> [textbox, password] ••••••••
      [aria-invalid="false"]
      [aria-describedby="password-error"]
    <button> [button] Show/Hide password
      [aria-label="Show password"]
      [aria-pressed="false"]
    <span> [alert] Error message (if invalid)

  <button> [button] Sign in
    [aria-busy="false"]
    [disabled="false"]

  <div> [text] Don't have an account?
    <a> [link] Sign up
```

## Responsive Breakpoints

### Mobile (375px - 767px)
```css
.auth-layout {
  padding: 1rem;              /* 16px */
  width: 100%;
}

.auth-card {
  max-width: 100%;
}

.form-field {
  min-height: 44px;           /* Touch target */
}

.button {
  min-height: 44px;
  font-size: 1rem;            /* 16px */
}
```

### Tablet (768px - 1279px)
```css
.auth-layout {
  padding: 1.5rem;            /* 24px */
}

.auth-card {
  max-width: 28rem;           /* 448px */
}
```

### Desktop (1280px+)
```css
.auth-layout {
  padding: 2rem;              /* 32px */
}

.auth-card {
  max-width: 28rem;           /* 448px */
}
```

## Performance Metrics

### Target Metrics
- **First Contentful Paint (FCP):** < 1.5s
- **Largest Contentful Paint (LCP):** < 2.5s
- **Time to Interactive (TTI):** < 3.5s
- **Cumulative Layout Shift (CLS):** < 0.1
- **First Input Delay (FID):** < 100ms

### Optimization Techniques
1. Suspense boundaries for code splitting
2. Lazy-loaded Framer Motion animations
3. Optimized re-renders with React Hook Form
4. Memoized components where needed
5. Hardware-accelerated animations (transform, opacity)

## Error Scenarios

### Network Errors
```
Error: Failed to fetch
Display: "Network error. Please check your connection."
Action: Keep form interactive, allow retry
```

### Validation Errors
```
Error: Email invalid
Display: Inline error below field
Action: Highlight field, show error message
```

### API Errors (400)
```
Error: Invalid credentials
Display: Toast notification + shake animation
Action: Clear password field, refocus email
```

### Server Errors (500)
```
Error: Internal server error
Display: "Something went wrong. Please try again later."
Action: Keep form interactive, log error
```

## Testing Strategy

### Unit Tests
- Form validation logic
- Animation variant definitions
- State management functions

### Integration Tests
- Form submission flow
- Error handling
- Success redirection

### E2E Tests (Playwright)
- Complete login flow
- Complete registration flow
- Error scenarios
- Responsive behavior
- Accessibility compliance

## Future Enhancements

### Phase 1 (High Priority)
- [ ] Forgot password flow
- [ ] Email verification UI
- [ ] Password strength indicator
- [ ] Rate limiting feedback

### Phase 2 (Medium Priority)
- [ ] Social auth (Google, GitHub)
- [ ] Multi-factor authentication
- [ ] Remember me checkbox
- [ ] Biometric authentication (WebAuthn)

### Phase 3 (Low Priority)
- [ ] Magic link login
- [ ] Passwordless authentication
- [ ] Account recovery flow
- [ ] Security settings page

---

**Last Updated:** November 21, 2025
**Maintained By:** Design System Team
