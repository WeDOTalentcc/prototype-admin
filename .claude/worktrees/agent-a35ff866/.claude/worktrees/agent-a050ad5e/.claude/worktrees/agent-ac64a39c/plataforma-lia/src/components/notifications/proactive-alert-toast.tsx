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
  data?: Record<string, any>
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
    color: 'text-gray-600 dark:text-gray-400'
  },
  productivity: {
    icon: Clock,
    label: 'Produtividade',
    color: 'text-purple-600 dark:text-purple-400'
  },
  communication: {
    icon: MessageCircle,
    label: 'Comunicação',
    color: 'text-teal-600 dark:text-teal-400'
  },
  predictive: {
    icon: Brain,
    label: 'IA Preditiva',
    color: 'text-amber-600 dark:text-amber-400'
  },
  system: {
    icon: Settings,
    label: 'Sistema',
    color: 'text-gray-600 dark:text-gray-400'
  }
}

const severityConfig = {
  info: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    border: 'border-gray-300 dark:border-gray-600',
    icon: 'text-gray-600 dark:text-gray-400',
    progressBg: 'bg-gray-700 dark:bg-gray-300'
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    icon: 'text-amber-600',
    progressBg: 'bg-amber-500'
  },
  urgent: {
    bg: 'bg-red-50 dark:bg-red-950/30',
    border: 'border-red-200 dark:border-red-800',
    icon: 'text-red-600',
    progressBg: 'bg-red-500'
  },
  success: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    border: 'border-emerald-200 dark:border-emerald-800',
    icon: 'text-emerald-600',
    progressBg: 'bg-emerald-500'
  },
  action_required: {
    bg: 'bg-purple-50 dark:bg-purple-950/30',
    border: 'border-purple-200 dark:border-purple-800',
    icon: 'text-purple-600',
    progressBg: 'bg-purple-500'
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
        "relative w-full max-w-md p-4 rounded-md border-2 backdrop-blur-md",
        severity.bg,
        severity.border,
        "transform transition-all duration-300 ease-out"
      )}
      style={{ animation: 'slideInFromRight 0.4s ease-out' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {autoDismiss && duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 rounded-b-xl overflow-hidden">
          <div 
            className={cn("h-full transition-all duration-100", severity.progressBg)}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      
      {alert.severity === 'urgent' && (
        <div className="absolute -top-1 -left-1">
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}

      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", 
            alert.severity === 'success' ? 'bg-emerald-100 dark:bg-emerald-900/50' :
            alert.severity === 'urgent' ? 'bg-red-100 dark:bg-red-900/50' :
            'bg-gray-100 dark:bg-gray-800')}>
            <LIAIcon size="sm" className="w-6 h-6" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <CategoryIcon className={cn("w-3.5 h-3.5", category.color)} />
            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
              {category.label}
            </span>
            <span className="text-xs text-gray-600">
              {formatTime(alert.timestamp)}
            </span>
          </div>
          
          <h4 className="font-sans text-sm font-semibold text-gray-950 dark:text-gray-50 mb-1">
            {alert.title}
          </h4>
          
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
            {alert.message}
          </p>

          <div className="flex items-center gap-2 mt-3">
            <Button
              variant="default"
              size="sm"
              onClick={() => onNavigateToChat(alert)}
              className="h-8 px-3 text-xs gap-1.5"
              style={{ backgroundColor: 'var(--wedo-blue)' }}
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
          className="h-6 w-6 p-0 hover:bg-black/5 dark:hover:bg-white/5 flex-shrink-0"
        >
          <X className="w-4 h-4 text-gray-600" />
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
    <div className="fixed bottom-4 right-4 z-[100] space-y-3 max-w-md w-full pointer-events-none">
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
          <span className="text-xs text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 px-2 py-1 rounded-full border">
            +{alerts.length - 3} alertas adicionais
          </span>
        </div>
      )}
    </div>
  )
}
