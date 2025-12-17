/**
 * Notes page with list and form.
 */
import { useState, useEffect } from 'react';
import NotesList from '../components/notes/NotesList';
import NoteForm from '../components/notes/NoteForm';
import { TagFilter } from '../components/tags/TagFilter';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Note } from '../types/note';
import { useNotes } from '../hooks/useNotes';
import { ContextPanel } from '@/components/context/ContextPanel';

function NotesPage() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isContextPanelCollapsed, setIsContextPanelCollapsed] = useState(false);
  const { data: notesData } = useNotes();

  const handleSelectNote = (note: Note) => {
    setSelectedNote(note);
    setIsCreating(false);
  };

  const handleNavigateToNoteById = (noteId: string) => {
    const notes = notesData?.notes || [];
    const targetNote = notes.find((n: Note) => n.id === noteId);
    if (targetNote) {
      handleSelectNote(targetNote);
    }
  };

  const handleCreateNew = () => {
    setSelectedNote(null);
    setIsCreating(true);
  };

  const handleCancel = () => {
    setSelectedNote(null);
    setIsCreating(false);
  };

  const handleSaveComplete = () => {
    setSelectedNote(null);
    setIsCreating(false);
  };

  // Listen for wiki link navigation events
  useEffect(() => {
    const handleWikiLinkNavigation = (event: Event) => {
      const customEvent = event as CustomEvent<{ noteId: string; noteTitle: string }>;
      const { noteId } = customEvent.detail;

      // Find the note by ID and navigate to it
      const notes = notesData?.notes || [];
      const targetNote = notes.find((n: Note) => n.id === noteId);

      if (targetNote) {
        handleSelectNote(targetNote);
      }
    };

    document.addEventListener('navigate-to-note', handleWikiLinkNavigation);

    return () => {
      document.removeEventListener('navigate-to-note', handleWikiLinkNavigation);
    };
  }, [notesData]);

  const hasNoteOpen = isCreating || selectedNote;

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)] relative">
      {/* Sidebar - Collapsible */}
      <div
        className={`flex-shrink-0 flex flex-col space-y-4 transition-all duration-300 ease-in-out h-full relative ${
          isSidebarCollapsed ? 'w-0' : 'w-80'
        }`}
      >
        <div className={`${isSidebarCollapsed ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300 flex flex-col h-full`}>
          {/* Tag Filter */}
          <div className="flex-shrink-0">
            <TagFilter selectedTags={selectedTags} onTagsChange={setSelectedTags} />
          </div>

          {/* Notes List with header */}
          <div className="flex-1 flex flex-col overflow-hidden min-h-0">
            <div className="flex justify-between items-center mb-4 flex-shrink-0">
              <h2 className="text-xl font-semibold text-stone-800 pl-3">Notes</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCreateNew}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  New Note
                </button>
                <button
                  onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                  className="p-1 text-stone-400 hover:text-stone-600 hover:bg-stone-100 rounded transition-colors"
                  title="Hide sidebar"
                >
                  <ChevronLeft size={20} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
              <NotesList
                onSelectNote={handleSelectNote}
                selectedNoteId={selectedNote?.id}
                selectedTags={selectedTags}
              />
            </div>
          </div>
        </div>

        {/* Show Sidebar Button - Only visible when collapsed */}
        {isSidebarCollapsed && (
          <button
            onClick={() => setIsSidebarCollapsed(false)}
            className="absolute top-3 left-2 p-1 text-stone-600 hover:text-stone-900 hover:bg-stone-100 rounded transition-colors z-10"
            title="Show sidebar"
          >
            <ChevronRight size={20} />
          </button>
        )}
      </div>

      {/* Main Content Area - Note editor or empty state */}
      <div className="flex-1 overflow-auto">
        {hasNoteOpen ? (
          <NoteForm
            note={selectedNote}
            onSave={handleSaveComplete}
            onCancel={handleCancel}
            onNavigateToNote={handleNavigateToNoteById}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-md p-8 text-center text-stone-500 h-full flex items-center justify-center">
            <div>
              <p className="text-xl">Select a note to edit or create a new one</p>
            </div>
          </div>
        )}
      </div>

      {/* Context Intelligence Panel - Only shown when a note is selected */}
      {selectedNote && !isCreating && (
        <div className="w-80 flex-shrink-0">
          <ContextPanel
            sourceType="note"
            sourceId={selectedNote.id}
            isCollapsed={isContextPanelCollapsed}
            onToggle={() => setIsContextPanelCollapsed(!isContextPanelCollapsed)}
          />
        </div>
      )}
    </div>
  );
}

export default NotesPage;
