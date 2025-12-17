/**
 * Documents page for uploading and managing documents.
 */
import { useState } from 'react';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentsList } from '@/components/documents/DocumentsList';
import { useDocument } from '@/hooks/useDocuments';
import type { Document } from '@/types/document';
import { FileText, X } from 'lucide-react';
import { ContextPanel } from '@/components/context/ContextPanel';

export function DocumentsPage() {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [isContextPanelCollapsed, setIsContextPanelCollapsed] = useState(false);
  const { data: documentContent, isLoading } = useDocument(selectedDocument?.id || null);

  const handleSelectDocument = (document: Document) => {
    setSelectedDocument(document);
  };

  const handleClosePreview = () => {
    setSelectedDocument(null);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
        <p className="text-gray-600">
          Upload and manage your documents for AI-powered search
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <DocumentUpload />
          <DocumentsList
            onSelectDocument={handleSelectDocument}
            selectedDocumentId={selectedDocument?.id}
          />
        </div>

        <div className="lg:sticky lg:top-8 lg:self-start space-y-6">
          {selectedDocument ? (
            <>
              <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="text-blue-600" size={20} />
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">
                        {selectedDocument.filename}
                      </h2>
                      <p className="text-sm text-gray-500">
                        {selectedDocument.file_type.toUpperCase()} • {(selectedDocument.file_size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleClosePreview}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                    aria-label="Close preview"
                  >
                    <X size={20} />
                  </button>
                </div>

                <div className="p-6">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : documentContent ? (
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans bg-gray-50 p-4 rounded-md border border-gray-200 max-h-96 overflow-y-auto">
                        {documentContent.content}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-12">
                      Failed to load document content
                    </p>
                  )}
                </div>
              </div>

              {/* Context Intelligence Panel */}
              <ContextPanel
                sourceType="document"
                sourceId={selectedDocument.id}
                isCollapsed={isContextPanelCollapsed}
                onToggle={() => setIsContextPanelCollapsed(!isContextPanelCollapsed)}
              />
            </>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <FileText className="mx-auto mb-4 text-gray-300" size={64} />
              <p className="text-gray-500">
                Select a document to preview its content
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
