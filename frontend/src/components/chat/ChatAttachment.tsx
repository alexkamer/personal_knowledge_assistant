import React from 'react';
import { X, FileText, File } from 'lucide-react';

interface ChatAttachmentProps {
  filename: string;
  size: number;
  onRemove?: () => void;
  status?: 'pending' | 'processed' | 'error';
  errorMessage?: string;
}

/**
 * Component to display a file attachment in the chat interface.
 * Can be used for both pending attachments (with remove button) and sent attachments (read-only).
 */
export const ChatAttachment: React.FC<ChatAttachmentProps> = ({
  filename,
  size,
  onRemove,
  status = 'processed',
  errorMessage,
}) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = () => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText className="w-4 h-4" />;
    if (ext === 'docx' || ext === 'doc') return <FileText className="w-4 h-4" />;
    if (ext === 'txt' || ext === 'md' || ext === 'markdown') return <File className="w-4 h-4" />;
    return <File className="w-4 h-4" />;
  };

  const getStatusColor = () => {
    if (status === 'error') return 'bg-red-100 border-red-300 text-red-800';
    if (status === 'pending') return 'bg-gray-100 border-gray-300 text-gray-700';
    return 'bg-blue-100 border-blue-300 text-blue-800';
  };

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm ${getStatusColor()}`}
      title={errorMessage || filename}
    >
      {getFileIcon()}
      <span className="font-medium truncate max-w-[200px]">{filename}</span>
      <span className="text-xs opacity-75">({formatFileSize(size)})</span>

      {status === 'error' && (
        <span className="text-xs ml-1" title={errorMessage}>
          ⚠️
        </span>
      )}

      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-1 hover:opacity-70 transition-opacity"
          aria-label="Remove attachment"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
