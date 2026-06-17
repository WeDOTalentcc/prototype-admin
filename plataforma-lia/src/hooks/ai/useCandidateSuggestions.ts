import useSWR from "swr"

export interface AISuggestion {
  id: string
  candidate_id: string
  vacancy_id: string
  trigger_type: string
  suggested_action: string
  confidence_score: number
  status: string
  payload?: Record<string, unknown>
  created_at: string
}

interface UseCandidateSuggestionsResult {
  suggestions: AISuggestion[]
  isLoading: boolean
  error: Error | null
  approveSuggestion: (id: string) => Promise<void>
  rejectSuggestion: (id: string, reason?: string) => Promise<void>
  mutate: () => void
}

let backoffMs = 0

const fetcher = async (url: string) => {
  try {
    if (backoffMs > 0) {
      await new Promise(r => setTimeout(r, backoffMs))
    }
    const res = await fetch(url)
    if (res.status === 429) {
      backoffMs = Math.min((backoffMs || 1000) * 2, 120000)
      return { suggestions: [] }
    }
    if (!res.ok) {
      return { suggestions: [] }
    }
    backoffMs = 0
    return res.json()
  } catch {
    return { suggestions: [] }
  }
}

export function useCandidateSuggestions(
  vacancyId: string | undefined,
  candidateId?: string
): UseCandidateSuggestionsResult {
  const shouldFetch = vacancyId && vacancyId.length > 0
  
  const endpoint = shouldFetch
    ? candidateId
      ? `/api/backend-proxy/api/v1/automation/ai-suggestions/candidate/${candidateId}`
      : `/api/backend-proxy/api/v1/automation/ai-suggestions/vacancy/${vacancyId}`
    : null
  
  const { data, error, isLoading, mutate } = useSWR<{ suggestions: AISuggestion[] }>(
    endpoint,
    fetcher,
    {
      refreshInterval: 60000,
      revalidateOnFocus: true,
    }
  )

  const approveSuggestion = async (id: string) => {
    try {
      await fetch(`/api/backend-proxy/api/v1/automation/ai-suggestions/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      mutate()
    } catch (e) {
      console.error("[useCandidateSuggestions] Error:", e)
    }
  }

  const rejectSuggestion = async (id: string, reason?: string) => {
    try {
      await fetch(`/api/backend-proxy/api/v1/automation/ai-suggestions/${id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      })
      mutate()
        console.error("[useCandidateSuggestions] Error:", error)
    } catch (e) {
    }
  }

  return {
    suggestions: data?.suggestions || [],
    isLoading,
    error: error || null,
    approveSuggestion,
    rejectSuggestion,
    mutate,
  }
}

export function getSuggestionForCandidate(
  suggestions: AISuggestion[],
  candidateId: string
): AISuggestion | undefined {
  return suggestions.find(s => s.candidate_id === candidateId && s.status === "pending")
}
