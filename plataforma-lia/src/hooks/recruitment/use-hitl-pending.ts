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
      // Task #801 (C4): usar fetchWithRetry para que erros transientes de
      // rede (cold-start, HMR) sejam reentrados e não sumam com a contagem.
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const res = await fetchWithRetry(
        "/api/backend-proxy/hitl/pending",
        {},
        { attempts: 3, timeoutMs: 10000, retryDelaysMs: [0, 1000, 3000] },
      )
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const data = await res.json()
      setItems(data.pending || [])
      setError(null)
    } catch (err) {
      // Não troca a lista preservada — apenas sinaliza erro.
      setError(err instanceof Error ? err.message : "Network error")
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

    // QW4 audit 2026-05-22: visibility guard. Antes, polling de 30s rodava
    // em toda rota com sidebar mesmo com aba em background. Quando backend
    // estava lento, saturava event loop do Next dev. Agora: skipa quando
    // aba hidden, refetch imediato quando user volta.
    const tick = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return
      fetchPending()
    }
    intervalRef.current = setInterval(tick, pollingIntervalMs)
    const onVisible = () => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        fetchPending()
      }
    }
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisible)
    }

    window.addEventListener("hitl:approval_required", handleApprovalRequired)
    window.addEventListener("hitl:approval_resolved", handleApprovalResolved)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", onVisible)
      }
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
