/**
 * Tag type definitions.
 */

export interface Tag {
  id: string;
  name: string;
  created_at: string;
}

export interface TagWithUsage extends Tag {
  note_count: number;
}
