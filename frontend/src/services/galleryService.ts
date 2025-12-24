/**
 * Gallery service for managing generated images.
 */
import apiClient from './api';
import type { GeneratedImage } from '@/types/imageGeneration';

export interface GalleryImage {
  id: string;
  prompt: string;
  negative_prompt?: string;
  image_data?: string; // Base64 full image (only in detail view)
  thumbnail_data?: string; // Base64 thumbnail
  image_format: string;
  metadata_?: Record<string, any>;
  width?: number;
  height?: number;
  is_favorite: boolean;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface GalleryListResponse {
  images: GalleryImage[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface UpdateImageRequest {
  is_favorite?: boolean;
  tags?: string[];
}

export const galleryService = {
  /**
   * List images with pagination and filters.
   */
  async listImages(params?: {
    limit?: number;
    offset?: number;
    favoritesOnly?: boolean;
    tags?: string;
    includeThumbnailsOnly?: boolean;
  }): Promise<GalleryListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.favoritesOnly) queryParams.append('favorites_only', 'true');
    if (params?.tags) queryParams.append('tags', params.tags);
    if (params?.includeThumbnailsOnly !== undefined) {
      queryParams.append('include_thumbnails_only', params.includeThumbnailsOnly.toString());
    }

    const response = await apiClient.get(`/gallery/list?${queryParams.toString()}`);
    return response.data;
  },

  /**
   * Get a single image by ID.
   */
  async getImage(imageId: string, includeFullImage = true): Promise<GalleryImage> {
    const queryParams = new URLSearchParams();
    queryParams.append('include_full_image', includeFullImage.toString());

    const response = await apiClient.get(`/gallery/${imageId}?${queryParams.toString()}`);
    return response.data;
  },

  /**
   * Update image metadata (favorite, tags).
   */
  async updateImage(imageId: string, updates: UpdateImageRequest): Promise<GalleryImage> {
    const response = await apiClient.patch(`/gallery/${imageId}`, updates);
    return response.data;
  },

  /**
   * Delete an image.
   */
  async deleteImage(imageId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/gallery/${imageId}`);
    return response.data;
  },

  /**
   * Toggle favorite status.
   */
  async toggleFavorite(imageId: string, isFavorite: boolean): Promise<GalleryImage> {
    return this.updateImage(imageId, { is_favorite: isFavorite });
  },

  /**
   * Download image as file.
   */
  downloadImage(image: GalleryImage, filename?: string): void {
    // Use full image if available, otherwise thumbnail
    const imageData = image.image_data || image.thumbnail_data;
    if (!imageData) {
      throw new Error('No image data available for download');
    }

    // Convert base64 to blob
    const byteString = atob(imageData);
    const arrayBuffer = new ArrayBuffer(byteString.length);
    const uint8Array = new Uint8Array(arrayBuffer);

    for (let i = 0; i < byteString.length; i++) {
      uint8Array[i] = byteString.charCodeAt(i);
    }

    const mimeType = image.image_format === 'jpeg' ? 'image/jpeg' : 'image/png';
    const blob = new Blob([arrayBuffer], { type: mimeType });

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `generated-image-${image.id}.${image.image_format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Copy prompt to clipboard.
   */
  async copyPromptToClipboard(prompt: string): Promise<void> {
    await navigator.clipboard.writeText(prompt);
  },
};
