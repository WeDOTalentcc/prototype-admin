import { useEffect, useRef, useCallback } from 'react'

const REFRESH_INTERVAL = 10 * 60 * 1000 // Check every 10 minutes

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
      // JWT users: refresh via JWT endpoint first
      const jwtResponse = await fetch('/api/auth/session/refresh', {
        method: 'POST',
        credentials: 'include',
      })

      if (jwtResponse.ok) {
        // skipped=true means token still valid, no refresh needed — also fine
        return true
      }

      if (jwtResponse.status === 401) {
        // JWT refresh token expired — try WorkOS SSO as fallback (SSO users)
        const ssoResponse = await fetch('/api/auth/workos/refresh', {
          method: 'POST',
          credentials: 'include',
        })

        if (!ssoResponse.ok && ssoResponse.status === 401) {
          // Both failed — session truly expired
          window.location.href = '/login'
          return false
        }

        return ssoResponse.ok
      }

      return false
    } catch {
      return false
    } finally {
      isRefreshingRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

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
