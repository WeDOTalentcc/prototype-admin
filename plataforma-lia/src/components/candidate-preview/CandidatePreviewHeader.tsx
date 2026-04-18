"use client"

import { textStyles, badgeStyles } from '@/lib/design-tokens'
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { CandidateAvatar } from"@/components/candidate-profile/CandidateAvatar"
import {
  X, Calendar, MessageSquare, Clock, Brain, CheckCircle, AlertCircle, Expand
} from"lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"
import dynamic from"next/dynamic"
import type { CandidateData } from"./ProfileTabTypes"

const LiaAnalysisModal = dynamic(() => import("@/components/modals/lia-analysis-modal").then(m => ({ default: m.LiaAnalysisModal })), { ssr: false })

interface CandidatePreviewHeaderProps {
  c: CandidateData
  candidate: Record<string, unknown>
  generateShortId: (name: string, id?: string) => string
  showLiaAnalysisModal: boolean
  setShowLiaAnalysisModal: (v: boolean) => void
  handleAnalysisTransport: (analysis: { type: string; content: string; candidate_id: string }) => void
  onOpenFullPage?: (candidate: Record<string, unknown>) => void
  onClose: () => void
}

export function CandidatePreviewHeader({
  c,
  candidate,
  generateShortId,
  showLiaAnalysisModal,
  setShowLiaAnalysisModal,
  handleAnalysisTransport,
  onOpenFullPage,
  onClose,
}: CandidatePreviewHeaderProps) {
  const formatDate = (dateStr: string | Date | null | undefined): string => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr as string | number)
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return ''
    }
  }

  const lastContactedAt = c.last_contacted_at || c.lastContactedAt
  const updatedAt = c.updated_at || c.updatedAt
  const createdAt = c.created_at || c.createdAt

  return (
    <>
      <div className="flex items-start gap-3 mb-1.5">
        <CandidateAvatar
          name={c.name as string}
          avatarUrl={(c.avatar_url as string | undefined) || (c.avatar as string | undefined) || (c.photo_url as string | undefined) || (c.photoUrl as string | undefined)}
          size="lg"
          showRing
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
            <h3 className={`${textStyles.title} truncate`}>
              {c.name as string}
            </h3>
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default">
              {generateShortId(c.name as string, (c.id as string | undefined) || (c.candidateId as string | undefined) || (c.pearch_id as string | undefined))}
            </Chip>
            {(c.seniority_level || c.seniorityLevel) && (
              <Chip variant="neutral" muted className={badgeStyles.warning}>
                {(c.seniority_level as string | undefined) || (c.seniorityLevel as string | undefined)}
              </Chip>
            )}
            {(c.years_of_experience !== undefined && c.years_of_experience !== null) || 
             (c.yearsOfExperience !== undefined && c.yearsOfExperience !== null) ? (
              <Chip variant="neutral" muted className={badgeStyles.default}>
                {typeof (c.years_of_experience || c.yearsOfExperience) === 'number' 
                  ? `${((c.years_of_experience as number | undefined) || (c.yearsOfExperience as number | undefined) || 0).toFixed(1)} anos` 
                  : `${c.years_of_experience || c.yearsOfExperience} anos`}
              </Chip>
            ) : null}
            {(c.communication_consent !== undefined || c.communicationConsent !== undefined) && (
              <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 ${(c.communication_consent ?? c.communicationConsent) ? '' : ''}`}>
                {(c.communication_consent ?? c.communicationConsent) ? <CheckCircle className="w-2.5 h-2.5" /> : <AlertCircle className="w-2.5 h-2.5" />}
                LGPD
              </Chip>
            )}
            {c.is_enriching && (
              <Chip variant="warning" muted className="text-micro px-1.5 py-0 h-4 flex items-center gap-0.5 bg-status-warning/15 animate-pulse">
                Enriquecendo...
              </Chip>
            )}
            {c.enrichment_source && !c.is_enriching && (() => {
              const src = String(c.enrichment_source).toLowerCase()
              const config = src === 'apify'
                ? { label: 'Apify', cls: 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30' }
                : src === 'pearch'
                  ? { label: 'Pearch', cls: 'bg-wedo-cyan/15 text-wedo-cyan border-wedo-cyan/30' }
                  : src === 'local'
                    ? { label: 'Local', cls: 'bg-stone-400/15 text-stone-500 border-stone-400/30' }
                    : { label: String(c.enrichment_source), cls: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default' }
              return (
                <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 h-4 ${config.cls}`}>
                  {config.label}
                </Chip>
              )
            })()}
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <p className={`${textStyles.bodySmall} truncate`}>
              {(c.position || c.title || 'Cargo não informado') as React.ReactNode}
            </p>
            <span className={`${textStyles.bodySmall} text-lia-text-secondary`}>•</span>
            <p className={`${textStyles.bodySmall} truncate`}>
              {(c.workHistory?.[0] as Record<string, unknown> | undefined)?.company as React.ReactNode || c.current_company as React.ReactNode || c.company as React.ReactNode || 'Empresa'}
            </p>
            {((c.workHistory?.[0] as Record<string, unknown> | undefined)?.industry || (c.workHistory?.[0] as Record<string, unknown> | undefined)?.segment || c.company_segment || c.industry) && (
              <>
                <span className={`${textStyles.description} text-lia-text-secondary`}>•</span>
                <p className={`${textStyles.description} truncate`}>
                  {((c.workHistory?.[0] as Record<string, unknown> | undefined)?.industry || (c.workHistory?.[0] as Record<string, unknown> | undefined)?.segment || c.company_segment || c.industry) as React.ReactNode}
                </p>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          <LiaAnalysisModal
            isOpen={showLiaAnalysisModal}
            onOpen={() => setShowLiaAnalysisModal(true)}
            onClose={() => setShowLiaAnalysisModal(false)}
            candidate={c}
            onTransportToOpinions={handleAnalysisTransport}
          >
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary border border-lia-border-default rounded-md flex-shrink-0"
              title="Análises LIA"
            >
              <Brain className="w-5 h-5 text-wedo-cyan" />
            </Button>
          </LiaAnalysisModal>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpenFullPage?.(candidate)}
                className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              >
                <Expand className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-xs">Expandir</TooltipContent>
          </Tooltip>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
          >
            <X className="w-4 h-4 text-lia-text-tertiary" />
          </Button>
        </div>
      </div>

      {(() => {
        if (!createdAt && !updatedAt && !lastContactedAt) return null
        
        return (
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            {!!createdAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                    <Calendar className="w-2.5 h-2.5" />
                    {String(formatDate(createdAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Data de cadastro</TooltipContent>
              </Tooltip>
            )}
            {!!updatedAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-secondary flex items-center gap-0.5 cursor-help">
                    <Clock className="w-2.5 h-2.5" />
                    {String(formatDate(updatedAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Última atualização</TooltipContent>
              </Tooltip>
            )}
            {!!lastContactedAt && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-micro text-lia-text-tertiary flex items-center gap-0.5 cursor-help">
                    <MessageSquare className="w-2.5 h-2.5" />
                    {String(formatDate(lastContactedAt as string | Date | null | undefined) || '')}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Último contato</TooltipContent>
              </Tooltip>
            )}
          </div>
        )
      })()}
    </>
  )
}
