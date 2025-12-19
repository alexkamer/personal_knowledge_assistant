/**
 * Types for autocomplete functionality.
 */

export interface AutocompleteRequest {
  prefix: string;
  context?: string;
}

export interface AutocompleteResponse {
  completion: string;
}
