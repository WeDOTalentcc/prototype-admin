"use client"


import { formatBRL } from "@/lib/pricing"
import { useState, useEffect, useRef, useCallback } from "react"
import { liaApi, HttpError } from "@/services/lia-api"
import type { Job } from "@/components/jobs"

interface UseJobsDataReturn {
  state: {
    backendJobs: Job[]
    isLoadingJobs: boolean
    jobsError: string | null
    hasMounted: boolean
    jobsRefreshKey: number
    dashboardStats: Record<string, unknown> | null
    isLoadingStats: boolean
    isExternalSourceFallback: boolean
  }
  actions: {
    setBackendJobs: React.Dispatch<React.SetStateAction<Job[]>>
    setJobsRefreshKey: React.Dispatch<React.SetStateAction<number>>
    loadBackendJobs: () => Promise<void>
  }
}

/**
 * Translates a fetch failure into a user-actionable message.
 *
 * Distinguishes (task #345):
 *   - 429 rate-limit ("muitas requisições — tentando novamente em Xs")
 *   - 504 / timeout ("backend demorando para responder")
 *   - 502 / 503 / network ("sem conexão com o servidor")
 *   - Other HTTP errors (preserves status)
 */
export function describeJobsLoadError(error: unknown): string {
  if (error instanceof HttpError) {
    if (error.status === 429) {
      const seconds = error.retryAfterMs ? Math.ceil(error.retryAfterMs / 1000) : null
      return seconds
        ? `Muitas requisições ao servidor — tentando novamente em ${seconds}s.`
        : 'Muitas requisições ao servidor — tentando novamente em instantes.'
    }
    if (error.status === 504) {
      return 'O backend está demorando para responder. Tente novamente em instantes.'
    }
    if (error.status === 502 || error.status === 503) {
      return 'Sem conexão com o servidor. Tente novamente em instantes.'
    }
    return `Erro ao carregar vagas (HTTP ${error.status}).`
  }
  if (error instanceof DOMException && (error.name === 'TimeoutError' || error.name === 'AbortError')) {
    return 'O backend está demorando para responder. Tente novamente em instantes.'
  }
  if (error instanceof TypeError) {
    return 'Sem conexão com o servidor. Verifique sua rede e tente novamente.'
  }
  return error instanceof Error ? error.message : 'Falha ao carregar vagas.'
}

export function useJobsData(): UseJobsDataReturn {
  const mountedRef = useRef(false)
  const inflightRef = useRef<Promise<void> | null>(null)
  const [hasMounted, setHasMounted] = useState(false)
  const [backendJobs, setBackendJobs] = useState<Job[]>([])
  const [isLoadingJobs, setIsLoadingJobs] = useState(true)
  const [jobsError, setJobsError] = useState<string | null>(null)
  const [jobsRefreshKey, setJobsRefreshKey] = useState(0)
  const [dashboardStats, setDashboardStats] = useState<Record<string, unknown> | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [isExternalSourceFallback, setIsExternalSourceFallback] = useState(false)

  useEffect(() => {
    mountedRef.current = true
    setHasMounted(true)
    return () => { mountedRef.current = false }
  }, [])

  const loadBackendJobs = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return
    // Concurrency guard (task #345): if a load is already in flight, callers
    // join the same promise instead of spawning parallel requests that would
    // amplify rate-limits.
    if (inflightRef.current) return inflightRef.current

    const run = async () => {
      try {
        setIsLoadingJobs(true)
        setJobsError(null)

        console.debug('[useJobsData] fetching job vacancies...')
        // Run jobs + overview in parallel — eliminates the two-phase render (layout shift).
        const [response, overviewDataRaw] = await Promise.allSettled([
          liaApi.listJobVacancies(undefined, 0, 50),
          liaApi.getJobVacanciesOverview(),
        ])
        const jobsResult = response.status === 'fulfilled' ? response.value : null
        const overviewResult = overviewDataRaw.status === 'fulfilled' ? overviewDataRaw.value : null
        console.debug('[useJobsData] responses received, jobs items:', jobsResult?.items?.length ?? 'none')

      if (!mountedRef.current) return

      if (!jobsResult || !jobsResult.items) {
        throw new Error('Invalid response format')
      }

      setIsExternalSourceFallback(jobsResult.source === 'local-fallback')

      const stageMapping: Record<string, Job['stage']> = {
        'Planejamento': 'Planejamento',
        'Aprovação': 'Aprovação',
        'Publicada': 'Publicada',
        'Triagem': 'Triagem',
        'Entrevistas': 'Entrevistas',
        'Finalização': 'Finalização',
        'Encerrada': 'Encerrada'
      }
      const convertedJobs: Job[] = jobsResult.items.map((jv_raw, index: number) => { try { const jv = jv_raw as unknown as Record<string, unknown>
        const funnelData = (jv.funnel_data as Record<string, number>) || { total: 0, screening: 0, interview: 0, final: 0, hired: 0 }
        return {
          id: index + 1,
          jobId: `WDT-${(jv.id as string).slice(0, 8).toUpperCase()}`,
          backendId: jv.id as string,
          title: jv.title as string,
          department: (jv.department as string) || 'Geral',
          location: (jv.location as string) || 'Não especificado',
          workModel: ((jv.work_model as Job['workModel']) || 'híbrido'),
          type: (jv.employment_type as string) || 'CLT',
          seniority: (jv.seniority_level as string) || (jv.seniority as string) || undefined,
          salary: jv.salary_range
            ? `${formatBRL(Number((jv.salary_range as Record<string, number>).min ?? 0))} - ${formatBRL(Number((jv.salary_range as Record<string, number>).max ?? 0))}`
            : 'A combinar',
          benefits: (jv.benefits as string[]) || [],
          status: ((jv.status as Job['status']) || 'Rascunho'),
          stage: stageMapping[(jv.stage as string) || ''] || 'Triagem',
          openDate: (jv.open_date as string)?.split('T')[0] || (jv.created_at as string)?.split('T')[0] || new Date().toISOString().split('T')[0],
          deadline: (jv.deadline as string)?.split('T')[0] || undefined,
          description: (jv.description as string) || '',
          requirements: (jv.requirements as string[]) || [],
          manager: (jv.manager as string) || 'Não definido',
          managerEmail: (jv.manager_email as string) || '',
          recruiter: (jv.recruiter as string) || 'Não definido',
          recruiterEmail: (jv.recruiter_email as string) || '',
          priority: ((jv.priority as Job['priority']) || 'média'),
          funnel: {
            total: funnelData.total || 0,
            screening: funnelData.screening || 0,
            interview: funnelData.interview || 0,
            final: funnelData.final || 0,
            hired: funnelData.hired || 0,
          },
          liaMetrics: jv.lia_metrics ? {
            pipeline_lia: (jv.lia_metrics as Record<string, number>).pipeline_lia || 0,
            triagens_agendadas: (jv.lia_metrics as Record<string, number>).triagens_agendadas || 0,
            triagens_realizadas: (jv.lia_metrics as Record<string, number>).triagens_realizadas || 0,
            sem_resposta: (jv.lia_metrics as Record<string, number>).sem_resposta || 0,
            entrevistas_agendadas: (jv.lia_metrics as Record<string, number>).entrevistas_agendadas || 0,
          } : undefined,
          publishedLinkedIn: (jv.published_linkedin as boolean) || false,
          publishedWebsite: (jv.published_website as boolean) || false,
          isConfidential: (jv.is_confidential as boolean) || false,
          visibility: ((jv.visibility as Job['visibility']) || 'public'),
          nps: (jv.nps as number) || 0,
          budget: (jv.budget as number) || undefined,
          budgetUsed: (jv.budget_used as number) || undefined,
          nextActions: (jv.next_actions as string[]) || [],
          urgencyLevel: ((jv.urgency_level as 1 | 2 | 3 | 4 | 5) || 3),
          approvalStatus: ((jv.approval_status as 'pendente' | 'aprovada' | 'rejeitada') || 'pendente'),
          tags: (jv.tags as string[]) || [],
          technicalRequirements: (jv.technical_requirements as unknown[]) || [],
          languages: (jv.languages as unknown[]) || [],
          behavioralCompetencies: (jv.behavioral_competencies as unknown[]) || [],
          screeningQuestions: (jv.screening_questions as unknown[]) || [],
          interviewStages: (jv.interview_stages as unknown[]) || [],
          hiringProcess: (jv.interview_stages && (jv.interview_stages as unknown[]).length > 0)
            ? [...(jv.interview_stages as Record<string, unknown>[])]
                .sort((a, b) => ((a.order as number) || 0) - ((b.order as number) || 0))
                .map((s) => (s.stageName || s.stage_name || s.name || '') as string)
                .filter((n) => n)
            : ((jv.hiring_process as string[]) || []),
          salaryRange: (jv.salary_range as Record<string, unknown>) || undefined,
          organizationalStructure: (jv.organizational_structure as Record<string, unknown>) || undefined,
          timeline: (jv.timeline as Record<string, unknown>) || undefined,
          governanceRules: (jv.governance_rules as Record<string, unknown>) || undefined,
          whatsappTemplateType: (jv.whatsapp_template_type as string) || undefined,
          targetSector: (jv.target_sector as string) || undefined,
          targetSegment: (jv.target_segment as string) || undefined,
          conversationId: (jv.conversation_id as string) || undefined,
          screeningConfig: (jv.screening_config as Record<string, unknown>) || undefined,
          screeningStatus: (jv.screening_status as string) || (jv.screening_config ? 'not_started' : 'not_configured'),
          deadlineScreening: (jv.deadline_screening as string) || undefined,
          deadlineShortlist: (jv.deadline_shortlist as string) || undefined,
          deadlineClosing: (jv.deadline_closing as string) || undefined,
          eligibilityQuestions: (jv.eligibility_questions as unknown[]) || [],
          confidentialityConfig: (jv.confidentiality_config as Record<string, unknown>) || undefined,
          enrichedJd: (jv.enriched_jd as Record<string, unknown>) || undefined,
          isAffirmative: (jv.is_affirmative as boolean) || false,
          createdAt: (jv.created_at as string) || undefined,
          updatedAt: (jv.updated_at as string) || undefined,
          publishedAt: (jv.published_at as string) || (jv.last_published_at as string) || undefined,
          closedAt: (jv.closed_at as string) || undefined,
          createdByEmail: (jv.created_by_email as string) || undefined,
          readinessStage: (jv.readiness_stage as string) || undefined,
          readinessBlockers: (jv.readiness_blockers as string[]) || [],
        } as unknown as Job
      } catch (itemErr) {
        console.warn(`[useJobsData] Failed to parse job at index ${index}`, itemErr instanceof Error ? itemErr.message : itemErr)
        return null
      }
      }).filter((j): j is Job => j !== null)

      console.debug('[useJobsData] transform complete, valid jobs:', convertedJobs.length)
      setBackendJobs(convertedJobs)

      try {
        const overviewData = overviewResult
        if (!mountedRef.current) return
        const stats = {
          total: overviewData.active_jobs.total + (overviewData.all_jobs.hired_last_90d || 0),
          ativas: overviewData.active_jobs.total,
          urgentes: overviewData.active_jobs.by_urgency?.['alta'] || 0,
          paralisadas: 0,
          concluidas: overviewData.all_jobs.hired_last_90d || 0,
          canceladas: 0,
          noFunil: overviewData.my_jobs.candidates_in_funnel || 0,
          entrevistasRecentes: overviewData.my_jobs.interviews_last_7d || 0,
          ofertas: overviewData.my_jobs.offers_sent || 0,
          ttfMedio: Math.round(overviewData.all_jobs.time_to_fill_avg_90d || overviewData.active_jobs.avg_days_open),
          taxaConversao: Math.round(overviewData.all_jobs.success_rate || overviewData.my_jobs.conversion_rate),
          atRisco: overviewData.active_jobs.at_risk,
          pipelineVazio: overviewData.active_jobs.empty_pipeline,
          deadlineProximo: overviewData.active_jobs.deadline_soon,
          porDepartamento: overviewData.all_jobs.by_department,
          tendenciaSemanal: overviewData.all_jobs.trend_weeks,
          insights: overviewData.insights,
        }
        setDashboardStats(stats)
        setIsLoadingStats(false)
        setIsLoadingJobs(false)
      } catch {
        if (!mountedRef.current) return
        const stats = {
          total: convertedJobs.length,
          ativas: convertedJobs.filter(job => job.status === 'Ativa').length,
          urgentes: convertedJobs.filter(job => job.urgencyLevel >= 4).length,
          paralisadas: convertedJobs.filter(job => job.status === 'Paralisada').length,
          concluidas: convertedJobs.filter(job => job.status === 'Concluída').length,
          canceladas: convertedJobs.filter(job => job.status === 'Cancelada').length,
          noFunil: convertedJobs.reduce((sum, job) => sum + ((job as unknown as { funnel?: { total?: number } }).funnel?.total || 0), 0),
          entrevistasRecentes: 0,
          ofertas: convertedJobs.filter(job => (job as unknown as { stage?: string }).stage === 'Oferta').length,
          ttfMedio: 0,
          taxaConversao: 0,
          atRisco: 0,
          pipelineVazio: 0,
          deadlineProximo: 0,
          porDepartamento: {},
          tendenciaSemanal: [],
          insights: [],
        }
        setDashboardStats(stats)
        setIsLoadingStats(false)
        setIsLoadingJobs(false)
      }
      } catch (error) {
        if (!mountedRef.current) return
        const message = describeJobsLoadError(error)
        console.error(
          '[useJobsData] loadBackendJobs failed:',
          error instanceof HttpError
            ? `HttpError ${error.status} (${error.message})`
            : error instanceof Error
              ? `${error.name}: ${error.message}`
              : error,
        )
        setJobsError(message)
        setIsLoadingStats(false)
        setIsLoadingJobs(false)
      }
    }

    const promise = run().finally(() => {
      inflightRef.current = null
    })
    inflightRef.current = promise
    return promise
  }, [])

  useEffect(() => {
    if (!hasMounted) return
    loadBackendJobs()
  }, [hasMounted, jobsRefreshKey, loadBackendJobs])

  useEffect(() => {
    const onFocus = () => {
      // Only refetch on focus when there is an error AND no load is currently
      // in flight — prevents the focus listener from amplifying load on the
      // backend while a retry is already happening (task #345).
      if (mountedRef.current && jobsError && !inflightRef.current) {
        loadBackendJobs()
      }
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [jobsError, loadBackendJobs])

  return {
    state: {
      backendJobs,
      isLoadingJobs,
      jobsError,
      hasMounted,
      jobsRefreshKey,
      dashboardStats,
      isLoadingStats,
      isExternalSourceFallback,
    },
    actions: {
      setBackendJobs,
      setJobsRefreshKey,
      loadBackendJobs,
    },
  }
}
