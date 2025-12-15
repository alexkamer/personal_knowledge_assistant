/**
 * Note API service.
 */
import { apiClient } from './api';
import type { Note, NoteCreate, NoteUpdate, NoteListResponse } from '../types/note';

export const noteService = {
  /**
   * Get all notes.
   */
  async getNotes(skip = 0, limit = 100): Promise<NoteListResponse> {
    const response = await apiClient.get<NoteListResponse>('/notes/', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Get a single note by ID.
   */
  async getNote(id: string): Promise<Note> {
    const response = await apiClient.get<Note>(`/notes/${id}`);
    return response.data;
  },

  /**
   * Create a new note.
   */
  async createNote(data: NoteCreate): Promise<Note> {
    const response = await apiClient.post<Note>('/notes/', data);
    return response.data;
  },

  /**
   * Update an existing note.
   */
  async updateNote(id: string, data: NoteUpdate): Promise<Note> {
    const response = await apiClient.put<Note>(`/notes/${id}`, data);
    return response.data;
  },

  /**
   * Delete a note.
   */
  async deleteNote(id: string): Promise<void> {
    await apiClient.delete(`/notes/${id}`);
  },
};
