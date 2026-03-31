"use client"
import React from "react"

import { 
  Users, Briefcase, List, Mail, X, Star, 
  ArrowRight, FileText, XCircle,
  Fingerprint, Share2
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"

export type BulkActionContext = 'funnel' | 'vacancy'

export type BulkActionId = 
  | 'add_to_vacancy'
  | 'add_to_list'
  | 'share_search'
  | 'send_message'
  | 'wsi_screening'
  | 'favorites'
  | 'move_stage'
  | 'request_data'
  | 'reject'

interface BulkAction {
  id: BulkActionId
  label: string
  shortLabel?: string
  icon: React.ReactNode
  contexts: BulkActionContext[]
  variant?: 'default' | 'destructive'
}

const BULK_ACTIONS: BulkAction[] = [
  {
    id: 'add_to_vacancy',
    label: 'Adicionar à Vaga',
    shortLabel: 'Vaga',
    icon: <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['funnel'],
  },
  {
    id: 'move_stage',
    label: 'Mover Etapa',
    icon: <ArrowRight className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['vacancy'],
  },
  {
    id: 'add_to_list',
    label: 'Adicionar à Lista',
    shortLabel: 'Lista',
    icon: <List className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['funnel', 'vacancy'],
  },
  {
    id: 'share_search',
    label: 'Compartilhar',
    shortLabel: 'Compartilhar',
    icon: <Share2 className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['funnel', 'vacancy'],
  },
  {
    id: 'wsi_screening',
    label: 'Triagem WSI',
    icon: <Fingerprint className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['funnel', 'vacancy'],
  },
  {
    id: 'request_data',
    label: 'Solicitar Dados',
    icon: <FileText className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['vacancy'],
  },
  {
    id: 'send_message',
    label: 'Mensagem',
    icon: <Mail className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />,
    contexts: ['funnel', 'vacancy'],
  },
  {
    id: 'favorites',
    label: 'Favoritos',
    icon: <Star className="w-3.5 h-3.5 text-status-warning" />,
    contexts: ['funnel', 'vacancy'],
  },
  {
    id: 'reject',
    label: 'Reprovar',
    icon: <XCircle className="w-3.5 h-3.5" />,
    contexts: ['vacancy'],
    variant: 'destructive',
  },
]

interface UnifiedBulkActionsBarProps {
  context: BulkActionContext
  selectedCount: number
  totalCount?: number
  showSelectAll?: boolean
  isAllSelected?: boolean
  onSelectAll?: () => void
  onDeselectAll: () => void
  onAction: (actionId: BulkActionId) => void
  disabledActions?: BulkActionId[]
  loadingActions?: BulkActionId[]
}

export const UnifiedBulkActionsBar = React.memo(function UnifiedBulkActionsBar({
  context,
  selectedCount,
  totalCount,
  showSelectAll = false,
  isAllSelected = false,
  onSelectAll,
  onDeselectAll,
  onAction,
  disabledActions = [],
  loadingActions = [],
}: UnifiedBulkActionsBarProps) {
  if (selectedCount === 0) return null

  const availableActions = BULK_ACTIONS.filter(action => action.contexts.includes(context))

  return (
    <div className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="flex items-center justify-between flex-wrap gap-2">
        {/* Left: Selection info */}
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
              <Users className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <span className="text-sm font-semibold text-lia-text-primary">
              {selectedCount} candidato{selectedCount > 1 ? 's' : ''} selecionado{selectedCount > 1 ? 's' : ''}
            </span>
            {totalCount !== undefined && totalCount > 0 && (
              <span className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">
                de {totalCount}
              </span>
            )}
          </div>
        </div>

        {/* Center: Action buttons */}
        <div className="flex flex-wrap gap-1.5">
          {availableActions.map((action) => {
            const isDisabled = disabledActions.includes(action.id)
            const isLoading = loadingActions.includes(action.id)
            const isDestructive = action.variant === 'destructive'

            return (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                onClick={() => onAction(action.id)}
                disabled={isDisabled || isLoading}
                className={`h-7 px-2.5 text-xs gap-1 bg-white hover:bg-gray-50 dark:bg-lia-bg-elevated dark:hover:bg-gray-600 ${
 isDestructive 
                    ? 'border-status-error/30 text-status-error hover:bg-status-error/10 dark:text-status-error dark:hover:bg-status-error/20' 
                    : 'border-lia-border-subtle text-lia-text-secondary dark:text-lia-text-primary'
                }`}
                title={action.label}
              >
                {action.icon}
                <span>{action.shortLabel || action.label}</span>
              </Button>
            )
          })}
        </div>

        {/* Right: Clear button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-7 px-2 text-xs text-lia-text-secondary hover:text-lia-text-primary dark:text-lia-text-tertiary dark:hover:text-lia-text-inverse"
          title="Limpar seleção"
        >
          <X className="w-3.5 h-3.5" />
          <span className="ml-1">Limpar</span>
        </Button>
      </div>
    </div>
  )
})
UnifiedBulkActionsBar.displayName = 'UnifiedBulkActionsBar'

export { BULK_ACTIONS }
export type { BulkAction }
