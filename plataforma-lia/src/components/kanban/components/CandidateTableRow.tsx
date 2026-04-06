'use client'

import React, { useState, memo } from 'react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
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

  return (
    <tr
      className={`border-b border-lia-border-subtle dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover cursor-pointer transition-colors motion-reduce:transition-none ${
        isSelected ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary/10' : ''
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      onClick={() => onCandidateClick(candidate)}
    >
      <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
        <div
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
          {(candidate as any).candidateCode || (candidate as any).id?.substring(0, 6).toUpperCase()}
        </div>
      </td>

      <td className="px-3 py-2">
        <div className="flex items-center gap-1 justify-center">
          <BrainCircuit className={`w-3 h-3 ${
            urgency.level === 'excellent' ? 'text-lia-text-primary' :
            urgency.level === 'great' ? 'text-lia-text-primary' :
            urgency.level === 'good' ? 'text-lia-text-primary' :
            urgency.level === 'average' ? 'text-lia-text-secondary' :
            urgency.level === 'below' ? 'text-lia-text-primary' :
            'text-lia-text-secondary'
          }`} />
          <span className={`text-sm font-semibold ${
            urgency.level === 'excellent' ? 'text-lia-text-primary' :
            urgency.level === 'great' ? 'text-lia-text-primary' :
            urgency.level === 'good' ? 'text-lia-text-primary' :
            urgency.level === 'average' ? 'text-lia-text-secondary' :
            urgency.level === 'below' ? 'text-lia-text-primary' :
            'text-lia-text-secondary'
          }`}>
            {ranking}
          </span>
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          {((candidate as any).liaScore !== null && (candidate as any).liaScore !== undefined) || ((candidate as any).score !== null && (candidate as any).score !== undefined) ? (
            <>
              <BrainCircuit className="w-3 h-3 text-lia-text-primary" />
              <Badge 
                variant="secondary" 
                className="text-xs px-2 py-0.5 font-semibold border-0 text-lia-text-primary"
                style={{backgroundColor: 'var(--lia-border-default)'} as React.CSSProperties}
              >
                {formatScorePercent((candidate as any).liaScore ?? (candidate as any).score, 0)}
              </Badge>
            </>
          ) : (
            <span className="text-xs text-lia-text-secondary">—</span>
          )}
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          <Target className="w-3 h-3 text-lia-text-primary" />
          <Badge 
            variant="secondary" 
            className="text-xs px-2 py-0.5 font-semibold border-0 text-lia-text-primary"
            style={{backgroundColor: 'var(--lia-text-tertiary)'}}
          >
            {formatScorePercent((candidate as any).skillsMatch || (candidate as any).fitScore || 0, 0)}
          </Badge>
        </div>
      </td>

      <td className="px-2 py-2">
        {(candidate as any).technicalTestScore !== null && (candidate as any).technicalTestScore !== undefined ? (
          <div className="flex items-center gap-1 justify-center group">
            <Badge
              variant="secondary"
              className="text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none text-lia-text-primary"
              style={{backgroundColor: (candidate as any).technicalTestScore >= 80 ? 'var(--status-success)' :
                                 (candidate as any).technicalTestScore >= 60 ? 'var(--status-warning)' :
                                 (candidate as any).technicalTestScore >= 40 ? 'var(--lia-text-tertiary)' :
                                 'var(--lia-text-secondary)'}}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent((candidate as any).technicalTestScore, 0)}
            </Badge>
            <Eye className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none" />
          </div>
        ) : (
          <span className="text-xs text-lia-text-secondary">—</span>
        )}
      </td>

      <td className="px-2 py-2">
        {(candidate as any).englishTestScore !== null && (candidate as any).englishTestScore !== undefined ? (
          <div className="flex items-center gap-1 justify-center group">
            <Badge
              variant="secondary"
              className="text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none text-lia-text-primary"
              style={{backgroundColor: (candidate as any).englishTestScore >= 80 ? 'var(--status-success)' :
                                 (candidate as any).englishTestScore >= 60 ? 'var(--status-warning)' :
                                 (candidate as any).englishTestScore >= 40 ? 'var(--lia-text-tertiary)' :
                                 'var(--lia-text-secondary)'}}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent((candidate as any).englishTestScore, 0)}
            </Badge>
            <Eye className="w-3 h-3 text-lia-text-secondary opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none" />
          </div>
        ) : (
          <span className="text-xs text-lia-text-secondary">—</span>
        )}
      </td>

      <td className="px-3 py-2">
        {(candidate as any).bigFive || (candidate as any).bigFiveScores ? (
          <div 
            className="flex gap-1 justify-center cursor-pointer group"
            onClick={(e) => {
              e.stopPropagation()
              if (onViewBigFive) {
                onViewBigFive(candidate)
              }
            }}
            title="Clique para ver relatório completo"
          >
            {Object.entries(candidate.bigFive || {}).slice(0, 3).map(([key, value], index) => (
              <div
                key={key}
                className="flex flex-col items-center"
                title={`${key}: ${value}%`}
              >
                <div 
                  className="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold transition-opacity motion-reduce:transition-none group-hover:opacity-80 text-lia-text-primary"
                  style={{backgroundColor: value >= 70 ? (index === 0 ? 'var(--status-success)' : index === 1 ? 'var(--lia-text-tertiary)' : 'var(--lia-border-default)') :
                                     value >= 40 ? (index === 0 ? 'var(--lia-text-secondary)' : index === 1 ? 'var(--lia-border-default)' : 'var(--lia-text-secondary)') :
                                     'var(--lia-text-secondary)'}}
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
                className="relative flex items-center justify-center w-8 h-8 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-md transition-colors motion-reduce:transition-none group"
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
          {candidate.role || (candidate as any).position || 'UX Designer'}
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs text-lia-text-primary">
          {candidate.currentCompany || (candidate.source === 'LinkedIn' ? 'TechCorp' : 'Digital Agency')}
        </div>
      </td>

      <td className="px-2 py-2">
        <Badge
          className="text-xs font-semibold border-0 whitespace-nowrap text-lia-text-primary"
          style={{backgroundColor: 
              candidate.stage === 'Funil' ? 'var(--lia-border-subtle)' :
              candidate.stage === 'Triagem' ? 'var(--lia-border-default)' :
              candidate.stage === 'Entrevista' ? 'var(--lia-text-tertiary)' :
              candidate.stage === 'Final' ? 'var(--lia-text-secondary)' :
              candidate.stage === 'Aprovados' ? 'var(--status-success)' :
              candidate.stage === 'Reprovados' ? 'var(--lia-border-subtle)' :
              'var(--lia-border-subtle)'}}
        >
          {candidate.stage}
        </Badge>
      </td>

      <td className="px-4 py-2">
        <div className="space-y-1">
          <div className="text-xs text-lia-text-secondary">
            {candidate.status || 'Novo'}
          </div>
          <CandidateBadges
            subStatus={(candidate as Record<string, unknown>).subStatus as string || candidate.status}
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
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" title="Fixar">
            <Pin className="w-3 h-3" />
          </Button>
        </div>
      </td>
    </tr>
  )
})

CandidateTableRowComponent.displayName = "CandidateTableRow"

export const CandidateTableRow = CandidateTableRowComponent
