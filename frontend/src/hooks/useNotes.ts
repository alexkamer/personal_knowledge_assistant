/**
 * React Query hooks for note management.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { noteService } from '../services/noteService';
import type { NoteCreate, NoteUpdate } from '../types/note';

const NOTES_QUERY_KEY = ['notes'];

/**
 * Hook to fetch all notes.
 */
export function useNotes() {
  return useQuery({
    queryKey: NOTES_QUERY_KEY,
    queryFn: () => noteService.getNotes(),
  });
}

/**
 * Hook to fetch a single note by ID.
 */
export function useNote(id: string) {
  return useQuery({
    queryKey: [...NOTES_QUERY_KEY, id],
    queryFn: () => noteService.getNote(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new note.
 */
export function useCreateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NoteCreate) => noteService.createNote(data),
    onSuccess: () => {
      // Invalidate notes list to refetch
      queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
    },
  });
}

/**
 * Hook to update a note.
 */
export function useUpdateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NoteUpdate }) =>
      noteService.updateNote(id, data),
    onSuccess: (_, variables) => {
      // Invalidate both the list and the specific note
      queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: [...NOTES_QUERY_KEY, variables.id] });
    },
  });
}

/**
 * Hook to delete a note.
 */
export function useDeleteNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => noteService.deleteNote(id),
    onSuccess: () => {
      // Invalidate notes list to refetch
      queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
    },
  });
}
