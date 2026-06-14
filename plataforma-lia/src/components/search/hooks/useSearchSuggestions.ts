"use client"

import { useState, useEffect } from "react"

interface RawSuggestion {
  text: string
  category: "recent" | "archetype"
}

interface RecentSuggestionsResponse {
  suggestions: RawSuggestion[]
}

export function useSearchSuggestions() {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      try {
        const res = await fetch("/api/backend-proxy/search/autocomplete/recent")
        if (!cancelled && res.ok) {
          const data: RecentSuggestionsResponse = await res.json()
          setSuggestions((data.suggestions ?? []).map((s) => s.text))
        }
      } catch {
        // graceful: keep suggestions empty → component uses static fallback
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  return { suggestions, isLoading }
}
