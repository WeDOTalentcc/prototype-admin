"use client"

import { useState, useEffect, useCallback, useRef } from "react"

export interface HitlPendingItem {
  pending_id: string
  thread_id: string
  domain: string
  action: string
  description: string
  data: Record<string, unknown>
  ws_session_id: string
  company_id?: string
  requested_at: string
  created_at?: string
  status?: string
}

interface UseHitlPendingOptions {
  enabled?: boolean
  pollingIntervalMs?: number
}

export function useHitlPending(options: UseHitlPendingOptions = {}) {
  const { enabled = true, pollingIntervalMs = 30000 } = options
  const [items, setItems] = useState<HitlPendingItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchPending = useCallback(async () => {
    try {
      setIsLoading(true)
      const res = await fetch("/api/backend-proxy/hitl/pending")
      if (!res.ok) {
        setError("Failed to fetch")
        return
      }
      const data = await res.json()
      setItems(data.pending || [])
      setError(null)
    } catch {
      setError("Network error")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleApprovalRequired = useCallback((event: Event) => {
    const detail = (event as CustomEvent).detail as HitlPendingItem | undefined
    if (detail?.pending_id) {
      setItems((prev) => {
        if (prev.some((i) => i.pending_id === detail.pending_id)) return prev
        return [detail, ...prev]
      })
    } else {
      fetchPending()
    }
  }, [fetchPending])

  const handleApprovalResolved = useCallback((event: Event) => {
    const detail = (event as CustomEvent).detail as { pending_id?: string } | undefined
    if (detail?.pending_id) {
      setItems((prev) => prev.filter((i) => i.pending_id !== detail.pending_id))
    } else {
      fetchPending()
    }
  }, [fetchPending])

  useEffect(() => {
    if (!enabled) return

    fetchPending()

    intervalRef.current = setInterval(fetchPending, pollingIntervalMs)

    window.addEventListener("hitl:approval_required", handleApprovalRequired)
    window.addEventListener("hitl:approval_resolved", handleApprovalResolved)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      window.removeEventListener("hitl:approval_required", handleApprovalRequired)
      window.removeEventListener("hitl:approval_resolved", handleApprovalResolved)
    }
  }, [enabled, pollingIntervalMs, fetchPending, handleApprovalRequired, handleApprovalResolved])

  return {
    items,
    count: items.length,
    isLoading,
    error,
    refresh: fetchPending,
  }
}
