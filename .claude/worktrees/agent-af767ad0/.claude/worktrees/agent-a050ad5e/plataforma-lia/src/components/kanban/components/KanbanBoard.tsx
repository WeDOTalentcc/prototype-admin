'use client'

import React, { useMemo, useCallback } from 'react'
import { KanbanColumn } from './KanbanColumn'
import { CandidateCard, type QuickActionType } from './CandidateCard'
import type { DynamicStage, KanbanCandidate, CandidatesDataMap } from '../types'
import { useDragDrop } from '../hooks'
import { filterKanbanCandidates, type KanbanFilterCriteria } from '../utils/filter-utils'
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

export type KanbanBoardFilters = KanbanFilterCriteria

export interface KanbanBoardProps {
  stages: DynamicStage[]
  candidatesData: CandidatesDataMap
  setCandidatesData?: React.Dispatch<React.SetStateAction<CandidatesDataMap>>
  filters?: KanbanBoardFilters
  selectedCandidates: Set<string>
  favoriteCandidates?: Set<string>
  viewedCandidates?: Set<string>
  onSelectCandidates?: (candidateIds: string[], selected: boolean) => void
  onToggleCandidateSelect?: (candidateId: string) => void
  onCandidateClick: (candidate: KanbanCandidate) => void
  onCandidateQuickAction: (action: QuickActionType, candidate: KanbanCandidate, extra?: any) => void
  onTransitionRequired?: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  onSubStatusChange?: (candidateId: string, newSubStatus: string, stage: string) => void
  subStatusOptions?: Array<{ code: string; display_name: string }>
  className?: string
}

export function KanbanBoard({
  stages,
  candidatesData,
  setCandidatesData,
  filters = {},
  selectedCandidates,
  favoriteCandidates = new Set(),
  viewedCandidates = new Set(),
  onSelectCandidates,
  onToggleCandidateSelect,
  onCandidateClick,
  onCandidateQuickAction,
  onTransitionRequired,
  onSubStatusChange,
  subStatusOptions,
  className = ''
}: KanbanBoardProps) {
  const { 
    draggedCandidate,
    dragOverColumn,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    isDragging,
    isDragEnabled
  } = useDragDrop({
    candidatesData,
    setCandidatesData,
    dynamicStages: stages,
    onTransitionRequired
  })

  const activeStages = useMemo(() => {
    return stages.filter(stage => stage.stageType === 'active')
  }, [stages])

  const finalStages = useMemo(() => {
    return stages.filter(stage => stage.stageType === 'final')
  }, [stages])

  const getFilteredCandidates = useCallback((stageId: string): KanbanCandidate[] => {
    const stageCandidates = candidatesData[stageId] || []
    return filterKanbanCandidates(stageCandidates, filters)
  }, [candidatesData, filters])

  const handleSelectAll = useCallback((stageId: string, candidateIds: string[]) => {
    if (onSelectCandidates) {
      const currentStage = candidatesData[stageId] || []
      const currentStageIds = currentStage.map(c => c.id)
      
      if (candidateIds.length > 0) {
        onSelectCandidates(candidateIds, true)
      } else {
        onSelectCandidates(currentStageIds, false)
      }
    }
  }, [candidatesData, onSelectCandidates])

  const renderColumn = (stage: DynamicStage) => {
    const filteredCandidates = getFilteredCandidates(stage.id)
    
    return (
      <KanbanColumn
        key={stage.id}
        stage={stage}
        candidates={filteredCandidates}
        isDropTarget={dragOverColumn === stage.id}
        selectedCandidates={selectedCandidates}
        favoriteCandidates={favoriteCandidates}
        viewedCandidates={viewedCandidates}
        onSelectAll={handleSelectAll}
        onCandidateClick={onCandidateClick}
        onCandidateSelect={onToggleCandidateSelect}
        onCandidateQuickAction={onCandidateQuickAction}
        onSubStatusChange={onSubStatusChange}
        subStatusOptions={subStatusOptions}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        isDragging={isDragging}
      />
    )
  }

  return (
    <div className={`flex gap-2 overflow-x-auto pb-2 ${className}`}>
      {activeStages.map(renderColumn)}
      
      {finalStages.length > 0 && (
        <>
          <div className="flex-shrink-0 w-px bg-gray-300 dark:bg-gray-600 mx-1" />
          {finalStages.map(renderColumn)}
        </>
      )}
    </div>
  )
}

export default KanbanBoard
