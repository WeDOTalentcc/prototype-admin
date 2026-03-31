'use client'

import React from 'react'
import { 
  Bell, X, Check, CheckCheck, Settings, Clock, 
  TrendingDown, MessageCircle, Brain, Zap,
  Filter, ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { useNotifications, type NotificationItem } from '@/hooks/use-notifications'

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
  info: { bg: 'bg-lia-bg-secondary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary dark:text-lia-text-tertiary', border: 'border-lia-border-default dark:border-lia-border-default' },
  success: { bg: 'bg-status-success/10', text: 'text-status-success', border: 'border-status-success/30' },
  warning: { bg: 'bg-status-warning/10', text: 'text-status-warning', border: 'border-status-warning/30' },
  urgent: { bg: 'bg-status-error/10', text: 'text-status-error', border: 'border-status-error/30' },
  action_required: { bg: 'bg-wedo-purple/10', text: 'text-wedo-purple', border: 'border-wedo-purple/30' }
}

const categoryLabels: Record<string, string> = {
  pipeline: 'Pipeline',
  productivity: 'Produtividade',
  communication: 'Comunicação',
  predictive: 'IA Preditiva',
  system: 'Sistema',
}

function formatTime(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return 'Agora'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}min`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

export function NotificationCenter({ userId = 'default_user', onNavigate }: NotificationCenterProps) {
  const {
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
  } = useNotifications({ userId })

  const handleAction = (notification: NotificationItem) => {
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

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="relative h-8 w-8 p-0"
          aria-label={unreadCount > 0 ? `Notificações, ${unreadCount} não lidas` : 'Notificações'}
        >
          <Bell className="h-4 w-4 text-lia-text-primary" aria-hidden="true" />
          {unreadCount > 0 && (
            <span
              role="status"
              aria-label={`${unreadCount} notificações não lidas`}
              className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-status-error text-xs font-medium text-lia-bg-primary dark:text-lia-bg-primary"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      
      <PopoverContent 
        className="w-96 p-0 bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
        align="end"
        sideOffset={8}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
            <h3 className="font-sans font-semibold text-sm text-lia-text-primary">Notificações</h3>
            {unreadCount > 0 && (
              <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                {unreadCount} novas
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 px-2" aria-label="Filtrar notificações">
                  <Filter className="w-3.5 h-3.5" aria-hidden="true" />
                  <ChevronDown className="w-3 h-3 ml-1" aria-hidden="true" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuLabel className="text-xs">Filtrar por</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setFilter(null)}>
                  Todas
                </DropdownMenuItem>
                {categories.map(cat => (
                  <DropdownMenuItem key={cat} onClick={() => setFilter(cat)}>
                    {categoryLabels[cat] || cat}
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
                aria-label="Marcar todas notificações como lidas"
              >
                <CheckCheck className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                Ler todas
              </Button>
            )}
          </div>
        </div>

        <ScrollArea className="h-[400px]">
          <div aria-live="polite" aria-atomic="false">
            {isLoading ? (
              <div className="flex items-center justify-center py-8" role="status" aria-label="Carregando notificações">
                <div className="animate-spin motion-reduce:animate-none rounded-full h-6 w-6 border-2 border-lia-border-default border-t-lia-text-tertiary dark:border-t-lia-text-tertiary" />
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <Bell className="w-10 h-10 text-lia-text-tertiary mb-3" aria-hidden="true" />
                <p className="text-sm text-lia-text-secondary">Nenhuma notificação</p>
                <p className="text-xs text-lia-text-tertiary mt-1">
                  Você está em dia com tudo!
                </p>
              </div>
            ) : (
              <div className="divide-y divide-lia-border-subtle">
                {filteredNotifications.map(notification => {
                  const colors = typeColors[notification.type] || typeColors.info
                  const CategoryIcon = categoryIcons[notification.category || 'default']
                  
                  return (
                    <div
                      key={notification.id}
                      role="article"
                      aria-label={`${notification.title}${!notification.is_read ? ', não lida' : ''}`}
                      className={cn(
                        "px-4 py-3 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none cursor-pointer",
                        !notification.is_read && "bg-lia-bg-secondary dark:bg-lia-bg-secondary"
                      )}
                      onClick={() => handleAction(notification)}
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn(
                          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                          colors.bg
                        )}>
                          <CategoryIcon className={cn("w-4 h-4", colors.text)} aria-hidden="true" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <h4 className={cn(
                              "text-sm font-medium truncate text-lia-text-primary",
                              !notification.is_read && "font-semibold"
                            )}>
                              {notification.title}
                            </h4>
                            {!notification.is_read && (
                              <span className="w-2 h-2 rounded-full bg-wedo-cyan flex-shrink-0" aria-hidden="true" />
                            )}
                          </div>
                          
                          <p className="text-xs text-lia-text-secondary line-clamp-2">
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="text-xs text-lia-text-tertiary">
                              {formatTime(notification.created_at)}
                            </span>
                            
                            {notification.action_label && (
                              <span className="text-xs font-medium text-wedo-cyan">
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
                              aria-label={`Marcar "${notification.title}" como lida`}
                              onClick={(e) => {
                                e.stopPropagation()
                                markAsRead(notification.id)
                              }}
                            >
                              <Check className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            aria-label={`Dispensar "${notification.title}"`}
                            onClick={(e) => {
                              e.stopPropagation()
                              dismissNotification(notification.id)
                            }}
                          >
                            <X className="w-3 h-3 text-lia-text-tertiary" aria-hidden="true" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="px-4 py-2 border-t border-lia-border-subtle">
          <Button 
            variant="ghost" 
            size="sm" 
            className="w-full h-8 text-xs"
            onClick={() => {
              onNavigate?.('Configurações')
              setIsOpen(false)
            }}
          >
            <Settings className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
            Configurar Notificações
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
