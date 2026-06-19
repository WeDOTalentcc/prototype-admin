"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

// IA_SESSION_QUERY_KEYS — canonical keys for IASidebar session queries
export const IA_SESSION_QUERY_KEYS = {
  sessions: (filters?: { pinned?: boolean; domainTag?: string; q?: string }) =>
    ["ia-sessions", filters ?? {}] as const,
  session: (id: string) => ["ia-session", id] as const,
}

export interface IASession {
  id: string
  user_id: string
  context_type: string
  context_id: string | null
  title: string | null
  summary: string | null
  intent: string | null
  status: string
  is_active: boolean
  is_pinned: boolean
  domain_tag: string | null
  note: string | null
  unread_count: number
  message_count: number
  created_at: string | null
  updated_at: string | null
}

interface SessionListResponse {
  conversations: IASession[]
  total: number
  offset: number
  limit: number
}

interface ListFilters {
  pinned?: boolean
  domain_tag?: string
  q?: string
  context_type?: string
  include_archived?: boolean
}

async function fetchSessions(filters: ListFilters = {}): Promise<IASession[]> {
  const params = new URLSearchParams()
  if (filters.pinned !== undefined) params.set("pinned", String(filters.pinned))
  if (filters.domain_tag) params.set("domain_tag", filters.domain_tag)
  if (filters.q) params.set("q", filters.q)
  if (filters.context_type) params.set("context_type", filters.context_type)
  if (filters.include_archived) params.set("include_archived", "true")

  const url = `/api/backend-proxy/conversations${params.size > 0 ? `?${params}` : ""}`
  const res = await fetch(url, { credentials: "include" })
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.status}`)
  const data: SessionListResponse = await res.json()
  return data.conversations
}

export function useIASessions(filters: ListFilters = {}) {
  return useQuery({
    queryKey: IA_SESSION_QUERY_KEYS.sessions(filters),
    queryFn: () => fetchSessions(filters),
    staleTime: 30_000, // 30s — React Query owns sessions[], not Zustand
    refetchOnWindowFocus: true,
  })
}

interface UpdateSessionPayload {
  title?: string | null
  is_pinned?: boolean | null
  note?: string | null
  domain_tag?: string | null
}

export function useUpdateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: UpdateSessionPayload & { id: string }) => {
      const res = await fetch(`/api/backend-proxy/conversations/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Failed to update session: ${res.status}`)
      return res.json()
    },
    onSuccess: () => {
      // Invalidate all session list queries
      qc.invalidateQueries({ queryKey: ["ia-sessions"] })
    },
  })
}

export function useMarkSessionRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}/mark-read`,
        { method: "POST", credentials: "include" }
      )
      if (!res.ok) throw new Error(`Failed to mark read: ${res.status}`)
      return res.json()
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ia-sessions"] })
    },
  })
}

export function useDeleteSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/backend-proxy/conversations/${id}`, {
        method: "DELETE",
        credentials: "include",
      })
      if (!res.ok) throw new Error(`Failed to delete session: ${res.status}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ia-sessions"] })
    },
  })
}

export function useArchiveSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}/archive`,
        { method: "POST", credentials: "include" }
      )
      if (!res.ok) throw new Error(`Failed to archive session: ${res.status}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ia-sessions"] })
    },
  })
}
