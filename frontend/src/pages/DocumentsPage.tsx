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
    <div className="max-w-7xl mx-auto px-6 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900 dark:text-white mb-2">Documents</h1>
        <p className="text-sm text-stone-600 dark:text-stone-400">
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
              <div className="bg-white/95 dark:bg-stone-900/95 backdrop-blur-xl border border-stone-200 dark:border-stone-800 rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-stone-50 dark:bg-stone-900 border-b border-stone-200 dark:border-stone-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="text-stone-700 dark:text-stone-300" size={18} />
                    <div>
                      <h2 className="text-sm font-semibold text-stone-900 dark:text-white">
                        {selectedDocument.filename}
                      </h2>
                      <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                        {selectedDocument.file_type.toUpperCase()} • {(selectedDocument.file_size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleClosePreview}
                    className="p-1.5 text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 rounded-md transition-colors"
                    aria-label="Close preview"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="p-5">
                  {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-stone-900 dark:border-white"></div>
                    </div>
                  ) : documentContent ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <pre className="whitespace-pre-wrap text-xs text-stone-700 dark:text-stone-300 font-mono bg-stone-50 dark:bg-stone-800/50 p-3 rounded-md border border-stone-200 dark:border-stone-700 max-h-96 overflow-y-auto">
                        {documentContent.content}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-stone-500 dark:text-stone-400 text-center text-sm py-12">
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
            <div className="bg-white/95 dark:bg-stone-900/95 backdrop-blur-xl border border-stone-200 dark:border-stone-800 rounded-lg p-12 text-center">
              <FileText className="mx-auto mb-4 text-stone-400 dark:text-stone-600" size={48} />
              <p className="text-stone-500 dark:text-stone-400 text-sm">
                Select a document to preview its content
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
