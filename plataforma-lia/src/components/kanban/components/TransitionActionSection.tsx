"use client"

import NextImage from "next/image"
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectTrigger, SelectValue } from '@/components/ui/select'
import { renderSubStatusOptions } from './rejection-categories'
import { useRejectionCategoryLabels } from './use-rejection-category-labels'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Button } from '@/components/ui/button'
import {
  Brain,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { KanbanCandidate } from '../types'
import { ACTION_BEHAVIOR_MODALS } from '../constants'
import type React from 'react'

interface BehaviorConfig {
  label: string
  icon: React.ReactNode
  description: string
}

interface BatchRejectionSectionProps {
  candidates: KanbanCandidate[]
  isRejectedBatch: boolean
  currentSubStatusOptions: Array<{ code: string; display_name: string; category?: string }>
  isBulkPredicting: boolean
  predictedSubStatuses: Record<string, string>
  predictionReasonings: Record<string, string>
  perCandidateSubStatus: Record<string, string>
  manuallyEditedCandidates: Set<string>
  subStatus: string
  showAllPerCandidate: boolean
  setShowAllPerCandidate: (fn: (prev: boolean) => boolean) => void
  handlePerCandidateSubStatusChange: (candidateId: string, value: string) => void
}

export function BatchRejectionSection({
  candidates,
  isRejectedBatch,
  currentSubStatusOptions,
  isBulkPredicting,
  predictedSubStatuses,
  predictionReasonings,
  perCandidateSubStatus,
  manuallyEditedCandidates,
  subStatus,
  showAllPerCandidate,
  setShowAllPerCandidate,
  handlePerCandidateSubStatusChange,
}: BatchRejectionSectionProps) {
  const rejectionCategoryLabels = useRejectionCategoryLabels()
  if (!isRejectedBatch || currentSubStatusOptions.length === 0) return null

  return (
    <div data-testid="transition-action-section" className="space-y-2">
      <button
        type="button"
        className="w-full flex items-center justify-between py-1.5 group"
        onClick={() => setShowAllPerCandidate(prev => !prev)}
      >
        <span className="font-sans text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
          Motivo por candidato
          {isBulkPredicting && (
            <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-wedo-cyan" />
          )}
          {!isBulkPredicting && Object.keys(predictedSubStatuses).length > 0 && (
            <span className="inline-flex items-center gap-0.5 text-micro font-normal text-lia-text-muted">
              <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
              IA
            </span>
          )}
        </span>
        <span className="flex items-center gap-1 text-micro text-lia-text-secondary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-muted transition-colors motion-reduce:transition-none">
          {candidates.length} candidatos
          {showAllPerCandidate ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
        </span>
      </button>
      {showAllPerCandidate && (
        <div className="max-h-[240px] overflow-y-auto space-y-1.5 pr-0.5">
          {candidates.map((c) => {
            const candidateSubStatus = perCandidateSubStatus[c.id] || subStatus
            const isAiPredicted = !manuallyEditedCandidates.has(c.id) && !!predictedSubStatuses[c.id]
            const reasoning = predictionReasonings[c.id]
            const initials = c.name
              ?.split(' ')
              .slice(0, 2)
              .map(n => n[0])
              .join('')
              .toUpperCase() || '?'

            return (
              <div
                key={c.id}
                className="p-2.5 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-lia-interactive-active dark:bg-lia-bg-elevated flex items-center justify-center flex-shrink-0">
                    {c.avatar ? (
                      <NextImage src={c.avatar} alt="" width={28} height={28} className="w-7 h-7 rounded-full object-cover" />
                    ) : (
                      <span className="text-micro font-semibold text-lia-text-secondary">{initials}</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-sans text-xs font-medium text-lia-text-primary truncate">
                      {c.name}
                    </p>
                    {(c.role || c.currentCompany) && (
                      <p className="font-sans text-xs text-lia-text-secondary truncate">
                        {c.role}{c.role && c.currentCompany ? ' @ ' : ''}{c.currentCompany}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {isAiPredicted && (
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                    )}
                    <Select
                      value={candidateSubStatus}
                      onValueChange={(value) => handlePerCandidateSubStatusChange(c.id, value)}
                    >
                      <SelectTrigger className="w-[180px] h-7 rounded-md text-xs">
                        <SelectValue placeholder="Selecione..." />
                      </SelectTrigger>
                      <SelectContent>
                        {renderSubStatusOptions(currentSubStatusOptions, 'text-xs', rejectionCategoryLabels)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                {reasoning && (
                  <p className="font-sans text-xs text-lia-text-secondary mt-1.5 ml-[38px] flex items-center gap-1">
                    <Brain className="w-2.5 h-2.5 text-wedo-cyan flex-shrink-0" />
                    {reasoning}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface ActionModeSectionProps {
  action: 'lia_auto' | 'manual' | 'just_move'
  setAction: (action: 'lia_auto' | 'manual' | 'just_move') => void
  behaviorConfig: BehaviorConfig | undefined
  currentActionBehavior: string
  onOpenSpecializedModal?: (modalType: string, context: Record<string, unknown>) => void
  handleOpenManualModal: () => void
}

export function ActionModeSection({
  action,
  setAction,
  behaviorConfig,
  currentActionBehavior,
  onOpenSpecializedModal,
  handleOpenManualModal,
}: ActionModeSectionProps) {
  if (behaviorConfig) {
    return (
      <div className="space-y-1">
        <Label className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider">
          Ação
        </Label>
        <RadioGroup
          value={action}
          onValueChange={(v) => setAction(v as 'lia_auto' | 'manual' | 'just_move')}
          className="space-y-1"
        >
          <div
            className={cn(
              "flex items-start gap-2 p-2 rounded-lg border cursor-pointer transition-colors",
              action === 'lia_auto'
                ? "border-lia-btn-primary-bg bg-lia-bg-primary dark:border-lia-border-medium dark:bg-lia-bg-secondary"
                : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-lia-border-medium"
            )}
            onClick={() => setAction('lia_auto')}
          >
            <RadioGroupItem value="lia_auto" id="action-lia" className="mt-0.5" />
            <div className="flex-1 min-w-0">
              <label htmlFor="action-lia" className="flex items-center gap-1 cursor-pointer">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                <span className="text-xs font-medium text-lia-text-primary">LIA automático</span>
                <span className="text-micro bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary px-1 py-px rounded-full ml-auto">
                  Recomendado
                </span>
              </label>
              <p className="text-micro text-lia-text-secondary mt-0.5 leading-tight">
                {behaviorConfig.description}
              </p>
            </div>
          </div>

          <div
            className={cn(
              "flex items-start gap-2 p-2 rounded-lg border cursor-pointer transition-colors",
              action === 'manual'
                ? "border-lia-btn-primary-bg bg-lia-bg-primary dark:border-lia-border-medium dark:bg-lia-bg-secondary"
                : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-lia-border-medium"
            )}
            onClick={() => setAction('manual')}
          >
            <RadioGroupItem value="manual" id="action-manual" className="mt-0.5" />
            <div className="flex-1">
              <label htmlFor="action-manual" className="flex items-center gap-1 cursor-pointer">
                <span className="text-xs font-medium text-lia-text-primary">Manual</span>
              </label>
              {action === 'manual' && onOpenSpecializedModal && ACTION_BEHAVIOR_MODALS[currentActionBehavior] && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-1.5 h-6 text-micro gap-1 rounded-lg"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleOpenManualModal()
                  }}
                >
                  {behaviorConfig.icon}
                  {behaviorConfig.label}
                </Button>
              )}
            </div>
          </div>

          <div
            className={cn(
              "flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors",
              action === 'just_move'
                ? "border-lia-btn-primary-bg bg-lia-bg-primary dark:border-lia-border-medium dark:bg-lia-bg-secondary"
                : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-lia-border-medium"
            )}
            onClick={() => setAction('just_move')}
          >
            <RadioGroupItem value="just_move" id="action-move" />
            <label htmlFor="action-move" className="text-xs font-medium text-lia-text-primary cursor-pointer">
              Apenas mover
            </label>
          </div>
        </RadioGroup>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <Label className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider">
        Ação
      </Label>
      <RadioGroup
        value={action}
        onValueChange={(v) => setAction(v as 'lia_auto' | 'manual' | 'just_move')}
        className="space-y-1"
      >
        <div
          className={cn(
            "flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors",
            action === 'lia_auto'
              ? "border-lia-btn-primary-bg bg-lia-bg-primary dark:border-lia-border-medium dark:bg-lia-bg-secondary"
              : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-lia-border-medium"
          )}
          onClick={() => setAction('lia_auto')}
        >
          <RadioGroupItem value="lia_auto" id="action-lia-generic" />
          <label htmlFor="action-lia-generic" className="flex items-center gap-1 cursor-pointer">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-primary">LIA automático</span>
          </label>
        </div>
        <div
          className={cn(
            "flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors",
            action === 'just_move'
              ? "border-lia-btn-primary-bg bg-lia-bg-primary dark:border-lia-border-medium dark:bg-lia-bg-secondary"
              : "border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-subtle dark:hover:border-lia-border-medium"
          )}
          onClick={() => setAction('just_move')}
        >
          <RadioGroupItem value="just_move" id="action-move-generic" />
          <label htmlFor="action-move-generic" className="text-xs font-medium text-lia-text-primary cursor-pointer">
            Apenas mover
          </label>
        </div>
      </RadioGroup>
    </div>
  )
}
