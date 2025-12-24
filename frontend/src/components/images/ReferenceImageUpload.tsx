/**
 * Component for uploading and managing reference images for guided generation.
 * Supports up to 14 images: 5 human, 6 object, 3 style.
 */
import { useState, useCallback, useRef } from 'react';
import { X, Upload, User, Box, Palette } from 'lucide-react';
import type { ReferenceImage } from '@/types/imageGeneration';

interface ReferenceImageUploadProps {
  images: ReferenceImage[];
  onChange: (images: ReferenceImage[]) => void;
  disabled?: boolean;
}

const IMAGE_LIMITS = {
  human: 5,
  object: 6,
  style: 3,
  total: 14,
};

export function ReferenceImageUpload({ images, onChange, disabled }: ReferenceImageUploadProps) {
  const [selectedType, setSelectedType] = useState<'human' | 'object' | 'style'>('object');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Count images by type
  const counts = {
    human: images.filter((img) => img.image_type === 'human').length,
    object: images.filter((img) => img.image_type === 'object').length,
    style: images.filter((img) => img.image_type === 'style').length,
  };

  const canAddMore = (type: 'human' | 'object' | 'style') => {
    return counts[type] < IMAGE_LIMITS[type] && images.length < IMAGE_LIMITS.total;
  };

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);

      files.forEach((file) => {
        // Check file type
        if (!file.type.startsWith('image/')) {
          alert(`${file.name} is not an image file`);
          return;
        }

        // Check if we can add more of this type
        if (!canAddMore(selectedType)) {
          alert(`Maximum ${IMAGE_LIMITS[selectedType]} ${selectedType} images allowed`);
          return;
        }

        // Read file as base64
        const reader = new FileReader();
        reader.onload = (event) => {
          const base64 = event.target?.result as string;
          const [, data] = base64.split(','); // Remove "data:image/png;base64," prefix

          const newImage: ReferenceImage = {
            image_data: data,
            mime_type: file.type,
            image_type: selectedType,
            preview_url: URL.createObjectURL(file),
          };

          onChange([...images, newImage]);
        };
        reader.readAsDataURL(file);
      });

      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    [images, onChange, selectedType, canAddMore]
  );

  const handleRemove = useCallback(
    (index: number) => {
      const newImages = [...images];
      // Revoke preview URL to free memory
      if (newImages[index].preview_url) {
        URL.revokeObjectURL(newImages[index].preview_url!);
      }
      newImages.splice(index, 1);
      onChange(newImages);
    },
    [images, onChange]
  );

  const getIcon = (type: string) => {
    switch (type) {
      case 'human':
        return <User className="w-4 h-4" />;
      case 'object':
        return <Box className="w-4 h-4" />;
      case 'style':
        return <Palette className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'human':
        return 'Person';
      case 'object':
        return 'Object';
      case 'style':
        return 'Style';
      default:
        return type;
    }
  };

  return (
    <div className="space-y-4">
      {/* Type Selection */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Image Type:</span>
        <div className="flex gap-2">
          {(['human', 'object', 'style'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              disabled={disabled}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                ${
                  selectedType === type
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {getIcon(type)}
              {getTypeLabel(type)}
              <span className="text-gray-400">
                ({counts[type]}/{IMAGE_LIMITS[type]})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Upload Button */}
      <div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled || !canAddMore(selectedType)}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || !canAddMore(selectedType)}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-dashed
            transition-colors text-sm font-medium
            ${
              disabled || !canAddMore(selectedType)
                ? 'border-gray-700 text-gray-600 cursor-not-allowed'
                : 'border-gray-600 text-gray-300 hover:border-indigo-500 hover:text-indigo-400'
            }
          `}
        >
          <Upload className="w-4 h-4" />
          {canAddMore(selectedType)
            ? `Upload ${getTypeLabel(selectedType)} Image${counts[selectedType] > 0 ? 's' : ''}`
            : `Max ${IMAGE_LIMITS[selectedType]} ${getTypeLabel(selectedType)} images reached`}
        </button>
        {images.length === 0 && (
          <p className="mt-2 text-xs text-gray-500">
            Reference images help generate consistent characters, specific objects, or artistic styles.
          </p>
        )}
      </div>

      {/* Image Grid */}
      {images.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>
              {images.length} of {IMAGE_LIMITS.total} reference images
            </span>
            <span className="text-gray-500">
              H: {counts.human}/{IMAGE_LIMITS.human} • O: {counts.object}/{IMAGE_LIMITS.object} • S:{' '}
              {counts.style}/{IMAGE_LIMITS.style}
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2">
            {images.map((image, index) => (
              <div
                key={index}
                className="relative aspect-square rounded-lg overflow-hidden bg-gray-800 group"
              >
                <img
                  src={image.preview_url}
                  alt={`Reference ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                {/* Type badge */}
                <div className="absolute top-1 left-1 flex items-center gap-1 px-1.5 py-0.5 bg-black/70 rounded text-xs text-white">
                  {getIcon(image.image_type)}
                  <span className="capitalize">{image.image_type[0]}</span>
                </div>
                {/* Remove button */}
                <button
                  onClick={() => handleRemove(index)}
                  disabled={disabled}
                  className={`
                    absolute top-1 right-1 p-1 bg-red-600 rounded-full
                    opacity-0 group-hover:opacity-100 transition-opacity
                    ${disabled ? 'cursor-not-allowed opacity-50' : 'hover:bg-red-700'}
                  `}
                  aria-label="Remove image"
                >
                  <X className="w-3 h-3 text-white" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
