"use client"

import { useEffect } from "react"
import type { ParsedEntities } from "@/components/search/smart-search-input"

export interface UseCandidatesPageEffectsParams {
  liaPromptValue: string
  setLiaPromptEntities: (v: ParsedEntities) => void
  setLiaSuggestions: (v: string[]) => void
  setLiaIsParsingEntities: (v: boolean) => void
}

export function useCandidatesPageEffects({
  liaPromptValue,
  setLiaPromptEntities,
  setLiaSuggestions,
  setLiaIsParsingEntities,
}: UseCandidatesPageEffectsParams) {
  useEffect(() => {
    const emptyEntities: ParsedEntities = {
      job_title: undefined, location: undefined, skills: [],
      years_experience: undefined, industry: undefined, seniority: undefined, company: undefined,
    }
    if (!liaPromptValue.trim()) { setLiaPromptEntities(emptyEntities); setLiaSuggestions([]); return }
    const timer = setTimeout(async () => {
      setLiaIsParsingEntities(true)
      try {
        const res = await fetch('/api/backend-proxy/search/parse-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: liaPromptValue }),
        })
        if (res.ok) {
          const data = await res.json()
          const e = data.entities || data
          setLiaPromptEntities({
            job_title: e.job_title || undefined, location: e.location || undefined,
            skills: e.skills || [], years_experience: e.years_experience || undefined,
            industry: e.industry || undefined, seniority: e.seniority || undefined,
            company: e.company || undefined,
          })
          setLiaSuggestions(Array.isArray(data.suggestions) ? data.suggestions : [])
        }
      } catch {} finally { setLiaIsParsingEntities(false) }
    }, 500)
    return () => clearTimeout(timer)
  }, [liaPromptValue, setLiaIsParsingEntities, setLiaPromptEntities, setLiaSuggestions])
}
