"use client"

import React, { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { JobKanbanPage } from "@/components/pages/job-kanban-page"
import { liaApi } from "@/services/lia-api"

export default function JobPage() {
  const params = useParams()
  const jobId = params?.id as string
  const [jobData, setJobData] = useState<any>(null)
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

        setJobData({
          id: vacancy.id,
          jobId: vacancy.job_code || vacancy.id,
          title: vacancy.title,
          department: vacancy.department,
          location: vacancy.location,
          workModel: vacancy.work_model,
          type: vacancy.contract_type || "CLT",
          level: vacancy.seniority_level,
          salary: salaryStr,
          status: vacancy.status,
          stage: vacancy.current_stage,
          openDate: vacancy.created_at?.split('T')[0],
          deadline: vacancy.deadline,
          manager: vacancy.manager,
          managerEmail: vacancy.manager_email,
          recruiter: vacancy.recruiter,
          recruiterEmail: vacancy.recruiter_email,
          description: vacancy.enriched_jd || vacancy.description,
          requirements: vacancy.technical_requirements || [],
          benefits: vacancy.benefits || [],
          funnel: vacancy.funnel_metrics,
          nps: vacancy.nps_score,
          priority: vacancy.priority,
          urgencyLevel: vacancy.urgency_level,
          hiringProcess: vacancy.interview_stages?.map((s: any) => s.name) || [],
          interviewStages: vacancy.interview_stages,
          avgTimePerStage: vacancy.avg_time_per_stage,
          screeningConfig: vacancy.screening_config,
        })
      })
      .catch(err => {
        setError('Erro ao carregar a vaga')
      })
      .finally(() => setIsLoading(false))
  }, [jobId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-wedo-cyan/30" />
      </div>
    )
  }

  if (error || !jobData) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-500 dark:text-gray-400 text-sm">
        {error || 'Vaga não encontrada'}
      </div>
    )
  }

  return <JobKanbanPage job={jobData} />
}
