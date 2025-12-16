/**
 * Tests for noteService
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { noteService } from './noteService';
import { apiClient } from './api';
import type { Note, NoteListResponse } from '@/types/note';

// Mock the api module
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('noteService', () => {
  const mockApiClient = vi.mocked(apiClient);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getNotes', () => {
    it('should fetch notes with default pagination', async () => {
      const mockResponse: NoteListResponse = {
        notes: [
          {
            id: 'note-1',
            title: 'Test Note',
            content: 'Test content',
            tags: ['test'],
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await noteService.getNotes();

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/', {
        params: { skip: 0, limit: 100 },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch notes with custom pagination', async () => {
      const mockResponse: NoteListResponse = {
        notes: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await noteService.getNotes(10, 50);

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/', {
        params: { skip: 10, limit: 50 },
      });
    });

    it('should fetch notes with tag filtering', async () => {
      const mockResponse: NoteListResponse = {
        notes: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await noteService.getNotes(0, 100, ['javascript', 'typescript']);

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/', {
        params: { skip: 0, limit: 100, tags: 'javascript,typescript' },
      });
    });

    it('should fetch notes without tags when tags array is empty', async () => {
      const mockResponse: NoteListResponse = {
        notes: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await noteService.getNotes(0, 100, []);

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/', {
        params: { skip: 0, limit: 100 },
      });
    });

    it('should fetch notes with single tag', async () => {
      const mockResponse: NoteListResponse = {
        notes: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      await noteService.getNotes(0, 100, ['python']);

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/', {
        params: { skip: 0, limit: 100, tags: 'python' },
      });
    });

    it('should handle empty note list', async () => {
      const mockResponse: NoteListResponse = {
        notes: [],
        total: 0,
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse } as any);

      const result = await noteService.getNotes();

      expect(result.notes).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(error);

      await expect(noteService.getNotes()).rejects.toThrow('Network Error');
    });
  });

  describe('getNote', () => {
    it('should fetch a specific note', async () => {
      const mockNote: Note = {
        id: 'note-1',
        title: 'Test Note',
        content: 'Test content',
        tags: ['test'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockNote } as any);

      const result = await noteService.getNote('note-1');

      expect(mockApiClient.get).toHaveBeenCalledWith('/notes/note-1');
      expect(result).toEqual(mockNote);
    });

    it('should handle note not found', async () => {
      const error = new Error('Note not found');
      mockApiClient.get.mockRejectedValue(error);

      await expect(noteService.getNote('nonexistent')).rejects.toThrow('Note not found');
    });

    it('should fetch note with multiple tags', async () => {
      const mockNote: Note = {
        id: 'note-1',
        title: 'Multi-tag Note',
        content: 'Content',
        tags: ['javascript', 'typescript', 'react'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockNote } as any);

      const result = await noteService.getNote('note-1');

      expect(result.tags).toEqual(['javascript', 'typescript', 'react']);
    });

    it('should fetch note with empty content', async () => {
      const mockNote: Note = {
        id: 'note-1',
        title: 'Empty Note',
        content: '',
        tags: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValue({ data: mockNote } as any);

      const result = await noteService.getNote('note-1');

      expect(result.content).toBe('');
      expect(result.tags).toEqual([]);
    });
  });

  describe('createNote', () => {
    it('should create a new note', async () => {
      const newNote = {
        title: 'New Note',
        content: 'New content',
        tags: ['new'],
      };

      const mockCreatedNote: Note = {
        id: 'note-1',
        ...newNote,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockCreatedNote } as any);

      const result = await noteService.createNote(newNote);

      expect(mockApiClient.post).toHaveBeenCalledWith('/notes/', newNote);
      expect(result).toEqual(mockCreatedNote);
    });

    it('should create note with empty tags', async () => {
      const newNote = {
        title: 'Note without tags',
        content: 'Content',
        tags: [],
      };

      const mockCreatedNote: Note = {
        id: 'note-1',
        ...newNote,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockCreatedNote } as any);

      const result = await noteService.createNote(newNote);

      expect(result.tags).toEqual([]);
    });

    it('should create note with empty content', async () => {
      const newNote = {
        title: 'Empty Content Note',
        content: '',
        tags: ['empty'],
      };

      const mockCreatedNote: Note = {
        id: 'note-1',
        ...newNote,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockCreatedNote } as any);

      const result = await noteService.createNote(newNote);

      expect(result.content).toBe('');
    });

    it('should handle creation errors', async () => {
      const newNote = {
        title: 'Error Note',
        content: 'Content',
        tags: [],
      };

      const error = new Error('Creation failed');
      mockApiClient.post.mockRejectedValue(error);

      await expect(noteService.createNote(newNote)).rejects.toThrow('Creation failed');
    });
  });

  describe('updateNote', () => {
    it('should update a note', async () => {
      const updateData = {
        title: 'Updated Title',
        content: 'Updated content',
        tags: ['updated'],
      };

      const mockUpdatedNote: Note = {
        id: 'note-1',
        ...updateData,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.put.mockResolvedValue({ data: mockUpdatedNote } as any);

      const result = await noteService.updateNote('note-1', updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/notes/note-1', updateData);
      expect(result).toEqual(mockUpdatedNote);
    });

    it('should update note title only', async () => {
      const updateData = {
        title: 'New Title',
      };

      const mockUpdatedNote: Note = {
        id: 'note-1',
        title: 'New Title',
        content: 'Original content',
        tags: ['test'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.put.mockResolvedValue({ data: mockUpdatedNote } as any);

      const result = await noteService.updateNote('note-1', updateData);

      expect(result.title).toBe('New Title');
    });

    it('should update note content only', async () => {
      const updateData = {
        content: 'New content',
      };

      const mockUpdatedNote: Note = {
        id: 'note-1',
        title: 'Original Title',
        content: 'New content',
        tags: ['test'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.put.mockResolvedValue({ data: mockUpdatedNote } as any);

      const result = await noteService.updateNote('note-1', updateData);

      expect(result.content).toBe('New content');
    });

    it('should update note tags only', async () => {
      const updateData = {
        tags: ['new', 'tags'],
      };

      const mockUpdatedNote: Note = {
        id: 'note-1',
        title: 'Original Title',
        content: 'Original content',
        tags: ['new', 'tags'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockApiClient.put.mockResolvedValue({ data: mockUpdatedNote } as any);

      const result = await noteService.updateNote('note-1', updateData);

      expect(result.tags).toEqual(['new', 'tags']);
    });

    it('should handle update errors', async () => {
      const updateData = {
        title: 'Error Title',
      };

      const error = new Error('Update failed');
      mockApiClient.put.mockRejectedValue(error);

      await expect(noteService.updateNote('note-1', updateData)).rejects.toThrow('Update failed');
    });

    it('should handle updating non-existent note', async () => {
      const updateData = {
        title: 'Updated Title',
      };

      const error = new Error('Note not found');
      mockApiClient.put.mockRejectedValue(error);

      await expect(noteService.updateNote('nonexistent', updateData)).rejects.toThrow(
        'Note not found'
      );
    });
  });

  describe('deleteNote', () => {
    it('should delete a note', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      await noteService.deleteNote('note-1');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/notes/note-1');
    });

    it('should handle deletion errors', async () => {
      const error = new Error('Delete failed');
      mockApiClient.delete.mockRejectedValue(error);

      await expect(noteService.deleteNote('note-1')).rejects.toThrow('Delete failed');
    });

    it('should handle deleting non-existent note', async () => {
      const error = new Error('Note not found');
      mockApiClient.delete.mockRejectedValue(error);

      await expect(noteService.deleteNote('nonexistent')).rejects.toThrow('Note not found');
    });

    it('should delete note with special characters in ID', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      await noteService.deleteNote('note-123-abc-xyz');

      expect(mockApiClient.delete).toHaveBeenCalledWith('/notes/note-123-abc-xyz');
    });

    it('should not return anything on successful deletion', async () => {
      mockApiClient.delete.mockResolvedValue({} as any);

      const result = await noteService.deleteNote('note-1');

      expect(result).toBeUndefined();
    });
  });
});
