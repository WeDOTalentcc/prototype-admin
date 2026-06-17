"use client"

import { useQuery } from "@tanstack/react-query"

export type CampaignStatus = "active" | "paused" | "completed" | "cancelled"

export interface CampaignStage {
  name: string
  label: string
  status: "completed" | "in_progress" | "pending"
}

export interface CampaignItem {
  id: string
  name: string
  description: string | null
  status: CampaignStatus
  job_id: string | null
  talent_pool_id: string | null
  automation_level: "manual" | "semi" | "full"
  current_stage_index: number
  current_stage: string | null
  stages: CampaignStage[]
  progress_pct: number
  total_candidates: number
  candidates_screened: number
  candidates_contacted: number
  candidates_interviewed: number
  candidates_offered: number
  candidates_hired: number
  created_by: string | null
  created_at: string | null
  updated_at: string | null
}

interface CampaignsApiResponse {
  data: CampaignItem[]
  total: number
  limit: number
  offset: number
}

export interface UseCampaignsListResult {
  campaigns: CampaignItem[]
  total: number
  isLoading: boolean
  isError: boolean
  refetch: () => void
}

const CAMPAIGNS_QUERY_KEY = ["recruitment-campaigns"] as const

async function fetchCampaigns(): Promise<CampaignsApiResponse> {
  const res = await fetch("/api/backend-proxy/recruitment-campaigns")
  if (!res.ok) throw new Error("Failed to fetch campaigns")
  const json = await res.json()
  // ResponseEnvelopeMiddleware wraps BE responses in { ok: true, data: payload }
  return ("ok" in json ? json.data : json) as CampaignsApiResponse
}

export function useCampaignsList(): UseCampaignsListResult {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: CAMPAIGNS_QUERY_KEY,
    queryFn: fetchCampaigns,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })

  return {
    campaigns: data?.data ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
  }
}
