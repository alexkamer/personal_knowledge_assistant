/**
 * Document type definitions matching backend API schemas.
 */

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_path: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  metadata_: string | null;
  category: string | null;
  thumbnail_url?: string; // Optional thumbnail/preview URL
}

export interface DocumentContent {
  id: string;
  filename: string;
  file_type: string;
  content: string;
  created_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}
