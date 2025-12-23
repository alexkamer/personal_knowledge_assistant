/**
 * Input Component - Knowledge Garden Design System
 *
 * Provides text inputs and textareas with consistent styling
 * and focus states.
 */

import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, ...props }, ref) => {
    const baseStyles = 'w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border rounded-lg text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none transition-all duration-150';

    const borderStyles = error
      ? 'border-rose-500 focus:ring-2 focus:ring-rose-500'
      : 'border-gray-300 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:border-transparent';

    return (
      <input
        type={type}
        className={cn(
          baseStyles,
          borderStyles,
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    const baseStyles = 'w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border rounded-xl text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none resize-none transition-all duration-150';

    const borderStyles = error
      ? 'border-rose-500 focus:ring-2 focus:ring-rose-500'
      : 'border-gray-300 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:border-transparent';

    return (
      <textarea
        className={cn(
          baseStyles,
          borderStyles,
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';
