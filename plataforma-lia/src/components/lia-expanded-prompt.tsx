"use client"

import React from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Brain, X, Send, Lightbulb } from "lucide-react"
import { LIAIcon } from "@/components/ui/lia-icon"

interface LiaExpandedPromptProps {
  title: string
  description?: string
  category?: 'vagas' | 'candidatos' | 'entrevistas' | 'relatorios' | 'localizacao' | 'industria'
  suggestions?: Array<{
    icon: React.ReactNode
    label: string
    description: string
    action: string
  }>
  onCommand?: (command: string) => void
  onClose?: () => void
  isExpanded?: boolean
  children?: React.ReactNode
}

// Cores padronizadas por categoria
const CATEGORY_COLORS: Record<string, {
  borderColor: string
  backgroundColor: string
  iconBg: string
  textColor: string
  badgeVariant: 'default' | 'secondary' | 'outline'
}> = {
  vagas: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'default'
  },
  candidatos: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'secondary'
  },
  entrevistas: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'default'
  },
  relatorios: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'secondary'
  },
  localizacao: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'secondary'
  },
  industria: {
    borderColor: 'var(--lia-border-subtle)',
    backgroundColor: 'var(--lia-bg-secondary)',
    iconBg: 'var(--lia-bg-tertiary)',
    textColor: 'var(--lia-text-primary)',
    badgeVariant: 'default'
  }
}

const DEFAULT_COLORS = CATEGORY_COLORS.candidatos

export function LiaExpandedPrompt({
  title,
  description,
  category = 'candidatos',
  suggestions = [],
  onCommand,
  onClose,
  isExpanded = true,
  children
}: LiaExpandedPromptProps) {
  const colors = CATEGORY_COLORS[category] || DEFAULT_COLORS

  if (!isExpanded) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onCommand?.('expand')}
        style={{borderColor: colors.borderColor,
          color: colors.textColor}}
        className="w-full justify-start gap-2"
      >
        <Brain className="w-4 h-4 text-wedo-cyan" />
        <span className="text-xs font-medium">{title}</span>
      </Button>
    )
  }

  return (
    <Card
      style={{borderColor: colors.borderColor,
        backgroundColor: colors.backgroundColor}}
      className="border"
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1">
            <div
              style={{backgroundColor: colors.iconBg}}
              className="p-2 rounded-md"
            >
              <LIAIcon className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div className="flex-1">
              <h3
                className="text-sm font-semibold"
                style={{color: colors.textColor}}
              >
                {title}
              </h3>
              {description && (
                <p className="text-xs text-lia-text-secondary mt-1">{description}</p>
              )}
            </div>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-6 w-6 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Sugestões rápidas */}
        {suggestions.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-secondary">
              💡 Sugestões Rápidas
            </label>
            <div className="grid grid-cols-1 gap-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={suggestion.action || index}
                  onClick={() => onCommand?.(suggestion.action)}
                  className="flex items-start gap-2 p-2 rounded-xl hover:opacity-90 transition-opacity motion-reduce:transition-none text-left border border-lia-border-subtle"
                  style={{backgroundColor: 'white',
                    borderColor: colors.borderColor + '40',
                    color: colors.textColor}}
                >
                  <span className="flex-shrink-0 mt-0.5">{suggestion.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium">{suggestion.label}</div>
                    <div className="text-xs text-lia-text-secondary mt-0.5">
                      {suggestion.description}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Conteúdo customizado */}
        {children && <div className="text-sm">{children}</div>}

        {/* Footer com dica */}
        <div
          className="text-xs p-2 rounded-md text-lia-text-secondary"
          style={{backgroundColor: colors.iconBg}}
        >
          <div className="flex items-start gap-2">
            <Lightbulb className="w-3 h-3 mt-0.5 flex-shrink-0" />
            <span>A IA aprende com seus padrões para sugerir ações mais precisas</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
