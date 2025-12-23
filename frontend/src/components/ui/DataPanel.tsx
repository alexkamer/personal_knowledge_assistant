/**
 * DataPanel - Professional panel component for clean, minimalist interface
 * Provides default and highlight variants with subtle styling
 */
import { ReactNode } from 'react';

interface DataPanelProps {
  children: ReactNode;
  variant?: 'default' | 'highlight' | 'danger';
  className?: string;
}

export function DataPanel({
  children,
  variant = 'default',
  className = '',
}: DataPanelProps) {
  // Base styles for all panels
  const baseStyles = 'relative backdrop-blur-md transition-all duration-200 rounded-lg';

  // Variant-specific styles
  const variantStyles = {
    default: 'bg-gray-900/80 border border-gray-700',
    highlight: 'bg-gray-900/80 border-2 border-primary-500',
    danger: 'bg-gray-900/80 border-2 border-danger-500',
  };

  return (
    <div
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

// Sub-components for structured content
interface DataPanelHeaderProps {
  children: ReactNode;
  className?: string;
}

export function DataPanelHeader({ children, className = '' }: DataPanelHeaderProps) {
  return (
    <div className={`px-6 py-4 border-b border-gray-700 ${className}`}>
      {children}
    </div>
  );
}

interface DataPanelTitleProps {
  children: ReactNode;
  glowing?: boolean;
  className?: string;
}

export function DataPanelTitle({ children, glowing = false, className = '' }: DataPanelTitleProps) {
  return (
    <h3
      className={`
        text-lg font-semibold
        ${glowing ? 'text-primary-500' : 'text-white'}
        ${className}
      `}
    >
      {children}
    </h3>
  );
}

interface DataPanelContentProps {
  children: ReactNode;
  className?: string;
}

export function DataPanelContent({ children, className = '' }: DataPanelContentProps) {
  return <div className={`px-6 py-4 ${className}`}>{children}</div>;
}

interface DataPanelFooterProps {
  children: ReactNode;
  className?: string;
}

export function DataPanelFooter({ children, className = '' }: DataPanelFooterProps) {
  return (
    <div className={`px-6 py-4 border-t border-gray-700 ${className}`}>
      {children}
    </div>
  );
}
