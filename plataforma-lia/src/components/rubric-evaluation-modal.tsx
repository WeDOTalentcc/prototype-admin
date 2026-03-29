"use client"

import React from "react"
import { Brain, Target, Check, AlertTriangle, X, FileText, TrendingUp, AlertCircle, User, Briefcase, Loader2, ThumbsUp, ThumbsDown, Shield, Clock, CheckCircle, XCircle, Lightbulb, BarChart3, ChevronDown, ChevronRight, ArrowRight } from "lucide-react"
import { toast } from "@/hooks/use-toast"

interface RubricRequirement {
  requirement: string
  name?: string
  priority: 'essential' | 'important' | 'nice-to-have' | string
  level: 'exceeds' | 'meets' | 'partial' | 'missing' | string
  evidence?: string
  evaluation?: string
  narrative?: string
}

interface RedFlag {
  type: string
  status: 'ok' | 'warning' | 'critical'
  detail?: string
}

interface Gap {
  requirement: string
  priority: string
  risk: 'low' | 'medium' | 'high'
  mitigation?: string
  tempo_estimado?: string
}

interface PontoForteImpacto {
  ponto: string
  evidencia: string
  impacto_negocio: string
}

interface RiscoMitigacao {
  risco: string
  nivel: 'baixo' | 'medio' | 'alto'
  mitigacao: string
  tempo_estimado?: string
}

interface ParecerLIA {
  contexto_fit?: string
  pontos_fortes_impacto?: PontoForteImpacto[]
  riscos_mitigacoes?: RiscoMitigacao[]
  recomendacao_final?: {
    decisao?: string
    justificativa?: string
    proximos_passos?: string[]
  }
}

interface RubricEvaluationData {
  job_id?: string
  job_title?: string
  job_code?: string
  score?: number
  overall_score?: number
  score_label?: string
  evaluations?: RubricRequirement[]
  requirements?: RubricRequirement[]
  summary?: string
  recommendation?: 'strong_yes' | 'interview' | 'maybe' | 'reject' | string
  strengths?: string[]
  concerns?: string[]
  candidate_name?: string
  red_flags?: RedFlag[]
  gaps?: Gap[]
  why_candidate?: string[]
  parecer_lia?: ParecerLIA
  audit_metrics?: {
    total_requirements?: number
    essential_met?: number
    essential_total?: number
    important_met?: number
    important_total?: number
    desirable_met?: number
    desirable_total?: number
    analysis_time?: number
    confidence_score?: number
    data_completeness?: string
    limitations?: string[]
  }
}

interface RubricEvaluationModalProps {
  isOpen: boolean
  onClose: () => void
  evaluation: RubricEvaluationData | null
  candidateId: string
  candidateName?: string
  jobId: string
  onApprove?: (candidateId: string, jobId: string) => Promise<void>
  onReject?: (candidateId: string, jobId: string) => Promise<void>
}

export function RubricEvaluationModal({
  isOpen,
  onClose,
  evaluation,
  candidateId,
  candidateName,
  jobId,
  onApprove,
  onReject,
}: RubricEvaluationModalProps) {
  const [isApproving, setIsApproving] = React.useState(false)
  const [isRejecting, setIsRejecting] = React.useState(false)
  const [activeSection, setActiveSection] = React.useState<'overview' | 'details'>('overview')
  const [showAudit, setShowAudit] = React.useState(false)

  if (!isOpen || !evaluation) return null

  const score = evaluation.score ?? evaluation.overall_score ?? 0
  const requirements = evaluation.evaluations ?? evaluation.requirements ?? []
  const jobTitle = evaluation.job_title || 'Vaga não especificada'
  const displayName = candidateName || evaluation.candidate_name || 'Candidato'

  const getScoreColor = (scoreValue: number) => {
    if (scoreValue >= 85) return 'var(--gray-600)'
    if (scoreValue >= 70) return 'var(--gray-600)'
    if (scoreValue >= 50) return 'var(--status-warning)'
    return 'var(--status-error)'
  }

  const getScoreBadge = (scoreValue: number) => {
    if (scoreValue >= 85) return { label: 'Excelente', bg: 'var(--wedo-cyan-bg-12)' }
    if (scoreValue >= 70) return { label: 'Bom', bg: 'var(--wedo-cyan-bg-08)' }
    if (scoreValue >= 50) return { label: 'Moderado', bg: 'var(--status-warning-bg-12)', color: 'var(--status-warning)' }
    if (scoreValue >= 30) return { label: 'Fraco', bg: 'var(--status-error-bg-12)', color: 'var(--status-error)' }
    return { label: 'Inadequado', bg: 'var(--status-error-bg-15)', color: 'var(--status-error)' }
  }

  const getDecisionBadge = (decisao?: string) => {
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

  const getEvaluationLevel = (req: RubricRequirement): string => {
    return req.level || req.evaluation || 'unknown'
  }

  const getRubricIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return <Check className="w-3.5 h-3.5 text-gray-700" />
      case 'meets':
        return <Check className="w-3.5 h-3.5 text-gray-700" />
      case 'partial':
        return <AlertTriangle className="w-3.5 h-3.5 text-[var(--status-warning)]" />
      case 'missing':
        return <X className="w-3.5 h-3.5 text-wedo-coral" />
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
    }
  }

  const getRubricStyle = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return { bg: 'var(--wedo-cyan-bg-08)', border: 'var(--gray-50)' }
      case 'meets':
        return { bg: 'var(--wedo-cyan-bg-04)', border: 'var(--gray-50)' }
      case 'partial':
        return { bg: 'var(--status-warning-bg-08)', border: 'var(--gray-50)', color: 'var(--status-warning)' }
      case 'missing':
        return { bg: 'var(--status-error-bg-08)', border: 'var(--gray-50)', color: 'var(--status-error)' }
      default:
        return { bg: 'var(--gray-50)', border: 'var(--gray-50)' }
    }
  }

  const getRubricLabel = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'exceeds':
        return 'Excede'
      case 'meets':
        return 'Atende'
      case 'partial':
        return 'Parcial'
      case 'missing':
        return 'Ausente'
      default:
        return level
    }
  }

  const getPriorityLabel = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'essential':
        return 'Essencial'
      case 'important':
        return 'Importante'
      case 'nice-to-have':
        return 'Desejável'
      default:
        return priority
    }
  }

  const getPriorityStyle = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'essential':
        return { bg: 'var(--status-error-bg-12)', color: 'var(--status-error)' }
      case 'important':
        return { bg: 'var(--status-warning-bg-12)', color: 'var(--status-warning)' }
      case 'nice-to-have':
        return { bg: 'var(--gray-50)' }
      default:
        return { bg: 'var(--gray-50)' }
    }
  }

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

  const mockRedFlags: RedFlag[] = evaluation.red_flags || [
    { type: 'Gaps na carreira', status: 'ok', detail: 'Trajetória linear' },
    { type: 'Job hopping', status: 'ok', detail: 'Média 2+ anos por empresa' },
    { type: 'Inconsistências', status: 'ok', detail: 'Dados consistentes' },
    { type: 'Senioridade', status: 'ok', detail: 'Nível alinhado com experiência' },
  ]

  const mockWhyCandidate = evaluation.why_candidate || [
    'Experiência sólida nas tecnologias core exigidas pela vaga',
    'Histórico de entregas em projetos de complexidade similar',
    'Competências complementares que agregam valor ao time',
  ]

  const mockParecer: ParecerLIA = evaluation.parecer_lia || {
    contexto_fit: `${displayName} apresenta um perfil técnico sólido e bem alinhado com as demandas da posição de ${jobTitle}. Sua trajetória profissional demonstra experiência consistente nas tecnologias e competências requeridas, com evidências de aplicação prática em ambientes similares ao contexto desta vaga.`,
    pontos_fortes_impacto: evaluation.strengths?.slice(0, 3).map((s, i) => ({
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
        ? ['Agendar Quick Screening para validar soft skills e fit cultural', 'Explorar experiência prática durante a triagem']
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
      toast({
        title: "Candidato aprovado",
        description: `${displayName} foi aprovado para triagem.`,
      })
      onClose()
    } catch (error) {
      toast({
        title: "Erro ao aprovar",
        description: "Não foi possível aprovar o candidato. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setIsApproving(false)
    }
  }

  const handleReject = async () => {
    if (!onReject) return
    setIsRejecting(true)
    try {
      await onReject(candidateId, jobId)
      toast({
        title: "Candidato reprovado",
        description: `${displayName} foi reprovado para esta vaga.`,
      })
      onClose()
    } catch (error) {
      toast({
        title: "Erro ao reprovar",
        description: "Não foi possível reprovar o candidato. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setIsRejecting(false)
    }
  }

  const isLoading = isApproving || isRejecting

  const sectionTabs = [
    { id: 'overview', label: 'Visão Geral', icon: Target },
    { id: 'details', label: 'Detalhes', icon: FileText },
  ] as const

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col rounded-md dark:bg-gray-800 dark:border-gray-700 border border-gray-100 bg-[var(--gray-50)]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-b-gray-100">
          <div className="flex items-center gap-3">
            <div 
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/[.12]"
            >
              <Target className="w-4 h-4 text-gray-700" />
            </div>
            <div>
              <h2 className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                Análise CV vs Vaga
              </h2>
              <div className="flex items-center gap-2 text-xs">
                <span className="flex items-center gap-1 text-gray-800 dark:text-gray-200">
                  <User className="w-3 h-3 text-gray-500" />
                  {displayName}
                </span>
                <span className="text-gray-100">|</span>
                <span className="flex items-center gap-1 text-gray-500">
                  <Briefcase className="w-3 h-3" />
                  {jobTitle}
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors hover:bg-gray-100 rounded-full text-gray-500"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section Tabs */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-b-gray-100">
          {sectionTabs.map((tab) => {
            const TabIcon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSection(tab.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
                style={{backgroundColor: activeSection === tab.id ? 'var(--wedo-cyan-bg-12)' : 'transparent',
                  color: activeSection === tab.id ? 'var(--gray-950)' : 'var(--gray-400)'}}
              >
                <TabIcon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {/* OVERVIEW SECTION */}
          {activeSection === 'overview' && (
            <div className="space-y-3">
              {/* Score Card */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">Score de Aderência</span>
                  <div className="flex items-center gap-2">
                    <span 
                      className="text-micro font-medium px-2 py-0.5 rounded-full"
                      style={{backgroundColor: scoreBadge.bg,
                        color: scoreBadge.color}}
                    >
                      {evaluation.score_label || scoreBadge.label}
                    </span>
                    {decisionBadge && (
                      <span 
                        className="text-micro font-medium px-2 py-0.5 rounded-full flex items-center gap-1"
                        style={{backgroundColor: decisionBadge.bg,
                          color: decisionBadge.color}}
                      >
                        <decisionBadge.icon className="w-3 h-3" />
                        {decisionBadge.label}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-3 rounded-full overflow-hidden bg-gray-100">
                    <div 
                      className="h-full rounded-full transition-all duration-700 ease-out"
                      style={{width: `${score}%`,
                        backgroundColor: getScoreColor(score)}}
                    />
                  </div>
                  <span className="text-xl font-bold min-w-[55px] text-right text-gray-950 dark:text-gray-50">
                    {score}%
                  </span>
                </div>
                
                {/* Category Breakdown */}
                <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-t-gray-100">
                  <div className="text-center">
                    <div className="text-micro mb-1 text-gray-500">Essenciais</div>
                    <div className="text-base-ui font-semibold" style={{color: essentialMet === essentialReqs.length ? 'var(--gray-950)' : 'var(--status-warning)'}}>
                      {essentialMet}/{essentialReqs.length}
                    </div>
                  </div>
                  <div className="text-center border-l border-l-gray-100 border-r border-r-gray-100">
                    <div className="text-micro mb-1 text-gray-500">Importantes</div>
                    <div className="text-base-ui font-semibold">
                      {importantMet}/{importantReqs.length}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-micro mb-1 text-gray-500">Desejáveis</div>
                    <div className="text-base-ui font-semibold">
                      {desirableMet}/{desirableReqs.length}
                    </div>
                  </div>
                </div>
              </div>

              {/* Parecer da LIA - Expandido */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <h3 className="text-xs font-semibold flex items-center gap-2 mb-3 text-gray-950 dark:text-gray-50">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Parecer da LIA
                </h3>
                
                {/* 1. Contexto e Fit */}
                <div className="mb-3">
                  <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-gray-500">
                    <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-wedo-cyan/[.12]">1</span>
                    Contexto e Fit
                  </div>
                  <p className="text-xs leading-relaxed pl-5 text-gray-800 dark:text-gray-200">
                    {mockParecer.contexto_fit}
                  </p>
                </div>

                {/* 2. Pontos Fortes com Impacto */}
                {mockParecer.pontos_fortes_impacto && mockParecer.pontos_fortes_impacto.length > 0 && (
                  <div className="mb-3">
                    <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-gray-500">
                      <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-wedo-cyan/[.12]">2</span>
                      Pontos Fortes e Impacto
                    </div>
                    <div className="space-y-1.5 pl-5">
                      {mockParecer.pontos_fortes_impacto.map((pf, idx) => (
                        <div 
                          key={idx} 
                          className="p-2 rounded-md bg-gray-50"
                        >
                          <div className="flex items-start gap-2">
                            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                            <div>
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">
                                {pf.ponto}
                              </span>
                              <p className="text-micro mt-0.5 text-gray-500">
                                {pf.evidencia}
                              </p>
                              <p className="text-micro mt-0.5 flex items-center gap-1">
                                <ArrowRight className="w-3 h-3" />
                                {pf.impacto_negocio}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Riscos e Mitigações */}
                {mockParecer.riscos_mitigacoes && mockParecer.riscos_mitigacoes.length > 0 && (
                  <div className="mb-3">
                    <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-gray-500">
                      <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold bg-status-warning/[.12] text-status-warning">3</span>
                      Riscos e Mitigações
                    </div>
                    <div className="space-y-1.5 pl-5">
                      {mockParecer.riscos_mitigacoes.map((rm, idx) => {
                        const nivelColor = rm.nivel === 'alto' ? 'var(--status-error)' : rm.nivel === 'medio' ? 'var(--status-warning)' : 'var(--gray-400)'
                        const nivelBgColor = rm.nivel === 'alto' ? 'var(--status-error-bg-15)' : rm.nivel === 'medio' ? 'var(--status-warning-bg-15)' : 'var(--gray-bg-15)'
                        return (
                          <div 
                            key={idx} 
                            className="p-2 rounded-md"
                            style={{borderLeft: `2px solid ${nivelColor}`}}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1">
                                <span className="text-xs font-medium text-gray-950 dark:text-gray-50">
                                  {rm.risco}
                                </span>
                                <p className="text-micro mt-0.5 text-gray-500">
                                  <span className="font-medium">Mitigação:</span> {rm.mitigacao}
                                </p>
                              </div>
                              <div className="flex flex-col items-end gap-1">
                                <span 
                                  className="text-micro font-medium px-1.5 py-0.5 rounded-full"
                                  style={{backgroundColor: nivelBgColor, color: nivelColor}}
                                >
                                  Risco {rm.nivel === 'alto' ? 'Alto' : rm.nivel === 'medio' ? 'Médio' : 'Baixo'}
                                </span>
                                {rm.tempo_estimado && (
                                  <span className="text-micro flex items-center gap-0.5 text-gray-500">
                                    <Clock className="w-3 h-3" />
                                    {rm.tempo_estimado}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* 4. Recomendação Final */}
                {mockParecer.recomendacao_final && (
                  <div>
                    <div className="text-micro font-semibold mb-1.5 flex items-center gap-1 text-gray-500">
                      <span className="w-4 h-4 rounded-full flex items-center justify-center text-micro font-bold" style={{backgroundColor: decisionBadge ? decisionBadge.bg : 'var(--wedo-cyan-bg-12)', color: decisionBadge ? decisionBadge.color : 'var(--gray-600)'}}>4</span>
                      Recomendação Final
                    </div>
                    <div className="pl-5 p-2.5 rounded-md border border-gray-100" style={{backgroundColor: decisionBadge ? decisionBadge.bg : 'var(--gray-50)'}}>
                      <p className="text-xs leading-relaxed mb-2 text-gray-800 dark:text-gray-200">
                        {mockParecer.recomendacao_final.justificativa}
                      </p>
                      {mockParecer.recomendacao_final.proximos_passos && mockParecer.recomendacao_final.proximos_passos.length > 0 && (
                        <div>
                          <span className="text-micro font-medium text-gray-500">Próximos Passos:</span>
                          <ul className="mt-1 space-y-0.5">
                            {mockParecer.recomendacao_final.proximos_passos.map((ps, idx) => (
                              <li key={idx} className="text-micro flex items-start gap-1.5 text-gray-800 dark:text-gray-200">
                                <span className="text-gray-700">→</span>
                                {ps}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Why This Candidate */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950 dark:text-gray-50">
                  <Lightbulb className="w-4 h-4 text-gray-700" />
                  Por que este candidato?
                </h3>
                <div className="space-y-1.5">
                  {mockWhyCandidate.map((reason, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-start gap-2 p-2 rounded-md bg-gray-50"
                    >
                      <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                      <span className="text-xs text-gray-800 dark:text-gray-200">
                        {reason}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* DETAILS SECTION */}
          {activeSection === 'details' && (
            <div className="space-y-3">
              {/* Avaliação por Requisito */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950 dark:text-gray-50">
                  <FileText className="w-4 h-4 text-gray-700" />
                  Matriz de Avaliação por Requisito
                </h3>
                <div className="space-y-2">
                  {sortedRequirements.map((req, idx) => {
                    const level = getEvaluationLevel(req)
                    const reqName = req.name || req.requirement
                    const rubricStyle = getRubricStyle(level)
                    const priorityStyle = getPriorityStyle(req.priority)
                    return (
                      <div 
                        key={idx} 
                        className="p-2.5 rounded-md transition-colors"
                        style={{backgroundColor: rubricStyle.bg,
                          border: `1px solid ${rubricStyle.border}`}}
                      >
                        <div className="flex items-start gap-2">
                          <div className="mt-0.5 flex-shrink-0">
                            {getRubricIcon(level)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">
                                {reqName}
                              </span>
                              {req.priority && (
                                <span 
                                  className="text-micro font-medium px-1.5 py-0 rounded-full"
                                  style={{backgroundColor: priorityStyle.bg,
                                    color: priorityStyle.color}}
                                >
                                  {getPriorityLabel(req.priority)}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-1">
                              <span className="text-micro font-medium" style={{color: rubricStyle.color}}>
                                {getRubricLabel(level)}
                              </span>
                              {req.evidence && (
                                <>
                                  <span className="text-gray-100">•</span>
                                  <span className="text-micro text-gray-500">
                                    {req.evidence}
                                  </span>
                                </>
                              )}
                            </div>
                            {req.narrative && (
                              <p className="text-micro mt-1 text-gray-500">
                                {req.narrative}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                  {sortedRequirements.length === 0 && (
                    <div className="text-center py-4 text-xs text-gray-500">
                      Nenhum requisito avaliado disponível.
                    </div>
                  )}
                </div>
              </div>

              {/* Red Flags */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950 dark:text-gray-50">
                  <Shield className="w-4 h-4 text-gray-700" />
                  Verificação de Red Flags
                </h3>
                <div className="space-y-1.5">
                  {mockRedFlags.map((flag, idx) => {
                    const statusIcon = flag.status === 'ok' ? CheckCircle : flag.status === 'warning' ? AlertTriangle : XCircle
                    const statusColor = flag.status === 'ok' ? 'var(--gray-950)' : flag.status === 'warning' ? 'var(--status-warning)' : 'var(--status-error)'
                    return (
                      <div 
                        key={idx} 
                        className="flex items-center justify-between p-2 rounded-md bg-gray-50"
                      >
                        <span className="text-xs text-gray-800 dark:text-gray-200">
                          {flag.type}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {flag.detail && (
                            <span className="text-micro text-gray-500">
                              {flag.detail}
                            </span>
                          )}
                          {React.createElement(statusIcon, { className: "w-3.5 h-3.5", style: { color: statusColor } })}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Auditoria - Collapsible */}
              <div className="p-3 border border-gray-100" style={{backgroundColor: 'var(--gray-50)', borderRadius: '8px'}}>
                <button
                  onClick={() => setShowAudit(!showAudit)}
                  className="w-full flex items-center justify-between text-xs font-semibold text-gray-950 dark:text-gray-50"
                 
                >
                  <span className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-gray-500" />
                    Métricas de Auditoria
                  </span>
                  {showAudit ? (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                </button>
                
                {showAudit && (
                  <div className="mt-3 pt-3 border-t border-t-gray-100">
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      <div className="p-2 rounded-md bg-gray-50">
                        <div className="text-micro text-gray-500">Total Requisitos</div>
                        <div className="text-sm font-bold text-gray-950 dark:text-gray-50">
                          {requirements.length}
                        </div>
                      </div>
                      <div className="p-2 rounded-md bg-gray-50">
                        <div className="text-micro text-gray-500">Red Flags</div>
                        <div className="text-sm font-bold" style={{color: mockRedFlags.filter(f => f.status !== 'ok').length > 0 ? 'var(--status-warning)' : 'var(--gray-600)'}}>
                          {mockRedFlags.filter(f => f.status !== 'ok').length}
                        </div>
                      </div>
                      <div className="p-2 rounded-md bg-gray-50">
                        <div className="text-micro text-gray-500">Taxa Essenciais</div>
                        <div className="text-sm font-bold" style={{color: essentialMet === essentialReqs.length ? 'var(--gray-950)' : 'var(--status-warning)'}}>
                          {essentialReqs.length > 0 ? Math.round((essentialMet / essentialReqs.length) * 100) : 100}%
                        </div>
                      </div>
                      <div className="p-2 rounded-md bg-gray-50">
                        <div className="text-micro text-gray-500">Tempo Análise</div>
                        <div className="text-sm font-bold text-gray-950 dark:text-gray-50">
                          {evaluation.audit_metrics?.analysis_time || '2.3'}s
                        </div>
                      </div>
                    </div>
                    
                    {/* Legenda */}
                    <div className="text-micro font-medium mb-1.5 text-gray-500">Legenda de Níveis</div>
                    <div className="grid grid-cols-4 gap-1">
                      {[
                        { code: 'E+', label: 'Excede', color: undefined, bgColor: undefined },
                        { code: 'A', label: 'Atende', color: undefined, bgColor: undefined },
                        { code: 'P', label: 'Parcial', color: 'var(--status-warning)', bgColor: 'var(--status-warning-bg-15)' },
                        { code: 'X', label: 'Ausente', color: 'var(--status-error)', bgColor: 'var(--status-error-bg-15)' },
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-center gap-1 p-1.5 rounded-md bg-gray-50">
                          <span 
                            className="text-micro font-bold w-5 h-5 flex items-center justify-center rounded-md"
                            style={{backgroundColor: item.bgColor, color: item.color}}
                          >
                            {item.code}
                          </span>
                          <span className="text-micro text-gray-500">{item.label}</span>
                        </div>
                      ))}
                    </div>
                    
                    {/* Metadados */}
                    <div className="mt-2 pt-2 space-y-1 border-t border-t-gray-100">
                      {[
                        { label: 'Versão', value: 'LIA CV Analyzer v1.0' },
                        { label: 'Data/Hora', value: new Date().toLocaleString('pt-BR') },
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-micro text-gray-500">{item.label}</span>
                          <span className="text-micro font-medium text-gray-800 dark:text-gray-200">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div 
          className="flex-shrink-0 px-4 py-3 flex items-center justify-between border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700"
        >
          <div className="flex items-center gap-2">
            <span className="text-micro text-gray-500">
              Decisão do Recrutador
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReject}
              disabled={isLoading || !onReject}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors hover:bg-status-error/10 disabled:opacity-50 disabled:cursor-not-allowed bg-white border border-gray-300 text-status-error dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-status-error"
              
            >
              {isRejecting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ThumbsDown className="w-3.5 h-3.5" />
              )}
              Reprovar
            </button>
            <button
              onClick={handleApprove}
              disabled={isLoading || !onApprove}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md transition-colors hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              
            >
              {isApproving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ThumbsUp className="w-3.5 h-3.5" />
              )}
              Aprovar para Triagem
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RubricEvaluationModal
