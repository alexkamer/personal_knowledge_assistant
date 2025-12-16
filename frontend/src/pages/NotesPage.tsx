/**
 * Notes page with list and form.
 */
import { useState } from 'react';
import NotesList from '../components/notes/NotesList';
import NoteForm from '../components/notes/NoteForm';
import { TagFilter } from '../components/tags/TagFilter';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Note } from '../types/note';

function NotesPage() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const handleSelectNote = (note: Note) => {
    setSelectedNote(note);
    setIsCreating(false);
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

  const hasNoteOpen = isCreating || selectedNote;

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)]">
      {/* Sidebar - Collapsible */}
      <div
        className={`flex-shrink-0 flex flex-col space-y-4 transition-all duration-300 ease-in-out h-full ${
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
              <h2 className="text-xl font-semibold text-gray-800 pl-3">Notes</h2>
              <button
                onClick={handleCreateNew}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                New Note
              </button>
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
      </div>

      {/* Collapse/Expand Button */}
      <button
        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-white border border-gray-300 rounded-r-lg px-1 py-4 hover:bg-gray-50 transition-colors shadow-md z-10"
        title={isSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
      >
        {isSidebarCollapsed ? (
          <ChevronRight size={20} className="text-gray-600" />
        ) : (
          <ChevronLeft size={20} className="text-gray-600" />
        )}
      </button>

      {/* Main Content Area - Note editor or empty state */}
      <div className="flex-1 overflow-auto">
        {hasNoteOpen ? (
          <NoteForm
            note={selectedNote}
            onSave={handleSaveComplete}
            onCancel={handleCancel}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500 h-full flex items-center justify-center">
            <div>
              <p className="text-xl">Select a note to edit or create a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default NotesPage;
