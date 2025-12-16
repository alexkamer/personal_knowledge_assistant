/**
 * Tests for tagService
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { tagService } from './tagService';
import api from './api';
import type { TagWithUsage } from '../types/tag';

// Mock the api module
vi.mock('./api', () => ({
  default: {
    get: vi.fn(),
  },
}));

describe('tagService', () => {
  const mockApi = vi.mocked(api);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTags', () => {
    it('should fetch all tags', async () => {
      const mockTags: TagWithUsage[] = [
        { id: '1', name: 'javascript', note_count: 10 },
        { id: '2', name: 'typescript', note_count: 5 },
      ];

      mockApi.get.mockResolvedValue({ data: mockTags } as any);

      const result = await tagService.getTags();

      expect(mockApi.get).toHaveBeenCalledWith('/tags/');
      expect(result).toEqual(mockTags);
    });

    it('should handle empty tags', async () => {
      mockApi.get.mockResolvedValue({ data: [] } as any);

      const result = await tagService.getTags();

      expect(result).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      const error = new Error('API Error');
      mockApi.get.mockRejectedValue(error);

      await expect(tagService.getTags()).rejects.toThrow('API Error');
    });
  });

  describe('getPopularTags', () => {
    it('should fetch popular tags with default limit', async () => {
      const mockTags: TagWithUsage[] = [
        { id: '1', name: 'javascript', note_count: 100 },
        { id: '2', name: 'typescript', note_count: 50 },
      ];

      mockApi.get.mockResolvedValue({ data: mockTags } as any);

      const result = await tagService.getPopularTags();

      expect(mockApi.get).toHaveBeenCalledWith('/tags/popular/', {
        params: { limit: 10 },
      });
      expect(result).toEqual(mockTags);
    });

    it('should fetch popular tags with custom limit', async () => {
      const mockTags: TagWithUsage[] = [
        { id: '1', name: 'javascript', note_count: 100 },
      ];

      mockApi.get.mockResolvedValue({ data: mockTags } as any);

      const result = await tagService.getPopularTags(5);

      expect(mockApi.get).toHaveBeenCalledWith('/tags/popular/', {
        params: { limit: 5 },
      });
      expect(result).toEqual(mockTags);
    });

    it('should handle limit of 1', async () => {
      const mockTags: TagWithUsage[] = [
        { id: '1', name: 'javascript', note_count: 100 },
      ];

      mockApi.get.mockResolvedValue({ data: mockTags } as any);

      await tagService.getPopularTags(1);

      expect(mockApi.get).toHaveBeenCalledWith('/tags/popular/', {
        params: { limit: 1 },
      });
    });

    it('should handle large limits', async () => {
      mockApi.get.mockResolvedValue({ data: [] } as any);

      await tagService.getPopularTags(100);

      expect(mockApi.get).toHaveBeenCalledWith('/tags/popular/', {
        params: { limit: 100 },
      });
    });

    it('should throw error on API failure', async () => {
      const error = new Error('Network Error');
      mockApi.get.mockRejectedValue(error);

      await expect(tagService.getPopularTags()).rejects.toThrow('Network Error');
    });
  });
});
