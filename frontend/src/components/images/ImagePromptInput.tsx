/**
 * Image generation prompt input form with controls.
 */
import { useState, useCallback, KeyboardEvent } from 'react';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

interface ImagePromptInputProps {
  onGenerate: (prompt: string) => void;
  disabled?: boolean;
  aspectRatio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4';
  onAspectRatioChange: (ratio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4') => void;
  imageSize: '1K' | '2K' | '4K';
  onImageSizeChange: (size: '1K' | '2K' | '4K') => void;
  numberOfImages: number;
  onNumberOfImagesChange: (count: number) => void;
  negativePrompt: string;
  onNegativePromptChange: (prompt: string) => void;
}

export function ImagePromptInput({
  onGenerate,
  disabled = false,
  aspectRatio,
  onAspectRatioChange,
  imageSize,
  onImageSizeChange,
  numberOfImages,
  onNumberOfImagesChange,
  negativePrompt,
  onNegativePromptChange,
}: ImagePromptInputProps) {
  const [prompt, setPrompt] = useState('');
  const [showNegativePrompt, setShowNegativePrompt] = useState(false);

  const handleSubmit = useCallback(() => {
    if (prompt.trim() && !disabled) {
      onGenerate(prompt.trim());
      setPrompt('');
      setShowNegativePrompt(false);
      onNegativePromptChange('');
    }
  }, [prompt, disabled, onGenerate, onNegativePromptChange]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="border-t border-gray-800 bg-gray-900/95 backdrop-blur-md">
      <div className="max-w-4xl mx-auto p-4 space-y-3">
        {/* Controls Row */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Aspect Ratio */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-400">Aspect Ratio:</label>
            <select
              value={aspectRatio}
              onChange={(e) => onAspectRatioChange(e.target.value as any)}
              disabled={disabled}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="1:1">1:1 (Square)</option>
              <option value="16:9">16:9 (Landscape)</option>
              <option value="9:16">9:16 (Portrait)</option>
              <option value="4:3">4:3 (Classic)</option>
              <option value="3:4">3:4 (Vertical)</option>
            </select>
          </div>

          {/* Image Size */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-400">Quality:</label>
            <select
              value={imageSize}
              onChange={(e) => onImageSizeChange(e.target.value as any)}
              disabled={disabled}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="1K">1K (Fast)</option>
              <option value="2K">2K (Balanced)</option>
              <option value="4K">4K (Best)</option>
            </select>
          </div>

          {/* Number of Images */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-400">Count:</label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4].map((num) => (
                <button
                  key={num}
                  onClick={() => onNumberOfImagesChange(num)}
                  disabled={disabled}
                  className={`w-8 h-8 rounded-md text-sm font-medium transition-colors ${
                    numberOfImages === num
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Negative Prompt Toggle */}
          <button
            onClick={() => setShowNegativePrompt(!showNegativePrompt)}
            disabled={disabled}
            className="ml-auto flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {showNegativePrompt ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            Negative Prompt
          </button>
        </div>

        {/* Negative Prompt (Collapsible) */}
        {showNegativePrompt && (
          <div className="space-y-2">
            <label className="text-sm text-gray-400">What NOT to include:</label>
            <textarea
              value={negativePrompt}
              onChange={(e) => onNegativePromptChange(e.target.value)}
              disabled={disabled}
              placeholder="e.g., blurry, low quality, distorted..."
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
              rows={2}
            />
          </div>
        )}

        {/* Prompt Input */}
        <div className="flex gap-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Describe the image you want to generate..."
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
            rows={3}
          />
          <button
            onClick={handleSubmit}
            disabled={disabled || !prompt.trim()}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-indigo-600"
          >
            <Sparkles size={20} />
            Generate
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          Press <kbd className="px-1.5 py-0.5 bg-gray-800 border border-gray-700 rounded text-gray-400">⌘</kbd> +{' '}
          <kbd className="px-1.5 py-0.5 bg-gray-800 border border-gray-700 rounded text-gray-400">Enter</kbd> to
          generate
        </p>
      </div>
    </div>
  );
}
