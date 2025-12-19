/**
 * Notes page with list and form.
 */
import { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import NotesList from '../components/notes/NotesList';
import NoteForm from '../components/notes/NoteForm';
import { TagFilter } from '../components/tags/TagFilter';
import { Pagination } from '@/components/ui/Pagination';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Note } from '../types/note';
import { useNotes } from '../hooks/useNotes';
import { usePaginationState } from '@/hooks/usePaginationState';
import { ContextPanel } from '@/components/context/ContextPanel';

function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // URL state management
  const selectedNoteId = searchParams.get('note') || null;
  const isCreating = searchParams.get('new') === 'true';
  const selectedTags = searchParams.get('tags')?.split(',').filter(Boolean) || [];
  const isSidebarCollapsed = searchParams.get('hideSidebar') === 'true';

  const [isContextPanelCollapsed, setIsContextPanelCollapsed] = useState(false);

  // Pagination state
  const pagination = usePaginationState({
    defaultLimit: 20,
    paramPrefix: 'note_',
  });

  // Fetch notes with pagination
  const { data: notesData, isLoading } = useNotes(
    pagination.offset,
    pagination.limit,
    selectedTags.length > 0 ? selectedTags : undefined
  );

  // Get selected note from fetched data
  const selectedNote = useMemo(() => {
    if (!selectedNoteId || !notesData) return null;
    return notesData.notes.find((n: Note) => n.id === selectedNoteId) || null;
  }, [selectedNoteId, notesData]);

  // URL param update helper
  const updateURLParam = useCallback((key: string, value: string | null) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
      return newParams;
    });
  }, [setSearchParams]);

  const handleSelectNote = useCallback((note: Note) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.set('note', note.id);
      newParams.delete('new');
      return newParams;
    });
  }, [setSearchParams]);

  const handleNavigateToNoteById = useCallback((noteId: string) => {
    updateURLParam('note', noteId);
    updateURLParam('new', null);
  }, [updateURLParam]);

  const handleCreateNew = useCallback(() => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.delete('note');
      newParams.set('new', 'true');
      return newParams;
    });
  }, [setSearchParams]);

  const handleCancel = useCallback(() => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.delete('note');
      newParams.delete('new');
      return newParams;
    });
  }, [setSearchParams]);

  const handleSaveComplete = useCallback(() => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      newParams.delete('note');
      newParams.delete('new');
      return newParams;
    });
  }, [setSearchParams]);

  const handleTagsChange = useCallback((tags: string[]) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (tags.length > 0) {
        newParams.set('tags', tags.join(','));
      } else {
        newParams.delete('tags');
      }
      // Reset to page 1 when tags change
      newParams.delete('note_page');
      return newParams;
    });
  }, [setSearchParams]);

  const handleToggleSidebar = useCallback(() => {
    updateURLParam('hideSidebar', !isSidebarCollapsed ? 'true' : null);
  }, [updateURLParam, isSidebarCollapsed]);

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
            <TagFilter selectedTags={selectedTags} onTagsChange={handleTagsChange} />
          </div>

          {/* Notes List with header */}
          <div className="flex-1 flex flex-col overflow-hidden min-h-0">
            <div className="flex justify-between items-center mb-4 flex-shrink-0">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 pl-3">
                Notes {notesData && `(${notesData.total})`}
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCreateNew}
                  className="px-4 py-1.5 bg-gray-900 dark:bg-white hover:bg-gray-800 dark:hover:bg-gray-100 text-white dark:text-gray-900 rounded-md text-sm font-medium transition-colors"
                >
                  New Note
                </button>
                <button
                  onClick={handleToggleSidebar}
                  className="p-1.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-800 rounded-md transition-colors"
                  title="Hide sidebar"
                >
                  <ChevronLeft size={18} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col">
              {isLoading ? (
                <div className="p-4 text-center text-gray-400 text-sm">
                  Loading notes...
                </div>
              ) : notesData && notesData.notes.length > 0 ? (
                <>
                  <div className="flex-1 overflow-y-auto">
                    <NotesList
                      notes={notesData.notes}
                      onSelectNote={handleSelectNote}
                      selectedNoteId={selectedNote?.id}
                    />
                  </div>

                  {/* Pagination Controls */}
                  {notesData.total > pagination.limit && (
                    <div className="flex-shrink-0 mt-3 px-2">
                      <Pagination
                        currentPage={pagination.page}
                        totalPages={pagination.totalPages(notesData.total)}
                        onPageChange={pagination.setPage}
                        hasNext={pagination.hasNextPage(notesData.total)}
                        hasPrev={pagination.hasPrevPage()}
                        showPageNumbers={false}
                        showFirstLast={false}
                      />
                    </div>
                  )}
                </>
              ) : (
                <div className="p-4 text-center text-gray-400 text-sm">
                  {selectedTags.length > 0 ? 'No notes with selected tags' : 'No notes yet'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Show Sidebar Button - Only visible when collapsed */}
        {isSidebarCollapsed && (
          <button
            onClick={handleToggleSidebar}
            className="absolute top-3 left-2 p-2 text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-lg shadow-md hover:shadow-lg transition-all z-10"
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
          <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-lg p-12 text-center text-gray-500 dark:text-gray-400 h-full flex items-center justify-center">
            <div>
              <p className="text-sm text-gray-400">Select a note to edit or create a new one</p>
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
