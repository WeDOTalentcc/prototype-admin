"use client"

import React from "react"
import { CheckCircle, Clock, XCircle } from "lucide-react"
import { toast } from "sonner"
import type {
  RubricEvaluationData,
  RubricRequirement,
  RedFlag,
  ParecerLIA,
  DecisionBadge,
  ScoreBadge,
  RubricStyle,
  PriorityStyle,
} from "./rubric-evaluation-types"

export function getEvaluationLevel(req: RubricRequirement): string {
  return req.level || req.evaluation || 'unknown'
}

export function getScoreColor(scoreValue: number): string {
  if (scoreValue >= 85) return 'var(--lia-text-secondary)'
  if (scoreValue >= 70) return 'var(--lia-text-secondary)'
  if (scoreValue >= 50) return 'var(--status-warning)'
  return 'var(--status-error)'
}

export function getScoreBadge(scoreValue: number): ScoreBadge {
  if (scoreValue >= 85) return { label: 'Excelente', bg: 'var(--wedo-cyan-bg-12)' }
  if (scoreValue >= 70) return { label: 'Bom', bg: 'var(--wedo-cyan-bg-08)' }
  if (scoreValue >= 50) return { label: 'Moderado', bg: 'var(--status-warning-bg-12)', color: 'var(--status-warning)' }
  if (scoreValue >= 30) return { label: 'Fraco', bg: 'var(--status-error-bg-12)', color: 'var(--status-error)' }
  return { label: 'Inadequado', bg: 'var(--status-error-bg-15)', color: 'var(--status-error)' }
}

export function getDecisionBadge(decisao?: string): DecisionBadge | null {
  switch (decisao?.toUpperCase()) {
    case 'APROVAR_TRIAGEM':
      return { label: 'Aprovar para Triagem', bg: 'var(--wedo-cyan-bg-12)', icon: CheckCircle }
    case 'MANTER_ESPERA':
      return { label: 'Manter em Espera', bg: 'var(--status-warning-bg-12)', color: 'var(--status-warning)', icon: Clock }
    case 'NAO_PROSSEGUIR':
      return { label: 'Não Prosseguir', bg: 'var(--status-error-bg-12)', color: 'var(--status-error)', icon: XCircle }
    default:
      return null
  }
}

export function getRubricStyle(level: string): RubricStyle {
  switch (level?.toLowerCase()) {
    case 'exceeds':
      return { bg: 'var(--wedo-cyan-bg-08)', border: 'var(--lia-bg-secondary)' }
    case 'meets':
      return { bg: 'var(--wedo-cyan-bg-04)', border: 'var(--lia-bg-secondary)' }
    case 'partial':
      return { bg: 'var(--status-warning-bg-08)', border: 'var(--lia-bg-secondary)', color: 'var(--status-warning)' }
    case 'missing':
      return { bg: 'var(--status-error-bg-08)', border: 'var(--lia-bg-secondary)', color: 'var(--status-error)' }
    default:
      return { bg: 'var(--lia-bg-secondary)', border: 'var(--lia-bg-secondary)' }
  }
}

export function getRubricLabel(level: string): string {
  switch (level?.toLowerCase()) {
    case 'exceeds': return 'Excede'
    case 'meets': return 'Atende'
    case 'partial': return 'Parcial'
    case 'missing': return 'Ausente'
    default: return level
  }
}

export function getPriorityLabel(priority: string): string {
  switch (priority?.toLowerCase()) {
    case 'essential': return 'Essencial'
    case 'important': return 'Importante'
    case 'nice-to-have': return 'Desejável'
    default: return priority
  }
}

export function getPriorityStyle(priority: string): PriorityStyle {
  switch (priority?.toLowerCase()) {
    case 'essential':
      return { bg: 'var(--status-error-bg-12)', color: 'var(--status-error)' }
    case 'important':
      return { bg: 'var(--status-warning-bg-12)', color: 'var(--status-warning)' }
    case 'nice-to-have':
      return { bg: 'var(--lia-bg-secondary)' }
    default:
      return { bg: 'var(--lia-bg-secondary)' }
  }
}

export function useRubricEvaluation(
  evaluation: RubricEvaluationData | null,
  candidateId: string,
  candidateName: string | undefined,
  jobId: string,
  onApprove?: (candidateId: string, jobId: string) => Promise<void>,
  onReject?: (candidateId: string, jobId: string) => Promise<void>,
  onClose?: () => void,
) {
  const [isApproving, setIsApproving] = React.useState(false)
  const [isRejecting, setIsRejecting] = React.useState(false)
  const [activeSection, setActiveSection] = React.useState<'overview' | 'details'>('overview')
  const [showAudit, setShowAudit] = React.useState(false)

  const score = evaluation?.score ?? evaluation?.overall_score ?? 0
  const requirements = evaluation?.evaluations ?? evaluation?.requirements ?? []
  const jobTitle = evaluation?.job_title || 'Vaga não especificada'
  const displayName = candidateName || evaluation?.candidate_name || 'Candidato'

  const sortedRequirements = [...requirements].sort((a, b) => {
    const priorityOrder = { 'essential': 0, 'important': 1, 'nice-to-have': 2 }
    const aPriority = a.priority?.toLowerCase() as keyof typeof priorityOrder
    const bPriority = b.priority?.toLowerCase() as keyof typeof priorityOrder
    return (priorityOrder[aPriority] ?? 3) - (priorityOrder[bPriority] ?? 3)
  })

  const scoreBadge = getScoreBadge(score)

  const essentialReqs = requirements.filter(r => r.priority?.toLowerCase() === 'essential')
  const essentialMet = essentialReqs.filter(r => ['exceeds', 'meets'].includes(getEvaluationLevel(r).toLowerCase())).length
  const importantReqs = requirements.filter(r => r.priority?.toLowerCase() === 'important')
  const importantMet = importantReqs.filter(r => ['exceeds', 'meets'].includes(getEvaluationLevel(r).toLowerCase())).length
  const desirableReqs = requirements.filter(r => r.priority?.toLowerCase() === 'nice-to-have')
  const desirableMet = desirableReqs.filter(r => ['exceeds', 'meets'].includes(getEvaluationLevel(r).toLowerCase())).length

  const mockRedFlags: RedFlag[] = evaluation?.red_flags || [
    { type: 'Gaps na carreira', status: 'ok', detail: 'Trajetória linear' },
    { type: 'Job hopping', status: 'ok', detail: 'Média 2+ anos por empresa' },
    { type: 'Inconsistências', status: 'ok', detail: 'Dados consistentes' },
    { type: 'Senioridade', status: 'ok', detail: 'Nível alinhado com experiência' },
  ]

  const mockWhyCandidate = evaluation?.why_candidate || [
    'Experiência sólida nas tecnologias core exigidas pela vaga',
    'Histórico de entregas em projetos de complexidade similar',
    'Competências complementares que agregam valor ao time',
  ]

  const mockParecer: ParecerLIA = evaluation?.parecer_lia || {
    contexto_fit: `${displayName} apresenta um perfil técnico sólido e bem alinhado com as demandas da posição de ${jobTitle}. Sua trajetória profissional demonstra experiência consistente nas tecnologias e competências requeridas, com evidências de aplicação prática em ambientes similares ao contexto desta vaga.`,
    pontos_fortes_impacto: evaluation?.strengths?.slice(0, 3).map((s, i) => ({
      ponto: s,
      evidencia: `Evidência identificada no currículo do candidato`,
      impacto_negocio: i === 0 ? 'Contribuição imediata sem curva de aprendizado' : i === 1 ? 'Reduz riscos e acelera entregas' : 'Agrega valor ao time existente'
    })) || [
      {
        ponto: 'Experiência nas tecnologias requeridas',
        evidencia: 'Histórico profissional consistente',
        impacto_negocio: 'Pode contribuir imediatamente sem curva de aprendizado significativa'
      },
      {
        ponto: 'Trajetória profissional sólida',
        evidencia: 'Progressão consistente na carreira',
        impacto_negocio: 'Demonstra capacidade de crescimento e adaptação'
      }
    ],
    riscos_mitigacoes: requirements
      .filter(r => ['partial', 'missing'].includes(getEvaluationLevel(r).toLowerCase()) && r.priority?.toLowerCase() === 'essential')
      .slice(0, 2)
      .map(r => ({
        risco: `${r.name || r.requirement} - ${getEvaluationLevel(r) === 'partial' ? 'conhecimento parcial' : 'sem evidências'}`,
        nivel: 'medio' as const,
        mitigacao: 'Pode ser desenvolvido com mentoria e treinamento estruturado',
        tempo_estimado: '2-3 meses'
      })),
    recomendacao_final: {
      decisao: score >= 70 ? 'APROVAR_TRIAGEM' : score >= 50 ? 'MANTER_ESPERA' : 'NAO_PROSSEGUIR',
      justificativa: score >= 70
        ? `O candidato atende ${essentialMet} de ${essentialReqs.length} requisitos essenciais com evidências sólidas. Os gaps identificados são mitigáveis e não impactam a capacidade de contribuição imediata.`
        : score >= 50
        ? `O candidato apresenta potencial, mas gaps em requisitos essenciais requerem avaliação mais aprofundada antes de prosseguir.`
        : `O candidato não atende requisitos mínimos para a posição. Recomenda-se não prosseguir neste momento.`,
      proximos_passos: score >= 70
        ? ['Agendar Quick Screening para validar soft skills e aderência cultural', 'Explorar experiência prática durante a triagem']
        : score >= 50
        ? ['Avaliar experiências adjacentes que possam compensar gaps', 'Considerar para outras vagas mais alinhadas']
        : ['Manter no talent pool para oportunidades futuras']
    }
  }

  const decisionBadge = getDecisionBadge(mockParecer.recomendacao_final?.decisao)

  const handleApprove = async () => {
    if (!onApprove) return
    setIsApproving(true)
    try {
      await onApprove(candidateId, jobId)
      toast.success("Candidato aprovado", { description: `${displayName} foi aprovado para triagem.` })
      onClose?.()
    } catch {
      toast.error("Erro ao aprovar", { description: "Não foi possível aprovar o candidato. Tente novamente." })
    } finally {
      setIsApproving(false)
    }
  }

  const handleReject = async () => {
    if (!onReject) return
    setIsRejecting(true)
    try {
      await onReject(candidateId, jobId)
      toast.success("Candidato reprovado", { description: `${displayName} foi reprovado para esta vaga.` })
      onClose?.()
    } catch {
      toast.error("Erro ao reprovar", { description: "Não foi possível reprovar o candidato. Tente novamente." })
    } finally {
      setIsRejecting(false)
    }
  }

  const isLoading = isApproving || isRejecting

  return {
    isApproving,
    isRejecting,
    isLoading,
    activeSection,
    setActiveSection,
    showAudit,
    setShowAudit,
    score,
    requirements,
    jobTitle,
    displayName,
    sortedRequirements,
    scoreBadge,
    essentialReqs,
    essentialMet,
    importantReqs,
    importantMet,
    desirableReqs,
    desirableMet,
    mockRedFlags,
    mockWhyCandidate,
    mockParecer,
    decisionBadge,
    handleApprove,
    handleReject,
  }
}
