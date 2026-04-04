export interface RubricRequirement {
  requirement: string
  name?: string
  priority: 'essential' | 'important' | 'nice-to-have' | string
  level: 'exceeds' | 'meets' | 'partial' | 'missing' | string
  evidence?: string
  evaluation?: string
  narrative?: string
}

export interface RedFlag {
  type: string
  status: 'ok' | 'warning' | 'critical'
  detail?: string
}

export interface Gap {
  requirement: string
  priority: string
  risk: 'low' | 'medium' | 'high'
  mitigation?: string
  tempo_estimado?: string
}

export interface PontoForteImpacto {
  ponto: string
  evidencia: string
  impacto_negocio: string
}

export interface RiscoMitigacao {
  risco: string
  nivel: 'baixo' | 'medio' | 'alto'
  mitigacao: string
  tempo_estimado?: string
}

export interface ParecerLIA {
  contexto_fit?: string
  pontos_fortes_impacto?: PontoForteImpacto[]
  riscos_mitigacoes?: RiscoMitigacao[]
  recomendacao_final?: {
    decisao?: string
    justificativa?: string
    proximos_passos?: string[]
  }
}

export interface RubricEvaluationData {
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

export interface RubricEvaluationModalProps {
  isOpen: boolean
  onClose: () => void
  evaluation: RubricEvaluationData | null
  candidateId: string
  candidateName?: string
  jobId: string
  onApprove?: (candidateId: string, jobId: string) => Promise<void>
  onReject?: (candidateId: string, jobId: string) => Promise<void>
}

export interface DecisionBadge {
  label: string
  bg: string
  color?: string
  icon: React.ComponentType<{ className?: string }>
}

export interface ScoreBadge {
  label: string
  bg: string
  color?: string
}

export interface RubricStyle {
  bg: string
  border: string
  color?: string
}

export interface PriorityStyle {
  bg: string
  color?: string
}
