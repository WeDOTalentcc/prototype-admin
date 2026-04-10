'use client'

import React, { useMemo, useCallback, memo } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { CandidateCard, type QuickActionType } from './CandidateCard'
import type { DynamicStage, KanbanCandidate } from '../types'
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

export interface ColumnStyle {
  bg: string
  border: string
  dot: string
  header: string
  accentColor: string
}

export interface KanbanColumnProps {
  stage: DynamicStage
  candidates: KanbanCandidate[]
  isDropTarget: boolean
  selectedCandidates: Set<string>
  favoriteCandidates?: Set<string>
  viewedCandidates?: Set<string>
  onSelectAll: (stageId: string, candidateIds: string[]) => void
  onCandidateClick: (candidate: KanbanCandidate) => void
  onCandidateSelect?: (candidateId: string) => void
  onCandidateQuickAction: (action: QuickActionType, candidate: KanbanCandidate, extra?: Record<string, unknown>) => void
  onSubStatusChange?: (candidateId: string, newSubStatus: string, stage: string) => void
  subStatusOptions?: Array<{ code: string; display_name: string }>
  onDragStart: (e: React.DragEvent, candidate: KanbanCandidate, fromColumn: string) => void
  onDragEnd: (e: React.DragEvent) => void
  onDragOver: (e: React.DragEvent, columnId: string) => void
  onDragLeave: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, toColumn: string) => void
  isDragging?: boolean
}

const getColumnStyle = (columnId: string, stageColor?: string): ColumnStyle => {
  const fixedStyles: Record<string, ColumnStyle> = {
    sourcing: {
      bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-lia-bg-inverse',
      header: 'text-lia-text-primary',
      accentColor: 'var(--lia-text-secondary)'
    },
    hired: {
      bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-lia-bg-inverse',
      header: 'text-lia-text-primary',
      accentColor: 'var(--lia-text-secondary)'
    },
    rejected: {
      bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-lia-border-default',
      header: 'text-lia-text-primary',
      accentColor: 'var(--lia-border-subtle)'
    },
    offer_declined: {
      bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-lia-border-default',
      header: 'text-lia-text-primary',
      accentColor: 'var(--lia-border-subtle)'
    }
  }

  if (fixedStyles[columnId]) {
    return fixedStyles[columnId]
  }

  return {
    bg: 'bg-lia-bg-primary dark:bg-lia-bg-primary',
    border: 'border-lia-border-subtle dark:border-lia-border-subtle',
    dot: 'bg-lia-bg-secondary0',
    header: 'text-lia-text-primary',
    accentColor: stageColor || 'var(--lia-text-tertiary)'
  }
}

const sortScreeningCandidates = (candidates: KanbanCandidate[]): KanbanCandidate[] => {
  return [...candidates].sort((a, b) => {
    if (a.needsAction && !b.needsAction) return -1
    if (!a.needsAction && b.needsAction) return 1
    return (b.score || 0) - (a.score || 0)
  })
}

const KanbanColumn = memo(function KanbanColumn({
  stage,
  candidates,
  isDropTarget,
  selectedCandidates,
  favoriteCandidates = new Set(),
  viewedCandidates = new Set(),
  onSelectAll,
  onCandidateClick,
  onCandidateSelect,
  onCandidateQuickAction,
  onSubStatusChange,
  subStatusOptions,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  onDrop,
  isDragging = false
}: KanbanColumnProps) {
  const columnStyle = getColumnStyle(stage.id, stage.color)
  
  const sortedCandidates = useMemo(() => {
    if (stage.id === 'screening') {
      return sortScreeningCandidates(candidates)
    }
    return candidates
  }, [candidates, stage.id])

  const candidateIds = useMemo(() => sortedCandidates.map(c => c.id), [sortedCandidates])
  
  const allSelected = useMemo(() => {
    if (sortedCandidates.length === 0) return false
    return sortedCandidates.every(c => selectedCandidates.has(c.id))
  }, [sortedCandidates, selectedCandidates])

  const handleSelectAllChange = useCallback((checked: boolean | 'indeterminate') => {
    if (checked === true) {
      onSelectAll(stage.id, candidateIds)
    } else {
      onSelectAll(stage.id, [])
    }
  }, [onSelectAll, stage.id, candidateIds])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    onDragOver(e, stage.id)
  }, [onDragOver, stage.id])

  const handleDrop = useCallback((e: React.DragEvent) => {
    onDrop(e, stage.id)
  }, [onDrop, stage.id])

  const handleCandidateDragStart = useCallback((e: React.DragEvent, candidate: KanbanCandidate) => {
    onDragStart(e, candidate, stage.id)
  }, [onDragStart, stage.id])

  return (
    <div
      data-testid={`kanban-column-${stage.id}`}
      className={`flex flex-col flex-1 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl min-w-[275px] max-w-[368px] border border-lia-border-subtle dark:border-lia-border-subtle transition-colors motion-reduce:transition-none duration-300 ${
        isDropTarget ? 'ring-2 ring-lia-border-medium bg-lia-bg-secondary dark:bg-lia-bg-secondary' : ''
      } h-[calc(100vh-16rem)]`}
      onDragOver={handleDragOver}
      onDragLeave={onDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex-shrink-0 p-2.5 pb-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div 
              className={`w-2 h-2 rounded-full ${columnStyle.dot} transition-transform motion-reduce:transition-none duration-300 ${
                isDropTarget ? 'scale-150' : ''
              }`}
            />
            <h3 className={`font-medium text-xs ${columnStyle.header}`}>
              {stage.displayName}
            </h3>
            <span className="text-micro text-lia-text-primary bg-lia-bg-tertiary dark:bg-lia-bg-secondary px-1.5 py-0.5 rounded-full">
              {sortedCandidates.length}
            </span>
          </div>
          {sortedCandidates.length > 0 && (
            <Checkbox
              data-testid={`kanban-column-select-all-${stage.id}`}
              checked={allSelected}
              onCheckedChange={handleSelectAllChange}
              className="w-3.5 h-3.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-interactive-active dark:data-[state=checked]:border-lia-border-subtle"
              title={`Selecionar todos da etapa ${stage.displayName}`}
            />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-1.5 pb-1 space-y-1">
        {sortedCandidates.map((candidate, index) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            stageId={stage.id}
            isSelected={selectedCandidates.has(candidate.id)}
            isFavorite={favoriteCandidates.has(candidate.id)}
            isViewed={viewedCandidates.has(candidate.id)}
            isDragging={isDragging}
            index={index}
            dropZoneActive={isDropTarget}
            onClick={onCandidateClick}
            onSelect={onCandidateSelect}
            onQuickAction={onCandidateQuickAction}
            onSubStatusChange={onSubStatusChange}
            subStatusOptions={subStatusOptions}
            onDragStart={handleCandidateDragStart}
            onDragEnd={onDragEnd}
          />
        ))}
      </div>
    </div>
  )
})
KanbanColumn.displayName = 'KanbanColumn'

export { KanbanColumn, getColumnStyle }
export default KanbanColumn
