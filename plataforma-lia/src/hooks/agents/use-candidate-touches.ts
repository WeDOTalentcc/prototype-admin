// Onda 2 F1 (2026-05-27) — hook canonical para touches por candidato.
//
// Consome GET /api/backend-proxy/agent-monitoring/candidate/{id}/touches.
// Usado por F8: ícone "tocado por agente" no card de candidato.
//
// staleTime 5min: touches são read-only audit trail, mudança discreta.
// Sem polling — refetch só on mount.
//
// N+1 awareness: chamar em 100 cards de kanban = 100 requests. Hoje o
// backend retorna `touch_count: 0` pra todos os candidates (MVP), então
// custo é baixo + componente só renderiza quando count > 0.
// Quando backend popular dados reais, gating por IntersectionObserver
// ou batch endpoint vira obrigatório (TODO Onda 3).
"use client"

import { useQuery } from "@tanstack/react-query"
import type { CandidateTouchesResponse } from "@/types/agents/candidate-touches"

export const CANDIDATE_TOUCHES_QUERY_KEY = (
  candidateId: string | null,
  sinceHours: number,
) =>
  ["agent-monitoring", "candidate-touches", candidateId, sinceHours] as const

async function fetchCandidateTouches(
  candidateId: string,
  sinceHours: number,
): Promise<CandidateTouchesResponse> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url = `/api/backend-proxy/agent-monitoring/candidate/${encodeURIComponent(
    candidateId,
  )}/touches?since_hours=${sinceHours}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch candidate touches: ${res.status}`)
  }
  return res.json()
}

interface UseCandidateTouchesOptions {
  candidateId: string | null
  sinceHours?: number
  enabled?: boolean
}

export function useCandidateTouches({
  candidateId,
  sinceHours = 24,
  enabled = true,
}: UseCandidateTouchesOptions) {
  return useQuery<CandidateTouchesResponse, Error>({
    queryKey: CANDIDATE_TOUCHES_QUERY_KEY(candidateId, sinceHours),
    queryFn: () => fetchCandidateTouches(candidateId as string, sinceHours),
    enabled: enabled && candidateId !== null,
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  })
}
