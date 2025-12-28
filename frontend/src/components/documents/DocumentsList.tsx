/**
 * Documents list component showing uploaded documents.
 */
import React, { useState } from 'react';
import { Trash2, Calendar, HardDrive, AlertCircle, RefreshCw, Filter, ArrowUpDown, Tag, FileText } from 'lucide-react';
import { useDocuments, useDeleteDocument, useCategories } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';
import { DocumentThumbnail } from './DocumentThumbnail';

interface DocumentsListProps {
  onSelectDocument?: (document: Document) => void;
  selectedDocumentId?: string;
}

export function DocumentsList({ onSelectDocument, selectedDocumentId }: DocumentsListProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, error, refetch } = useDocuments(selectedCategory, sortBy, sortOrder);
  const { data: categories } = useCategories();
  const deleteDocument = useDeleteDocument();

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();

    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteDocument.mutateAsync(id);
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-lg p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-500 mx-auto"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-lg p-8">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <AlertCircle size={20} />
            <span className="font-medium">Failed to load documents</span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            {(error as any)?.response?.data?.detail || error.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg shadow-md hover:shadow-lg transition-all"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-lg p-8">
        <div className="text-center text-gray-400">
          <FileText className="mx-auto mb-4 text-gray-500" size={48} />
          <p className="font-medium text-lg">No documents yet</p>
          <p className="text-sm mt-2">Upload your first document to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with count and controls */}
      <div className="flex items-center justify-between px-3">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
          Documents ({data.total})
        </h2>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-900/80 backdrop-blur-xl border border-gray-300/50 dark:border-gray-700/50 rounded-lg hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors"
        >
          <Filter size={16} />
          {showFilters ? 'Hide' : 'Show'} Filters
        </button>
      </div>

      {/* Filters and Sorting Panel */}
      {showFilters && (
        <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-300/50 dark:border-gray-700/50 rounded-xl shadow-lg p-4 space-y-4">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <Tag size={16} />
              Category
            </label>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || undefined)}
              className="w-full px-3 py-2 bg-gray-900/80 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 dark:text-white"
            >
              <option value="">All Categories</option>
              {categories?.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Controls */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <ArrowUpDown size={16} />
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900/80 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 dark:text-white"
              >
                <option value="created_at">Date Created</option>
                <option value="filename">Name</option>
                <option value="file_size">Size</option>
                <option value="category">Category</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Order
              </label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900/80 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 dark:text-white"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          {/* Active Filters Summary */}
          {(selectedCategory || sortBy !== 'created_at' || sortOrder !== 'desc') && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Active:</span>
              {selectedCategory && (
                <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded">
                  {selectedCategory}
                </span>
              )}
              {(sortBy !== 'created_at' || sortOrder !== 'desc') && (
                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded">
                  {sortBy} ({sortOrder})
                </span>
              )}
              <button
                onClick={() => {
                  setSelectedCategory(undefined);
                  setSortBy('created_at');
                  setSortOrder('desc');
                }}
                className="ml-auto text-primary-600 dark:text-primary-400 hover:underline"
              >
                Clear All
              </button>
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        {data.documents.map((document) => (
          <div
            key={document.id}
            onClick={() => onSelectDocument?.(document)}
            className={`
              p-5 cursor-pointer transition-all duration-200 rounded-2xl shadow-lg hover:shadow-xl animate-slide-in-left
              ${
                selectedDocumentId === document.id
                  ? 'bg-primary-500 text-white scale-[1.02]'
                  : 'bg-gray-900/80 backdrop-blur-xl border border-gray-700 hover:scale-[1.01]'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start flex-1 min-w-0 gap-3">
                <DocumentThumbnail
                  fileType={document.file_type}
                  filename={document.filename}
                  thumbnailUrl={document.thumbnail_url}
                  size="sm"
                />
                <div className="flex-1 min-w-0">
                  <h3 className={`text-sm font-semibold truncate ${
                    selectedDocumentId === document.id
                      ? 'text-white'
                      : 'text-gray-900 dark:text-white'
                  }`}>
                    {document.filename}
                  </h3>

                  <div className={`mt-2 flex items-center gap-4 text-xs ${
                    selectedDocumentId === document.id
                      ? 'text-primary-100'
                      : 'text-gray-400'
                  }`}>
                    <span className="flex items-center gap-1">
                      <HardDrive size={14} />
                      {formatFileSize(document.file_size)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar size={14} />
                      {formatDate(document.created_at)}
                    </span>
                    <span className={`uppercase px-2 py-0.5 rounded-full font-medium ${
                      selectedDocumentId === document.id
                        ? 'bg-white/20 text-white backdrop-blur-sm'
                        : 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                    }`}>
                      {document.file_type}
                    </span>
                  </div>

                  {document.category && (
                    <div className={`mt-2 flex items-center gap-1.5 text-xs ${
                      selectedDocumentId === document.id
                        ? 'text-primary-100'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      <Tag size={14} />
                      <span className={`px-2 py-0.5 rounded-full font-medium ${
                        selectedDocumentId === document.id
                          ? 'bg-white/20 text-white backdrop-blur-sm'
                          : 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
                      }`}>
                        {document.category}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={(e) => handleDelete(e, document.id)}
                disabled={deleteDocument.isPending}
                className={`ml-4 p-2 rounded-lg transition-colors disabled:opacity-50 ${
                  selectedDocumentId === document.id
                    ? 'text-white hover:bg-white/20'
                    : 'text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                }`}
                aria-label="Delete document"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
