// @ts-nocheck
'use client'

import React, { useEffect, useState } from 'react'
import { X, MessageCircle, TrendingDown, Clock, AlertTriangle, Brain, Zap, Users, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { LIAIcon } from '@/components/ui/lia-icon'

export interface ProactiveAlert {
  id: string
  condition: string
  category: 'pipeline' | 'productivity' | 'communication' | 'predictive' | 'system'
  title: string
  message: string
  severity: 'info' | 'warning' | 'urgent' | 'success' | 'action_required'
  suggestedAction?: string
  actionLabel?: string
  data?: Record<string, unknown>
  timestamp: Date
  autoDismiss?: boolean
  duration?: number
}

interface ProactiveAlertToastProps {
  alert: ProactiveAlert
  onDismiss: (id: string) => void
  onAction: (alert: ProactiveAlert) => void
  onNavigateToChat: (alert: ProactiveAlert) => void
}

const categoryConfig = {
  pipeline: {
    icon: TrendingDown,
    label: 'Pipeline',
    color: 'text-lia-text-secondary dark:text-lia-text-tertiary'
  },
  productivity: {
    icon: Clock,
    label: 'Produtividade',
    color: 'text-wedo-purple dark:text-wedo-purple'
  },
  communication: {
    icon: MessageCircle,
    label: 'Comunicação',
    color: 'text-wedo-cyan dark:text-wedo-cyan'
  },
  predictive: {
    icon: Brain,
    label: 'IA Preditiva',
    color: 'text-status-warning dark:text-status-warning'
  },
  system: {
    icon: Settings,
    label: 'Sistema',
    color: 'text-lia-text-secondary dark:text-lia-text-tertiary'
  }
}

const severityConfig = {
  info: {
    bg: 'bg-gray-100 dark:bg-lia-bg-secondary',
    border: 'border-lia-border-default dark:border-lia-border-default',
    icon: 'text-lia-text-secondary dark:text-lia-text-tertiary',
    progressBg: 'bg-gray-700'
  },
  warning: {
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/30 dark:border-status-warning/30',
    icon: 'text-status-warning',
    progressBg: 'bg-status-warning'
  },
  urgent: {
    bg: 'bg-status-error/10',
    border: 'border-status-error/30 dark:border-status-error/30',
    icon: 'text-status-error',
    progressBg: 'bg-status-error'
  },
  success: {
    bg: 'bg-status-success/10',
    border: 'border-status-success/30 dark:border-status-success/30',
    icon: 'text-status-success',
    progressBg: 'bg-status-success'
  },
  action_required: {
    bg: 'bg-wedo-purple/10',
    border: 'border-wedo-purple/30 dark:border-wedo-purple/30',
    icon: 'text-wedo-purple',
    progressBg: 'bg-wedo-purple'
  }
}

export function ProactiveAlertToast({ 
  alert, 
  onDismiss, 
  onAction, 
  onNavigateToChat 
}: ProactiveAlertToastProps) {
  const [progress, setProgress] = useState(100)
  const [isHovered, setIsHovered] = useState(false)
  
  const category = categoryConfig[alert.category]
  const severity = severityConfig[alert.severity]
  const CategoryIcon = category.icon
  const duration = alert.duration || (alert.severity === 'urgent' ? 0 : 10000)
  const autoDismiss = alert.autoDismiss !== false && alert.severity !== 'urgent'
  
  useEffect(() => {
    if (!autoDismiss || isHovered || duration === 0) return
    
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev <= 0) {
          onDismiss(alert.id)
          return 0
        }
        return prev - (100 / (duration / 100))
      })
    }, 100)
    
    return () => clearInterval(interval)
  }, [autoDismiss, isHovered, duration, alert.id, onDismiss])
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div
      className={cn(
 "relative w-full max-w-md p-4 rounded-md border backdrop-blur-md",
        severity.bg,
        severity.border,
        "transform transition-colors duration-300 ease-out"
      )}
      style={{animation: 'slideInFromRight 0.4s ease-out'}}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {autoDismiss && duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-lia-bg-elevated rounded-b-xl overflow-hidden">
          <div 
            className={cn("h-full transition-[width,height] duration-100", severity.progressBg)}
            style={{width: `${progress}%`}}
          />
        </div>
      )}
      
      {alert.severity === 'urgent' && (
        <div className="absolute -top-1 -left-1">
          <span className="flex h-3 w-3">
            <span className="animate-ping motion-reduce:animate-none absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error"></span>
          </span>
        </div>
      )}

      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", 
 alert.severity === 'success' ? 'bg-status-success/15' :
            alert.severity === 'urgent' ? 'bg-status-error/15 dark:bg-status-error/50' :
            'bg-gray-100 dark:bg-lia-bg-secondary')}>
            <LIAIcon size="sm" className="w-6 h-6" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <CategoryIcon className={cn("w-3.5 h-3.5", category.color)} />
            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">
              {category.label}
            </span>
            <span className="text-xs lia-text-base">
              {formatTime(alert.timestamp)}
            </span>
          </div>
          
          <h4 className="font-sans text-sm font-semibold text-lia-text-primary mb-1">
            {alert.title}
          </h4>
          
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-secondary leading-relaxed">
            {alert.message}
          </p>

          <div className="flex items-center gap-2 mt-3">
            <Button
              variant="default"
              size="sm"
              onClick={() => onNavigateToChat(alert)}
              className="h-8 px-3 text-xs gap-1.5"
              className="bg-[var(--wedo-blue)]"
            >
              <LIAIcon size="xs" className="w-3.5 h-3.5" />
              Reanalisar
            </Button>
            
            {alert.actionLabel && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onAction(alert)}
                className="h-8 px-3 text-xs gap-1.5"
              >
                <Zap className="w-3.5 h-3.5" />
                {alert.actionLabel}
              </Button>
            )}
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDismiss(alert.id)}
          className="h-6 w-6 p-0 hover:bg-black/5 dark:hover:bg-lia-bg-primary/5 flex-shrink-0"
        >
          <X className="w-4 h-4 lia-text-base" />
        </Button>
      </div>
    </div>
  )
}

interface ProactiveAlertContainerProps {
  alerts: ProactiveAlert[]
  onDismiss: (id: string) => void
  onAction: (alert: ProactiveAlert) => void
  onNavigateToChat: (alert: ProactiveAlert) => void
}

export function ProactiveAlertContainer({ 
  alerts, 
  onDismiss, 
  onAction, 
  onNavigateToChat 
}: ProactiveAlertContainerProps) {
  if (alerts.length === 0) return null
  
  return (
    <div className="fixed bottom-4 right-4 z-toast space-y-3 max-w-md w-full pointer-events-none">
      {alerts.slice(0, 3).map((alert) => (
        <div key={alert.id} className="pointer-events-auto">
          <ProactiveAlertToast
            alert={alert}
            onDismiss={onDismiss}
            onAction={onAction}
            onNavigateToChat={onNavigateToChat}
          />
        </div>
      ))}
      
      {alerts.length > 3 && (
        <div className="pointer-events-auto text-center">
          <span className="text-xs text-lia-text-primary dark:text-lia-text-primary bg-white dark:bg-lia-bg-secondary px-2 py-1 rounded-full border">
            +{alerts.length - 3} alertas adicionais
          </span>
        </div>
      )}
    </div>
  )
}
