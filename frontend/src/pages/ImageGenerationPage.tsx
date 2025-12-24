/**
 * Image Generation Page - AI-powered image generation using Gemini Imagen.
 */
import { useState, useCallback, useReducer } from 'react';
import { AlertCircle } from 'lucide-react';
import { ImagePromptInput } from '@/components/images/ImagePromptInput';
import { ImageMessageList } from '@/components/images/ImageMessageList';
import { imageGenerationService } from '@/services/imageGenerationService';
import type { ImageGenerationMessage, GeneratedImage, ImageGenerationMetadata } from '@/types/imageGeneration';

// Streaming state types
interface StreamingState {
  isStreaming: boolean;
  status: string;
}

type StreamingAction =
  | { type: 'START_STREAMING' }
  | { type: 'UPDATE_STATUS'; payload: string }
  | { type: 'RESET' };

const initialStreamingState: StreamingState = {
  isStreaming: false,
  status: '',
};

function streamingReducer(state: StreamingState, action: StreamingAction): StreamingState {
  switch (action.type) {
    case 'START_STREAMING':
      return {
        isStreaming: true,
        status: 'Preparing...',
      };
    case 'UPDATE_STATUS':
      return {
        ...state,
        status: action.payload,
      };
    case 'RESET':
      return initialStreamingState;
    default:
      return state;
  }
}

export function ImageGenerationPage() {
  // Streaming state
  const [streamingState, dispatchStreaming] = useReducer(streamingReducer, initialStreamingState);

  // Messages state (chat-like history)
  const [messages, setMessages] = useState<ImageGenerationMessage[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form controls state
  const [aspectRatio, setAspectRatio] = useState<'1:1' | '16:9' | '9:16' | '4:3' | '3:4'>('1:1');
  const [imageSize, setImageSize] = useState<'1K' | '2K' | '4K'>('2K');
  const [numberOfImages, setNumberOfImages] = useState(1);
  const [negativePrompt, setNegativePrompt] = useState('');

  const handleGenerate = useCallback(
    async (prompt: string) => {
      try {
        setErrorMessage(null);
        dispatchStreaming({ type: 'START_STREAMING' });

        // Add prompt message immediately to history
        const promptMessage: ImageGenerationMessage = {
          id: `prompt-${Date.now()}`,
          type: 'prompt',
          prompt,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, promptMessage]);

        // Generate images with streaming status updates
        await imageGenerationService.generateImagesStream(
          {
            prompt,
            negative_prompt: negativePrompt || undefined,
            aspect_ratio: aspectRatio,
            image_size: imageSize,
            number_of_images: numberOfImages,
          },
          // onStatus
          (status: string) => {
            dispatchStreaming({ type: 'UPDATE_STATUS', payload: status });
          },
          // onImages
          (images: GeneratedImage[], metadata: ImageGenerationMetadata) => {
            // Add images message to history
            const imageMessage: ImageGenerationMessage = {
              id: `images-${Date.now()}`,
              type: 'images',
              images,
              metadata,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, imageMessage]);
            dispatchStreaming({ type: 'RESET' });
          },
          // onDone
          () => {
            dispatchStreaming({ type: 'RESET' });
          },
          // onError
          (error: string) => {
            setErrorMessage(error);
            dispatchStreaming({ type: 'RESET' });
          }
        );
      } catch (error: any) {
        console.error('Failed to generate images:', error);
        setErrorMessage(error?.message || 'Failed to generate images');
        dispatchStreaming({ type: 'RESET' });
      }
    },
    [aspectRatio, imageSize, numberOfImages, negativePrompt]
  );

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex-shrink-0">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold text-white">Image Generation</h1>
          <p className="text-sm text-gray-400 mt-1">
            Create stunning images with AI-powered generation
          </p>
        </div>
      </header>

      {/* Error Banner */}
      {errorMessage && (
        <div className="border-b border-red-800 bg-red-900/20 px-6 py-3 flex-shrink-0">
          <div className="max-w-6xl mx-auto flex items-start gap-3">
            <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-200">Error</h3>
              <p className="text-sm text-red-300 mt-1">{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-400 hover:text-red-300 transition-colors"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Message List (scrollable) */}
      <div className="flex-1 overflow-hidden">
        <ImageMessageList
          messages={messages}
          isStreaming={streamingState.isStreaming}
          status={streamingState.status}
        />
      </div>

      {/* Input Form (fixed at bottom) */}
      <ImagePromptInput
        onGenerate={handleGenerate}
        disabled={streamingState.isStreaming}
        aspectRatio={aspectRatio}
        onAspectRatioChange={setAspectRatio}
        imageSize={imageSize}
        onImageSizeChange={setImageSize}
        numberOfImages={numberOfImages}
        onNumberOfImagesChange={setNumberOfImages}
        negativePrompt={negativePrompt}
        onNegativePromptChange={setNegativePrompt}
      />
    </div>
  );
}
