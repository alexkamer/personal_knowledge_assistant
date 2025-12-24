/**
 * Image Gallery - Grid view of generated images with management features.
 * Includes: favorites, download, delete, copy prompt.
 */
import { useState, useEffect, useCallback } from 'react';
import { Download, Star, Trash2, Copy, Check, RefreshCw } from 'lucide-react';
import { galleryService, type GalleryImage } from '@/services/galleryService';

interface ImageGalleryProps {
  onRegeneratePrompt?: (prompt: string) => void;
}

export function ImageGallery({ onRegeneratePrompt }: ImageGalleryProps) {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<GalleryImage | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Pagination
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  // Filters
  const [favoritesOnly, setFavoritesOnly] = useState(false);

  // Load images
  const loadImages = useCallback(
    async (append = false) => {
      try {
        setLoading(true);
        setError(null);

        const response = await galleryService.listImages({
          limit,
          offset: append ? offset : 0,
          favoritesOnly,
          includeThumbnailsOnly: true,
        });

        if (append) {
          setImages((prev) => [...prev, ...response.images]);
        } else {
          setImages(response.images);
          setOffset(0);
        }

        setHasMore(response.has_more);
        setLoading(false);
      } catch (err: any) {
        console.error('Failed to load images:', err);
        setError('Failed to load images. Please try again.');
        setLoading(false);
      }
    },
    [offset, favoritesOnly]
  );

  // Initial load
  useEffect(() => {
    loadImages(false);
  }, [favoritesOnly]);

  // Toggle favorite
  const handleToggleFavorite = async (image: GalleryImage) => {
    try {
      const updated = await galleryService.toggleFavorite(image.id, !image.is_favorite);

      // Update local state
      setImages((prev) =>
        prev.map((img) => (img.id === updated.id ? { ...img, is_favorite: updated.is_favorite } : img))
      );
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
      setError('Failed to update favorite');
    }
  };

  // Download image
  const handleDownload = async (image: GalleryImage) => {
    try {
      // If we only have thumbnail, fetch full image first
      if (!image.image_data) {
        const fullImage = await galleryService.getImage(image.id, true);
        galleryService.downloadImage(fullImage);
      } else {
        galleryService.downloadImage(image);
      }
    } catch (err) {
      console.error('Failed to download image:', err);
      setError('Failed to download image');
    }
  };

  // Copy prompt
  const handleCopyPrompt = async (image: GalleryImage) => {
    try {
      await galleryService.copyPromptToClipboard(image.prompt);
      setCopiedId(image.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy prompt:', err);
      setError('Failed to copy prompt');
    }
  };

  // Delete image
  const handleDelete = async (image: GalleryImage) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      await galleryService.deleteImage(image.id);
      setImages((prev) => prev.filter((img) => img.id !== image.id));

      if (selectedImage?.id === image.id) {
        setSelectedImage(null);
      }
    } catch (err) {
      console.error('Failed to delete image:', err);
      setError('Failed to delete image');
    }
  };

  // Load more images
  const handleLoadMore = () => {
    setOffset((prev) => prev + limit);
    loadImages(true);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with filters */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Your Gallery</h2>

          <div className="flex items-center gap-4">
            {/* Favorites filter */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={favoritesOnly}
                onChange={(e) => setFavoritesOnly(e.target.checked)}
                className="w-4 h-4 text-indigo-600 bg-gray-700 border-gray-600 rounded focus:ring-indigo-500"
              />
              <Star className="w-4 h-4 text-yellow-400" fill={favoritesOnly ? "currentColor" : "none"} />
              <span className="text-sm text-gray-300">Favorites Only</span>
            </label>

            {/* Refresh button */}
            <button
              onClick={() => loadImages(false)}
              disabled={loading}
              className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {images.length > 0 && (
          <p className="text-sm text-gray-500 mt-2">{images.length} images loaded</p>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/20 border-b border-red-800 px-6 py-3">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Gallery grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading && images.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
              <p className="text-gray-400 mt-4">Loading images...</p>
            </div>
          </div>
        ) : images.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-400">
                {favoritesOnly ? 'No favorite images yet' : 'No images generated yet'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {favoritesOnly ? 'Star some images to see them here' : 'Generate your first image to get started'}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {images.map((image) => (
                <div
                  key={image.id}
                  className="group relative aspect-square bg-gray-900 rounded-lg overflow-hidden border border-gray-800 hover:border-indigo-500 transition-all"
                >
                  {/* Image */}
                  <img
                    src={`data:image/${image.image_format};base64,${image.thumbnail_data || image.image_data}`}
                    alt={image.prompt.slice(0, 50)}
                    className="w-full h-full object-cover cursor-pointer"
                    onClick={() => setSelectedImage(image)}
                  />

                  {/* Hover overlay with actions */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    {/* Favorite */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleFavorite(image);
                      }}
                      className="p-2 bg-gray-800/90 rounded-full hover:bg-gray-700 transition-colors"
                      title={image.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      <Star
                        className="w-5 h-5 text-yellow-400"
                        fill={image.is_favorite ? 'currentColor' : 'none'}
                      />
                    </button>

                    {/* Download */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(image);
                      }}
                      className="p-2 bg-gray-800/90 rounded-full hover:bg-gray-700 transition-colors"
                      title="Download image"
                    >
                      <Download className="w-5 h-5 text-blue-400" />
                    </button>

                    {/* Copy prompt */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyPrompt(image);
                      }}
                      className="p-2 bg-gray-800/90 rounded-full hover:bg-gray-700 transition-colors"
                      title="Copy prompt"
                    >
                      {copiedId === image.id ? (
                        <Check className="w-5 h-5 text-green-400" />
                      ) : (
                        <Copy className="w-5 h-5 text-gray-300" />
                      )}
                    </button>

                    {/* Delete */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(image);
                      }}
                      className="p-2 bg-gray-800/90 rounded-full hover:bg-red-700 transition-colors"
                      title="Delete image"
                    >
                      <Trash2 className="w-5 h-5 text-red-400" />
                    </button>
                  </div>

                  {/* Favorite indicator */}
                  {image.is_favorite && (
                    <div className="absolute top-2 right-2">
                      <Star className="w-5 h-5 text-yellow-400" fill="currentColor" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Load more button */}
            {hasMore && (
              <div className="mt-8 text-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loading}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Image detail modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="bg-gray-900 rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Image */}
            <div className="p-4">
              <img
                src={`data:image/${selectedImage.image_format};base64,${
                  selectedImage.image_data || selectedImage.thumbnail_data
                }`}
                alt={selectedImage.prompt}
                className="w-full rounded-lg"
              />
            </div>

            {/* Details */}
            <div className="border-t border-gray-800 p-6 space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-1">Prompt</h3>
                <p className="text-white">{selectedImage.prompt}</p>
              </div>

              {selectedImage.negative_prompt && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-1">Negative Prompt</h3>
                  <p className="text-white">{selectedImage.negative_prompt}</p>
                </div>
              )}

              {selectedImage.metadata_ && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {selectedImage.metadata_.aspect_ratio && (
                    <div>
                      <span className="text-gray-400">Aspect Ratio:</span>
                      <span className="text-white ml-2">{selectedImage.metadata_.aspect_ratio}</span>
                    </div>
                  )}
                  {selectedImage.metadata_.image_size && (
                    <div>
                      <span className="text-gray-400">Size:</span>
                      <span className="text-white ml-2">{selectedImage.metadata_.image_size}</span>
                    </div>
                  )}
                  {selectedImage.width && selectedImage.height && (
                    <div>
                      <span className="text-gray-400">Dimensions:</span>
                      <span className="text-white ml-2">
                        {selectedImage.width}×{selectedImage.height}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3 pt-4">
                <button
                  onClick={() => handleToggleFavorite(selectedImage)}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  <Star
                    className="w-4 h-4 text-yellow-400"
                    fill={selectedImage.is_favorite ? 'currentColor' : 'none'}
                  />
                  {selectedImage.is_favorite ? 'Unfavorite' : 'Favorite'}
                </button>

                <button
                  onClick={() => handleDownload(selectedImage)}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>

                <button
                  onClick={() => handleCopyPrompt(selectedImage)}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  {copiedId === selectedImage.id ? (
                    <>
                      <Check className="w-4 h-4 text-green-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy Prompt
                    </>
                  )}
                </button>

                {onRegeneratePrompt && (
                  <button
                    onClick={() => {
                      onRegeneratePrompt(selectedImage.prompt);
                      setSelectedImage(null);
                    }}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
