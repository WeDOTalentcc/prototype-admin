import { useCallback, useRef, useState } from "react"

export interface PaginationParams {
  limit: number
  cursor?: string
}

export interface PaginationResult<T> {
  items: T[]
  next_cursor?: string
  nextCursor?: string  // accept both snake_case (backend) and camelCase
  has_more?: boolean
  hasMore?: boolean
}

interface PaginationState<T> {
  items: T[]
  isLoading: boolean
  error: Error | null
  hasMore: boolean
  nextCursor: string | undefined
}

export interface UsePaginationOptions {
  limit?: number
  onError?: (error: Error) => void
}

export function usePagination<T>(
  fetchFn: (params: PaginationParams) => Promise<PaginationResult<T>>,
  options: UsePaginationOptions = {},
) {
  const { limit = 20, onError } = options

  const [state, setState] = useState<PaginationState<T>>({
    items: [],
    isLoading: false,
    error: null,
    hasMore: true,
    nextCursor: undefined,
  })

  // Refs prevent stale closures — fetchMore identity stays stable across renders.
  const isFetchingRef = useRef(false)
  const nextCursorRef = useRef<string | undefined>(undefined)
  const hasMoreRef = useRef(true)
  // Keep fetchFn current without making it a dep of fetchMore.
  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  const fetchMore = useCallback(async () => {
    if (isFetchingRef.current || !hasMoreRef.current) return

    isFetchingRef.current = true
    setState(prev => ({ ...prev, isLoading: true }))

    try {
      const result = await fetchFnRef.current({ limit, cursor: nextCursorRef.current })

      // Accept both naming conventions from backend
      const nextCursor = result.next_cursor ?? result.nextCursor
      const hasMore = result.has_more ?? result.hasMore ?? false

      nextCursorRef.current = nextCursor
      hasMoreRef.current = hasMore

      setState(prev => ({
        items: [...prev.items, ...result.items],
        nextCursor,
        hasMore,
        isLoading: false,
        error: null,
      }))
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      setState(prev => ({ ...prev, isLoading: false, error: err }))
      onError?.(err)
    } finally {
      isFetchingRef.current = false
    }
  }, [limit, onError]) // stable identity — no state in deps

  const reset = useCallback(() => {
    nextCursorRef.current = undefined
    hasMoreRef.current = true
    isFetchingRef.current = false
    setState({ items: [], isLoading: false, error: null, hasMore: true, nextCursor: undefined })
  }, [])

  return { ...state, fetchMore, reset }
}
