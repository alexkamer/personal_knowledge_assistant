/**
 * Documents page for uploading and managing documents.
 */
import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { DocumentsList } from '@/components/documents/DocumentsList';
import { DocumentsGridView } from '@/components/documents/DocumentsGridView';
import { DocumentsViewToggle } from '@/components/documents/DocumentsViewToggle';
import { DocumentsSearch } from '@/components/documents/DocumentsSearch';
import { DocumentsAnalytics } from '@/components/documents/DocumentsAnalytics';
import { DocumentViewer } from '@/components/documents/DocumentViewer';
import { Pagination } from '@/components/ui/Pagination';
import { useDocument, useDocuments, useDeleteDocument } from '@/hooks/useDocuments';
import { usePaginationState } from '@/hooks/usePaginationState';
import type { Document } from '@/types/document';
import { FileText, X, BarChart3, Trash2 } from 'lucide-react';
import { ContextPanel } from '@/components/context/ContextPanel';

type ViewMode = 'list' | 'grid';

export function DocumentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // URL state management for all filters and selections
  const selectedDocumentId = searchParams.get('doc') || null;
  const viewMode = (searchParams.get('view') as ViewMode) || 'grid';
  const searchQuery = searchParams.get('search') || '';
  const category = searchParams.get('category') || undefined;
  const sortBy = searchParams.get('sortBy') || 'created_at';
  const sortOrder = searchParams.get('sortOrder') || 'desc';
  const showAnalytics = searchParams.get('hideStats') !== 'true';

  const [isContextPanelCollapsed, setIsContextPanelCollapsed] = useState(false);

  // Pagination state
  const pagination = usePaginationState({
    defaultLimit: 20,
    paramPrefix: 'doc_',
  });

  // Fetch documents with pagination
  const { data: allDocuments, isLoading: isLoadingDocuments } = useDocuments(
    pagination.offset,
    pagination.limit,
    category,
    sortBy,
    sortOrder
  );

  const { data: documentContent, isLoading } = useDocument(selectedDocumentId);
  const deleteDocument = useDeleteDocument();

  // Get selected document from fetched data
  const selectedDocument = useMemo(() => {
    if (!selectedDocumentId || !allDocuments) return null;
    return allDocuments.documents.find((doc) => doc.id === selectedDocumentId) || null;
  }, [selectedDocumentId, allDocuments]);

  // Update URL params helper
  const updateURLParam = useCallback((key: string, value: string | null) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
      return newParams;
    });
  }, [setSearchParams]);

  const handleSelectDocument = useCallback((document: Document) => {
    updateURLParam('doc', document.id);
  }, [updateURLParam]);

  const handleClosePreview = useCallback(() => {
    updateURLParam('doc', null);
  }, [updateURLParam]);

  const handleDelete = useCallback(async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteDocument.mutateAsync(id);
        if (selectedDocumentId === id) {
          updateURLParam('doc', null);
        }
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  }, [deleteDocument, selectedDocumentId, updateURLParam]);

  const handleSearch = useCallback((query: string) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);
      if (query) {
        newParams.set('search', query);
      } else {
        newParams.delete('search');
      }
      // Reset to page 1 when searching
      newParams.delete('doc_page');
      return newParams;
    });
  }, [setSearchParams]);

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    updateURLParam('view', mode);
  }, [updateURLParam]);

  const handleToggleAnalytics = useCallback(() => {
    updateURLParam('hideStats', showAnalytics ? 'true' : null);
  }, [updateURLParam, showAnalytics]);

  // Calculate analytics
  const analytics = {
    totalDocuments: allDocuments?.total || 0,
    totalSize: allDocuments?.documents.reduce((sum, doc) => sum + doc.file_size, 0) || 0,
    recentUploads: allDocuments?.documents.filter((doc) => {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return new Date(doc.created_at) > weekAgo;
    }).length || 0,
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text mb-2">Documents</h1>
          <p className="text-sm text-gray-400">
            Upload and manage your documents for AI-powered search
          </p>
        </div>
        <button
          onClick={handleToggleAnalytics}
          className="glass glass-hover elevated px-4 py-2 rounded-lg flex items-center gap-2 text-gray-300 spring-scale"
        >
          <BarChart3 size={18} />
          {showAnalytics ? 'Hide' : 'Show'} Stats
        </button>
      </div>

      {/* Analytics Dashboard */}
      {showAnalytics && (
        <div className="mb-6">
          <DocumentsAnalytics
            totalDocuments={analytics.totalDocuments}
            totalSize={analytics.totalSize}
            recentUploads={analytics.recentUploads}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <DocumentUpload />

          {/* Search and View Controls */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <DocumentsSearch onSearch={handleSearch} initialValue={searchQuery} />
            </div>
            <DocumentsViewToggle view={viewMode} onViewChange={handleViewModeChange} />
          </div>

          {/* Documents List or Grid */}
          {isLoadingDocuments ? (
            <div className="glass elevated rounded-xl p-12 text-center">
              <p className="text-gray-400 text-sm">Loading documents...</p>
            </div>
          ) : allDocuments && allDocuments.documents.length > 0 ? (
            <>
              {viewMode === 'list' ? (
                <div className="space-y-3">
                  {allDocuments.documents.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => handleSelectDocument(doc)}
                      className={`w-full glass glass-hover elevated rounded-xl p-4 text-left transition-all spring-scale ${
                        selectedDocument?.id === doc.id
                          ? 'ring-2 ring-indigo-500'
                          : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-semibold text-white truncate mb-1">
                            {doc.filename}
                          </h3>
                          <div className="flex items-center gap-3 text-xs text-gray-400">
                            <span className="uppercase">{doc.file_type}</span>
                            <span>•</span>
                            <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                            <span>•</span>
                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                          </div>
                          {doc.category && (
                            <div className="mt-2">
                              <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-indigo-500/20 text-indigo-300">
                                {doc.category}
                              </span>
                            </div>
                          )}
                        </div>
                        <button
                          onClick={(e) => handleDelete(e, doc.id)}
                          className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          aria-label="Delete document"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <DocumentsGridView
                  documents={allDocuments.documents}
                  selectedDocumentId={selectedDocument?.id}
                  onSelectDocument={handleSelectDocument}
                  onDeleteDocument={handleDelete}
                  isDeleting={deleteDocument.isPending}
                />
              )}

              {/* Pagination Controls */}
              {allDocuments.total > pagination.limit && (
                <div className="mt-6">
                  <Pagination
                    currentPage={pagination.page}
                    totalPages={pagination.totalPages(allDocuments.total)}
                    onPageChange={pagination.setPage}
                    hasNext={pagination.hasNextPage(allDocuments.total)}
                    hasPrev={pagination.hasPrevPage()}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="glass elevated rounded-xl p-12 text-center">
              <p className="text-gray-400 text-sm">No documents found</p>
              {searchQuery && (
                <button
                  onClick={() => handleSearch('')}
                  className="mt-3 text-indigo-400 hover:text-indigo-300 text-sm"
                >
                  Clear search
                </button>
              )}
            </div>
          )}
        </div>

        <div className="lg:sticky lg:top-8 lg:self-start space-y-6">
          {selectedDocument ? (
            <>
              <div className="glass elevated-lg rounded-xl overflow-hidden fade-in">
                <div className="px-4 py-3 glass border-b border-gray-700/50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="text-gray-400" size={18} />
                    <div>
                      <h2 className="text-sm font-semibold text-white">
                        {selectedDocument.filename}
                      </h2>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {selectedDocument.file_type.toUpperCase()} • {(selectedDocument.file_size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleClosePreview}
                    className="p-1.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-800 rounded-md transition-colors"
                    aria-label="Close preview"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="p-5">
                  <DocumentViewer
                    content={documentContent?.content || ''}
                    fileType={selectedDocument.file_type}
                    filename={selectedDocument.filename}
                    isLoading={isLoading}
                  />
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
            <div className="glass elevated rounded-xl p-12 text-center">
              <div className="float">
                <FileText className="mx-auto mb-4 text-gray-400 pulse-soft" size={64} />
              </div>
              <p className="text-gray-400 text-sm font-medium">
                Select a document to preview its content
              </p>
              <p className="text-gray-500 text-xs mt-2">
                Click any document from the {viewMode} to see details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
