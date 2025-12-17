/**
 * BacklinksPanel - Shows notes that link to the current note
 */
import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';

interface Backlink {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface BacklinksPanelProps {
  noteId: string;
  onNavigate: (noteId: string) => void;
}

export function BacklinksPanel({ noteId, onNavigate }: BacklinksPanelProps) {
  const [backlinks, setBacklinks] = useState<Backlink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBacklinks = async () => {
      if (!noteId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/notes/${noteId}/backlinks`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch backlinks');
        }

        const data = await response.json();
        setBacklinks(data.backlinks || []);
      } catch (err) {
        console.error('Error fetching backlinks:', err);
        setError('Failed to load backlinks');
      } finally {
        setLoading(false);
      }
    };

    fetchBacklinks();
  }, [noteId]);

  if (loading) {
    return (
      <div className="mt-6 pt-6 border-t border-stone-200">
        <h3 className="text-sm font-semibold text-stone-700 mb-3">Linked References</h3>
        <p className="text-sm text-stone-500">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6 pt-6 border-t border-stone-200">
        <h3 className="text-sm font-semibold text-stone-700 mb-3">Linked References</h3>
        <p className="text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (backlinks.length === 0) {
    return (
      <div className="mt-6 pt-6 border-t border-stone-200">
        <h3 className="text-sm font-semibold text-stone-700 mb-3">Linked References</h3>
        <p className="text-sm text-stone-500 italic">No other notes link to this note yet.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 pt-6 border-t border-stone-200">
      <h3 className="text-sm font-semibold text-stone-700 mb-3">
        Linked References ({backlinks.length})
      </h3>
      <div className="space-y-2">
        {backlinks.map((backlink) => (
          <button
            key={backlink.id}
            onClick={() => onNavigate(backlink.id)}
            className="w-full text-left px-3 py-2 rounded-md hover:bg-blue-50 transition-colors group flex items-center gap-2"
          >
            <ArrowLeft size={14} className="text-stone-400 group-hover:text-blue-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-stone-900 group-hover:text-blue-700 truncate">
                {backlink.title}
              </p>
              <p className="text-xs text-stone-500">
                Updated {new Date(backlink.updated_at).toLocaleDateString()}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
