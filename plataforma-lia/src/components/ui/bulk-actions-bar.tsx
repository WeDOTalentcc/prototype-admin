"use client"

import React from "react"
import { X, Loader2, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"

interface BulkActionItem {
  id: string
  label: string
  icon: React.ReactNode
  onClick: () => void
  variant?: 'default' | 'destructive'
  disabled?: boolean
  loading?: boolean
  loadingLabel?: string
  hidden?: boolean
}

interface BulkActionsBarProps {
  selectedCount: number
  totalCount?: number
  entityLabel?: string
  entityIcon?: React.ReactNode
  showSelectAll?: boolean
  isAllSelected?: boolean
  onSelectAll?: () => void
  onDeselectAll: () => void
  actions: BulkActionItem[]
  className?: string
}

const BUTTON_CLASS = "h-8 px-3 text-xs gap-2 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
const DESTRUCTIVE_BUTTON_CLASS = "h-8 px-3 text-xs gap-2 border-status-error/30 text-status-error hover:bg-status-error/10 dark:text-status-error dark:bg-lia-bg-elevated dark:hover:bg-status-error/20"

export const BulkActionsBar = React.memo(function BulkActionsBar({
  selectedCount,
  totalCount,
  entityLabel,
  entityIcon,
  showSelectAll = false,
  isAllSelected = false,
  onSelectAll,
  onDeselectAll,
  actions,
  className,
}: BulkActionsBarProps) {
  if (selectedCount === 0) return null

  const label = entityLabel || 'candidato'
  const plural = selectedCount > 1
  const displayLabel = label === 'candidato'
    ? `${selectedCount} candidato${plural ? 's' : ''} selecionado${plural ? 's' : ''}`
    : label === 'vaga'
      ? `${selectedCount} vaga${plural ? 's' : ''} selecionada${plural ? 's' : ''}`
      : `${selectedCount} ${label}${plural ? 's' : ''}`

  const visibleActions = actions.filter(a => !a.hidden)

  return (
    <div
      className={cn(
        "p-3 rounded-md bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle",
        className
      )}
    >
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {showSelectAll && onSelectAll && (
            <div className="flex items-center gap-2">
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={onSelectAll}
                className="data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900 dark:data-[state=checked]:bg-gray-100 dark:data-[state=checked]:border-lia-border-subtle"
              />
              <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                Selecionar todos
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
              {entityIcon || <Users className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />}
            </div>
            <span className="text-sm font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {displayLabel}
            </span>
            {totalCount !== undefined && totalCount > 0 && (
              <span className="text-xs text-lia-text-tertiary">
                de {totalCount}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {visibleActions.map((action) => {
            const isDestructive = action.variant === 'destructive'

            return (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                onClick={action.onClick}
                disabled={action.disabled || action.loading}
                className={isDestructive ? DESTRUCTIVE_BUTTON_CLASS : BUTTON_CLASS}
                title={action.label}
              >
                {action.loading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                ) : (
                  action.icon
                )}
                <span>{action.loading && action.loadingLabel ? action.loadingLabel : action.label}</span>
              </Button>
            )
          })}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-8 px-2 text-xs text-lia-text-primary hover:text-lia-text-primary dark:text-lia-text-primary dark:hover:text-lia-text-inverse"
          title="Limpar seleção"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
})

BulkActionsBar.displayName = 'BulkActionsBar'

export type { BulkActionItem, BulkActionsBarProps }
