"use client"

import React, { useCallback, useMemo } from "react"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import type { SearchSpec } from "@/lib/api/candidate-search"

interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

const ENTITY_LABELS: Record<string, string> = {
  job_title: 'Cargo',
  location: 'Localização',
  years_experience: 'Experiência',
  industry: 'Setor',
  skills: 'Habilidades',
  seniority: 'Senioridade',
  company: 'Empresa'
}

const CRITERIA_TYPE_MAP: Record<string, string> = {
  'Cargo': 'job_title',
  'Localização': 'location',
  'Experiência': 'years_experience',
  'Setor': 'industry',
  'Habilidades': 'skills',
  'Habilidade': 'skills',
  'Senioridade': 'seniority',
  'Empresa': 'company'
}

interface SearchCriterion {
  id: string
  type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
  label: string
  value: string
  active: boolean
}

interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

interface AutocompleteSuggestion {
  text: string
  category: string
  icon?: string
  description?: string
  insert_text?: string
}

interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

interface SearchFilters {
  ppiOptions: Record<string, unknown>
  general: Record<string, unknown>
  locations: Record<string, unknown>
  job: Record<string, unknown>
  company: Record<string, unknown>
  skills: Record<string, unknown>
  education: Record<string, unknown>
  languages: Record<string, unknown>
}

interface UseEAPCallbacksParams {
  toast: (opts: Record<string, unknown>) => void
  parseEntitiesFromQuery: (query: string) => Promise<void>
  parsedEntities: BackendEntities
  advancedFilters: SearchFilters
  naturalSearchValue: string
  promptEnhancement: {
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null
  promptEnhancementDismissed: boolean
  dismissedQueryRef: React.MutableRefObject<string>
  autocompleteCache: React.MutableRefObject<Map<string, AutocompleteSuggestion[]>>
  similarProfiles: SimilarProfile[]
  similarUrls: string[]
  similarCvFiles: File[]
  editingArchetype: ArchetypeData | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  archetypeToDelete: { id: string; name: string } | null
  showAutocomplete: boolean
  autocompleteSuggestions: AutocompleteSuggestion[]
  selectedAutocompleteIndex: number
  extractedCriteria: SearchCriterion[]
  onCommand: (command: string, action: string) => void
  selectedCandidates: Record<string, unknown>[]
  candidateContext: Record<string, unknown> | null
  savedTemplates: Record<string, unknown>[]
  filteredCount: number
  totalCount: number
  inputValue: string
  isProcessing: boolean
  isExpanded: boolean
  templateSuggestions: Record<string, unknown>
  suggestionQueue: Record<string, unknown>
  setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  setShowPremiumAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancement: React.Dispatch<React.SetStateAction<typeof promptEnhancement>>
  setPromptEnhancementDismissed: React.Dispatch<React.SetStateAction<boolean>>
  setAutocompleteSuggestions: React.Dispatch<React.SetStateAction<AutocompleteSuggestion[]>>
  setShowAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  setSimilarProfiles: React.Dispatch<React.SetStateAction<SimilarProfile[]>>
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  setSimilarCvFiles: React.Dispatch<React.SetStateAction<File[]>>
  setCombinedSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  setShowCombinedSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  setCombinedProfileKeywords: React.Dispatch<React.SetStateAction<string[]>>
  setIsAnalyzingProfiles: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypes: React.Dispatch<React.SetStateAction<ArchetypeData[]>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedJobForArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<ArchetypeData | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setShowDeleteArchetypeDialog: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeToDelete: React.Dispatch<React.SetStateAction<{ id: string; name: string } | null>>
  setIsCreatingFromSearch: React.Dispatch<React.SetStateAction<boolean>>
  setNewArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setSearchSource: React.Dispatch<React.SetStateAction<'local' | 'global' | 'hybrid'>>
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  setExtractedCriteria: React.Dispatch<React.SetStateAction<SearchCriterion[]>>
  setSearchAnalysis: React.Dispatch<React.SetStateAction<SearchAnalysis | null>>
  setParsedEntities: React.Dispatch<React.SetStateAction<BackendEntities>>
  setIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  setIsEnhancingPrompt: React.Dispatch<React.SetStateAction<boolean>>
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>
  setLastCommand: React.Dispatch<React.SetStateAction<string>>
  setCommandHistory: React.Dispatch<React.SetStateAction<string[]>>
  setInputValue: React.Dispatch<React.SetStateAction<string>>
  setIsExpanded: React.Dispatch<React.SetStateAction<boolean>>
  setShowHistory: React.Dispatch<React.SetStateAction<boolean>>
  MAX_SIMILAR_URLS: number
  MAX_CV_FILES: number
  pendingSourceChange: 'hybrid' | 'global' | null
}

export function useEAPCallbacks(params: UseEAPCallbacksParams) {
  const {
    toast,
    parseEntitiesFromQuery,
    parsedEntities,
    advancedFilters,
    naturalSearchValue,
    promptEnhancement,
    promptEnhancementDismissed,
    dismissedQueryRef,
    autocompleteCache,
    similarProfiles,
    similarUrls,
    similarCvFiles,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    archetypeToDelete,
    showAutocomplete,
    autocompleteSuggestions,
    selectedAutocompleteIndex,
    extractedCriteria,
    onCommand,
    selectedCandidates,
    candidateContext,
    savedTemplates,
    filteredCount,
    totalCount,
    inputValue,
    isProcessing,
    templateSuggestions,
    suggestionQueue,
    setNaturalSearchValue,
    setShowPremiumAutocomplete,
    setPromptEnhancement,
    setPromptEnhancementDismissed,
    setAutocompleteSuggestions,
    setShowAutocomplete,
    setSelectedAutocompleteIndex,
    setSimilarProfiles,
    setSimilarUrls,
    setSimilarCvFiles,
    setCombinedSuggestions,
    setShowCombinedSuggestions,
    setCombinedProfileKeywords,
    setIsAnalyzingProfiles,
    setArchetypes,
    setIsCreatingArchetype,
    setSelectedJobForArchetype,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setNewTagInput,
    setIsSavingArchetype,
    setIsDeletingArchetype,
    setShowDeleteArchetypeDialog,
    setArchetypeToDelete,
    setIsCreatingFromSearch,
    setNewArchetypeDescription,
    setSearchSource,
    setPendingSourceChange,
    setShowSourceChangeModal,
    setExtractedCriteria,
    setSearchAnalysis,
    setParsedEntities,
    setIsParsingEntities,
    setIsEnhancingPrompt,
    setIsProcessing,
    setLastCommand,
    setCommandHistory,
    setInputValue,
    setIsExpanded,
    setShowHistory,
    MAX_SIMILAR_URLS,
    MAX_CV_FILES,
    pendingSourceChange,
  } = params

  const parseEntitiesFromQueryCb = useCallback(async (query: string) => {
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
          const newCriteria: SearchCriterion[] = []
          let idx = 0

          if (entities.job_title) {
            newCriteria.push({
              id: `entity-job_title-${idx++}`,
              type: 'job_title',
              label: ENTITY_LABELS.job_title,
              value: entities.job_title,
              active: true
            })
          }

          if (entities.location) {
            newCriteria.push({
              id: `entity-location-${idx++}`,
              type: 'location',
              label: ENTITY_LABELS.location,
              value: entities.location,
              active: true
            })
          }

          if (entities.years_experience) {
            newCriteria.push({
              id: `entity-years_experience-${idx++}`,
              type: 'years_experience',
              label: ENTITY_LABELS.years_experience,
              value: entities.years_experience,
              active: true
            })
          }

          if (entities.industry) {
            newCriteria.push({
              id: `entity-industry-${idx++}`,
              type: 'industry',
              label: ENTITY_LABELS.industry,
              value: entities.industry,
              active: true
            })
          }

          if (entities.skills && entities.skills.length > 0) {
            entities.skills.forEach((skill, skillIdx) => {
              newCriteria.push({
                id: `entity-skills-${idx++}-${skillIdx}`,
                type: 'skills',
                label: 'Habilidade',
                value: skill,
                active: true
              })
            })
          }

          if (entities.seniority) {
            newCriteria.push({
              id: `entity-seniority-${idx++}`,
              type: 'seniority',
              label: ENTITY_LABELS.seniority,
              value: entities.seniority,
              active: true
            })
          }

          if (entities.company) {
            newCriteria.push({
              id: `entity-company-${idx++}`,
              type: 'company',
              label: ENTITY_LABELS.company,
              value: entities.company,
              active: true
            })
          }

          setExtractedCriteria(newCriteria)
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
  }, [setSearchAnalysis, setExtractedCriteria, setParsedEntities, setIsParsingEntities])

  const fetchPromptEnhancement = useCallback(async (query: string) => {
    if (!query || query.length < 10 || promptEnhancementDismissed) {
      setPromptEnhancement(null)
      return
    }

    setIsEnhancingPrompt(true)
    try {
      const response = await fetch('/api/backend-proxy/enhance-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.enhanced_query && data.enhanced_query !== query) {
          setPromptEnhancement(data)
        }
      }
    } catch (error) {
    } finally {
      setIsEnhancingPrompt(false)
    }
  }, [promptEnhancementDismissed, setPromptEnhancement, setIsEnhancingPrompt])

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      setNaturalSearchValue(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement, setNaturalSearchValue, setPromptEnhancement])

  const handleDismissEnhancement = useCallback(() => {
    dismissedQueryRef.current = naturalSearchValue
    setPromptEnhancementDismissed(true)
    setPromptEnhancement(null)
  }, [naturalSearchValue, dismissedQueryRef, setPromptEnhancementDismissed, setPromptEnhancement])

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      const keywords: string[] = []
      if (analysis.keywords && analysis.keywords.length > 0) {
        keywords.push(...analysis.keywords.slice(0, 5))
      }
      if (analysis.entities) {
        if (analysis.entities.skills) keywords.push(...analysis.entities.skills.slice(0, 3))
        if (analysis.entities.job_titles) keywords.push(...analysis.entities.job_titles.slice(0, 2))
        if (analysis.entities.locations) keywords.push(...analysis.entities.locations.slice(0, 2))
      }
      const uniqueKeywords = [...new Set(keywords)]
      if (uniqueKeywords.length > 0) {
        const searchText = uniqueKeywords.join(', ')
        setNaturalSearchValue(prev => prev ? `${prev}, ${searchText}` : searchText)
        parseEntitiesFromQuery(searchText)
        toast({
          title: "Arquivo analisado",
          description: `Extraídos ${uniqueKeywords.length} critérios de ${file.name}`,
        })
      } else {
        toast({
          title: "Arquivo processado",
          description: `${file.name} foi analisado mas não foram encontrados critérios de busca`,
          variant: "default"
        })
      }
    } else {
      toast({
        title: "Erro na análise",
        description: analysis.error || "Não foi possível analisar o arquivo",
        variant: "destructive"
      })
    }
  }, [toast, parseEntitiesFromQuery, setNaturalSearchValue])

  const handleAudioTranscription = useCallback((text: string) => {
    if (text && text.trim()) {
      setNaturalSearchValue(prev => {
        const newValue = prev ? `${prev} ${text.trim()}` : text.trim()
        parseEntitiesFromQuery(newValue)
        return newValue
      })
      setShowPremiumAutocomplete(true)
      toast({
        title: "Transcrição concluída",
        description: "Texto adicionado à busca",
      })
    }
  }, [toast, parseEntitiesFromQuery, setNaturalSearchValue, setShowPremiumAutocomplete])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    setNaturalSearchValue(suggestion)
    setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery, setNaturalSearchValue, setShowPremiumAutocomplete])

  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
      return
    }

    const cacheKey = query.toLowerCase().trim()
    if (autocompleteCache.current.has(cacheKey)) {
      setAutocompleteSuggestions(autocompleteCache.current.get(cacheKey) || [])
      setShowAutocomplete(true)
      return
    }

    try {
      const res = await fetch(`/api/backend-proxy/search-assistant/autocomplete/?query=${encodeURIComponent(query)}`)
      if (res.ok) {
        const data = await res.json()
        const items = data.items || []
        const suggestions: AutocompleteSuggestion[] = items.map((item: Record<string, unknown>) => ({
          text: item.text,
          category: item.category,
          icon: item.icon,
          description: item.description,
          insert_text: item.insert_text || item.text
        }))
        autocompleteCache.current.set(cacheKey, suggestions)
        setAutocompleteSuggestions(suggestions)
        setShowAutocomplete(suggestions.length > 0)
      }
    } catch (error) {
    }
  }, [autocompleteCache, setAutocompleteSuggestions, setShowAutocomplete])

  const analyzeCombinedProfiles = useCallback(async () => {
    if (similarProfiles.length === 0) return

    setIsAnalyzingProfiles(true)

    try {
      const formData = new FormData()
      similarProfiles.forEach(profile => {
        if (profile.type === 'linkedin') {
          formData.append('urls', profile.url)
        }
      })

      const res = await fetch('/api/backend-proxy/search/similar/combine-profiles', {
        method: 'POST',
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        setCombinedProfileKeywords(data.keywords || [])
      }
    } catch (error) {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarProfiles, setIsAnalyzingProfiles, setCombinedProfileKeywords])

  const createArchetypeFromJob = useCallback(async (jobId: string) => {
    setIsCreatingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/from-job/${jobId}/`, {
        method: 'POST'
      })

      if (res.ok) {
        const data = await res.json()
        setArchetypes(prev => [...prev, data])
        setSelectedJobForArchetype(null)
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [setIsCreatingArchetype, setArchetypes, setSelectedJobForArchetype])

  const hasParsedEntities = useCallback(() => {
    return !!(
      parsedEntities.job_title ||
      parsedEntities.location ||
      parsedEntities.seniority ||
      parsedEntities.industry ||
      parsedEntities.company ||
      parsedEntities.years_experience ||
      (parsedEntities.skills && parsedEntities.skills.length > 0)
    )
  }, [parsedEntities])

  const buildSearchSpec = useCallback(() => {
    const spec: Record<string, unknown> = {}

    if (parsedEntities.job_title) spec.job_title = parsedEntities.job_title
    if (parsedEntities.location) spec.location = parsedEntities.location
    if (parsedEntities.seniority) spec.seniority = parsedEntities.seniority
    if (parsedEntities.industry) spec.industry = parsedEntities.industry
    if (parsedEntities.company) spec.company = parsedEntities.company
    if (parsedEntities.years_experience) spec.years_experience = parsedEntities.years_experience
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      spec.skills = parsedEntities.skills
    }

    if (advancedFilters.locations?.locations && (advancedFilters.locations.locations as string[]).length > 0) {
      spec.locations = advancedFilters.locations.locations
    }
    if (advancedFilters.job?.titles && (advancedFilters.job.titles as string[]).length > 0) {
      spec.job_titles = advancedFilters.job.titles
    }
    if (advancedFilters.job?.levels && (advancedFilters.job.levels as string[]).length > 0) {
      spec.seniority_levels = advancedFilters.job.levels
    }
    if (advancedFilters.skills?.skillItems && (advancedFilters.skills.skillItems as Array<{ name: string }>).length > 0) {
      spec.required_skills = (advancedFilters.skills.skillItems as Array<{ name: string }>).map(s => s.name)
    }
    if (advancedFilters.languages?.languages && (advancedFilters.languages.languages as string[]).length > 0) {
      spec.languages = advancedFilters.languages.languages
    }
    if (advancedFilters.general?.minExperience) {
      spec.years_experience_min = advancedFilters.general.minExperience
    }
    if (advancedFilters.general?.maxExperience) {
      spec.years_experience_max = advancedFilters.general.maxExperience
    }

    return spec
  }, [parsedEntities, advancedFilters])

  const generateArchetypeName = useCallback(() => {
    const nameParts: string[] = []
    if (parsedEntities.job_title) nameParts.push(parsedEntities.job_title)
    if (parsedEntities.seniority) nameParts.push(parsedEntities.seniority)
    if (parsedEntities.location) nameParts.push(parsedEntities.location)
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      nameParts.push(parsedEntities.skills.slice(0, 2).join('/'))
    }
    return nameParts.length > 0 ? nameParts.slice(0, 3).join(' - ') : undefined
  }, [parsedEntities])

  const createArchetypeFromActiveSearch = useCallback(async () => {
    if (!hasParsedEntities()) {
      toast({
        title: "Busca incompleta",
        description: "Faça uma busca com critérios definidos antes de salvar como arquétipo.",
        variant: "destructive"
      })
      return
    }

    setIsCreatingFromSearch(true)
    try {
      const searchSpec = buildSearchSpec()
      const generatedName = generateArchetypeName()

      const payload = {
        search_spec: searchSpec,
        name: generatedName,
        description: naturalSearchValue || "Arquétipo criado a partir de busca",
        emoji: "🎯"
      }

      const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        const data = await res.json()
        const newArchetype = data.archetype || data
        setArchetypes(prev => [...prev, newArchetype])
        toast({
          title: "Arquétipo salvo!",
          description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado a partir da sua busca.`
        })
      } else {
        const error = await res.json()
        toast({
          title: "Erro ao salvar arquétipo",
          description: error.detail || error.error || "Não foi possível salvar o arquétipo.",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erro ao salvar arquétipo",
        description: "Ocorreu um erro de conexão. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsCreatingFromSearch(false)
    }
  }, [hasParsedEntities, buildSearchSpec, generateArchetypeName, naturalSearchValue, toast, setIsCreatingFromSearch, setArchetypes])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    if (!description.trim()) return

    setIsCreatingArchetype(true)
    try {
      const generatedName = generateArchetypeName()

      if (hasParsedEntities()) {
        const searchSpec = buildSearchSpec()

        const payload = {
          search_spec: searchSpec,
          name: generatedName,
          description,
          emoji: "🎯"
        }

        const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast({
            title: "Arquétipo criado",
            description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.`
          })
        } else {
          const error = await res.json()
          toast({
            title: "Erro ao criar arquétipo",
            description: error.detail || error.error || "Não foi possível criar o arquétipo.",
            variant: "destructive"
          })
        }
      } else {
        const payload: Record<string, unknown> = {
          description,
          name: generatedName,
          emoji: "🎯"
        }

        const res = await fetch('/api/backend-proxy/search/archetypes/from-description/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast({
            title: "Arquétipo criado",
            description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.`
          })
        } else {
          const error = await res.json()
          toast({
            title: "Erro ao criar arquétipo",
            description: error.detail || error.error || "Não foi possível criar o arquétipo.",
            variant: "destructive"
          })
        }
      }
    } catch (error) {
      toast({
        title: "Erro ao criar arquétipo",
        description: "Ocorreu um erro de conexão. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec, toast, setIsCreatingArchetype, setArchetypes, setNewArchetypeDescription])

  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    const archRecord = arch as Record<string, unknown>
    const query = (archRecord.query as string) || (arch.criteria?.query as string) || ""
    setEditArchetypeQuery(query)
    setEditArchetypeDescription(arch.description || "")
    const emoji = (archRecord.emoji as string) || (arch.criteria?.emoji as string) || "🎯"
    setEditArchetypeEmoji(emoji)
    const tags: string[] = []
    const criteria = arch.criteria || {}
    if (criteria.job_title) tags.push(criteria.job_title as string)
    if (criteria.location) tags.push(criteria.location as string)
    if (criteria.seniority) tags.push(criteria.seniority as string)
    if (criteria.industry) tags.push(criteria.industry as string)
    if (criteria.skills && Array.isArray(criteria.skills)) {
      tags.push(...(criteria.skills as string[]))
    }
    setEditArchetypeTags(tags)
    setNewTagInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setNewTagInput])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setNewTagInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setNewTagInput])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return

    setIsSavingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${editingArchetype.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editArchetypeName.trim(),
          query: editArchetypeQuery.trim(),
          description: editArchetypeDescription.trim() || null,
          emoji: editArchetypeEmoji || "🎯",
          tags: editArchetypeTags.length > 0 ? editArchetypeTags : null
        })
      })

      if (res.ok) {
        const updated = await res.json()
        setArchetypes(prev => prev.map(a => a.id === editingArchetype.id ? { ...a, ...updated } : a))
        closeEditArchetype()
        toast({
          title: "Arquétipo atualizado",
          description: `"${editArchetypeName}" foi salvo com sucesso.`
        })
      } else {
        const error = await res.json()
        toast({
          title: "Erro ao atualizar arquétipo",
          description: error.detail || error.error || "Não foi possível salvar as alterações.",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erro ao atualizar arquétipo",
        description: "Ocorreu um erro de conexão. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, closeEditArchetype, toast, setIsSavingArchetype, setArchetypes])

  const openDeleteArchetypeDialog = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setArchetypeToDelete({ id: arch.id, name: arch.name })
    setShowDeleteArchetypeDialog(true)
  }, [setArchetypeToDelete, setShowDeleteArchetypeDialog])

  const confirmDeleteArchetype = useCallback(async () => {
    if (!archetypeToDelete) return

    const archId = archetypeToDelete.id
    const archName = archetypeToDelete.name
    setIsDeletingArchetype(archId)
    setShowDeleteArchetypeDialog(false)

    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${archId}/`, {
        method: 'DELETE'
      })

      if (res.ok) {
        setArchetypes(prev => prev.filter(a => a.id !== archId))
        toast({
          title: "Arquétipo excluído",
          description: `"${archName}" foi removido com sucesso.`
        })
      } else {
        const error = await res.json()
        toast({
          title: "Erro ao excluir arquétipo",
          description: error.detail || error.error || "Não foi possível excluir o arquétipo.",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erro ao excluir arquétipo",
        description: "Ocorreu um erro de conexão. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsDeletingArchetype(null)
      setArchetypeToDelete(null)
    }
  }, [archetypeToDelete, toast, setIsDeletingArchetype, setShowDeleteArchetypeDialog, setArchetypes, setArchetypeToDelete])

  const addSimilarProfile = useCallback((url: string, type: 'linkedin' | 'cv' = 'linkedin', filename?: string) => {
    if (similarProfiles.length >= 3) return
    if (similarProfiles.some(p => p.url === url)) return
    setSimilarProfiles(prev => [...prev, { url, type, filename }])
  }, [similarProfiles, setSimilarProfiles])

  const removeSimilarProfile = useCallback((url: string) => {
    setSimilarProfiles(prev => prev.filter(p => p.url !== url))
  }, [setSimilarProfiles])

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

  const updateSimilarUrl = useCallback((index: number, value: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = value
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

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 1
  }, [similarUrls, similarCvFiles])

  const analyzeProfiles = useCallback(async () => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    if (validUrls.length === 0 && similarCvFiles.length === 0) return

    setIsAnalyzingProfiles(true)
    try {
      const formData = new FormData()
      validUrls.forEach(url => formData.append('urls', url))
      similarCvFiles.forEach(file => formData.append('cvs', file))

      const response = await fetch('/api/backend-proxy/search/similar/combine-profiles', {
        method: "POST",
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        const keywords = data.keywords || []
        setCombinedSuggestions(keywords)
        setShowCombinedSuggestions(true)

        if (data.title) {
          setCombinedProfileKeywords(prev => {
            const combined = [...keywords]
            if (data.title && !combined.includes(data.title)) combined.push(data.title)
            if (data.location && !combined.includes(data.location)) combined.push(data.location)
            return combined
          })
        }

        if (keywords.length > 0) {
          const searchQuery = keywords.slice(0, 6).join(', ')
          setNaturalSearchValue(searchQuery)
        }
      }
    } catch (error) {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles, setIsAnalyzingProfiles, setCombinedSuggestions, setShowCombinedSuggestions, setCombinedProfileKeywords, setNaturalSearchValue])

  const handleAutocompleteKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showAutocomplete || autocompleteSuggestions.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev =>
        prev < autocompleteSuggestions.length - 1 ? prev + 1 : 0
      )
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev =>
        prev > 0 ? prev - 1 : autocompleteSuggestions.length - 1
      )
    } else if (e.key === 'Tab' || e.key === 'Enter') {
      if (autocompleteSuggestions[selectedAutocompleteIndex]) {
        e.preventDefault()
        const selected = autocompleteSuggestions[selectedAutocompleteIndex]
        const insertValue = selected.insert_text || selected.text
        setNaturalSearchValue(prev => {
          const words = prev.split(' ')
          words.pop()
          return [...words, insertValue].join(' ') + ' '
        })
        setShowAutocomplete(false)
      }
    } else if (e.key === 'Escape') {
      setShowAutocomplete(false)
    }
  }, [showAutocomplete, autocompleteSuggestions, selectedAutocompleteIndex, setSelectedAutocompleteIndex, setNaturalSearchValue, setShowAutocomplete])

  const handleSourceChange = (newSource: 'local' | 'hybrid' | 'global') => {
    if (newSource === 'local') {
      setSearchSource('local')
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  const confirmSourceChange = () => {
    if (pendingSourceChange) {
      setSearchSource(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }

  const removeCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.filter(c => c.id !== id))
  }

  const toggleCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.map(c =>
      c.id === id ? { ...c, active: !c.active } : c
    ))
  }

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

  const getAdvancedFilters = () => {
    return {
      selectedCandidates: selectedCandidates.length,
      contextType: 'candidates',
      filteredCount,
      totalCount
    }
  }

  const checkForTemplateSuggestions = () => {
    const pendingSuggestions = (templateSuggestions as Record<string, (...args: unknown[]) => unknown>).getPendingSuggestions() as Array<Record<string, unknown>>
    pendingSuggestions.forEach(suggestion => {
      if ((templateSuggestions as Record<string, (...args: unknown[]) => boolean>).shouldShowSuggestion(suggestion)) {
        (suggestionQueue as Record<string, (...args: unknown[]) => void>).addSuggestion(suggestion)
        ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).markSuggestionAsShown(suggestion.id)
      }
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isProcessing) {
      setIsProcessing(true)
      setLastCommand(inputValue)

      ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).addCommand(inputValue, getAdvancedFilters(), ['text_command'])

      setCommandHistory(prev => [inputValue, ...prev.slice(0, 4)])

      setTimeout(() => {
        onCommand(inputValue, 'text_command')
        setInputValue("")
        setIsExpanded(false)
        setIsProcessing(false)
        checkForTemplateSuggestions()
      }, 1500)
    }
  }

  const handleSuggestionClick = (suggestion: Record<string, unknown>) => {
    if (!isProcessing) {
      setIsProcessing(true)
      setLastCommand(suggestion.label as string)

      if (suggestion.isTemplate) {
        executeTemplate(suggestion.template as Record<string, unknown>)
        return
      }

      ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).addCommand(suggestion.label as string, getAdvancedFilters(), [suggestion.action])

      setCommandHistory(prev => [suggestion.label as string, ...prev.slice(0, 4)])

      setTimeout(() => {
        onCommand(suggestion.label as string, suggestion.action as string)
        setIsExpanded(false)
        setIsProcessing(false)
        checkForTemplateSuggestions()
      }, 1200)
    }
  }

  const executeTemplate = (template: Record<string, unknown>) => {
    const templates = JSON.parse(localStorage.getItem('lia-templates') || '[]')
    const updatedTemplates = templates.map((t: Record<string, unknown>) =>
      t.id === template.id
        ? { ...t, usageCount: (t.usageCount as number) + 1, updatedAt: new Date() }
        : t
    )
    localStorage.setItem('lia-templates', JSON.stringify(updatedTemplates))

    setTimeout(() => {
      onCommand(template.command as string, (template.actions as string[])[0] || 'execute_template')
      setIsExpanded(false)
      setIsProcessing(false)
    }, 1000)
  }

  const buildSearchSpecFromEntities = useMemo((): SearchSpec | null => {
    if (!parsedEntities || Object.keys(parsedEntities).length === 0) {
      return null
    }

    return {
      job_title: parsedEntities.job_title,
      location: parsedEntities.location,
      years_experience: parsedEntities.years_experience,
      industry: parsedEntities.industry,
      skills: parsedEntities.skills,
      seniority: parsedEntities.seniority,
      company: parsedEntities.company,
    }
  }, [parsedEntities])

  const canSaveAsArchetype = useMemo(() => {
    return naturalSearchValue.trim().length > 3 ||
           (parsedEntities && Object.values(parsedEntities).some(v => v && (Array.isArray(v) ? v.length > 0 : true)))
  }, [naturalSearchValue, parsedEntities])

  const handleArchetypeSaved = (newArchetype: ArchetypeData) => {
    setArchetypes(prev => [...prev, newArchetype])
    toast({
      title: "Arquétipo salvo",
      description: `"${newArchetype.name}" foi adicionado aos seus arquétipos.`
    })
  }

  const handleHistoryCommand = (command: string) => {
    setInputValue(command)
    setShowHistory(false)
  }

  const getSmartSuggestions = () => {
    if (candidateContext) {
      return [
        { id: 'analyze_profile', icon: '🔍', label: `Analisar perfil completo de ${(candidateContext as Record<string, unknown>).name}`, description: 'Análise detalhada de competências, fit cultural e potencial', action: 'analyze_individual_profile' },
        { id: 'generate_interview_questions', icon: '❓', label: 'Gerar roteiro de entrevista personalizado', description: 'Perguntas técnicas e comportamentais baseadas no perfil', action: 'generate_interview_questions' },
        { id: 'draft_email', icon: '📧', label: 'Rascunhar convite personalizado', description: 'Email de convite customizado para o candidato', action: 'draft_personalized_email' },
        { id: 'compare_with_role', icon: '⚖️', label: 'Comparar com requisitos da vaga', description: 'Match detalhado com job description', action: 'compare_with_job_requirements' },
        { id: 'predict_success', icon: '🎯', label: 'Predizer sucesso na posição', description: 'Análise preditiva baseada em dados históricos', action: 'predict_candidate_success' },
        { id: 'salary_benchmark', icon: '💰', label: 'Benchmark salarial personalizado', description: 'Comparação com mercado baseada no perfil específico', action: 'salary_benchmark' }
      ]
    }

    const selectedCount = selectedCandidates.length
    const allSuggestions: Array<Record<string, unknown>> = []

    if (selectedCount === 0 && savedTemplates.length > 0) {
      allSuggestions.push(...savedTemplates.map(template => ({
        id: `template-${template.id}`,
        icon: '🔖',
        label: template.name,
        description: `Template salvo • ${template.usageCount} usos`,
        action: 'execute_template',
        template: template,
        isTemplate: true
      })))
    }

    if (selectedCount === 0) {
      const advancedSuggestions = [
        { id: 'smart_search_ai', icon: '🧠', label: 'Busca inteligente com IA', description: 'Descreva o perfil ideal e a LIA encontra candidatos similares', action: 'ai_smart_search', category: 'search' },
        { id: 'boolean_search_expert', icon: '🔧', label: 'Busca booleana avançada', description: 'Construtor visual de queries complexas para LinkedIn/Github', action: 'boolean_search_builder', category: 'search' },
        { id: 'passive_candidates', icon: '🕵️', label: 'Identificar candidatos passivos', description: 'Encontrar talentos que não estão procurando ativamente', action: 'find_passive_candidates', category: 'search' },
        { id: 'competitor_analysis', icon: '🏢', label: 'Mapear concorrentes e talentos', description: 'Análise de empresas similares e seus melhores profissionais', action: 'competitor_talent_mapping', category: 'search' },
        { id: 'pipeline_automation', icon: '⚙️', label: 'Automatizar pipeline de talentos', description: 'Configurar fluxos automáticos para diferentes perfis', action: 'setup_pipeline_automation', category: 'automation' },
        { id: 'email_sequences', icon: '📬', label: 'Sequências de email inteligentes', description: 'Campanhas de nurturing personalizadas por segmento', action: 'create_email_sequences', category: 'automation' },
        { id: 'calendar_optimization', icon: '📅', label: 'Otimizar agenda de entrevistas', description: 'Sugerir melhor organização e horários mais eficientes', action: 'optimize_interview_calendar', category: 'automation' },
        { id: 'market_trends', icon: '📈', label: 'Análise de tendências do mercado', description: 'Insights sobre salários, demanda e escassez de talentos', action: 'analyze_market_trends', category: 'analytics' },
        { id: 'diversity_analysis', icon: '🌈', label: 'Análise de diversidade e inclusão', description: 'Métricas D&I e sugestões para melhorar representatividade', action: 'diversity_inclusion_analysis', category: 'analytics' },
        { id: 'conversion_funnels', icon: '🎯', label: 'Análise de funis de conversão', description: 'Identificar gargalos e oportunidades de melhoria', action: 'analyze_conversion_funnels', category: 'analytics' },
        { id: 'predictive_hiring', icon: '🔮', label: 'Previsões de contratação', description: 'Predizer necessidades futuras baseado em crescimento', action: 'predictive_hiring_analysis', category: 'analytics' },
        { id: 'interview_scorecards', icon: '📋', label: 'Criar scorecards de entrevista', description: 'Formulários estruturados para avaliação consistente', action: 'create_interview_scorecards', category: 'tools' },
        { id: 'reference_automation', icon: '📞', label: 'Automatizar checagem de referências', description: 'Templates e fluxos para verificação de background', action: 'automate_reference_checks', category: 'tools' },
        { id: 'onboarding_preparation', icon: '🎯', label: 'Preparar onboarding personalizado', description: 'Planos customizados baseados no perfil do novo hire', action: 'prepare_custom_onboarding', category: 'tools' },
        { id: 'salary_intelligence', icon: '💎', label: 'Inteligência salarial avançada', description: 'Benchmarks detalhados por região, experiência e skills', action: 'advanced_salary_intelligence', category: 'intelligence' },
        { id: 'skill_gap_analysis', icon: '🔍', label: 'Análise de lacunas de habilidades', description: 'Identificar skills em falta no time e no mercado', action: 'skill_gap_analysis', category: 'intelligence' },
        { id: 'employer_branding', icon: '✨', label: 'Otimizar employer branding', description: 'Sugestões para melhorar atratividade da empresa', action: 'optimize_employer_branding', category: 'intelligence' }
      ]

      const shuffled = advancedSuggestions.sort(() => 0.5 - Math.random())
      allSuggestions.push(...shuffled.slice(0, 10))
      return allSuggestions
    }

    if (selectedCount === 1) {
      const candidate = selectedCandidates[0]
      const candidateName = (candidate.name as string) || 'Candidato'
      const candidateScore = ((candidate.liaAnalysis as Record<string, unknown>)?.score as number) || (candidate.score as number) || 0

      const individualSuggestions = [
        { id: 'send_personalized_email', icon: '📧', label: `Enviar convite personalizado para ${candidateName}`, description: 'Email customizado baseado no perfil e interesses', action: 'send_personalized_email' },
        { id: 'schedule_interview', icon: '📅', label: 'Agendar entrevista estratégica', description: 'Escolher melhor horário e formato baseado no perfil', action: 'schedule_strategic_interview' },
        { id: 'deep_profile_analysis', icon: '🔬', label: 'Análise profunda do perfil', description: 'Investigação completa de competências e fit cultural', action: 'deep_profile_analysis' },
        { id: 'salary_negotiation_prep', icon: '💰', label: 'Preparar negociação salarial', description: 'Estratégia e faixas baseadas no perfil específico', action: 'prepare_salary_negotiation' },
        { id: 'reference_check_strategy', icon: '📋', label: 'Estratégia de referências', description: 'Plano para checagem de background e referências', action: 'plan_reference_checks' },
        { id: 'competitor_intel', icon: '🕵️', label: 'Intel sobre empresa atual', description: 'Pesquisa sobre empresa e possíveis motivadores', action: 'research_current_company' }
      ]

      if (candidateScore >= 85) {
        individualSuggestions.push({ id: 'fast_track_vip', icon: '⚡', label: 'Fast-track VIP', description: 'Processo acelerado para candidato excepcional', action: 'vip_fast_track' })
      }

      if (candidateScore < 70) {
        individualSuggestions.push({ id: 'improvement_coaching', icon: '📚', label: 'Coaching para candidato', description: 'Sugestões de desenvolvimento para melhorar fit', action: 'candidate_coaching_suggestions' })
      }

      return individualSuggestions
    }

    const batchSuggestions = [
      { id: 'bulk_email_campaign', icon: '📧', label: `Campanha de email para ${selectedCount} candidatos`, description: 'Emails personalizados em massa com A/B testing', action: 'bulk_email_campaign' },
      { id: 'comparative_analysis', icon: '📊', label: `Análise comparativa detalhada`, description: 'Relatório completo comparando perfis selecionados', action: 'detailed_comparative_analysis' },
      { id: 'interview_coordination', icon: '🗓️', label: 'Coordenar entrevistas em lote', description: 'Otimizar agenda para múltiplas entrevistas', action: 'coordinate_batch_interviews' },
      { id: 'shortlist_creation', icon: '⭐', label: 'Criar shortlist inteligente', description: 'Ranking automático baseado em critérios específicos', action: 'create_intelligent_shortlist' },
      { id: 'diversity_check', icon: '🌈', label: 'Verificar diversidade do grupo', description: 'Análise D&I do conjunto de candidatos selecionados', action: 'check_group_diversity' },
      { id: 'salary_range_analysis', icon: '💰', label: 'Análise de faixas salariais', description: 'Comparar expectativas e definir estratégia de ofertas', action: 'analyze_salary_ranges' },
      { id: 'rejection_management', icon: '💔', label: 'Gestão inteligente de rejeições', description: 'Feedback personalizado e manutenção de relacionamento', action: 'manage_intelligent_rejections' }
    ]

    return batchSuggestions
  }

  const getPlaceholder = () => {
    if (candidateContext) {
      return `O que gostaria de fazer com ${(candidateContext as Record<string, unknown>).name}? Ex: analisar perfil, enviar email, agendar entrevista, comparar com outros...`
    }

    const selectedCount = selectedCandidates.length

    if (selectedCount === 0) {
      return "Peça à LIA para filtrar candidatos, fazer buscas específicas, analisar perfis, enviar emails, agendar entrevistas, comparar candidatos..."
    }

    if (selectedCount === 1) {
      return `O que fazer com ${(selectedCandidates[0] as Record<string, unknown>).name}?`
    }

    return `${selectedCount} candidatos selecionados. Como proceder?`
  }

  return {
    parseEntitiesFromQueryCb,
    fetchPromptEnhancement,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    handleFileAnalyzed,
    handleAudioTranscription,
    handlePremiumAutocompleteSelect,
    fetchAutocomplete,
    analyzeCombinedProfiles,
    createArchetypeFromJob,
    hasParsedEntities,
    buildSearchSpec,
    generateArchetypeName,
    createArchetypeFromActiveSearch,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    openDeleteArchetypeDialog,
    confirmDeleteArchetype,
    addSimilarProfile,
    removeSimilarProfile,
    addSimilarUrl,
    removeSimilarUrl,
    updateSimilarUrl,
    handleCvUpload,
    removeCvFile,
    removeSuggestion,
    hasMultipleSources,
    analyzeProfiles,
    handleAutocompleteKeyDown,
    handleSourceChange,
    confirmSourceChange,
    removeCriterion,
    toggleCriterion,
    buildSearchQueryFromCriteria,
    executeSearchWithCriteria,
    handleSubmit,
    handleSuggestionClick,
    handleHistoryCommand,
    handleArchetypeSaved,
    getSmartSuggestions,
    getPlaceholder,
    buildSearchSpecFromEntities,
    canSaveAsArchetype,
  }
}
