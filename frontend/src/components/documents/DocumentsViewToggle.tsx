/**
 * View toggle component for switching between list and grid views
 */
import { Grid3x3, List } from 'lucide-react';

interface DocumentsViewToggleProps {
  view: 'list' | 'grid';
  onViewChange: (view: 'list' | 'grid') => void;
}

export function DocumentsViewToggle({ view, onViewChange }: DocumentsViewToggleProps) {
  return (
    <div className="flex items-center gap-1 glass rounded-lg p-1">
      <button
        onClick={() => onViewChange('list')}
        className={`
          p-2 rounded-md transition-all duration-200 spring-scale
          ${view === 'list'
            ? 'bg-primary-500 text-white elevated'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }
        `}
        title="List view"
      >
        <List size={18} />
      </button>
      <button
        onClick={() => onViewChange('grid')}
        className={`
          p-2 rounded-md transition-all duration-200 spring-scale
          ${view === 'grid'
            ? 'bg-primary-500 text-white elevated'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }
        `}
        title="Grid view"
      >
        <Grid3x3 size={18} />
      </button>
    </div>
  );
}
