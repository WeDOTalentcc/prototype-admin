"use client"

import React, { useEffect, useCallback } from "react"
import { useTemplateSuggestions } from "@/hooks/ai/use-template-suggestions"
import { useTemplateSuggestionQueue } from "@/components/template-suggestion-toast"
import { useCreditEstimator } from "@/hooks/search/useCreditEstimator"
import { useChatStateStore } from "@/stores/chat-state-store"

interface UseEAPEffectsParams {
  showGlobalSearchOptions: boolean
  searchSource: 'local' | 'global' | 'hybrid'
  activeSearchTab: string
  naturalSearchValue: string
  promptEnhancementDismissed: boolean
  dismissedQueryRef: React.MutableRefObject<string>
  enhanceTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>
  forceExpanded: boolean | undefined
  isExpanded: boolean
  showHistory: boolean
  commandHistory: string[]
  pearchSearchType: 'fast'
  candidateLimit: number
  setSearchSource: React.Dispatch<React.SetStateAction<'local' | 'global' | 'hybrid'>>
  setPromptEnhancement: React.Dispatch<React.SetStateAction<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>>
  setPromptEnhancementDismissed: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypes: React.Dispatch<React.SetStateAction<Array<{ id: string; name: string; description?: string; department?: string; hired_candidate?: { name: string }; criteria?: Record<string, unknown> }>>>
  setClosedJobsForArchetype: React.Dispatch<React.SetStateAction<Array<Record<string, unknown>>>>
  setIsExpanded: React.Dispatch<React.SetStateAction<boolean>>
  setInputValue: React.Dispatch<React.SetStateAction<string>>
  setShowHistory: React.Dispatch<React.SetStateAction<boolean>>
  setSavedTemplates: React.Dispatch<React.SetStateAction<Array<Record<string, unknown>>>>
  fetchPromptEnhancement: (query: string) => Promise<void>
  handleSubmit: (e: React.FormEvent) => void
}

export function useEAPEffects(params: UseEAPEffectsParams) {
  const {
    showGlobalSearchOptions,
    searchSource,
    activeSearchTab,
    naturalSearchValue,
    promptEnhancementDismissed,
    dismissedQueryRef,
    enhanceTimeoutRef,
    forceExpanded,
    isExpanded,
    showHistory,
    commandHistory,
    pearchSearchType,
    candidateLimit,
    setSearchSource,
    setPromptEnhancement,
    setPromptEnhancementDismissed,
    setArchetypes,
    setClosedJobsForArchetype,
    setIsExpanded,
    setInputValue,
    setShowHistory,
    setSavedTemplates,
    fetchPromptEnhancement,
    handleSubmit,
  } = params

  const creditEstimator = useCreditEstimator()
  const templateSuggestions = useTemplateSuggestions()
  const suggestionQueue = useTemplateSuggestionQueue()

  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource, setSearchSource])

  useEffect(() => {
    if (searchSource !== 'local') {
      creditEstimator.fetchBalance().catch(() => { /* TODO: integrar com Sentry */ })
    }
  }, [searchSource, creditEstimator])

  useEffect(() => {
    const loadArchetypesAndJobs = async () => {
      try {
        const [archetypesRes, jobsRes] = await Promise.all([
          fetch('/api/backend-proxy/search/archetypes/'),
          fetch('/api/backend-proxy/search/archetypes/suggestions/closed-jobs/?limit=5')
        ])

        if (archetypesRes.ok) {
          const data = await archetypesRes.json()
          setArchetypes(data.archetypes || data || [])
        }

        if (jobsRes.ok) {
          const data = await jobsRes.json()
          setClosedJobsForArchetype(data.jobs || data || [])
        }
      } catch (error) {
      }
    }

    loadArchetypesAndJobs()
  }, [setArchetypes, setClosedJobsForArchetype])

  useEffect(() => {
    if (activeSearchTab !== 'natural' || !naturalSearchValue || naturalSearchValue.length < 10) {
      setPromptEnhancement(null)
      return
    }

    if (promptEnhancementDismissed && dismissedQueryRef.current) {
      const dismissedPrefix = dismissedQueryRef.current.toLowerCase().slice(0, 15)
      const currentPrefix = naturalSearchValue.toLowerCase().slice(0, 15)
      if (dismissedPrefix !== currentPrefix) {
        setPromptEnhancementDismissed(false)
        dismissedQueryRef.current = ""
      }
    }

    if (enhanceTimeoutRef.current) {
      clearTimeout(enhanceTimeoutRef.current)
    }

    enhanceTimeoutRef.current = setTimeout(() => {
      if (!promptEnhancementDismissed) {
        fetchPromptEnhancement(naturalSearchValue)
      }
    }, 1500)

    return () => {
      if (enhanceTimeoutRef.current) {
        clearTimeout(enhanceTimeoutRef.current)
      }
    }
  }, [naturalSearchValue, activeSearchTab, promptEnhancementDismissed, fetchPromptEnhancement, dismissedQueryRef, enhanceTimeoutRef, setPromptEnhancement, setPromptEnhancementDismissed])

  useEffect(() => {
    if (forceExpanded !== undefined) {
      setIsExpanded(forceExpanded)
    }
  }, [forceExpanded, setIsExpanded])

  useEffect(() => {
    const executeTemplate = sessionStorage.getItem('lia-execute-template')
    if (executeTemplate) {
      try {
        const template = JSON.parse(executeTemplate)
        setInputValue(template.command)
        setIsExpanded(true)

        setTimeout(() => {
          handleSubmit(new Event('submit') as unknown as React.FormEvent)
        }, 1000)

        sessionStorage.removeItem('lia-execute-template')
      } catch (error) {
      }
    }
  }, [handleSubmit, setInputValue, setIsExpanded])

  const liaTemplates = useChatStateStore((s) => s.liaTemplates)

  useEffect(() => {
    if (liaTemplates.length > 0) {
      const topTemplates = [...liaTemplates]
        .sort((a: Record<string, unknown>, b: Record<string, unknown>) => (b.usageCount as number) - (a.usageCount as number))
        .slice(0, 3)
      setSavedTemplates(topTemplates)
    }
  }, [liaTemplates, setSavedTemplates])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false)
        setShowHistory(false)
      }

      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault()
        setIsExpanded(true)
        setTimeout(() => {
          const input = document.querySelector('input[placeholder*="LIA"]') as HTMLInputElement
          input?.focus()
        }, 100)
      }

      if (e.ctrlKey && e.key === 'h' && isExpanded && commandHistory.length > 0) {
        e.preventDefault()
        setShowHistory(!showHistory)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isExpanded, showHistory, commandHistory.length, setIsExpanded, setShowHistory])

  const extractionTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = React.useRef<string>('')

  const extractCriteriaFromQuery = React.useCallback((query: string, setExtractedCriteria: React.Dispatch<React.SetStateAction<Array<{
    id: string
    type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
    label: string
    value: string
    active: boolean
  }>>>) => {
    if (extractionTimeoutRef.current) {
      clearTimeout(extractionTimeoutRef.current)
    }

    extractionTimeoutRef.current = setTimeout(() => {
      const queryLower = query.toLowerCase().trim()

      if (queryLower === lastQueryRef.current) return
      lastQueryRef.current = queryLower

      setExtractedCriteria(prev => {
        const manuallyModified = prev.filter(c => !c.active)
        const newlyExtracted: Array<{
          id: string
          type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
          label: string
          value: string
          active: boolean
        }> = []

        const locations = ['são paulo', 'rio de janeiro', 'belo horizonte', 'curitiba', 'porto alegre', 'brasília', 'sp', 'rj']
        for (const loc of locations) {
          if (queryLower.includes(loc)) {
            const id = `loc-${loc.replace(/\s/g, '-')}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({
                id,
                type: 'location',
                label: 'Localização',
                value: loc.charAt(0).toUpperCase() + loc.slice(1),
                active: true
              })
            }
            break
          }
        }

        const expMatch = queryLower.match(/(\d+)\+?\s*anos?|(\d+)\+?\s*years?/)
        if (expMatch) {
          const years = expMatch[1] || expMatch[2]
          const id = `exp-${years}`
          const existing = prev.find(c => c.id === id)
          if (!existing) {
            newlyExtracted.push({
              id,
              type: 'experience',
              label: 'Experiência',
              value: `${years}+ anos`,
              active: true
            })
          }
        }

        const skills = ['python', 'react', 'node', 'java', 'typescript', 'javascript', 'aws', 'docker', 'kubernetes', 'sql', 'figma', 'ux', 'ui', 'angular', 'vue', 'spring', 'django', 'flask', 'fastapi']
        for (const skill of skills) {
          if (queryLower.includes(skill)) {
            const id = `skill-${skill}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({
                id,
                type: 'skills',
                label: 'Skills',
                value: skill.charAt(0).toUpperCase() + skill.slice(1),
                active: true
              })
            }
          }
        }

        const languages = ['inglês', 'espanhol', 'francês', 'alemão', 'english', 'spanish', 'fluente', 'avançado']
        for (const lang of languages) {
          if (queryLower.includes(lang)) {
            const id = `lang-${lang}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({
                id,
                type: 'language',
                label: 'Idioma',
                value: lang.charAt(0).toUpperCase() + lang.slice(1),
                active: true
              })
            }
            break
          }
        }

        const seniorities: Record<string, string> = {
          'sênior': 'Sênior', 'senior': 'Sênior',
          'pleno': 'Pleno',
          'júnior': 'Júnior', 'junior': 'Júnior',
          'lead': 'Tech Lead', 'tech lead': 'Tech Lead',
          'especialista': 'Especialista', 'staff': 'Staff'
        }
        for (const [key, val] of Object.entries(seniorities)) {
          if (queryLower.includes(key)) {
            const id = `seniority-${key.replace(/\s/g, '-')}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({
                id,
                type: 'job_title',
                label: 'Senioridade',
                value: val,
                active: true
              })
            }
            break
          }
        }

        const existingActive = prev.filter(c => c.active)
        const merged = [...existingActive, ...manuallyModified]

        for (const newCrit of newlyExtracted) {
          if (!merged.find(c => c.id === newCrit.id)) {
            merged.push(newCrit)
          }
        }

        return merged
      })
    }, 300)
  }, [])

  React.useEffect(() => {
    return () => {
      if (extractionTimeoutRef.current) {
        clearTimeout(extractionTimeoutRef.current)
      }
    }
  }, [])

  const creditEstimate = React.useMemo(() => {
    if (searchSource === 'local') {
      return { total: 0, perCandidate: 0, isLocal: true, canAfford: true, isLoading: false as boolean }
    }

    const estimate = creditEstimator.calculateLocal({
      searchType: pearchSearchType,
      limit: candidateLimit,
      highFreshness: false,
      requireEmails: false,
      showEmails: false,
      requirePhoneNumbers: false,
      showPhoneNumbers: false,
      requirePhonesOrEmails: false
    })

    const availableCredits = creditEstimator.balance?.available_credits ?? Infinity
    const canAfford = availableCredits >= estimate.total_estimated

    return {
      total: estimate.total_estimated,
      perCandidate: estimate.cost_per_candidate,
      isLocal: false,
      breakdown: estimate.breakdown,
      canAfford,
      availableCredits: creditEstimator.balance?.available_credits,
      isLoading: creditEstimator.isLoading
    }
  }, [searchSource, pearchSearchType, candidateLimit, creditEstimator])

  const handleVoiceToggle = (
    isListening: boolean,
    setIsListening: React.Dispatch<React.SetStateAction<boolean>>,
    setInputValueFn: React.Dispatch<React.SetStateAction<string>>
  ) => {
    setIsListening(!isListening)
    if (!isListening) {
      setTimeout(() => {
        setInputValueFn("Enviar convite para desenvolvedores selecionados")
        setIsListening(false)
      }, 2000)
    }
  }

  const getStatusInfo = (selectedCandidates: Record<string, unknown>[], filteredCount: number, totalCount: number) => {
    const selectedCount = selectedCandidates.length

    if (selectedCount > 0) {
      return {
        text: `${selectedCount} selecionado${selectedCount > 1 ? 's' : ''}`,
        color: 'text-lia-text-secondary',
        bgColor: 'bg-lia-bg-secondary border-lia-border-subtle'
      }
    }

    if (filteredCount < totalCount) {
      return {
        text: `${filteredCount} de ${totalCount} candidatos`,
        color: 'text-status-warning',
        bgColor: 'bg-status-warning/10 border-status-warning/30'
      }
    }

    return {
      text: `${totalCount} candidatos`,
      color: 'text-lia-text-secondary',
      bgColor: 'bg-lia-bg-primary border-lia-border-subtle'
    }
  }

  return {
    creditEstimator,
    creditEstimate,
    templateSuggestions,
    suggestionQueue,
    extractCriteriaFromQuery,
    extractionTimeoutRef,
    handleVoiceToggle,
    getStatusInfo,
  }
}
