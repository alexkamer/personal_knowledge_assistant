/**
 * Note create/edit form component.
 */
import { useState, useEffect } from 'react';
import { useCreateNote, useUpdateNote } from '../../hooks/useNotes';
import type { Note } from '../../types/note';

interface NoteFormProps {
  note: Note | null;
  onSave: () => void;
  onCancel: () => void;
}

function NoteForm({ note, onSave, onCancel }: NoteFormProps) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');

  const createNote = useCreateNote();
  const updateNote = useUpdateNote();

  // Load note data when editing
  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setContent(note.content);
      setTags(note.tags || '');
    } else {
      setTitle('');
      setContent('');
      setTags('');
    }
  }, [note]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim() || !content.trim()) {
      alert('Title and content are required');
      return;
    }

    try {
      if (note) {
        // Update existing note
        await updateNote.mutateAsync({
          id: note.id,
          data: {
            title: title.trim(),
            content: content.trim(),
            tags: tags.trim() || undefined,
          },
        });
      } else {
        // Create new note
        await createNote.mutateAsync({
          title: title.trim(),
          content: content.trim(),
          tags: tags.trim() || undefined,
        });
      }
      onSave();
    } catch (error) {
      console.error('Error saving note:', error);
      alert('Failed to save note');
    }
  };

  const isLoading = createNote.isPending || updateNote.isPending;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        {note ? 'Edit Note' : 'Create Note'}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter note title"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
            Content
          </label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={10}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter note content"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            id="tags"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. work, ideas, todo"
            disabled={isLoading}
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Saving...' : 'Save Note'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default NoteForm;
