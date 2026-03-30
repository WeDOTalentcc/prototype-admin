"use client"

import React, { useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { 
  X, 
  ArrowRight, 
  Send, 
  Mail, 
  MessageSquare, 
  XCircle,
  CheckSquare,
  Users,
  MoreHorizontal,
  FileText
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

export type BulkActionType = 
  | 'move_stage' 
  | 'request_data' 
  | 'send_message' 
  | 'reject' 
  | 'export'
  | 'add_to_list'
  | 'share_search'
  | 'favorites'

export interface BulkAction {
  id: BulkActionType
  label: string
  icon: React.ReactNode
  variant?: 'default' | 'destructive'
  disabled?: boolean
}

const DEFAULT_ACTIONS: BulkAction[] = [
  { id: 'move_stage', label: 'Mover Etapa', icon: <ArrowRight className="w-4 h-4" /> },
  { id: 'request_data', label: 'Solicitar Dados', icon: <FileText className="w-4 h-4" /> },
  { id: 'send_message', label: 'Mensagem', icon: <Mail className="w-4 h-4" /> },
  { id: 'reject', label: 'Reprovar', icon: <XCircle className="w-4 h-4" />, variant: 'destructive' },
]

export interface BulkSelectionBarProps {
  selectedCount: number
  totalCount: number
  isAllSelected?: boolean
  actions?: BulkAction[]
  onSelectAll: () => void
  onClearSelection: () => void
  onAction: (actionId: BulkActionType) => void
  className?: string
  showSecondaryActions?: boolean
}

export function BulkSelectionBar({
  selectedCount,
  totalCount,
  isAllSelected = false,
  actions = DEFAULT_ACTIONS,
  onSelectAll,
  onClearSelection,
  onAction,
  className,
  showSecondaryActions = true,
}: BulkSelectionBarProps) {
  if (selectedCount === 0) {
    return null
  }
  
  const primaryActions = actions.slice(0, 3)
  const secondaryActions = actions.slice(3)
  
  const handleAction = useCallback((actionId: BulkActionType) => {
    onAction(actionId)
  }, [onAction])

  return (
    <div 
      className={cn(
 "fixed top-0 left-0 right-0 z-50",
        "bg-gray-900 border-b border-gray-800",
        "",
        "animate-in slide-in-from-top duration-200",
        className
      )}
    >
      <div className="max-w-screen-2xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={onSelectAll}
                className="border-gray-600 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
              />
              <span className="text-sm lia-text-muted">
                Selecionar todos
              </span>
            </div>
            
            <div className="h-4 w-px bg-gray-700" />
            
            <div className="flex items-center gap-2">
              <Badge 
                className="bg-gray-200 text-lia-text-secondary border-lia-border-default hover:bg-gray-300 dark:bg-lia-bg-elevated dark:text-lia-text-secondary dark:border-lia-border-default"
              >
                <Users className="w-3 h-3 mr-1" />
                {selectedCount}
              </Badge>
              <span className="text-sm lia-text-secondary">
                {selectedCount === 1 ? 'candidato selecionado' : 'candidatos selecionados'}
                {totalCount > 0 && ` de ${totalCount}`}
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {primaryActions.map((action) => (
              <Button
                key={action.id}
                variant={action.variant === 'destructive' ? 'destructive' : 'outline'}
                size="sm"
                onClick={() => handleAction(action.id)}
                disabled={action.disabled}
                className={cn(
 action.variant !== 'destructive' && "border-gray-700 lia-text-muted hover:bg-gray-800 hover:text-white"
                )}
              >
                {action.icon}
                <span className="ml-1.5 hidden sm:inline">{action.label}</span>
              </Button>
            ))}
            
            {showSecondaryActions && secondaryActions.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-gray-700 lia-text-muted hover:bg-gray-800 hover:text-white"
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="min-w-[180px]">
                  {secondaryActions.map((action, index) => (
                    <React.Fragment key={action.id}>
                      {action.variant === 'destructive' && index > 0 && (
                        <DropdownMenuSeparator />
                      )}
                      <DropdownMenuItem
                        onClick={() => handleAction(action.id)}
                        disabled={action.disabled}
                        className={cn(
 action.variant === 'destructive' && "text-status-error focus:text-status-error"
                        )}
                      >
                        {action.icon}
                        <span className="ml-2">{action.label}</span>
                      </DropdownMenuItem>
                    </React.Fragment>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            
            <div className="h-4 w-px bg-gray-700 mx-1" />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              className="lia-text-secondary hover:lia-text-muted hover:bg-gray-800"
            >
              <X className="w-4 h-4" />
              <span className="ml-1.5 hidden sm:inline">Limpar</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function BulkSelectionBarInline({
  selectedCount,
  totalCount,
  isAllSelected = false,
  actions = DEFAULT_ACTIONS,
  onSelectAll,
  onClearSelection,
  onAction,
  className,
}: BulkSelectionBarProps) {
  if (selectedCount === 0) {
    return null
  }
  
  return (
    <div 
      className={cn(
 "bg-gray-100 dark:bg-lia-bg-secondary/50 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md",
        "px-4 py-2.5",
        "animate-in fade-in duration-200",
        className
      )}
    >
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={isAllSelected}
              onCheckedChange={onSelectAll}
              className="data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
              Todos
            </span>
          </div>
          
          <Badge 
            className="bg-gray-200 text-lia-text-secondary border-lia-border-default dark:bg-lia-bg-elevated dark:text-lia-text-secondary dark:border-lia-border-default"
          >
            {selectedCount} selecionado{selectedCount !== 1 && 's'}
          </Badge>
        </div>
        
        <div className="flex items-center gap-1.5">
          {actions.slice(0, 4).map((action) => (
            <Button
              key={action.id}
              variant={action.variant === 'destructive' ? 'destructive' : 'ghost'}
              size="sm"
              onClick={() => onAction(action.id)}
              disabled={action.disabled}
              className={cn(
 "h-7 text-xs",
                action.variant !== 'destructive' && "text-lia-text-secondary dark:text-lia-text-secondary"
              )}
            >
              {action.icon}
              <span className="ml-1 hidden md:inline">{action.label}</span>
            </Button>
          ))}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearSelection}
            className="h-7 text-xs lia-text-secondary hover:lia-text-base"
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
