'use client'

import React, { memo } from 'react'
import { CandidateAvatar } from '@/components/candidate-profile/CandidateAvatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel
} from '@/components/ui/dropdown-menu'
import { 
  MoreVertical, 
  Eye, 
  Mail, 
  MessageCircle, 
  Calendar, 
  ClipboardList, 
  MessageSquareText, 
  Heart, 
  EyeOff,
  Zap,
  Briefcase,
  Building,
  MapPin,
  Gauge,
  BrainCircuit,
  Target,
  Code,
  Globe,
  Fingerprint
} from 'lucide-react'
import { ScoreIconButton } from '@/components/ui/score-icon-button'
import { WarningBadge, SourceBadge, StatusBadge, ChannelBadge, DateTimeBadge, OriginBadge, AwaitingBadge } from '@/components/ui/status-badge'
import { textStyles, buttonStyles, cardStyles, badgeStyles, formatScorePercent } from '@/lib/design-tokens'
import { isApplicationSource } from '@/lib/recruitment-stages'
import type { KanbanCandidate } from '../types'
import { CandidateBadges } from './CandidateBadges'
import { OverrideApproveButton } from './OverrideApproveButton'
import { SUB_STATUS_DISPLAY_MAP } from '../utils/badge-utils'

export type QuickActionType = 
  | 'email' 
  | 'whatsapp' 
  | 'schedule_interview' 
  | 'wsi_screening' 
  | 'feedback' 
  | 'toggle_favorite' 
  | 'hide' 
  | 'view_details'
  | 'open_score_modal'

export interface CandidateCardProps {
  candidate: KanbanCandidate
  stageId: string
  vacancyId?: string
  isSelected?: boolean
  isDragging?: boolean
  isFavorite?: boolean
  isViewed?: boolean
  onSelect?: (candidateId: string) => void
  onClick?: (candidate: KanbanCandidate) => void
  onQuickAction?: (action: QuickActionType, candidate: KanbanCandidate, extra?: Record<string, unknown>) => void
  onOverrideApproved?: (candidateId: string) => void
  onSubStatusChange?: (candidateId: string, newSubStatus: string, stage: string) => void
  subStatusOptions?: Array<{ code: string; display_name: string }>
  onDragStart?: (e: React.DragEvent, candidate: KanbanCandidate) => void
  onDragEnd?: (e: React.DragEvent) => void
  index?: number
  dropZoneActive?: boolean
}

const getAvatarUrl = (_id: string, _name: string): string | undefined => {
  return undefined
}

const calculateGeneralScore = (candidate: KanbanCandidate): number | null => {
  const scores: number[] = []
  if (candidate.score != null) scores.push(candidate.score)
  if (candidate.fitScore != null) scores.push(candidate.fitScore)
  if (candidate.wsiScore != null) scores.push(candidate.wsiScore)
  if (scores.length === 0) return null
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
}

const CandidateCard = memo(function CandidateCard({
  candidate,
  stageId,
  vacancyId,
  isSelected = false,
  isDragging = false,
  isFavorite = false,
  isViewed = false,
  onSelect,
  onClick,
  onQuickAction,
  onOverrideApproved,
  onSubStatusChange,
  subStatusOptions,
  onDragStart,
  onDragEnd,
  index = 0,
  dropZoneActive = false
}: CandidateCardProps) {
  const avatarUrl = candidate.avatar?.startsWith('http') 
    ? candidate.avatar 
    : getAvatarUrl(candidate.id || '', candidate.name || '')

  const generalScore = calculateGeneralScore(candidate)
  const screeningScore = candidate.score
  const cvScore = candidate.fitScore
  const b5Data = candidate.bigFive
  const b5Score = b5Data 
    ? Math.round(Object.values(b5Data).reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0) / Object.values(b5Data).length) 
    : null

  const scores = [
    { id: 'geral', icon: Gauge, value: generalScore, label: 'Geral', alwaysClickable: false },
    { id: 'triagem', icon: BrainCircuit, value: screeningScore, label: 'Triagem', alwaysClickable: true },
    { id: 'cv', icon: Target, value: cvScore, label: 'CV', alwaysClickable: true },
    { id: 'tecnico', icon: Code, value: null, label: 'Técnico', alwaysClickable: false },
    { id: 'ingles', icon: Globe, value: null, label: 'Inglês', alwaysClickable: false },
    { id: 'b5', icon: Fingerprint, value: b5Score, label: 'B5', alwaysClickable: false }
  ]

  const handleCardClick = () => {
    if (!isDragging && onClick) {
      onClick(candidate)
    }
  }

  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onSelect) {
      onSelect(candidate.id)
    }
  }

  const handleQuickAction = (action: QuickActionType, extra?: Record<string, unknown>) => (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onQuickAction) {
      onQuickAction(action, candidate, extra)
    }
  }

  const handleDragStartInternal = (e: React.DragEvent) => {
    if (onDragStart) {
      onDragStart(e, candidate)
    }
  }

  return (
    <div
      draggable
      onDragStart={handleDragStartInternal}
      onDragEnd={onDragEnd}
      className={`bg-lia-bg-primary dark:bg-lia-bg-primary rounded-md border relative overflow-hidden ${
        candidate.needsAction ? 'border-l-4 border-l-lia-btn-primary-hover border-lia-border-subtle dark:border-lia-border-subtle' : 
        (candidate.status === 'triado_aprovado' || candidate.status === 'triado') && stageId === 'screening' ? 'border-l-4 border-l-lia-border-default dark:border-l-lia-border-medium border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : 
        'border-lia-border-subtle dark:border-lia-border-subtle'
      } ${isDragging ? 'opacity-50 cursor-grabbing' : 'cursor-move'} transition-colors duration-300 group`}
      style={{animationDelay: `${index * 50}ms`,
        minHeight: '110px',
        transition: 'all 0.3s ease',
        animation: dropZoneActive ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : undefined}}
      onMouseEnter={(e) => {
        if (!isDragging) {
          e.currentTarget.style.transform = 'translateY(-1px)'
          e.currentTarget.style.boxShadow = '0 4px 12px var(--overlay-10)'
        }
      }}
      onMouseLeave={(e) => {
        if (!isDragging) {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = ''
        }
      }}
      onClick={handleCardClick}
    >
      {candidate.needsAction && (
        <div 
          className="px-2 py-0.5 border-b bg-lia-bg-tertiary"
        >
          <div className="flex items-center gap-1">
            <Zap className="w-2 h-2 animate-pulse motion-reduce:animate-none text-lia-text-secondary" />
            <span className="text-micro font-bold text-lia-text-secondary">
              Ação Necessária
            </span>
          </div>
        </div>
      )}

      <div className="p-2 relative">
        <div className="absolute right-2 top-8 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none z-10">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-1 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-md transition-opacity motion-reduce:transition-none bg-lia-bg-primary/80 dark:bg-lia-bg-primary/80"
                onClick={(e) => e.stopPropagation()}
                title="Mais opções"
              >
                <MoreVertical className="w-3 h-3 text-lia-text-secondary" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent side="right" align="start" sideOffset={8} className="w-48">
              <DropdownMenuItem 
                onClick={handleQuickAction('email')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <Mail className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Enviar Email
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={handleQuickAction('whatsapp')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <MessageCircle className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Enviar WhatsApp
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={handleQuickAction('schedule_interview')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <Calendar className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Agendar Entrevista
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={handleQuickAction('wsi_screening')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <ClipboardList className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Triagem WSI
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={handleQuickAction('feedback')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <MessageSquareText className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Enviar Feedback
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={handleQuickAction('toggle_favorite')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <Heart className={`w-3.5 h-3.5 mr-2 ${isFavorite ? 'fill-red-500 text-status-error' : 'text-lia-text-secondary'}`} />
                {isFavorite ? 'Remover dos Favoritos' : 'Adicionar a Favoritos'}
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={handleQuickAction('hide')} 
                className="text-xs text-lia-text-primary hover:bg-lia-bg-secondary cursor-pointer" 
               
              >
                <EyeOff className="w-3.5 h-3.5 mr-2 text-lia-text-secondary" />
                Ocultar Candidato
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <button
            className="p-1 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-md transition-colors motion-reduce:transition-none bg-lia-bg-primary/80 dark:bg-lia-bg-primary/80"
            onClick={handleQuickAction('view_details')}
            title="Ver detalhes do candidato"
          >
            <Eye className="w-3.5 h-3.5 text-lia-text-primary" />
          </button>
        </div>

        <div className="flex items-center gap-1.5 mb-2 pr-6">
          <input
            type="checkbox"
            checked={isSelected}
            className="w-3 h-3 rounded-md cursor-pointer flex-shrink-0 border border-lia-border-subtle"
            onClick={handleCheckboxClick}
            onChange={() => {}}
          />

          <div className="relative flex-shrink-0">
            <CandidateAvatar
              name={candidate.name}
              avatarUrl={avatarUrl}
              size="sm"
            />
            {isViewed && (
              <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-lia-border-default rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                <Eye className="w-2 h-2 text-white" />
              </div>
            )}
          </div>

          <div className="flex items-center gap-1 flex-1 min-w-0">
            <h4 className="font-medium text-xs truncate text-lia-text-primary">
              {candidate.name}
            </h4>
          </div>
        </div>

        <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
          {scores.map(({ id, icon: Icon, value, label, alwaysClickable }) => (
            <ScoreIconButton
              key={id}
              id={id}
              icon={Icon}
              value={value}
              formattedValue={value ? formatScorePercent(value, 0) : undefined}
              label={label}
              alwaysClickable={alwaysClickable}
              // @ts-ignore TODO: fix type — Argument of type 'string' is not assignable to parameter of type 'Record<string,
              onClick={() => onQuickAction?.('open_score_modal', candidate, id)}
            />
          ))}
        </div>

        <div className="space-y-0 mb-1.5">
          <div className="flex items-center gap-1 text-xs">
            <Briefcase className="w-2.5 h-2.5 flex-shrink-0" />
            <span className="truncate">{candidate.role || 'Cargo não informado'}</span>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <Building className="w-2.5 h-2.5 flex-shrink-0" />
            <span className="truncate">{candidate.currentCompany || candidate.company || 'Não informado'}</span>
          </div>
          {candidate.location && (
            <div className="flex items-center gap-1 text-xs">
              <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
              <span className="truncate">{candidate.location}</span>
            </div>
          )}
        </div>

        <div className="mt-2 flex flex-wrap gap-1">
          {candidate.warnings && candidate.warnings > 0 && (
            <WarningBadge days={candidate.warnings} />
          )}

          {candidate.origin && (
            <OriginBadge origin={candidate.origin} />
          )}

          {(candidate.status === 'awaiting_screening' || candidate.sub_status === 'awaiting_screening' || candidate.subStatus === 'awaiting_screening') && (
            <>
              <AwaitingBadge />
              {vacancyId && (
                <OverrideApproveButton
                  candidateId={candidate.id}
                  candidateName={candidate.name}
                  vacancyId={vacancyId}
                  onApproved={onOverrideApproved}
                />
              )}
            </>
          )}

          <SourceBadge 
            source={candidate.source || 'website'} 
            isApplication={isApplicationSource(candidate.source || 'website')}
          />

          {(candidate.subStatus || candidate.sub_status) && onSubStatusChange && subStatusOptions && subStatusOptions.length > 0 ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <button className="cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none">
                  <StatusBadge
                    stageId={stageId}
                    subStatus={candidate.subStatus || candidate.sub_status}
                  />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-44">
                <DropdownMenuLabel className="text-micro text-lia-text-secondary">Alterar Sub-status</DropdownMenuLabel>
                {subStatusOptions.map((opt) => {
                  const display = SUB_STATUS_DISPLAY_MAP[opt.code]
                  const isCurrent = opt.code === (candidate.subStatus || candidate.sub_status)
                  return (
                    <DropdownMenuItem
                      key={opt.code}
                      className={`text-xs cursor-pointer ${isCurrent ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        onSubStatusChange(candidate.id, opt.code, stageId)
                      }}
                    >
                      {display?.label || opt.display_name}
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (candidate.subStatus || candidate.sub_status) ? (
            <StatusBadge
              stageId={stageId}
              subStatus={candidate.subStatus || candidate.sub_status}
            />
          ) : null}
        </div>

        <CandidateBadges
          subStatus={candidate.subStatus}
          actionBehavior={candidate.actionBehavior}
          stageId={stageId}
          needsAction={candidate.needsAction}
          lastActionDate={candidate.lastActionDate}
          slaHours={candidate.slaHours}
        />
      </div>
    </div>
  )
})
CandidateCard.displayName = 'CandidateCard'

export { CandidateCard }
export default CandidateCard
