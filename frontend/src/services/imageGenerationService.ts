/**
 * Service for image generation API calls.
 */
import type { ImageGenerationRequest, GeneratedImage, ImageGenerationMetadata } from '@/types/imageGeneration';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const imageGenerationService = {
  /**
   * Generate images and stream status updates via SSE.
   *
   * @param request - Image generation request parameters
   * @param onStatus - Callback for status updates
   * @param onImages - Callback when images are generated
   * @param onDone - Callback when generation is complete
   * @param onError - Callback for errors
   */
  async generateImagesStream(
    request: ImageGenerationRequest,
    onStatus: (status: string) => void,
    onImages: (images: GeneratedImage[], metadata: ImageGenerationMetadata) => void,
    onDone: () => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/images/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is null');
      }

      let buffer = '';
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Decode the chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages (separated by double newlines)
          let boundary = buffer.indexOf('\n\n');
          while (boundary !== -1) {
            const message = buffer.substring(0, boundary);
            buffer = buffer.substring(boundary + 2);

            // Extract data from SSE message
            const lines = message.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));

                  switch (data.type) {
                    case 'status':
                      onStatus(data.status);
                      break;

                    case 'images':
                      onImages(data.images, data.metadata);
                      break;

                    case 'done':
                      onDone();
                      break;

                    case 'error':
                      onError(data.error);
                      break;
                  }
                } catch (e) {
                  console.error('Failed to parse SSE data:', e);
                }
              }
            }

            // Check for next complete message
            boundary = buffer.indexOf('\n\n');
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error: any) {
      console.error('Image generation service error:', error);
      onError(error?.message || 'Failed to generate images');
    }
  },

  /**
   * Check if image generation service is available.
   *
   * @returns Promise with service health status
   */
  async checkHealth(): Promise<{ available: boolean; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/images/health`);
      const data = await response.json();
      return {
        available: data.available,
        message: data.message,
      };
    } catch (error) {
      return {
        available: false,
        message: 'Failed to check service health',
      };
    }
  },
};
