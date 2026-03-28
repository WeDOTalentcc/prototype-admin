"use client"

import React from 'react'
import { Calendar, Zap, Mail, Users, MessageCircle, BarChart3, LucideIcon } from 'lucide-react'
import { Button } from './button'

export interface QuickAction {
  id: string
  label: string
  icon: LucideIcon
  onClick: () => void
  variant?: 'default' | 'primary' | 'success' | 'warning'
}

interface QuickActionChipsProps {
  actions: QuickAction[]
  className?: string
}

export function QuickActionChips({ actions, className = '' }: QuickActionChipsProps) {
  const getVariantStyles = (variant: QuickAction['variant'] = 'default') => {
    switch (variant) {
      case 'primary':
 return 'text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:bg-gray-100'
      case 'success':
        return 'bg-status-success/10 text-status-success border-status-success/30 hover:bg-status-success/20'
      case 'warning':
        return 'bg-status-warning/10 text-status-warning border-status-warning/30 hover:bg-status-warning/20'
      default:
        return 'hover:bg-gray-100 dark:hover:bg-gray-800'
    }
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {actions.map((action) => {
        const Icon = action.icon
        return (
          <Button
            key={action.id}
            variant="outline"
            size="sm"
            onClick={action.onClick}
            className={`inline-flex items-center gap-2 px-3 py-1.5 h-auto rounded-md text-sm font-medium transition-all duration-200 ${getVariantStyles(action.variant)}`}
            style={{
              borderColor: 'rgb(209 213 219)'
            }}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{action.label}</span>
          </Button>
        )
      })}
    </div>
  )
}

export const defaultCandidateActions: Omit<QuickAction, 'onClick'>[] = [
  {
    id: 'schedule',
    label: 'Agendar Entrevista',
    icon: Calendar,
    variant: 'primary'
  },
  {
    id: 'evaluate',
    label: 'Avaliar Fit Técnico',
    icon: Zap,
    variant: 'default'
  },
  {
    id: 'email',
    label: 'Gerar Email',
    icon: Mail,
    variant: 'default'
  },
  {
    id: 'whatsapp',
    label: 'Enviar WhatsApp',
    icon: MessageCircle,
    variant: 'default'
  },
  {
    id: 'compare',
    label: 'Comparar Perfis',
    icon: Users,
    variant: 'default'
  },
  {
    id: 'analytics',
    label: 'Ver Analytics',
    icon: BarChart3,
    variant: 'default'
  }
]
