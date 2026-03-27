'use client'

import React from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useNotifications, type Notification } from './notification-context'
import { cn } from '@/lib/utils'

interface ToastProps {
  notification: Notification
}

const typeConfig = {
  success: {
    icon: CheckCircle,
    bgColor: 'bg-status-success/10',
    borderColor: 'border-status-success/30 dark:border-status-success/30',
    iconColor: 'text-status-success dark:text-status-success',
    titleColor: 'text-status-success dark:text-status-success'
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-status-error/10',
    borderColor: 'border-status-error/30 dark:border-status-error/30',
    iconColor: 'text-status-error dark:text-status-error',
    titleColor: 'text-status-error dark:text-status-error'
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-status-warning/10',
    borderColor: 'border-status-warning/30 dark:border-status-warning/30',
    iconColor: 'text-status-warning dark:text-status-warning',
    titleColor: 'text-status-warning dark:text-status-warning'
  },
  info: {
    icon: Info,
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    borderColor: 'border-gray-300 dark:border-gray-600',
    iconColor: 'text-gray-600 dark:text-gray-400',
    titleColor: 'text-gray-700 dark:text-gray-300'
  }
}

export function Toast({ notification }: ToastProps) {
  const { removeNotification } = useNotifications()
  const config = typeConfig[notification.type]
  const Icon = config.icon

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const durationSeconds = notification.duration ? notification.duration / 1000 : 0

  return (
    <div
      className={cn(
        "relative w-full max-w-sm p-4 rounded-md border backdrop-blur-sm",
        config.bgColor,
        config.borderColor
      )}
      style={{ animation: 'slideInFromRight 0.3s ease-out' }}
    >
      {/* Indicador de tempo real */}
      {notification.realTime && (
        <div
          className="absolute -top-1 -right-1 w-3 h-3 bg-status-success rounded-full"
          style={{ animation: 'scaleInDelayed 0.2s ease-out' }}
        >
          <div
            className="w-full h-full bg-status-success rounded-full"
            style={{ animation: 'realtimePulse 2s infinite' }}
          />
        </div>
      )}

      <div className="flex items-start gap-3">
        <div style={{ animation: 'scaleRotateIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s backwards' }}>
          <Icon className={cn("w-5 h-5 flex-shrink-0", config.iconColor)} />
        </div>

        <div className="flex-1 min-w-0">
          <div style={{ animation: 'fadeInUp 0.3s ease-out 0.2s backwards' }}>
            <h4 className={cn("text-sm font-semibold", config.titleColor)}>
              {notification.title}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              {notification.message}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              {formatTime(notification.timestamp)}
            </p>
          </div>

          {/* Actions */}
          {notification.actions && notification.actions.length > 0 && (
            <div
              className="flex gap-2 mt-3"
              style={{ animation: 'fadeInDown 0.3s ease-out 0.3s backwards' }}
            >
              {notification.actions.map((action, index) => (
                <Button
                  key={index}
                  variant={action.variant === 'primary' ? 'default' : 'outline'}
                  size="sm"
                  onClick={action.action}
                  className="h-7 text-xs"
                >
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>

        <div style={{ animation: 'scaleInDelayed 0.2s ease-out 0.4s backwards' }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => removeNotification(notification.id)}
            className="h-6 w-6 p-0 hover:bg-black/5 dark:hover:bg-white/5"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Progress bar para duração */}
      {notification.duration && notification.duration > 0 && (
        <div
          className="absolute bottom-0 left-0 h-1 bg-current opacity-20 rounded-b-lg"
          style={{
            animation: `progressShrink ${durationSeconds}s linear forwards`
          }}
        />
      )}
    </div>
  )
}
