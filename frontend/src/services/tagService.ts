/**
 * Service for tag-related API operations.
 */

import api from './api';
import { TagWithUsage } from '../types/tag';

export const tagService = {
  /**
   * Get all tags with usage counts.
   */
  async getTags(): Promise<TagWithUsage[]> {
    const response = await api.get<TagWithUsage[]>('/tags/');
    return response.data;
  },

  /**
   * Get most used tags.
   */
  async getPopularTags(limit = 10): Promise<TagWithUsage[]> {
    const response = await api.get<TagWithUsage[]>('/tags/popular/', {
      params: { limit },
    });
    return response.data;
  },
};
