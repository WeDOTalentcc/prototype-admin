"use client"

import { useState, useEffect, useCallback } from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Bell, X, TrendingUp, AlertTriangle, UserMinus, UserPlus,
  Building, Target, Zap, Eye, Settings, Loader2, RefreshCw
} from"lucide-react"
import { liaApi, BackendNotification } from"@/services/lia-api"

interface IntelligenceNotification {
  id: string
  type: string
  priority: string
  timestamp: Date
  title: string
  message: string
  details: Record<string, unknown>
  actions: string[]
  read: boolean
}

interface IntelligenceNotificationsProps {
  onNotificationAction?: (notificationId: string, action: string) => void
  userId?: string
}

const mapBackendToFrontend = (notification: BackendNotification): IntelligenceNotification => {
  const typeMapping: Record<string, string> = {
    'talent_movement': 'talent_movement',
    'salary_alert': 'salary_alert',
    'hiring_trend': 'hiring_trend',
    'competitor_move': 'competitor_move',
    'proactive_insight': 'hiring_trend',
    'system_update': 'system',
    'job_match': 'hiring_trend',
    'candidate_action': 'talent_movement',
  }

  const getActions = (type: string): string[] => {
    switch (type) {
      case 'talent_movement':
        return ['approach', 'track', 'dismiss']
      case 'salary_alert':
        return ['review_salaries', 'update_offer', 'dismiss']
      case 'hiring_trend':
        return ['map_candidates', 'create_pipeline', 'dismiss']
      case 'competitor_move':
        return ['counter_strategy', 'protect_talents', 'dismiss']
      default:
        return ['view', 'dismiss']
    }
  }

  return {
    id: notification.id,
    type: typeMapping[notification.notification_type] || notification.notification_type || 'system',
    priority: notification.priority || 'medium',
    timestamp: new Date(notification.created_at),
    title: notification.title,
    message: notification.message || '',
    details: notification.extra_data || {},
    actions: getActions(typeMapping[notification.notification_type] || notification.notification_type),
    read: notification.is_read
  }
}

export function IntelligenceNotifications({ 
  onNotificationAction, 
  userId = 'default_user' 
}: IntelligenceNotificationsProps) {
  const [notifications, setNotifications] = useState<IntelligenceNotification[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [urgentCount, setUrgentCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetch, setLastFetch] = useState<Date | null>(null)

  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await liaApi.getNotifications(userId, false, undefined, 50)

      if (response.success && response.data) {
        const mappedNotifications = (response.data.notifications || []).map(mapBackendToFrontend)
        setNotifications(mappedNotifications)
        setUnreadCount(response.data.unread_count || 0)
        setUrgentCount(response.data.urgent_count || 0)
        setLastFetch(new Date())
      } else {
        setNotifications([])
      }
    } catch {
      setNotifications([])
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await liaApi.getUnreadCount(userId)
      if (response.success && response.data) {
        setUnreadCount(response.data.unread_count || 0)
        setUrgentCount(response.data.urgent_count || 0)
      }
    } catch (err) {
    }
  }, [userId])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchUnreadCount()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  useEffect(() => {
    if (isOpen) {
      fetchNotifications()
    }
  }, [isOpen, fetchNotifications])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
      case 'urgent':
        return ' border-status-error/30'
      case 'medium':
        return ' border-status-warning/30'
      case 'low':
        return ' border-lia-border-default dark:border-lia-border-default'
      default:
        return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'talent_movement':
        return <UserMinus className="w-4 h-4" />
      case 'salary_alert':
        return <TrendingUp className="w-4 h-4" />
      case 'hiring_trend':
        return <UserPlus className="w-4 h-4" />
      case 'competitor_move':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Bell className="w-4 h-4" />
    }
  }

  const handleAction = async (notificationId: string, action: string) => {
    if (onNotificationAction) {
      onNotificationAction(notificationId, action)
    }

    try {
      if (action === 'dismiss') {
        await liaApi.dismissNotification(notificationId, userId)
        setNotifications(prev => prev.filter(n => n.id !== notificationId))
        setUnreadCount(prev => Math.max(0, prev - 1))
      } else {
        await liaApi.markNotificationAsRead(notificationId, userId)
        setNotifications(prev =>
          prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        )
        const wasUnread = notifications.find(n => n.id === notificationId && !n.read)
        if (wasUnread) {
          setUnreadCount(prev => Math.max(0, prev - 1))
        }
      }

      switch (action) {
        case 'approach':
          break
        case 'track':
          break
        case 'review_salaries':
          break
        case 'map_candidates':
          break
        case 'counter_strategy':
          break
      }
    } catch (err) {
    }
  }

  const markAllAsRead = async () => {
    try {
      await liaApi.markAllNotificationsAsRead(userId)
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (err) {
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - timestamp.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Agora'
    if (diffInMinutes < 60) return `${diffInMinutes}m atrás`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h atrás`
    return `${Math.floor(diffInMinutes / 1440)}d atrás`
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <div className={`absolute -top-1 -right-1 w-5 h-5 text-white text-xs rounded-full flex items-center justify-center ${urgentCount > 0 ? 'bg-status-error animate-pulse motion-reduce:animate-none' : 'bg-status-error'}`}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </div>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 top-12 w-96 bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl z-50 max-h-96 overflow-hidden">
          <div className="p-4 dark:border-lia-border-subtle">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-lia-text-primary">
                🧠 Inteligência Competitiva
              </h3>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchNotifications}
                  disabled={isLoading}
                  className="h-6 w-6 p-0"
                  title="Atualizar notificações"
                >
                  <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} />
                </Button>
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-xs"
                  >
                    Marcar todas como lidas
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  className="h-6 w-6 p-0"
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            </div>
            {urgentCount > 0 && (
              <div className="mt-2 text-xs text-status-error dark:text-status-error flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                {urgentCount} notificação(ões) urgente(s)
              </div>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
            {isLoading && notifications.length === 0 ? (
              <div className="p-6 text-center" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-8 h-8 text-lia-text-secondary mx-auto mb-2 animate-spin motion-reduce:animate-none" />
                <p className="text-sm text-lia-text-primary">Carregando notificações...</p>
              </div>
            ) : error ? (
              <div className="p-6 text-center">
                <AlertTriangle className="w-8 h-8 text-status-error mx-auto mb-2" />
                <p className="text-sm text-status-error mb-2">{error}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchNotifications}
                  className="text-xs"
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Tentar novamente
                </Button>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-6 text-center">
                <Bell className="w-8 h-8 text-lia-text-secondary mx-auto mb-2" />
                <p className="text-sm text-lia-text-primary">Nenhuma notificação</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 transition-colors motion-reduce:transition-none ${
 !notification.read ? 'bg-wedo-cyan/10 dark:bg-wedo-cyan/15' : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-full ${getPriorityColor(notification.priority)}`}>
                      {getTypeIcon(notification.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-lia-text-primary">
                          {notification.title}
                        </span>
                        <Chip variant="neutral" muted className={`text-xs ${getPriorityColor(notification.priority)}`}>
                          {notification.priority}
                        </Chip>
                      </div>

                      <p className="text-sm text-lia-text-secondary mb-2">
                        {notification.message}
                      </p>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-lia-text-primary">
                          {formatTimestamp(notification.timestamp)}
                        </span>

                        <div className="flex gap-1">
                          {notification.actions.slice(0, 3).map((action) => (
                            <Button
                              key={action}
                              variant="outline"
                              size="sm"
                              className="h-6 text-xs"
                              onClick={() => handleAction(notification.id, action)}
                            >
                              {action === 'approach' && <Target className="w-3 h-3 mr-1" />}
                              {action === 'track' && <Eye className="w-3 h-3 mr-1" />}
                              {action === 'dismiss' && <X className="w-3 h-3 mr-1" />}
                              {action === 'review_salaries' && <TrendingUp className="w-3 h-3 mr-1" />}
                              {action === 'map_candidates' && <Building className="w-3 h-3 mr-1" />}
                              {action === 'counter_strategy' && <Zap className="w-3 h-3 mr-1" />}
                              {action === 'view' && <Eye className="w-3 h-3 mr-1" />}

                              {action === 'approach' && 'Abordar'}
                              {action === 'track' && 'Monitorar'}
                              {action === 'dismiss' && 'Dispensar'}
                              {action === 'review_salaries' && 'Revisar'}
                              {action === 'map_candidates' && 'Mapear'}
                              {action === 'counter_strategy' && 'Estratégia'}
                              {action === 'view' && 'Ver'}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-3 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <div className="flex items-center justify-between">
              {lastFetch && (
                <span className="text-xs text-lia-text-secondary">
                  Atualizado: {formatTimestamp(lastFetch)}
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="text-xs ml-auto"
                onClick={() => {
                  setIsOpen(false)
                }}
              >
                <Settings className="w-3 h-3 mr-1" />
                Ver Dashboard Completo
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
