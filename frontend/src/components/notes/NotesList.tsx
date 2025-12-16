/**
 * List of notes component.
 */
import { useState, useMemo } from 'react';
import { useNotes, useDeleteNote } from '../../hooks/useNotes';
import { Trash2, AlertCircle, RefreshCw, Search, FileText } from 'lucide-react';
import type { Note } from '../../types/note';

interface NotesListProps {
  onSelectNote: (note: Note) => void;
  selectedNoteId?: string;
  selectedTags?: string[];
}

// Helper function to extract readable text preview from content
function extractPreviewText(content: string, maxLength: number = 150): string {
  if (!content || content.trim() === '') return 'Empty note';

  try {
    // Try parsing as Lexical JSON format
    const parsed = JSON.parse(content);

    if (parsed.root && parsed.root.children) {
      // Lexical format - extract text from nodes
      let text = '';
      const extractTextFromNode = (node: any): string => {
        if (node.type === 'text') {
          return node.text || '';
        }
        if (node.children && Array.isArray(node.children)) {
          return node.children.map(extractTextFromNode).join(' ');
        }
        return '';
      };

      text = parsed.root.children.map(extractTextFromNode).join(' ');
      return text.trim().substring(0, maxLength) || 'Empty note';
    } else if (Array.isArray(parsed)) {
      // Old block format - extract text from blocks
      const text = parsed
        .map((block: any) => block.content || '')
        .join(' ')
        .trim();
      return text.substring(0, maxLength) || 'Empty note';
    }
  } catch {
    // If not JSON, treat as plain text
    return content.substring(0, maxLength);
  }

  return content.substring(0, maxLength);
}

function NotesList({ onSelectNote, selectedNoteId, selectedTags }: NotesListProps) {
  const { data, isLoading, error, refetch } = useNotes(selectedTags);
  const deleteNote = useDeleteNote();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter notes by search query
  const filteredNotes = useMemo(() => {
    if (!data?.notes) return [];

    if (!searchQuery.trim()) return data.notes;

    const query = searchQuery.toLowerCase();
    return data.notes.filter((note) =>
      note.title.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query) ||
      note.tags_rel.some((tag) => tag.name.toLowerCase().includes(query))
    );
  }, [data?.notes, searchQuery]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation(); // Prevent selecting note when clicking delete
    if (window.confirm('Are you sure you want to delete this note?')) {
      await deleteNote.mutateAsync(id);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">Loading notes...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle size={20} />
            <span className="font-medium">Failed to load notes</span>
          </div>
          <p className="text-sm text-gray-600 text-center">
            {(error as any)?.response?.data?.detail || error.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.notes.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <FileText size={48} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500 text-lg font-medium">
          No notes yet. Create your first note!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search notes by title, content, or tags..."
          className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        />
      </div>

      {/* Notes List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
        {filteredNotes.length === 0 ? (
          <div className="p-8 text-center">
            <Search size={32} className="mx-auto text-gray-300 mb-2" />
            <p className="text-gray-500">No notes match your search</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredNotes.map((note) => (
              <div
                key={note.id}
                onClick={() => onSelectNote(note)}
                className={`p-5 cursor-pointer transition-all ${
                  selectedNoteId === note.id
                    ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500'
                    : 'hover:bg-gray-50 border-l-4 border-transparent'
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 truncate mb-1">
                      {note.title}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                      {extractPreviewText(note.content)}
                    </p>
                    {note.tags_rel && note.tags_rel.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {note.tags_rel.map((tag) => (
                          <span
                            key={tag.id}
                            className="px-2.5 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full"
                          >
                            #{tag.name}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="mt-3 text-xs text-gray-500 font-medium">
                      Updated {new Date(note.updated_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, note.id)}
                    className="flex-shrink-0 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors group"
                    disabled={deleteNote.isPending}
                    title="Delete note"
                  >
                    <Trash2 size={18} className="group-hover:scale-110 transition-transform" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default NotesList;
