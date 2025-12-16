/**
 * RelatedNotesPanel - Shows semantically similar notes using vector embeddings
 */
import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

interface RelatedNote {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  similarity_score: number;
}

interface RelatedNotesPanelProps {
  noteId: string;
  onNavigate: (noteId: string) => void;
}

export function RelatedNotesPanel({ noteId, onNavigate }: RelatedNotesPanelProps) {
  const [relatedNotes, setRelatedNotes] = useState<RelatedNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRelatedNotes = async () => {
      if (!noteId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/notes/${noteId}/related?limit=5`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch related notes');
        }

        const data = await response.json();
        setRelatedNotes(data.related_notes || []);
      } catch (err) {
        console.error('Error fetching related notes:', err);
        setError('Failed to load related notes');
      } finally {
        setLoading(false);
      }
    };

    fetchRelatedNotes();
  }, [noteId]);

  if (loading) {
    return (
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Sparkles size={16} className="text-purple-600" />
          Related Notes
        </h3>
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Sparkles size={16} className="text-purple-600" />
          Related Notes
        </h3>
        <p className="text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (relatedNotes.length === 0) {
    return (
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Sparkles size={16} className="text-purple-600" />
          Related Notes
        </h3>
        <p className="text-sm text-gray-500 italic">No semantically related notes found.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 pt-6 border-t border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <Sparkles size={16} className="text-purple-600" />
        Related Notes ({relatedNotes.length})
      </h3>
      <p className="text-xs text-gray-500 mb-3">
        Discovered by AI based on semantic similarity
      </p>
      <div className="space-y-2">
        {relatedNotes.map((relatedNote) => (
          <button
            key={relatedNote.id}
            onClick={() => onNavigate(relatedNote.id)}
            className="w-full text-left px-3 py-2 rounded-md hover:bg-purple-50 transition-colors group flex items-start gap-2"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 group-hover:text-purple-700 truncate">
                {relatedNote.title}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-xs text-gray-500">
                  {Math.round(relatedNote.similarity_score * 100)}% similar
                </p>
                <span className="text-xs text-gray-300">•</span>
                <p className="text-xs text-gray-500">
                  Updated {new Date(relatedNote.updated_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
