/**
 * Button Component - Knowledge Garden Design System
 *
 * Provides primary, secondary, ghost, and icon button variants
 * with consistent styling and animations.
 */

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 spring-scale disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';

    const variants = {
      primary: 'bg-primary-500 hover:bg-primary-600 text-white elevated hover:elevated-lg ripple',
      secondary: 'bg-gray-800 hover:bg-gray-750 text-gray-300 border border-gray-700 ripple',
      ghost: 'text-gray-400 hover:bg-gray-800',
      icon: 'text-gray-400 hover:bg-gray-800 rounded-lg',
    };

    const sizes = {
      sm: variant === 'icon' ? 'p-1.5' : 'px-3 py-1.5 text-sm',
      md: variant === 'icon' ? 'p-2' : 'px-4 py-2 text-base',
      lg: variant === 'icon' ? 'p-3' : 'px-6 py-3 text-lg',
    };

    const roundedStyles = {
      primary: 'rounded-lg',
      secondary: 'rounded-lg',
      ghost: 'rounded-md',
      icon: 'rounded-lg',
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          roundedStyles[variant],
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
            Loading...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
