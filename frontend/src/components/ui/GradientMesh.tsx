/**
 * Gradient Mesh Background - Knowledge Garden Design System
 *
 * Animated gradient background for the chat page.
 * Creates a subtle, moving gradient mesh using indigo, lavender, and amber colors.
 */

import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface GradientMeshProps extends HTMLAttributes<HTMLDivElement> {
  animated?: boolean;
}

export function GradientMesh({ className, animated = true, ...props }: GradientMeshProps) {
  return (
    <div
      className={cn(
        'fixed inset-0 -z-10 overflow-hidden',
        className
      )}
      {...props}
    >
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-lavender-50 to-amber-50 dark:from-stone-950 dark:via-indigo-950/50 dark:to-stone-950" />

      {/* Animated gradient orbs */}
      {animated && (
        <>
          {/* Indigo orb (top-left) */}
          <div
            className="absolute w-[600px] h-[600px] -top-48 -left-48 bg-gradient-radial from-indigo-200/40 via-indigo-100/20 to-transparent dark:from-indigo-900/30 dark:via-indigo-950/15 dark:to-transparent rounded-full blur-3xl animate-float-slow"
            style={{
              animation: 'float-slow 20s ease-in-out infinite',
            }}
          />

          {/* Lavender orb (top-right) */}
          <div
            className="absolute w-[500px] h-[500px] -top-32 -right-32 bg-gradient-radial from-lavender-200/40 via-lavender-100/20 to-transparent dark:from-lavender-900/30 dark:via-lavender-950/15 dark:to-transparent rounded-full blur-3xl animate-float-medium"
            style={{
              animation: 'float-medium 15s ease-in-out infinite',
              animationDelay: '2s',
            }}
          />

          {/* Amber orb (bottom-center) */}
          <div
            className="absolute w-[450px] h-[450px] -bottom-24 left-1/2 -translate-x-1/2 bg-gradient-radial from-amber-200/30 via-amber-100/15 to-transparent dark:from-amber-900/25 dark:via-amber-950/10 dark:to-transparent rounded-full blur-3xl animate-float-fast"
            style={{
              animation: 'float-fast 12s ease-in-out infinite',
              animationDelay: '4s',
            }}
          />
        </>
      )}

      {/* Noise texture overlay for subtle grain */}
      <div
        className="absolute inset-0 opacity-[0.015] dark:opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' /%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}

// Add custom animations to global CSS
// These will be added via Tailwind config
