"use client"

import { formatBRL } from "@/lib/pricing"
import { formatJobLocation } from "@/lib/jobs/location"

interface JobData {
  id: string
  jobId: string
  backendId?: string
  title: string
  department?: string
  location?: string
  workModel?: string
  type: string
  level?: string
  salary?: string
  status?: string
  stage?: string
  openDate?: string
  deadline?: string
  manager?: string
  managerEmail?: string
  recruiter?: string
  recruiterEmail?: string
  description?: string
  requirements?: string[]
  benefits?: string[]
  funnel?: unknown
  nps?: number
  priority?: string
  urgencyLevel?: string
  hiringProcess?: string[]
  interviewStages?: unknown[]
  avgTimePerStage?: unknown
  screeningConfig?: unknown
}


import React, { useState, useEffect, useCallback } from "react"
import { useParams } from "next/navigation"
import { JobKanbanPage } from "@/components/pages/job-kanban-page"
import { liaApi } from "@/services/lia-api"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { useLoadingWatchdog } from "@/hooks/shared/use-loading-watchdog"
import { useFocusedJobStore } from "@/stores/focused-job-store"

export default function JobPage() {
  const params = useParams()
  const jobId = params?.id as string
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadTrigger, setReloadTrigger] = useState(0)
  const { setFocusedJob } = useFocusedJobStore()

  const handleRetry = useCallback(() => {
    setError(null)
    setJobData(null)
    setIsLoading(true)
    setReloadTrigger(prev => prev + 1)
  }, [])

  useLoadingWatchdog(isLoading, () => {
    setIsLoading(false)
    setError("Tempo limite de carregamento excedido")
  }, 20_000)

  useEffect(() => {
    if (!jobId) return

    setIsLoading(true)
    setError(null)
    liaApi.getJobVacancy(jobId)
      .then(vacancy => {
        const salaryRange = vacancy.salary_range
        const salaryStr = salaryRange
          ? `${formatBRL(Number(salaryRange.min || 0))} - ${formatBRL(Number(salaryRange.max || 0))}`
          : undefined

        const v = vacancy as typeof vacancy & {
          job_code?: string
          contract_type?: string
          current_stage?: string
          enriched_jd?: string
          funnel_metrics?: unknown
          nps_score?: number
          avg_time_per_stage?: unknown
          candidate_count?: number
        }
        setJobData({
          id: v.id,
          jobId: v.job_code || v.id,
          backendId: v.id,
          title: v.title,
          department: v.department,
          location: formatJobLocation(v.location),
          workModel: v.work_model,
          type: v.contract_type || "CLT",
          level: v.seniority_level,
          salary: salaryStr,
          status: v.status,
          stage: v.current_stage,
          openDate: v.created_at?.split("T")[0],
          deadline: v.deadline,
          manager: v.manager,
          managerEmail: v.manager_email,
          recruiter: v.recruiter,
          recruiterEmail: v.recruiter_email,
          description: v.enriched_jd || v.description,
          requirements: (v.technical_requirements || []).map(r => String(r)),
          // Task #765 — JobVacancy.benefits may now be structured dicts
          // (post-migration) or legacy strings. Flatten to display names
          // for the read-only detail view.
          benefits: (v.benefits || []).map(b =>
            typeof b === "string" ? b : (b?.name ?? "")
          ).filter(Boolean),
          funnel: v.funnel_metrics,
          nps: v.nps_score,
          priority: v.priority,
          urgencyLevel: v.urgency_level != null ? String(v.urgency_level) : undefined,
          hiringProcess: (v.interview_stages || []).map((s: { name?: string }) => s.name || ""),
          interviewStages: v.interview_stages,
          avgTimePerStage: v.avg_time_per_stage,
          screeningConfig: v.screening_config,
        })

        // Populate focused-job store so the LIA chat sidebar has context
        // about the currently-viewed vacancy without requiring a separate fetch.
        const candidateCount = Number(v.candidate_count ?? 0)
        setFocusedJob({
          id: v.id,
          title: v.title,
          candidateCount,
          todayInterviewCount: 0,
        })

        // Attempt to enrich with today's interview count asynchronously.
        fetch(`/api/backend-proxy/interviews?job_id=${v.id}&date=today`)
          .then(r => (r.ok ? r.json() : null))
          .then(data => {
            if (data && typeof data.total === "number") {
              setFocusedJob({
                id: v.id,
                title: v.title,
                candidateCount,
                todayInterviewCount: data.total,
              })
            }
          })
          .catch(() => {
            // silently ignore — todayInterviewCount defaults to 0
          })
      })
      .catch(() => {
        setError("Erro ao carregar a vaga")
      })
      .finally(() => setIsLoading(false))
  }, [jobId, reloadTrigger, setFocusedJob])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen" aria-live="polite" aria-busy={true} role="status">
        <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-wedo-cyan/30" />
      </div>
    )
  }

  if (error || !jobData) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 text-lia-text-secondary dark:text-lia-text-tertiary" role="alert" aria-live="assertive">
        <p className="text-sm">{error || "Vaga não encontrada"}</p>
        {error && (
          <button
            onClick={handleRetry}
            className="text-xs px-3 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
          >
            Tentar novamente
          </button>
        )}
      </div>
    )
  }

  return (
    <ErrorBoundarySection
      fallback={
        <div className="flex flex-col items-center justify-center h-screen gap-4 text-lia-text-secondary dark:text-lia-text-tertiary" role="alert">
          <p className="text-sm">Erro ao carregar a vaga. Tente novamente.</p>
          <button
            onClick={() => window.location.reload()}
            className="text-xs px-3 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors"
          >
            Recarregar página
          </button>
        </div>
      }
    >
      <JobKanbanPage job={jobData as unknown as Record<string, unknown>} />
    </ErrorBoundarySection>
  )
}
