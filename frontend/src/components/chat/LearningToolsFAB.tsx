/**
 * Floating Action Button for Learning Tools - Knowledge Garden Design System
 *
 * Modern FAB with expandable menu for learning features.
 */
import { useState } from 'react';
import { Lightbulb, Brain, BookOpen, Clock, Sparkles, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LearningToolsFABProps {
  onDetectGaps: () => void;
  onGenerateQuiz: () => void;
  onCaptureSnapshot: () => void;
  onViewTimeline: () => void;
  isLoadingQuiz?: boolean;
  isLoadingSnapshot?: boolean;
  disabled?: boolean;
}

export function LearningToolsFAB({
  onDetectGaps,
  onGenerateQuiz,
  onCaptureSnapshot,
  onViewTimeline,
  isLoadingQuiz = false,
  isLoadingSnapshot = false,
  disabled = false,
}: LearningToolsFABProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const tools = [
    {
      id: 'gaps',
      label: 'Learning Gaps',
      icon: Lightbulb,
      onClick: onDetectGaps,
      gradient: 'from-orange-500 to-yellow-500',
      hoverGradient: 'hover:from-orange-600 hover:to-yellow-600',
      disabled: false,
    },
    {
      id: 'quiz',
      label: 'Quiz Me',
      icon: Brain,
      onClick: onGenerateQuiz,
      gradient: 'from-purple-500 to-blue-500',
      hoverGradient: 'hover:from-purple-600 hover:to-blue-600',
      disabled: isLoadingQuiz,
    },
    {
      id: 'snapshot',
      label: 'Snapshot',
      icon: BookOpen,
      onClick: onCaptureSnapshot,
      gradient: 'from-green-500 to-teal-500',
      hoverGradient: 'hover:from-green-600 hover:to-teal-600',
      disabled: isLoadingSnapshot,
    },
    {
      id: 'timeline',
      label: 'Timeline',
      icon: Clock,
      onClick: onViewTimeline,
      gradient: 'from-indigo-500 to-purple-500',
      hoverGradient: 'hover:from-indigo-600 hover:to-purple-600',
      disabled: false,
    },
  ];

  return (
    <div className="fixed bottom-24 right-8 z-20">
      {/* Expanded Menu */}
      {isExpanded && (
        <div className="mb-4 space-y-3 animate-slide-in-bottom">
          {tools.map((tool, index) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => {
                  if (!tool.disabled && !disabled) {
                    tool.onClick();
                    setIsExpanded(false);
                  }
                }}
                disabled={tool.disabled || disabled}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg transition-all duration-200",
                  "bg-gradient-to-r text-white",
                  tool.gradient,
                  tool.hoverGradient,
                  "hover:shadow-xl hover:scale-105",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
                  "group"
                )}
                style={{
                  animationDelay: `${index * 50}ms`,
                }}
              >
                <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/30 transition-colors">
                  <Icon size={20} />
                </div>
                <span className="font-medium text-sm pr-2">{tool.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Main FAB Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        className={cn(
          "w-14 h-14 rounded-full shadow-2xl transition-all duration-300",
          "flex items-center justify-center",
          "bg-gradient-to-br from-indigo-500 to-purple-600",
          "hover:from-indigo-600 hover:to-purple-700",
          "hover:shadow-glow hover:scale-110",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
          "group relative"
        )}
        title={isExpanded ? "Close learning tools" : "Open learning tools"}
      >
        {/* Icon with rotation animation */}
        <div
          className={cn(
            "transition-transform duration-300",
            isExpanded ? "rotate-45" : "rotate-0"
          )}
        >
          {isExpanded ? (
            <X size={24} className="text-white" />
          ) : (
            <Sparkles size={24} className="text-white" />
          )}
        </div>

        {/* Pulse animation when not expanded */}
        {!isExpanded && (
          <div className="absolute inset-0 rounded-full bg-primary-400 animate-ping opacity-20" />
        )}
      </button>
    </div>
  );
}
