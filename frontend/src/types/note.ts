/**
 * Note types matching backend schemas.
 */

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  content: string;
  tags?: string;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  tags?: string;
}

export interface NoteListResponse {
  notes: Note[];
  total: number;
}
