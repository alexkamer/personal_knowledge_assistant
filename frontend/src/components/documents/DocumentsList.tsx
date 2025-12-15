/**
 * Documents list component showing uploaded documents.
 */
import React from 'react';
import { FileText, Trash2, Calendar, HardDrive } from 'lucide-react';
import { useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';

interface DocumentsListProps {
  onSelectDocument?: (document: Document) => void;
  selectedDocumentId?: string;
}

export function DocumentsList({ onSelectDocument, selectedDocumentId }: DocumentsListProps) {
  const { data, isLoading, error } = useDocuments();
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
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center text-red-600">
          <p className="font-medium">Failed to load documents</p>
          <p className="text-sm mt-2">Please try refreshing the page</p>
        </div>
      </div>
    );
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center text-gray-500">
          <FileText className="mx-auto mb-4" size={48} />
          <p className="font-medium">No documents yet</p>
          <p className="text-sm mt-2">Upload your first document to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">
          Documents ({data.total})
        </h2>
      </div>

      <div className="divide-y divide-gray-200">
        {data.documents.map((document) => (
          <div
            key={document.id}
            onClick={() => onSelectDocument?.(document)}
            className={`
              p-4 hover:bg-gray-50 transition-colors cursor-pointer
              ${selectedDocumentId === document.id ? 'bg-blue-50' : ''}
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start flex-1 min-w-0">
                <FileText
                  className="flex-shrink-0 mr-3 mt-1 text-blue-600"
                  size={20}
                />
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {document.filename}
                  </h3>

                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <HardDrive size={14} />
                      {formatFileSize(document.file_size)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar size={14} />
                      {formatDate(document.created_at)}
                    </span>
                    <span className="uppercase bg-gray-100 px-2 py-0.5 rounded">
                      {document.file_type}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={(e) => handleDelete(e, document.id)}
                disabled={deleteDocument.isPending}
                className="ml-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
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
