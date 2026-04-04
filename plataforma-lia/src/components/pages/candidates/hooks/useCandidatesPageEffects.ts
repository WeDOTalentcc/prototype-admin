"use client"

import { useEffect, useRef } from "react"
import type { Dispatch, SetStateAction } from "react"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { Candidate } from "@/components/pages/candidates/types"
import type { ChatMessage } from "./candidates-core"

export interface UseCandidatesPageEffectsParams {
  selectedCandidatesForBatch: Set<string>
  userCollapsedLIA: boolean
  candidates: Candidate[]
  liaPromptValue: string
  setShowExpandedLIA: (v: boolean) => void
  setChatMessages: Dispatch<SetStateAction<ChatMessage[]>>
  setLiaPromptEntities: (v: ParsedEntities) => void
  setLiaSuggestions: (v: string[]) => void
  setLiaIsParsingEntities: (v: boolean) => void
}

export function useCandidatesPageEffects({
  selectedCandidatesForBatch,
  userCollapsedLIA,
  candidates,
  liaPromptValue,
  setShowExpandedLIA,
  setChatMessages,
  setLiaPromptEntities,
  setLiaSuggestions,
  setLiaIsParsingEntities,
}: UseCandidatesPageEffectsParams) {
  const prevSelectedCountRef = useRef(0)
  useEffect(() => {
    const currentCount = selectedCandidatesForBatch.size
    const prevCount = prevSelectedCountRef.current
    if (currentCount > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
      if (currentCount !== prevCount) {
        const names = candidates
          .filter(c => selectedCandidatesForBatch.has(c.id))
          .slice(0, 3)
          .map(c => c.name)
        const preview = names.join(', ') + (currentCount > 3 ? ` e mais ${currentCount - 3}` : '')
        const plural = currentCount > 1
        setChatMessages(prev => [
          ...prev,
          {
            id: `lia-selection-${Date.now()}`,
            type: 'lia' as const,
            content: `Você selecionou **${currentCount} candidato${plural ? 's' : ''}**: ${preview}.\n\nPosso analisar ${plural ? 'estes candidatos' : 'este candidato'} para você:\n\n• **Analisar potencial de crescimento**\n• **Definir tipo de perfil** (executor, estratégico, etc)\n• **Resumo executivo do perfil**`,
            timestamp: new Date(),
          },
        ])
      }
    }
    prevSelectedCountRef.current = currentCount
  }, [selectedCandidatesForBatch.size, userCollapsedLIA, candidates, selectedCandidatesForBatch])

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
  }, [liaPromptValue])

  useEffect(() => { setShowExpandedLIA(true) }, [])
}
