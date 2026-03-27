'use client'

import React, { useState } from 'react'
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

export interface CandidateTableRowAlert {
  type: 'urgent' | 'action' | 'warning'
  icon: React.ReactNode
  label: string
  color: string
}

export interface CandidateTableRowProps {
  candidate: any
  onCandidateClick: (candidate: any) => void
  isSelected?: boolean
  onToggleSelect?: (candidateId: string) => void
  calculateRanking: (candidate: any) => number
  getAlerts: (candidate: any) => CandidateTableRowAlert[]
  getUrgency: (ranking: number) => UrgencyLevel
  onViewBigFive?: (candidate: any) => void
  onEmailCandidate?: (candidate: any) => void
  viewedCandidateIds?: Set<string>
}

export function CandidateTableRow({ 
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
      className={`border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors ${
        isSelected ? 'bg-gray-100 dark:bg-gray-800/10' : ''
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
          <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
            isSelected
              ? 'bg-gray-900 border-gray-900 dark:bg-gray-200 dark:border-gray-200'
              : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 hover:border-gray-500 dark:hover:border-gray-500'
          }`}>
            {isSelected && (
              <CheckCircle className="w-3.5 h-3.5 text-white" fill="currentColor" />
            )}
          </div>
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs font-mono text-gray-600 dark:text-gray-400">
          {candidate.candidateCode || candidate.id?.substring(0, 6).toUpperCase()}
        </div>
      </td>

      <td className="px-3 py-2">
        <div className="flex items-center gap-1 justify-center">
          <BrainCircuit className={`w-3 h-3 ${
            urgency.level === 'excellent' ? 'text-gray-950 dark:text-gray-50' :
            urgency.level === 'great' ? 'text-gray-800 dark:text-gray-200' :
            urgency.level === 'good' ? 'text-gray-800 dark:text-gray-200' :
            urgency.level === 'average' ? 'text-gray-600 dark:text-gray-400' :
            urgency.level === 'below' ? 'text-gray-800 dark:text-gray-200' :
            'text-gray-600 dark:text-gray-600'
          }`} />
          <span className={`text-sm font-semibold ${
            urgency.level === 'excellent' ? 'text-gray-950 dark:text-gray-50' :
            urgency.level === 'great' ? 'text-gray-800 dark:text-gray-200' :
            urgency.level === 'good' ? 'text-gray-800 dark:text-gray-200' :
            urgency.level === 'average' ? 'text-gray-600 dark:text-gray-400' :
            urgency.level === 'below' ? 'text-gray-800 dark:text-gray-200' :
            'text-gray-600 dark:text-gray-600'
          }`}>
            {ranking}
          </span>
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          {(candidate.liaScore !== null && candidate.liaScore !== undefined) || (candidate.score !== null && candidate.score !== undefined) ? (
            <>
              <BrainCircuit className="w-3 h-3 text-gray-950 dark:text-gray-50" />
              <Badge 
                variant="secondary" 
                className="text-xs px-2 py-0.5 font-semibold border-0 text-gray-950 dark:text-gray-50"
                style={{ backgroundColor: '#A8CED5' }}
              >
                {formatScorePercent(candidate.liaScore ?? candidate.score, 0)}
              </Badge>
            </>
          ) : (
            <span className="text-xs text-gray-600 dark:text-gray-500">—</span>
          )}
        </div>
      </td>

      <td className="px-2 py-2">
        <div className="flex items-center gap-1 justify-center">
          <Target className="w-3 h-3 text-gray-950 dark:text-gray-50" />
          <Badge 
            variant="secondary" 
            className="text-xs px-2 py-0.5 font-semibold border-0 text-gray-950 dark:text-gray-50"
            style={{ backgroundColor: '#BFA8D5' }}
          >
            {formatScorePercent(candidate.skillsMatch || candidate.fitScore || 0, 0)}
          </Badge>
        </div>
      </td>

      <td className="px-2 py-2">
        {candidate.technicalTestScore !== null && candidate.technicalTestScore !== undefined ? (
          <div className="flex items-center gap-1 justify-center group">
            <Badge
              variant="secondary"
              className="text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity text-gray-950 dark:text-gray-50"
              style={{
                backgroundColor: candidate.technicalTestScore >= 80 ? '#A8D5B7' :
                                 candidate.technicalTestScore >= 60 ? '#A8CED5' :
                                 candidate.technicalTestScore >= 40 ? '#BFA8D5' :
                                 '#D5A8C6'
              }}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent(candidate.technicalTestScore, 0)}
            </Badge>
            <Eye className="w-3 h-3 text-gray-600 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        ) : (
          <span className="text-xs text-gray-600 dark:text-gray-500">—</span>
        )}
      </td>

      <td className="px-2 py-2">
        {candidate.englishTestScore !== null && candidate.englishTestScore !== undefined ? (
          <div className="flex items-center gap-1 justify-center group">
            <Badge
              variant="secondary"
              className="text-xs px-2 py-0.5 font-semibold border-0 cursor-pointer hover:opacity-80 transition-opacity text-gray-950 dark:text-gray-50"
              style={{
                backgroundColor: candidate.englishTestScore >= 80 ? '#A8D5B7' :
                                 candidate.englishTestScore >= 60 ? '#A8CED5' :
                                 candidate.englishTestScore >= 40 ? '#BFA8D5' :
                                 '#D5A8C6'
              }}
              onClick={(e) => {
                e.stopPropagation()
              }}
              title="Clique para ver detalhes"
            >
              {formatScorePercent(candidate.englishTestScore, 0)}
            </Badge>
            <Eye className="w-3 h-3 text-gray-600 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        ) : (
          <span className="text-xs text-gray-600 dark:text-gray-500">—</span>
        )}
      </td>

      <td className="px-3 py-2">
        {candidate.bigFive || candidate.bigFiveScores ? (
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
            {Object.entries(candidate.bigFive || candidate.bigFiveScores || {}).slice(0, 3).map(([key, value]: [string, any], index) => (
              <div
                key={key}
                className="flex flex-col items-center"
                title={`${key}: ${value}%`}
              >
                <div 
                  className="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold transition-opacity group-hover:opacity-80 text-gray-950 dark:text-gray-50"
                  style={{
                    backgroundColor: value >= 70 ? (index === 0 ? '#A8D5B7' : index === 1 ? '#BFA8D5' : '#A8CED5') :
                                     value >= 40 ? (index === 0 ? '#D5BFA8' : index === 1 ? '#A8CED5' : '#D5BFA8') :
                                     '#D5A8C6'
                  }}
                >
                  {value}
                </div>
              </div>
            ))}
            <Eye className="w-3 h-3 text-gray-600 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity self-center ml-1" />
          </div>
        ) : (
          <span className="text-xs text-gray-600 dark:text-gray-500">—</span>
        )}
      </td>

      <td className="px-3 py-2">
        {alerts.length > 0 ? (
          <Popover>
            <PopoverTrigger asChild>
              <button 
                className="relative flex items-center justify-center w-8 h-8 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors group"
                aria-label={`${alerts.length} alerta${alerts.length > 1 ? 's' : ''} da LIA`}
              >
                <Bell className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-100" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-950 text-xs font-bold rounded-full flex items-center justify-center">
                  {alerts.length}
                </span>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-3" align="start">
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
                  <Bell className="w-3.5 h-3.5" />
                  Alertas LIA ({alerts.length})
                </h4>
                {alerts.map((alert, index) => (
                  <div
                    key={index}
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
          <span className="text-xs text-gray-600 dark:text-gray-500 flex items-center justify-center">—</span>
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
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                <Eye className="w-2.5 h-2.5 text-white" />
              </div>
            )}
          </div>
          <div className="font-medium text-sm text-gray-950 dark:text-gray-50">
            {candidate.name}
          </div>
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs text-gray-950 dark:text-gray-50">
          {candidate.role || candidate.position || 'UX Designer'}
        </div>
      </td>

      <td className="px-4 py-2">
        <div className="text-xs text-gray-950 dark:text-gray-50">
          {candidate.currentCompany || (candidate.source === 'LinkedIn' ? 'TechCorp' : 'Digital Agency')}
        </div>
      </td>

      <td className="px-2 py-2">
        <Badge
          className="text-xs font-semibold border-0 whitespace-nowrap text-gray-950 dark:text-gray-50"
          style={{
            backgroundColor: 
              candidate.stage === 'Funil' ? '#E5E7EB' :
              candidate.stage === 'Triagem' ? '#A8CED5' :
              candidate.stage === 'Entrevista' ? '#BFA8D5' :
              candidate.stage === 'Final' ? '#D5BFA8' :
              candidate.stage === 'Aprovados' ? '#A8D5B7' :
              candidate.stage === 'Reprovados' ? '#E5E7EB' :
              '#E5E7EB'
          }}
        >
          {candidate.stage}
        </Badge>
      </td>

      <td className="px-4 py-2">
        <div className="space-y-1">
          <div className="text-xs text-gray-600 dark:text-gray-400">
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
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" title="Fixar">
            <Pin className="w-3 h-3" />
          </Button>
        </div>
      </td>
    </tr>
  )
}
