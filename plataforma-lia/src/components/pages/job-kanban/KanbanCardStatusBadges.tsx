"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import { KanbanChip, type KanbanChipVariant } from "./KanbanChip"
import { AISuggestionBadge } from "@/components/ai"
import { OverrideApproveButton } from "@/components/kanban/components/OverrideApproveButton"
import { OfferStatusBadgeConnected } from "@/components/offer/OfferStatusBadgeConnected"
import {
  User,
  BrainCircuit,
  CheckCircle,
  Clock,
  MessageCircle,
  Target,
  CalendarCheck,
  Star,
  FileText,
  Trophy,
  XCircle,
  Calendar,
  DollarSign,
  AlertCircle,
  Linkedin,
  Globe,
  Mail,
  Phone,
  MessageSquare,
  Video,
  Building,
  Users,
  Briefcase,
  Search,
} from "lucide-react"
import { isApplicationSource } from "@/lib/recruitment-stages"
import { getSuggestionForCandidate } from "@/hooks/ai/useCandidateSuggestions"

type AISuggestion = {
  id: string
  candidate_id?: string
  suggested_action?: string
  confidence?: number
  [key: string]: unknown
}

type CandidatesData = Record<string, unknown[]>

interface KanbanCardStatusBadgesProps {
  candidate: {
    id: string
    name: string
    status?: string
    sub_status?: string
    subStatus?: string
    source?: string
    origin?: string
    liatriagem?: string
    contactChannelId?: string
    agendada?: string | boolean
    interviewDate?: string
    typeOfInterview?: string
    interviewCompleted?: boolean
    interviewFeedback?: unknown
    proposal?: unknown
    proposalResponse?: unknown
    negotiating?: boolean
    startDate?: string
    rejectionReason?: string
    rejectionStage?: string
    feedbackSent?: boolean
    warning?: boolean
    warningDays?: string
    daysPaused?: number
    expectativa?: string
    needsAction?: boolean
    [key: string]: unknown
  }
  stageId: string
  aiSuggestions: AISuggestion[]
  currentJob: { id?: string | number; backendId?: string | number; [key: string]: unknown }
  setCandidatesData: (value: CandidatesData | ((prev: CandidatesData) => CandidatesData)) => void
  onOpenAnalysis: (candidate: unknown) => void
  approveSuggestion: (suggestionId: string) => void
  rejectSuggestion: (suggestionId: string) => void
}

const channelIcons: Record<string, React.ElementType> = {
  whatsapp: MessageSquare,
  email: Mail,
  phone: Phone,
  linkedin: Linkedin,
  teams: Video,
  presencial: Building,
}

const channelLabels: Record<string, string> = {
  whatsapp: "WhatsApp",
  email: "Email",
  phone: "Telefone",
  linkedin: "LinkedIn",
  teams: "Teams",
  presencial: "Presencial",
}

const sourceIcons: Record<string, React.ElementType> = {
  linkedin: Linkedin,
  indeed: Briefcase,
  google_jobs: Search,
  website: Globe,
  referral: Users,
  headhunting: Target,
  internal: Building,
  lia_database: BrainCircuit,
  recruiter: User,
  pearch: Globe,
}

const sourceLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  indeed: "Indeed",
  google_jobs: "Google Jobs",
  website: "Site",
  referral: "Indicação",
  headhunting: "Hunting",
  internal: "Interno",
  lia_database: "Base Interna",
  recruiter: "Manual",
  pearch: "Banco Global",
}

const originIcons: Record<string, React.ElementType> = {
  web: Globe,
  whatsapp: MessageCircle,
  sourcing: Search,
  ats: Briefcase,
}

const originLabels: Record<string, string> = {
  web: "Web",
  whatsapp: "WhatsApp",
  sourcing: "Busca",
  ats: "ATS",
}

interface CandidateChipProps {
  variant?: KanbanChipVariant
  icon: React.ElementType
  label: React.ReactNode
  pulse?: boolean
  onClick?: () => void
  title?: string
  className?: string
}

function CandidateChip({
  variant = "neutral",
  icon: Icon,
  label,
  pulse,
  onClick,
  title,
  className,
}: CandidateChipProps) {
  return (
    <KanbanChip
      density="compact"
      variant={variant}
      title={title}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      aria-label={onClick ? title || (typeof label === "string" ? label : undefined) : undefined}
      className={[
        pulse ? "motion-safe:animate-pulse motion-reduce:animate-none" : "",
        onClick ? "cursor-pointer hover:opacity-80" : "",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Icon className="w-2 h-2 flex-shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </KanbanChip>
  )
}

export function KanbanCardStatusBadges({
  candidate,
  stageId,
  aiSuggestions,
  currentJob,
  setCandidatesData,
  onOpenAnalysis,
  approveSuggestion,
  rejectSuggestion,
}: KanbanCardStatusBadgesProps) {
  const t = useTranslations('kanban')
  const locale = useLocale()

  const channelKey = (candidate.contactChannelId || "whatsapp").toLowerCase()
  const ChannelIcon = channelIcons[channelKey] || MessageSquare
  const channelLabel = channelLabels[channelKey] || candidate.contactChannelId || "WhatsApp"

  const interviewChannelKey = (candidate.typeOfInterview || "teams").toLowerCase()
  const InterviewChannelIcon = channelIcons[interviewChannelKey] || MessageSquare
  const interviewChannelLabel =
    channelLabels[interviewChannelKey] || candidate.typeOfInterview || "Teams"

  const sourceKey = (candidate.source || "website").toLowerCase()
  const SourceIcon = sourceIcons[sourceKey] || User
  const baseSourceLabel = sourceLabels[sourceKey] || candidate.source || "Site"
  const isApplication = isApplicationSource(candidate.source || "website")
  const sourceLabel = isApplication ? `Inscrito ${baseSourceLabel}` : baseSourceLabel
  const sourceTitle = isApplication
    ? `Inscrito via ${baseSourceLabel}`
    : `Origem: ${baseSourceLabel}`

  const originKey = (candidate.origin || "").toLowerCase()
  const OriginIcon = originIcons[originKey] || Search
  const originLabel = originLabels[originKey] || candidate.origin || "Busca"

  const formatDateTime = (date: string) => {
    const d = new Date(date)
    const day = d.getDate().toString().padStart(2, "0")
    const month = (d.getMonth() + 1).toString().padStart(2, "0")
    const hours = d.getHours().toString().padStart(2, "0")
    const minutes = d.getMinutes().toString().padStart(2, "0")
    return `${day}/${month} às ${hours}:${minutes}`
  }

  return (
    <>
      {/* Tags de Status Compactas */}
      <div className="mt-2 flex flex-wrap gap-1">
        {/* AI Suggestion Badge */}
        {(() => {
          const suggestion = getSuggestionForCandidate(
            aiSuggestions as unknown as import("@/hooks/ai/useCandidateSuggestions").AISuggestion[],
            String(candidate.id),
          )
          if (suggestion) {
            return (
              <div onClick={(e) => e.stopPropagation()}>
                <AISuggestionBadge
                  suggestion={suggestion}
                  onApprove={(id) => Promise.resolve(approveSuggestion(id))}
                  onReject={(id) => Promise.resolve(rejectSuggestion(id))}
                  compact
                />
              </div>
            )
          }
          return null
        })()}

        {/* FUNIL - Candidatos sem triagem ainda */}
        {stageId === "sourcing" && (
          <>
            <CandidateChip
              variant="neutral"
              icon={User}
              label={
                candidate.source === "linkedin"
                  ? t('appliedViaLinkedin')
                  : candidate.source === "website"
                  ? t('appliedOnWebsite')
                  : candidate.source === "lia_database"
                  ? t('mappedByLIA')
                  : t('addedManually')
              }
            />
            <CandidateChip
              variant="info"
              icon={BrainCircuit}
              label={t('liaWillStartScreening')}
              pulse
            />
          </>
        )}

        {/* TRIAGEM - Candidatos em contato com LIA */}
        {stageId === "screening" && (
          <>
            {candidate.needsAction || candidate.status === "triado_aprovado" ? (
              <>
                <CandidateChip
                  variant="neutral"
                  icon={CheckCircle}
                  label={t('screeningCompleted')}
                />
                <CandidateChip
                  variant="info"
                  icon={Target}
                  label={t('pendingDecision')}
                  pulse
                  onClick={() => onOpenAnalysis(candidate)}
                  title={t('clickToSeeFullAnalysis')}
                />
              </>
            ) : (
              <CandidateChip
                variant="neutral"
                icon={MessageCircle}
                label={
                  candidate.liatriagem === "respondendo"
                    ? t('respondingNow')
                    : t('conversationInProgress')
                }
              />
            )}
            <CandidateChip variant="neutral" icon={ChannelIcon} label={channelLabel} />
          </>
        )}

        {/* ENTREVISTA */}
        {(stageId === "interview_hr" ||
          stageId === "interview_technical" ||
          stageId === "interview_manager") && (
          <>
            {candidate.agendada ? (
              <>
                <CandidateChip
                  variant="success"
                  icon={CalendarCheck}
                  label={t('interviewConfirmed')}
                />
                {candidate.interviewDate && (
                  <CandidateChip
                    variant="neutral"
                    icon={Calendar}
                    label={formatDateTime(candidate.interviewDate)}
                  />
                )}
                <CandidateChip
                  variant="neutral"
                  icon={InterviewChannelIcon}
                  label={interviewChannelLabel}
                />
              </>
            ) : (
              <CandidateChip
                variant="info"
                icon={Clock}
                label={t('awaitingScheduling')}
                pulse
              />
            )}
            {candidate.interviewCompleted && !candidate.interviewFeedback && (
              <CandidateChip
                variant="info"
                icon={Clock}
                label={t('pendingFeedback')}
                pulse
              />
            )}
          </>
        )}

        {/* FINAL */}
        {stageId === "offer" && (
          <>
            <CandidateChip variant="neutral" icon={Star} label={t('finalist')} />
            {candidate.proposal ? (
              <>
                <CandidateChip
                  variant="neutral"
                  icon={FileText}
                  label={t('proposalSent')}
                />
                {!candidate.proposalResponse && (
                  <CandidateChip
                    variant="info"
                    icon={Clock}
                    label={t('awaitingResponse')}
                    pulse
                  />
                )}
              </>
            ) : (
              <CandidateChip
                variant="info"
                icon={Clock}
                label={t('awaitingApproval')}
                pulse
              />
            )}
            {candidate.negotiating && (
              <CandidateChip
                variant="neutral"
                icon={MessageCircle}
                label={t('inNegotiation')}
              />
            )}
            <OfferStatusBadgeConnected candidateId={candidate.id} />
          </>
        )}

        {/* CONTRATADOS */}
        {stageId === "hired" && (
          <>
            <CandidateChip variant="success" icon={Trophy} label={t('hiredStatus')} />
            {candidate.startDate && (
              <CandidateChip
                variant="neutral"
                icon={Calendar}
                label={t('startDateLabel', {
                  date: new Date(candidate.startDate).toLocaleDateString(locale, {
                    day: "2-digit",
                    month: "2-digit",
                  }),
                })}
              />
            )}
            {candidate.sub_status && (
              <CandidateChip variant="neutral" icon={FileText} label={candidate.sub_status} />
            )}
          </>
        )}

        {/* REPROVADOS */}
        {stageId === "rejected" && (
          <>
            <CandidateChip
              variant="danger"
              icon={XCircle}
              label={
                candidate.rejectionReason === "withdrew"
                  ? t('withdrew')
                  : candidate.rejectionStage === "screening"
                  ? t('rejectedScreening')
                  : candidate.rejectionStage === "interview"
                  ? t('rejectedInterview')
                  : t('rejectedStatus')
              }
            />
            {candidate.feedbackSent && (
              <CandidateChip
                variant="neutral"
                icon={CheckCircle}
                label={t('feedbackSent')}
              />
            )}
          </>
        )}

        {/* PROPOSTA RECUSADA */}
        {stageId === "offer_declined" && (
          <>
            <CandidateChip
              variant="danger"
              icon={XCircle}
              label={t('proposalDeclined')}
            />
            {candidate.feedbackSent && (
              <CandidateChip
                variant="neutral"
                icon={CheckCircle}
                label={t('feedbackSent')}
              />
            )}
          </>
        )}

        {/* Badge de Warning - Dias parado */}
        {(candidate.warning || candidate.warningDays) && (
          <CandidateChip
            variant="warning"
            icon={AlertCircle}
            label={
              candidate.warningDays ||
              (candidate.daysPaused ? `${candidate.daysPaused} dias parado` : "Atenção")
            }
          />
        )}

        {/* Badge de expectativa salarial */}
        {candidate.expectativa && (
          <CandidateChip
            variant={
              candidate.expectativa === "no budget"
                ? "neutral"
                : candidate.expectativa === "acima do budget"
                ? "warning"
                : "neutral"
            }
            icon={DollarSign}
            label={candidate.expectativa}
          />
        )}

        {/* Badge de Origem */}
        {candidate.origin && (
          <CandidateChip
            variant="neutral"
            icon={OriginIcon}
            label={originLabel}
            title={`Origem: ${originLabel}`}
          />
        )}

        {/* Badge Aguardando (fila de saturação) + Override */}
        {(candidate.status === "awaiting_screening" ||
          candidate.sub_status === "awaiting_screening" ||
          candidate.subStatus === "awaiting_screening") && (
          <>
            <CandidateChip
              variant="warning"
              icon={Clock}
              label="Aguardando"
              title="Aguardando na fila de saturação"
            />
            {(currentJob?.backendId || currentJob?.id) && (
              <OverrideApproveButton
                candidateId={candidate.id}
                candidateName={candidate.name}
                vacancyId={String(currentJob.backendId || currentJob.id)}
                onApproved={(cId: string) => {
                  setCandidatesData((prev) => {
                    const updated = { ...prev }
                    Object.keys(updated).forEach((key) => {
                      updated[key] = updated[key].map((c) => {
                        const cObj = c as Record<string, unknown>
                        return String(cObj.id) === cId
                          ? { ...cObj, status: "triado_aprovado" as const, sub_status: undefined, subStatus: undefined }
                          : c
                      })
                    })
                    return updated
                  })
                }}
              />
            )}
          </>
        )}

        {/* Tag de Origem */}
        <CandidateChip
          variant="neutral"
          icon={SourceIcon}
          label={sourceLabel}
          title={sourceTitle}
        />

        {/* Sub-Status Badge */}
        {candidate.sub_status && !["hired", "rejected", "offer_declined"].includes(stageId) && (
          <CandidateChip variant="neutral" icon={FileText} label={candidate.sub_status} />
        )}
      </div>
    </>
  )
}
