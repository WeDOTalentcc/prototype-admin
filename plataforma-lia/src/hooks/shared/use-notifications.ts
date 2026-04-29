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

      // [Task #801/#803] usar fetchWithRetry em vez de fetch() cru — herda
      // retry, timeout e HttpError(transientNetworkError) consistentes.
      const { fetchWithRetry } = await import("@/services/lia-api/base")
      const response = await fetchWithRetry(
        `/api/backend-proxy/notifications?user_id=${userId}&limit=50`,
      )

      if (response.status === 429) {
        backoffRef.current = Math.min((backoffRef.current || 1000) * 2, 120000)
        setError("Limite de requisições atingido. Tentando novamente...")
        return
      }

      if (!response.ok) {
        setError(`Erro ao carregar notificações (${response.status})`)
        return
      }

      backoffRef.current = 0

      const data = await response.json()

      if (data.success && data.data?.notifications) {
        const mappedNotifications = data.data.notifications.map(mapBackendNotification)
        setNotifications(mappedNotifications)
        lastFetchRef.current = Date.now()
      } else {
        setNotifications([])
      }

      fetchWithRetry(`/api/backend-proxy/notifications/unread-count?user_id=${userId}`)
        .then(r => r.json())
        .then(d => {
          if (typeof d.unread_count === "number") setServerUnreadCount(d.unread_count)
          else if (d.data && typeof d.data.unread_count === "number") setServerUnreadCount(d.data.unread_count)
        })
        .catch((err) => { console.error('[useNotifications] unread-count fetch failed', err) })
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
    } catch {
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
    } catch {
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
    const interval = setInterval(fetchNotifications, pollingInterval)
    return () => clearInterval(interval)
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
