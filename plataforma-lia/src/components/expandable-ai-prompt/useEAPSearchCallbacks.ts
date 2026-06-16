"use client"

import React, { useCallback, useMemo } from "react"
import type { SearchSpec } from "@/lib/api/candidate-search"
import {
  type BackendEntities,
  type SearchCriterion,
  type SearchAnalysis,
  type AutocompleteSuggestion,
  type SimilarProfile,
  type UseEAPCallbacksParams,
  ENTITY_LABELS,
  CRITERIA_TYPE_MAP,
} from './useEAPCallbacksTypes'

export function useEAPSearchCallbacks(params: UseEAPCallbacksParams) {
  const {
    parsedEntities,
    naturalSearchValue,
    promptEnhancement,
    promptEnhancementDismissed,
    dismissedQueryRef,
    autocompleteCache,
    similarProfiles,
    similarUrls,
    similarCvFiles,
    showAutocomplete,
    autocompleteSuggestions,
    selectedAutocompleteIndex,
    extractedCriteria,
    onCommand,
    pendingSourceChange,
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
    setSearchSource,
    setPendingSourceChange,
    setShowSourceChangeModal,
    setExtractedCriteria,
    setSearchAnalysis,
    setParsedEntities,
    setIsParsingEntities,
    setIsEnhancingPrompt,
    MAX_SIMILAR_URLS,
    MAX_CV_FILES,
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

  return {
    parseEntitiesFromQueryCb,
    fetchPromptEnhancement,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    fetchAutocomplete,
    analyzeCombinedProfiles,
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
    buildSearchSpecFromEntities,
    canSaveAsArchetype,
  }
}
