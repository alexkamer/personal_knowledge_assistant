/**
 * Note types matching backend schemas.
 */

import { Tag } from './tag';

export interface Note {
  id: string;
  title: string;
  content: string;
  tags_rel: Tag[];
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  content: string;
  tag_names: string[];
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  tag_names?: string[];
}

export interface NoteListResponse {
  notes: Note[];
  total: number;
}
