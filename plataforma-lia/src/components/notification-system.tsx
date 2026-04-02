"use client"

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { createPortal } from "react-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X, Bell, CheckCircle, AlertCircle, Info, Clock, Loader2 } from "lucide-react"
import {
  useNotifications,
  CATEGORY_LABELS,
  type Notification,
  type NotificationCategory,
} from "@/hooks/use-notifications"

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
      default: return <Info className="w-4 h-4 text-lia-text-secondary" />
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
      role="button"
      tabIndex={0}
      className={`group relative p-2.5 rounded-md cursor-pointer transition-colors motion-reduce:transition-none duration-200 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary ${
 !notification.read 
          ? "bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle" 
          : "bg-transparent border border-transparent"
      }`}
      onClick={handleClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleClick(); } }}
    >
      <div className="flex items-start gap-2.5">
        <div className="flex-shrink-0 mt-0.5">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
 !notification.read 
              ? notification.type === 'success' ? 'bg-status-success/15 dark:bg-status-success/30' 
                : notification.type === 'warning' ? 'bg-status-warning/15 dark:bg-status-warning/30'
                : notification.type === 'error' ? 'bg-status-error/15 dark:bg-status-error/30'
                : 'bg-wedo-cyan/15'
              : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
          }`}>
            {getIcon}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={`text-xs font-medium leading-tight ${
 !notification.read ? "text-lia-text-primary" : "text-lia-text-secondary"
 }`}>
              {notification.title}
            </h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              className="h-5 w-5 p-0 text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none -mt-0.5 -mr-1"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
          <p className={`text-xs mt-0.5 leading-relaxed ${
 !notification.read ? "text-lia-text-secondary" : "text-lia-text-primary"
 }`}>
            {notification.message}
          </p>
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-xs text-lia-text-secondary flex items-center gap-1">
              <Clock className="w-2.5 h-2.5" />
              {timeAgo}
            </span>
            <div className="flex items-center gap-2">
              {notification.actionUrl && notification.actionLabel && (
                <a
                  href={notification.actionUrl}
                  className="text-xs font-medium text-wedo-cyan hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {notification.actionLabel}
                </a>
              )}
              {!notification.read && (
                <button
                  onClick={handleMarkAsRead}
                  className="text-xs font-medium hover:underline text-lia-text-secondary"
                >
                  Marcar lida
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
})

NotificationItem.displayName = 'NotificationItem'

interface NotificationSystemProps {
  onNotificationClick?: (notification: Notification) => void
  userId?: string
  pollingInterval?: number
}

const CATEGORY_ORDER: NotificationCategory[] = [
  "pipeline",
  "productivity",
  "communication",
  "predictive",
  "system",
]

export function NotificationSystem({ 
  onNotificationClick, 
  userId = "default_user",
  pollingInterval = 60000
}: NotificationSystemProps) {
  const {
    notifications,
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
  } = useNotifications({ userId, pollingInterval })

  const [isOpen, setIsOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)
  const [portalPosition, setPortalPosition] = useState({ top: 0, right: 0 })

  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setPortalPosition({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      })
    }
  }, [])

  const toggleOpen = useCallback(() => {
    updatePosition()
    setIsOpen(prev => {
      const newState = !prev
      if (newState) refreshIfStale()
      return newState
    })
  }, [refreshIfStale, updatePosition])

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!isOpen) return
    const timeoutId = setTimeout(() => {
      const handleClickOutside = (e: MouseEvent) => {
        if (
          panelRef.current && !panelRef.current.contains(e.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(e.target as Node)
        ) {
          setIsOpen(false)
        }
      }
      document.addEventListener('mousedown', handleClickOutside)
      cleanupRef.current = () => document.removeEventListener('mousedown', handleClickOutside)
    }, 100)
    return () => {
      clearTimeout(timeoutId)
      cleanupRef.current?.()
      cleanupRef.current = null
    }
  }, [isOpen])

  const panelContent = isOpen ? (
    <div
      ref={panelRef}
      className="fixed z-modal"
      style={{ top: portalPosition.top, right: portalPosition.right }}
    >
      <Card className="w-[340px] max-h-[480px] overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lg">
        <CardContent className="p-0">
          <div className="px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-lia-text-primary">
                Notificações
                {unreadCount > 0 && (
                  <span className="ml-2 text-xs font-medium px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">
                    {unreadCount} nova{unreadCount > 1 ? 's' : ''}
                  </span>
                )}
              </h3>
              <div className="flex items-center gap-1" role="status" aria-live="polite" aria-label="Carregando...">
                {isLoading && (
                  <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                )}
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-xs h-6 px-2 text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                  >
                    Marcar lidas
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleOpen}
                  className="h-6 w-6 p-0 text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary"
                  aria-label="Fechar notificações"
                >
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            <div className="flex gap-1 mt-2 overflow-x-auto" role="tablist" aria-label="Filtrar notificações por categoria">
              <button
                role="tab"
                aria-selected={activeCategory === null}
                onClick={() => setActiveCategory(null)}
                className={`px-2 py-1 text-xs rounded-lg whitespace-nowrap transition-colors ${
                  activeCategory === null
                    ? "bg-wedo-cyan/15 text-wedo-cyan font-medium"
                    : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
                }`}
              >
                Todas
              </button>
              {CATEGORY_ORDER.map(cat => (
                <button
                  key={cat}
                  role="tab"
                  aria-selected={activeCategory === cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-2 py-1 text-xs rounded-lg whitespace-nowrap transition-colors ${
                    activeCategory === cat
                      ? "bg-wedo-cyan/15 text-wedo-cyan font-medium"
                      : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
                  }`}
                >
                  {CATEGORY_LABELS[cat]}
                </button>
              ))}
            </div>
          </div>

          <div className="max-h-[340px] overflow-y-auto bg-lia-bg-secondary dark:bg-lia-bg-primary/50" aria-live="polite">
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
            ) : hasNotifications && notifications.length > 0 ? (
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
                <Bell className="w-8 h-8 mx-auto mb-2 text-lia-text-disabled" aria-hidden="true" />
                <p className="text-sm text-lia-text-primary">
                  {isLoading ? "Carregando..." : activeCategory ? `Nenhuma notificação em ${CATEGORY_LABELS[activeCategory]}` : "Nenhuma notificação"}
                </p>
                {!isLoading && !activeCategory && (
                  <p className="text-xs text-lia-text-secondary mt-1">Você está em dia com tudo!</p>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  ) : null

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={toggleOpen}
        className="inline-flex items-center justify-center h-7 w-7 p-0 relative rounded-lg border-0 bg-transparent text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary cursor-pointer transition-colors"
        aria-label={unreadCount > 0 ? `Notificações, ${unreadCount} não lidas` : 'Notificações'}
        aria-expanded={isOpen}
        aria-haspopup="true"
        data-testid="notification-bell"
      >
        <Bell className="w-3.5 h-3.5" aria-hidden="true" />
        {unreadCount > 0 && (
          <span
            role="status"
            aria-label={`${unreadCount} notificações não lidas`}
            className="absolute -top-0.5 -right-0.5 h-4 w-4 text-[10px] leading-none p-0 flex items-center justify-center rounded-full bg-status-error text-lia-bg-primary dark:text-lia-bg-primary font-medium"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {mounted && panelContent && createPortal(panelContent, document.body)}
    </div>
  )
}
