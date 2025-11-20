/**
 * Badge Component (shadcn/ui style)
 */
import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'secondary' | 'destructive';
  children: React.ReactNode;
}

export function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
        {
          'bg-gray-100 text-gray-800': variant === 'default',
          'border border-gray-300 bg-transparent': variant === 'outline',
          'bg-gray-100 text-gray-900': variant === 'secondary',
          'bg-red-100 text-red-800': variant === 'destructive',
        },
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

