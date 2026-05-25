"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { ClipboardList, Check, AlertTriangle, XCircle, Clock, RefreshCw, ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"

export type DataRequestStatus = 'pending' | 'complete' | 'partial' | 'expired' | 'cancelled'

export interface RequestedField {
  id: string
  name: string
  displayName: string
  status: 'completed' | 'pending' | 'missing'
}

export interface DataRequestIndicatorProps {
  candidateId: string
  status: DataRequestStatus
  fieldsRequested: RequestedField[]
  fieldsCompleted: RequestedField[]
  expiresAt?: Date | string | null
  onResend?: (candidateId: string) => void
  onViewDetails?: (candidateId: string) => void
  className?: string
  size?: 'sm' | 'md'
}

const STATUS_CONFIG: Record<DataRequestStatus, {
  icon: React.ReactNode
  label: string
  color?: string
  bgColor: string
}> = {
  pending: {
    icon: <ClipboardList className="w-3 h-3" />,
    label: 'Aguardando',
    bgColor: 'var(--wedo-cyan-bg-15)',
  },
  complete: {
    icon: <Check className="w-3 h-3" />,
    label: 'Completo',
    color: 'var(--status-success)',
    bgColor: 'var(--status-success-bg-15)',
  },
  partial: {
    icon: <AlertTriangle className="w-3 h-3" />,
    label: 'Parcial',
    color: 'var(--wedo-orange)',
    bgColor: 'var(--wedo-orange-bg-15)',
  },
  expired: {
    icon: <Clock className="w-3 h-3" />,
    label: 'Expirado',
    color: 'var(--status-error)',
    bgColor: 'var(--status-error-bg-15)',
  },
  cancelled: {
    icon: <XCircle className="w-3 h-3" />,
    label: 'Cancelado',
    bgColor: 'var(--lia-bg-tertiary)',
  },
}

function formatDate(date: Date | string | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function isExpired(date: Date | string | null | undefined): boolean {
  if (!date) return false
  const d = typeof date === 'string' ? new Date(date) : date
  return d < new Date()
}

export const DataRequestIndicator = React.memo(function DataRequestIndicator({
  candidateId,
  status,
  fieldsRequested,
  fieldsCompleted,
  expiresAt,
  onResend,
  onViewDetails,
  className,
  size = 'sm',
}: DataRequestIndicatorProps) {
  const config = STATUS_CONFIG[status]
  const totalFields = fieldsRequested.length
  const completedCount = fieldsCompleted.length
  const percentage = totalFields > 0 ? Math.round((completedCount / totalFields) * 100) : 0

  const allFields = fieldsRequested.map(field => {
    const isCompleted = fieldsCompleted.some(f => f.id === field.id)
    return {
      ...field,
      status: isCompleted ? 'completed' : 'pending' as const,
    }
  })

  const expired = status !== 'complete' && status !== 'cancelled' && isExpired(expiresAt)
  const effectiveStatus = expired && status === 'pending' ? 'expired' : status
  const effectiveConfig = STATUS_CONFIG[effectiveStatus]

  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'
  const containerSize = size === 'sm' ? 'w-5 h-5' : 'w-6 h-6'

  return (
    <TooltipProvider>
      <Tooltip delayDuration={200}>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={cn(
 "inline-flex items-center justify-center rounded-full transition-colors",
              containerSize,
              className
            )}
            style={{backgroundColor: effectiveConfig.bgColor,
              color: effectiveConfig.color}}
            onClick={(e) => {
              e.stopPropagation()
              onViewDetails?.(candidateId)
            }}
          >
            <span className={iconSize}>{effectiveConfig.icon}</span>
          </button>
        </TooltipTrigger>
        <TooltipContent 
          side="top" 
          className="w-64 p-0 bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle"
        >
          <div className="p-3 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className="w-5 h-5 rounded-full flex items-center justify-center"
                  style={{backgroundColor: effectiveConfig.bgColor,
                    color: effectiveConfig.color}}
                >
                  {effectiveConfig.icon}
                </span>
                <span className="text-xs font-medium text-lia-text-primary">
                  {effectiveConfig.label}
                </span>
              </div>
              <span 
                className="text-micro font-semibold px-2 py-0.5 rounded-full"
                style={{backgroundColor: effectiveConfig.bgColor,
                  color: effectiveConfig.color}}
              >
                {percentage}%
              </span>
            </div>

            <div className="space-y-1.5">
              <p className="text-micro font-medium text-lia-text-tertiary uppercase tracking-wide">
                Campos Solicitados
              </p>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {allFields.map((field) => (
                  <div key={field.id} className="flex items-center gap-2 text-xs">
                    {field.status === 'completed' ? (
                      <Check className="w-3 h-3 text-wedo-green flex-shrink-0" />
                    ) : (
                      <Clock className="w-3 h-3 text-wedo-orange flex-shrink-0" />
                    )}
                    <span className={cn(
 "truncate",
                      field.status === 'completed' 
                        ? "text-lia-text-secondary" 
                        : "text-lia-text-tertiary"
                    )}>
                      {field.displayName}
                    </span>
                  </div>
                ))}
                {allFields.length === 0 && (
                  <span className="text-xs text-lia-text-secondary">Nenhum campo solicitado</span>
                )}
              </div>
            </div>

            {expiresAt && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-lia-text-tertiary">Expira em:</span>
                <span className={cn(
 "font-medium",
                  expired ? "text-status-error" : "text-lia-text-secondary"
                )}>
                  {formatDate(expiresAt)}
                  {expired && " (expirado)"}
                </span>
              </div>
            )}

            <div className="flex gap-2 pt-1">
              {effectiveStatus !== 'complete' && effectiveStatus !== 'cancelled' && (
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 h-7 text-xs gap-1 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation()
                    onResend?.(candidateId)
                  }}
                >
                  <RefreshCw className="w-3 h-3" />
                  Reenviar
                </Button>
              )}
              <Button
                size="sm"
                variant="secondary"
                className="flex-1 h-7 text-xs gap-1 bg-wedo-cyan/15 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation()
                  onViewDetails?.(candidateId)
                }}
              >
                <ExternalLink className="w-3 h-3" />
                Ver Detalhes
              </Button>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
})
DataRequestIndicator.displayName = 'DataRequestIndicator'

export function getDataRequestStatusFromFields(
  fieldsRequested: RequestedField[],
  fieldsCompleted: RequestedField[],
  expiresAt?: Date | string | null,
  isCancelled?: boolean
): DataRequestStatus {
  if (isCancelled) return 'cancelled'
  if (fieldsRequested.length === 0) return 'pending'
  
  const completedCount = fieldsCompleted.length
  const totalFields = fieldsRequested.length
  
  if (completedCount === totalFields) return 'complete'
  
  if (expiresAt) {
    const expDate = typeof expiresAt === 'string' ? new Date(expiresAt) : expiresAt
    if (expDate < new Date()) return 'expired'
  }
  
  if (completedCount > 0) return 'partial'
  
  return 'pending'
}
