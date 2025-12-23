/**
 * Loading skeleton component for better UX during data fetching
 */

interface LoadingSkeletonProps {
  type?: 'card' | 'list' | 'text' | 'circle';
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ type = 'card', count = 1, className = '' }: LoadingSkeletonProps) {
  const skeletons = Array.from({ length: count }, (_, i) => i);

  if (type === 'card') {
    return (
      <>
        {skeletons.map((i) => (
          <div
            key={i}
            className={`bg-white/90 dark:bg-gray-900/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-800/50 rounded-2xl shadow-lg p-5 animate-pulse ${className}`}
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-xl" />
              <div className="flex-1 space-y-3">
                <div className="h-5 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg w-3/4" />
                <div className="h-4 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg w-full" />
                <div className="h-4 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg w-2/3" />
              </div>
            </div>
          </div>
        ))}
      </>
    );
  }

  if (type === 'list') {
    return (
      <>
        {skeletons.map((i) => (
          <div
            key={i}
            className={`flex items-center gap-3 p-4 bg-white/90 dark:bg-gray-900/80 backdrop-blur-xl border border-gray-200/50 dark:border-gray-800/50 rounded-xl animate-pulse ${className}`}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg w-2/3" />
              <div className="h-3 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg w-1/2" />
            </div>
          </div>
        ))}
      </>
    );
  }

  if (type === 'text') {
    return (
      <>
        {skeletons.map((i) => (
          <div
            key={i}
            className={`h-4 bg-gradient-to-r from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-lg animate-pulse ${className}`}
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </>
    );
  }

  if (type === 'circle') {
    return (
      <>
        {skeletons.map((i) => (
          <div
            key={i}
            className={`w-12 h-12 bg-gradient-to-br from-stone-200 to-stone-300 dark:from-stone-700 dark:to-stone-800 rounded-full animate-pulse ${className}`}
          />
        ))}
      </>
    );
  }

  return null;
}

export default LoadingSkeleton;
