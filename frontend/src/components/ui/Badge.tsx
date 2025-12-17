/**
 * Badge Component - Knowledge Garden Design System
 *
 * Provides status badges and tags with different color variants
 * for categorization and status indication.
 */

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple' | 'amber';
  size?: 'sm' | 'md' | 'lg';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center font-semibold border transition-colors';

    const variants = {
      default: 'bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border-stone-200 dark:border-stone-700',
      success: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
      warning: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800',
      error: 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800',
      info: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800',
      purple: 'bg-lavender-50 dark:bg-lavender-900/20 text-lavender-700 dark:text-lavender-400 border-lavender-200 dark:border-lavender-800',
      amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs rounded-md',
      md: 'px-2.5 py-1 text-xs rounded-md',
      lg: 'px-3 py-1.5 text-sm rounded-lg',
    };

    return (
      <span
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: 'active' | 'inactive' | 'pending' | 'completed';
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ className, status, size = 'md', ...props }, ref) => {
    const statusConfig = {
      active: { variant: 'success' as const, icon: '✓', label: 'Active' },
      inactive: { variant: 'default' as const, icon: '○', label: 'Inactive' },
      pending: { variant: 'warning' as const, icon: '◷', label: 'Pending' },
      completed: { variant: 'success' as const, icon: '✓', label: 'Completed' },
    };

    const config = statusConfig[status];

    return (
      <Badge ref={ref} variant={config.variant} size={size} className={className} {...props}>
        <span className="mr-1">{config.icon}</span>
        {config.label}
      </Badge>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';
