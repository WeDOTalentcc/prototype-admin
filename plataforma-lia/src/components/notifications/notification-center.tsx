'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { 
  Bell, X, Check, CheckCheck, Trash2, Settings, Clock, 
  TrendingDown, MessageCircle, Brain, Zap, AlertTriangle,
  Filter, ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'

async function fetchNotificationsApi(endpoint: string, options?: RequestInit) {
  const response = await fetch(`/api/backend-proxy${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  if (!response.ok) {
    return { success: false, data: { notifications: [] } }
  }
  const data = await response.json()
  return data
}

interface Notification {
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

interface NotificationCenterProps {
  userId?: string
  onNavigate?: (page: string) => void
}

const categoryIcons: Record<string, React.ElementType> = {
  pipeline: TrendingDown,
  productivity: Clock,
  communication: MessageCircle,
  predictive: Brain,
  system: Settings,
  default: Bell
}

const typeColors: Record<string, { bg: string; text: string; border: string }> = {
  info: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400', border: 'border-gray-300 dark:border-gray-600' },
  success: { bg: 'bg-emerald-50 dark:bg-emerald-950/30', text: 'text-emerald-600', border: 'border-emerald-200' },
  warning: { bg: 'bg-amber-50 dark:bg-amber-950/30', text: 'text-amber-600', border: 'border-amber-200' },
  urgent: { bg: 'bg-red-50 dark:bg-red-950/30', text: 'text-red-600', border: 'border-red-200' },
  action_required: { bg: 'bg-purple-50 dark:bg-purple-950/30', text: 'text-purple-600', border: 'border-purple-200' }
}

export function NotificationCenter({ userId = 'default_user', onNavigate }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
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
        setUnreadCount(response.data.notifications.filter((n: Notification) => !n.is_read).length)
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
    } catch (error) {
      console.error('Error fetching notification summary:', error)
    }
  }, [userId])

  useEffect(() => {
    isMounted.current = true
    fetchSummary()
    const interval = setInterval(fetchSummary, 60000)
    return () => {
      isMounted.current = false
      clearInterval(interval)
    }
  }, [fetchSummary])

  useEffect(() => {
    if (isOpen) {
      fetchNotifications()
    }
  }, [isOpen, fetchNotifications])

  const markAsRead = async (notificationId: string) => {
    try {
      await fetchNotificationsApi(`/notifications/${notificationId}/read?user_id=${userId}`, {
        method: 'POST'
      })
      
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error marking notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      await fetchNotificationsApi(`/notifications/read-all?user_id=${userId}`, {
        method: 'POST'
      })
      
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (error) {
      console.error('Error marking all as read:', error)
    }
  }

  const dismissNotification = async (notificationId: string) => {
    try {
      await fetchNotificationsApi(`/notifications/${notificationId}/dismiss?user_id=${userId}`, {
        method: 'POST'
      })
      
      setNotifications(prev => prev.filter(n => n.id !== notificationId))
    } catch (error) {
      console.error('Error dismissing notification:', error)
    }
  }

  const handleAction = (notification: Notification) => {
    if (notification.action_url) {
      if (notification.action_url.startsWith('/chat')) {
        onNavigate?.('Chat com LIA')
      } else {
        window.location.href = notification.action_url
      }
    }
    markAsRead(notification.id)
    setIsOpen(false)
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Agora'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}min`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
  }

  const filteredNotifications = filter 
    ? notifications.filter(n => n.category === filter)
    : notifications

  const categories = [...new Set(notifications.map(n => n.category).filter(Boolean))]

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="relative h-8 w-8 p-0"
          aria-label="Notificações"
        >
          <Bell className="h-4 w-4 text-gray-800 dark:text-gray-500" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[11px] font-medium text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      
      <PopoverContent 
        className="w-96 p-0 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800"
        align="end"
        sideOffset={8}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4" style={{ color: 'var(--wedo-blue)' }} />
            <h3 className="font-sans font-semibold text-sm text-gray-950 dark:text-gray-50">Notificações</h3>
            {unreadCount > 0 && (
              <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                {unreadCount} novas
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 px-2">
                  <Filter className="w-3.5 h-3.5" />
                  <ChevronDown className="w-3 h-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuLabel className="text-xs">Filtrar por</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setFilter(null)}>
                  Todas
                </DropdownMenuItem>
                {categories.map(cat => (
                  <DropdownMenuItem key={cat} onClick={() => setFilter(cat || null)}>
                    {cat === 'pipeline' && 'Pipeline'}
                    {cat === 'productivity' && 'Produtividade'}
                    {cat === 'communication' && 'Comunicação'}
                    {cat === 'predictive' && 'IA Preditiva'}
                    {cat === 'system' && 'Sistema'}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            
            {unreadCount > 0 && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 px-2 text-xs"
                onClick={markAllAsRead}
              >
                <CheckCheck className="w-3.5 h-3.5 mr-1" />
                Ler todas
              </Button>
            )}
          </div>
        </div>

        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-gray-400 dark:border-t-gray-500" />
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <Bell className="w-10 h-10 text-gray-800 mb-3" />
              <p className="text-sm text-gray-800">Nenhuma notificação</p>
              <p className="text-xs text-gray-800 mt-1">
                Você está em dia com tudo!
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredNotifications.map(notification => {
                const colors = typeColors[notification.type] || typeColors.info
                const CategoryIcon = categoryIcons[notification.category || 'default']
                
                return (
                  <div
                    key={notification.id}
                    className={cn(
                      "px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer",
                      !notification.is_read && "bg-gray-100 dark:bg-gray-800"
                    )}
                    onClick={() => handleAction(notification)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                        colors.bg
                      )}>
                        <CategoryIcon className={cn("w-4 h-4", colors.text)} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h4 className={cn(
                            "text-sm font-medium truncate",
                            notification.is_read 
                              ? "text-gray-800 dark:text-gray-500" 
                              : "text-gray-950 dark:text-gray-50"
                          )}>
                            {notification.title}
                          </h4>
                          {!notification.is_read && (
                            <span className="w-2 h-2 rounded-full bg-gray-700 dark:bg-gray-300 flex-shrink-0" />
                          )}
                        </div>
                        
                        <p className="text-xs text-gray-800 dark:text-gray-500 line-clamp-2">
                          {notification.message}
                        </p>
                        
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-xs text-gray-800">
                            {formatTime(notification.created_at)}
                          </span>
                          
                          {notification.action_label && (
                            <span className="text-xs font-medium" style={{ color: 'var(--wedo-blue)' }}>
                              {notification.action_label} →
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        {!notification.is_read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              markAsRead(notification.id)
                            }}
                          >
                            <Check className="w-3 h-3 text-gray-800" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            dismissNotification(notification.id)
                          }}
                        >
                          <X className="w-3 h-3 text-gray-800" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </ScrollArea>

        <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-800">
          <Button 
            variant="ghost" 
            size="sm" 
            className="w-full h-8 text-xs"
            onClick={() => {
              onNavigate?.('Configurações')
              setIsOpen(false)
            }}
          >
            <Settings className="w-3.5 h-3.5 mr-1.5" />
            Configurar Notificações
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
