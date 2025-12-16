/**
 * Note create/edit form component - Outliner-based like RemNote
 * Auto-saves changes after 1 second of inactivity
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useCreateNote, useUpdateNote } from '../../hooks/useNotes';
import type { Note } from '../../types/note';
import { TagInput } from '../tags/TagInput';
import { LexicalOutlinerEditor } from './LexicalOutlinerEditor';
import { BacklinksPanel } from './BacklinksPanel';
import { RelatedNotesPanel } from './RelatedNotesPanel';

interface NoteFormProps {
  note: Note | null;
  onSave: () => void;
  onCancel: () => void;
  onNavigateToNote?: (noteId: string) => void;
}

function NoteForm({ note, onSave, onCancel, onNavigateToNote }: NoteFormProps) {
  const [content, setContent] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const noteIdRef = useRef<string | null>(null);

  const createNote = useCreateNote();
  const updateNote = useUpdateNote();

  // Track the current note ID to detect note changes
  const currentNoteIdRef = useRef<string | null>(null);

  // Load note data when editing
  useEffect(() => {
    if (note) {
      // Only update content if we're switching to a different note
      if (currentNoteIdRef.current !== note.id) {
        noteIdRef.current = note.id;
        currentNoteIdRef.current = note.id;
        setContent(note.content || '');
        setTags(note.tags_rel.map((tag) => tag.name));
      }
    } else {
      noteIdRef.current = null;
      currentNoteIdRef.current = null;
      setContent('');
      setTags([]);
    }
  }, [note]);

  // Auto-save function
  const saveNote = useCallback(async () => {
    // Check if there's any content
    if (!content || content.trim() === '' || content === '{}') {
      return; // Don't save empty notes
    }

    // Generate title from content (extract first text)
    let autoTitle = 'Untitled';
    try {
      const parsed = JSON.parse(content);
      if (parsed.root && parsed.root.children) {
        // Extract first text from Lexical editor state
        const firstChild = parsed.root.children[0];
        if (firstChild && firstChild.children && firstChild.children[0]) {
          const firstText = firstChild.children[0].text;
          if (firstText) {
            autoTitle = firstText.substring(0, 100);
          }
        }
      }
    } catch {
      // If not JSON, use as-is
      autoTitle = content.substring(0, 100);
    }

    try {
      setIsSaving(true);
      if (noteIdRef.current) {
        // Update existing note
        await updateNote.mutateAsync({
          id: noteIdRef.current,
          data: {
            title: autoTitle.trim() || 'Untitled',
            content: content,
            tag_names: tags,
          },
        });
      } else {
        // Create new note
        const newNote = await createNote.mutateAsync({
          title: autoTitle.trim() || 'Untitled',
          content: content,
          tag_names: tags,
        });
        // Store the new note ID for subsequent updates
        noteIdRef.current = newNote.id;
      }
      setLastSaved(new Date());
    } catch (error) {
      console.error('Error saving note:', error);
    } finally {
      setIsSaving(false);
    }
  }, [content, tags, createNote, updateNote]);

  // Debounced auto-save effect
  useEffect(() => {
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for auto-save (1 second after last change)
    saveTimeoutRef.current = setTimeout(() => {
      saveNote();
    }, 1000);

    // Cleanup on unmount
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content, tags]);

  const isLoading = createNote.isPending || updateNote.isPending;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden h-full flex flex-col">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Lexical Editor - takes all available space */}
        <div className="flex-1 overflow-y-auto">
          <LexicalOutlinerEditor
            key={note?.id || 'new'}
            initialContent={note?.content || ''}
            onChange={setContent}
            placeholder="Start typing... Press Enter for new line, Tab to indent"
          />
        </div>

        {/* Bottom toolbar with tags and auto-save indicator */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 space-y-3">
          {/* Tags and Save Status */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <TagInput value={tags} onChange={setTags} disabled={false} />
            </div>

            {/* Auto-save indicator */}
            <div className="flex items-center gap-2 text-sm text-gray-500">
              {isSaving ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Saving...</span>
                </>
              ) : lastSaved ? (
                <span>Saved {formatTimeSince(lastSaved)}</span>
              ) : null}
            </div>
          </div>

          {/* Backlinks Panel - only show when editing an existing note */}
          {note && onNavigateToNote && (
            <>
              <BacklinksPanel noteId={note.id} onNavigate={onNavigateToNote} />
              <RelatedNotesPanel noteId={note.id} onNavigate={onNavigateToNote} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper function to format time since last save
function formatTimeSince(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
  if (seconds < 10) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default NoteForm;
