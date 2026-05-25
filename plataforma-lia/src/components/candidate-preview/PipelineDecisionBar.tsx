"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import {
  CheckCircle2, XCircle, ChevronDown, Loader2, Brain,
  ArrowRight, Video, RotateCcw, Send, DollarSign, UserPlus
} from "lucide-react"
import { toast } from "sonner"
import { useCurrentCompany } from "@/hooks/company/use-current-company"
import { AUTHORITATIVE_ACTION_MATRIX } from "@/components/kanban/utils/action-matrix"
import type { CandidateData } from "./ProfileTabTypes"

interface StageInfo {
  name: string
  display_name: string
  stage_order: number
  color: string
  action_behavior: string
  sub_statuses?: Array<{ name: string; display_name: string }>
}

interface PipelineDecisionBarProps {
  candidate: CandidateData
  jobId?: string
  onCandidateUpdated?: () => void
}

interface HighlightData {
  summary: string
  strengths: string[]
}

export function PipelineDecisionBar({
  candidate,
  jobId,
  onCandidateUpdated,
}: PipelineDecisionBarProps) {
  const { companyId } = useCurrentCompany()
  const [pipeline, setPipeline] = useState<StageInfo[]>([])
  const [currentStage, setCurrentStage] = useState<string>("")
  const [currentSubStatus, setCurrentSubStatus] = useState<string>("")
  const [showMoveDropdown, setShowMoveDropdown] = useState(false)
  const [showSubStatusDropdown, setShowSubStatusDropdown] = useState(false)
  const [confirmingAction, setConfirmingAction] = useState<"approve" | "reject" | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [highlight, setHighlight] = useState<HighlightData | null>(null)

  const candidateId = (candidate.id || candidate.candidateId || candidate.pearch_id) as string | undefined
  const vacancyCandidateId = (candidate as Record<string, unknown>).vacancy_candidate_id as string | undefined
  const vacancyId = (candidate as Record<string, unknown>).vacancy_id as string | undefined
  const effectiveJobId = jobId || vacancyId
  const canTransition = !!vacancyCandidateId && !!effectiveJobId

  const candidateStage = (candidate as Record<string, unknown>).stage as string | undefined
  const candidateSubStatus = ((candidate as Record<string, unknown>).status || (candidate as Record<string, unknown>).sub_status) as string | undefined

  const fetchPipeline = useCallback(async () => {
    if (!effectiveJobId) return
    try {
      const url = `/api/backend-proxy/jobs/${effectiveJobId}/pipeline`
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        if (data.pipeline) {
          setPipeline(data.pipeline.filter((s: StageInfo) => s.name !== 'rejected' && s.name !== 'hired'))
        }
      }
    } catch (err) {
      console.warn('[PipelineDecisionBar] Failed to fetch pipeline:', err)
    }
  }, [effectiveJobId])

  const fetchHighlight = useCallback(async () => {
    if (!candidateId || !companyId) return
    try {
      const response = await fetch(
        `/api/backend-proxy/opinions/candidate/${candidateId}/summary?company_id=${encodeURIComponent(companyId)}`
      )
      if (response.ok) {
        const data = await response.json()
        const opinion = data.current_general_opinion
        const opinionStrengths = opinion?.strengths || opinion?.key_strengths || []
        if (opinion?.summary || (opinionStrengths && opinionStrengths.length > 0)) {
          setHighlight({
            summary: opinion.summary || "",
            strengths: Array.isArray(opinionStrengths) ? opinionStrengths : [],
          })
          return
        }
      }
    } catch (err) {
      console.warn('[PipelineDecisionBar] Failed to fetch highlight:', err)
    }

    const position = (candidate.position || candidate.title || "") as string
    const company = (((candidate.work_history as Array<Record<string, unknown>> | undefined)?.[0])?.company || candidate.current_company || candidate.company || "") as string
    const years = (candidate.years_of_experience || candidate.yearsOfExperience) as number | undefined
    const seniority = (candidate.seniority_level || candidate.seniorityLevel || "") as string

    if (position || company) {
      const parts: string[] = []
      if (seniority && position) {
        parts.push(`${seniority} ${position}`)
      } else if (position) {
        parts.push(position)
      }
      if (company) parts.push(`na ${company}`)
      if (years) parts.push(`com ${years} anos de experiência`)
      setHighlight({
        summary: parts.join(" ") + ".",
        strengths: [],
      })
    }
  }, [candidateId, companyId, candidate])

  useEffect(() => {
    if (effectiveJobId) {
      fetchPipeline()
    }
  }, [effectiveJobId, fetchPipeline])

  useEffect(() => {
    if (candidateStage) {
      setCurrentStage(candidateStage)
    }
    if (candidateSubStatus) {
      setCurrentSubStatus(candidateSubStatus as string)
    }
  }, [candidateStage, candidateSubStatus])

  useEffect(() => {
    fetchHighlight()
  }, [fetchHighlight])

  const stageInfo = pipeline.find(
    s => s.name === currentStage || s.display_name === currentStage ||
      s.name.toLowerCase() === currentStage.toLowerCase() ||
      s.display_name?.toLowerCase() === currentStage.toLowerCase()
  )
  const canonicalStage = stageInfo?.name || currentStage
  const stageColor = stageInfo?.color || "var(--lia-text-secondary)"
  const actionBehavior = stageInfo?.action_behavior || "passive"
  const stageDisplayName = stageInfo?.display_name || currentStage || "—"

  const actionConfig = AUTHORITATIVE_ACTION_MATRIX[actionBehavior] || AUTHORITATIVE_ACTION_MATRIX['passive']
  const subStatuses: Array<string | { name: string; display_name: string }> = stageInfo?.sub_statuses || actionConfig?.defaultSubStatuses?.map(s => ({
    name: s,
    display_name: s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
  })) || []

  const subStatusDisplay = currentSubStatus
    ? currentSubStatus.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    : ""

  const handleApprove = async () => {
    if (!candidateId) return
    setIsProcessing(true)

    const stageLwr = canonicalStage.toLowerCase()
    const useScreeningEndpoint = stageLwr === 'screening' || stageLwr === 'triagem' ||
      stageLwr === 'intake' || stageLwr === 'funil'

    try {
      if (useScreeningEndpoint) {
        const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/screening-decision/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_id: effectiveJobId,
            decision: 'approved',
          }),
        })
        if (response.ok) {
          const data = await response.json()
          toast.success('Candidato aprovado', {
            description: `${candidate.name} avançou para ${data.new_stage || 'próxima etapa'}.`,
          })
          if (data.new_stage) setCurrentStage(data.new_stage)
          onCandidateUpdated?.()
        } else {
          const errorData = await response.json().catch(() => ({}))
          if (errorData.detail?.error === 'missing_contact_info') {
            toast.error('Dados de contato incompletos', {
              description: `${candidate.name} não possui email ou telefone válido.`,
            })
          } else {
            toast.error('Erro ao aprovar', {
              description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar.',
            })
          }
        }
      } else {
        if (!vacancyCandidateId) {
          toast.error('Erro ao aprovar', { description: 'Candidato sem vínculo com vaga. Não é possível executar transição.' })
          return
        }
        const nextStageIdx = pipeline.findIndex(s => s.name === canonicalStage) + 1
        const nextStage = nextStageIdx < pipeline.length ? pipeline[nextStageIdx] : null
        if (!nextStage) {
          toast.error('Erro ao aprovar', { description: 'Não há próxima etapa disponível.' })
          return
        }
        const response = await fetch(`/api/backend-proxy/transition/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vacancy_candidate_id: vacancyCandidateId,
            from_stage: canonicalStage,
            to_stage: nextStage.name,
            vacancy_id: effectiveJobId,
            action: 'manual',
          }),
        })
        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            toast.success('Candidato aprovado', {
              description: `${candidate.name} avançou para ${nextStage.display_name}.`,
            })
            setCurrentStage(nextStage.name)
            if (data.new_sub_status) setCurrentSubStatus(data.new_sub_status)
            onCandidateUpdated?.()
          } else {
            toast.error('Erro ao aprovar', { description: data.message || 'Não foi possível aprovar.' })
          }
        } else {
          toast.error('Erro ao aprovar', { description: 'Falha ao executar transição.' })
        }
      }
    } catch {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    } finally {
      setIsProcessing(false)
      setConfirmingAction(null)
    }
  }

  const handleReject = async () => {
    if (!candidateId) return
    setIsProcessing(true)

    const stageLwr = canonicalStage.toLowerCase()
    const useScreeningEndpoint = stageLwr === 'screening' || stageLwr === 'triagem' ||
      stageLwr === 'intake' || stageLwr === 'funil'

    try {
      if (useScreeningEndpoint) {
        const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/screening-decision/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_id: effectiveJobId,
            decision: 'rejected',
            reason: 'Reprovado via preview',
          }),
        })
        if (response.ok) {
          toast.error('Candidato reprovado', {
            description: `${candidate.name} foi movido para Reprovados.`,
          })
          setCurrentStage('rejected')
          onCandidateUpdated?.()
        } else {
          const errorData = await response.json().catch(() => ({}))
          toast.error('Erro ao reprovar', {
            description: errorData.error || 'Não foi possível reprovar o candidato.',
          })
        }
      } else {
        if (!vacancyCandidateId) {
          toast.error('Erro ao reprovar', { description: 'Candidato sem vínculo com vaga. Não é possível executar transição.' })
          return
        }
        const response = await fetch(`/api/backend-proxy/transition/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vacancy_candidate_id: vacancyCandidateId,
            from_stage: canonicalStage,
            to_stage: 'rejected',
            vacancy_id: effectiveJobId,
            action: 'manual',
          }),
        })
        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            toast.error('Candidato reprovado', {
              description: `${candidate.name} foi movido para Reprovados.`,
            })
            setCurrentStage('rejected')
            onCandidateUpdated?.()
          } else {
            toast.error('Erro ao reprovar', { description: data.message || 'Não foi possível reprovar.' })
          }
        } else {
          toast.error('Erro ao reprovar', { description: 'Falha ao executar transição.' })
        }
      }
    } catch {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    } finally {
      setIsProcessing(false)
      setConfirmingAction(null)
    }
  }

  const handleMoveToStage = async (targetStageName: string) => {
    if (!vacancyCandidateId) {
      toast.error('Erro ao mover', { description: 'Candidato sem vínculo com vaga.' })
      return
    }
    setIsProcessing(true)
    setShowMoveDropdown(false)
    try {
      const response = await fetch(`/api/backend-proxy/transition/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vacancy_candidate_id: vacancyCandidateId,
          from_stage: canonicalStage,
          to_stage: targetStageName,
          vacancy_id: effectiveJobId,
          action: 'manual',
        }),
      })
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          const target = pipeline.find(s => s.name === targetStageName)
          toast.success('Candidato movido', {
            description: `${candidate.name} foi movido para ${target?.display_name || targetStageName}.`,
          })
          setCurrentStage(targetStageName)
          if (data.new_sub_status) {
            setCurrentSubStatus(data.new_sub_status)
          }
          onCandidateUpdated?.()
        } else {
          toast.error('Erro ao mover', { description: data.message || 'Não foi possível mover.' })
        }
      } else {
        toast.error('Erro ao mover', { description: 'Falha ao executar transição.' })
      }
    } catch {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSubStatusChange = async (newSubStatus: string) => {
    if (!vacancyCandidateId) {
      toast.error('Erro ao atualizar status', { description: 'Candidato sem vínculo com vaga.' })
      return
    }
    setShowSubStatusDropdown(false)
    try {
      const response = await fetch(`/api/backend-proxy/transition/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vacancy_candidate_id: vacancyCandidateId,
          from_stage: canonicalStage,
          to_stage: canonicalStage,
          sub_status: newSubStatus,
          vacancy_id: effectiveJobId,
          action: 'manual',
        }),
      })
      if (response.ok) {
        setCurrentSubStatus(newSubStatus)
        toast.success('Status atualizado', {
          description: `Sub-status alterado para ${newSubStatus.replace(/_/g, ' ')}.`,
        })
        onCandidateUpdated?.()
      } else {
        toast.error('Erro ao atualizar status', { description: 'Não foi possível alterar o sub-status.' })
      }
    } catch {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    }
  }

  const stageLower = canonicalStage.toLowerCase()
  const isScreeningStage = actionBehavior === 'screening' || stageLower === 'screening' || stageLower === 'triagem'
  const isInterviewStage = actionBehavior === 'scheduling' || stageLower.includes('interview') || stageLower.includes('entrevista')
  const isOfferStage = actionBehavior === 'offer' || stageLower.includes('offer') || stageLower.includes('proposta')
  const isPassiveStage = !isScreeningStage && !isInterviewStage && !isOfferStage

  const renderInlineConfirm = (action: "approve" | "reject") => {
    const isApprove = action === "approve"
    const firstName = (candidate.name as string)?.split(' ')[0] || 'Candidato'

    return (
      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        <span className="text-micro text-lia-text-secondary">
          {isApprove ? `Aprovar ${firstName}?` : `Reprovar ${firstName}?`}
        </span>
        <button
          onClick={isApprove ? handleApprove : handleReject}
          disabled={isProcessing}
          className={
            'inline-flex items-center gap-0.5 px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover ' +
            'disabled:bg-lia-border-default disabled:text-lia-text-secondary disabled:cursor-not-allowed ' +
            'transition-colors duration-150'
          }
        >
          {isProcessing ? (
            <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
          ) : (
            'Sim'
          )}
        </button>
        <button
          onClick={() => setConfirmingAction(null)}
          disabled={isProcessing}
          className={
            'inline-flex items-center px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-lia-bg-primary text-lia-text-primary border border-lia-border-default hover:bg-lia-interactive-hover ' +
            'transition-colors duration-150'
          }
        >
          Não
        </button>
      </div>
    )
  }

  const renderContextualButtons = () => {
    if (confirmingAction) {
      return renderInlineConfirm(confirmingAction)
    }

    if (isScreeningStage) {
      return (
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => setConfirmingAction("approve")}
            disabled={isProcessing}
            className="flex-1 h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Aprovar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingAction("reject")}
            disabled={isProcessing}
            className="flex-1 h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)]"
          >
            <XCircle className="w-3.5 h-3.5" />
            Reprovar
          </Button>
        </div>
      )
    }

    if (isInterviewStage) {
      return (
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <Video className="w-3.5 h-3.5" />
            Entrar na Sala
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1 text-micro border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover"
          >
            <RotateCcw className="w-3 h-3" />
            Reagendar
          </Button>
          <span className="text-lia-text-disabled mx-0.5">|</span>
          <Button
            size="sm"
            onClick={() => setConfirmingAction("approve")}
            disabled={isProcessing}
            className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Passou
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingAction("reject")}
            disabled={isProcessing}
            className="h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)]"
          >
            <XCircle className="w-3.5 h-3.5" />
            Não passou
          </Button>
        </div>
      )
    }

    if (isOfferStage) {
      return (
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <Send className="w-3.5 h-3.5" />
            Enviar Proposta
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1 text-micro border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover"
          >
            <DollarSign className="w-3 h-3" />
            Negociar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmingAction("reject")}
            disabled={isProcessing}
            className="h-7 gap-1 text-micro border-[var(--lia-destructive-border)]/30 text-[var(--lia-destructive-bg)] hover:bg-[var(--lia-brand-primary-light)]"
          >
            <XCircle className="w-3.5 h-3.5" />
            Recusar
          </Button>
        </div>
      )
    }

    return (
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={() => {
            const nextStageIdx = pipeline.findIndex(s => s.name === canonicalStage) + 1
            if (nextStageIdx < pipeline.length) {
              handleMoveToStage(pipeline[nextStageIdx].name)
            }
          }}
          disabled={isProcessing}
          className="h-7 gap-1 text-micro bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
        >
          <ArrowRight className="w-3.5 h-3.5" />
          Avançar Etapa
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="h-7 gap-1 text-micro border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover"
        >
          <UserPlus className="w-3 h-3" />
          Adicionar à Lista
        </Button>
      </div>
    )
  }

  if (!effectiveJobId) {
    if (highlight && (highlight.summary || highlight.strengths.length > 0)) {
      return (
        <div className="border-b px-3 py-2 bg-lia-bg-primary dark:bg-lia-bg-primary">
          <div className="flex items-start gap-1.5 px-2 py-1.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <Brain className="w-3 h-3 text-wedo-cyan mt-0.5 flex-shrink-0" />
            <p className="text-micro text-lia-text-secondary leading-relaxed">
              {highlight.summary}
              {highlight.strengths.length > 0 && (
                <> {highlight.strengths.slice(0, 2).join('. ')}.</>
              )}
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="rounded-lg px-3 py-2 bg-lia-bg-primary dark:bg-lia-bg-primary space-y-2" style={{ borderBottomColor: stageColor }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: stageColor }} />
            <span className="text-xs font-semibold text-lia-text-primary">{stageDisplayName}</span>
          </div>
          {subStatusDisplay && (
            <>
              <span className="text-micro text-lia-text-tertiary">·</span>
              <div className="relative">
                <button
                  onClick={() => setShowSubStatusDropdown(!showSubStatusDropdown)}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-lia-bg-tertiary border border-lia-border-subtle rounded text-micro text-lia-text-secondary font-medium hover:bg-lia-interactive-hover transition-colors"
                >
                  {subStatusDisplay}
                  <ChevronDown className="w-2.5 h-2.5" />
                </button>
                {showSubStatusDropdown && subStatuses.length > 0 && (
                  <div className="absolute top-full left-0 mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-md z-50 min-w-[160px] py-1">
                    {subStatuses.map((sub) => (
                      <button
                        key={typeof sub === 'string' ? sub : sub.name}
                        onClick={() => handleSubStatusChange(typeof sub === 'string' ? sub : sub.name)}
                        className="w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
                      >
                        {typeof sub === 'string' ? sub.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : sub.display_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        <div className="relative">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowMoveDropdown(!showMoveDropdown)}
            disabled={isProcessing}
            className="h-6 gap-1 text-micro border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
          >
            <ChevronDown className="w-3 h-3" />
            Mover para
          </Button>
          {showMoveDropdown && pipeline.length > 0 && (
            <div className="absolute top-full right-0 mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl shadow-md z-50 min-w-[180px] py-1">
              {pipeline
                .filter(s => s.name !== canonicalStage)
                .map((stage) => (
                  <button
                    key={stage.name}
                    onClick={() => handleMoveToStage(stage.name)}
                    className="w-full text-left px-3 py-1.5 text-micro text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors flex items-center gap-2"
                  >
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: stage.color }} />
                    {stage.display_name}
                  </button>
                ))}
            </div>
          )}
        </div>
      </div>

      {renderContextualButtons()}

      {highlight && (highlight.summary || highlight.strengths.length > 0) && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
          <Brain className="w-3 h-3 text-wedo-cyan mt-0.5 flex-shrink-0" />
          <p className="text-micro text-lia-text-secondary leading-relaxed">
            {highlight.summary}
            {highlight.strengths.length > 0 && (
              <> {highlight.strengths.slice(0, 2).join('. ')}.</>
            )}
          </p>
        </div>
      )}
    </div>
  )
}
