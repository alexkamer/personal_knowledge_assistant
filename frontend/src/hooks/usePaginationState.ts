/**
 * Shared hook for managing pagination state with URL synchronization.
 *
 * This hook manages pagination parameters (page, limit, filters, sorting)
 * and syncs them with URL query parameters for proper browser navigation.
 */
import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

export interface PaginationState {
  page: number;
  limit: number;
  offset: number;
}

export interface PaginationActions {
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  resetPagination: () => void;
}

export interface UsePaginationStateOptions {
  defaultPage?: number;
  defaultLimit?: number;
  paramPrefix?: string; // Prefix for URL params to avoid conflicts (e.g., 'doc_' for documents)
}

export interface UsePaginationStateResult extends PaginationState, PaginationActions {
  hasNextPage: (total?: number) => boolean;
  hasPrevPage: () => boolean;
  totalPages: (total?: number) => number;
}

/**
 * Hook for managing pagination state with URL synchronization.
 *
 * @example
 * ```tsx
 * const pagination = usePaginationState({
 *   defaultLimit: 20,
 *   paramPrefix: 'doc_'
 * });
 *
 * // Use in API call
 * const { data } = useDocuments(pagination.offset, pagination.limit);
 *
 * // Use in UI
 * <button onClick={pagination.nextPage}>Next</button>
 * ```
 */
export function usePaginationState(
  options: UsePaginationStateOptions = {}
): UsePaginationStateResult {
  const {
    defaultPage = 1,
    defaultLimit = 20,
    paramPrefix = '',
  } = options;

  const [searchParams, setSearchParams] = useSearchParams();

  // Parse current pagination state from URL
  const page = useMemo(() => {
    const pageParam = searchParams.get(`${paramPrefix}page`);
    return pageParam ? Math.max(1, parseInt(pageParam, 10)) : defaultPage;
  }, [searchParams, paramPrefix, defaultPage]);

  const limit = useMemo(() => {
    const limitParam = searchParams.get(`${paramPrefix}limit`);
    return limitParam ? Math.max(1, parseInt(limitParam, 10)) : defaultLimit;
  }, [searchParams, paramPrefix, defaultLimit]);

  const offset = useMemo(() => {
    return (page - 1) * limit;
  }, [page, limit]);

  // Update URL with new pagination state
  const updatePaginationParams = useCallback((updates: Partial<{ page: number; limit: number }>) => {
    setSearchParams((prev) => {
      const newParams = new URLSearchParams(prev);

      if (updates.page !== undefined) {
        if (updates.page === defaultPage) {
          newParams.delete(`${paramPrefix}page`);
        } else {
          newParams.set(`${paramPrefix}page`, updates.page.toString());
        }
      }

      if (updates.limit !== undefined) {
        if (updates.limit === defaultLimit) {
          newParams.delete(`${paramPrefix}limit`);
        } else {
          newParams.set(`${paramPrefix}limit`, updates.limit.toString());
        }
      }

      return newParams;
    });
  }, [setSearchParams, paramPrefix, defaultPage, defaultLimit]);

  const setPage = useCallback((newPage: number) => {
    updatePaginationParams({ page: Math.max(1, newPage) });
  }, [updatePaginationParams]);

  const setLimit = useCallback((newLimit: number) => {
    updatePaginationParams({ limit: Math.max(1, newLimit), page: 1 });
  }, [updatePaginationParams]);

  const nextPage = useCallback(() => {
    setPage(page + 1);
  }, [page, setPage]);

  const prevPage = useCallback(() => {
    setPage(Math.max(1, page - 1));
  }, [page, setPage]);

  const resetPagination = useCallback(() => {
    updatePaginationParams({ page: defaultPage, limit: defaultLimit });
  }, [updatePaginationParams, defaultPage, defaultLimit]);

  const hasNextPage = useCallback((total?: number) => {
    if (total === undefined) return true; // Don't know, assume there might be more
    return offset + limit < total;
  }, [offset, limit]);

  const hasPrevPage = useCallback(() => {
    return page > 1;
  }, [page]);

  const totalPages = useCallback((total?: number) => {
    if (total === undefined) return 1;
    return Math.ceil(total / limit);
  }, [limit]);

  return {
    page,
    limit,
    offset,
    setPage,
    setLimit,
    nextPage,
    prevPage,
    resetPagination,
    hasNextPage,
    hasPrevPage,
    totalPages,
  };
}
