"use client"

import { useCallback } from "react"
import {
  type ParsedEntities,
  type SearchMode,
  type SearchMetadata,
  type ArchetypeVacancy,
  type AutocompleteItem,
  type SearchAnalysis,
  type SearchSource,
  API_BASE,
} from "./smartSearchConstants"

interface UseSmartSearchCallbacksParams {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => void
  onCancel: () => void
  onSearchSourceChange?: (source: SearchSource) => void
  isLoading: boolean
  mode: SearchMode
  entities: ParsedEntities
  booleanError: string | null
  jdContent: string
  similarUrls: string[]
  similarCvFiles: File[]
  combinedSuggestions: string[]
  showCombinedSuggestions: boolean
  selectedArchetype: ArchetypeVacancy | null
  archetypeSearchPrompt: string
  similarSearchPrompt: string
  jdSearchPrompt: string
  booleanFinalPrompt: string
  promptEnhancement: {
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null
  promptEnhancementDismissed: boolean
  showAutocomplete: boolean
  autocompleteItems: AutocompleteItem[]
  selectedAutocompleteIndex: number
  usedAutocompleteTerms: Set<string>
  autocompleteCache: React.MutableRefObject<Map<string, AutocompleteItem[]>>
  autocompleteAbortRef: React.MutableRefObject<AbortController | null>
  dismissedQueryRef: React.MutableRefObject<string>
  textareaRef: React.MutableRefObject<HTMLTextAreaElement | null>
  setEntities: React.Dispatch<React.SetStateAction<ParsedEntities>>
  setIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  setSearchAnalysis: React.Dispatch<React.SetStateAction<SearchAnalysis | null>>
  setIsAnalyzing: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancement: React.Dispatch<React.SetStateAction<typeof promptEnhancement>>
  setIsEnhancingPrompt: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancementDismissed: React.Dispatch<React.SetStateAction<boolean>>
  setBooleanError: React.Dispatch<React.SetStateAction<string | null>>
  setAutocompleteItems: React.Dispatch<React.SetStateAction<AutocompleteItem[]>>
  setShowAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  setUsedAutocompleteTerms: React.Dispatch<React.SetStateAction<Set<string>>>
  setArchetypeVacancies: React.Dispatch<React.SetStateAction<ArchetypeVacancy[]>>
  setIsLoadingArchetypes: React.Dispatch<React.SetStateAction<boolean>>
  setClosedJobSuggestions: React.Dispatch<React.SetStateAction<Array<Record<string, unknown>>>>
  setIsLoadingClosedJobs: React.Dispatch<React.SetStateAction<boolean>>
  setJobSearchResults: React.Dispatch<React.SetStateAction<Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: Array<Record<string, unknown>> | null
  }>>>
  setIsSearchingJobs: React.Dispatch<React.SetStateAction<boolean>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeTab: React.Dispatch<React.SetStateAction<"list" | "create">>
  setSelectedArchetype: React.Dispatch<React.SetStateAction<ArchetypeVacancy | null>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<Record<string, unknown> | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSkills: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSeniority: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeIndustry: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeExperienceMin: React.Dispatch<React.SetStateAction<number | null>>
  setEditArchetypeLocation: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeWorkModel: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeLanguages: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeEmploymentType: React.Dispatch<React.SetStateAction<string>>
  setNewLanguageInput: React.Dispatch<React.SetStateAction<string>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setNewSkillInput: React.Dispatch<React.SetStateAction<string>>
  setJobSearchQuery: React.Dispatch<React.SetStateAction<string>>
  setArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setShowArchetypeActions: React.Dispatch<React.SetStateAction<string | null>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  setSimilarCvFiles: React.Dispatch<React.SetStateAction<File[]>>
  setCombinedSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  setShowCombinedSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  setIsAnalyzingProfiles: React.Dispatch<React.SetStateAction<boolean>>
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingSourceChange: 'hybrid' | 'global' | null
  editingArchetype: Record<string, unknown> | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  editArchetypeSkills: string[]
  editArchetypeSeniority: string
  editArchetypeIndustry: string
  editArchetypeExperienceMin: number | null
  editArchetypeLocation: string
  editArchetypeWorkModel: string
  editArchetypeLanguages: string[]
  editArchetypeEmploymentType: string
  MAX_SIMILAR_URLS: number
  MAX_CV_FILES: number
}

export function useSmartSearchCallbacks(params: UseSmartSearchCallbacksParams) {
  const {
    value,
    onChange,
    onSubmit,
    onSearchSourceChange,
    isLoading,
    mode,
    entities,
    booleanError,
    jdContent,
    similarUrls,
    similarCvFiles,
    combinedSuggestions,
    selectedArchetype,
    archetypeSearchPrompt,
    similarSearchPrompt,
    jdSearchPrompt,
    booleanFinalPrompt,
    promptEnhancement,
    promptEnhancementDismissed,
    showAutocomplete,
    autocompleteItems,
    selectedAutocompleteIndex,
    usedAutocompleteTerms,
    autocompleteCache,
    autocompleteAbortRef,
    dismissedQueryRef,
    textareaRef,
    setEntities,
    setIsParsingEntities,
    setSearchAnalysis,
    setIsAnalyzing,
    setPromptEnhancement,
    setIsEnhancingPrompt,
    setPromptEnhancementDismissed,
    setBooleanError,
    setAutocompleteItems,
    setShowAutocomplete,
    setSelectedAutocompleteIndex,
    setUsedAutocompleteTerms,
    setArchetypeVacancies,
    setIsLoadingArchetypes,
    setClosedJobSuggestions,
    setIsLoadingClosedJobs,
    setJobSearchResults,
    setIsSearchingJobs,
    setIsCreatingArchetype,
    setArchetypeTab,
    setSelectedArchetype,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setEditArchetypeSkills,
    setEditArchetypeSeniority,
    setEditArchetypeIndustry,
    setEditArchetypeExperienceMin,
    setEditArchetypeLocation,
    setEditArchetypeWorkModel,
    setEditArchetypeLanguages,
    setEditArchetypeEmploymentType,
    setNewLanguageInput,
    setNewTagInput,
    setNewSkillInput,
    setJobSearchQuery,
    setArchetypeDescription,
    setShowArchetypeActions,
    setIsSavingArchetype,
    setIsDeletingArchetype,
    setSimilarUrls,
    setSimilarCvFiles,
    setCombinedSuggestions,
    setShowCombinedSuggestions,
    setIsAnalyzingProfiles,
    setPendingSourceChange,
    setShowSourceChangeModal,
    pendingSourceChange,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    editArchetypeSkills,
    editArchetypeSeniority,
    editArchetypeIndustry,
    editArchetypeExperienceMin,
    editArchetypeLocation,
    editArchetypeWorkModel,
    editArchetypeLanguages,
    editArchetypeEmploymentType,
    MAX_SIMILAR_URLS,
    MAX_CV_FILES,
  } = params

  const parseQuery = useCallback(async (query: string) => {
    if (!query || query.length < 5) {
      setEntities({})
      setSearchAnalysis(null)
      return
    }

    setIsParsingEntities(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/parse-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        setEntities(data.entities || {})
      }
    } catch (error) {
    } finally {
      setIsParsingEntities(false)
    }
  }, [setEntities, setSearchAnalysis, setIsParsingEntities])

  const analyzeSearch = useCallback(async (query: string, currentEntities: ParsedEntities) => {
    if (!query || query.length < 5) {
      setSearchAnalysis(null)
      return
    }

    setIsAnalyzing(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search-assistant/analyze/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, entities: currentEntities })
      })

      if (response.ok) {
        const data = await response.json()
        setSearchAnalysis(data)
      }
    } catch (error) {
    } finally {
      setIsAnalyzing(false)
    }
  }, [setSearchAnalysis, setIsAnalyzing])

  const fetchPromptEnhancement = useCallback(async (query: string) => {
    if (!query || query.length < 10 || promptEnhancementDismissed) {
      setPromptEnhancement(null)
      return
    }

    setIsEnhancingPrompt(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/enhance-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.enhanced_query && data.enhanced_query !== query && data.confidence >= 0.6) {
          setPromptEnhancement({
            enhanced_query: data.enhanced_query,
            explanation: data.explanation,
            confidence: data.confidence,
            suggestions: data.suggestions || []
          })
        } else {
          setPromptEnhancement(null)
        }
      }
    } catch (error) {
      setPromptEnhancement(null)
    } finally {
      setIsEnhancingPrompt(false)
    }
  }, [promptEnhancementDismissed, setPromptEnhancement, setIsEnhancingPrompt])

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement, onChange, setPromptEnhancement])

  const handleEditEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
      textareaRef.current?.focus()
    }
  }, [promptEnhancement, onChange, setPromptEnhancement, textareaRef])

  const handleDismissEnhancement = useCallback(() => {
    setPromptEnhancement(null)
    setPromptEnhancementDismissed(true)
    dismissedQueryRef.current = value
  }, [value, setPromptEnhancement, setPromptEnhancementDismissed, dismissedQueryRef])

  const handleApplySuggestion = useCallback((suggestionValue: string) => {
    const currentValue = value.trim()
    const newValue = currentValue ? `${currentValue}, ${suggestionValue}` : suggestionValue
    onChange(newValue)
    textareaRef.current?.focus()
  }, [value, onChange, textareaRef])

  const handleSourceChange = (newSource: SearchSource) => {
    if (newSource === 'local') {
      onSearchSourceChange?.(newSource)
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  const confirmSourceChange = () => {
    if (pendingSourceChange && onSearchSourceChange) {
      onSearchSourceChange(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }

  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setAutocompleteItems([])
      setShowAutocomplete(false)
      return
    }

    const lastWord = query.split(" ").pop()?.toLowerCase() || ""
    const cacheKey = lastWord.slice(0, 4)

    if (autocompleteCache.current.has(cacheKey)) {
      const cached = autocompleteCache.current.get(cacheKey)!
      const filtered = cached.filter(item =>
        (item.text.toLowerCase().includes(lastWord) ||
        item.insert_text.toLowerCase().includes(lastWord)) &&
        !usedAutocompleteTerms.has(item.insert_text.toLowerCase())
      )
      if (filtered.length > 0) {
        setAutocompleteItems(filtered.slice(0, 8))
        setShowAutocomplete(true)
        setSelectedAutocompleteIndex(-1)
        return
      }
    }

    if (autocompleteAbortRef.current) {
      autocompleteAbortRef.current.abort()
    }
    autocompleteAbortRef.current = new AbortController()

    try {
      const response = await fetch(
        `${API_BASE}/api/backend-proxy/search-assistant/autocomplete?query=${encodeURIComponent(query)}`,
        { signal: autocompleteAbortRef.current.signal }
      )
      if (response.ok) {
        const data = await response.json()
        const allItems = data.items || []
        const items = allItems.filter((item: AutocompleteItem) => !usedAutocompleteTerms.has(item.insert_text.toLowerCase()))
        setAutocompleteItems(items)
        setShowAutocomplete(items.length > 0)
        setSelectedAutocompleteIndex(-1)

        if (allItems.length > 0 && cacheKey.length >= 2) {
          autocompleteCache.current.set(cacheKey, allItems)
          if (autocompleteCache.current.size > 50) {
            const firstKey = autocompleteCache.current.keys().next().value
            if (firstKey) autocompleteCache.current.delete(firstKey)
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
      }
      setShowAutocomplete(false)
    }
  }, [usedAutocompleteTerms, autocompleteCache, autocompleteAbortRef, setAutocompleteItems, setShowAutocomplete, setSelectedAutocompleteIndex])

  const handleAutocompleteSelect = useCallback((item: AutocompleteItem) => {
    const trimmedValue = value.trimEnd()
    const lastSpaceIndex = trimmedValue.lastIndexOf(" ")
    const beforeLastWord = lastSpaceIndex >= 0 ? trimmedValue.substring(0, lastSpaceIndex + 1) : ""
    const newValue = beforeLastWord + item.insert_text + " "
    onChange(newValue)
    setUsedAutocompleteTerms(prev => new Set(prev).add(item.insert_text.toLowerCase()))
    setShowAutocomplete(false)
    setAutocompleteItems([])
    textareaRef.current?.focus()
  }, [value, onChange, setUsedAutocompleteTerms, setShowAutocomplete, setAutocompleteItems, textareaRef])

  const validateBoolean = useCallback((query: string) => {
    if (!query.trim()) {
      setBooleanError(null)
      return true
    }

    const openParens = (query.match(/\(/g) || []).length
    const closeParens = (query.match(/\)/g) || []).length

    if (openParens !== closeParens) {
      setBooleanError("Parênteses não balanceados")
      return false
    }

    const hasOperators = /\b(AND|OR|NOT)\b/i.test(query)
    if (query.length > 10 && !hasOperators) {
      setBooleanError("Use operadores AND, OR, NOT para combinar termos")
      return false
    }

    setBooleanError(null)
    return true
  }, [setBooleanError])

  const loadArchetypes = useCallback(async () => {
    setIsLoadingArchetypes(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`)
      if (response.ok) {
        const data = await response.json()
        setArchetypeVacancies(data.archetypes || [])
      }
    } catch (error) {
    } finally {
      setIsLoadingArchetypes(false)
    }
  }, [setArchetypeVacancies, setIsLoadingArchetypes])

  const loadClosedJobSuggestions = useCallback(async () => {
    setIsLoadingClosedJobs(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/suggestions/closed-jobs?limit=5`)
      if (response.ok) {
        const data = await response.json()
        setClosedJobSuggestions(data.suggestions || [])
      }
    } catch (error) {
    } finally {
      setIsLoadingClosedJobs(false)
    }
  }, [setClosedJobSuggestions, setIsLoadingClosedJobs])

  const searchJobsForArchetype = useCallback(async (query: string) => {
    if (!query.trim()) {
      setJobSearchResults([])
      return
    }

    setIsSearchingJobs(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/job-vacancies?limit=20`)
      if (response.ok) {
        const data = await response.json()
        const jobs = data.items || []
        const queryLower = query.toLowerCase()
        const filtered = jobs.filter((job: Record<string, unknown>) =>
          (job.title as string)?.toLowerCase().includes(queryLower) ||
          (job.id as string)?.toLowerCase().includes(queryLower) ||
          (job.department as string)?.toLowerCase().includes(queryLower)
        )
        setJobSearchResults(filtered.slice(0, 10))
      }
    } catch (error) {
      setJobSearchResults([])
    } finally {
      setIsSearchingJobs(false)
    }
  }, [setJobSearchResults, setIsSearchingJobs])

  const openArchetypeFromJob = useCallback((job: Record<string, unknown>) => {
    const skills: string[] = []
    if (job.technical_requirements && Array.isArray(job.technical_requirements)) {
      job.technical_requirements.forEach((req: Record<string, unknown>) => {
        if (req.skill) skills.push(req.skill as string)
        else if (typeof req === 'string') skills.push(req)
      })
    }

    const seniorityMap: Record<string, string> = {
      "Júnior": "junior", "Junior": "junior",
      "Pleno": "pleno",
      "Sênior": "senior", "Senior": "senior",
      "Especialista": "senior",
      "Lead": "lead", "Tech Lead": "lead",
      "Staff": "staff", "Principal": "principal",
      "Gerente": "manager", "Diretor": "director"
    }

    setEditingArchetype({ id: null, is_default: false, fromJob: true, jobId: job.id })
    setEditArchetypeName((job.title as string) || "")
    setEditArchetypeQuery(`${(job.title as string) || ""} ${job.department ? `${job.department}` : ""}`.trim())
    setEditArchetypeDescription((job.description as string)?.slice(0, 300) || "")
    setEditArchetypeEmoji("🎯")
    setEditArchetypeTags([job.department as string, job.status as string].filter(Boolean) as string[])
    setEditArchetypeSkills(skills.slice(0, 10))
    setEditArchetypeSeniority(seniorityMap[job.seniority_level as string] || "")
    setEditArchetypeIndustry("")
    setEditArchetypeExperienceMin(null)
    setEditArchetypeLocation("")
    setEditArchetypeWorkModel("")
    setEditArchetypeLanguages([])
    setEditArchetypeEmploymentType("")
    setNewLanguageInput("")
    setNewTagInput("")
    setNewSkillInput("")
    setJobSearchQuery("")
    setJobSearchResults([])
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput, setJobSearchQuery, setJobSearchResults])

  const createArchetypeFromJob = useCallback(async (jobId: string, customName?: string) => {
    setIsCreatingArchetype(true)
    try {
      let url = `${API_BASE}/api/backend-proxy/search/archetypes/from-job/${jobId}`
      if (customName) {
        url += `?custom_name=${encodeURIComponent(customName)}`
      }
      const response = await fetch(url, { method: 'POST' })
      if (response.ok) {
        const newArchetype = await response.json()
        await loadArchetypes()
        setArchetypeTab("list")
        setSelectedArchetype(newArchetype)
        return newArchetype
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [loadArchetypes, setIsCreatingArchetype, setArchetypeTab, setSelectedArchetype])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    setIsCreatingArchetype(true)
    try {
      const response = await fetch('/api/ai/extract-archetype-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      })

      let extractedData: Record<string, unknown> = {}
      if (response.ok) {
        extractedData = await response.json()
      }

      setEditingArchetype({ id: null, is_default: false, fromDescription: true })
      setEditArchetypeName((extractedData.name as string) || "Novo Arquétipo")
      setEditArchetypeQuery((extractedData.query as string) || description)
      setEditArchetypeDescription(description)
      setEditArchetypeEmoji((extractedData.emoji as string) || "🎯")
      setEditArchetypeTags((extractedData.tags as string[]) || [])
      setEditArchetypeSkills((extractedData.skills as string[]) || [])
      setEditArchetypeSeniority((extractedData.seniority as string) || "")
      setEditArchetypeIndustry((extractedData.industry as string) || "")
      setEditArchetypeExperienceMin((extractedData.experience_years_min as number) || null)
      setEditArchetypeLocation("")
      setEditArchetypeWorkModel("")
      setEditArchetypeLanguages([])
      setEditArchetypeEmploymentType("")
      setNewLanguageInput("")
      setNewTagInput("")
      setNewSkillInput("")
      setArchetypeDescription("")
      setArchetypeTab("list")
    } catch (error) {
      setEditingArchetype({ id: null, is_default: false, fromDescription: true })
      setEditArchetypeName("Novo Arquétipo")
      setEditArchetypeQuery(description)
      setEditArchetypeDescription(description)
      setEditArchetypeEmoji("🎯")
      setEditArchetypeTags([])
      setEditArchetypeSkills([])
      setEditArchetypeSeniority("")
      setEditArchetypeIndustry("")
      setEditArchetypeExperienceMin(null)
      setEditArchetypeLocation("")
      setEditArchetypeWorkModel("")
      setEditArchetypeLanguages([])
      setEditArchetypeEmploymentType("")
      setNewLanguageInput("")
      setNewTagInput("")
      setNewSkillInput("")
      setArchetypeDescription("")
      setArchetypeTab("list")
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [setIsCreatingArchetype, setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput, setArchetypeDescription, setArchetypeTab])

  const openEditArchetype = useCallback((arch: Record<string, unknown>, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName((arch.name as string) || (arch.title as string) || "")
    setEditArchetypeQuery((arch.query as string) || "")
    setEditArchetypeDescription((arch.description as string) || "")
    setEditArchetypeEmoji((arch.emoji as string) || "🎯")
    setEditArchetypeTags((arch.tags as string[]) || [])
    setEditArchetypeSkills(((arch.filters as Record<string, unknown>)?.skills as string[]) || [])
    setEditArchetypeSeniority((arch.seniority as string) || ((arch.filters as Record<string, unknown>)?.seniority as string) || "")
    setEditArchetypeIndustry((arch.industry as string) || "")
    setEditArchetypeExperienceMin(((arch.filters as Record<string, unknown>)?.experience_years_min as number) || null)
    setEditArchetypeLocation(((arch.filters as Record<string, unknown>)?.location as string) || "")
    setEditArchetypeWorkModel(((arch.filters as Record<string, unknown>)?.work_model as string) || "")
    setEditArchetypeLanguages(((arch.filters as Record<string, unknown>)?.languages as string[]) || [])
    setEditArchetypeEmploymentType(((arch.filters as Record<string, unknown>)?.employment_type as string) || "")
    setNewTagInput("")
    setNewSkillInput("")
    setNewLanguageInput("")
    setShowArchetypeActions(null)
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewTagInput, setNewSkillInput, setNewLanguageInput, setShowArchetypeActions])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setEditArchetypeSkills([])
    setEditArchetypeSeniority("")
    setEditArchetypeIndustry("")
    setEditArchetypeExperienceMin(null)
    setEditArchetypeLocation("")
    setEditArchetypeWorkModel("")
    setEditArchetypeLanguages([])
    setEditArchetypeEmploymentType("")
    setNewLanguageInput("")
    setNewTagInput("")
    setNewSkillInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return

    setIsSavingArchetype(true)
    try {
      const filters: Record<string, unknown> = {}
      if (editArchetypeSkills.length > 0) filters.skills = editArchetypeSkills
      if (editArchetypeSeniority) filters.seniority = editArchetypeSeniority
      if (editArchetypeExperienceMin !== null && editArchetypeExperienceMin > 0) {
        filters.experience_years_min = editArchetypeExperienceMin
      }
      if (editArchetypeLocation) filters.location = editArchetypeLocation
      if (editArchetypeWorkModel) filters.work_model = editArchetypeWorkModel
      if (editArchetypeLanguages.length > 0) filters.languages = editArchetypeLanguages
      if (editArchetypeEmploymentType) filters.employment_type = editArchetypeEmploymentType

      const payload = {
        name: editArchetypeName.trim(),
        query: editArchetypeQuery.trim(),
        description: editArchetypeDescription.trim() || null,
        emoji: editArchetypeEmoji || "🎯",
        tags: editArchetypeTags,
        seniority: editArchetypeSeniority || null,
        industry: editArchetypeIndustry || null,
        filters: Object.keys(filters).length > 0 ? filters : null
      }

      let response: Response

      if (editingArchetype.id) {
        response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/${editingArchetype.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      } else {
        response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      }

      if (response.ok) {
        await loadArchetypes()
        closeEditArchetype()
        setArchetypeTab("list")
      } else {
        const error = await response.json()
        alert(error.detail || "Erro ao salvar arquétipo")
      }
    } catch (error) {
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills, editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin, editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages, editArchetypeEmploymentType, loadArchetypes, closeEditArchetype, setIsSavingArchetype, setArchetypeTab])

  const deleteArchetype = useCallback(async (archId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Tem certeza que deseja excluir este arquétipo?")) return

    setIsDeletingArchetype(archId)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/${archId}/`, {
        method: 'DELETE'
      })
      if (response.ok) {
        await loadArchetypes()
        if (selectedArchetype?.id === archId) {
          setSelectedArchetype(null)
        }
      } else {
        const error = await response.json()
        alert(error.detail || "Erro ao excluir arquétipo")
      }
    } catch (error) {
    } finally {
      setIsDeletingArchetype(null)
      setShowArchetypeActions(null)
    }
  }, [loadArchetypes, selectedArchetype, setIsDeletingArchetype, setSelectedArchetype, setShowArchetypeActions])

  const addSimilarUrl = useCallback(() => {
    if (similarUrls.length < MAX_SIMILAR_URLS) {
      setSimilarUrls(prev => [...prev, ""])
    }
  }, [similarUrls.length, MAX_SIMILAR_URLS, setSimilarUrls])

  const removeSimilarUrl = useCallback((index: number) => {
    setSimilarUrls(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [setSimilarUrls, setCombinedSuggestions, setShowCombinedSuggestions])

  const updateSimilarUrl = useCallback((index: number, val: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = val
      return newUrls
    })
  }, [setSimilarUrls])

  const handleCvUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    const newFiles = Array.from(files).slice(0, MAX_CV_FILES - similarCvFiles.length)
    setSimilarCvFiles(prev => [...prev, ...newFiles].slice(0, MAX_CV_FILES))
  }, [similarCvFiles.length, MAX_CV_FILES, setSimilarCvFiles])

  const removeCvFile = useCallback((index: number) => {
    setSimilarCvFiles(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [setSimilarCvFiles, setCombinedSuggestions, setShowCombinedSuggestions])

  const removeSuggestion = useCallback((keyword: string) => {
    setCombinedSuggestions(prev => prev.filter(k => k !== keyword))
  }, [setCombinedSuggestions])

  const addSuggestion = useCallback((keyword: string) => {
    if (!combinedSuggestions.includes(keyword)) {
      setCombinedSuggestions(prev => [...prev, keyword])
    }
  }, [combinedSuggestions, setCombinedSuggestions])

  const analyzeProfiles = useCallback(async () => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    if (validUrls.length === 0 && similarCvFiles.length === 0) return

    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      validUrls.forEach((url, i) => formData.append(`urls[${i}]`, url))
      similarCvFiles.forEach((file, i) => formData.append(`cvs[${i}]`, file))

      const response = await fetch(`${API_BASE}/api/backend-proxy/search/similar/combine-profiles`, {
        method: "POST",
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setCombinedSuggestions(data.keywords || [])
        setShowCombinedSuggestions(true)
      }
    } catch (error) {
      const mockKeywords = ["Sênior", "Python", "AWS", "Data Engineer", "Fintech", "SQL", "Spark"]
      setCombinedSuggestions(mockKeywords)
      setShowCombinedSuggestions(true)
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles, setIsAnalyzingProfiles, setCombinedSuggestions, setShowCombinedSuggestions])

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 2
  }, [similarUrls, similarCvFiles])

  const buildArchetypePrompt = useCallback((arch: Record<string, unknown>): string => {
    const parts: string[] = []

    if (arch.query) {
      parts.push(arch.query as string)
    }

    if ((arch.filters as Record<string, unknown>)?.skills && ((arch.filters as Record<string, unknown>)?.skills as string[]).length > 0) {
      parts.push(`Skills: ${((arch.filters as Record<string, unknown>)?.skills as string[]).join(", ")}`)
    } else if (arch.tags && (arch.tags as string[]).length > 0) {
      parts.push(`Tags: ${(arch.tags as string[]).join(", ")}`)
    }

    if (arch.seniority) {
      const seniorityMap: Record<string, string> = {
        junior: "Júnior", pleno: "Pleno", senior: "Sênior",
        lead: "Lead/Tech Lead", staff: "Staff", principal: "Principal",
        manager: "Gerente", director: "Diretor", executive: "Executivo"
      }
      parts.push(`Senioridade: ${seniorityMap[arch.seniority as string] || arch.seniority}`)
    }

    if (arch.industry) {
      const industryMap: Record<string, string> = {
        technology: "Tecnologia", fintech: "Fintech/Finanças",
        healthcare: "Saúde", education: "Educação",
        ecommerce: "E-commerce/Varejo", logistics: "Logística",
        consulting: "Consultoria", manufacturing: "Indústria/Manufatura",
        agritech: "Agronegócio", other: "Outro"
      }
      parts.push(`Indústria: ${industryMap[arch.industry as string] || arch.industry}`)
    }

    if ((arch.filters as Record<string, unknown>)?.experience_years_min) {
      parts.push(`${(arch.filters as Record<string, unknown>)?.experience_years_min}+ anos de experiência`)
    }

    if (parts.length === 0) {
      return `Buscar candidatos similares ao arquétipo "${(arch.name as string) || (arch.title as string)}"`
    }

    return parts.join(", ")
  }, [])

  const handleSubmit = () => {
    if (isLoading) return

    const metadata: SearchMetadata = { mode }

    if (mode === "natural" && value.trim()) {
      onSubmit(value.trim(), entities, mode, metadata)
    } else if (mode === "boolean" && value.trim() && !booleanError) {
      metadata.booleanQuery = value.trim()
      const queryText = booleanFinalPrompt.trim() || `Boolean: ${value.trim()}`
      metadata.searchText = queryText
      onSubmit(queryText, entities, mode, metadata)
    } else if (mode === "jd" && jdContent.trim()) {
      metadata.jobDescription = jdContent.trim()
      const queryText = jdSearchPrompt.trim() || `Job Description Analysis`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    } else if (mode === "similar") {
      const validUrls = similarUrls.filter(url => url.trim().length > 0)
      if (validUrls.length === 0 && similarCvFiles.length === 0) return

      metadata.similarProfileUrls = validUrls
      metadata.similarProfileUrl = validUrls[0] || ""

      if (combinedSuggestions.length > 0) {
        metadata.combinedProfile = { keywords: combinedSuggestions }
      }

      const queryText = similarSearchPrompt.trim() || `Similar to: ${validUrls[0] || "CV upload"}`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    } else if (mode === "archetypes" && selectedArchetype) {
      metadata.archetypeVacancyId = selectedArchetype.id
      metadata.archetypeCandidateId = selectedArchetype.hired_candidate?.id
      metadata.archetypeProfile = selectedArchetype.hired_candidate
      const queryText = archetypeSearchPrompt.trim() || `Arquétipo: ${selectedArchetype.title}`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    }
  }

  return {
    parseQuery,
    analyzeSearch,
    fetchPromptEnhancement,
    handleAcceptEnhancement,
    handleEditEnhancement,
    handleDismissEnhancement,
    handleApplySuggestion,
    handleSourceChange,
    confirmSourceChange,
    fetchAutocomplete,
    handleAutocompleteSelect,
    validateBoolean,
    loadArchetypes,
    loadClosedJobSuggestions,
    searchJobsForArchetype,
    openArchetypeFromJob,
    createArchetypeFromJob,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    deleteArchetype,
    addSimilarUrl,
    removeSimilarUrl,
    updateSimilarUrl,
    handleCvUpload,
    removeCvFile,
    removeSuggestion,
    addSuggestion,
    analyzeProfiles,
    hasMultipleSources,
    buildArchetypePrompt,
    handleSubmit,
  }
}
