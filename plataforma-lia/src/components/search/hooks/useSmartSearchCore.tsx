// @ts-nocheck
"use client"


import { useState, useEffect, useCallback, useRef } from "react"
import { 
  MapPin, Briefcase, Clock, Building2, Code, X, Search, 
  FileText, Binary, Users, Upload, 
  Globe, Target, Loader2, Linkedin,
  AlertTriangle, HelpCircle, Wand2, Brain,
  Pencil, Trash2, Home, Zap, Mail, Phone,
  ChevronUp, ChevronDown, Tag
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { INDUSTRIES, INDUSTRY_CATEGORIES, type Industry } from "@/lib/industry-constants"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { EditArchetypeModal } from "../EditArchetypeModal"
import { SearchModeArchetypes } from "../SearchModeArchetypes"
import { SearchScopeControls } from "./SearchScopeControls"
import { buildHighlightedText } from "./renderHighlightedText"
import {
  type ParsedEntities,
  type SearchSource,
  type SmartSearchInputProps,
  type SearchMode,
  type ArchetypeCandidate,
  type ArchetypeVacancy,
  type SearchMetadata,
  type CombinedProfileSuggestion,
  type SearchTag,
  type SearchAlert,
  type SearchAnalysis,
  type AutocompleteItem,
  type AutocompleteResponse,
  API_BASE,
  SEARCH_SUGGESTIONS,
  MAX_SIMILAR_URLS,
  MAX_CV_FILES,
} from "./smartSearchConstants"
import { useSmartSearchArchetypes } from "./useSmartSearchArchetypes"
import { useSmartSearchSimilar } from "./useSmartSearchSimilar"

export type { ParsedEntities, SearchSource, SmartSearchInputProps, SearchMode, ArchetypeCandidate, ArchetypeVacancy, SearchMetadata, CombinedProfileSuggestion }

export function useSmartSearchCore(props: SmartSearchInputProps) {
  const {
    value,
    onChange,
    onSubmit,
    onCancel,
    onOpenFilters,
    onGoToResults,
    isLoading = false,
    placeholder = "Desenvolvedores Python com 5+ anos em São Paulo...",
    className,
    activeFiltersCount = 0,
    searchSource = "local",
    onSearchSourceChange,
    requireEmails = false,
    onRequireEmailsChange,
    requirePhoneNumbers = false,
    onRequirePhoneNumbersChange
  } = props
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  
  // Only show global/hybrid options after settings are loaded AND global search is enabled
  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled
  const [mode, setMode] = useState<SearchMode>("natural")
  const [entities, setEntities] = useState<ParsedEntities>({})
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [booleanError, setBooleanError] = useState<string | null>(null)
  const [jdContent, setJdContent] = useState("")
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showAssistantTip, setShowAssistantTip] = useState(true)
  const [autocompleteItems, setAutocompleteItems] = useState<AutocompleteItem[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(-1)
  const [usedAutocompleteTerms, setUsedAutocompleteTerms] = useState<Set<string>>(new Set())
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true)
  const [promptEnhancement, setPromptEnhancement] = useState<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>(null)
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [promptEnhancementDismissed, setPromptEnhancementDismissed] = useState(false)
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [jdVacancySearch, setJdVacancySearch] = useState("")
  const [jdVacancyResults, setJdVacancyResults] = useState<Array<{
    id: string
    job_id: string | null
    title: string
    status: string
    created_at: string
    description_preview: string | null
  }>>([])
  const [isSearchingVacancies, setIsSearchingVacancies] = useState(false)
  const [selectedVacancy, setSelectedVacancy] = useState<{
    id: string
    title: string
    job_id: string | null
  } | null>(null)
  const [showVacancyResults, setShowVacancyResults] = useState(false)
  const [jdSearchPrompt, setJdSearchPrompt] = useState("")
  const [booleanFinalPrompt, setBooleanFinalPrompt] = useState("")
  const jdVacancySearchTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const dismissedQueryRef = useRef<string>("")
  const enhanceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const panelWidth = "100%"
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const ghostOverlayRef = useRef<HTMLDivElement>(null)
  const parseTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const analyzeTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const autocompleteAbortRef = useRef<AbortController | null>(null)
  const autocompleteCache = useRef<Map<string, AutocompleteItem[]>>(new Map())
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cvFileInputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Sub-hooks
  const archetypes = useSmartSearchArchetypes()
  const similar = useSmartSearchSimilar()

  // Destructure archetype state for convenience (same names as before)
  const {
    archetypeVacancies, selectedArchetype, isLoadingArchetypes, archetypeSearch,
    archetypeTab, archetypeCreateMode, closedJobSuggestions, isLoadingClosedJobs,
    jobSearchQuery, jobSearchResults, isSearchingJobs, archetypeDescription,
    isCreatingArchetype, editingArchetype, editArchetypeName, editArchetypeQuery,
    editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills,
    editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin,
    editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages,
    editArchetypeEmploymentType, newLanguageInput, newTagInput, newSkillInput,
    isSavingArchetype, isDeletingArchetype, showArchetypeActions, expandedArchetypeId,
    skillSuggestions, isLoadingSkillSuggestions, isFindingSimilarSkills, tagSuggestions,
    isLoadingTagSuggestions, isFindingSimilarTags, aiSuggestedSkills, selectedAiSkills,
    showSkillSuggestions, aiSuggestedTags, selectedAiTags, showTagSuggestions,
    industrySearchQuery, isIndustryDropdownOpen, archetypeSearchPrompt,
    setArchetypeVacancies, setSelectedArchetype, setArchetypeSearch, setArchetypeTab,
    setArchetypeCreateMode, setArchetypeDescription, setJobSearchQuery,
    setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription,
    setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills,
    setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin,
    setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages,
    setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput,
    setShowArchetypeActions, setExpandedArchetypeId, setAiSuggestedSkills, setSelectedAiSkills,
    setShowSkillSuggestions, setAiSuggestedTags, setSelectedAiTags, setShowTagSuggestions,
    setIndustrySearchQuery, setIsIndustryDropdownOpen, setArchetypeSearchPrompt,
    setIsFindingSimilarSkills, setIsFindingSimilarTags,
    loadArchetypes, loadClosedJobSuggestions, searchJobsForArchetype, openArchetypeFromJob,
    createArchetypeFromJob, createArchetypeFromDescription, openEditArchetype, closeEditArchetype,
    saveArchetype, deleteArchetype, buildArchetypePrompt,
  } = archetypes

  // Destructure similar state for convenience
  const {
    similarUrl, similarUrls, similarCvFiles, combinedSuggestions, isAnalyzingProfiles,
    showCombinedSuggestions, similarSearchPrompt,
    setSimilarUrl, setSimilarUrls, setSimilarCvFiles, setCombinedSuggestions,
    setShowCombinedSuggestions, setSimilarSearchPrompt,
    addSimilarUrl, removeSimilarUrl, updateSimilarUrl, handleCvUpload, removeCvFile,
    removeSuggestion, addSuggestion, analyzeProfiles, hasMultipleSources,
  } = similar

  const { 
    suggestions: semanticSkillSuggestions, 
    isLoading: isLoadingSemanticSkills, 
    search: searchSemanticSkills,
    clearSuggestions: clearSemanticSkillSuggestions
  } = useSemanticSearch({ domain: "skills", debounceMs: 400 })

  const { 
    suggestions: semanticTagSuggestions, 
    isLoading: isLoadingSemanticTags, 
    search: searchSemanticTags,
    clearSuggestions: clearSemanticTagSuggestions
  } = useSemanticSearch({ domain: "roles", debounceMs: 400 })

  // Reset search source to local if global search is disabled
  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global') && onSearchSourceChange) {
      onSearchSourceChange('local')
    }
  }, [showGlobalSearchOptions, searchSource, onSearchSourceChange])

  const tags: SearchTag[] = [
    { key: "location", label: "Localização", icon: MapPin, filled: !!entities.location, value: entities.location },
    { key: "job_title", label: "Cargo", icon: Briefcase, filled: !!entities.job_title, value: entities.job_title },
    { key: "years_experience", label: "Experiência", icon: Clock, filled: !!entities.years_experience, value: entities.years_experience },
    { key: "industry", label: "Setor", icon: Building2, filled: !!entities.industry, value: entities.industry },
    { key: "skills", label: "Habilidades", icon: Code, filled: !!(entities.skills && entities.skills.length > 0), value: entities.skills?.join(", ") }
  ]

  const filledCount = tags.filter(t => t.filled).length

  const renderHighlightedText = useCallback(() => {
    return buildHighlightedText(value, entities, filledCount)
  }, [value, entities, filledCount])

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
  }, [])

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
  }, [])

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
  }, [promptEnhancementDismissed])

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement, onChange])

  const handleEditEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
      textareaRef.current?.focus()
    }
  }, [promptEnhancement, onChange])

  const handleDismissEnhancement = useCallback(() => {
    setPromptEnhancement(null)
    setPromptEnhancementDismissed(true)
    dismissedQueryRef.current = value
  }, [value])

  const handleApplySuggestion = useCallback((suggestionValue: string) => {
    const currentValue = value.trim()
    const newValue = currentValue ? `${currentValue}, ${suggestionValue}` : suggestionValue
    onChange(newValue)
    textareaRef.current?.focus()
  }, [value, onChange])

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
        const data: AutocompleteResponse = await response.json()
        const allItems = data.items || []
        const items = allItems.filter(item => !usedAutocompleteTerms.has(item.insert_text.toLowerCase()))
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
  }, [usedAutocompleteTerms])

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
  }, [value, onChange])

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
  }, [])

  useEffect(() => {
    if (mode === "natural") {
      if (parseTimeoutRef.current) {
        clearTimeout(parseTimeoutRef.current)
      }

      parseTimeoutRef.current = setTimeout(() => {
        parseQuery(value)
      }, 300)

      return () => {
        if (parseTimeoutRef.current) {
          clearTimeout(parseTimeoutRef.current)
        }
      }
    } else if (mode === "boolean") {
      validateBoolean(value)
    }
  }, [value, mode, parseQuery, validateBoolean])

  useEffect(() => {
    if (mode === "natural" && value && Object.keys(entities).length > 0) {
      if (analyzeTimeoutRef.current) {
        clearTimeout(analyzeTimeoutRef.current)
      }

      analyzeTimeoutRef.current = setTimeout(() => {
        analyzeSearch(value, entities)
      }, 500)

      return () => {
        if (analyzeTimeoutRef.current) {
          clearTimeout(analyzeTimeoutRef.current)
        }
      }
    }
  }, [entities, value, mode, analyzeSearch])

  useEffect(() => {
    if (mode === "natural" && value && autocompleteEnabled) {
      if (autocompleteTimeoutRef.current) {
        clearTimeout(autocompleteTimeoutRef.current)
      }

      autocompleteTimeoutRef.current = setTimeout(() => {
        fetchAutocomplete(value)
      }, 80)

      return () => {
        if (autocompleteTimeoutRef.current) {
          clearTimeout(autocompleteTimeoutRef.current)
        }
      }
    } else {
      setShowAutocomplete(false)
      setAutocompleteItems([])
    }
  }, [value, mode, fetchAutocomplete, autocompleteEnabled])

  useEffect(() => {
    if (!value || value.trim().length === 0) {
      setUsedAutocompleteTerms(new Set())
    }
  }, [value])

  useEffect(() => {
    setUsedAutocompleteTerms(new Set())
  }, [mode])

  useEffect(() => {
    if (promptEnhancementDismissed && dismissedQueryRef.current) {
      const dismissedPrefix = dismissedQueryRef.current.toLowerCase().slice(0, 15)
      const currentPrefix = value.toLowerCase().slice(0, 15)
      const prefixChanged = currentPrefix !== dismissedPrefix
      const lengthChanged = Math.abs(value.length - dismissedQueryRef.current.length) > 10
      if (prefixChanged || lengthChanged) {
        setPromptEnhancementDismissed(false)
        dismissedQueryRef.current = ""
      }
    }
    
    if (mode === "natural" && value && value.length >= 10 && !promptEnhancementDismissed) {
      if (enhanceTimeoutRef.current) {
        clearTimeout(enhanceTimeoutRef.current)
      }

      enhanceTimeoutRef.current = setTimeout(() => {
        fetchPromptEnhancement(value)
      }, 1200)

      return () => {
        if (enhanceTimeoutRef.current) {
          clearTimeout(enhanceTimeoutRef.current)
        }
      }
    } else if (!promptEnhancementDismissed) {
      setPromptEnhancement(null)
    }
  }, [value, mode, searchSource, fetchPromptEnhancement, promptEnhancementDismissed])

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  useEffect(() => {
    setEntities({})
    setBooleanError(null)
    setSelectedArchetype(null)
    setSimilarSearchPrompt("")
    setJdSearchPrompt("")
    setBooleanFinalPrompt("")
    setArchetypeSearchPrompt("")
    if (mode === "jd") {
      onChange("")
    }
    if (mode === "archetypes") {
      loadArchetypes()
      loadClosedJobSuggestions()
    }
  }, [mode, loadArchetypes, loadClosedJobSuggestions])

  useEffect(() => {
    if (combinedSuggestions.length > 0 && showCombinedSuggestions) {
      const validUrls = similarUrls.filter(url => url.trim().length > 0)
      const sourceCount = validUrls.length + similarCvFiles.length
      const prompt = sourceCount > 1 
        ? `Buscar candidatos similares aos ${sourceCount} perfis analisados. Características combinadas: ${combinedSuggestions.join(", ")}`
        : `Buscar candidatos similares ao perfil: ${combinedSuggestions.join(", ")}`
      setSimilarSearchPrompt(prompt)
    }
  }, [combinedSuggestions, showCombinedSuggestions, similarUrls, similarCvFiles])

  useEffect(() => {
    if (jdContent.trim().length > 0) {
      const preview = jdContent.length > 200 
        ? `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent.slice(0, 200)}...`
        : `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent}`
      setJdSearchPrompt(preview)
    } else {
      setJdSearchPrompt("")
    }
  }, [jdContent])

  useEffect(() => {
    if (value.trim() && mode === "boolean") {
      setBooleanFinalPrompt(`Busca booleana: ${value.trim()}`)
    } else {
      setBooleanFinalPrompt("")
    }
  }, [value, mode])

  useEffect(() => {
    if (selectedArchetype) {
      const prompt = buildArchetypePrompt(selectedArchetype)
      setArchetypeSearchPrompt(prompt)
    } else {
      setArchetypeSearchPrompt("")
    }
  }, [selectedArchetype, buildArchetypePrompt])

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
        metadata.combinedProfile = {
          keywords: combinedSuggestions
        }
      }
      
      // Use similarSearchPrompt if available, otherwise fallback to default text
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

  const getGhostTextInfo = useCallback((): { suffix: string | null; showFallbackCard: boolean; fullEnhancement: string | null } => {
    if (!promptEnhancement || showAutocomplete || isEnhancingPrompt) {
      return { suffix: null, showFallbackCard: false, fullEnhancement: null }
    }
    const enhanced = promptEnhancement.enhanced_query
    const userText = value
    if (enhanced.toLowerCase().startsWith(userText.toLowerCase())) {
      return { suffix: enhanced.slice(userText.length), showFallbackCard: false, fullEnhancement: null }
    }
    return { suffix: null, showFallbackCard: true, fullEnhancement: enhanced }
  }, [promptEnhancement, value, showAutocomplete, isEnhancingPrompt])

  const ghostTextInfo = getGhostTextInfo()
  const ghostTextSuffix = ghostTextInfo.suffix

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const visibleItems = Math.min(autocompleteItems.length, 5)
    if (showAutocomplete && visibleItems > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev => 
          prev < visibleItems - 1 ? prev + 1 : 0
        )
        return
      }
      if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev => 
          prev > 0 ? prev - 1 : visibleItems - 1
        )
        return
      }
      if ((e.key === "Tab" || e.key === "Enter") && selectedAutocompleteIndex >= 0) {
        e.preventDefault()
        handleAutocompleteSelect(autocompleteItems[selectedAutocompleteIndex])
        return
      }
      if (e.key === "Escape") {
        e.preventDefault()
        setShowAutocomplete(false)
        return
      }
    }
    
    if (e.key === "Tab" && !e.shiftKey && (ghostTextSuffix || ghostTextInfo.showFallbackCard) && !showAutocomplete) {
      e.preventDefault()
      handleAcceptEnhancement()
      return
    }
    
    if (e.key === "Escape" && promptEnhancement) {
      e.preventDefault()
      handleDismissEnhancement()
      return
    }
    
    if (e.key === "Enter" && !e.shiftKey && mode !== "jd") {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === "Escape") {
      onCancel()
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      setJdContent(text)
      setSelectedVacancy(null)
    } catch (error) {
    }
  }

  const searchJobVacancies = useCallback(async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setJdVacancyResults([])
      setShowVacancyResults(false)
      return
    }
    
    setIsSearchingVacancies(true)
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/search?query=${encodeURIComponent(searchTerm)}&page_size=5`)
      if (response.ok) {
        const data = await response.json()
        setJdVacancyResults(data.items || [])
        setShowVacancyResults(true)
      }
    } catch (error) {
      setJdVacancyResults([])
    } finally {
      setIsSearchingVacancies(false)
    }
  }, [])

  useEffect(() => {
    if (jdVacancySearchTimeoutRef.current) {
      clearTimeout(jdVacancySearchTimeoutRef.current)
    }
    
    if (jdVacancySearch.length >= 2) {
      jdVacancySearchTimeoutRef.current = setTimeout(() => {
        searchJobVacancies(jdVacancySearch)
      }, 300)
    } else {
      setJdVacancyResults([])
      setShowVacancyResults(false)
    }
    
    return () => {
      if (jdVacancySearchTimeoutRef.current) {
        clearTimeout(jdVacancySearchTimeoutRef.current)
      }
    }
  }, [jdVacancySearch, searchJobVacancies])

  const handleSelectVacancy = async (vacancy: typeof jdVacancyResults[0]) => {
    setSelectedVacancy({
      id: vacancy.id,
      title: vacancy.title,
      job_id: vacancy.job_id
    })
    setShowVacancyResults(false)
    setJdVacancySearch("")
    
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/${vacancy.id}`)
      if (response.ok) {
        const fullVacancy = await response.json()
        if (fullVacancy.description) {
          setJdContent(fullVacancy.description)
        } else {
          const parts: string[] = []
          if (fullVacancy.title) parts.push(`Cargo: ${fullVacancy.title}`)
          if (fullVacancy.department) parts.push(`Departamento: ${fullVacancy.department}`)
          if (fullVacancy.location) parts.push(`Localização: ${fullVacancy.location}`)
          if (fullVacancy.seniority_level) parts.push(`Senioridade: ${fullVacancy.seniority_level}`)
          if (fullVacancy.requirements?.length) parts.push(`Requisitos: ${fullVacancy.requirements.join(', ')}`)
          setJdContent(parts.join('\n\n'))
        }
      }
    } catch (error) {
      if (vacancy.description_preview) {
        setJdContent(vacancy.description_preview.replace('...', ''))
      }
    }
  }

  const clearSelectedVacancy = () => {
    setSelectedVacancy(null)
    setJdContent("")
    setJdVacancySearch("")
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ""
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
      })
    } catch {
      return dateStr
    }
  }

  const modes: { key: SearchMode; label: string; icon: React.ElementType }[] = [
    { key: "natural", label: "Linguagem Natural", icon: Brain },
    { key: "similar", label: "Similar", icon: Users },
    { key: "jd", label: "Descrição da Vaga", icon: FileText },
    { key: "boolean", label: "Boolean", icon: Binary },
    { key: "archetypes", label: "Arquétipos", icon: Target }
  ]

  const canSubmit = () => {
    if (isLoading) return false
    switch (mode) {
      case "natural":
        return value.trim().length > 0
      case "boolean":
        if (value.trim().length > 0 && booleanFinalPrompt.trim().length === 0) {
          return false
        }
        return value.trim().length > 0 && !booleanError
      case "jd":
        return jdContent.trim().length > 0
      case "similar":
        const validUrls = similarUrls.filter(url => url.trim().length > 0)
        return validUrls.length > 0 || similarCvFiles.length > 0
      case "archetypes":
        return selectedArchetype !== null
      default:
        return false
    }
  }

  const scopeControlsProps = {
    searchSource,
    onSearchSourceChange,
    handleSourceChange,
    showGlobalSearchOptions,
    onRequireEmailsChange,
    onRequirePhoneNumbersChange,
    requireEmails,
    requirePhoneNumbers,
    canSubmit,
    isLoading: isLoading || false,
  }

  const getPlaceholder = () => {
    switch (mode) {
      case "natural":
        return placeholder
      case "similar":
        return "Cole a URL do LinkedIn ou ID do candidato..."
      case "jd":
        return "Cole a descrição da vaga aqui..."
      case "boolean":
        return "(software OR engineer) AND (python OR java) AND NOT junior"
      case "archetypes":
        return "Buscar vagas concluídas..."
      default:
        return placeholder
    }
  }

  const filteredArchetypes = archetypeVacancies.filter(v => {
    const searchLower = archetypeSearch.toLowerCase()
    const title = v.title || ''
    const hiredName = v.hired_candidate?.name || ''
    const department = v.department || ''
    return title.toLowerCase().includes(searchLower) ||
      hiredName.toLowerCase().includes(searchLower) ||
      department.toLowerCase().includes(searchLower)
  })


  return {
    modes, value, MAX_CV_FILES, MAX_SIMILAR_URLS, SearchScopeControls, scopeControlsProps,
    activeFiltersCount, addSimilarUrl, aiSuggestedSkills, aiSuggestedTags, analyzeProfiles,
    archetypeCreateMode, archetypeDescription, archetypeSearch, archetypeSearchPrompt,
    archetypeTab, archetypeVacancies, autocompleteEnabled, autocompleteItems, booleanError,
    buildArchetypePrompt, canSubmit, className, clearSelectedVacancy, closeEditArchetype,
    combinedSuggestions, confirmSourceChange, containerRef, createArchetypeFromDescription,
    cvFileInputRef, deleteArchetype, editArchetypeDescription, editArchetypeEmoji,
    editArchetypeEmploymentType, editArchetypeExperienceMin, editArchetypeIndustry,
    editArchetypeLanguages, editArchetypeLocation, editArchetypeName, editArchetypeQuery,
    editArchetypeSeniority, editArchetypeSkills, editArchetypeTags, editArchetypeWorkModel,
    editingArchetype, entities, expandedArchetypeId, fileInputRef, filledCount,
    filteredArchetypes, formatDate, getPlaceholder, ghostOverlayRef, ghostTextInfo,
    ghostTextSuffix, handleAcceptEnhancement, handleAutocompleteSelect, handleCvUpload,
    handleDismissEnhancement, handleFileUpload, handleKeyDown, handleSelectVacancy,
    handleSourceChange, handleSubmit, hasMultipleSources, industrySearchQuery,
    isAnalyzingProfiles, isCreatingArchetype, isDeletingArchetype, isFindingSimilarSkills,
    isFindingSimilarTags, isIndustryDropdownOpen, isLoading, isLoadingArchetypes,
    isParsingEntities, isSavingArchetype, isSearchingJobs, isSearchingVacancies,
    jdContent, jdSearchPrompt, jdVacancyResults, jdVacancySearch, jobSearchQuery,
    jobSearchResults, mode, newLanguageInput, newSkillInput, newTagInput,
    onChange, onGoToResults, onOpenFilters, onRequireEmailsChange, onRequirePhoneNumbersChange,
    onSearchSourceChange, onSubmit, openArchetypeFromJob, openEditArchetype, panelWidth,
    pendingSourceChange, placeholder, removeCvFile, removeSimilarUrl, removeSuggestion,
    requireEmails, requirePhoneNumbers, saveArchetype, searchAnalysis, searchJobsForArchetype,
    searchSource, selectedAiSkills, selectedAiTags, selectedArchetype, selectedAutocompleteIndex,
    selectedVacancy, setAiSuggestedSkills, setAiSuggestedTags, setArchetypeCreateMode,
    setArchetypeDescription, setArchetypeSearch, setArchetypeSearchPrompt, setArchetypeTab,
    setAutocompleteEnabled, setAutocompleteItems, setEditArchetypeDescription,
    setEditArchetypeEmoji, setEditArchetypeEmploymentType, setEditArchetypeExperienceMin,
    setEditArchetypeIndustry, setEditArchetypeLanguages, setEditArchetypeLocation,
    setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeSeniority,
    setEditArchetypeSkills, setEditArchetypeTags, setEditArchetypeWorkModel,
    setExpandedArchetypeId, setIndustrySearchQuery, setIsFindingSimilarSkills,
    setIsFindingSimilarTags, setIsIndustryDropdownOpen, setJdContent, setJdSearchPrompt,
    setJdVacancySearch, setJobSearchQuery, setMode, setNewLanguageInput, setNewSkillInput,
    setNewTagInput, setPendingSourceChange, setSelectedAiSkills, setSelectedAiTags,
    setSelectedArchetype, setSelectedAutocompleteIndex, setSelectedVacancy,
    setShowAutocomplete, setShowSkillSuggestions, setShowSourceChangeModal,
    setShowTagSuggestions, setSimilarSearchPrompt, showAutocomplete, showCombinedSuggestions,
    showGlobalSearchOptions, showSkillSuggestions, showSourceChangeModal, showTagSuggestions,
    showVacancyResults, similarCvFiles, similarSearchPrompt, similarUrls, tags,
    textareaRef, updateSimilarUrl,
  }
}
