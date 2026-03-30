export interface WSIScore {
  dimension: string
  score: number
  label: string
}

export interface InsightCategory {
  type: 'action' | 'analysis' | 'comparison' | 'attention'
  title: string
  description: string
  badge?: string
}

export interface ConversionRate {
  from: string
  to: string
  rate: number
  benchmark?: number
  status: 'good' | 'warning' | 'critical'
}

export interface StageBottleneck {
  stage: string
  avgDays: number
  dropRate: number
  stuckCount: number
}

export interface DemographicDistribution {
  name: string
  count: number
  percentage: number
}

export interface CandidateDemographics {
  cities?: DemographicDistribution[]
  workModels?: DemographicDistribution[]
  genders?: DemographicDistribution[]
  ageRanges?: DemographicDistribution[]
  educationLevels?: DemographicDistribution[]
  experienceYears?: DemographicDistribution[]
}

export interface JobBehavioralCompetency {
  competency: string
  weight: string
}

export interface JobLiaMetrics {
  pipeline_lia: number
  triagens_agendadas: number
  triagens_realizadas: number
  sem_resposta: number
  entrevistas_agendadas: number
  conversionRates?: ConversionRate[]
  bottlenecks?: StageBottleneck[]
  insights?: InsightCategory[]
}

export interface JobInsightData {
  id: string
  code?: string
  title: string
  status: string
  priority?: string
  deadline?: string
  candidates_count?: number
  approved_count?: number
  screening_count?: number
  rejected_count?: number
  performance_score?: number
  avg_time_per_stage?: number
  salary_min?: number
  salary_max?: number
  work_model?: string
  location?: string
  behavioral_competencies?: JobBehavioralCompetency[]
  benefits?: string[]
  days_open?: number
  lia_metrics?: JobLiaMetrics
  candidate_demographics?: CandidateDemographics
}

export interface JobInsightsModalProps {
  isOpen: boolean
  onClose: () => void
  onSendEmail?: (reportData: { jobIds: string[]; reportHtml: string }) => void
  jobs: JobInsightData[]
  aggregatedDemographics?: CandidateDemographics
  conversionRates?: ConversionRate[]
  bottlenecks?: StageBottleneck[]
  insights?: InsightCategory[]
}
