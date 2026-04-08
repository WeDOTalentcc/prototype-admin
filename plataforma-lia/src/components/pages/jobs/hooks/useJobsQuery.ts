"use client"

import { useState, useCallback, useEffect } from "react"
import { liaApi } from "@/services/lia-api"
import type { JobVacancy, JobFilters, JobSortConfig, JobMetrics } from "../types"

interface UseJobsQueryOptions {
  initialPageSize?: number
  autoLoad?: boolean
}

interface UseJobsQueryResult {
  jobs: JobVacancy[]
  isLoading: boolean
  error: Error | null
  totalCount: number
  metrics: JobMetrics | null
  filters: JobFilters
  sortConfig: JobSortConfig
  setFilters: (filters: JobFilters) => void
  setSortConfig: (config: JobSortConfig) => void
  loadJobs: () => Promise<void>
  loadMore: () => Promise<void>
  createJob: (data: Partial<JobVacancy>) => Promise<JobVacancy>
  updateJob: (id: string, data: Partial<JobVacancy>) => Promise<JobVacancy>
  deleteJob: (id: string) => Promise<void>
  duplicateJob: (id: string) => Promise<JobVacancy>
}

export function useJobsQuery(options: UseJobsQueryOptions = {}): UseJobsQueryResult {
  const { initialPageSize = 20, autoLoad = true } = options

  const [jobs, setJobs] = useState<JobVacancy[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [metrics, setMetrics] = useState<JobMetrics | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  
  const [filters, setFilters] = useState<JobFilters>({})
  const [sortConfig, setSortConfig] = useState<JobSortConfig>({
    column: "createdAt",
    direction: "desc",
  })

  const transformJob = useCallback((raw: Record<string, unknown>): JobVacancy => {
    return {
      id: raw.id as string,
      title: raw.title as string,
      department: raw.department as string | undefined,
      location: raw.location as string | undefined,
      workModel: (raw.work_model || "hybrid") as JobVacancy["workModel"],
      status: (raw.status || "draft") as JobVacancy["status"],
      priority: (raw.priority || "medium") as JobVacancy["priority"],
      seniority: raw.seniority as string | undefined,
      salaryMin: raw.salary_min as number | undefined,
      salaryMax: raw.salary_max as number | undefined,
      salaryCurrency: raw.salary_currency as string | undefined,
      requiredSkills: raw.required_skills as string[] | undefined,
      niceToHaveSkills: raw.nice_to_have_skills as string[] | undefined,
      description: raw.description as string | undefined,
      candidatesCount: (raw.candidates_count || 0) as number,
      applicationsCount: (raw.applications_count || 0) as number,
      interviewsScheduled: (raw.interviews_scheduled || 0) as number,
      offersExtended: (raw.offers_extended || 0) as number,
      hiringManagerId: raw.hiring_manager_id as string | undefined,
      hiringManagerName: raw.hiring_manager_name as string | undefined,
      recruiterId: raw.recruiter_id as string | undefined,
      recruiterName: raw.recruiter_name as string | undefined,
      createdAt: raw.created_at as string,
      updatedAt: raw.updated_at as string,
      publishedAt: raw.published_at as string | undefined,
      openDate: raw.open_date as string | undefined,
      targetCloseDate: raw.target_close_date as string | undefined,
      daysOpen: raw.days_open as number | undefined,
      confidenceScore: raw.confidence_score as number | undefined,
      tags: raw.tags as string[] | undefined,
      isConfidential: raw.is_confidential as boolean | undefined,
    }
  }, [])

  const loadJobs = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    setCurrentPage(1)

    try {
      const response = await liaApi.listJobVacancies(undefined, 0, initialPageSize)

      const transformedJobs = response.items.map(jv => transformJob(jv as unknown as Record<string, unknown>))
      setJobs(transformedJobs)
      setTotalCount(response.total)

      const newMetrics: JobMetrics = {
        totalJobs: response.total,
        activeJobs: transformedJobs.filter((j: JobVacancy) => j.status === "active").length,
        draftJobs: transformedJobs.filter((j: JobVacancy) => j.status === "draft").length,
        closedJobs: transformedJobs.filter((j: JobVacancy) => j.status === "closed").length,
        totalCandidates: transformedJobs.reduce((sum: number, j: JobVacancy) => sum + j.candidatesCount, 0),
        avgTimeToFill: 45,
        avgCandidatesPerJob: transformedJobs.length > 0 
          ? transformedJobs.reduce((sum: number, j: JobVacancy) => sum + j.candidatesCount, 0) / transformedJobs.length 
          : 0,
      }
      setMetrics(newMetrics)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load jobs"))
    } finally {
      setIsLoading(false)
    }
  }, [initialPageSize, transformJob])

  const loadMore = useCallback(async () => {
    if (isLoading) return

    setIsLoading(true)

    try {
      const nextPage = currentPage + 1
      const offset = (nextPage - 1) * initialPageSize
      const response = await liaApi.listJobVacancies(undefined, offset, initialPageSize)

      const transformedJobs = response.items.map(jv => transformJob(jv as unknown as Record<string, unknown>))
      setJobs((prev) => [...prev, ...transformedJobs])
      setCurrentPage(nextPage)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load more jobs"))
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, currentPage, initialPageSize, transformJob])
  const createJob = useCallback(async (data: Partial<JobVacancy>): Promise<JobVacancy> => {
    const response = await liaApi.createJobVacancy(data as any)
    const newJob = transformJob(response as unknown as Record<string, unknown>)
    setJobs((prev) => [newJob, ...prev])
    setTotalCount((prev) => prev + 1)
    return newJob
  }, [transformJob])

  const updateJob = useCallback(async (id: string, data: Partial<JobVacancy>): Promise<JobVacancy> => {
    const response = await liaApi.updateJobVacancy(id, data)
    const updatedJob = transformJob(response as unknown as Record<string, unknown>)
    setJobs((prev) => prev.map((j) => (j.id === id ? updatedJob : j)))
    return updatedJob
  }, [transformJob])

  const deleteJob = useCallback(async (id: string): Promise<void> => {
    await liaApi.deleteJobVacancy(id)
    setJobs((prev) => prev.filter((j) => j.id !== id))
    setTotalCount((prev) => prev - 1)
  }, [])

  const duplicateJob = useCallback(async (id: string): Promise<JobVacancy> => {
    const originalJob = jobs.find((j) => j.id === id)
    if (!originalJob) throw new Error("Job not found")

    const duplicateData: Partial<JobVacancy> = {
      ...originalJob,
      title: `${originalJob.title} (Cópia)`,
      status: "draft",
    }
    delete (duplicateData as Record<string, unknown>).id
    delete (duplicateData as Record<string, unknown>).createdAt
    delete (duplicateData as Record<string, unknown>).updatedAt

    return createJob(duplicateData)
  }, [jobs, createJob])

  useEffect(() => {
    if (autoLoad) {
      loadJobs()
    }
  }, [autoLoad, loadJobs])

  return {
    jobs,
    isLoading,
    error,
    totalCount,
    metrics,
    filters,
    sortConfig,
    setFilters,
    setSortConfig,
    loadJobs,
    loadMore,
    createJob,
    updateJob,
    deleteJob,
    duplicateJob,
  }
}
