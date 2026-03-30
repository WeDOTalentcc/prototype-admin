"use client"

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { X, Bell, CheckCircle, AlertCircle, Info, Clock, Loader2 } from "lucide-react"

interface Notification {
  id: string
  title: string
  message: string
  type: "success" | "warning" | "info" | "error"
  timestamp: Date
  read: boolean
  actionUrl?: string
  proactive_type?: string
  priority?: string
  related_job_id?: string
  related_candidate_id?: string
}

interface BackendNotification {
  id: string
  title: string
  message: string
  notification_type: string
  proactive_type?: string
  priority?: string
  is_read: boolean
  created_at: string
  action_url?: string
  related_job_id?: string
  related_candidate_id?: string
}

interface NotificationSystemProps {
  onNotificationClick?: (notification: Notification) => void
  userId?: string
  pollingInterval?: number
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

const mapBackendNotification = (n: BackendNotification): Notification => ({
  id: n.id,
  title: n.title,
  message: n.message || "",
  type: mapNotificationType(n.notification_type),
  timestamp: new Date(n.created_at),
  read: n.is_read,
  actionUrl: n.action_url,
  proactive_type: n.proactive_type,
  priority: n.priority,
  related_job_id: n.related_job_id,
  related_candidate_id: n.related_candidate_id,
})

const NotificationItem = React.memo(({
  notification,
  onMarkAsRead,
  onRemove,
  onClick
}: {
  notification: Notification
  onMarkAsRead: (id: string) => void
  onRemove: (id: string) => void
  onClick?: (notification: Notification) => void
}) => {
  const handleMarkAsRead = useCallback(() => {
    onMarkAsRead(notification.id)
  }, [onMarkAsRead, notification.id])

  const handleRemove = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onRemove(notification.id)
  }, [onRemove, notification.id])

  const handleClick = useCallback(() => {
    if (!notification.read) {
      onMarkAsRead(notification.id)
    }
    onClick?.(notification)
  }, [notification.read, notification.id, notification, onMarkAsRead, onClick])

  const getIcon = useMemo(() => {
    switch (notification.type) {
      case "success": return <CheckCircle className="w-4 h-4 text-status-success" />
      case "warning": return <AlertCircle className="w-4 h-4 text-status-warning" />
      case "error": return <AlertCircle className="w-4 h-4 text-status-error" />
      default: return <Info className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
    }
  }, [notification.type])

  const timeAgo = useMemo(() => {
    const now = Date.now()
    const diff = now - notification.timestamp.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days > 0) return `${days}d atrás`
    if (hours > 0) return `${hours}h atrás`
    if (minutes > 0) return `${minutes}m atrás`
    return 'agora'
  }, [notification.timestamp])

  return (
    <div
      className={`relative p-2.5 rounded-md cursor-pointer transition-colors duration-200 hover:bg-lia-bg-primary dark:hover:bg-gray-800 ${
 !notification.read 
          ? "bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle" 
          : "bg-transparent border border-transparent"
      }`}
      onClick={handleClick}
     
    >
      <div className="flex items-start gap-2.5">
        <div className="flex-shrink-0 mt-0.5">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
 !notification.read 
              ? notification.type === 'success' ? 'bg-status-success/15 dark:bg-status-success/30' 
                : notification.type === 'warning' ? 'bg-status-warning/15 dark:bg-status-warning/30'
                : notification.type === 'error' ? 'bg-status-error/15 dark:bg-status-error/30'
                : 'bg-wedo-cyan/15'
              : 'bg-gray-100 dark:bg-lia-bg-secondary'
          }`}>
            {getIcon}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={`text-xs font-medium leading-tight ${
 !notification.read ? "text-gray-950" : "text-gray-600 dark:text-lia-text-tertiary"
 }`}>
              {notification.title}
            </h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              className="h-5 w-5 p-0 lia-text-base hover:lia-text-base dark:hover:lia-text-muted opacity-0 group-hover:opacity-100 transition-opacity -mt-0.5 -mr-1"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
          <p className={`text-xs mt-0.5 leading-relaxed ${
 !notification.read ? "text-gray-600" : "text-gray-800 dark:text-lia-text-primary"
 }`}>
            {notification.message}
          </p>
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-xs text-gray-600 flex items-center gap-1">
              <Clock className="w-2.5 h-2.5" />
              {timeAgo}
            </span>
            {!notification.read && (
              <button
                onClick={handleMarkAsRead}
                className="text-xs font-medium hover:underline lia-text-base"
              >
                Marcar lida
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
})

NotificationItem.displayName = 'NotificationItem'

export function NotificationSystem({ 
  onNotificationClick, 
  userId = "default_user",
  pollingInterval = 60000
}: NotificationSystemProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const lastFetchRef = useRef<number>(0)

  const backoffRef = useRef(0)

  const fetchNotifications = useCallback(async () => {
    try {
      if (backoffRef.current > 0) {
        await new Promise(r => setTimeout(r, backoffRef.current))
      }
      setIsLoading(true)
      setError(null)
      
      const response = await fetch(`/api/backend-proxy/notifications?user_id=${userId}&limit=50`)
      
      if (response.status === 429) {
        backoffRef.current = Math.min((backoffRef.current || 1000) * 2, 120000)
        setNotifications([])
        return
      }
      
      if (!response.ok) {
        setNotifications([])
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
    } catch {
      setNotifications([])
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const markAsRead = useCallback(async (id: string) => {
    try {
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      )
      
      await fetch(`/api/backend-proxy/notifications/${id}/read?user_id=${userId}`, {
        method: "POST"
      })
    } catch (err) {
    }
  }, [userId])

  const markAllAsRead = useCallback(async () => {
    try {
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
      
      await fetch(`/api/backend-proxy/notifications/read-all?user_id=${userId}`, {
        method: "POST"
      })
    } catch (err) {
    }
  }, [userId])

  const removeNotification = useCallback(async (id: string) => {
    try {
      setNotifications(prev => prev.filter(n => n.id !== id))
      
      await fetch(`/api/backend-proxy/notifications/${id}/dismiss?user_id=${userId}`, {
        method: "POST"
      })
    } catch (err) {
    }
  }, [userId])

  const toggleOpen = useCallback(() => {
    setIsOpen(prev => {
      const newState = !prev
      if (newState && Date.now() - lastFetchRef.current > 5000) {
        fetchNotifications()
      }
      return newState
    })
  }, [fetchNotifications])

  const unreadCount = useMemo(() =>
    notifications.filter(n => !n.read).length,
    [notifications]
  )

  const hasNotifications = useMemo(() =>
    notifications.length > 0,
    [notifications.length]
  )

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  useEffect(() => {
    const interval = setInterval(fetchNotifications, pollingInterval)
    return () => clearInterval(interval)
  }, [fetchNotifications, pollingInterval])

  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission()
    }
  }, [])

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleOpen}
        className="h-7 w-7 p-0 relative text-gray-800 dark:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <Bell className="w-3.5 h-3.5" />
        {unreadCount > 0 && (
          <Badge
            className="absolute -top-0.5 -right-0.5 h-4 w-4 text-xs p-0 flex items-center justify-center bg-status-error text-white border-0"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <Card className="absolute right-0 top-9 w-[340px] max-h-[420px] overflow-hidden z-50 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
          <CardContent className="p-0">
            <div className="px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-950">
                  Notificações
                  {unreadCount > 0 && (
                    <span className="ml-2 text-xs font-medium px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary">
                      {unreadCount} nova{unreadCount > 1 ? 's' : ''}
                    </span>
                  )}
                </h3>
                <div className="flex items-center gap-1">
                  {isLoading && (
                    <Loader2 className="w-3 h-3 animate-spin lia-text-base" />
                  )}
                  {unreadCount > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={markAllAsRead}
                      className="text-xs h-6 px-2 text-gray-800 dark:text-lia-text-primary hover:text-gray-800 dark:hover:text-gray-200"
                     
                    >
                      Marcar lidas
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleOpen}
                    className="h-6 w-6 p-0 lia-text-base hover:lia-text-base dark:hover:lia-text-muted"
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="max-h-[340px] overflow-y-auto bg-gray-50 dark:bg-lia-bg-primary/50">
              {error ? (
                <div className="py-10 px-4 text-center">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 text-status-error" />
                  <p className="text-sm text-status-error">{error}</p>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={fetchNotifications}
                    className="mt-2 text-xs"
                  >
                    Tentar novamente
                  </Button>
                </div>
              ) : hasNotifications ? (
                <div className="p-2 space-y-1.5">
                  {notifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={markAsRead}
                      onRemove={removeNotification}
                      onClick={onNotificationClick}
                    />
                  ))}
                </div>
              ) : (
                <div className="py-10 px-4 text-center">
                  <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm text-gray-800 dark:text-lia-text-primary">
                    {isLoading ? "Carregando..." : "Nenhuma notificação"}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export async function sendNotification(
  userId: string,
  title: string,
  message: string,
  options?: {
    channels?: string[]
    notificationType?: string
    proactiveType?: string
    priority?: string
    data?: Record<string, unknown>
    relatedJobId?: string
    relatedCandidateId?: string
    suggestedActions?: string[]
  }
): Promise<{ success: boolean; data?: unknown }> {
  try {
    const response = await fetch("/api/backend-proxy/notifications/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        title,
        message,
        channels: options?.channels || ["chat", "bell"],
        notification_type: options?.notificationType || "info",
        proactive_type: options?.proactiveType,
        priority: options?.priority || "normal",
        data: options?.data,
        related_job_id: options?.relatedJobId,
        related_candidate_id: options?.relatedCandidateId,
        suggested_actions: options?.suggestedActions,
      }),
    })

    return await response.json()
  } catch (error) {
    return { success: false }
  }
}
