// @ts-nocheck
"use client"

import React from "react"
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
import { getSuggestionForCandidate } from "@/hooks/useCandidateSuggestions"

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
  return (
{/* Tags de Status Compactas */}
<div className="mt-2 flex flex-wrap gap-1">
  {/* AI Suggestion Badge */}
  {(() => {
    const suggestion = getSuggestionForCandidate(aiSuggestions, candidate.id)
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
            ? "Aplicou via LinkedIn"
            : candidate.source === "website"
            ? "Aplicou no site"
            : candidate.source === "lia_database"
            ? "Mapeado pela LIA"
            : "Adicionado manual"
        }
      />
      <StatusBadge
        stageId={stageId}
        variant="accent"
        icon={BrainCircuit}
        label="LIA iniciará triagem"
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
            label="Triagem concluída"
          />
          <StatusBadge
            stageId={stageId}
            variant="accent"
            icon={Target}
            label="Decisão pendente"
            pulse
            onClick={() => onOpenAnalysis(candidate)}
            title="Clique para ver análise completa"
          />
        </>
      ) : (
        <StatusBadge
          stageId={stageId}
          variant="outlined"
          icon={MessageCircle}
          label={
            candidate.liatriagem === "respondendo"
              ? "Respondendo agora"
              : "Conversa em andamento"
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
            label="Entrevista confirmada"
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
          label="Aguardando agendamento"
          pulse
        />
      )}
      {candidate.interviewCompleted && !candidate.interviewFeedback && (
        <StatusBadge
          stageId={stageId}
          variant="accent"
          icon={Clock}
          label="Feedback pendente"
          pulse
        />
      )}
    </>
  )}

  {/* FINAL */}
  {stageId === "offer" && (
    <>
      <StatusBadge stageId={stageId} variant="standard" icon={Star} label="Finalista" />
      {candidate.proposal ? (
        <>
          <StatusBadge
            stageId={stageId}
            variant="dark"
            icon={FileText}
            label="Proposta enviada"
          />
          {!candidate.proposalResponse && (
            <StatusBadge
              stageId={stageId}
              variant="accent"
              icon={Clock}
              label="Aguardando resposta"
              pulse
            />
          )}
        </>
      ) : (
        <StatusBadge
          stageId={stageId}
          variant="accent"
          icon={Clock}
          label="Aguardando aprovação"
          pulse
        />
      )}
      {candidate.negotiating && (
        <StatusBadge
          stageId={stageId}
          variant="outlined"
          icon={MessageCircle}
          label="Em negociação"
        />
      )}
    </>
  )}

  {/* CONTRATADOS */}
  {stageId === "hired" && (
    <>
      <StatusBadge stageId={stageId} variant="hired" icon={Trophy} label="Contratado" />
      {candidate.startDate && (
        <StatusBadge
          stageId={stageId}
          variant="standard"
          icon={Calendar}
          label={`Início: ${new Date(candidate.startDate).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
          })}`}
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
            ? "Desistiu"
            : candidate.rejectionStage === "screening"
            ? "Reprovado triagem"
            : candidate.rejectionStage === "interview"
            ? "Reprovado entrevista"
            : "Reprovado"
        }
      />
      {candidate.feedbackSent && (
        <StatusBadge
          stageId={stageId}
          variant="dark"
          icon={CheckCircle}
          label="Feedback enviado"
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
        label="Proposta recusada"
      />
      {candidate.feedbackSent && (
        <StatusBadge
          stageId={stageId}
          variant="dark"
          icon={CheckCircle}
          label="Feedback enviado"
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
          vacancyId={(currentJob.backendId || currentJob.id).toString()}
          onApproved={(cId: string) => {
            setCandidatesData((prev) => {
              const updated = { ...prev }
              Object.keys(updated).forEach((key) => {
                updated[key] = updated[key].map((c) =>
                  c.id === cId
                    ? { ...c, status: "triado_aprovado", sub_status: undefined, subStatus: undefined }
                    : c
                )
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
            </div>

  )
}
