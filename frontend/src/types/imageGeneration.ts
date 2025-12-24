/**
 * TypeScript types for image generation feature.
 */

export interface ReferenceImage {
  image_data: string; // Base64 encoded image data
  mime_type: string; // e.g., "image/jpeg", "image/png"
  image_type: 'human' | 'object' | 'style';
  preview_url?: string; // Local URL for preview (not sent to API)
}

export interface ImageGenerationRequest {
  prompt: string;
  negative_prompt?: string;
  aspect_ratio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4';
  image_size: '1K' | '2K' | '4K';
  number_of_images: number; // 1-4
  model?: 'gemini-2.5-flash-image' | 'gemini-3-pro-image-preview';
  reference_images?: ReferenceImage[];
}

export interface GeneratedImage {
  id?: string; // UUID from backend (if saved)
  image_data: string; // Base64 encoded image data
  format: 'png' | 'jpeg';
}

export interface ImageGenerationMetadata {
  prompt: string;
  aspect_ratio: string;
  image_size: string;
  model: string;
  negative_prompt?: string;
}

export interface ImageGenerationMessage {
  id: string; // Local ID for UI (e.g., "prompt-12345" or "images-12345")
  type: 'prompt' | 'images';
  prompt?: string; // For prompt messages
  images?: GeneratedImage[]; // For image messages
  metadata?: ImageGenerationMetadata; // Metadata for image messages
  created_at: string;
}
