/**
 * Notes page with list and form.
 */
import { useState } from 'react';
import NotesList from '../components/notes/NotesList';
import NoteForm from '../components/notes/NoteForm';
import type { Note } from '../types/note';

function NotesPage() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isCreating, setIsCreating] = useState(false);

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

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Notes List */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Notes</h2>
          <button
            onClick={handleCreateNew}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            New Note
          </button>
        </div>
        <NotesList onSelectNote={handleSelectNote} selectedNoteId={selectedNote?.id} />
      </div>

      {/* Note Form */}
      <div>
        {(isCreating || selectedNote) && (
          <NoteForm
            note={selectedNote}
            onSave={handleSaveComplete}
            onCancel={handleCancel}
          />
        )}
        {!isCreating && !selectedNote && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
            Select a note to edit or create a new one
          </div>
        )}
      </div>
    </div>
  );
}

export default NotesPage;
