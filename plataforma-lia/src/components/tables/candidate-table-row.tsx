"use client"

import React from "react"
import type { CandidateRowProps, TableColumn } from "./types"
import {
  CandidateCell,
  ScoreCell,
  LocationCell,
  CompanyCell,
  PositionCell,
  LinkedInCell,
  SalaryCell,
  SourceCell,
  SkillsCell,
  WorkModelCell,
  SelectionCheckbox,
  ActionButtons,
  SubStatusCell,
  StageCell,
  InteractiveSubStatusCell,
  InteractiveStageCell
} from "./cell-renderers"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

export function CandidateTableRow({
  candidate,
  columns,
  isSelected = false,
  isPinned = false,
  isFavorite = false,
  showCheckbox = false,
  needsAction = false,
  stageBorderColor,
  jobVacancyId,
  companyId,
  isInteractive = false,
  onRowClick,
  onToggleSelect,
  onTogglePin,
  onToggleFavorite,
  onStatusChange,
  onStageChange,
  onTransitionRequest,
  renderActions,
  renderLeftOverlayActions,
  renderCustomCell
}: CandidateRowProps & { companyId?: string }) {
  
  const renderCellContent = (column: TableColumn) => {
    const columnId = column.id
    
    // Check for custom cell renderer from props first
    const customCell = renderCustomCell?.(columnId)
    if (customCell !== null && customCell !== undefined) {
      return customCell
    }
    
    // Check if column has its own render function
    if (column.render) {
      return column.render(candidate, column)
    }

    switch (columnId) {
      case 'checkbox':
        return showCheckbox && onToggleSelect ? (
          <SelectionCheckbox isSelected={isSelected} onToggle={onToggleSelect} />
        ) : null

      case 'name':
      case 'candidato':
        return (
          <CandidateCell 
            candidate={candidate} 
            isPinned={isPinned} 
            isFavorite={isFavorite} 
          />
        )

      case 'score':
      case 'lia_score':
      case 'match_score':
        const score = candidate.liaAnalysis?.score || candidate.lia_score || candidate.score || 0
        return <ScoreCell score={score} />

      case 'position':
      case 'current_title':
      case 'cargo':
        return <PositionCell candidate={candidate} />

      case 'company':
      case 'current_company':
      case 'empresa':
        return <CompanyCell candidate={candidate} />

      case 'location':
      case 'location_city':
      case 'localizacao':
        return <LocationCell candidate={candidate} />

      case 'linkedin':
      case 'linkedin_url':
        return <LinkedInCell url={candidate.linkedin || candidate.linkedin_url} />

      case 'salary':
      case 'current_salary':
        return <SalaryCell value={candidate.current_salary || candidate.salary?.current} />

      case 'expected_salary':
      case 'desired_salary_max':
        return <SalaryCell value={candidate.desired_salary_max || candidate.salary?.expected} />

      case 'source':
        return <SourceCell source={candidate.source} />

      case 'status':
      case 'sub_status':
        // Usa sub_status se disponível, senão mostra o status/stage
        const statusValue = candidate.sub_status || (typeof candidate.status === 'string' ? candidate.status : undefined)
        if (isInteractive && onStatusChange) {
          return (
            <InteractiveSubStatusCell 
              candidateId={candidate.id}
              candidateName={candidate.name}
              stage={candidate.stage}
              subStatus={statusValue}
              jobVacancyId={jobVacancyId}
              onStatusChange={onStatusChange}
            />
          )
        }
        return <SubStatusCell stage={candidate.stage} subStatus={statusValue} />

      case 'stage':
      case 'etapa':
        if (isInteractive && (onStageChange || onTransitionRequest)) {
          return (
            <InteractiveStageCell 
              candidateId={candidate.id}
              candidateName={candidate.name}
              candidateRole={candidate.current_title || candidate.position}
              candidateAvatar={candidate.avatar || candidate.avatar_url}
              candidateEmail={candidate.email}
              candidatePhone={candidate.phone}
              currentStage={candidate.stage}
              onStageChange={onStageChange}
              onTransitionRequest={onTransitionRequest}
            />
          )
        }
        return <StageCell stage={candidate.stage} />

      case 'skills':
      case 'technical_skills':
        return <SkillsCell skills={candidate.skills || candidate.technical_skills} />

      case 'work_model':
      case 'workModel':
        return <WorkModelCell model={candidate.workModel || candidate.work_model_preference} />

      case 'actions':
      case 'acoes':
        return (
          <ActionButtons
            isPinned={isPinned}
            isFavorite={isFavorite}
            needsAction={needsAction}
            onTogglePin={onTogglePin}
            onToggleFavorite={onToggleFavorite}
          >
            {renderActions?.()}
          </ActionButtons>
        )

      default:
        const value = candidate[columnId]
        if (value === null || value === undefined) return null
        if (typeof value === 'object') return JSON.stringify(value)
        return <span className="text-xs text-lia-text-primary">{String(value)}</span>
    }
  }

  const rowStyle: React.CSSProperties = {
    ...(stageBorderColor ? { 
      borderLeft: `3px solid ${stageBorderColor}`,
    } : {})
  }

  const overlayContent = renderLeftOverlayActions?.()
  const firstDataColumnIndex = columns.findIndex(c => c.id !== 'checkbox')

  return (
    <tr
      className={`group cursor-pointer transition-colors motion-reduce:transition-none relative dark:border-lia-border-subtle ${
 isSelected 
          ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary hover:bg-lia-interactive-active/70 dark:hover:bg-lia-bg-inverse/70' 
          : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50'
      }`}
      style={rowStyle}
      onClick={onRowClick}
    >
      {columns.map((column, index) => (
        <td 
          key={column.id}
          className={`py-2 px-3 relative whitespace-nowrap overflow-hidden ${
 column.align === 'center' ? 'text-center' : 
            column.align === 'right' ? 'text-right' : 'text-left'
          }`}
          style={{width: column.width,
            minWidth: column.minWidth}}
        >
          {renderCellContent(column)}
          {index === firstDataColumnIndex && overlayContent && (
            <div 
              className="absolute left-0 top-0 h-full flex items-center pl-2 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none duration-200 z-20"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-0.5 bg-lia-bg-primary/95 dark:bg-lia-bg-primary/95 backdrop-blur-sm rounded-md px-1.5 py-1 border border-lia-border-subtle dark:border-lia-border-subtle">
                {overlayContent}
              </div>
            </div>
          )}
        </td>
      ))}
    </tr>
  )
}
