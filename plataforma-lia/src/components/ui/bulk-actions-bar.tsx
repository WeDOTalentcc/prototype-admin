"use client"

import React from"react"
import { X, Loader2, Users } from"lucide-react"
import { Button } from"@/components/ui/button"
import { Checkbox } from"@/components/ui/checkbox"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"

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
  layout?: 'inline' | 'fixed'
  className?: string
}

const INLINE_BUTTON ="h-8 px-3 text-xs gap-2 bg-lia-bg-primary hover:bg-lia-interactive-hover border-lia-border-subtle text-lia-text-primary dark:bg-lia-bg-elevated"
const INLINE_DESTRUCTIVE ="h-8 px-3 text-xs gap-2 border-status-error/30 text-status-error hover:bg-status-error/10 dark:text-status-error dark:bg-lia-bg-elevated dark:hover:bg-status-error/20"
const FIXED_BUTTON ="h-8 px-3 text-xs gap-2 border-lia-border-strong text-lia-text-muted hover:bg-lia-btn-primary-hover hover:text-white"
const FIXED_DESTRUCTIVE ="h-8 px-3 text-xs gap-2 bg-status-error text-white hover:bg-status-error/90"

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
  layout = 'inline',
  className,
}: BulkActionsBarProps) {
  if (selectedCount === 0) return null

  const isFixed = layout === 'fixed'
  const label = entityLabel || 'candidato'
  const plural = selectedCount > 1
  const displayLabel = label === 'candidato'
    ? `${selectedCount} candidato${plural ? 's' : ''} selecionado${plural ? 's' : ''}`
    : label === 'vaga'
      ? `${selectedCount} vaga${plural ? 's' : ''} selecionada${plural ? 's' : ''}`
      : `${selectedCount} ${label}${plural ? 's' : ''}`

  const visibleActions = actions.filter(a => !a.hidden)

  const containerClass = isFixed
    ?"fixed top-0 left-0 right-0 z-50 bg-lia-btn-primary-bg animate-in slide-in-from-top duration-200"
    :"p-3 rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle"

  return (
    <div className={cn(containerClass, className)}>
      <div className={cn("flex items-center justify-between flex-wrap",
        isFixed ?"max-w-screen-2xl mx-auto px-4 py-3 gap-4" :"gap-3"
      )}>
        <div className="flex items-center gap-3">
          {showSelectAll && onSelectAll && (
            <div className="flex items-center gap-2">
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={onSelectAll}
                className={cn(
                  isFixed
                    ?"border-lia-border-medium data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                    :"data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-tertiary dark:data-[state=checked]:border-lia-border-subtle"
                )}
              />
              <span className={cn("text-xs",
                isFixed ?"text-lia-text-tertiary" :"text-lia-text-secondary"
              )}>
                Selecionar todos
              </span>
            </div>
          )}

          {isFixed && showSelectAll && <div className="h-4 w-px bg-lia-bg-inverse" />}

          <div className="flex items-center gap-2">
            {isFixed ? (
              <Chip variant="neutral" muted className="bg-lia-interactive-active text-lia-text-secondary border-lia-border-default hover:bg-lia-border-default dark:bg-lia-bg-elevated dark:border-lia-border-default">
                {entityIcon || <Users className="w-3 h-3 mr-1" />}
                {selectedCount}
              </Chip>
            ) : (
              <div className="w-6 h-6 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
                {entityIcon || <Users className="w-3.5 h-3.5 text-lia-text-secondary" />}
              </div>
            )}
            <span className={cn("text-sm",
              isFixed ?"text-lia-text-tertiary" :"font-semibold text-lia-text-primary"
            )} aria-live="polite" aria-atomic="true">
              {displayLabel}
            </span>
            {totalCount !== undefined && totalCount > 0 && (
              <span className={cn("text-xs", isFixed ?"text-lia-text-secondary" :"text-lia-text-tertiary")}>
                de {totalCount}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex flex-wrap gap-2">
            {visibleActions.map((action) => {
              const isDestructive = action.variant === 'destructive'
              const btnClass = isFixed
                ? (isDestructive ? FIXED_DESTRUCTIVE : FIXED_BUTTON)
                : (isDestructive ? INLINE_DESTRUCTIVE : INLINE_BUTTON)

              return (
                <Button
                  key={action.id}
                  variant="outline"
                  size="sm"
                  onClick={action.onClick}
                  disabled={action.disabled || action.loading}
                  className={btnClass}
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

          {isFixed && <div className="h-4 w-px bg-lia-bg-inverse mx-1" />}

          <Button
            variant="ghost"
            size="sm"
            onClick={onDeselectAll}
            className={cn("h-8 px-2 text-xs",
              isFixed
                ?"text-lia-text-tertiary hover:text-lia-text-muted hover:bg-lia-btn-primary-hover"
                :"text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
            )}
            title="Limpar seleção"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  )
})

BulkActionsBar.displayName = 'BulkActionsBar'

export type BulkActionType =
  | 'move_stage'
  | 'request_data'
  | 'send_message'
  | 'reject'
  | 'export'
  | 'add_to_list'
  | 'add_to_vacancy'
  | 'share_search'
  | 'favorites'
  | 'wsi_screening'
  | 'hide'
  | 'save_to_base'
  | 'publish'
  | 'insights'
  | 'duplicate'
  | 'toggle_status'
  | 'assign_recruiter'
  | 'add_tags'
  | 'remove_tags'

export type { BulkActionItem, BulkActionsBarProps }
