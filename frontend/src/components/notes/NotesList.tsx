/**
 * List of notes component.
 */
import { useState, useMemo, useRef, useEffect } from 'react';
import { useDeleteNote, useUpdateNote } from '../../hooks/useNotes';
import { MoreVertical, Search, FileText } from 'lucide-react';
import type { Note } from '../../types/note';

interface NotesListProps {
  notes: Note[];
  onSelectNote: (note: Note) => void;
  selectedNoteId?: string;
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

function NotesList({ notes, onSelectNote, selectedNoteId }: NotesListProps) {
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
    if (!notes) return [];

    if (!searchQuery.trim()) return notes;

    const query = searchQuery.toLowerCase();
    return notes.filter((note) =>
      note.title.toLowerCase().includes(query) ||
      note.content.toLowerCase().includes(query) ||
      note.tags_rel.some((tag) => tag.name.toLowerCase().includes(query))
    );
  }, [notes, searchQuery]);

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

  // Notes are now passed as props, so no loading/error states here
  // Parent component handles those states

  return (
    <div className="space-y-3">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" size={18} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search notes by title, content, or tags..."
          className="w-full pl-10 pr-4 py-2.5 bg-white/90 dark:bg-gray-800/90 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-xl text-gray-900 dark:text-white placeholder-stone-500 dark:placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm transition-all"
        />
      </div>

      {/* Notes List */}
      <div className="space-y-3">
        {filteredNotes.length === 0 ? (
          <div className="bg-white/90 dark:bg-gray-900/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-800/50 rounded-2xl shadow-lg p-8 text-center">
            <Search size={32} className="mx-auto text-gray-300 dark:text-gray-600 mb-2" />
            <p className="text-gray-500 dark:text-gray-400">No notes match your search</p>
          </div>
        ) : (
          filteredNotes.map((note) => (
              <div
                key={note.id}
                onClick={() => onSelectNote(note)}
                className={`p-5 cursor-pointer transition-all duration-200 rounded-2xl shadow-lg hover:shadow-xl animate-slide-in-left ${
                  selectedNoteId === note.id
                    ? 'bg-primary-500 text-white scale-[1.02]'
                    : 'bg-white/90 dark:bg-gray-900/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-800/50 hover:scale-[1.01]'
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
                      <h3 className={`text-lg font-semibold truncate mb-1 ${
                        selectedNoteId === note.id
                          ? 'text-white'
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {note.title}
                      </h3>
                    )}
                    <p className={`text-sm line-clamp-2 leading-relaxed ${
                      selectedNoteId === note.id
                        ? 'text-primary-100'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {extractPreviewText(note.content)}
                    </p>
                    {note.tags_rel && note.tags_rel.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {note.tags_rel.map((tag) => (
                          <span
                            key={tag.id}
                            className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                              selectedNoteId === note.id
                                ? 'bg-white/20 text-white backdrop-blur-sm'
                                : 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                            }`}
                          >
                            #{tag.name}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className={`mt-3 text-xs font-medium ${
                      selectedNoteId === note.id
                        ? 'text-primary-200'
                        : 'text-gray-500 dark:text-gray-500'
                    }`}>
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
                      className={`p-2 rounded-lg transition-colors ${
                        selectedNoteId === note.id
                          ? 'text-white hover:bg-white/20'
                          : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                      title="More options"
                    >
                      <MoreVertical size={18} />
                    </button>

                    {openMenuId === note.id && (
                      <div className="absolute right-0 top-full mt-1 w-32 bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl border border-gray-700 rounded-xl shadow-xl z-10">
                        <button
                          onClick={(e) => handleEdit(e, note)}
                          className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-xl transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, note.id)}
                          className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-b-xl transition-colors"
                          disabled={deleteNote.isPending}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}

export default NotesList;
