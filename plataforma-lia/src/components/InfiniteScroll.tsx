import { useEffect, useRef } from "react"

interface InfiniteScrollProps {
  onLoadMore: () => void
  hasMore: boolean
  isLoading: boolean
  /** px below viewport edge to trigger load (default 200) */
  threshold?: number
  children: React.ReactNode
  loadingFallback?: React.ReactNode
}

/**
 * Wraps children with an IntersectionObserver sentinel that calls onLoadMore
 * when the sentinel enters the viewport. Safe for React StrictMode (double-mount).
 */
export function InfiniteScroll({
  onLoadMore,
  hasMore,
  isLoading,
  threshold = 200,
  children,
  loadingFallback = null,
}: InfiniteScrollProps) {
  const sentinelRef = useRef<HTMLDivElement>(null)
  // Keep callbacks stable without recreating the observer on every render.
  const onLoadMoreRef = useRef(onLoadMore)
  onLoadMoreRef.current = onLoadMore
  const hasMoreRef = useRef(hasMore)
  hasMoreRef.current = hasMore
  const isLoadingRef = useRef(isLoading)
  isLoadingRef.current = isLoading

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMoreRef.current && !isLoadingRef.current) {
          onLoadMoreRef.current()
        }
      },
      { rootMargin: `${threshold}px` },
    )

    observer.observe(sentinel)
    return () => observer.unobserve(sentinel)
  }, [threshold]) // observer only recreated when threshold changes

  return (
    <>
      {children}
      {hasMore && (
        <div ref={sentinelRef} aria-hidden="true" style={{ minHeight: 1 }}>
          {isLoading ? loadingFallback : null}
        </div>
      )}
    </>
  )
}
