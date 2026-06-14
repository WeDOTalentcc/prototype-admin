"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { type CampaignItem } from "./useCampaignsList"

const CAMPAIGN_DETAIL_KEY = (id: string) => ["recruitment-campaign", id] as const

async function fetchProjectDetail(id: string): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}`)
  if (!res.ok) throw new Error("Failed to fetch project")
  return res.json()
}

async function advanceStageRequest(id: string): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}/advance-stage`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("Failed to advance stage")
  return res.json()
}

export function useProjectDetail(id: string) {
  const queryClient = useQueryClient()

  const { data: project, isLoading, isError } = useQuery({
    queryKey: CAMPAIGN_DETAIL_KEY(id),
    queryFn: () => fetchProjectDetail(id),
    staleTime: 30_000,
    enabled: Boolean(id),
  })

  const { mutate: advance, isPending: isAdvancing } = useMutation({
    mutationFn: () => advanceStageRequest(id),
    onSuccess: (updated) => {
      queryClient.setQueryData(CAMPAIGN_DETAIL_KEY(id), updated)
      queryClient.invalidateQueries({ queryKey: ["recruitment-campaigns"] })
    },
  })

  return { project, isLoading, isError, advance, isAdvancing }
}
