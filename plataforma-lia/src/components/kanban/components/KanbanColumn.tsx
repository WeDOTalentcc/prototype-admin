'use client'

import React, { useMemo } from 'react'
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
  onCandidateQuickAction: (action: QuickActionType, candidate: KanbanCandidate, extra?: any) => void
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
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      dot: 'bg-gray-700 dark:bg-gray-300',
      header: 'text-gray-800 dark:text-gray-200',
      accentColor: '#374151'
    },
    hired: {
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      dot: 'bg-gray-700 dark:bg-gray-300',
      header: 'text-gray-800 dark:text-gray-200',
      accentColor: '#374151'
    },
    rejected: {
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      dot: 'bg-gray-300 dark:bg-gray-600',
      header: 'text-gray-800 dark:text-gray-200',
      accentColor: '#D1D5DB'
    },
    offer_declined: {
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      dot: 'bg-gray-300 dark:bg-gray-600',
      header: 'text-gray-800 dark:text-gray-200',
      accentColor: '#D1D5DB'
    }
  }

  if (fixedStyles[columnId]) {
    return fixedStyles[columnId]
  }

  return {
    bg: 'bg-white dark:bg-gray-900',
    border: 'border-gray-200 dark:border-gray-700',
    dot: 'bg-gray-500 dark:bg-gray-400',
    header: 'text-gray-800 dark:text-gray-200',
    accentColor: stageColor || '#6B7280'
  }
}

const sortScreeningCandidates = (candidates: KanbanCandidate[]): KanbanCandidate[] => {
  return [...candidates].sort((a, b) => {
    if (a.needsAction && !b.needsAction) return -1
    if (!a.needsAction && b.needsAction) return 1
    return (b.score || 0) - (a.score || 0)
  })
}

export function KanbanColumn({
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

  const handleSelectAllChange = (checked: boolean | 'indeterminate') => {
    if (checked === true) {
      onSelectAll(stage.id, candidateIds)
    } else {
      onSelectAll(stage.id, [])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    onDragOver(e, stage.id)
  }

  const handleDrop = (e: React.DragEvent) => {
    onDrop(e, stage.id)
  }

  const handleCandidateDragStart = (e: React.DragEvent, candidate: KanbanCandidate) => {
    onDragStart(e, candidate, stage.id)
  }

  return (
    <div
      className={`flex flex-col flex-1 bg-white dark:bg-gray-900 rounded-md min-w-[275px] max-w-[368px] border border-gray-200 dark:border-gray-700 transition-all duration-300 ${
        isDropTarget ? 'ring-2 ring-gray-400 bg-gray-50 dark:bg-gray-800' : ''
      } h-[calc(100vh-16rem)]`}
      onDragOver={handleDragOver}
      onDragLeave={onDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex-shrink-0 p-2.5 pb-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div 
              className={`w-2 h-2 rounded-full ${columnStyle.dot} transition-transform duration-300 ${
                isDropTarget ? 'scale-150' : ''
              }`}
            />
            <h3 className={`font-medium text-xs ${columnStyle.header}`}>
              {stage.displayName}
            </h3>
            <span className="text-micro text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
              {sortedCandidates.length}
            </span>
          </div>
          {sortedCandidates.length > 0 && (
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAllChange}
              className="w-3.5 h-3.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900 dark:data-[state=checked]:bg-gray-200 dark:data-[state=checked]:border-gray-200"
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
}

export { getColumnStyle }
export default KanbanColumn
