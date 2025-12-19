/**
 * Reusable pagination component with accessible controls.
 */
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  hasNext?: boolean;
  hasPrev?: boolean;
  showFirstLast?: boolean;
  showPageNumbers?: boolean;
  className?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  hasNext = true,
  hasPrev = true,
  showFirstLast = true,
  showPageNumbers = true,
  className = '',
}: PaginationProps) {
  // Generate page numbers to display (max 7: 1 ... 4 5 6 ... 10)
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible + 2) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const pageNumbers = showPageNumbers ? getPageNumbers() : [];

  if (totalPages <= 1 && !hasNext) {
    return null; // Don't show pagination if only one page
  }

  return (
    <nav
      className={`flex items-center justify-between gap-2 ${className}`}
      aria-label="Pagination"
    >
      <div className="flex items-center gap-1">
        {/* First Page */}
        {showFirstLast && (
          <button
            onClick={() => onPageChange(1)}
            disabled={!hasPrev || currentPage === 1}
            className="p-2 rounded-lg glass glass-hover spring-scale disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 text-gray-300"
            aria-label="First page"
            title="First page"
          >
            <ChevronsLeft size={18} />
          </button>
        )}

        {/* Previous Page */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrev}
          className="p-2 rounded-lg glass glass-hover spring-scale disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 text-gray-300"
          aria-label="Previous page"
          title="Previous page"
        >
          <ChevronLeft size={18} />
        </button>

        {/* Page Numbers */}
        {showPageNumbers && (
          <div className="flex items-center gap-1 mx-2">
            {pageNumbers.map((page, index) => {
              if (page === '...') {
                return (
                  <span
                    key={`ellipsis-${index}`}
                    className="px-2 text-gray-500"
                    aria-hidden="true"
                  >
                    ...
                  </span>
                );
              }

              const pageNum = page as number;
              const isActive = pageNum === currentPage;

              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={`
                    min-w-[36px] px-3 py-1.5 rounded-lg text-sm font-medium transition-all spring-scale
                    ${
                      isActive
                        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                        : 'glass glass-hover text-gray-300'
                    }
                  `}
                  aria-label={`Page ${pageNum}`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
        )}

        {/* Next Page */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext}
          className="p-2 rounded-lg glass glass-hover spring-scale disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 text-gray-300"
          aria-label="Next page"
          title="Next page"
        >
          <ChevronRight size={18} />
        </button>

        {/* Last Page */}
        {showFirstLast && totalPages > 1 && (
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={!hasNext || currentPage === totalPages}
            className="p-2 rounded-lg glass glass-hover spring-scale disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 text-gray-300"
            aria-label="Last page"
            title="Last page"
          >
            <ChevronsRight size={18} />
          </button>
        )}
      </div>

      {/* Page Info */}
      <div className="text-sm text-gray-400">
        Page <span className="font-semibold text-gray-200">{currentPage}</span>
        {totalPages > 1 && (
          <>
            {' '}
            of <span className="font-semibold text-gray-200">{totalPages}</span>
          </>
        )}
      </div>
    </nav>
  );
}

/**
 * Simple pagination component for infinite scroll scenarios.
 */
export interface LoadMorePaginationProps {
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading?: boolean;
  className?: string;
}

export function LoadMorePagination({
  onLoadMore,
  hasMore,
  isLoading = false,
  className = '',
}: LoadMorePaginationProps) {
  if (!hasMore && !isLoading) {
    return null;
  }

  return (
    <div className={`flex justify-center ${className}`}>
      <button
        onClick={onLoadMore}
        disabled={!hasMore || isLoading}
        className="px-6 py-2.5 rounded-lg glass glass-hover spring-scale text-sm font-medium text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
      >
        {isLoading ? 'Loading...' : hasMore ? 'Load More' : 'No more items'}
      </button>
    </div>
  );
}
