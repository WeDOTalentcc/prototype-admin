"use client"

import { useState, useEffect } from "react"
import {
  ThumbsUp, ThumbsDown, Clock, CheckCircle, Star, AlertTriangle
} from "lucide-react"
import { liaApi, WSIResultDetails, WSICandidateRanking, WSIVacancyRanking } from "@/services/lia-api"
import type { Candidate } from "@/components/pages/candidates/types"

export interface F11ReportData {
  seniority?: string
  seniority_weights?: { technical: number; behavioral: number }
  mode?: string
  question_count?: number
  cbi_questions?: Array<{ severity?: string; question?: string; texto?: string; focus?: string; foco?: string }>
  response_analyses?: Array<{ feedback?: string }>
  [key: string]: unknown
}

export const WSI_CLASSIFICATION_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  excepcional:     { bg: 'var(--status-success-bg)',  text: 'var(--status-success)', label: 'Excepcional' },
  excelente:       { bg: 'var(--status-success-bg)',  text: 'var(--status-success)', label: 'Excelente' },
  alto:            { bg: 'var(--lia-bg-tertiary)',            text: 'var(--lia-text-primary)',        label: 'Alto' },
  medio:           { bg: 'var(--status-warning-bg)',  text: 'var(--status-warning)',  label: 'Médio' },
  abaixo_da_media: { bg: 'var(--status-error-bg)',    text: 'var(--status-error)',    label: 'Abaixo da média' },
  regular:         { bg: 'var(--status-error-bg)',    text: 'var(--status-error)',    label: 'Regular / Baixo' },
}

export const getClassificationColor = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification] ?? { bg: 'var(--wedo-cyan-bg-12)', text: 'var(--lia-text-secondary)', label: classification }

export const getClassificationLabel = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification]?.label ?? classification

export const getDecisionDisplay = (decision?: string) => {
  const normalized = (decision ?? '').toUpperCase().replace('NAO_APROVADO', 'REPROVADO').replace('AGUARDANDO', 'EM_AVALIACAO')
  switch (normalized) {
    case 'APROVADO':
    case 'aprovado':
      return { label: 'Aprovado', icon: ThumbsUp, color: 'var(--status-success)', bg: 'var(--status-success-bg)' }
    case 'EM_AVALIACAO':
    case 'aguardando':
      return { label: 'Em Avaliação', icon: Clock, color: 'var(--status-warning)', bg: 'var(--status-warning-bg)' }
    case 'REPROVADO':
    case 'nao_aprovado':
      return { label: 'Não Aprovado', icon: ThumbsDown, color: 'var(--status-error)', bg: 'var(--status-error-bg)' }
    default: return { label: 'Pendente', icon: Clock, color: 'var(--lia-text-tertiary)', bg: 'var(--lia-bg-secondary)' }
  }
}

// Escala WSI 0-10 (Task #512). Helper canônico em `lib/wsi/visual.ts`.
export const wsiToPercent = (score: number) => Math.round((score / 10) * 100)

export const bloomLabel = (n: number) =>
  (["", "Recordar", "Compreender", "Aplicar", "Analisar", "Avaliar", "Criar"] as const)[n] ?? `Nível ${n}`

export const dreyfusLabel = (n: number) =>
  (["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"] as const)[n] ?? `Nível ${n}`

// Escala WSI 0-10 (Task #512) — política 3-tier visual: ver `lib/wsi/visual.ts`
// (WSI_VISUAL_3TIER: verde >=7.5, amarelo >=6.0, vermelho <6.0).
// Reexporta o helper canônico para evitar drift de cutoffs.
export { getWsiScoreColor as getScoreColor, getWsiScoreColor as getScoreColor3Tier } from "@/lib/wsi/visual"

export const gapConfig = {
  ok:    { label: "Alinhado",          icon: CheckCircle,   color: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" },
  acima: { label: "Acima do esperado", icon: Star,          color: "text-wedo-cyan-text",  bg: "bg-wedo-cyan/10",     border: "border-wedo-cyan/30"       },
  gap:   { label: "Gap identificado",  icon: AlertTriangle, color: "text-status-warning",  bg: "bg-status-warning/10",border: "border-status-warning/30"  },
}

export const starComponents = [
  { key: "S" as const, label: "Situação", desc: "Contexto descrito" },
  { key: "T" as const, label: "Tarefa", desc: "Objetivo claro" },
  { key: "A" as const, label: "Ação", desc: "O que foi feito" },
  { key: "R" as const, label: "Resultado", desc: "Impacto mensurável" },
]

export const sevConfig = {
  alta:  { label: "ALTA",  color: "text-status-error",   bg: "bg-status-error/10",   border: "border-status-error/30",   dot: "bg-status-error"   },
  media: { label: "MÉDIA", color: "text-status-warning",  bg: "bg-status-warning/10", border: "border-status-warning/30", dot: "bg-status-warning" },
  baixa: { label: "BAIXA", color: "lia-text-secondary",        bg: "bg-lia-bg-secondary",           border: "border-lia-border-subtle",          dot: "bg-lia-border-medium"       },
}

export const getFrameworkLabel = (framework: string) => {
  switch (framework) {
    case 'CBI': return 'Competency-Based'
    case 'Bloom': return "Bloom's Taxonomy"
    case 'Dreyfus': return 'Dreyfus Model'
    case 'BigFive': return 'Big Five (OCEAN)'
    default: return framework
  }
}

export function useTriagemDetailsState(
  candidate: Candidate,
  isOpen: boolean,
  jobVacancyId?: string
) {
  const [activeTab, setActiveTab] = useState<'triagem' | 'parecer' | 'comparativo'>('triagem')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['responses']))
  const [loading, setLoading] = useState(true)
  const [details, setDetails] = useState<WSIResultDetails | null>(null)
  const [ranking, setRanking] = useState<WSICandidateRanking | null>(null)
  const [vacancyRanking, setVacancyRanking] = useState<WSIVacancyRanking | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [feedbackStatus, setFeedbackStatus] = useState<Record<string, unknown> | null>(null)
  const [sendingFeedback, setSendingFeedback] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState(false)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [confirmReject, setConfirmReject] = useState(false)
  const [f11Report, setF11Report] = useState<F11ReportData | null>(null)
  const [bigFiveHint, setBigFiveHint] = useState<string | null>(null)
  const [copiedFeedback, setCopiedFeedback] = useState(false)

  useEffect(() => {
    if (isOpen && candidate?.id) {
      loadData()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, candidate?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const resultsData = await liaApi.wsiGetCandidateResults(candidate.id, 1)
      if (resultsData.total_screenings === 0) {
        setError('Nenhuma triagem WSI encontrada para este candidato.')
        return
      }
      const latestResult = resultsData.results[0]
      const detailsData = await liaApi.wsiGetResultDetails(latestResult.result_id)
      setDetails(detailsData)
      try {
        const fbStatus = await liaApi.wsiGetFeedbackStatus(latestResult.result_id)
        setFeedbackStatus(fbStatus)
      } catch (e) {}
      const vacId = jobVacancyId || detailsData.job_vacancy_id
      if (vacId) {
        try {
          const [rankData, vacRankData] = await Promise.all([
            liaApi.wsiGetCandidateRanking(candidate.id, vacId),
            liaApi.wsiGetVacancyRanking(vacId)
          ])
          setRanking(rankData)
          setVacancyRanking(vacRankData)
        } catch (e) {}
      }
      const sessionId = detailsData.session?.session_id || detailsData.session_id
      if (sessionId) {
        try {
          const f11 = await fetch(`/api/backend-proxy/wsi/f11-report/${sessionId}`)
          if (f11.ok) setF11Report(await f11.json())
        } catch (e) {}
      }
    } catch (err) {
      setError('Erro ao carregar dados da triagem.')
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const handleSendFeedback = async () => {
    if (!details) return
    const resultId = details.result_id || (details as WSIResultDetails & { id?: string }).id
    if (!resultId) return
    setSendingFeedback(true)
    setFeedbackError(null)
    try {
      const result = await liaApi.wsiTriggerFeedback(resultId)
      setFeedbackSuccess(true)
      setFeedbackStatus({ ...feedbackStatus, feedback_sent: true })
      setTimeout(() => setFeedbackSuccess(false), 5000)
    } catch (err: unknown) {
      setFeedbackError(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao enviar feedback')
    } finally {
      setSendingFeedback(false)
    }
  }

  const decision = details?.scores?.decision || (details as WSIResultDetails & { decision?: string })?.decision
  const decisionNormalized = (decision ?? '').toUpperCase()
  const isPendingDecision = !decision || decisionNormalized === 'AGUARDANDO' || decisionNormalized === 'EM_AVALIACAO'
  const canTriggerFeedback = !!details && !!details.scores
  const feedbackAlreadySent = feedbackStatus?.feedback_sent === true

  return {
    activeTab, setActiveTab, expandedSections, loading, details, ranking,
    vacancyRanking, error, feedbackStatus, sendingFeedback, feedbackSuccess,
    feedbackError, approving, setApproving, rejecting, setRejecting,
    confirmReject, setConfirmReject, f11Report, bigFiveHint, setBigFiveHint,
    copiedFeedback, setCopiedFeedback, toggleSection, handleSendFeedback,
    decision, decisionNormalized, isPendingDecision, canTriggerFeedback,
    feedbackAlreadySent,
  }
}
