/**
 * List of notes component.
 */
import { useNotes, useDeleteNote } from '../../hooks/useNotes';
import { Trash2, AlertCircle, RefreshCw } from 'lucide-react';
import type { Note } from '../../types/note';

interface NotesListProps {
  onSelectNote: (note: Note) => void;
  selectedNoteId?: string;
}

function NotesList({ onSelectNote, selectedNoteId }: NotesListProps) {
  const { data, isLoading, error, refetch } = useNotes();
  const deleteNote = useDeleteNote();

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
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">
          No notes yet. Create your first note!
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="divide-y divide-gray-200">
        {data.notes.map((note) => (
          <div
            key={note.id}
            onClick={() => onSelectNote(note)}
            className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
              selectedNoteId === note.id ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {note.title}
                </h3>
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                  {note.content}
                </p>
                {note.tags && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {note.tags.split(',').map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                      >
                        {tag.trim()}
                      </span>
                    ))}
                  </div>
                )}
                <p className="mt-2 text-xs text-gray-500">
                  {new Date(note.updated_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => handleDelete(e, note.id)}
                className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                disabled={deleteNote.isPending}
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NotesList;
