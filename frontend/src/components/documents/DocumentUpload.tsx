/**
 * Document upload component with drag-and-drop support and URL input.
 */
import React, { useCallback, useState } from 'react';
import { Upload, Link } from 'lucide-react';
import { useUploadDocument, useCreateDocumentFromURL } from '@/hooks/useDocuments';

export function DocumentUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [url, setUrl] = useState('');
  const uploadDocument = useUploadDocument();
  const createFromURL = useCreateDocumentFromURL();

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      try {
        setErrorMessage(null);
        await uploadDocument.mutateAsync(file);
      } catch (error: any) {
        console.error('Upload failed:', error);
        const message = error.response?.data?.detail || error.message || 'Upload failed. Please try again.';
        setErrorMessage(message);
      }
    },
    [uploadDocument]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleUrlSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!url.trim()) return;

      try {
        setErrorMessage(null);
        await createFromURL.mutateAsync(url);
        setUrl('');
        setShowUrlInput(false);
      } catch (error: any) {
        console.error('Failed to create document from URL:', error);
        const message = error.response?.data?.detail || error.message || 'Failed to fetch URL. Please check the URL and try again.';
        setErrorMessage(message);
      }
    },
    [url, createFromURL]
  );

  const isLoading = uploadDocument.isPending || createFromURL.isPending;
  const isError = uploadDocument.isError || createFromURL.isError;
  const isSuccess = uploadDocument.isSuccess || createFromURL.isSuccess;

  return (
    <div className="space-y-4">
      {/* File Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          bg-gray-900/80 backdrop-blur-xl border-2 border-dashed rounded-2xl shadow-lg p-8 text-center transition-all duration-200
          ${
            isDragging
              ? 'border-indigo-500 dark:border-indigo-400 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]'
              : 'border-gray-300/50 dark:border-gray-700/50 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-xl'
          }
          ${isLoading ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <Upload className={`mx-auto mb-4 ${isDragging ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'} transition-colors`} size={48} />

        <div className="mb-4">
          <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {isLoading ? 'Processing...' : 'Upload a document'}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Drag and drop your file here, or click to browse
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
            Supported formats: TXT, MD, PDF, DOCX
          </p>
        </div>

        <label className="inline-block">
          <input
            type="file"
            onChange={handleFileInput}
            accept=".txt,.md,.pdf,.doc,.docx"
            disabled={isLoading}
            className="hidden"
          />
          <span className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg shadow-md hover:shadow-lg cursor-pointer inline-block transition-all">
            Choose File
          </span>
        </label>

        {(isError || errorMessage) && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
            <p className="text-sm text-red-600 dark:text-red-400">
              {errorMessage || (uploadDocument.isError ? 'Upload failed. Please try again.' : 'Failed to fetch URL. Please check the URL and try again.')}
            </p>
          </div>
        )}

        {isSuccess && !errorMessage && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
            <p className="text-sm text-green-600 dark:text-green-400">
              Document added successfully!
            </p>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300 dark:border-gray-700"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-gray-50 dark:bg-gray-950 text-gray-400">or</span>
        </div>
      </div>

      {/* URL Input */}
      {!showUrlInput ? (
        <button
          onClick={() => setShowUrlInput(true)}
          disabled={isLoading}
          className="w-full px-4 py-3 bg-gray-900/80 backdrop-blur-xl border-2 border-gray-300/50 dark:border-gray-700/50 rounded-2xl shadow-lg hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 text-gray-700 dark:text-gray-300"
        >
          <Link size={20} />
          <span>Add from URL</span>
        </button>
      ) : (
        <form onSubmit={handleUrlSubmit} className="bg-gray-900/80 backdrop-blur-xl border-2 border-gray-300/50 dark:border-gray-700/50 rounded-2xl shadow-lg p-6">
          <div className="flex items-start gap-3 mb-4">
            <Link className="text-primary-600 dark:text-primary-400 mt-2.5" size={20} />
            <div className="flex-1">
              <label htmlFor="url-input" className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                Enter URL
              </label>
              <input
                id="url-input"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/article"
                disabled={isLoading}
                className="w-full px-3 py-2 bg-gray-900/80 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500"
                autoFocus
              />
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                Supports articles, blog posts, documentation pages, and more
              </p>
            </div>
          </div>

          {/* Error message for URL form */}
          {errorMessage && createFromURL.isError && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">
                {errorMessage}
              </p>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setShowUrlInput(false);
                setUrl('');
                setErrorMessage(null);
              }}
              disabled={isLoading}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !url.trim()}
              className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {createFromURL.isPending ? 'Fetching...' : 'Add Document'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
