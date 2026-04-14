"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import {
  StatusBadge,
  ChannelBadge,
  SourceBadge,
  WarningBadge,
  DateTimeBadge,
  OriginBadge,
  AwaitingBadge,
} from "@/components/ui/status-badge"
import { AISuggestionBadge } from "@/components/ai"
import { OverrideApproveButton } from "@/components/kanban/components/OverrideApproveButton"
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
  return (
    <>
{/* Tags de Status Compactas */}
<div className="mt-2 flex flex-wrap gap-1">
  {/* AI Suggestion Badge */}
  {(() => {
    const suggestion = getSuggestionForCandidate(aiSuggestions as unknown as import("@/hooks/ai/useCandidateSuggestions").AISuggestion[], String(candidate.id))
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
      <StatusBadge
        stageId={stageId}
        variant="standard"
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
      <StatusBadge
        stageId={stageId}
        variant="accent"
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
          <StatusBadge
            stageId={stageId}
            variant="dark"
            icon={CheckCircle}
            label={t('screeningCompleted')}
          />
          <StatusBadge
            stageId={stageId}
            variant="accent"
            icon={Target}
            label={t('pendingDecision')}
            pulse
            onClick={() => onOpenAnalysis(candidate)}
            title={t('clickToSeeFullAnalysis')}
          />
        </>
      ) : (
        <StatusBadge
          stageId={stageId}
          variant="outlined"
          icon={MessageCircle}
          label={
            candidate.liatriagem === "respondendo"
              ? t('respondingNow')
              : t('conversationInProgress')
          }
        />
      )}
      <ChannelBadge channel={candidate.contactChannelId || "whatsapp"} />
    </>
  )}

  {/* ENTREVISTA */}
  {(stageId === "interview_hr" ||
    stageId === "interview_technical" ||
    stageId === "interview_manager") && (
    <>
      {candidate.agendada ? (
        <>
          <StatusBadge
            stageId={stageId}
            variant="scheduled"
            icon={CalendarCheck}
            label={t('interviewConfirmed')}
          />
          {candidate.interviewDate && (
            <DateTimeBadge date={candidate.interviewDate} />
          )}
          <ChannelBadge channel={candidate.typeOfInterview || "teams"} />
        </>
      ) : (
        <StatusBadge
          stageId={stageId}
          variant="accent"
          icon={Clock}
          label={t('awaitingScheduling')}
          pulse
        />
      )}
      {candidate.interviewCompleted && !candidate.interviewFeedback && (
        <StatusBadge
          stageId={stageId}
          variant="accent"
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
      <StatusBadge stageId={stageId} variant="standard" icon={Star} label={t('finalist')} />
      {candidate.proposal ? (
        <>
          <StatusBadge
            stageId={stageId}
            variant="dark"
            icon={FileText}
            label={t('proposalSent')}
          />
          {!candidate.proposalResponse && (
            <StatusBadge
              stageId={stageId}
              variant="accent"
              icon={Clock}
              label={t('awaitingResponse')}
              pulse
            />
          )}
        </>
      ) : (
        <StatusBadge
          stageId={stageId}
          variant="accent"
          icon={Clock}
          label={t('awaitingApproval')}
          pulse
        />
      )}
      {candidate.negotiating && (
        <StatusBadge
          stageId={stageId}
          variant="outlined"
          icon={MessageCircle}
          label={t('inNegotiation')}
        />
      )}
    </>
  )}

  {/* CONTRATADOS */}
  {stageId === "hired" && (
    <>
      <StatusBadge stageId={stageId} variant="hired" icon={Trophy} label={t('hiredStatus')} />
      {candidate.startDate && (
        <StatusBadge
          stageId={stageId}
          variant="standard"
          icon={Calendar}
          label={t('startDateLabel', { date: new Date(candidate.startDate).toLocaleDateString(locale, {
            day: "2-digit",
            month: "2-digit",
          }) })}
        />
      )}
      {candidate.sub_status && (
        <StatusBadge stageId={stageId} subStatus={candidate.sub_status} />
      )}
    </>
  )}

  {/* REPROVADOS */}
  {stageId === "rejected" && (
    <>
      <StatusBadge
        stageId={stageId}
        variant="rejected"
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
        <StatusBadge
          stageId={stageId}
          variant="dark"
          icon={CheckCircle}
          label={t('feedbackSent')}
        />
      )}
    </>
  )}

  {/* PROPOSTA RECUSADA */}
  {stageId === "offer_declined" && (
    <>
      <StatusBadge
        stageId={stageId}
        variant="rejected"
        icon={XCircle}
        label={t('proposalDeclined')}
      />
      {candidate.feedbackSent && (
        <StatusBadge
          stageId={stageId}
          variant="dark"
          icon={CheckCircle}
          label={t('feedbackSent')}
        />
      )}
    </>
  )}

  {/* Badge de Warning - Dias parado */}
  {(candidate.warning || candidate.warningDays) && (
    <WarningBadge days={candidate.daysPaused} message={candidate.warningDays} />
  )}

  {/* Badge de expectativa salarial */}
  {candidate.expectativa && (
    <StatusBadge
      stageId={stageId}
      variant={
        candidate.expectativa === "no budget"
          ? "dark"
          : candidate.expectativa === "acima do budget"
          ? "outlined"
          : "standard"
      }
      icon={DollarSign}
      label={candidate.expectativa}
    />
  )}

  {/* Badge de Origem */}
  {candidate.origin && <OriginBadge origin={candidate.origin} />}

  {/* Badge Aguardando (fila de saturação) + Override */}
  {(candidate.status === "awaiting_screening" ||
    candidate.sub_status === "awaiting_screening" ||
    candidate.subStatus === "awaiting_screening") && (
    <>
      <AwaitingBadge />
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
  <SourceBadge
    source={candidate.source || "website"}
    isApplication={isApplicationSource(candidate.source || "website")}
  />

  {/* Sub-Status Badge */}
  {candidate.sub_status && !["hired", "rejected", "offer_declined"].includes(stageId) && (
    <StatusBadge stageId={stageId} subStatus={candidate.sub_status} />
  )}
</div>
    </>
  )
}
