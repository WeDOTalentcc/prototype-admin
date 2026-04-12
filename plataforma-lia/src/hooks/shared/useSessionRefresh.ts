import { useEffect, useRef, useCallback } from 'react'

const REFRESH_INTERVAL = 5 * 60 * 1000 // Check every 5 minutes
const REFRESH_THRESHOLD = 30 * 60 * 1000 // Refresh if less than 30 min left

interface SessionRefreshHook {
  refreshSession: () => Promise<boolean>
  isRefreshing: boolean
}

export function useSessionRefresh(enabled: boolean = true): SessionRefreshHook {
  const isRefreshingRef = useRef(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const refreshSession = useCallback(async (): Promise<boolean> => {
    if (isRefreshingRef.current) return false
    
    isRefreshingRef.current = true
    try {
      const response = await fetch('/api/auth/workos/refresh', {
        method: 'POST',
        credentials: 'include',
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          // Session expired or invalid, redirect to login
          window.location.href = '/login'
          return false
        }
        return false
      }
      
      const data = await response.json()
      return data.refreshed
    } catch (error) {
      return false
    } finally {
      isRefreshingRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    // Initial refresh check
    refreshSession()

    // Set up periodic refresh
    intervalRef.current = setInterval(() => {
      refreshSession()
    }, REFRESH_INTERVAL)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, refreshSession])

  return {
    refreshSession,
    isRefreshing: isRefreshingRef.current,
  }
}
