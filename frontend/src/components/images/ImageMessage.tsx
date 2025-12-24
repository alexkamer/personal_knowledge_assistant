/**
 * Individual image generation message component.
 * Renders either a prompt message or images message.
 */
import { useState } from 'react';
import { Download, Maximize2, X } from 'lucide-react';
import type { ImageGenerationMessage } from '@/types/imageGeneration';

interface ImageMessageProps {
  message: ImageGenerationMessage;
}

export function ImageMessage({ message }: ImageMessageProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  // Prompt message
  if (message.type === 'prompt') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-3">
        <div className="bg-gray-800/50 rounded-lg px-4 py-3 border border-gray-700">
          <p className="text-white whitespace-pre-wrap">{message.prompt}</p>
        </div>
      </div>
    );
  }

  // Images message
  if (message.type === 'images' && message.images) {
    const gridClass = message.images.length === 1
      ? 'grid-cols-1'
      : message.images.length === 2
      ? 'grid-cols-2'
      : 'grid-cols-2 md:grid-cols-3';

    return (
      <>
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className={`grid ${gridClass} gap-4`}>
            {message.images.map((image, index) => (
              <div key={index} className="relative group">
                {/* Image */}
                <div className="relative bg-gray-900 rounded-lg overflow-hidden border border-gray-700 aspect-square">
                  <img
                    src={`data:image/${image.format};base64,${image.image_data}`}
                    alt={`Generated image ${index + 1}`}
                    className="w-full h-full object-contain"
                  />

                  {/* Hover Overlay with Actions */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button
                      onClick={() => setSelectedImage(`data:image/${image.format};base64,${image.image_data}`)}
                      className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                      title="View full size"
                    >
                      <Maximize2 size={20} className="text-white" />
                    </button>
                    <button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = `data:image/${image.format};base64,${image.image_data}`;
                        link.download = `generated-image-${Date.now()}.${image.format}`;
                        link.click();
                      }}
                      className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                      title="Download image"
                    >
                      <Download size={20} className="text-white" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Metadata */}
          {message.metadata && (
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-400">
              <span className="px-2 py-1 bg-gray-800 rounded">{message.metadata.aspect_ratio}</span>
              <span className="px-2 py-1 bg-gray-800 rounded">{message.metadata.image_size}</span>
              <span className="px-2 py-1 bg-gray-800 rounded">{message.metadata.model.split('-')[0]}</span>
              {message.metadata.negative_prompt && (
                <span className="px-2 py-1 bg-gray-800 rounded" title={message.metadata.negative_prompt}>
                  Negative prompt
                </span>
              )}
            </div>
          )}
        </div>

        {/* Full Size Image Modal */}
        {selectedImage && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedImage(null)}
          >
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X size={24} className="text-white" />
            </button>
            <img
              src={selectedImage}
              alt="Full size"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
      </>
    );
  }

  return null;
}
