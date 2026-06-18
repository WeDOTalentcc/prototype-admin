"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Button } from "@/components/ui/button"
import {
  CheckCircle2, XCircle, ChevronDown, ChevronRight,
  Loader2, Video, RotateCcw, ArrowRight, Brain,
} from "lucide-react"
import { toast } from "sonner"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { useAuthenticatedUserId } from "@/hooks/shared/use-authenticated-user-id"
import type { CandidateData } from "./ProfileTabTypes"

interface StageInfo {
  name: string
  display_name: string
  stage_order: number
  color: string
  action_behavior: string
  is_rejection?: boolean
  is_hired?: boolean
  sub_statuses?: Array<{ name: string; display_name: string }>
}

interface InterviewData {
  interview_id: string
  meeting_url: string | null
  status: string
}

interface PipelineDecisionBarProps {
  candidate: CandidateData
  jobId?: string
  onCandidateUpdated?: () => void
}

export function PipelineDecisionBar({
  candidate,
  jobId,
  onCandidateUpdated,
}: PipelineDecisionBarProps) {
  const { companyId } = useCurrentCompany()
  const { userId } = useAuthenticatedUserId()

  const [pipeline, setPipeline] = useState<StageInfo[]>([])
  const [currentStage, setCurrentStage] = useState<string>("")
  const [currentSubStatus, setCurrentSubStatus] = useState<string>("")
  const [showMoveDropdown, setShowMoveDropdown] = useState(false)
  const [hoveredStageIdx, setHoveredStageIdx] = useState<number | null>(null)
  const [confirmingReject, setConfirmingReject] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [interviewData, setInterviewData] = useState<InterviewData | null>(null)
  const [highlight, setHighlight] = useState<{ summary: string; strengths: string[] } | null>(null)
  const flyoutRef = useRef<HTMLDivElement>(null)

  const c = candidate as Record<string, unknown>
  const candidateId = (candidate.id || candidate.candidateId || c.pearch_id) as string | undefined
  const vacancyCandidateId = c.vacancy_candidate_id as string | undefined
  const vacancyId = c.vacancy_id as string | undefined
  const effectiveJobId = jobId || (vacancyId as string | undefined)
  const canTransition = !!vacancyCandidateId && !!effectiveJobId

  const candidateStage = c.stage as string | undefined
  const candidateSubStatus = (c.status || c.sub_status) as string | undefined

  const fetchPipeline = useCallback(async () => {
    if (!effectiveJobId) return
    try {
      const res = await fetch(`/api/backend-proxy/jobs/${effectiveJobId}/pipeline`)
      if (res.ok) {
        const data = await res.json()
        if (data.pipeline) {
          setPipeline(data.pipeline.filter((s: StageInfo) => !s.is_hired))
        }
      }
    } catch { /* silent */ }
  }, [effectiveJobId])

  const fetchInterviewData = useCallback(async () => {
    if (!candidateId) return
    try {
      const params = new URLSearchParams({ candidate_id: candidateId, status: "scheduled" })
      if (effectiveJobId) params.set("job_vacancy_id", effectiveJobId)
      const res = await fetch(`/api/backend-proxy/interviews?${params}`)
      if (res.ok) {
        const data = await res.json()
        const list: Array<{ id: string; meeting_url: string | null; status: string }> =
          Array.isArray(data) ? data : (data.interviews || data.items || [])
        const active = list.find(i => ["scheduled", "confirmed"].includes(i.status))
        if (active) {
          setInterviewData({ interview_id: active.id, meeting_url: active.meeting_url, status: active.status })
        }
      }
    } catch { /* silent */ }
  }, [candidateId, effectiveJobId])

  const fetchHighlight = useCallback(async () => {
    if (!candidateId || !companyId) return
    try {
      const res = await fetch(
        `/api/backend-proxy/opinions/candidate/${candidateId}/summary?company_id=${encodeURIComponent(companyId)}`
      )
      if (res.ok) {
        const data = await res.json()
        const opinion = data.current_general_opinion
        const strengths = opinion?.strengths || opinion?.key_strengths || []
        if (opinion?.summary || strengths.length > 0) {
          setHighlight({ summary: opinion.summary || "", strengths: Array.isArray(strengths) ? strengths : [] })
          return
        }
      }
    } catch { /* silent */ }
    const position = (candidate.position || candidate.title || "") as string
    const company = (
      (candidate.work_history as Array<Record<string, unknown>> | undefined)?.[0]?.company ||
      c.current_company || c.company || ""
    ) as string
    const years = (candidate.years_of_experience || c.yearsOfExperience) as number | undefined
    const seniority = (c.seniority_level || c.seniorityLevel || "") as string
    if (position || company) {
      const parts: string[] = []
      if (seniority && position) parts.push(`${seniority} ${position}`)
      else if (position) parts.push(position)
      if (company) parts.push(`na ${company}`)
      if (years) parts.push(`com ${years} anos de experiência`)
      setHighlight({ summary: parts.join(" ") + ".", strengths: [] })
    }
  }, [candidateId, companyId, candidate, c])

  useEffect(() => { if (effectiveJobId) fetchPipeline() }, [effectiveJobId, fetchPipeline])
  useEffect(() => { if (candidateStage) setCurrentStage(candidateStage) }, [candidateStage])
  useEffect(() => { if (candidateSubStatus) setCurrentSubStatus(candidateSubStatus) }, [candidateSubStatus])
  useEffect(() => { fetchHighlight() }, [fetchHighlight])

  const stageInfo = pipeline.find(
    s => s.name === currentStage ||
      s.name.toLowerCase() === currentStage.toLowerCase() ||
      s.display_name?.toLowerCase() === currentStage.toLowerCase()
  )
  const canonicalStage = stageInfo?.name || currentStage
  const stageColor = stageInfo?.color || "var(--lia-text-secondary)"
  const actionBehavior = stageInfo?.action_behavior || "passive"
  const stageDisplayName = stageInfo?.display_name || currentStage || "—"
  const subStatusDisplay = currentSubStatus
    ? (stageInfo?.sub_statuses?.find(s => s.name === currentSubStatus)?.display_name ||
       currentSubStatus.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()))
    : ""

  useEffect(() => {
    if (actionBehavior === "scheduling") fetchInterviewData()
  }, [actionBehavior, fetchInterviewData])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (flyoutRef.current && !flyoutRef.current.contains(e.target as Node)) {
        setShowMoveDropdown(false)
        setHoveredStageIdx(null)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const handleTransition = useCallback(async (toStage: string, subStatus?: string) => {
    setShowMoveDropdown(false)
    setHoveredStageIdx(null)
    setIsProcessing(true)

    const useScreeningEndpoint =
      actionBehavior === "screening" || actionBehavior === "intake"

    try {
      if (useScreeningEndpoint) {
        const isApprove = !pipeline.find(s => s.name === toStage)?.is_rejection && toStage !== "rejected"
        const body: Record<string, unknown> = {
          job_id: effectiveJobId,
          decision: isApprove ? "approved" : "rejected",
        }
        if (!isApprove && userId) body.reviewer_id = userId
        if (!isApprove && subStatus) body.reason = subStatus

        const res = await fetch(`/api/backend-proxy/candidates/${candidateId}/screening-decision/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        })
        if (res.ok) {
          const data = await res.json()
          if (isApprove) {
            toast.success("Candidato aprovado", {
              description: `${candidate.name} avançou para ${data.new_stage || "próxima etapa"}.`,
            })
            if (data.new_stage) setCurrentStage(data.new_stage)
          } else {
            toast.success("Candidato reprovado", {
              description: `${candidate.name} foi movido para Reprovados.`,
            })
            setCurrentStage("rejected")
          }
          onCandidateUpdated?.()
        } else {
          const err = await res.json().catch(() => ({}))
          toast.error("Erro", { description: err.detail?.message || err.error || "Não foi possível executar ação." })
        }
      } else {
        if (!canTransition) {
          toast.error("Candidato sem vínculo com vaga", {
            description: "Não é possível mover este candidato.",
          })
          return
        }
        const body: Record<string, unknown> = {
          vacancy_candidate_id: vacancyCandidateId,
          from_stage: canonicalStage,
          to_stage: toStage,
          vacancy_id: effectiveJobId,
          action: "manual",
        }
        if (subStatus) body.sub_status = subStatus

        const res = await fetch("/api/backend-proxy/transition/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        })
        if (res.ok) {
          const data = await res.json()
          if (data.requires_approval) {
            toast.info("Aguardando aprovação", {
              description: `A transição de ${candidate.name} requer aprovação antes de ser concluída.`,
            })
            onCandidateUpdated?.()
          } else if (data.success) {
            const targetStage = pipeline.find(s => s.name === toStage)
            const targetSubLabel = subStatus
              ? (targetStage?.sub_statuses?.find(s => s.name === subStatus)?.display_name || subStatus)
              : null
            toast.success("Candidato movido", {
              description: targetSubLabel
                ? `${candidate.name} → ${targetStage?.display_name || toStage} · ${targetSubLabel}`
                : `${candidate.name} → ${targetStage?.display_name || toStage}`,
            })
            setCurrentStage(toStage)
            if (subStatus) setCurrentSubStatus(subStatus)
            else if (data.new_sub_status) setCurrentSubStatus(data.new_sub_status)
            onCandidateUpdated?.()
          } else {
            toast.error("Erro ao mover", { description: data.message || "Não foi possível mover." })
          }
        } else {
          toast.error("Erro ao mover", { description: "Falha ao executar transição." })
        }
      }
    } catch {
      toast.error("Erro de conexão", { description: "Não foi possível conectar ao servidor." })
    } finally {
      setIsProcessing(false)
      setConfirmingReject(false)
    }
  }, [
    candidateId, vacancyCandidateId, effectiveJobId,
    canonicalStage, actionBehavior, canTransition,
    pipeline, candidate.name, onCandidateUpdated, userId,
  ])

  const handleEnterRoom = useCallback(() => {
    const url = interviewData?.meeting_url
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer")
    } else {
      toast.error("Link indisponível", {
        description: "Não há entrevista agendada com link de vídeo.",
      })
    }
  }, [interviewData])

  const handleReschedule = useCallback(() => {
    if (!interviewData?.interview_id) {
      toast.error("Entrevista não encontrada", {
        description: "Nenhuma entrevista agendada encontrada para este candidato.",
      })
      return
    }
    toast.info("Selecione um novo horário", {
      description: "Acesse o calendário da entrevista para escolher um novo horário e confirme o reagendamento.",
    })
  }, [interviewData])

  // ---------- No job context: show AI highlight only ----------
  if (!effectiveJobId) {
    if (highlight?.summary) {
      return (
        <div className="border-b px-3 py-2 bg-lia-bg-primary">
          <div className="flex items-start gap-1.5 px-2 py-1.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <Brain className="w-3 h-3 text-wedo-cyan mt-0.5 flex-shrink-0" />
            <p className="text-micro text-lia-text-secondary leading-relaxed">
              {highlight.summary}
              {highlight.strengths.length > 0 && (
                <> {highlight.strengths.slice(0, 2).join(". ")}.</>
              )}
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  // ---------- Derived values ----------
  const isScreening = actionBehavior === "screening" || actionBehavior === "intake"
  const isScheduling = actionBehavior === "scheduling"
  const isOffer = actionBehavior === "offer"
  const currentIdx = pipeline.findIndex(s => s.name === canonicalStage)
  const nextStage = currentIdx >= 0 && currentIdx < pipeline.length - 1 ? pipeline[currentIdx + 1] : null
  const rejectStageName = pipeline.find(s => s.is_rejection)?.name || "rejected"

  // ---------- Confirm-reject inline dialog ----------
  const renderConfirmReject = () => {
    const firstName = (candidate.name as string)?.split(" ")[0] || "Candidato"
    const label = isOffer ? "Recusar proposta" : isScheduling ? "Não passou?" : "Reprovar"
    return (
      <div className="flex items-center gap-1.5">
        <span className="text-micro text-lia-text-secondary">{label} {firstName}?</span>
        <button
          onClick={() => handleTransition(rejectStageName)}
          disabled={isProcessing}
          className="inline-flex items-center gap-0.5 px-2 py-0.5 text-micro font-medium rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50 transition-colors"
        >
          {isProcessing ? <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" /> : "Sim"}
        </button>
        <button
          onClick={() => setConfirmingReject(false)}
          disabled={isProcessing}
          className="inline-flex items-center px-2 py-0.5 text-micro font-medium rounded-md bg-lia-bg-primary text-lia-text-primary border border-lia-border-default hover:bg-lia-interactive-hover transition-colors"
        >
          Não
        </button>
      </div>
    )
  }

  // ---------- Contextual CTAs by stage type ----------
  const renderContextualCTAs = () => {
    if (confirmingReject) return renderConfirmReject()

    if (isScreening) {
      return (
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => nextStage && handleTransition(nextStage.name)}
            disabled={isProcessing || !nextStage}
            className="flex-1 h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isProcessing
              ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              : <CheckCircle2 className="w-3.5 h-3.5" />}
            Aprovar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingReject(true)}
            disabled={isProcessing}
            className="flex-1 h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)]"
          >
            <XCircle className="w-3.5 h-3.5" />
            Reprovar
          </Button>
        </div>
      )
    }

    if (isScheduling) {
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          <Button
            size="sm"
            onClick={handleEnterRoom}
            disabled={isProcessing || !interviewData?.meeting_url}
            title={!interviewData?.meeting_url ? "Nenhuma entrevista com link agendada" : undefined}
            className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text disabled:opacity-40"
          >
            <Video className="w-3.5 h-3.5" />
            Entrar na Sala
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleReschedule}
            disabled={isProcessing || !interviewData?.interview_id}
            title={!interviewData?.interview_id ? "Nenhuma entrevista ativa encontrada" : undefined}
            className="h-7 gap-1 text-micro border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover disabled:opacity-40"
          >
            <RotateCcw className="w-3 h-3" />
            Reagendar
          </Button>
          <span className="text-lia-text-disabled mx-0.5">|</span>
          <Button
            size="sm"
            onClick={() => nextStage && handleTransition(nextStage.name)}
            disabled={isProcessing || !nextStage || !canTransition}
            className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text disabled:opacity-40"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Passou
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingReject(true)}
            disabled={isProcessing || !canTransition}
            className="h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)] disabled:opacity-40"
          >
            <XCircle className="w-3.5 h-3.5" />
            Não passou
          </Button>
        </div>
      )
    }

    if (isOffer) {
      return (
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => nextStage && handleTransition(nextStage.name, "offer_accepted")}
            disabled={isProcessing || !nextStage || !canTransition}
            className="flex-1 h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text disabled:opacity-40"
          >
            {isProcessing
              ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              : <CheckCircle2 className="w-3.5 h-3.5" />}
            Proposta Aceita
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingReject(true)}
            disabled={isProcessing || !canTransition}
            className="flex-1 h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)] disabled:opacity-40"
          >
            <XCircle className="w-3.5 h-3.5" />
            Recusar
          </Button>
        </div>
      )
    }

    // passive / other stages — quick advance button if next stage exists
    if (nextStage && canTransition) {
      return (
        <Button
          size="sm"
          onClick={() => handleTransition(nextStage.name)}
          disabled={isProcessing}
          className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
        >
          <ArrowRight className="w-3.5 h-3.5" />
          Avançar para {nextStage.display_name}
        </Button>
      )
    }

    return null
  }

  return (
    <div className="rounded-lg px-3 py-2 bg-lia-bg-primary space-y-2">
      {/* Row 1: Stage indicator + sub-status badge + Mover para flyout */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: stageColor }} />
          <span className="text-xs font-semibold text-lia-text-primary truncate">{stageDisplayName}</span>
          {subStatusDisplay && (
            <span className="text-micro text-lia-text-tertiary px-1.5 py-0.5 bg-lia-bg-tertiary border border-lia-border-subtle rounded flex-shrink-0">
              {subStatusDisplay}
            </span>
          )}
        </div>

        {/* Flyout "Mover para" */}
        <div className="relative flex-shrink-0" ref={flyoutRef}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => { setShowMoveDropdown(v => !v); setHoveredStageIdx(null) }}
            disabled={isProcessing}
            className="h-6 gap-1 text-micro border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
          >
            <ChevronDown className="w-3 h-3" />
            Mover para
          </Button>

          {showMoveDropdown && (
            <div className="absolute top-full right-0 mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lg z-50 min-w-[200px] py-1">
              {pipeline.filter(s => s.name !== canonicalStage).map((stage, idx) => (
                <div
                  key={stage.name}
                  className="relative"
                  onMouseEnter={() => setHoveredStageIdx(idx)}
                  onMouseLeave={() => setHoveredStageIdx(null)}
                >
                  <button
                    onClick={() => {
                      if (!stage.sub_statuses?.length) handleTransition(stage.name)
                    }}
                    disabled={!canTransition && !isScreening}
                    className={[
                      "w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary",
                      "hover:bg-lia-interactive-hover transition-colors flex items-center gap-2",
                      (!canTransition && !isScreening) ? "opacity-40 cursor-not-allowed" : "",
                    ].join(" ")}
                  >
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: stage.color }} />
                    <span className="flex-1">{stage.display_name}</span>
                    {!!stage.sub_statuses?.length && (
                      <ChevronRight className="w-3 h-3 text-lia-text-tertiary" />
                    )}
                  </button>

                  {/* Sub-status nested flyout */}
                  {hoveredStageIdx === idx && !!stage.sub_statuses?.length && (
                    <div className="absolute top-0 right-full mr-0.5 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-lg z-50 min-w-[220px] py-1">
                      <button
                        onClick={() => handleTransition(stage.name)}
                        className="w-full text-left px-3 py-1.5 text-micro text-lia-text-tertiary hover:bg-lia-interactive-hover italic transition-colors"
                      >
                        Sem sub-status específico
                      </button>
                      <div className="border-t border-lia-border-subtle my-0.5" />
                      {stage.sub_statuses.map(sub => (
                        <button
                          key={sub.name}
                          onClick={() => handleTransition(stage.name, sub.name)}
                          className="w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
                        >
                          {sub.display_name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!canTransition && !isScreening && (
                <p className="px-3 py-2 text-micro text-lia-text-tertiary border-t border-lia-border-subtle mt-0.5">
                  Candidato não vinculado a esta vaga
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Contextual CTAs */}
      {renderContextualCTAs()}

      {/* AI highlight strip */}
      {highlight?.summary && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
          <Brain className="w-3 h-3 text-wedo-cyan mt-0.5 flex-shrink-0" />
          <p className="text-micro text-lia-text-secondary leading-relaxed">
            {highlight.summary}
            {highlight.strengths.length > 0 && (
              <> {highlight.strengths.slice(0, 2).join(". ")}.</>
            )}
          </p>
        </div>
      )}
    </div>
  )
}
