"use client"
import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import NextImage from"next/image"

import React, { useState, lazy, Suspense } from"react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from"@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  MapPin, Linkedin, Building2, Star, Pin, Github, Globe,
  Mail, Phone, Briefcase, CheckCircle, StickyNote, Zap, ChevronDown, ArrowRight, Brain, Loader2, Info
} from"lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from"@/components/ui/tooltip"
import { toast } from"sonner"
import type { TableCandidate } from"./types"
import {
  getSubStatusDisplayName,
  SUB_STATUSES,
  type SubStatus,
} from "@/lib/recruitment-stages"
import { RECRUITMENT_STAGES, type RecruitmentStage } from "@/lib/recruitment/stages-data"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { 
  DataRequestIndicator, 
  type DataRequestStatus, 
  type RequestedField 
} from"@/components/ui/data-request-indicator"

const getRandomAvatarUrl = (_candidateId: string, _name: string): string | undefined => {
  return undefined
}

export interface CandidateCellDataRequest {
  status: DataRequestStatus
  fieldsRequested: RequestedField[]
  fieldsCompleted: RequestedField[]
  expiresAt?: Date | string | null
}

export function CandidateCell({ 
  candidate, 
  isPinned, 
  isFavorite,
  dataRequest,
  onDataRequestResend,
  onDataRequestViewDetails
}: { 
  candidate: TableCandidate
  isPinned?: boolean
  isFavorite?: boolean
  dataRequest?: CandidateCellDataRequest | null
  onDataRequestResend?: (candidateId: string) => void
  onDataRequestViewDetails?: (candidateId: string) => void
}) {
  const initials = candidate.name
    ?.split(' ')
    .map((n: string) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '??'

  const avatarUrl = candidate.avatar || candidate.avatar_url || getRandomAvatarUrl(candidate.id || '', candidate.name || '')

  return (
    <div className="flex items-center gap-2">
      <Avatar className="w-8 h-8">
        <AvatarImage src={avatarUrl} />
        <AvatarFallback 
          className="text-xs font-medium bg-wedo-cyan/15"
        >
          {initials}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-xs text-lia-text-primary truncate">
            {candidate.name}
          </span>
          {dataRequest && (
            <DataRequestIndicator
              candidateId={candidate.id || ''}
              status={dataRequest.status}
              fieldsRequested={dataRequest.fieldsRequested}
              fieldsCompleted={dataRequest.fieldsCompleted}
              expiresAt={dataRequest.expiresAt}
              onResend={onDataRequestResend}
              onViewDetails={onDataRequestViewDetails}
              size="sm"
            />
          )}
          {isPinned && (
            <Pin className="w-2.5 h-2.5 text-lia-text-secondary fill-current flex-shrink-0" />
          )}
          {isFavorite && (
            <Star className="w-2.5 h-2.5 text-wedo-orange fill-current flex-shrink-0" />
          )}
        </div>
        {candidate.email && (
          <span className="text-xs text-lia-text-secondary truncate block">
            {candidate.email}
          </span>
        )}
      </div>
    </div>
  )
}

export function ScoreCell({ score, showIcon = true }: { score: number; showIcon?: boolean }) {
  const getScoreStyle = (score: number): React.CSSProperties => {
    if (score >= 90) return { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--status-success)' }
    if (score >= 80) return { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-cyan-dark)' }
    if (score >= 70) return { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-orange)' }
    return { color: 'var(--lia-text-primary)' }
  }

  if (!score || score <= 0) return null

  const formattedScore = Number.isInteger(score) ? score : score.toFixed(1)

  return (
    <Chip density="relaxed" variant="neutral" muted className="px-1.5 py-0.5" style={getScoreStyle(score)}>
      {showIcon && <Star className="w-2.5 h-2.5 mr-0.5" />}
      {formattedScore}
    </Chip>
  )
}

export function LocationCell({ candidate }: { candidate: TableCandidate }) {
  const location = candidate.location || candidate.location_city || 
    (candidate.location_city && candidate.location_state 
      ? `${candidate.location_city}, ${candidate.location_state}` 
      : null)

  if (!location) return null

  return (
    <div className="flex items-center gap-1 text-xs text-lia-text-primary">
      <MapPin className="w-3 h-3 flex-shrink-0" />
      <span className="truncate max-w-[100px]">{location}</span>
    </div>
  )
}

export function CompanyCell({ candidate }: { candidate: TableCandidate }) {
  const company = (candidate.current_company || (candidate.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.company) as string | null | undefined

  if (!company) return null

  return (
    <div className="flex items-center gap-1 text-xs text-lia-text-primary">
      <Building2 className="w-3 h-3 flex-shrink-0" />
      <span className="truncate max-w-[120px]">{company}</span>
    </div>
  )
}

export function PositionCell({ candidate }: { candidate: TableCandidate }) {
  const position = candidate.position || candidate.current_title

  if (!position) return null

  return (
    <span className="text-xs text-lia-text-primary truncate">
      {position}
    </span>
  )
}

export function LinkedInCell({ url, onClick }: { url?: string; onClick?: (e: React.MouseEvent) => void }) {
  if (!url) return null

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => {
        e.stopPropagation()
        onClick?.(e)
      }}
      className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
    >
      <Linkedin className="w-3.5 h-3.5" />
    </a>
  )
}

export function SalaryCell({ value, currency = 'BRL' }: { value?: number; currency?: string }) {
  if (!value) return null

  const formatted = new Intl.NumberFormat('pt-BR', { 
    style: 'currency', 
    currency 
  }).format(value)

  return (
    <span className="text-xs text-lia-text-primary">
      {formatted}
    </span>
  )
}

export function SourceCell({ source }: { source?: string }) {
  if (!source) return null

  const getSourceConfig = (src: string): { label: string; style: React.CSSProperties } => {
    const lower = src.toLowerCase()
    if (lower.includes('linkedin')) return { label: 'LinkedIn', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-cyan-dark)' } }
    if (lower.includes('pearch')) return { label: 'Pearch', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-purple)' } }
    if (lower.includes('local') || lower.includes('base')) return { label: 'Base Local', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--status-success)' } }
    if (lower.includes('manual') || lower.includes('recruiter')) return { label: 'Manual', style: { color: 'var(--lia-text-primary)' } }
    return { label: src, style: { color: 'var(--lia-text-primary)' } }
  }

  const config = getSourceConfig(source)

  return (
    <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5" style={config.style}>
      {config.label}
    </Chip>
  )
}

export function ContactCell({ 
  email, 
  phone,
  hasEmail,
  hasPhone,
  has_email,
  has_phone,
  showReveal = false 
}: { 
  email?: string
  phone?: string
  hasEmail?: boolean
  hasPhone?: boolean
  has_email?: boolean
  has_phone?: boolean
  showReveal?: boolean
}) {
  const emailAvailable = hasEmail ?? has_email
  const phoneAvailable = hasPhone ?? has_phone
  const displayEmail = email || (emailAvailable ? '••••@••••' : null)
  const displayPhone = phone || (phoneAvailable ? '(••) •••••-••••' : null)

  return (
    <div className="flex items-center gap-2">
      {displayEmail && (
        <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
          <Mail className="w-3 h-3" />
          <span className="truncate max-w-[100px]">{displayEmail}</span>
        </div>
      )}
      {displayPhone && (
        <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
          <Phone className="w-3 h-3" />
          <span>{displayPhone}</span>
        </div>
      )}
    </div>
  )
}

export function SkillsCell({ skills, maxShow = 3 }: { skills?: string[]; maxShow?: number }) {
  if (!skills || skills.length === 0) return null

  const visible = skills.slice(0, maxShow)
  const remaining = skills.length - maxShow

  return (
    <div className="flex flex-wrap gap-1">
      {visible.map((skill, idx) => (
        <Chip key={idx} variant="neutral" muted className="text-micro px-1.5 py-0">
          {skill}
        </Chip>
      ))}
      {remaining > 0 && (
        <Chip variant="neutral" className="text-micro px-1.5 py-0">
          +{remaining}
        </Chip>
      )}
    </div>
  )
}

export function WorkModelCell({ model }: { model?: string }) {
  if (!model) return null

  const getModelConfig = (m: string): { label: string; style: React.CSSProperties } => {
    const lower = m.toLowerCase()
    if (lower === 'remoto') return { label: 'Remoto', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--status-success)' } }
    if (lower === 'híbrido') return { label: 'Híbrido', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-cyan-dark)' } }
    if (lower === 'presencial') return { label: 'Presencial', style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-orange)' } }
    return { label: m, style: { color: 'var(--lia-text-primary)' } }
  }

  const config = getModelConfig(model)

  return (
    <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5" style={config.style}>
      {config.label}
    </Chip>
  )
}

export function SelectionCheckbox({ 
  isSelected, 
  onToggle 
}: { 
  isSelected: boolean
  onToggle: () => void 
}) {
  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        onToggle()
      }}
      className="cursor-pointer flex items-center justify-center"
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={() => {}}
        className="w-4 h-4 rounded-md"
      />
    </div>
  )
}

export function NoteCell({
  hasNote,
  onViewNote
}: {
  hasNote: boolean
  onViewNote?: (e: React.MouseEvent) => void
}) {
  if (!hasNote) return null

  return (
    <Button
      variant="ghost"
      size="sm"
      className="h-6 w-6 p-0 hover:bg-status-warning/15 dark:hover:bg-status-warning/20"
      onClick={(e) => {
        e.stopPropagation()
        onViewNote?.(e)
      }}
      title="Ver nota"
    >
      <StickyNote className="w-3.5 h-3.5 text-status-warning" />
    </Button>
  )
}

// Helper to get sub-status color based on properties
function getSubStatusColors(status?: SubStatus): { bg: string; text: string; bgStyle: string; textStyle: string } {
  if (!status) return { bg: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary', bgStyle: 'var(--lia-border-subtle)', textStyle: 'var(--lia-text-tertiary)' }
 if (status.isApproval) return { bg: 'bg-lia-bg-tertiary', text: 'text-lia-text-primary', bgStyle: 'var(--wedo-cyan-bg-15)', textStyle: 'var(--lia-text-secondary)' }
  if (status.isRejection) return { bg: 'bg-status-error/15 dark:bg-status-error/30', text: 'text-status-error dark:text-status-error', bgStyle: 'var(--status-error-bg-15)', textStyle: 'var(--status-error)' }
  if (status.isWaiting) return { bg: 'bg-status-warning/15 dark:bg-status-warning/30', text: 'text-status-warning dark:text-status-warning', bgStyle: 'var(--status-warning-bg-15)', textStyle: 'var(--status-warning)' }
  return { bg: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary', bgStyle: 'var(--lia-bg-tertiary)', textStyle: 'var(--lia-text-tertiary)' }
}

export function SubStatusCell({ stage, subStatus }: { stage?: string; subStatus?: string }) {
  // WT-2022 P0.SUB_STATUSES: hook canonical-first ANTES de qualquer early return
  // (Rules of Hooks). Fallback hardcoded preserva back-compat enquanto boot.
  const { legacySubStatuses } = useRecruitmentStages()

  if (!subStatus || !stage) return null

  const displayName = getSubStatusDisplayName(stage, subStatus)
  const subStatuses = legacySubStatuses[stage] ?? SUB_STATUSES[stage] ?? []
  const subStatusMetadata = subStatuses.find(s => s.name === subStatus)
  const colors = getSubStatusColors(subStatusMetadata)

  return (
    <Chip variant="neutral" muted 
      className="text-micro px-1.5 py-0.5" 
      style={{backgroundColor: colors.bgStyle, color: colors.textStyle}}
    >
      {displayName}
    </Chip>
  )
}

// Interactive SubStatusCell with dropdown for changing sub-status
export function InteractiveSubStatusCell({ 
  candidateId,
  candidateName,
  stage, 
  subStatus,
  jobVacancyId,
  onStatusChange
}: { 
  candidateId: string
  candidateName?: string
  stage?: string
  subStatus?: string
  jobVacancyId?: string
  onStatusChange?: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean | void>
}) {
  // WT-2022 P0.SUB_STATUSES: hooks SEMPRE no topo (Rules of Hooks). Mesmo
  // padrao do SubStatusCell — hook canonical-first com fallback hardcoded.
  const [open, setOpen] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const { legacySubStatuses } = useRecruitmentStages()

  if (!stage) return null

  const displayName = subStatus ? getSubStatusDisplayName(stage, subStatus) : 'Sem status'
  const availableSubStatuses = legacySubStatuses[stage] ?? SUB_STATUSES[stage] ?? []
  const currentMetadata = availableSubStatuses.find(s => s.name === subStatus)
  const colors = getSubStatusColors(currentMetadata)

  const handleStatusChange = async (newSubStatus: string) => {
    if (newSubStatus === subStatus || !onStatusChange) return
    
    setIsUpdating(true)
    try {
      await onStatusChange(candidateId, newSubStatus, stage, jobVacancyId)
      
      const newStatusName = availableSubStatuses.find(s => s.name === newSubStatus)?.displayName || newSubStatus
      toast.success(`Status atualizado para"${newStatusName}"`, {
        description: `${candidateName || 'Candidato'} movido com sucesso`,
      })
      setOpen(false)
    } catch (error) {
      toast.error('Erro ao atualizar status', {
        description: 'Não foi possível atualizar o status do candidato. Tente novamente.',
      })
    } finally {
      setIsUpdating(false)
    }
  }

  if (!onStatusChange || availableSubStatuses.length === 0) {
    return <SubStatusCell stage={stage} subStatus={subStatus} />
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1 hover:opacity-80 transition-opacity motion-reduce:transition-none cursor-pointer"
          disabled={isUpdating}
        >
          <Chip variant="neutral" muted 
            className="text-micro px-1.5 py-0.5 flex items-center gap-0.5" 
            style={{backgroundColor: colors.bgStyle, color: colors.textStyle}}
          >
            {isUpdating ? 'Atualizando...' : displayName}
            <ChevronDown className="w-2.5 h-2.5" />
          </Chip>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="start" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
        <div className="text-xs font-medium text-lia-text-tertiary mb-2 px-1">
          Alterar status
        </div>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {availableSubStatuses.map((status) => {
            const statusColors = getSubStatusColors(status)
            const isSelected = status.name === subStatus
            return (
              <button
                key={status.name}
                onClick={() => handleStatusChange(status.name)}
                className={`w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors motion-reduce:transition-none ${
 isSelected 
                    ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary' 
                    : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50'
                }`}
              >
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium ${statusColors.bg} ${statusColors.text}`}>
                  {status.displayName}
                </span>
              </button>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}

interface InteractiveStageCellProps {
  candidateId: string
  candidateName?: string
  candidateRole?: string
  candidateAvatar?: string
  candidateEmail?: string
  candidatePhone?: string
  currentStage?: string
  onStageChange?: (candidateId: string, newStage: string, subStatus?: string, jobVacancyId?: string) => Promise<boolean | void>
  onTransitionRequest?: (candidate: {
    id: string
    name: string
    email?: string
    phone?: string
    avatar?: string
    currentTitle?: string
  }, fromStage: string, toStage: string) => void
}

export function InteractiveStageCell({
  candidateId,
  candidateName,
  candidateRole,
  candidateAvatar,
  candidateEmail,
  candidatePhone,
  currentStage,
  onStageChange,
  onTransitionRequest
}: InteractiveStageCellProps) {
  const [open, setOpen] = useState(false)
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('interactive-stage', open)
  const [selectedStage, setSelectedStage] = useState<string>('')

  // WT-2022 P0.STAGES: hook canonical com fallback transitional ao RECRUITMENT_STAGES estatico
  const { legacyStages } = useRecruitmentStages()
  const stages = legacyStages.length > 0 ? legacyStages : RECRUITMENT_STAGES

  const currentStageInfo = stages.find(s => s.name === currentStage)
  const stageDisplayName = currentStageInfo?.displayName || currentStage || 'Sem etapa'
  
  const finalStages = ['hired', 'rejected', 'offer_declined']
  const activeStages = stages.filter(s => s.stageType !== 'standby' && s.stageType !== 'final')

  const handleConfirm = () => {
    if (!selectedStage) return
    
    setOpen(false)
    
    if (onTransitionRequest) {
      onTransitionRequest(
        {
          id: candidateId,
          name: candidateName || 'Candidato',
          email: candidateEmail,
          phone: candidatePhone,
          avatar: candidateAvatar,
          currentTitle: candidateRole,
        },
        currentStage || '',
        selectedStage
      )
    }
    
    setSelectedStage('')
  }

  if (!onStageChange && !onTransitionRequest) {
    return (
      <Chip variant="neutral" muted 
        className="text-micro px-1.5 py-0.5 font-medium"
        style={{backgroundColor: currentStageInfo?.color || 'var(--lia-border-subtle)'}}
      >
        {stageDisplayName}
      </Chip>
    )
  }

  return (
    <>
      <button
        onClick={(e) => {
          e.stopPropagation()
          setOpen(true)
        }}
        className="hover:opacity-80 transition-opacity motion-reduce:transition-none cursor-pointer"
      >
        <Chip variant="neutral" muted 
          className="text-micro px-1.5 py-0.5 flex items-center gap-0.5 font-medium"
          style={{backgroundColor: currentStageInfo?.color || 'var(--lia-border-subtle)'}}
        >
          {stageDisplayName}
          <ChevronDown className="w-2.5 h-2.5" />
        </Chip>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-md" onClick={(e) => e.stopPropagation()}>
          <DialogHeader className="px-6 py-4 dark:border-lia-border-subtle">
            <DialogTitle className="flex items-center gap-3 text-base font-semibold text-lia-text-primary">
              <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                <ArrowRight className="w-5 h-5 text-lia-text-secondary" />
              </div>
              Mover Candidato
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-5 py-3">
            {candidateName && (
              <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle">
                {candidateAvatar && (
                  <NextImage src={candidateAvatar} alt={candidateName} width={40} height={40} className="w-10 h-10 rounded-full" />
                )}
                <div>
                  <span className="text-base-ui font-medium text-lia-text-primary block">{candidateName}</span>
                  {candidateRole && (
                    <span className="text-xs text-lia-text-secondary">{candidateRole}</span>
                  )}
                </div>
              </div>
            )}

            <div className="flex items-center gap-3 justify-center text-sm">
              <span className="px-3 py-1.5 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full text-lia-text-secondary text-xs font-medium">
                {stageDisplayName}
              </span>
              <ArrowRight className="w-4 h-4 text-lia-text-secondary" />
 <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${selectedStage ? 'dark:text-lia-text-tertiary border border-lia-border-default dark:border-lia-border-default' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                {selectedStage ? (stages.find(s => s.name === selectedStage)?.displayName || selectedStage) : 'Selecione'}
              </span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-lia-text-primary">
                Nova Etapa
              </label>
              <Select value={selectedStage} onValueChange={setSelectedStage}>
                <SelectTrigger className="text-xs">
                  <SelectValue placeholder="Selecione a etapa" />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  <div className="px-2 py-1 text-xs font-semibold text-lia-text-secondary">Etapas Ativas</div>
                  {activeStages.map(stage => (
                    <SelectItem key={stage.name} value={stage.name} disabled={stage.name === currentStage}>
                      {stage.displayName}
                    </SelectItem>
                  ))}
                  <div className="px-2 py-1 text-xs font-semibold text-lia-text-secondary mt-2">Etapas Finais</div>
                  {finalStages.map(stageName => {
                    const stage = stages.find(s => s.name === stageName)
                    return (
                      <SelectItem key={stageName} value={stageName}>
                        {stage?.displayName || stageName}
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button 
                variant="outline" 
                className="flex-1 text-xs font-semibold rounded-xl transition-colors motion-reduce:transition-none duration-150 bg-lia-bg-primary text-lia-text-primary border border-lia-border-default hover:bg-lia-bg-secondary hover:border-lia-border-medium dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
                onClick={() => {
                  setOpen(false)
                  setSelectedStage('')
                }}
              >
                Cancelar
              </Button>
              <Button 
                className="flex-1 text-xs font-semibold rounded-xl transition-colors motion-reduce:transition-none duration-150 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover active:bg-lia-bg-inverse dark:hover:bg-lia-interactive-active"
                disabled={!selectedStage}
                onClick={handleConfirm}
              >
                Continuar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

// Simple stage display cell (non-interactive)
export function StageCell({ stage }: { stage?: string }) {
  // WT-2022 P0.STAGES: hook canonical no TOPO (Rules-of-Hooks) antes do early return
  const { legacyStages } = useRecruitmentStages()
  const stages = legacyStages.length > 0 ? legacyStages : RECRUITMENT_STAGES

  if (!stage) return null
  
  const stageInfo = stages.find(s => s.name === stage)
  const displayName = stageInfo?.displayName || stage
  
  return (
    <Chip variant="neutral" muted 
      className="text-micro px-1.5 py-0.5"
      style={{backgroundColor: stageInfo?.color || 'var(--lia-text-tertiary)', color: 'var(--lia-bg-secondary)'}}
    >
      {displayName}
    </Chip>
  )
}

export function ActionButtons({
  isPinned,
  isFavorite,
  needsAction = false,
  onTogglePin,
  onToggleFavorite,
  children
}: {
  isPinned?: boolean
  isFavorite?: boolean
  needsAction?: boolean
  onTogglePin?: () => void
  onToggleFavorite?: () => void
  children?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-end gap-1 relative" onClick={(e) => e.stopPropagation()}>
      {/* Indicador"Ação Necessária" - visível fora do hover, escondido no hover */}
      {needsAction && (
        <div className="absolute inset-0 flex items-center justify-end pr-1 group-hover:opacity-0 group-hover:pointer-events-none transition-opacity motion-reduce:transition-none duration-200">
          <div 
            className="flex items-center gap-1 px-2 py-1 rounded-full bg-lia-btn-primary-hover/[.08]"
          >
            <Zap className="w-3 h-3 text-lia-text-primary animate-pulse motion-reduce:animate-none" />
            <span className="text-micro font-semibold text-lia-text-primary">
              Ação Necessária
            </span>
          </div>
        </div>
      )}

      {/* Botões de ação - escondidos fora do hover, visíveis no hover */}
      <div className={`flex items-center gap-1 ${needsAction ? 'opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none duration-200' : ''}`}>
        {onToggleFavorite && (
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-wedo-orange/15 dark:hover:bg-wedo-orange/10/20 ${
 isFavorite ? 'text-wedo-orange-text' : 'text-lia-text-secondary'
            }`}
            onClick={onToggleFavorite}
            title={isFavorite ?"Remover dos favoritos" :"Adicionar aos favoritos"}
          >
            <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-current' : ''}`} />
          </Button>
        )}

        {onTogglePin && (
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-wedo-cyan/15 dark:hover:bg-wedo-cyan/10/20 ${
 isPinned ? 'text-lia-text-secondary' : 'text-lia-text-secondary'
            }`}
            onClick={onTogglePin}
            title={isPinned ?"Desafixar" :"Fixar"}
          >
            <Pin className={`w-3.5 h-3.5 ${isPinned ? 'fill-current' : ''}`} />
          </Button>
        )}

        {children}
      </div>
    </div>
  )
}
