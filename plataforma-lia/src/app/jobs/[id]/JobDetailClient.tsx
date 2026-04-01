"use client"

interface JobData {
  id: string
  jobId: string
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


import React, { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { JobKanbanPage } from "@/components/pages/job-kanban-page"
import { liaApi } from "@/services/lia-api"

export default function JobPage() {
  const params = useParams()
  const jobId = params?.id as string
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return

    setIsLoading(true)
    liaApi.getJobVacancy(jobId)
      .then(vacancy => {
        const salaryRange = vacancy.salary_range
        const salaryStr = salaryRange
          ? `R$ ${Number(salaryRange.min || 0).toLocaleString('pt-BR')} - R$ ${Number(salaryRange.max || 0).toLocaleString('pt-BR')}`
          : undefined

        // Extended vacancy has fields not in current TypeScript type definitions
        const v = vacancy as typeof vacancy & {
          job_code?: string
          contract_type?: string
          current_stage?: string
          enriched_jd?: string
          funnel_metrics?: unknown
          nps_score?: number
          avg_time_per_stage?: unknown
        }
        setJobData({
          id: v.id,
          jobId: v.job_code || v.id,
          title: v.title,
          department: v.department,
          location: v.location,
          workModel: v.work_model,
          type: v.contract_type || "CLT",
          level: v.seniority_level,
          salary: salaryStr,
          status: v.status,
          stage: v.current_stage,
          openDate: v.created_at?.split('T')[0],
          deadline: v.deadline,
          manager: v.manager,
          managerEmail: v.manager_email,
          recruiter: v.recruiter,
          recruiterEmail: v.recruiter_email,
          description: v.enriched_jd || v.description,
          requirements: (v.technical_requirements || []).map(r => String(r)),
          benefits: v.benefits || [],
          funnel: v.funnel_metrics,
          nps: v.nps_score,
          priority: v.priority,
          urgencyLevel: v.urgency_level != null ? String(v.urgency_level) : undefined,
          hiringProcess: (v.interview_stages || []).map((s: { name?: string }) => s.name || ''),
          interviewStages: v.interview_stages,
          avgTimePerStage: v.avg_time_per_stage,
          screeningConfig: v.screening_config,
        })
      })
      .catch(err => {
        setError('Erro ao carregar a vaga')
      })
      .finally(() => setIsLoading(false))
  }, [jobId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen" aria-live="polite" aria-busy={true} role="status">
        <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-wedo-cyan/30" />
      </div>
    )
  }

  if (error || !jobData) {
    return (
      <div className="flex items-center justify-center h-screen lia-text-500 dark:text-lia-text-tertiary text-sm" role="alert" aria-live="assertive">
        {error || 'Vaga não encontrada'}
      </div>
    )
  }

  return <JobKanbanPage job={jobData as unknown as Record<string, unknown>} />
}
