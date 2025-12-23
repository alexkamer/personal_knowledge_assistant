/**
 * Grid view component for documents with beautiful card layout
 */
import { Trash2, Calendar, HardDrive, Tag } from 'lucide-react';
import type { Document } from '@/types/document';
import { useState } from 'react';
import { DocumentThumbnail } from './DocumentThumbnail';

interface DocumentsGridViewProps {
  documents: Document[];
  selectedDocumentId?: string;
  onSelectDocument: (document: Document) => void;
  onDeleteDocument: (e: React.MouseEvent, id: string) => void;
  isDeleting: boolean;
}

export function DocumentsGridView({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onDeleteDocument,
  isDeleting,
}: DocumentsGridViewProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const getFileTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      pdf: 'text-red-400 bg-red-500/10',
      txt: 'text-gray-400 bg-gray-500/10',
      md: 'text-blue-400 bg-blue-500/10',
      doc: 'text-blue-400 bg-blue-500/10',
      docx: 'text-blue-400 bg-blue-500/10',
    };
    return colors[type.toLowerCase()] || 'text-gray-400 bg-gray-500/10';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {documents.map((document, index) => {
        const isSelected = selectedDocumentId === document.id;
        const isHovered = hoveredId === document.id;
        const colorClass = getFileTypeColor(document.file_type);

        return (
          <div
            key={document.id}
            onClick={() => onSelectDocument(document)}
            onMouseEnter={() => setHoveredId(document.id)}
            onMouseLeave={() => setHoveredId(null)}
            className={`
              group cursor-pointer
              glass glass-hover elevated ambient-glow
              rounded-xl overflow-hidden
              transition-all duration-300
              fade-in stagger-${(index % 5) + 1}
              ${isSelected ? 'ring-2 ring-primary-500 scale-[1.02]' : ''}
            `}
          >
            {/* Document Thumbnail */}
            <div className={`
              p-6 flex items-center justify-center
              ${isSelected ? 'bg-primary-500/20' : 'bg-gray-800/50'}
              transition-colors duration-200
            `}>
              <DocumentThumbnail
                fileType={document.file_type}
                filename={document.filename}
                thumbnailUrl={document.thumbnail_url}
                size="lg"
              />
            </div>

            {/* Document Info */}
            <div className="p-4">
              <h3 className="text-sm font-semibold text-white truncate mb-2">
                {document.filename}
              </h3>

              <div className="flex items-center gap-3 text-xs text-gray-400 mb-3">
                <span className="flex items-center gap-1">
                  <HardDrive size={12} />
                  {formatFileSize(document.file_size)}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar size={12} />
                  {formatDate(document.created_at)}
                </span>
              </div>

              {/* File Type Badge */}
              <div className="flex items-center justify-between">
                <span className={`
                  px-2 py-1 rounded-md text-xs font-medium uppercase
                  ${colorClass}
                `}>
                  {document.file_type}
                </span>

                {/* Category Tag */}
                {document.category && (
                  <span className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-success-500/10 text-success-400">
                    <Tag size={12} />
                    {document.category}
                  </span>
                )}
              </div>
            </div>

            {/* Hover Actions */}
            <div className={`
              absolute top-2 right-2
              opacity-0 group-hover:opacity-100
              transition-opacity duration-200
            `}>
              <button
                onClick={(e) => onDeleteDocument(e, document.id)}
                disabled={isDeleting}
                className="
                  p-2 rounded-lg
                  glass
                  text-gray-400 hover:text-danger-400
                  transition-colors spring-scale
                  disabled:opacity-50
                "
                aria-label="Delete document"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
