"use client"

import { useState, useEffect, useCallback, useMemo, useRef } from "react"

export interface Notification {
  id: string
  title: string
  message: string
  type: "success" | "warning" | "info" | "error"
  category: NotificationCategory
  timestamp: Date
  read: boolean
  actionUrl?: string
  actionLabel?: string
  proactive_type?: string
  priority?: string
  related_job_id?: string
  related_candidate_id?: string
}

export type NotificationCategory =
  | "pipeline"
  | "productivity"
  | "communication"
  | "predictive"
  | "system"

export const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  pipeline: "Pipeline",
  productivity: "Produtividade",
  communication: "Comunicação",
  predictive: "Preditivo",
  system: "Sistema",
}

interface BackendNotification {
  id: string
  title: string
  message: string
  notification_type: string
  category?: string
  proactive_type?: string
  priority?: string
  is_read: boolean
  created_at: string
  action_url?: string
  action_label?: string
  related_job_id?: string
  related_candidate_id?: string
}

const mapNotificationType = (type: string): "success" | "warning" | "info" | "error" => {
  switch (type) {
    case "success": return "success"
    case "warning": return "warning"
    case "urgent":
    case "error": return "error"
    case "action_required": return "warning"
    default: return "info"
  }
}

const mapCategory = (category?: string): NotificationCategory => {
  if (category && category in CATEGORY_LABELS) return category as NotificationCategory
  return "system"
}


interface BackendAlert {
  id: string
  title: string
  message: string
  severity?: string
  category?: string
  condition?: string
  is_read?: boolean
  is_resolved?: boolean
  created_at?: string
  action_url?: string
  action_label?: string
  related_job_id?: string
  related_candidate_id?: string
}

const mapBackendAlert = (a: BackendAlert): Notification => ({
  id: `alert-${a.id}`,
  title: a.title,
  message: a.message || "",
  type: a.severity === "urgent" || a.severity === "error" ? "error"
    : a.severity === "warning" ? "warning"
    : a.severity === "success" ? "success"
    : "info",
  category: (a.category as NotificationCategory) ?? "system",
  timestamp: a.created_at ? new Date(a.created_at) : new Date(),
  read: a.is_read ?? false,
  actionUrl: a.action_url,
  actionLabel: a.action_label,
  related_job_id: a.related_job_id,
  related_candidate_id: a.related_candidate_id,
})

const mapBackendNotification = (n: BackendNotification): Notification => ({
  id: n.id,
  title: n.title,
  message: n.message || "",
  type: mapNotificationType(n.notification_type),
  category: mapCategory(n.category),
  timestamp: new Date(n.created_at),
  read: n.is_read,
  actionUrl: n.action_url,
  actionLabel: n.action_label,
  proactive_type: n.proactive_type,
  priority: n.priority,
  related_job_id: n.related_job_id,
  related_candidate_id: n.related_candidate_id,
})

interface UseNotificationsOptions {
  userId?: string
  pollingInterval?: number
}

export function useNotifications({
  userId = "default_user",
  pollingInterval = 60000,
}: UseNotificationsOptions = {}) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState<NotificationCategory | null>(null)
  const [serverUnreadCount, setServerUnreadCount] = useState<number | null>(null)
  const lastFetchRef = useRef<number>(0)
  const backoffRef = useRef(0)

  const fetchNotifications = useCallback(async () => {
    try {
      if (backoffRef.current > 0) {
        await new Promise(r => setTimeout(r, backoffRef.current))
      }
      setIsLoading(true)
      setError(null)

      const { fetchWithRetry } = await import("@/services/lia-api/base")

      // Dual-fetch: notifications (historical delivery records) + active alerts.
      // Alerts with channel_bell=true flow through proactive_alert_service into
      // /notifications, but undelivered active alerts live only in /alerts.
      // Merging both ensures the panel mirrors Teams + AlertPreferences settings.
      const [notifResponse, alertsResponse] = await Promise.allSettled([
        fetchWithRetry(`/api/backend-proxy/notifications?user_id=${userId}&limit=50`),
        fetchWithRetry(`/api/backend-proxy/alerts?user_id=${userId}&limit=30`),
      ])

      if (
        notifResponse.status === "fulfilled" &&
        notifResponse.value.status === 429
      ) {
        backoffRef.current = Math.min((backoffRef.current || 1000) * 2, 120000)
        setError("Limite de requisições atingido. Tentando novamente...")
        return
      }

      backoffRef.current = 0

      const merged: Notification[] = []
      const seenIds = new Set<string>()

      // 1. Notification records (bell-channel delivery)
      if (notifResponse.status === "fulfilled" && notifResponse.value.ok) {
        const data = await notifResponse.value.json()
        if (data.success && data.data?.notifications) {
          for (const n of data.data.notifications.map(mapBackendNotification)) {
            seenIds.add(n.id)
            merged.push(n)
          }
        }
      } else if (notifResponse.status === "fulfilled" && !notifResponse.value.ok) {
        setError(`Erro ao carregar notificações (${notifResponse.value.status})`)
      }

      // 2. Active alerts (same source as Teams digest + AlertPreferences).
      // Skip alerts already present as notifications (dedup by condition id prefix).
      if (alertsResponse.status === "fulfilled" && alertsResponse.value.ok) {
        const alertData = await alertsResponse.value.json()
        const alertList: BackendAlert[] = Array.isArray(alertData)
          ? alertData
          : alertData.alerts ?? alertData.data ?? []
        for (const a of alertList) {
          if (a.is_resolved) continue
          const mappedId = `alert-${a.id}`
          if (!seenIds.has(mappedId)) {
            seenIds.add(mappedId)
            merged.push(mapBackendAlert(a))
          }
        }
      }

      // Sort merged list by timestamp desc
      merged.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      setNotifications(merged)
      lastFetchRef.current = Date.now()

      fetchWithRetry(`/api/backend-proxy/notifications/unread-count?user_id=${userId}`)
        .then(r => r.json())
        .then(d => {
          if (typeof d.unread_count === "number") setServerUnreadCount(d.unread_count)
          else if (d.data && typeof d.data.unread_count === "number") setServerUnreadCount(d.data.unread_count)
        })
        .catch(() => { /* unread-count is supplementary, swallow */ })
    } catch (err) {
      setError("Falha ao conectar com o servidor de notificações")
      setNotifications([])
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const markAsRead = useCallback(async (id: string) => {
    try {
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const response = await fetchWithRetry(
        `/api/backend-proxy/notifications/${id}/read?user_id=${userId}`,
        { method: "POST" },
      )
      const data = await response.json()
      if (data.success) {
        setNotifications(prev =>
          prev.map(n => n.id === id ? { ...n, read: true } : n)
        )
        setServerUnreadCount(prev => prev !== null && prev > 0 ? prev - 1 : prev)
      }
    } catch (error) {
      console.error("[use-notifications] markAsRead failed:", error)
    }
  }, [userId])

  const markAllAsRead = useCallback(async () => {
    try {
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const response = await fetchWithRetry(
        `/api/backend-proxy/notifications/read-all?user_id=${userId}`,
        { method: "POST" },
      )
      const data = await response.json()
      if (data.success) {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })))
        setServerUnreadCount(0)
      }
    } catch {
    }
  }, [userId])

  const removeNotification = useCallback(async (id: string) => {
    try {
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const response = await fetchWithRetry(
        `/api/backend-proxy/notifications/${id}/dismiss?user_id=${userId}`,
        { method: "POST" },
      )
      const data = await response.json()
      if (data.success) {
        setNotifications(prev => prev.filter(n => n.id !== id))
      }
    } catch (error) {
      console.error("[use-notifications] markAllAsRead failed:", error)
    }
  }, [userId])

  const filteredNotifications = useMemo(() => {
    if (!activeCategory) return notifications
    return notifications.filter(n => n.category === activeCategory)
  }, [notifications, activeCategory])

  const unreadCount = useMemo(() =>
    serverUnreadCount !== null ? serverUnreadCount : notifications.filter(n => !n.read).length,
    [notifications, serverUnreadCount]
  )

  const hasNotifications = useMemo(() =>
    notifications.length > 0,
    [notifications.length]
  )

  const refreshIfStale = useCallback(() => {
    if (Date.now() - lastFetchRef.current > 5000) {
      fetchNotifications()
    }
  }, [fetchNotifications])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  useEffect(() => {
    // QW4 audit 2026-05-22: visibility guard. Antes, este polling rodava em
    // toda rota com sidebar montada, mesmo com aba em background. Quando
    // backend ficava lento, polls saturavam event loop do Next dev server.
    // Agora: skipa o poll quando aba esta hidden + refetch imediato quando
    // user volta pra aba (sync inteligente).
    const tick = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return
      fetchNotifications()
    }
    const interval = setInterval(tick, pollingInterval)
    const onVisible = () => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        fetchNotifications()
      }
    }
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisible)
    }
    return () => {
      clearInterval(interval)
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", onVisible)
      }
    }
  }, [fetchNotifications, pollingInterval])

  return {
    notifications: filteredNotifications,
    allNotifications: notifications,
    isLoading,
    error,
    unreadCount,
    hasNotifications,
    activeCategory,
    setActiveCategory,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    removeNotification,
    refreshIfStale,
  }
}
