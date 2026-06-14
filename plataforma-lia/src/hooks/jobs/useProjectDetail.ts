"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { type CampaignItem } from "./useCampaignsList"

const CAMPAIGN_DETAIL_KEY = (id: string) => ["recruitment-campaign", id] as const

function unwrap<T>(json: unknown): T {
  if (json && typeof json === "object" && "ok" in (json as Record<string, unknown>)) {
    return (json as Record<string, unknown>).data as T
  }
  return json as T
}

async function fetchProjectDetail(id: string): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}`)
  if (!res.ok) throw new Error("Failed to fetch project")
  return unwrap(await res.json())
}

async function advanceStageRequest(id: string): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}/advance-stage`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("Failed to advance stage")
  return unwrap(await res.json())
}

async function updateCampaignRequest(
  id: string,
  updates: Record<string, unknown>,
): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error("Failed to update campaign")
  return unwrap(await res.json())
}

async function addCheckpointRequest(id: string, note: string): Promise<CampaignItem> {
  const res = await fetch(`/api/backend-proxy/recruitment-campaigns/${id}/add-checkpoint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  })
  if (!res.ok) throw new Error("Failed to add checkpoint")
  return unwrap(await res.json())
}

export function useProjectDetail(id: string) {
  const queryClient = useQueryClient()

  const { data: project, isLoading, isError } = useQuery({
    queryKey: CAMPAIGN_DETAIL_KEY(id),
    queryFn: () => fetchProjectDetail(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
    enabled: Boolean(id),
  })

  const invalidateList = () => {
    queryClient.invalidateQueries({ queryKey: ["recruitment-campaigns"] })
  }

  const { mutate: advance, isPending: isAdvancing } = useMutation({
    mutationFn: () => advanceStageRequest(id),
    onSuccess: (updated) => {
      queryClient.setQueryData(CAMPAIGN_DETAIL_KEY(id), updated)
      invalidateList()
    },
  })

  const { mutate: update, isPending: isUpdating } = useMutation({
    mutationFn: (updates: Record<string, unknown>) => updateCampaignRequest(id, updates),
    onSuccess: (updated) => {
      queryClient.setQueryData(CAMPAIGN_DETAIL_KEY(id), updated)
      invalidateList()
    },
  })

  const { mutate: addCheckpoint, isPending: isAddingCheckpoint } = useMutation({
    mutationFn: (note: string) => addCheckpointRequest(id, note),
    onSuccess: (updated) => {
      queryClient.setQueryData(CAMPAIGN_DETAIL_KEY(id), updated)
    },
  })

  return {
    project,
    isLoading,
    isError,
    advance,
    isAdvancing,
    update,
    isUpdating,
    addCheckpoint,
    isAddingCheckpoint,
  }
}
