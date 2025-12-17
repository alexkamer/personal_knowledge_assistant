/**
 * Card Component - Knowledge Garden Design System
 *
 * Provides standard, glass, and gradient card variants
 * for different use cases (content containers, floating elements, learning tools).
 */

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'standard' | 'glass' | 'gradient';
  hoverable?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'standard', hoverable = false, children, ...props }, ref) => {
    const baseStyles = 'rounded-xl';

    const variants = {
      standard: 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm',
      glass: 'bg-white/80 dark:bg-stone-900/70 backdrop-blur-xl backdrop-saturate-150 border border-white/20 dark:border-stone-800/50 shadow-xl',
      gradient: 'bg-gradient-to-br from-indigo-50 to-lavender-50 dark:from-indigo-900/20 dark:to-lavender-900/20 border border-indigo-200 dark:border-indigo-800 shadow-sm',
    };

    const hoverStyles = hoverable ? 'transition-all duration-200 hover:shadow-md hover:scale-[1.02]' : '';

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          hoverStyles,
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-2xl font-semibold leading-none tracking-tight text-stone-900 dark:text-white', className)}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-stone-500 dark:text-stone-400', className)}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center p-6 pt-0', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';
