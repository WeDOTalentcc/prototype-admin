/**
 * suggestions-api.ts — GET /lia/suggestions client.
 *
 * P1-3 (Fase B 2026-05-23): consumido por ChatSuggestionsPanel pra mostrar
 * sugestoes DINAMICAS (vagas ativas, candidatos novos, deadline expiring)
 * acima da lista estatica de QUERY_EXAMPLES. Fallback estatico se API falhar.
 */
import { BACKEND_URL, HttpError } from "./base"

export interface SuggestionCard {
  id: string
  type: string
  icon: string
  title: string
  description: string
  action: string
  priority: "high" | "medium" | "low" | string
  category: string
  metadata?: Record<string, unknown> | null
}

export interface SuggestionsResponse {
  suggestions: SuggestionCard[]
  generated_at: string
  context?: Record<string, unknown> | null
}

/**
 * Fetch dynamic suggestions for homepage panel.
 * `limit` defaults to backend default (6); pass higher to fetch more cards.
 *
 * Throws HttpError on non-2xx; caller (panel) should catch and fall back to
 * static QUERY_EXAMPLES — anti-pattern silent fallback NÃO aplica aqui porque
 * o caller documenta o fallback explicitamente.
 */
export async function fetchDynamicSuggestions(
  limit?: number,
): Promise<SuggestionsResponse> {
  const path = limit ? `/lia/suggestions?limit=${limit}` : "/lia/suggestions"
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  })
  if (!response.ok) {
    let detail = ""
    try {
      detail = await response.text()
    } catch {
      // best effort
    }
    throw new HttpError(
      response.status,
      `Suggestions request failed: ${response.status} ${response.statusText}`,
      { body: detail },
    )
  }
  return response.json() as Promise<SuggestionsResponse>
}
