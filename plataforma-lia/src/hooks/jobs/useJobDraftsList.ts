"use client"

import { useQuery } from "@tanstack/react-query"

export type JobDraftStatus =
  | "draft"
  | "structured"
  | "reviewed"
  | "confirmed"
  | "published"
  | "cancelled"

export interface JobDraftItem {
  id: string
  job_title: string | null
  department: string | null
  seniority: string | null
  status: JobDraftStatus
  current_step: number
  total_steps: number
  published_job_id: string | null
  created_at: string
  updated_at: string
}

interface JobDraftsApiResponse {
  drafts: JobDraftItem[]
  total: number
  page: number
}

export interface UseJobDraftsListResult {
  drafts: JobDraftItem[]
  total: number
  isLoading: boolean
  isError: boolean
  refetch: () => void
}

const JOB_DRAFTS_QUERY_KEY = ["job-drafts"] as const

async function fetchJobDrafts(): Promise<JobDraftsApiResponse> {
  const res = await fetch("/api/backend-proxy/job-drafts")
  if (!res.ok) throw new Error("Failed to fetch job drafts")
  return res.json()
}

export function useJobDraftsList(): UseJobDraftsListResult {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: JOB_DRAFTS_QUERY_KEY,
    queryFn: fetchJobDrafts,
    staleTime: 30_000,
  })

  return {
    drafts: data?.drafts ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
  }
}
