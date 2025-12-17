/**
 * List of notes component.
 */
import { useState, useMemo, useRef, useEffect } from 'react';
import { useNotes, useDeleteNote, useUpdateNote } from '../../hooks/useNotes';
import { MoreVertical, AlertCircle, RefreshCw, Search, FileText } from 'lucide-react';
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
  const updateNote = useUpdateNote();
  const [searchQuery, setSearchQuery] = useState('');
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);
  const editInputRef = useRef<HTMLInputElement>(null);

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

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when editing starts
  useEffect(() => {
    if (editingNoteId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingNoteId]);

  const handleMenuToggle = (e: React.MouseEvent, noteId: string) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === noteId ? null : noteId);
  };

  const handleEdit = (e: React.MouseEvent, note: Note) => {
    e.stopPropagation();
    setEditingNoteId(note.id);
    setEditTitle(note.title);
    setOpenMenuId(null);
  };

  const handleSaveEdit = async (e: React.FormEvent, note: Note) => {
    e.preventDefault();
    e.stopPropagation();

    if (!editTitle.trim()) {
      setEditTitle(note.title); // Reset to original
      setEditingNoteId(null);
      return;
    }

    try {
      await updateNote.mutateAsync({
        id: note.id,
        data: {
          title: editTitle.trim(),
        },
      });
      setEditingNoteId(null);
    } catch (error) {
      console.error('Failed to update note title:', error);
      setEditTitle(note.title); // Reset to original
      setEditingNoteId(null);
    }
  };

  const handleCancelEdit = (e: React.MouseEvent, originalTitle: string) => {
    e.stopPropagation();
    setEditTitle(originalTitle);
    setEditingNoteId(null);
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setOpenMenuId(null);
    if (window.confirm('Are you sure you want to delete this note?')) {
      await deleteNote.mutateAsync(id);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-stone-500">Loading notes...</div>
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
          <p className="text-sm text-stone-600 text-center">
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
        <FileText size={48} className="mx-auto text-stone-300 mb-3" />
        <p className="text-stone-500 text-lg font-medium">
          No notes yet. Create your first note!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-stone-400" size={18} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search notes by title, content, or tags..."
          className="w-full pl-10 pr-4 py-2.5 border-2 border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        />
      </div>

      {/* Notes List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden border border-stone-200">
        {filteredNotes.length === 0 ? (
          <div className="p-8 text-center">
            <Search size={32} className="mx-auto text-stone-300 mb-2" />
            <p className="text-stone-500">No notes match your search</p>
          </div>
        ) : (
          <div className="divide-y divide-stone-200">
            {filteredNotes.map((note) => (
              <div
                key={note.id}
                onClick={() => onSelectNote(note)}
                className={`p-5 cursor-pointer transition-all ${
                  selectedNoteId === note.id
                    ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500'
                    : 'hover:bg-stone-50 border-l-4 border-transparent'
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div className="flex-1 min-w-0">
                    {editingNoteId === note.id ? (
                      <form onSubmit={(e) => handleSaveEdit(e, note)} className="mb-1">
                        <input
                          ref={editInputRef}
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onBlur={(e) => {
                            // Convert blur to form submission
                            const form = e.currentTarget.form;
                            if (form) {
                              form.requestSubmit();
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Escape') {
                              handleCancelEdit(e as any, note.title);
                            }
                          }}
                          className="w-full px-2 py-1 text-lg font-semibold border-2 border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </form>
                    ) : (
                      <h3 className="text-lg font-semibold text-stone-900 truncate mb-1">
                        {note.title}
                      </h3>
                    )}
                    <p className="text-sm text-stone-600 line-clamp-2 leading-relaxed">
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
                    <p className="mt-3 text-xs text-stone-500 font-medium">
                      Updated {new Date(note.updated_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </p>
                  </div>

                  {/* Three-dot menu */}
                  <div className="relative flex-shrink-0" ref={openMenuId === note.id ? menuRef : null}>
                    <button
                      onClick={(e) => handleMenuToggle(e, note.id)}
                      className="p-2 text-stone-500 hover:bg-stone-100 rounded-lg transition-colors"
                      title="More options"
                    >
                      <MoreVertical size={18} />
                    </button>

                    {openMenuId === note.id && (
                      <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-stone-200 rounded-lg shadow-lg z-10">
                        <button
                          onClick={(e) => handleEdit(e, note)}
                          className="w-full px-4 py-2 text-left text-sm text-stone-700 hover:bg-stone-100 rounded-t-lg transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, note.id)}
                          className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-b-lg transition-colors"
                          disabled={deleteNote.isPending}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
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
