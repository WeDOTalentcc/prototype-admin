"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import useSWR from "swr"

export type SemanticDomain = 
  | "skills"
  | "job-titles" 
  | "roles"
  | "industries"
  | "expertise"
  | "fields-of-study"
  | "companies"

export interface SemanticSuggestion {
  term: string
  confidence: number
  is_synonym: boolean
  is_related: boolean
  is_broader: boolean
  is_narrower: boolean
  canonical_id?: string
}

export interface SemanticExpansionResult {
  original_query: string
  domain: string
  suggestions: SemanticSuggestion[]
  cached: boolean
  processing_time_ms: number
}

interface UseSemanticSearchOptions {
  domain: SemanticDomain
  debounceMs?: number
  minQueryLength?: number
  maxSuggestions?: number
  enabled?: boolean
}

interface UseSemanticSearchResult {
  suggestions: SemanticSuggestion[]
  isLoading: boolean
  error: string | null
  search: (query: string, existing?: string[]) => Promise<void>
  clearSuggestions: () => void
  processingTimeMs: number
  cached: boolean
}

async function fetchSemanticSuggestions(
  domain: SemanticDomain,
  query: string,
  existing: string[]
): Promise<SemanticExpansionResult> {
  const response = await fetch(`/api/backend-proxy/semantic-search/${domain}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, existing }),
  })

  if (!response.ok) {
    throw new Error(`Semantic search failed: ${response.status}`)
  }

  const result = await response.json()
  return result.data
}

export function useSemanticSearch({
  domain,
  debounceMs = 400,
  minQueryLength = 2,
  maxSuggestions = 10,
  enabled = true,
}: UseSemanticSearchOptions): UseSemanticSearchResult {
  const [suggestions, setSuggestions] = useState<SemanticSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [processingTimeMs, setProcessingTimeMs] = useState(0)
  const [cached, setCached] = useState(false)
  
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)

  const clearSuggestions = useCallback(() => {
    setSuggestions([])
    setError(null)
    setProcessingTimeMs(0)
    setCached(false)
  }, [])

  const search = useCallback(async (query: string, existing: string[] = []) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    if (!enabled || !query || query.length < minQueryLength) {
      clearSuggestions()
      return
    }

    const currentRequestId = ++requestIdRef.current

    debounceTimeoutRef.current = setTimeout(async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = new AbortController()

      setIsLoading(true)
      setError(null)

      try {
        const result = await fetchSemanticSuggestions(domain, query, existing)

        if (currentRequestId !== requestIdRef.current) {
          return
        }

        const filteredSuggestions = result.suggestions
          .filter(s => !existing.map(e => e.toLowerCase()).includes(s.term.toLowerCase()))
          .slice(0, maxSuggestions)

        setSuggestions(filteredSuggestions)
        setProcessingTimeMs(result.processing_time_ms)
        setCached(result.cached)
      } catch (err) {
        if (currentRequestId !== requestIdRef.current) {
          return
        }
        
        if (err instanceof Error && err.name === "AbortError") {
          return
        }

        setError(err instanceof Error ? err.message : "Search failed")
        setSuggestions([])
      } finally {
        if (currentRequestId === requestIdRef.current) {
          setIsLoading(false)
        }
      }
    }, debounceMs)
  }, [domain, debounceMs, minQueryLength, maxSuggestions, enabled, clearSuggestions])

  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    suggestions,
    isLoading,
    error,
    search,
    clearSuggestions,
    processingTimeMs,
    cached,
  }
}

export function useSemanticSkills(existing: string[] = []) {
  return useSemanticSearch({ domain: "skills" })
}

export function useSemanticJobTitles(existing: string[] = []) {
  return useSemanticSearch({ domain: "job-titles" })
}

export function useSemanticRoles(existing: string[] = []) {
  return useSemanticSearch({ domain: "roles" })
}

export function useSemanticIndustries(existing: string[] = []) {
  return useSemanticSearch({ domain: "industries" })
}

export function useSemanticExpertise(existing: string[] = []) {
  return useSemanticSearch({ domain: "expertise" })
}

export function useSemanticFieldsOfStudy(existing: string[] = []) {
  return useSemanticSearch({ domain: "fields-of-study" })
}

export function useSemanticCompanies(existing: string[] = []) {
  return useSemanticSearch({ domain: "companies" })
}
