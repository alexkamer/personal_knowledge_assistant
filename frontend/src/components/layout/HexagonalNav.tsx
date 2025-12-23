/**
 * Sidebar Navigation - Clean, professional vertical navigation
 * Inspired by Linear and Vercel's minimalist aesthetic
 */
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Search, StickyNote, FileText, Youtube, Settings } from 'lucide-react';
import { useState } from 'react';

interface NavMode {
  path: string;
  icon: typeof MessageSquare;
  label: string;
  description: string;
}

const navModes: NavMode[] = [
  {
    path: '/chat',
    icon: MessageSquare,
    label: 'Chat',
    description: 'Ask questions and get AI-powered answers from your knowledge base'
  },
  {
    path: '/research',
    icon: Search,
    label: 'Research',
    description: 'Run one-time web research tasks to gather information on any topic'
  },
  {
    path: '/notes',
    icon: StickyNote,
    label: 'Notes',
    description: 'Create and manage personal notes in your knowledge base'
  },
  {
    path: '/documents',
    icon: FileText,
    label: 'Documents',
    description: 'Upload and manage documents (PDF, Word, Markdown, etc.)'
  },
  {
    path: '/youtube',
    icon: Youtube,
    label: 'YouTube',
    description: 'Add YouTube videos and extract transcripts to your knowledge base'
  },
  {
    path: '/settings',
    icon: Settings,
    label: 'Settings',
    description: 'Configure application settings and preferences'
  },
];

export function HexagonalNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  const [hoveredMode, setHoveredMode] = useState<string | null>(null);

  return (
    <div className="fixed left-0 top-0 h-screen w-20 bg-gray-900 border-r border-gray-700 flex flex-col items-center py-6 z-50">
      {/* Logo/Brand Area */}
      <div className="mb-8 flex flex-col items-center">
        <div className="w-10 h-10 rounded-lg bg-primary-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
          K
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 flex flex-col gap-2 w-full px-2">
        {navModes.map((mode) => {
          const isActive = currentPath === mode.path;
          const Icon = mode.icon;

          return (
            <div key={mode.path} className="relative">
              <button
                onClick={() => navigate(mode.path)}
                onMouseEnter={() => setHoveredMode(mode.path)}
                onMouseLeave={() => setHoveredMode(null)}
                className={`
                  relative group
                  w-full py-3 px-3
                  rounded-lg
                  transition-all duration-150
                  ${
                    isActive
                      ? 'bg-primary-500 text-white shadow-md'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }
                `}
              >
                <div className="flex flex-col items-center gap-1">
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="text-[9px] font-medium tracking-wide">
                    {mode.label}
                  </span>
                </div>

                {/* Active indicator - simple left border */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
                )}
              </button>

              {/* Tooltip on hover */}
              {hoveredMode === mode.path && (
                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50 pointer-events-none">
                  <div className="bg-gray-800 text-white px-3 py-2 rounded-lg shadow-lg border border-gray-700 min-w-[200px] max-w-[250px]">
                    <div className="font-semibold text-sm mb-1">{mode.label}</div>
                    <div className="text-xs text-gray-300">{mode.description}</div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Bottom indicator - connection status */}
      <div className="mt-auto pt-4 border-t border-gray-700 w-8">
        <div className="w-2 h-2 rounded-full bg-success-500 mx-auto" />
      </div>
    </div>
  );
}
