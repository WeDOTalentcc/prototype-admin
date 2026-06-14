"use client"

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { createPortal } from "react-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  X,
  Bell,
  CheckCircle,
  AlertCircle,
  Info,
  Clock,
  Loader2,
  GitBranch,
  Zap,
  MessageSquare,
  TrendingUp,
  Monitor,
  BellOff,
  Check,
  ExternalLink,
  Trash2,
} from "lucide-react"
import {
  useNotifications,
  CATEGORY_LABELS,
  type Notification,
  type NotificationCategory,
} from "@/hooks/shared/use-notifications"
import { cn } from "@/lib/utils"

const CATEGORY_ICONS: Record<NotificationCategory, React.ElementType> = {
  pipeline: GitBranch,
  productivity: Zap,
  communication: MessageSquare,
  predictive: TrendingUp,
  system: Monitor,
}

function getTemporalGroup(timestamp: Date): string {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))

  const isToday = timestamp.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = timestamp.toDateString() === yesterday.toDateString()

  if (minutes < 30) return "Agora"
  if (isToday) return "Hoje"
  if (isYesterday) return "Ontem"
  return "Esta Semana"
}

function formatTimeAgo(timestamp: Date): string {
  const now = Date.now()
  const diff = now - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days > 0) return `${days}d atrás`
  if (hours > 0) return `${hours}h atrás`
  if (minutes > 0) return `${minutes}m atrás`
  return "agora"
}

const NotificationItem = React.memo(({
  notification,
  onMarkAsRead,
  onRemove,
  onClick,
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
  }, [notification, onMarkAsRead, onClick])

  const getIcon = useMemo(() => {
    switch (notification.type) {
      case "success": return <CheckCircle className="w-4 h-4 text-status-success" />
      case "warning": return <AlertCircle className="w-4 h-4 text-status-warning" />
      case "error": return <AlertCircle className="w-4 h-4 text-status-error" />
      default: return <Info className="w-4 h-4 text-lia-text-secondary" />
    }
  }, [notification.type])

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "group relative p-3 rounded-lg cursor-pointer transition-all motion-reduce:transition-none duration-200",
        !notification.read
          ? "bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle shadow-sm"
          : "bg-transparent border border-transparent hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary"
      )}
      onClick={handleClick}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleClick() } }}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <div className={cn(
            "w-7 h-7 rounded-full flex items-center justify-center",
            !notification.read
              ? notification.type === "success" ? "bg-status-success/15 dark:bg-status-success/30"
                : notification.type === "warning" ? "bg-status-warning/15 dark:bg-status-warning/30"
                : notification.type === "error" ? "bg-status-error/15 dark:bg-status-error/30"
                : "bg-wedo-cyan/15"
              : "bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
          )}>
            {getIcon}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={cn(
              "text-xs font-medium leading-tight",
              !notification.read ? "text-lia-text-primary" : "text-lia-text-secondary"
            )}>
              {notification.title}
            </h4>
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none -mt-0.5 -mr-1 flex-shrink-0">
              {!notification.read && (
                <button
                  onClick={(e) => { e.stopPropagation(); handleMarkAsRead() }}
                  className="h-5 w-5 p-0 flex items-center justify-center rounded text-lia-text-secondary hover:text-status-success hover:bg-status-success/10 transition-colors"
                  title="Marcar como lida"
                >
                  <Check className="w-3 h-3" />
                </button>
              )}
              <button
                onClick={handleRemove}
                className="h-5 w-5 p-0 flex items-center justify-center rounded text-lia-text-secondary hover:text-status-error hover:bg-status-error/10 transition-colors"
                title="Remover"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
          <p className={cn(
            "text-xs mt-0.5 leading-relaxed line-clamp-2",
            !notification.read ? "text-lia-text-secondary" : "text-lia-text-tertiary"
          )}>
            {notification.message}
          </p>
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-[10px] text-lia-text-muted flex items-center gap-1">
              <Clock className="w-2.5 h-2.5" />
              {formatTimeAgo(notification.timestamp)}
            </span>
            {notification.actionUrl && notification.actionLabel && (
              <a
                href={notification.actionUrl}
                className="text-[10px] font-medium text-lia-text-secondary hover:underline flex items-center gap-0.5"
                onClick={(e) => e.stopPropagation()}
              >
                {notification.actionLabel}
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
})

NotificationItem.displayName = "NotificationItem"

interface NotificationSystemProps {
  onNotificationClick?: (notification: Notification) => void
  userId?: string
  pollingInterval?: number
  panelPosition?: "sidebar" | "topbar"
}

const CATEGORY_ORDER: NotificationCategory[] = [
  "pipeline",
  "productivity",
  "communication",
  "predictive",
  "system",
]

const TEMPORAL_ORDER = ["Agora", "Hoje", "Ontem", "Esta Semana"]

export function NotificationSystem({
  onNotificationClick,
  userId = "default_user",
  pollingInterval = 60000,
  panelPosition = "sidebar",
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
  const [hasNewNotification, setHasNewNotification] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)
  const [portalPosition, setPortalPosition] = useState({ top: 0, left: 0, right: 0, fromSidebar: false })
  const prevUnreadCountRef = useRef(unreadCount)

  useEffect(() => {
    if (prevUnreadCountRef.current !== null && unreadCount > prevUnreadCountRef.current) {
      setHasNewNotification(true)
      const newest = notifications.find(n => !n.read)
      if (newest) {
        toast(newest.title, {
          description: newest.message?.slice(0, 80),
          duration: 5000,
          icon: <Bell className="w-4 h-4 text-wedo-cyan-text" />,
          position: "bottom-right",
          className: "notification-toast",
        })
      }
      const timer = setTimeout(() => setHasNewNotification(false), 1500)
      return () => clearTimeout(timer)
    }
    prevUnreadCountRef.current = unreadCount
  }, [unreadCount, notifications])

  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const panelWidth = 420
      const panelHeight = 520
      const margin = 8

      if (panelPosition === "sidebar") {
        let top = rect.bottom - panelHeight
        if (top < margin) top = margin
        if (top + panelHeight > window.innerHeight - margin) {
          top = window.innerHeight - panelHeight - margin
        }
        top = Math.max(margin, top)

        let left = rect.right + margin
        if (left + panelWidth > window.innerWidth - margin) {
          left = rect.left - panelWidth - margin
        }
        left = Math.max(margin, left)

        setPortalPosition({ top, left, right: 0, fromSidebar: true })
      } else {
        setPortalPosition({
          top: rect.bottom + 4,
          left: 0,
          right: Math.max(margin, window.innerWidth - rect.right),
          fromSidebar: false,
        })
      }
    }
  }, [panelPosition])

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

    const handleResize = () => updatePosition()
    window.addEventListener("resize", handleResize)

    const timeoutId = setTimeout(() => {
      const handleClickOutside = (e: MouseEvent) => {
        if (
          panelRef.current && !panelRef.current.contains(e.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(e.target as Node)
        ) {
          setIsOpen(false)
        }
      }
      document.addEventListener("mousedown", handleClickOutside)
      cleanupRef.current = () => {
        document.removeEventListener("mousedown", handleClickOutside)
        window.removeEventListener("resize", handleResize)
      }
    }, 100)
    return () => {
      clearTimeout(timeoutId)
      window.removeEventListener("resize", handleResize)
      cleanupRef.current?.()
      cleanupRef.current = null
    }
  }, [isOpen, updatePosition])

  const groupedNotifications = useMemo(() => {
    const groups: Record<string, Notification[]> = {}
    for (const n of notifications) {
      const group = getTemporalGroup(n.timestamp)
      if (!groups[group]) groups[group] = []
      groups[group].push(n)
    }
    return TEMPORAL_ORDER
      .filter(g => groups[g]?.length)
      .map(g => ({ label: g, items: groups[g] }))
  }, [notifications])

  const panelContent = isOpen ? (
    <div
      ref={panelRef}
      className="fixed z-modal animate-in fade-in slide-in-from-bottom-2 duration-200"
      style={
        portalPosition.fromSidebar
          ? { top: portalPosition.top, left: portalPosition.left }
          : { top: portalPosition.top, right: portalPosition.right }
      }
    >
      <Card className="w-[420px] max-h-[520px] overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-xl">
        <CardContent className="p-0">
          <div className="px-4 py-3 bg-lia-bg-primary dark:bg-lia-bg-primary border-b border-lia-border-subtle">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-lia-text-primary" />
                <h3 className="text-sm font-semibold text-lia-text-primary">
                  Notificações
                </h3>
                {unreadCount > 0 && (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-status-error/15 text-status-error">
                    {unreadCount} nova{unreadCount > 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1" role="status" aria-live="polite" aria-label="Carregando...">
                {isLoading && (
                  <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                )}
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-[10px] h-6 px-2 text-wedo-cyan-text hover:text-wedo-cyan/80"
                  >
                    <Check className="w-3 h-3 mr-1" />
                    Marcar todas lidas
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleOpen}
                  className="h-6 w-6 p-0 text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary"
                  aria-label="Fechar notificações"
                  data-dismiss="true"
                >
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            <div className="flex gap-1 mt-2.5 overflow-x-auto pb-0.5" role="tablist" aria-label="Filtrar notificações por categoria">
              <button
                role="tab"
                aria-selected={activeCategory === null}
                onClick={() => setActiveCategory(null)}
                className={cn(
                  "px-2.5 py-1.5 text-[11px] rounded-lg whitespace-nowrap transition-colors flex items-center gap-1.5",
                  activeCategory === null
                    ? "bg-wedo-cyan/15 text-wedo-cyan-text font-medium"
                    : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
                )}
              >
                <Bell className="w-3 h-3" />
                Todas
              </button>
              {CATEGORY_ORDER.map(cat => {
                const CatIcon = CATEGORY_ICONS[cat]
                return (
                  <button
                    key={cat}
                    role="tab"
                    aria-selected={activeCategory === cat}
                    onClick={() => setActiveCategory(cat)}
                    className={cn(
                      "px-2.5 py-1.5 text-[11px] rounded-lg whitespace-nowrap transition-colors flex items-center gap-1.5",
                      activeCategory === cat
                        ? "bg-wedo-cyan/15 text-wedo-cyan-text font-medium"
                        : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
                    )}
                  >
                    <CatIcon className="w-3 h-3" />
                    {CATEGORY_LABELS[cat]}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="max-h-[380px] overflow-y-auto bg-lia-bg-secondary dark:bg-lia-bg-primary/50" aria-live="polite">
            {error ? (
              <div className="py-12 px-4 text-center">
                <AlertCircle className="w-8 h-8 mx-auto mb-3 text-status-error" />
                <p className="text-sm text-status-error font-medium">{error}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchNotifications}
                  className="mt-3 text-xs"
                >
                  Tentar novamente
                </Button>
              </div>
            ) : hasNotifications && groupedNotifications.length > 0 ? (
              <div className="p-2">
                {groupedNotifications.map((group) => (
                  <div key={group.label} className="mb-2 last:mb-0">
                    <div className="flex items-center gap-2 px-2 py-1.5">
                      <span className="text-[10px] font-semibold text-lia-text-tertiary tracking-wider uppercase">
                        {group.label}
                      </span>
                      <div className="flex-1 h-px bg-lia-border-subtle" />
                      <span className="text-[10px] text-lia-text-muted">
                        {group.items.length}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {group.items.map((notification) => (
                        <NotificationItem
                          key={notification.id}
                          notification={notification}
                          onMarkAsRead={markAsRead}
                          onRemove={removeNotification}
                          onClick={onNotificationClick}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-14 px-6 text-center">
                <div className="w-14 h-14 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-4">
                  <BellOff className="w-6 h-6 text-lia-text-muted" aria-hidden="true" />
                </div>
                <p className="text-sm font-medium text-lia-text-primary">
                  {isLoading ? "Carregando..." : activeCategory ? `Nenhuma em ${CATEGORY_LABELS[activeCategory]}` : "Tudo em dia!"}
                </p>
                {!isLoading && !activeCategory && (
                  <p className="text-xs text-lia-text-secondary mt-1.5">
                    Quando houver atualizações, elas aparecerão aqui.
                  </p>
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
        className={cn(
          "inline-flex items-center justify-center h-7 w-7 p-0 relative rounded-lg border-0 bg-transparent text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary cursor-pointer transition-colors",
          hasNewNotification && "animate-notification-shake"
        )}
        aria-label={unreadCount > 0 ? `Notificações, ${unreadCount} não lidas` : "Notificações"}
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
