# Design Guidelines - Agent Squad Frontend

**Last Updated:** November 21, 2025

## Animation System

### Core Easing Function
Use consistent easing for all animations:
```typescript
ease: [0.22, 1, 0.36, 1] // Smooth, professional cubic-bezier
```

### Standard Animation Variants

#### 1. Container Entrance (Staggered Children)
```typescript
const containerVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1],
      staggerChildren: 0.1, // Adjust based on content density
    },
  },
};
```

#### 2. Item Fade In
```typescript
const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1],
    },
  },
};
```

#### 3. Error Shake
```typescript
const shakeVariants = {
  shake: {
    x: [-10, 10, -10, 10, 0],
    transition: { duration: 0.4 },
  },
};

// Usage:
<motion.div
  variants={shakeVariants}
  animate={shouldShake ? 'shake' : ''}
>
```

#### 4. Success Spring
```typescript
const successVariants = {
  hidden: { scale: 0, rotate: -180 },
  visible: {
    scale: 1,
    rotate: 0,
    transition: {
      type: 'spring',
      stiffness: 200,
      damping: 15,
    },
  },
};
```

#### 5. Interactive Elements (Hover/Tap)
```typescript
<motion.div
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
  transition={{ duration: 0.2 }}
>
```

#### 6. Input Focus
```typescript
<motion.div
  whileFocus={{ scale: 1.01 }}
  transition={{ duration: 0.2 }}
>
```

## Typography

### Font Stack
- **Primary:** Geist Sans (configured via `next/font`)
- **Monospace:** Geist Mono

### Scale
- **Hero:** `text-5xl md:text-6xl lg:text-7xl` (3rem → 3.75rem → 4.5rem)
- **H1:** `text-3xl md:text-4xl` (1.875rem → 2.25rem)
- **H2:** `text-2xl md:text-3xl` (1.5rem → 1.875rem)
- **H3:** `text-xl md:text-2xl` (1.25rem → 1.5rem)
- **Body:** `text-base` (1rem)
- **Small:** `text-sm` (0.875rem)
- **Tiny:** `text-xs` (0.75rem)

### Weight
- **Bold:** `font-bold` (700) - Headings, emphasis
- **Semibold:** `font-semibold` (600) - Subheadings
- **Medium:** `font-medium` (500) - Labels, links
- **Normal:** `font-normal` (400) - Body text

### Line Height
- **Tight:** `leading-tight` (1.25) - Headings
- **Snug:** `leading-snug` (1.375) - Subheadings
- **Normal:** `leading-normal` (1.5) - Body text
- **Relaxed:** `leading-relaxed` (1.625) - Long-form content

## Color System

### Theme Variables
All colors use CSS custom properties defined in `globals.css`:

#### Light Mode
- `--background`: oklch(1 0 0) - Pure white
- `--foreground`: oklch(0.145 0 0) - Near black
- `--primary`: oklch(0.205 0 0) - Dark gray
- `--primary-foreground`: oklch(0.985 0 0) - Off white
- `--muted`: oklch(0.97 0 0) - Light gray
- `--muted-foreground`: oklch(0.556 0 0) - Medium gray
- `--border`: oklch(0.922 0 0) - Light border
- `--ring`: oklch(0.708 0 0) - Focus ring

#### Dark Mode
- `--background`: oklch(0.145 0 0) - Near black
- `--foreground`: oklch(0.985 0 0) - Off white
- `--primary`: oklch(0.922 0 0) - Light gray
- `--primary-foreground`: oklch(0.205 0 0) - Dark gray
- `--muted`: oklch(0.269 0 0) - Dark gray
- `--muted-foreground`: oklch(0.708 0 0) - Medium gray
- `--border`: oklch(1 0 0 / 10%) - Subtle border
- `--ring`: oklch(0.556 0 0) - Focus ring

### Usage
```tsx
// Background gradient (auth pages)
className="bg-gradient-to-br from-background via-background to-muted/20"

// Card with backdrop blur
className="bg-card/95 backdrop-blur-sm border-border/50"

// Muted text
className="text-muted-foreground"

// Interactive elements
className="text-primary hover:text-primary/80"
```

## Spacing

### 8px Grid System
All spacing uses multiples of 8px (Tailwind's 0.5rem units):

- `p-1` = 4px (0.5 unit)
- `p-2` = 8px (1 unit)
- `p-3` = 12px (1.5 units)
- `p-4` = 16px (2 units)
- `p-6` = 24px (3 units)
- `p-8` = 32px (4 units)
- `p-12` = 48px (6 units)
- `p-16` = 64px (8 units)

### Component Spacing
- **Between sections:** `space-y-6` (24px)
- **Between form fields:** `space-y-4` (16px)
- **Between related items:** `space-y-2` (8px)
- **Card padding:** `p-6` (24px)

## Responsive Design

### Breakpoints
- **Mobile:** 375px - 767px (default, no prefix)
- **Tablet:** 768px - 1279px (`md:`)
- **Desktop:** 1280px+ (`lg:`)
- **Wide:** 1920px+ (`xl:`)

### Mobile-First Approach
Always design for mobile first, then enhance for larger screens:

```tsx
<div className="
  w-full          // Mobile: full width
  md:max-w-2xl    // Tablet: constrained width
  lg:max-w-4xl    // Desktop: larger constraint
">
```

### Touch Targets
Minimum 44x44px for all interactive elements:
```tsx
<Button className="min-h-[44px]">Click me</Button>
<Input className="min-h-[44px]" />
```

## Accessibility

### Focus Indicators
- Use visible focus rings: `focus:ring-2 focus:ring-ring focus:ring-offset-2`
- Outline set globally: `outline-ring/50`

### ARIA Labels
```tsx
<button
  aria-label="Show password"
  aria-pressed={showPassword}
>
  <Eye className="h-4 w-4" />
</button>
```

### Color Contrast
- Text: Minimum 4.5:1 ratio (WCAG AA)
- Large text: Minimum 3:1 ratio
- Test with dark mode enabled

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Logical tab order
- Enter/Space for activation
- Escape for dismissal

### Screen Readers
- Semantic HTML (`<button>`, `<nav>`, `<main>`)
- Form labels with `<FormLabel>` from shadcn/ui
- Error messages announced via `<FormMessage>`
- Status updates with `aria-live` regions

## Component Patterns

### Form Fields
```tsx
<FormField
  control={form.control}
  name="fieldName"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Label</FormLabel>
      <FormControl>
        <div className="relative">
          <Icon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <motion.div whileFocus={{ scale: 1.01 }} transition={{ duration: 0.2 }}>
            <Input
              type="text"
              placeholder="Placeholder"
              className="pl-10 min-h-[44px]"
              {...field}
            />
          </motion.div>
        </div>
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Buttons
```tsx
<motion.div
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
  transition={{ duration: 0.2 }}
>
  <Button className="w-full min-h-[44px]">
    {isLoading ? (
      <>
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading...
      </>
    ) : (
      'Submit'
    )}
  </Button>
</motion.div>
```

### Cards
```tsx
<Card className="border-border/50 shadow-xl backdrop-blur-sm bg-card/95">
  <CardContent className="pt-6">
    {/* Content */}
  </CardContent>
</Card>
```

### Loading Skeletons
```tsx
<div className="space-y-4">
  <Skeleton className="h-8 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
  <Skeleton className="h-11 w-full" />
</div>
```

## Icons

### Library
Use `lucide-react` for all icons:

```tsx
import { Mail, Lock, Eye, EyeOff, Loader2, CheckCircle2 } from 'lucide-react';

// Standard size: h-4 w-4 (16px)
<Mail className="h-4 w-4 text-muted-foreground" />

// Large size: h-5 w-5 (20px)
<CheckCircle2 className="h-5 w-5" />
```

### Placement
- **Input icons:** Left side, 12px from edge
- **Button icons:** Left side with 8px margin
- **Toggle buttons:** Centered in 44x44px container

## Toast Notifications

### Configuration
Using `sonner` (shadcn/ui integration):

```tsx
import { toast } from 'sonner';

// Success
toast.success('Title', {
  description: 'Description text',
  icon: <CheckCircle2 className="h-4 w-4" />,
});

// Error
toast.error('Title', {
  description: 'Error message',
});

// Custom
toast('Title', {
  description: 'Custom message',
  icon: <Icon className="h-4 w-4" />,
});
```

## Loading States

### Inline Loading
```tsx
{isLoading ? (
  <>
    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
    Loading text...
  </>
) : (
  'Normal text'
)}
```

### Skeleton Loading
Use `<Skeleton>` component for content loading states.

### Suspense Boundaries
```tsx
<Suspense fallback={<LoadingSkeleton />}>
  <Component />
</Suspense>
```

## Error Handling

### Form Validation
- Inline errors via `<FormMessage>`
- Shake animation on form-level errors
- Red border on invalid fields

### API Errors
- Toast notifications for user-facing errors
- Error boundaries for critical failures
- Fallback UI for graceful degradation

## Performance

### Animation Optimization
- Use `transform` and `opacity` for hardware acceleration
- Avoid animating `width`, `height`, `top`, `left`
- Use `will-change` sparingly

### Code Splitting
- Lazy load heavy components
- Use Suspense boundaries
- Dynamic imports for routes

### Bundle Size
- Import icons individually: `import { Icon } from 'lucide-react'`
- Avoid importing entire libraries
- Monitor bundle size with `bun run build`

## Testing

### Checklist for New Components
- [ ] Responsive across all breakpoints
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Touch targets meet 44px minimum
- [ ] Color contrast meets WCAG AA
- [ ] Dark mode styled correctly
- [ ] Loading states implemented
- [ ] Error states handled
- [ ] Animations perform smoothly
- [ ] No layout shift during load

## Future Enhancements

### Planned Features
1. Password strength indicator
2. Social authentication UI
3. Multi-factor authentication flow
4. Forgot password/reset password
5. Email verification UI
6. Account settings pages
7. Profile management

### Animation Library
Consider building reusable animation components:
- `<FadeIn>` - Standard fade in
- `<SlideIn>` - Slide in from direction
- `<Stagger>` - Stagger children
- `<Shake>` - Error shake
- `<Success>` - Success animation

## Resources

- [Framer Motion Docs](https://www.framer.com/motion/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)

---

**Note:** This document should be updated as new patterns emerge. Always consult this guide before implementing new UI components.
