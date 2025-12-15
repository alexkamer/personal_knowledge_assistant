/**
 * Document upload component with drag-and-drop support.
 */
import React, { useCallback, useState } from 'react';
import { Upload } from 'lucide-react';
import { useUploadDocument } from '@/hooks/useDocuments';

export function DocumentUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const uploadDocument = useUploadDocument();

  const handleFile = useCallback(
    async (file: File) => {
      try {
        await uploadDocument.mutateAsync(file);
      } catch (error) {
        console.error('Upload failed:', error);
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

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center transition-colors
        ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }
        ${uploadDocument.isPending ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      <Upload className="mx-auto mb-4 text-gray-400" size={48} />

      <div className="mb-4">
        <p className="text-lg font-medium text-gray-700 mb-2">
          {uploadDocument.isPending ? 'Uploading...' : 'Upload a document'}
        </p>
        <p className="text-sm text-gray-500">
          Drag and drop your file here, or click to browse
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Supported formats: TXT, MD, PDF, DOCX
        </p>
      </div>

      <label className="inline-block">
        <input
          type="file"
          onChange={handleFileInput}
          accept=".txt,.md,.pdf,.doc,.docx"
          disabled={uploadDocument.isPending}
          className="hidden"
        />
        <span className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer inline-block transition-colors">
          Choose File
        </span>
      </label>

      {uploadDocument.isError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">
            Upload failed. Please try again.
          </p>
        </div>
      )}

      {uploadDocument.isSuccess && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-600">
            Document uploaded successfully!
          </p>
        </div>
      )}
    </div>
  );
}
