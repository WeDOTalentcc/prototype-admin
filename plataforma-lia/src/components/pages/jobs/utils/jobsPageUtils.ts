import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"
import type { Job, JobFilters } from "@/components/jobs"
import type { JobVacancy } from "@/services/lia-api"
import { getJobSeniority } from "@/lib/jobs/seniority"
import { formatJobLocation } from "@/lib/jobs/location"
import { READINESS_STAGES_ORDER, type ReadinessStage } from "@/services/lia-api/readiness-api"

const READINESS_STAGE_RANK: Record<string, number> = READINESS_STAGES_ORDER.reduce(
  (acc, stage, index) => {
    acc[stage] = index
    return acc
  },
  {} as Record<string, number>,
)

const STATUS_RANK: Record<string, number> = [
  'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta',
  'Paralisada', 'Interna', 'Rascunho',
  'Fechada (preenchida)', 'Fechada (expirada)',
  'Cancelada', 'Concluída', 'Arquivada',
].reduce((acc, status, index) => {
  acc[status] = index
  return acc
}, {} as Record<string, number>)

const SCREENING_STATUS_RANK: Record<string, number> = {
  active: 0,
  paused: 1,
  not_started: 2,
  completed: 3,
  not_configured: 4,
}

function compareNumbers(
  a: number | null | undefined,
  b: number | null | undefined,
  direction: "asc" | "desc",
): number {
  const aMissing = a === null || a === undefined || Number.isNaN(a)
  const bMissing = b === null || b === undefined || Number.isNaN(b)
  if (aMissing && bMissing) return 0
  if (aMissing) return 1
  if (bMissing) return -1
  if (a === b) return 0
  return direction === "asc" ? (a as number) - (b as number) : (b as number) - (a as number)
}

function compareStrings(
  a: string | null | undefined,
  b: string | null | undefined,
  direction: "asc" | "desc",
): number {
  const aVal = (a ?? "").trim()
  const bVal = (b ?? "").trim()
  if (!aVal && !bVal) return 0
  if (!aVal) return 1
  if (!bVal) return -1
  const cmp = aVal.localeCompare(bVal, undefined, { sensitivity: "base", numeric: true })
  return direction === "asc" ? cmp : -cmp
}

function compareDateStrings(
  a: string | null | undefined,
  b: string | null | undefined,
  direction: "asc" | "desc",
): number {
  const aTime = a ? new Date(a).getTime() : NaN
  const bTime = b ? new Date(b).getTime() : NaN
  return compareNumbers(
    Number.isNaN(aTime) ? null : aTime,
    Number.isNaN(bTime) ? null : bTime,
    direction,
  )
}

function compareRanks(
  aRank: number | undefined,
  bRank: number | undefined,
  direction: "asc" | "desc",
): number {
  return compareNumbers(
    aRank === undefined ? null : aRank,
    bRank === undefined ? null : bRank,
    direction,
  )
}

export function compareJobsByColumn(
  a: Job,
  b: Job,
  column: string | null,
  direction: "asc" | "desc",
): number {
  if (!column) return 0
  switch (column) {
    case "prontidao": {
      const aStage = a.readinessStage as ReadinessStage | undefined
      const bStage = b.readinessStage as ReadinessStage | undefined
      return compareRanks(
        aStage ? READINESS_STAGE_RANK[aStage] : undefined,
        bStage ? READINESS_STAGE_RANK[bStage] : undefined,
        direction,
      )
    }
    case "id":
      return compareNumbers(a.id, b.id, direction)
    case "vaga":
      return compareStrings(a.title, b.title, direction)
    case "candidatos":
      return compareNumbers(a.funnel?.total ?? 0, b.funnel?.total ?? 0, direction)
    case "status":
      return compareRanks(STATUS_RANK[a.status], STATUS_RANK[b.status], direction)
    case "screeningStatus":
      return compareRanks(
        a.screeningStatus ? SCREENING_STATUS_RANK[a.screeningStatus] : undefined,
        b.screeningStatus ? SCREENING_STATUS_RANK[b.screeningStatus] : undefined,
        direction,
      )
    case "recrutador":
      return compareStrings(a.recruiter, b.recruiter, direction)
    case "gestor":
      return compareStrings(a.manager, b.manager, direction)
    case "prazoTriagem":
      return compareDateStrings(a.deadlineScreening, b.deadlineScreening, direction)
    case "prazoShortlist":
      return compareDateStrings(a.deadlineShortlist, b.deadlineShortlist, direction)
    case "prazoEncerramento":
      return compareDateStrings(a.deadlineClosing ?? a.deadline, b.deadlineClosing ?? b.deadline, direction)
    default:
      return 0
  }
}

export function sortJobsByColumn(
  jobs: Job[],
  column: string | null,
  direction: "asc" | "desc",
): Job[] {
  if (!column) return jobs
  return [...jobs].sort((a, b) => compareJobsByColumn(a, b, column, direction))
}

export interface DashboardStats {
  total: number
  ativas: number
  urgentes: number
  paralisadas: number
  concluidas: number
  canceladas: number
  noFunil: number
  entrevistasRecentes: number
  ofertas: number
  ttfMedio: number
  taxaConversao: number
  atRisco: number
  pipelineVazio: number
  deadlineProximo: number
  porDepartamento: Record<string, number>
  tendenciaSemanal: unknown[]
  insights: unknown[]
}

interface InterviewStageRecord {
  order?: number
  stageName?: string
  stage_name?: string
  name?: string
}

export function convertBackendJobToFrontend(jv: JobVacancy, index: number): Job {
  const funnelData = (jv as unknown as Record<string, unknown>).funnel_data as Record<string, number> | undefined || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }

  const stageMapping: Record<string, Job['stage']> = {
    'Planejamento': 'Planejamento',
    'Aprovação': 'Aprovação',
    'Publicada': 'Publicada',
    'Triagem': 'Triagem',
    'Entrevistas': 'Entrevistas',
    'Finalização': 'Finalização',
    'Encerrada': 'Encerrada'
  }

  const raw = jv as unknown as Record<string, unknown>
  const liaMetricsRaw = raw.lia_metrics as Record<string, number> | undefined
  const salaryRange = raw.salary_range as Record<string, number> | undefined
  const interviewStages = (raw.interview_stages as InterviewStageRecord[] | undefined) || []

  return {
    id: index + 1,
    jobId: `WDT-${jv.id.slice(0, 8).toUpperCase()}`,
    backendId: jv.id,
    title: jv.title,
    department: jv.department || 'Geral',
    location: formatJobLocation(jv.location) || '',
    workModel: (raw.work_model as Job['workModel']) || 'híbrido',
    type: (raw.employment_type as string) || 'CLT',
    seniority: (raw.seniority_level as string) || (raw.seniority as string) || undefined,
    salary: salaryRange ? `${formatBRL(Number(salaryRange.min ?? 0))} - ${formatBRL(Number(salaryRange.max ?? 0))}` : 'A combinar',
    benefits: (raw.benefits as string[]) || [],
    status: (jv.status as Job['status']) || 'Rascunho',
    stage: stageMapping[(raw.stage as string) || ''] || 'Triagem',
    openDate: (raw.open_date as string)?.split('T')[0] || (raw.created_at as string)?.split('T')[0] || new Date().toISOString().split('T')[0],
    deadline: (raw.deadline as string)?.split('T')[0] || undefined,
    description: jv.description || '',
    requirements: (raw.requirements as string[]) || [],
    manager: (raw.manager as string) || 'Não definido',
    managerEmail: (raw.manager_email as string) || '',
    recruiter: (raw.recruiter as string) || 'Não definido',
    recruiterEmail: (raw.recruiter_email as string) || '',
    priority: (raw.priority as Job['priority']) || 'média',
    funnel: {
      total: funnelData.total || 0,
      screening: funnelData.screening || 0,
      interview: funnelData.interview || 0,
      final: funnelData.final || 0,
      hired: funnelData.hired || 0
    },
    liaMetrics: liaMetricsRaw ? {
      pipeline_lia: liaMetricsRaw.pipeline_lia || 0,
      triagens_agendadas: liaMetricsRaw.triagens_agendadas || 0,
      triagens_realizadas: liaMetricsRaw.triagens_realizadas || 0,
      sem_resposta: liaMetricsRaw.sem_resposta || 0,
      entrevistas_agendadas: liaMetricsRaw.entrevistas_agendadas || 0
    } : undefined,
    publishedLinkedIn: (raw.published_linkedin as boolean) || false,
    publishedWebsite: (raw.published_website as boolean) || false,
    isConfidential: (raw.is_confidential as boolean) || false,
    visibility: (raw.visibility as Job['visibility']) || 'public',
    nps: (raw.nps as number) || 0,
    budget: (raw.budget as number) || undefined,
    budgetUsed: (raw.budget_used as number) || undefined,
    nextActions: (raw.next_actions as string[]) || [],
    urgencyLevel: ((raw.urgency_level as number) || 3) as 1 | 2 | 3 | 4 | 5,
    approvalStatus: ((raw.approval_status as string) || 'pendente') as 'pendente' | 'aprovada' | 'rejeitada',
    tags: (raw.tags as string[]) || [],
    technicalRequirements: (raw.technical_requirements as Record<string, unknown>[]) || [],
    languages: (raw.languages as Record<string, unknown>[]) || [],
    behavioralCompetencies: (raw.behavioral_competencies as Record<string, unknown>[]) || [],
    screeningQuestions: (raw.screening_questions as Job['screeningQuestions']) || [],
    interviewStages: interviewStages as Job['interviewStages'],
    hiringProcess: interviewStages.length > 0
      ? [...interviewStages]
          .sort((a, b) => (a.order || 0) - (b.order || 0))
          .map((s) => s.stageName || s.stage_name || s.name || '')
          .filter((n: string) => n)
      : ((raw.hiring_process as string[]) || []),
    salaryRange: salaryRange as Job['salaryRange'],
    organizationalStructure: raw.organizational_structure as Job['organizationalStructure'],
    timeline: raw.timeline as Job['timeline'],
    governanceRules: raw.governance_rules as Job['governanceRules'],
    whatsappTemplateType: raw.whatsapp_template_type as Job['whatsappTemplateType'],
    targetSector: raw.target_sector as string | undefined,
    targetSegment: raw.target_segment as string | undefined,
    conversationId: raw.conversation_id as string | undefined,
    screeningConfig: raw.screening_config as Job['screeningConfig'],
    screeningStatus: (raw.screening_status as Job['screeningStatus']) || (raw.screening_config ? 'not_started' : 'not_configured'),
    deadlineScreening: raw.deadline_screening as string | undefined,
    deadlineShortlist: raw.deadline_shortlist as string | undefined,
    deadlineClosing: raw.deadline_closing as string | undefined,
    eligibilityQuestions: (raw.eligibility_questions as Job['eligibilityQuestions']) || [],
    confidentialityConfig: raw.confidentiality_config as Job['confidentialityConfig'],
    enrichedJd: raw.enriched_jd as Job['enrichedJd'],
    isAffirmative: (raw.is_affirmative as boolean) || false,
    createdAt: raw.created_at as string | undefined,
    updatedAt: raw.updated_at as string | undefined,
    publishedAt: (raw.published_at as string) || (raw.last_published_at as string) || undefined,
    closedAt: raw.closed_at as string | undefined,
    createdByEmail: raw.created_by_email as string | undefined,
  }
}

export function convertBackendJobSimple(jv: Record<string, unknown>, index: number): Job {
  const funnelData = (jv.funnel_data as Record<string, number>) || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
  const stageMapping: Record<string, Job['stage']> = {
    'Planejamento': 'Planejamento', 'Aprovação': 'Aprovação', 'Publicada': 'Publicada',
    'Triagem': 'Triagem', 'Entrevistas': 'Entrevistas', 'Finalização': 'Finalização', 'Encerrada': 'Encerrada'
  }
  return {
    id: index + 1,
    backendId: jv.id as string,
    jobId: `WDT-${(jv.id as string).slice(0, 8).toUpperCase()}`,
    title: jv.title as string,
    department: (jv.department as string) || 'Geral',
    location: formatJobLocation(jv.location as Parameters<typeof formatJobLocation>[0]) || '',
    workModel: (jv.work_model as Job['workModel']) || 'híbrido',
    type: (jv.employment_type as string) || 'CLT',
    seniority: (jv.seniority_level as string) || (jv.seniority as string) || undefined,
    salary: jv.salary_range ? `${formatBRL(Number((jv.salary_range as Record<string, number>).min ?? 0))} - ${formatBRL(Number((jv.salary_range as Record<string, number>).max ?? 0))}` : 'A combinar',
    status: (jv.status as Job['status']) || 'Rascunho',
    stage: stageMapping[(jv.stage as string) || ''] || 'Triagem',
    openDate: (jv.open_date as string)?.split('T')[0] || (jv.created_at as string)?.split('T')[0] || new Date().toISOString().split('T')[0],
    description: (jv.description as string) || '',
    requirements: (jv.requirements as string[]) || [],
    manager: (jv.manager as string) || 'Não definido',
    managerEmail: '',
    recruiter: (jv.recruiter as string) || 'Não definido',
    recruiterEmail: '',
    priority: (jv.priority as Job['priority']) || 'média',
    funnel: { total: funnelData.total || 0, screening: funnelData.screening || 0, interview: funnelData.interview || 0, final: funnelData.final || 0, hired: funnelData.hired || 0 },
    benefits: [],
    publishedLinkedIn: false,
    publishedWebsite: false,
    isConfidential: false,
    nps: 0,
    nextActions: [],
    urgencyLevel: 3 as 1 | 2 | 3 | 4 | 5,
    approvalStatus: 'pendente' as const,
    tags: (jv.tags as string[]) || [],
    conversationId: jv.conversation_id as string | undefined,
    createdAt: jv.created_at as string | undefined,
  } as Job
}

export function computeFallbackStats(jobs: Job[]): DashboardStats {
  return {
    total: jobs.length,
    ativas: jobs.filter(job => job.status === 'Ativa').length,
    urgentes: jobs.filter(job => job.urgencyLevel >= 4).length,
    paralisadas: jobs.filter(job => job.status === 'Paralisada').length,
    concluidas: jobs.filter(job => job.status === 'Concluída').length,
    canceladas: jobs.filter(job => job.status === 'Cancelada').length,
    noFunil: jobs.reduce((sum, job) => sum + (job.funnel?.total || 0), 0),
    entrevistasRecentes: 0,
    ofertas: jobs.filter(job => (job.stage as string) === 'Oferta').length,
    ttfMedio: 0,
    taxaConversao: 0,
    atRisco: 0,
    pipelineVazio: 0,
    deadlineProximo: 0,
    porDepartamento: {},
    tendenciaSemanal: [],
    insights: [],
  }
}

export function organizeJobsByStatus(jobs: Job[]) {
  const statusOrder = [
    'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta',
    'Paralisada', 'Interna', 'Rascunho',
    'Fechada (preenchida)', 'Fechada (expirada)',
    'Cancelada', 'Concluída', 'Arquivada'
  ] as const

  const grouped: Record<string, Job[]> = {}
  for (const s of statusOrder) grouped[s] = []
  jobs.forEach(job => {
    if (grouped[job.status]) grouped[job.status].push(job)
  })

  return { statusOrder, grouped }
}

export interface AdvancedFilters {
  job_titles: string[]
  departments: string[]
  locations: string[]
  work_models: string[]
  job_types: string[]
  seniority_levels: string[]
  salary_ranges: string[]
  status: string[]
  stages: string[]
  priorities: string[]
  managers: string[]
  benefits: string[]
  requirements: string[]
  industries: string[]
  budget_ranges: string[]
  urgency_levels: string[]
  contract_duration: string[]
  team_size: string[]
  [key: string]: string[]
}

export const EMPTY_ADVANCED_FILTERS: AdvancedFilters = {
  job_titles: [], departments: [], locations: [], work_models: [],
  job_types: [], seniority_levels: [], salary_ranges: [], status: [],
  stages: [], priorities: [], managers: [], benefits: [],
  requirements: [], industries: [], budget_ranges: [],
  urgency_levels: [], contract_duration: [], team_size: []
}

interface TechReqLike { technology?: string; category?: string }
interface LangLike { language?: string }
interface CompetencyLike { competency?: string }

export function filterJobs(
  allJobs: Job[],
  activeFilter: string,
  selectedStatusFilter: string,
  searchTerm: string,
  booleanSearch: string,
  advancedFilters: AdvancedFilters,
  jobFilters: JobFilters,
  pinnedJobs: Set<number>
): Job[] {
  return allJobs.filter(job => {
    let matchesActiveFilter = true
    if (activeFilter === 'ativas') matchesActiveFilter = job.status === 'Ativa'
    else if (activeFilter === 'urgentes') matchesActiveFilter = job.urgencyLevel >= 4
    else if (activeFilter === 'paralisadas') matchesActiveFilter = job.status === 'Paralisada'
    else if (activeFilter === 'concluidas') matchesActiveFilter = job.status === 'Concluída'
    else if (activeFilter === 'canceladas') matchesActiveFilter = job.status === 'Cancelada'
    if (!matchesActiveFilter) return false

    let matchesStatus = true
    if (selectedStatusFilter !== 'todas') matchesStatus = job.status === selectedStatusFilter

    const searchLower = searchTerm.toLowerCase()
    let matchesSearch = searchTerm === "" ||
      job.jobId.toLowerCase().includes(searchLower) ||
      job.title.toLowerCase().includes(searchLower) ||
      job.department.toLowerCase().includes(searchLower) ||
      job.location.toLowerCase().includes(searchLower) ||
      job.type.toLowerCase().includes(searchLower) ||
      (getJobSeniority(job)?.toLowerCase().includes(searchLower) ?? false) ||
      job.salary.toLowerCase().includes(searchLower) ||
      job.description.toLowerCase().includes(searchLower) ||
      job.manager.toLowerCase().includes(searchLower) ||
      job.managerEmail.toLowerCase().includes(searchLower) ||
      job.recruiter.toLowerCase().includes(searchLower) ||
      job.recruiterEmail.toLowerCase().includes(searchLower) ||
      job.requirements.some(req => req.toLowerCase().includes(searchLower)) ||
      job.benefits.some(benefit => benefit.toLowerCase().includes(searchLower)) ||
      (job.tags || []).some(tag => tag.toLowerCase().includes(searchLower)) ||
      (job.technicalRequirements as TechReqLike[] || []).some((tr) =>
        tr.technology?.toLowerCase().includes(searchLower) ||
        tr.category?.toLowerCase().includes(searchLower)
      ) ||
      (job.languages as LangLike[] || []).some((lang) =>
        lang.language?.toLowerCase().includes(searchLower)
      ) ||
      (job.behavioralCompetencies as CompetencyLike[] || []).some((bc) =>
        bc.competency?.toLowerCase().includes(searchLower)
      ) ||
      (job.targetSector || '').toLowerCase().includes(searchLower) ||
      (job.targetSegment || '').toLowerCase().includes(searchLower) ||
      job.status.toLowerCase().includes(searchLower) ||
      job.priority.toLowerCase().includes(searchLower) ||
      job.stage.toLowerCase().includes(searchLower)

    if (booleanSearch.trim()) {
      const booleanLower = booleanSearch.toLowerCase()
      const jobText = [
        job.title, job.department, job.location, job.type,
        getJobSeniority(job) ?? '', job.description, job.manager,
        ...job.requirements, ...job.benefits
      ].join(' ').toLowerCase()

      if (booleanLower.includes(' and ')) {
        const terms = booleanLower.split(' and ')
        matchesSearch = terms.every(term => jobText.includes(term.trim()))
      } else if (booleanLower.includes(' or ')) {
        const terms = booleanLower.split(' or ')
        matchesSearch = terms.some(term => jobText.includes(term.trim()))
      } else {
        matchesSearch = jobText.includes(booleanLower)
      }
    }

    let matchesAdvancedFilters = true
    if (advancedFilters.job_titles.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_titles.some(t => job.title.toLowerCase().includes(t.toLowerCase()))
    if (advancedFilters.departments.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.departments.some(d => job.department.toLowerCase().includes(d.toLowerCase()))
    if (advancedFilters.locations.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.locations.some(l => job.location.toLowerCase().includes(l.toLowerCase()))
    if (advancedFilters.work_models.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.work_models.some(m => job.workModel.toLowerCase().includes(m.toLowerCase()))
    if (advancedFilters.job_types.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_types.some(t => job.type.toLowerCase().includes(t.toLowerCase()))
    if (advancedFilters.seniority_levels.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.seniority_levels.some(l => getJobSeniority(job)?.toLowerCase().includes(l.toLowerCase()) ?? false)
    if (advancedFilters.status.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.status.some(s => job.status.toLowerCase().includes(s.toLowerCase()))
    if (advancedFilters.stages.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.stages.some(s => job.stage.toLowerCase().includes(s.toLowerCase()))
    if (advancedFilters.priorities.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.priorities.some(p => job.priority.toLowerCase().includes(p.toLowerCase()))
    if (advancedFilters.managers.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.managers.some(m => job.manager.toLowerCase().includes(m.toLowerCase()))
    if (advancedFilters.benefits.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.benefits.some(b => job.benefits.some(jb => jb.toLowerCase().includes(b.toLowerCase())))
    if (advancedFilters.requirements.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.requirements.some(r => job.requirements.some(jr => jr.toLowerCase().includes(r.toLowerCase())))
    if (advancedFilters.budget_ranges.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.budget_ranges.some(range => {
        const budget = job.budget || 0
        switch (range) {
          case `Até ${CURRENCY_SYMBOL} 50.000`: return budget <= 50000
          case `${CURRENCY_SYMBOL} 50.000 - ${CURRENCY_SYMBOL} 100.000`: return budget >= 50000 && budget <= 100000
          case `${CURRENCY_SYMBOL} 100.000+`: return budget >= 100000
          default: return false
        }
      })
    if (advancedFilters.urgency_levels.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.urgency_levels.some(l => job.urgencyLevel.toString() === l)
    if (advancedFilters.contract_duration.length > 0)
      matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.contract_duration.some(d => job.type.toLowerCase().includes(d.toLowerCase()))

    let matchesInlineFilters = true
    if (jobFilters.status?.statuses?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.status.statuses.includes(job.status)
    if (jobFilters.status?.priorities?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.status.priorities.includes(job.priority)
    if (jobFilters.status?.stages?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.status.stages.includes(job.stage)
    if (jobFilters.position?.workModels?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.position.workModels.includes(job.workModel)
    if (jobFilters.position?.levels?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.position.levels.some(l => getJobSeniority(job)?.toLowerCase().includes(l.toLowerCase()) ?? false)
    if (jobFilters.team?.departments?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.team.departments.some(d => job.department.toLowerCase().includes(d.toLowerCase()))
    if (jobFilters.team?.recruiters?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.team.recruiters.some(r => job.recruiter.toLowerCase().includes(r.toLowerCase()))
    if (jobFilters.team?.managers?.length) matchesInlineFilters = matchesInlineFilters && jobFilters.team.managers.some(m => job.manager.toLowerCase().includes(m.toLowerCase()))
    if (jobFilters.position?.locations?.length)
      matchesInlineFilters = matchesInlineFilters && jobFilters.position.locations.some(loc =>
        job.location.toLowerCase().includes(loc.toLowerCase()) ||
        (loc.toLowerCase() === 'remoto' && job.workModel === 'remoto')
      )
    if (jobFilters.publishing?.channels?.length) {
      const publishedChannels: string[] = []
      if (job.publishedLinkedIn) publishedChannels.push('linkedin')
      if (job.publishedWebsite) publishedChannels.push('website')
      if (job.publishedIndeed) publishedChannels.push('indeed')
      matchesInlineFilters = matchesInlineFilters && jobFilters.publishing.channels.some(ch => publishedChannels.includes(ch))
    }
    if (jobFilters.publishing?.unpublished)
      matchesInlineFilters = matchesInlineFilters && !job.publishedLinkedIn && !job.publishedWebsite && !job.publishedIndeed
    if (jobFilters.funnel?.emptyPipeline)
      matchesInlineFilters = matchesInlineFilters && job.funnel.total === 0
    if (jobFilters.metrics?.lowConversion) {
      const conversionRate = job.funnel.total > 0 ? (job.funnel.hired / job.funnel.total) : 0
      matchesInlineFilters = matchesInlineFilters && conversionRate < 0.1
    }
    if (jobFilters.metrics?.minNPS)
      matchesInlineFilters = matchesInlineFilters && job.nps >= jobFilters.metrics.minNPS
    if (jobFilters.metrics?.maxDaysOpen) {
      const daysOpenCalc = Math.floor((new Date().getTime() - new Date(job.openDate).getTime()) / (1000 * 60 * 60 * 24))
      matchesInlineFilters = matchesInlineFilters && daysOpenCalc <= jobFilters.metrics.maxDaysOpen
    }

    return matchesStatus && matchesSearch && matchesAdvancedFilters && matchesInlineFilters
  }).sort((a, b) => {
    const aIsPinned = pinnedJobs.has(a.id)
    const bIsPinned = pinnedJobs.has(b.id)
    if (aIsPinned && !bIsPinned) return -1
    if (!aIsPinned && bIsPinned) return 1
    return 0
  })
}

export function isJobCreationIntent(message: string): boolean {
  const lowerMessage = message.toLowerCase()
  const patterns = [
    'criar vaga', 'nova vaga', 'abrir vaga', 'cadastrar vaga',
    'registrar vaga', 'quero criar', 'preciso de uma vaga',
    'preciso abrir', 'montar vaga', 'configurar vaga',
    'iniciar processo seletivo', 'novo processo seletivo'
  ]
  return patterns.some(pattern => lowerMessage.includes(pattern))
}

export function getContextualSuggestions(jobs: Job[]): string[] {
  const suggestions: string[] = []
  const urgentCount = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4).length
  if (urgentCount > 0)
    suggestions.push(`Analisar ${urgentCount} vaga${urgentCount > 1 ? 's' : ''} urgente${urgentCount > 1 ? 's' : ''}`)
  const emptyPipeline = jobs.filter(j => j.funnel.total === 0).length
  if (emptyPipeline > 0)
    suggestions.push(`${emptyPipeline} vaga${emptyPipeline > 1 ? 's' : ''} sem candidatos`)
  const now = Date.now()
  const upcomingDeadlines = jobs.filter(j => {
    if (!j.deadline) return false
    const deadline = new Date(j.deadline).getTime()
    const daysRemaining = Math.floor((deadline - now) / (1000 * 60 * 60 * 24))
    return daysRemaining >= 0 && daysRemaining <= 7
  }).length
  if (upcomingDeadlines > 0) suggestions.push(`Vagas com deadline em 7 dias`)
  const pausedCount = jobs.filter(j => j.status === 'Paralisada').length
  if (pausedCount > 0)
    suggestions.push(`Revisar ${pausedCount} vaga${pausedCount > 1 ? 's' : ''} paralisada${pausedCount > 1 ? 's' : ''}`)
  if (suggestions.length === 0) {
    suggestions.push('Resumo das minhas vagas')
    suggestions.push('Performance dos últimos 30 dias')
  }
  if (suggestions.length < 4 && !suggestions.some(s => s.includes('Performance')))
    suggestions.push('Performance das vagas ativas')
  if (suggestions.length < 4) suggestions.push('Top 5 vagas com mais candidatos')
  return suggestions.slice(0, 4)
}

export function processLocalJobCommand(command: string, jobs: Job[]): string {
  const trimmedCommand = command.trim().toLowerCase()
  const activeJobs = jobs.filter(j => j.status === 'Ativa')

  if (trimmedCommand.includes('quantas vagas') || trimmedCommand.includes('vagas abertas') || trimmedCommand.includes('total de vagas')) {
    const total = jobs.length
    const ativas = activeJobs.length
    const paralisadas = jobs.filter(j => j.status === 'Paralisada').length
    const concluidas = jobs.filter(j => j.status === 'Concluída').length
    return `📊 **Resumo de Vagas**\n\n• **Total de vagas:** ${total}\n• **Vagas ativas:** ${ativas}\n• **Vagas paralisadas:** ${paralisadas}\n• **Vagas concluídas:** ${concluidas}\n\n💡 Dica: Use "vagas urgentes" para ver as que precisam de atenção imediata.`
  }

  if (trimmedCommand.includes('vagas urgentes') || trimmedCommand.includes('urgente') || trimmedCommand.includes('prioridade alta')) {
    const urgentes = jobs.filter(j => j.priority === 'alta' || j.urgencyLevel >= 4)
    if (urgentes.length === 0) return `✅ **Nenhuma vaga urgente no momento**\n\nTodas as vagas estão com prioridade normal. Continue monitorando!`
    const lista = urgentes.slice(0, 10).map((j, i) => `${i + 1}. **${j.title}** - ${j.department} (${j.funnel.total} candidatos)`).join('\n')
    return `🚨 **${urgentes.length} Vaga(s) Urgente(s)**\n\n${lista}\n\n💡 Essas vagas precisam de atenção imediata.`
  }

  if (trimmedCommand.includes('resumir') || trimmedCommand.includes('resumo') || trimmedCommand.includes('overview') || trimmedCommand.includes('visão geral')) {
    const porStatus: Record<string, number> = {}
    const porDept: Record<string, number> = {}
    let totalCandidatos = 0
    jobs.forEach(j => {
      porStatus[j.status] = (porStatus[j.status] || 0) + 1
      porDept[j.department] = (porDept[j.department] || 0) + 1
      totalCandidatos += j.funnel.total
    })
    const statusText = Object.entries(porStatus).map(([s, c]) => `• ${s}: ${c}`).join('\n')
    const topDepts = Object.entries(porDept).sort((a, b) => b[1] - a[1]).slice(0, 5)
    const deptText = topDepts.map(([d, c]) => `• ${d}: ${c} vagas`).join('\n')
    return `📋 **Resumo das ${jobs.length} Vagas**\n\n**Por Status:**\n${statusText}\n\n**Top Departamentos:**\n${deptText}\n\n**Total de candidatos no funil:** ${totalCandidatos}`
  }

  if (trimmedCommand.includes('performance') || trimmedCommand.includes('métricas') || trimmedCommand.includes('kpis')) {
    const totalVagas = jobs.length
    const totalCandidatos = jobs.reduce((sum, j) => sum + j.funnel.total, 0)
    const totalContratados = jobs.reduce((sum, j) => sum + j.funnel.hired, 0)
    const taxaConversao = totalCandidatos > 0 ? ((totalContratados / totalCandidatos) * 100).toFixed(1) : '0'
    const nowMs = Date.now()
    const diasAbertos = jobs.map(j => Math.floor((nowMs - new Date(j.openDate).getTime()) / (1000 * 60 * 60 * 24)))
    const mediaDias = diasAbertos.length > 0 ? Math.round(diasAbertos.reduce((a, b) => a + b, 0) / diasAbertos.length) : 0
    return `📊 **Performance Geral das Vagas**\n\n📋 **Total de vagas:** ${totalVagas}\n👥 **Candidatos no funil:** ${totalCandidatos}\n✅ **Contratações:** ${totalContratados}\n📈 **Taxa de conversão:** ${taxaConversao}%\n⏱️ **Tempo médio aberta:** ${mediaDias} dias`
  }

  if (trimmedCommand.includes('top 5') || trimmedCommand.includes('top5') || trimmedCommand.includes('mais candidatos')) {
    const topVagas = [...jobs].sort((a, b) => b.funnel.total - a.funnel.total).slice(0, 5)
    if (topVagas.length === 0) return `📊 Nenhuma vaga disponível para análise.`
    const lista = topVagas.map((j, i) => `${i + 1}. **${j.title}**\n   📁 ${j.funnel.total} candidatos | 🎯 ${j.funnel.interview} em entrevista | ✅ ${j.funnel.hired} contratados`).join('\n\n')
    return `🏆 **Top 5 Vagas com Mais Candidatos**\n\n${lista}`
  }

  if (trimmedCommand.includes('sem candidatos') || trimmedCommand.includes('funil vazio') || trimmedCommand.includes('pipeline vazio')) {
    const semCandidatos = jobs.filter(j => j.funnel.total === 0)
    if (semCandidatos.length === 0) return `✅ **Todas as vagas têm candidatos!**\n\nNenhuma vaga está com pipeline vazio.`
    const lista = semCandidatos.slice(0, 10).map((j, i) => `${i + 1}. **${j.title}** - ${j.department} (${j.status})`).join('\n')
    return `⚠️ **${semCandidatos.length} Vaga(s) sem Candidatos**\n\n${lista}\n\n💡 Considere ampliar a divulgação ou revisar os requisitos.`
  }

  if (trimmedCommand.includes('departamentos') || trimmedCommand.includes('por departamento')) {
    const porDept: Record<string, { total: number; ativas: number; candidatos: number }> = {}
    jobs.forEach(j => {
      const d = j.department || 'Outros'
      if (!porDept[d]) porDept[d] = { total: 0, ativas: 0, candidatos: 0 }
      porDept[d].total++
      if (j.status === 'Ativa') porDept[d].ativas++
      porDept[d].candidatos += j.funnel.total
    })
    const lista = Object.entries(porDept).sort((a, b) => b[1].total - a[1].total).map(([dept, data]) => `• **${dept}:** ${data.total} vagas (${data.ativas} ativas) | ${data.candidatos} candidatos`).join('\n')
    return `🏢 **Vagas por Departamento**\n\n${lista}`
  }

  return `🤔 **Entendi sua pergunta, mas estou operando em modo offline**\n\nPosso ajudar localmente com:\n\n📊 "quantas vagas abertas" | "resumir vagas"\n🚨 "vagas urgentes" | "vagas sem candidatos"\n📈 "performance geral" | "top 5 vagas"\n🏢 "departamentos contratando"\n\n💡 Para análises mais detalhadas, tente novamente em alguns instantes.`
}

export function getActiveJobFiltersCount(jobFilters: JobFilters): number {
  let count = 0
  if (jobFilters.status?.statuses?.length) count += jobFilters.status.statuses.length
  if (jobFilters.status?.priorities?.length) count += jobFilters.status.priorities.length
  if (jobFilters.status?.stages?.length) count += jobFilters.status.stages.length
  if (jobFilters.dates?.openedWithinDays) count += 1
  if (jobFilters.dates?.closingWithinDays) count += 1
  if (jobFilters.dates?.noActivityDays) count += 1
  if (jobFilters.team?.recruiters?.length) count += jobFilters.team.recruiters.length
  if (jobFilters.team?.managers?.length) count += jobFilters.team.managers.length
  if (jobFilters.team?.departments?.length) count += jobFilters.team.departments.length
  if (jobFilters.position?.levels?.length) count += jobFilters.position.levels.length
  if (jobFilters.position?.types?.length) count += jobFilters.position.types.length
  if (jobFilters.position?.workModels?.length) count += jobFilters.position.workModels.length
  if (jobFilters.position?.locations?.length) count += jobFilters.position.locations.length
  if (jobFilters.funnel?.minCandidates) count += 1
  if (jobFilters.funnel?.maxCandidates) count += 1
  if (jobFilters.funnel?.emptyPipeline) count += 1
  if (jobFilters.funnel?.stuckInStage) count += 1
  if (jobFilters.metrics?.minNPS) count += 1
  if (jobFilters.metrics?.maxDaysOpen) count += 1
  if (jobFilters.metrics?.lowConversion) count += 1
  if (jobFilters.publishing?.channels?.length) count += jobFilters.publishing.channels.length
  if (jobFilters.publishing?.unpublished) count += 1
  return count
}

export const HOOK_TO_TABLE_COLUMN_MAP: Record<string, string> = {
  'id': 'id', 'status': 'status', 'screeningStatus': 'screeningStatus',
  'title': 'vaga', 'candidates': 'candidatos', 'performance': 'performance',
  'recruiter': 'recrutador', 'manager': 'gestor',
  'deadlineScreening': 'prazoTriagem', 'deadlineShortlist': 'prazoShortlist',
  'deadlineClosing': 'prazoEncerramento',
}

export const SEARCH_TEMPLATES = [
  "Vagas Tech Sênior", "Vagas Design", "Vagas Remotas",
  "Vagas Urgentes", "Vagas Júnior", "Vagas Product Manager",
  "Vagas Data Science", "Vagas DevOps", "Vagas Startup", "Vagas Enterprise"
]
