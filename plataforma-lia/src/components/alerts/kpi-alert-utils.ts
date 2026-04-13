export interface KPIAlert {
  id: string
  type: 'critical' | 'warning' | 'info' | 'success'
  category: 'performance' | 'deadline' | 'target' | 'budget' | 'quality'
  title: string
  description: string
  recruiterName: string
  recruiterId: string
  department: string
  metric: string
  currentValue: number
  targetValue: number
  threshold: number
  variance: number
  trend: 'up' | 'down' | 'stable'
  createdAt: Date
  isRead: boolean
  isArchived: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  suggestedActions: string[]
  affectedJobs?: string[]
  estimatedImpact: 'low' | 'medium' | 'high'
}

export interface BackendAlert {
  id: string
  alert_type: string
  severity: string
  status: string
  title: string
  message: string
  user_id?: string
  job_id?: string
  candidate_id?: string
  context?: Record<string, unknown>
  suggested_actions?: string[]
  created_at: string
}

export interface AlertPreference {
  id?: string
  user_id: string
  alert_type: string
  name?: string
  description?: string
  is_enabled: boolean
  threshold?: number
  channels: {
    email: boolean
    bell: boolean
    teams: boolean
    whatsapp: boolean
  }
  cooldown_hours: number
}

export interface AlertRule {
  id: string
  name: string
  metric: string
  operator: '>' | '<' | '=' | '>=' | '<='
  threshold: number
  enabled: boolean
  severity: 'critical' | 'warning' | 'info'
  frequency: 'realtime' | 'daily' | 'weekly'
  departments: string[]
  notifications: {
    email: boolean
    push: boolean
    inApp: boolean
  }
}

export const mapAlertTypeToMetric = (alertType: string): string => {
  const mapping: Record<string, string> = {
    time_to_hire_critical: 'avgTimeToFill',
    conversion_rate_low: 'conversionRate',
    nps_declining: 'npsScore',
    no_hires: 'totalHires',
    quality_score_low: 'qualityOfHireScore'
  }
  return mapping[alertType] || alertType
}

export const getOperatorForType = (alertType: string): string => {
  if (alertType.includes('low') || alertType.includes('declining')) return '<'
  if (alertType.includes('critical') || alertType.includes('high')) return '>'
  return '>'
}

export const getSeverityForType = (alertType: string): string => {
  if (alertType.includes('critical')) return 'critical'
  if (alertType.includes('risk') || alertType.includes('pending')) return 'warning'
  return 'info'
}

export const convertPreferencesToRules = (preferences: AlertPreference[]): AlertRule[] => {
  return preferences.map(pref => ({
    id: pref.alert_type,
    name: pref.name || pref.alert_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    metric: mapAlertTypeToMetric(pref.alert_type),
    operator: getOperatorForType(pref.alert_type) as '>' | '<' | '=' | '>=' | '<=',
    threshold: pref.threshold || 0,
    enabled: pref.is_enabled,
    severity: getSeverityForType(pref.alert_type) as 'critical' | 'warning' | 'info',
    frequency: 'daily' as const,
    departments: ['all'],
    notifications: {
      email: pref.channels.email,
      push: pref.channels.bell,
      inApp: pref.channels.bell
    }
  }))
}

export const getSuggestedActions = (metric: string, _currentValue: number, _threshold: number): string[] => {
  switch (metric) {
    case 'avgTimeToFill':
      return [
        'Revisar processo de entrevistas para otimização',
        'Implementar automação na triagem inicial',
        'Reduzir número de etapas do processo',
        'Agendar reunião com gestores para alinhar requisitos'
      ]
    case 'conversionRate':
      return [
        'Melhorar qualidade do sourcing',
        'Revisar critérios de triagem',
        'Implementar pré-qualificação mais rigorosa',
        'Analisar feedback dos candidatos rejeitados'
      ]
    case 'npsScore':
      return [
        'Coletar feedback detalhado dos candidatos',
        'Melhorar comunicação durante o processo',
        'Revisar experiência do candidato',
        'Implementar follow-up pós-entrevista'
      ]
    case 'totalHires':
      return [
        'Aumentar atividades de sourcing',
        'Revisar requisitos das vagas',
        'Implementar sourcing passivo',
        'Buscar parcerias com universidades'
      ]
    case 'qualityOfHireScore':
      return [
        'Melhorar processo de avaliação técnica',
        'Implementar entrevistas comportamentais',
        'Revisar aderência cultural',
        'Acompanhar onboarding dos novos contratados'
      ]
    default:
      return ['Analisar métrica em detalhes', 'Consultar gestor direto']
  }
}

export const getCategoryFromMetric = (metric: string): KPIAlert['category'] => {
  switch (metric) {
    case 'avgTimeToFill': return 'deadline'
    case 'conversionRate': return 'performance'
    case 'npsScore': return 'quality'
    case 'totalHires': return 'target'
    case 'qualityOfHireScore': return 'quality'
    default: return 'performance'
  }
}

export const getMetricDisplayName = (metric: string): string => {
  switch (metric) {
    case 'avgTimeToFill': return 'Tempo de Preenchimento'
    case 'conversionRate': return 'Taxa de Conversão'
    case 'npsScore': return 'NPS'
    case 'totalHires': return 'Total de Contratações'
    case 'qualityOfHireScore': return 'Score de Qualidade'
    default: return metric
  }
}

export const getPriorityFromSeverity = (severity: string, variance: number): KPIAlert['priority'] => {
  if (severity === 'critical') return variance > 50 ? 'urgent' : 'high'
  if (severity === 'warning') return variance > 25 ? 'high' : 'medium'
  return 'low'
}

export const getAffectedJobs = (_recruiter: Record<string, unknown>): string[] => {
  return [`Vaga ${Math.floor(Math.random() * 100)}`]
}

export const getEstimatedImpact = (_metric: string, variance: number): KPIAlert['estimatedImpact'] => {
  if (variance > 50) return 'high'
  if (variance > 25) return 'medium'
  return 'low'
}

export const defaultAlertRules: AlertRule[] = [
  {
    id: 'tth-critical',
    name: 'Time to Hire Crítico',
    metric: 'avgTimeToFill',
    operator: '>',
    threshold: 45,
    enabled: true,
    severity: 'critical',
    frequency: 'daily',
    departments: ['all'],
    notifications: { email: true, push: true, inApp: true }
  },
  {
    id: 'conversion-low',
    name: 'Taxa de Conversão Baixa',
    metric: 'conversionRate',
    operator: '<',
    threshold: 1.5,
    enabled: true,
    severity: 'warning',
    frequency: 'weekly',
    departments: ['all'],
    notifications: { email: true, push: false, inApp: true }
  },
  {
    id: 'nps-declining',
    name: 'NPS em Declínio',
    metric: 'npsScore',
    operator: '<',
    threshold: 75,
    enabled: true,
    severity: 'warning',
    frequency: 'daily',
    departments: ['all'],
    notifications: { email: false, push: true, inApp: true }
  },
  {
    id: 'no-hires',
    name: 'Sem Contratações',
    metric: 'totalHires',
    operator: '=',
    threshold: 0,
    enabled: true,
    severity: 'critical',
    frequency: 'weekly',
    departments: ['all'],
    notifications: { email: true, push: true, inApp: true }
  },
  {
    id: 'quality-score-low',
    name: 'Score de Qualidade Baixo',
    metric: 'qualityOfHireScore',
    operator: '<',
    threshold: 3.5,
    enabled: true,
    severity: 'warning',
    frequency: 'weekly',
    departments: ['all'],
    notifications: { email: true, push: false, inApp: true }
  }
]
