/**
 * Service for AI-powered text autocomplete.
 */
import { apiClient } from './api';
import type { AutocompleteRequest, AutocompleteResponse } from '../types/autocomplete';

export const autocompleteService = {
  /**
   * Get AI-powered text completion for a given prefix.
   *
   * @param prefix - The text to complete
   * @param context - Optional additional context
   * @returns Promise resolving to the completion text
   */
  async getCompletion(prefix: string, context?: string): Promise<string> {
    const response = await apiClient.post<AutocompleteResponse>(
      '/autocomplete/',
      {
        prefix,
        context,
      } as AutocompleteRequest
    );
    return response.data.completion;
  },
};
