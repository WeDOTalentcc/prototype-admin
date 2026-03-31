'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

let ncBackoffMs = 0

async function fetchNotificationsApi(endpoint: string, options?: RequestInit) {
  if (ncBackoffMs > 0) {
    await new Promise(r => setTimeout(r, ncBackoffMs))
  }
  const response = await fetch(`/api/backend-proxy${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  if (response.status === 429) {
    ncBackoffMs = Math.min((ncBackoffMs || 1000) * 2, 120000)
    return { success: false, data: { notifications: [] } }
  }
  if (!response.ok) {
    return { success: false, data: { notifications: [] } }
  }
  ncBackoffMs = 0
  const data = await response.json()
  return data
}

export interface NotificationItem {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'urgent' | 'action_required'
  category?: string
  source_agent?: string
  is_read: boolean
  created_at: string
  action_url?: string
  action_label?: string
  related_job_id?: string
  related_candidate_id?: string
}

export interface UseNotificationsOptions {
  userId?: string
  pollingIntervalMs?: number
}

export interface UseNotificationsReturn {
  notifications: NotificationItem[]
  unreadCount: number
  isLoading: boolean
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  filter: string | null
  setFilter: (filter: string | null) => void
  filteredNotifications: NotificationItem[]
  categories: string[]
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  dismissNotification: (notificationId: string) => Promise<void>
  refreshNotifications: () => Promise<void>
}

export function useNotifications({
  userId = 'default_user',
  pollingIntervalMs = 60000,
}: UseNotificationsOptions = {}): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const [filter, setFilter] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const isMounted = useRef(true)

  const fetchNotifications = useCallback(async () => {
    if (!isMounted.current) return
    setIsLoading(true)
    try {
      const response = await fetchNotificationsApi(`/notifications?user_id=${userId}&limit=50`)

      if (isMounted.current && response.success && response.data?.notifications) {
        setNotifications(response.data.notifications)
        setUnreadCount(response.data.notifications.filter((n: NotificationItem) => !n.is_read).length)
      }
    } catch {
    } finally {
      if (isMounted.current) setIsLoading(false)
    }
  }, [userId])

  const fetchSummary = useCallback(async () => {
    if (!isMounted.current) return
    try {
      const response = await fetchNotificationsApi(`/notifications/summary?user_id=${userId}`)

      if (isMounted.current && response.success && response.data) {
        setUnreadCount(response.data.unread_count || 0)
      }
    } catch {
    }
  }, [userId])

  useEffect(() => {
    isMounted.current = true
    fetchSummary()
    const interval = setInterval(fetchSummary, pollingIntervalMs)
    return () => {
      isMounted.current = false
      clearInterval(interval)
    }
  }, [fetchSummary, pollingIntervalMs])

  useEffect(() => {
    if (isOpen) {
      fetchNotifications()
    }
  }, [isOpen, fetchNotifications])

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      const response = await fetchNotificationsApi(`/notifications/${notificationId}/read?user_id=${userId}`, {
        method: 'POST'
      })

      if (response.success) {
        setNotifications(prev => {
          const target = prev.find(n => n.id === notificationId)
          if (target && !target.is_read) {
            setUnreadCount(c => Math.max(0, c - 1))
          }
          return prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
        })
      }
    } catch {
    }
  }, [userId])

  const markAllAsRead = useCallback(async () => {
    try {
      const response = await fetchNotificationsApi(`/notifications/read-all?user_id=${userId}`, {
        method: 'POST'
      })

      if (response.success) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
        setUnreadCount(0)
      }
    } catch {
    }
  }, [userId])

  const dismissNotification = useCallback(async (notificationId: string) => {
    try {
      const response = await fetchNotificationsApi(`/notifications/${notificationId}/dismiss?user_id=${userId}`, {
        method: 'POST'
      })

      if (response.success) {
        setNotifications(prev => {
          const target = prev.find(n => n.id === notificationId)
          if (target && !target.is_read) {
            setUnreadCount(c => Math.max(0, c - 1))
          }
          return prev.filter(n => n.id !== notificationId)
        })
      }
    } catch {
    }
  }, [userId])

  const filteredNotifications = filter
    ? notifications.filter(n => n.category === filter)
    : notifications

  const categories = [...new Set(notifications.map(n => n.category).filter(Boolean))] as string[]

  return {
    notifications,
    unreadCount,
    isLoading,
    isOpen,
    setIsOpen,
    filter,
    setFilter,
    filteredNotifications,
    categories,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    refreshNotifications: fetchNotifications,
  }
}
