'use client'

import React, { useState, memo } from 'react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Chip } from '@/components/ui/chip'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { 
  BrainCircuit, 
  Target, 
  Eye, 
  Bell, 
  Pin, 
  CheckCircle
} from 'lucide-react'
import { textStyles, buttonStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { type UrgencyLevel } from '../utils/status-utils'
import { CandidateBadges } from './CandidateBadges'
import type { KanbanCandidate } from '../types'

export interface CandidateTableRowAlert {
  type: 'urgent' | 'action' | 'warning'
  icon: React.ReactNode
  label: string
  color: string
}

export interface CandidateTableRowProps {
  candidate: KanbanCandidate
  onCandidateClick: (candidate: KanbanCandidate) => void
  isSelected?: boolean
  onToggleSelect?: (candidateId: string) => void
  calculateRanking: (candidate: KanbanCandidate) => number
  getAlerts: (candidate: KanbanCandidate) => CandidateTableRowAlert[]
  getUrgency: (ranking: number) => UrgencyLevel
  onViewBigFive?: (candidate: KanbanCandidate) => void
  onEmailCandidate?: (candidate: KanbanCandidate) => void
  viewedCandidateIds?: Set<string>
}

function getScoreBgClass(score: number): string {
  if (score >= 80) return 'bg-[color:var(--status-success)]'
  if (score >= 60) return 'bg-[color:var(--status-warning)]'
  if (score >= 40) return 'bg-[color:var(--lia-text-tertiary)]'
  return 'bg-[color:var(--lia-text-secondary)]'
}

function getStageBgClass(stage: string): string {
  switch (stage) {
    case 'Funil': return 'bg-[color:var(--lia-border-subtle)]'
    case 'Triagem': return 'bg-[color:var(--lia-border-default)]'
    case 'Entrevista': return 'bg-[color:var(--lia-text-tertiary)]'
    case 'Final': return 'bg-[color:var(--lia-text-secondary)]'
    case 'Aprovados': return 'bg-[color:var(--status-success)]'
    default: return 'bg-[color:var(--lia-border-subtle)]'
  }
}

function getBigFiveBgClass(value: number, index: number): string {
  if (value >= 70) {
    if (index === 0) return 'bg-[color:var(--status-success)]'
    if (index === 1) return 'bg-[color:var(--lia-text-tertiary)]'
    return 'bg-[color:var(--lia-border-default)]'
  }
  if (value >= 40) {
    if (index === 0) return 'bg-[color:var(--lia-text-secondary)]'
    if (index === 1) return 'bg-[color:var(--lia-border-default)]'
    return 'bg-[color:var(--lia-text-secondary)]'
  }
  return 'bg-[color:var(--lia-text-secondary)]'
}

const CandidateTableRowComponent = memo(function CandidateTableRow({ 
  candidate, 
  onCandidateClick, 
  isSelected, 
  onToggleSelect, 
  calculateRanking, 
  getAlerts, 
  getUrgency, 
  onViewBigFive, 
  onEmailCandidate, 
  viewedCandidateIds = new Set()
}: CandidateTableRowProps) {
  const [showActions, setShowActions] = useState(false)
  const ranking = calculateRanking(candidate)
  const alerts = getAlerts(candidate)
  const urgency = getUrgency(ranking)

  const liaScore = candidate.liaScore ?? candidate.score
  const skillsMatch = candidate.skillsMatch ?? candidate.fitScore ?? 0
  const technicalTestScore = candidate.technicalTestScore
  const englishTestScore = candidate.englishTestScore
  const candidateCode = candidate.candidateCode ?? candidate.id?.substring(0, 6).toUpperCase()
  const bigFiveData = candidate.bigFive ?? null
  const hasBigFive = !!(candidate.bigFive || candidate.bigFiveScores)

  return (
    <tr
      data-testid={`candidate-row-${candidate.id}`}
      className={` dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover cursor-pointer transition-colors motion-reduce:transition-none ${
        isSelected ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : ''
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      onClick={() => onCandidateClick(candidate)}
    >
      <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
        <div
          data-testid={`candidate-select-${candidate.id}`}
          onClick={() => onToggleSelect && onToggleSelect(candidate.id)}
          className="cursor-pointer"
        >
          <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors motion-reduce:transition-none ${
            isSelected
              ? 'bg-lia-btn-primary-bg border-lia-btn-primary-bg dark:border-lia-border-subtle'
              : 'bg-lia-bg-primary dark:bg-lia-bg-elevated border-lia-border-default dark:border-lia-border-default hover:border-lia-border-medium dark:hover:border-lia-border-medium'
          }`}>
            {isSelected && (
              <CheckCircle className="w-3.5 h-3.5 text-white" fill="currentColor" />
            )}
          </div>
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs font-mono text-lia-text-secondary">
          {candidateCode}
        </div>
      </td>

      <td className="px-3 py-2">
        <div className="flex items-center gap-1 justify-center">
          <BrainCircuit className={`w-3 h-3 ${
            urgency.level === 'average' ? 'text-lia-text-secondary' : 'text-lia-text-primary'
          }`} />
          <span className={`text-sm font-semibold ${
            urgency.level === 'average' ? 'text-lia-text-secondary' : 'text-lia-text-primary'
          }`}>
            {ranking}
          </span>
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          {(liaScore !== null && liaScore !== undefined) ? (
            <>
              <BrainCircuit className="w-3 h-3 text-lia-text-primary" />
              <Chip 
                variant="neutral" muted 
                className="text-xs px-2 py-0.5 font-semibold border-0 text-lia-text-primary bg-[color:var(--lia-border-default)]"
              >
                {formatScorePercent(liaScore, 0)}
              </Chip>
            </>
          ) : (
            <span className="text-xs text-lia-text-secondary">—</span>
          )}
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          <Target className="w-3 h-3 text-lia-text-primary" />
          <Chip 
            variant="neutral" muted 
            className="text-xs px-2 py-0.5 font-semibold border-0 text-lia-text-primary bg-[color:var(--lia-text-tertiary)]"
          >
            {formatScorePercent(skillsMatch, 0)}
          </Chip>
        </div>
      </td>

      <td className="px-2 py-2">
        {(technicalTestScore !== null && technicalTestScore !== undefined) ? (
          <div className="flex items-center gap-1 justify-center group">
            <Chip
              variant="neutral" muted
              className={`text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none text-lia-text-primary ${getScoreBgClass(technicalTestScore)}`}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent(technicalTestScore, 0)}
            </Chip>
            <Eye className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none" />
          </div>
        ) : (
          <span className="text-xs text-lia-text-secondary">—</span>
        )}
      </td>

      <td className="px-2 py-2">
        {(englishTestScore !== null && englishTestScore !== undefined) ? (
          <div className="flex items-center gap-1 justify-center group">
            <Chip
              variant="neutral" muted
              className={`text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none text-lia-text-primary ${getScoreBgClass(englishTestScore)}`}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent(englishTestScore, 0)}
            </Chip>
            <Eye className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none" />
          </div>
        ) : (
          <span className="text-xs text-lia-text-secondary">—</span>
        )}
      </td>

      <td className="px-3 py-2">
        {hasBigFive ? (
          <div 
            data-testid={`candidate-bigfive-${candidate.id}`}
            className="flex gap-1 justify-center cursor-pointer group"
            onClick={(e) => {
              e.stopPropagation()
              if (onViewBigFive) {
                onViewBigFive(candidate)
              }
            }}
            title="Clique para ver relatório completo"
          >
            {Object.entries(bigFiveData || {}).slice(0, 3).map(([key, value], index) => (
              <div
                key={key}
                className="flex flex-col items-center"
                title={`${key}: ${value}%`}
              >
                <div 
                  className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold transition-opacity motion-reduce:transition-none group-hover:opacity-80 text-lia-text-primary ${getBigFiveBgClass(value, index)}`}
                >
                  {value}
                </div>
              </div>
            ))}
            <Eye className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none self-center ml-1" />
          </div>
        ) : (
          <span className="text-xs text-lia-text-secondary">—</span>
        )}
      </td>

      <td className="px-3 py-2">
        {alerts.length > 0 ? (
          <Popover>
            <PopoverTrigger asChild>
              <button 
                data-testid={`candidate-alerts-${candidate.id}`}
                className="relative flex items-center justify-center w-8 h-8 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl transition-colors motion-reduce:transition-none group"
                aria-label={`${alerts.length} alerta${alerts.length > 1 ? 's' : ''} da LIA`}
              >
                <Bell className="w-4 h-4 text-lia-text-secondary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-disabled" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-bold rounded-full flex items-center justify-center">
                  {alerts.length}
                </span>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-3" align="start">
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
                  <Bell className="w-3.5 h-3.5" />
                  Alertas LIA ({alerts.length})
                </h4>
                {alerts.map((alert, index) => (
                  <div
                    key={`alert-${index}`}
                    className={`flex items-start gap-2 p-2 rounded-md border text-xs ${alert.color}`}
                  >
                    <span className="flex-shrink-0 mt-0.5">{alert.icon}</span>
                    <span className="flex-1 font-medium leading-relaxed">{alert.label}</span>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        ) : (
          <span className="text-xs text-lia-text-secondary flex items-center justify-center">—</span>
        )}
      </td>

      <td className="px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Avatar className="w-8 h-8">
              <AvatarImage src={candidate.avatar} alt={candidate.name} />
              <AvatarFallback>{candidate.name.split(' ').map((n: string) => n[0]).join('')}</AvatarFallback>
            </Avatar>
            {viewedCandidateIds.has(candidate.id) && (
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-lia-border-default rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                <Eye className="w-2.5 h-2.5 text-white" />
              </div>
            )}
          </div>
          <div className="font-medium text-sm text-lia-text-primary">
            {candidate.name}
          </div>
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs text-lia-text-primary">
          {candidate.role || candidate.position || 'UX Designer'}
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs text-lia-text-primary">
          {candidate.currentCompany || (candidate.source === 'LinkedIn' ? 'TechCorp' : 'Digital Agency')}
        </div>
      </td>

      <td className="px-2 py-2">
        <Chip variant="neutral" muted
          className={`text-xs font-semibold border-0 whitespace-nowrap text-lia-text-primary ${getStageBgClass(candidate.stage || '')}`}
        >
          {candidate.stage}
        </Chip>
      </td>

      <td className="px-4 py-2">
        <div className="space-y-1">
          <div className="text-xs text-lia-text-secondary">
            {candidate.status || 'Novo'}
          </div>
          <CandidateBadges
            subStatus={candidate.subStatus || candidate.status}
            actionBehavior={candidate.actionBehavior}
            stageId={candidate.stageId}
            needsAction={candidate.needsAction}
            lastActionDate={candidate.lastActionDate}
            slaHours={candidate.slaHours}
            compact
          />
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            data-testid={`candidate-pin-${candidate.id}`}
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            title="Fixar"
          >
            <Pin className="w-3 h-3" />
          </Button>
        </div>
      </td>
    </tr>
  )
})

CandidateTableRowComponent.displayName ="CandidateTableRow"

export const CandidateTableRow = CandidateTableRowComponent
