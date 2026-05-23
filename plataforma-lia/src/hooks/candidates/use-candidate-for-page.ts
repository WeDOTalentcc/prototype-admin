"use client"

import useSWR from "swr"
import { liaApi, type CandidateLocal } from "@/services/lia-api"

/**
 * Canonical hook for loading a candidate by URL id parameter.
 *
 * Usage: standalone route /funil-de-talentos/candidato/[id] passes the URL
 * id to this hook. Hook returns SWR-managed candidate + loading + error,
 * keyed by ['candidate-by-id', id] for cross-component cache reuse.
 *
 * For drawer / kanban-side scenarios, the candidate is already in memory
 * (kanban list) — those callers should NOT use this hook; pass candidate
 * directly as prop to <CandidatePage candidate={...} mode="modal" />.
 */
export function useCandidateForPage(id: string | undefined) {
  const { data, error, isLoading, mutate } = useSWR<CandidateLocal>(
    id ? ["candidate-by-id", id] : null,
    async () => liaApi.getCandidate(id!),
    {
      revalidateOnFocus: false,
      dedupingInterval: 30000,
      revalidateOnReconnect: true,
    }
  )

  return {
    candidate: data ?? null,
    loading: isLoading,
    error: error ? (error as Error).message : null,
    mutate,
  }
}
