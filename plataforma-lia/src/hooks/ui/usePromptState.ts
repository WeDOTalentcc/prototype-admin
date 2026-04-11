"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useCreditEstimator } from "@/hooks/search/useCreditEstimator"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import {
  MapPin, Briefcase, Clock, Building2, Code
} from "lucide-react"
import {
  extractCriteriaFromText,
  getTagColors,
  mapEntitiesToCriteria,
  extractKeywordsFromFileAnalysis,
  buildSearchSpecFromParsed,
  generateArchetypeNameFromEntities,
  hasParsedEntitiesData
} from "./promptStateCriteriaUtils"
import { toast } from "sonner"
import {
  usePromptSearchState,
  usePromptAutocompleteState,
  usePromptSimilarProfileState,
  usePromptArchetypeState,
} from "../prompt"

export interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

export interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

export const ENTITY_LABELS: Record<string, string> = {
  job_title: 'Cargo',
  location: 'Localização',
  years_experience: 'Experiência',
  industry: 'Setor',
  skills: 'Habilidades',
  seniority: 'Senioridade',
  company: 'Empresa'
}

export const CRITERIA_TYPE_MAP: Record<string, string> = {
  'Cargo': 'job_title',
  'Localização': 'location',
  'Experiência': 'years_experience',
  'Setor': 'industry',
  'Habilidades': 'skills',
  'Habilidade': 'skills',
  'Senioridade': 'seniority',
  'Empresa': 'company'
}

export const CONTEXT_COLORS: Record<string, {
  border: string
  bg: string
  headerText: string
  headerBg: string
}> = {
  candidates: {
    border: "var(--wedo-green-light)",
    bg: "var(--wedo-green-bg-10)",
    headerText: "var(--status-success)",
    headerBg: "var(--wedo-green-bg-15)"
  },
  jobs: {
    border: "var(--lia-text-tertiary)",
    bg: "var(--lia-bg-secondary)",
    headerText: "var(--lia-text-secondary)",
    headerBg: "var(--lia-bg-secondary)"
  }
}

export interface AutocompleteSuggestion {
  text: string
  category: string
  icon?: string
  description?: string
  insert_text?: string
}

export interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

export interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

export interface SearchCriterion {
  id: string
  type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
  label: string
  value: string
  active: boolean
}

export interface SearchTag {
  key: keyof BackendEntities
  label: string
  icon: typeof MapPin
  filled: boolean
  value?: string
}

export type SearchTab = 'natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
export type PromptSearchSource = 'local' | 'global' | 'hybrid'

export interface UsePromptStateParams {
  forceExpanded?: boolean
  onCommand: (command: string, action: string) => void
}

export function usePromptState({ forceExpanded = false, onCommand }: UsePromptStateParams) {
  const searchState = usePromptSearchState(forceExpanded)

  const {
    naturalSearchValue, setNaturalSearchValue,
    activeSearchTab,
    searchSource, pearchSearchType, candidateLimit,
    advancedFilters,
    handleSourceChange, confirmSourceChange,
  } = searchState

  const [parsedEntities, setParsedEntities] = useState<BackendEntities>({})
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)
  const [extractedCriteria, setExtractedCriteria] = useState<SearchCriterion[]>([])

  const autocompleteState = usePromptAutocompleteState({ naturalSearchValue, activeSearchTab })

  const {
    fetchAutocomplete,
    fetchPromptEnhancement,
    handleAcceptEnhancement: _handleAcceptEnhancement,
    handleDismissEnhancement,
    handleAutocompleteKeyDown: _handleAutocompleteKeyDown,
  } = autocompleteState

  const hasParsedEntities = useCallback(
    () => hasParsedEntitiesData(parsedEntities),
    [parsedEntities]
  )

  const buildSearchSpec = useCallback(
    () => buildSearchSpecFromParsed(parsedEntities, advancedFilters) as Record<string, unknown>,
    [parsedEntities, advancedFilters]
  )

  const generateArchetypeName = useCallback(
    () => generateArchetypeNameFromEntities(parsedEntities) ?? '',
    [parsedEntities]
  )

  const archetypeState = usePromptArchetypeState({
    naturalSearchValue,
    parsedEntities,
    hasParsedEntities,
    buildSearchSpec,
    generateArchetypeName,
  })

  const similarProfileState = usePromptSimilarProfileState()

  const parseEntitiesFromQuery = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 5) {
      setSearchAnalysis(null)
      setExtractedCriteria([])
      setParsedEntities({})
      return
    }
    setIsParsingEntities(true)
    try {
      const [parseRes, analysisRes] = await Promise.all([
        fetch('/api/backend-proxy/search/parse-query/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        }),
        fetch('/api/backend-proxy/search-assistant/analyze/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        })
      ])
      if (parseRes.ok) {
        const parseData = await parseRes.json()
        const entities = parseData.entities as BackendEntities
        setParsedEntities(entities || {})
        if (entities) {
          setExtractedCriteria(mapEntitiesToCriteria(entities))
        }
      }
      if (analysisRes.ok) {
        const backendAnalysis = await analysisRes.json()
        const criteriaFound = (backendAnalysis.filled_criteria || []).map((label: string) => ({
          type: CRITERIA_TYPE_MAP[label] || label.toLowerCase(),
          label,
          value: label
        }))
        const criteriaMissing = (backendAnalysis.missing_criteria || []).map((label: string) => ({
          type: CRITERIA_TYPE_MAP[label] || label.toLowerCase(),
          label,
          importance: label === 'Cargo' || label === 'Localização' ? 'high' : 'medium'
        }))
        const adaptedAnalysis: SearchAnalysis = {
          completeness_score: backendAnalysis.completeness_score || 0,
          criteria_found: criteriaFound,
          criteria_missing: criteriaMissing,
          alerts: backendAnalysis.alerts || [],
          suggestions: [],
          enrichment_suggestions: backendAnalysis.enrichment_suggestions || {},
          next_recommended_action: backendAnalysis.next_recommended_action
        }
        setSearchAnalysis(adaptedAnalysis)
      }
    } catch (error) {
    } finally {
      setIsParsingEntities(false)
    }
  }, [])

  const handleAcceptEnhancement = useCallback(() => {
    _handleAcceptEnhancement(setNaturalSearchValue)
  }, [_handleAcceptEnhancement, setNaturalSearchValue])

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      const uniqueKeywords = extractKeywordsFromFileAnalysis(analysis)
      if (uniqueKeywords.length > 0) {
        const searchText = uniqueKeywords.join(', ')
        setNaturalSearchValue(prev => prev ? `${prev}, ${searchText}` : searchText)
        parseEntitiesFromQuery(searchText)
        toast.info("Arquivo analisado", { description: `Extraídos ${uniqueKeywords.length} critérios de ${file.name}` })
      } else {
        toast.info("Arquivo processado", { description: `${file.name} foi analisado mas não foram encontrados critérios de busca` })
      }
    } else {
      toast.error("Erro na análise", { description: analysis.error || "Não foi possível analisar o arquivo" })
    }
  }, [parseEntitiesFromQuery, setNaturalSearchValue])

  const handleAudioTranscription = useCallback((text: string) => {
    if (text && text.trim()) {
      setNaturalSearchValue(prev => {
        const newValue = prev ? `${prev} ${text.trim()}` : text.trim()
        parseEntitiesFromQuery(newValue)
        return newValue
      })
      searchState.setShowPremiumAutocomplete(true)
      toast.info("Transcrição concluída", { description: "Texto adicionado à busca" })
    }
  }, [parseEntitiesFromQuery, setNaturalSearchValue, searchState])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    setNaturalSearchValue(suggestion)
    searchState.setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery, setNaturalSearchValue, searchState])

  const handleAutocompleteKeyDown = useCallback((e: React.KeyboardEvent) => {
    _handleAutocompleteKeyDown(e, setNaturalSearchValue)
  }, [_handleAutocompleteKeyDown, setNaturalSearchValue])

  const extractionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = useRef<string>('')

  const extractCriteriaFromQuery = useCallback((query: string) => {
    if (extractionTimeoutRef.current) {
      clearTimeout(extractionTimeoutRef.current)
    }
    extractionTimeoutRef.current = setTimeout(() => {
      const queryLower = query.toLowerCase().trim()
      if (queryLower === lastQueryRef.current) return
      lastQueryRef.current = queryLower
      setExtractedCriteria(prev => extractCriteriaFromText(query, prev))
    }, 300)
  }, [])

  useEffect(() => {
    return () => {
      if (extractionTimeoutRef.current) {
        clearTimeout(extractionTimeoutRef.current)
      }
    }
  }, [])

  const buildSearchQueryFromCriteria = useCallback(() => {
    const activeCriteria = extractedCriteria.filter(c => c.active)
    if (activeCriteria.length === 0) return naturalSearchValue
    const parts: string[] = []
    activeCriteria.forEach(c => {
      if (c.type === 'location') parts.push(`em ${c.value}`)
      else if (c.type === 'experience') parts.push(`com ${c.value}`)
      else if (c.type === 'years_experience') parts.push(`com ${c.value}`)
      else if (c.type === 'skills') parts.push(c.value)
      else if (c.type === 'language') parts.push(`com ${c.value}`)
      else if (c.type === 'job_title') parts.push(c.value)
      else if (c.type === 'seniority') parts.push(c.value)
      else if (c.type === 'industry') parts.push(`em ${c.value}`)
      else if (c.type === 'company') parts.push(`da ${c.value}`)
    })
    return parts.join(' ')
  }, [extractedCriteria, naturalSearchValue])

  const executeSearchWithCriteria = useCallback(() => {
    const searchQuery = buildSearchQueryFromCriteria()
    if (searchQuery.trim()) {
      onCommand(searchQuery, 'natural_search')
    }
  }, [buildSearchQueryFromCriteria, onCommand])

  const buildSearchSpecFromEntities = useMemo(
    () => Object.keys(parsedEntities).length === 0 ? null : {
      job_title: parsedEntities.job_title, location: parsedEntities.location,
      years_experience: parsedEntities.years_experience, industry: parsedEntities.industry,
      skills: parsedEntities.skills, seniority: parsedEntities.seniority, company: parsedEntities.company,
    },
    [parsedEntities]
  )

  const canSaveAsArchetype = useMemo(() => {
    return naturalSearchValue.trim().length > 3 ||
      (parsedEntities && Object.values(parsedEntities).some(v => v && (Array.isArray(v) ? v.length > 0 : true)))
  }, [naturalSearchValue, parsedEntities])

  const creditEstimator = useCreditEstimator()

  useEffect(() => {
    if (searchSource !== 'local') {
      creditEstimator.fetchBalance().catch((err) => { console.warn('[usePromptState] fetchBalance fire-and-forget failed', err) })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchSource])

  const searchTags: SearchTag[] = useMemo(() => [
    { key: "location" as keyof BackendEntities, label: "Localização", icon: MapPin, filled: !!parsedEntities.location, value: parsedEntities.location },
    { key: "job_title" as keyof BackendEntities, label: "Cargo", icon: Briefcase, filled: !!parsedEntities.job_title, value: parsedEntities.job_title },
    { key: "years_experience" as keyof BackendEntities, label: "Experiência", icon: Clock, filled: !!parsedEntities.years_experience, value: parsedEntities.years_experience },
    { key: "industry" as keyof BackendEntities, label: "Setor", icon: Building2, filled: !!parsedEntities.industry, value: parsedEntities.industry },
    { key: "skills" as keyof BackendEntities, label: "Habilidades", icon: Code, filled: !!(parsedEntities.skills && parsedEntities.skills.length > 0), value: parsedEntities.skills?.join(", ") }
  ], [parsedEntities])

  const filledTagsCount = useMemo(() => searchTags.filter(t => t.filled).length, [searchTags])

  const removeCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.filter(c => c.id !== id))
  }

  const toggleCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.map(c =>
      c.id === id ? { ...c, active: !c.active } : c
    ))
  }

  const creditEstimate = useMemo(() => {
    if (searchSource === 'local') {
      return { total: 0, perCandidate: 0, isLocal: true, canAfford: true } as const
    }
    const estimate = creditEstimator.calculateLocal({
      searchType: pearchSearchType, limit: candidateLimit, highFreshness: false,
      requireEmails: false, showEmails: false, requirePhoneNumbers: false,
      showPhoneNumbers: false, requirePhonesOrEmails: false
    })
    const availableCredits = creditEstimator.balance?.available_credits ?? Infinity
    const canAfford = availableCredits >= estimate.total_estimated
    return {
      total: estimate.total_estimated, perCandidate: estimate.cost_per_candidate,
      isLocal: false, breakdown: estimate.breakdown, canAfford,
      availableCredits: creditEstimator.balance?.available_credits,
      isLoading: creditEstimator.isLoading
    }
  }, [searchSource, pearchSearchType, candidateLimit, creditEstimator])

  return {
    toast,
    ...searchState,
    handleSourceChange,
    confirmSourceChange,
    ...autocompleteState,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    handleAutocompleteKeyDown,
    ...similarProfileState,
    ...archetypeState,
    isParsingEntities,
    searchAnalysis,
    parsedEntities,
    extractedCriteria, setExtractedCriteria,
    creditEstimate,
    searchTags,
    filledTagsCount,
    getTagColors,
    parseEntitiesFromQuery,
    fetchAutocomplete,
    fetchPromptEnhancement,
    handleFileAnalyzed,
    handleAudioTranscription,
    handlePremiumAutocompleteSelect,
    buildSearchSpec,
    hasParsedEntities,
    generateArchetypeName,
    canSaveAsArchetype,
    extractCriteriaFromQuery,
    extractionTimeoutRef,
    buildSearchQueryFromCriteria,
    executeSearchWithCriteria,
    buildSearchSpecFromEntities,
    removeCriterion,
    toggleCriterion,
  }
}
