/**
 * Context Intelligence Types
 *
 * Types for the Cross-Feature Intelligence system that connects
 * YouTube videos, Notes, and Documents.
 */

/**
 * Type of content source
 */
export type SourceType = 'note' | 'document' | 'youtube';

/**
 * A single piece of related content discovered through semantic search
 */
export interface RelatedContentItem {
  /** Type of source: note, document, or youtube */
  source_type: SourceType;

  /** Unique identifier of the source */
  source_id: string;

  /** Title of the source content */
  source_title: string;

  /** Similarity score between 0 and 1 (higher = more similar) */
  similarity_score: number;

  /** Preview snippet of the matching content */
  preview?: string;

  /** Timestamp in seconds (for YouTube videos only) */
  timestamp?: number;

  /** Number of matching chunks from this source */
  chunk_count: number;
}

/**
 * Source information for a contradiction
 */
export interface ContradictionSource {
  /** Type of source: note or document */
  type: SourceType;

  /** Unique identifier of the source */
  id: string;

  /** Title of the source */
  title: string;

  /** Relevant excerpt showing the contradictory statement */
  excerpt: string;
}

/**
 * A detected logical contradiction between two sources
 */
export interface ContradictionItem {
  /** First source in the contradiction */
  source1: ContradictionSource;

  /** Second source in the contradiction */
  source2: ContradictionSource;

  /** Type of contradiction (factual/methodological/conceptual/temporal) */
  contradiction_type: string;

  /** Explanation of why these sources contradict */
  explanation: string;

  /** Severity level of the contradiction */
  severity: 'high' | 'medium' | 'low';

  /** AI confidence in this contradiction (0.0-1.0) */
  confidence: number;
}

/**
 * Response from the context intelligence API
 */
export interface ContextResponse {
  /** Type of the source being analyzed */
  source_type: SourceType;

  /** ID of the source being analyzed */
  source_id: string;

  /** Title of the source being analyzed */
  source_title: string;

  /** List of semantically related content items */
  related_content: RelatedContentItem[];

  /** AI-generated synthesis explaining connections (optional) */
  synthesis?: string | null;

  /** Suggested questions for further exploration (optional) */
  suggested_questions: string[];

  /** Detected logical contradictions (Innovation: Contradiction Detective) */
  contradictions: ContradictionItem[];
}

/**
 * Parameters for fetching context intelligence
 */
export interface ContextParams {
  /** Whether to include AI-generated synthesis */
  include_synthesis?: boolean;

  /** Whether to include suggested questions */
  include_questions?: boolean;

  /** Number of related items to return (1-20) */
  top_k?: number;
}
