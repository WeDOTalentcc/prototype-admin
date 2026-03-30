"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useCreditEstimator, getCostLevel, getCostColor } from "@/hooks/useCreditEstimator"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { useToast } from "@/hooks/use-toast"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import {
  MapPin, Briefcase, Clock, Building2, Code
} from "lucide-react"

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
    border: "var(--gray-400)",
    bg: "var(--gray-bg-05)",
    headerText: "var(--gray-600)",
    headerBg: "var(--gray-bg-10)"
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
export type SearchSource = 'local' | 'global' | 'hybrid'

export interface UsePromptStateParams {
  forceExpanded?: boolean
  onCommand: (command: string, action: string) => void
}

export function usePromptState({ forceExpanded = false, onCommand }: UsePromptStateParams) {
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const { toast } = useToast()
  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled

  const [isExpanded, setIsExpanded] = useState(forceExpanded)
  const [showPremiumAutocomplete, setShowPremiumAutocomplete] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastCommand, setLastCommand] = useState<string>("")
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [showBooleanMode, setShowBooleanMode] = useState(false)
  const [naturalSearchValue, setNaturalSearchValue] = useState("")
  const [booleanSearchValue, setBooleanSearchValue] = useState("")

  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('natural')
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [selectedArquetipo, setSelectedArquetipo] = useState<string | null>(null)
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")

  const [searchSource, setSearchSource] = useState<SearchSource>('local')
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [pearchSearchType, setPearchSearchType] = useState<'fast' | 'pro'>('fast')
  const [candidateLimit, setCandidateLimit] = useState(15)

  const [requireEmails, setRequireEmails] = useState(false)
  const [requirePhoneNumbers, setRequirePhoneNumbers] = useState(false)

  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])

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

  const [promptEnhancement, setPromptEnhancement] = useState<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>(null)
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [promptEnhancementDismissed, setPromptEnhancementDismissed] = useState(false)
  const dismissedQueryRef = useRef<string>("")
  const enhanceTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const [filterLocation, setFilterLocation] = useState("")
  const [filterExperience, setFilterExperience] = useState("any")
  const [filterSeniority, setFilterSeniority] = useState("any")
  const [filterWorkModel, setFilterWorkModel] = useState("any")

  const [showAdvancedFiltersModal, setShowAdvancedFiltersModal] = useState(false)
  const [advancedFilters, setAdvancedFilters] = useState<SearchFilters>({
    ppiOptions: {},
    general: {},
    job: {},
    company: {},
    skills: {},
    education: {},
    languages: {}
  })

  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)

  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AutocompleteSuggestion[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(0)
  const autocompleteCache = useRef<Map<string, AutocompleteSuggestion[]>>(new Map())
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true)

  const [parsedEntities, setParsedEntities] = useState<BackendEntities>({})

  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const cvFileInputRef = useRef<HTMLInputElement>(null)
  const MAX_SIMILAR_URLS = 2
  const MAX_CV_FILES = 2

  const [similarProfiles, setSimilarProfiles] = useState<SimilarProfile[]>([])
  const [combinedProfileKeywords, setCombinedProfileKeywords] = useState<string[]>([])

  const [archetypes, setArchetypes] = useState<ArchetypeData[]>([])
  const [closedJobsForArchetype, setClosedJobsForArchetype] = useState<Record<string, unknown>[]>([])
  const [archetypeSearchFilter, setArchetypeSearchFilter] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [newArchetypeDescription, setNewArchetypeDescription] = useState("")
  const [selectedJobForArchetype, setSelectedJobForArchetype] = useState<string | null>(null)

  const [editingArchetype, setEditingArchetype] = useState<ArchetypeData | null>(null)
  const [editArchetypeName, setEditArchetypeName] = useState("")
  const [editArchetypeQuery, setEditArchetypeQuery] = useState("")
  const [editArchetypeDescription, setEditArchetypeDescription] = useState("")
  const [editArchetypeEmoji, setEditArchetypeEmoji] = useState("")
  const [editArchetypeTags, setEditArchetypeTags] = useState<string[]>([])
  const [newTagInput, setNewTagInput] = useState("")
  const [isSavingArchetype, setIsSavingArchetype] = useState(false)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState<string | null>(null)
  const [showDeleteArchetypeDialog, setShowDeleteArchetypeDialog] = useState(false)
  const [archetypeToDelete, setArchetypeToDelete] = useState<{ id: string; name: string } | null>(null)

  const [showSaveArchetypeModal, setShowSaveArchetypeModal] = useState(false)
  const [isCreatingFromSearch, setIsCreatingFromSearch] = useState(false)

  const [extractedCriteria, setExtractedCriteria] = useState<SearchCriterion[]>([])

  const creditEstimator = useCreditEstimator()

  useEffect(() => {
    if (searchSource !== 'local') {
      creditEstimator.fetchBalance().catch(() => { /* TODO: integrar com Sentry */ })
    }
  }, [searchSource])

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
  }, [])

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
          const newCriteria: SearchCriterion[] = []
          let idx = 0
          if (entities.job_title) {
            newCriteria.push({ id: `entity-job_title-${idx++}`, type: 'job_title', label: ENTITY_LABELS.job_title, value: entities.job_title, active: true })
          }
          if (entities.location) {
            newCriteria.push({ id: `entity-location-${idx++}`, type: 'location', label: ENTITY_LABELS.location, value: entities.location, active: true })
          }
          if (entities.years_experience) {
            newCriteria.push({ id: `entity-years_experience-${idx++}`, type: 'years_experience', label: ENTITY_LABELS.years_experience, value: entities.years_experience, active: true })
          }
          if (entities.industry) {
            newCriteria.push({ id: `entity-industry-${idx++}`, type: 'industry', label: ENTITY_LABELS.industry, value: entities.industry, active: true })
          }
          if (entities.skills && entities.skills.length > 0) {
            entities.skills.forEach((skill, skillIdx) => {
              newCriteria.push({ id: `entity-skills-${idx++}-${skillIdx}`, type: 'skills', label: 'Habilidade', value: skill, active: true })
            })
          }
          if (entities.seniority) {
            newCriteria.push({ id: `entity-seniority-${idx++}`, type: 'seniority', label: ENTITY_LABELS.seniority, value: entities.seniority, active: true })
          }
          if (entities.company) {
            newCriteria.push({ id: `entity-company-${idx++}`, type: 'company', label: ENTITY_LABELS.company, value: entities.company, active: true })
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
  }, [])

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
  }, [promptEnhancementDismissed])

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      setNaturalSearchValue(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement])

  const handleDismissEnhancement = useCallback(() => {
    dismissedQueryRef.current = naturalSearchValue
    setPromptEnhancementDismissed(true)
    setPromptEnhancement(null)
  }, [naturalSearchValue])

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
        toast({ title: "Arquivo analisado", description: `Extraídos ${uniqueKeywords.length} critérios de ${file.name}` })
      } else {
        toast({ title: "Arquivo processado", description: `${file.name} foi analisado mas não foram encontrados critérios de busca`, variant: "default" })
      }
    } else {
      toast({ title: "Erro na análise", description: analysis.error || "Não foi possível analisar o arquivo", variant: "destructive" })
    }
  }, [toast, parseEntitiesFromQuery])

  const handleAudioTranscription = useCallback((text: string) => {
    if (text && text.trim()) {
      setNaturalSearchValue(prev => {
        const newValue = prev ? `${prev} ${text.trim()}` : text.trim()
        parseEntitiesFromQuery(newValue)
        return newValue
      })
      setShowPremiumAutocomplete(true)
      toast({ title: "Transcrição concluída", description: "Texto adicionado à busca" })
    }
  }, [toast, parseEntitiesFromQuery])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    setNaturalSearchValue(suggestion)
    setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery])

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
  }, [naturalSearchValue, activeSearchTab, promptEnhancementDismissed, fetchPromptEnhancement])

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
  }, [])

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
  }, [similarProfiles])

  const createArchetypeFromJob = useCallback(async (jobId: string) => {
    setIsCreatingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/from-job/${jobId}/`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setArchetypes(prev => [...prev, data])
        setSelectedJobForArchetype(null)
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [])

  const hasParsedEntities = useCallback(() => {
    return !!(
      parsedEntities.job_title || parsedEntities.location || parsedEntities.seniority ||
      parsedEntities.industry || parsedEntities.company || parsedEntities.years_experience ||
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
    if (parsedEntities.skills && parsedEntities.skills.length > 0) spec.skills = parsedEntities.skills
    const filtersRec = advancedFilters as Record<string, Record<string, unknown>>
    if (filtersRec.locations?.locations && Array.isArray(filtersRec.locations.locations) && (filtersRec.locations.locations as unknown[]).length > 0) spec.locations = filtersRec.locations.locations as string[]
    if (advancedFilters.job?.titles && advancedFilters.job.titles.length > 0) spec.job_titles = advancedFilters.job.titles
    if (advancedFilters.job?.levels && advancedFilters.job.levels.length > 0) spec.seniority_levels = advancedFilters.job.levels
    if (advancedFilters.skills?.skillItems && advancedFilters.skills.skillItems.length > 0) spec.required_skills = advancedFilters.skills.skillItems.map(s => s.name)
    if (advancedFilters.languages?.languages && advancedFilters.languages.languages.length > 0) spec.languages = advancedFilters.languages.languages
    if (advancedFilters.general?.minExperience) spec.years_experience_min = advancedFilters.general.minExperience
    if (advancedFilters.general?.maxExperience) spec.years_experience_max = advancedFilters.general.maxExperience
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
      toast({ title: "Busca incompleta", description: "Faça uma busca com critérios definidos antes de salvar como arquétipo.", variant: "destructive" })
      return
    }
    setIsCreatingFromSearch(true)
    try {
      const searchSpec = buildSearchSpec()
      const generatedName = generateArchetypeName()
      const payload = { search_spec: searchSpec, name: generatedName, description: naturalSearchValue || "Arquétipo criado a partir de busca", emoji: "🎯" }
      const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      })
      if (res.ok) {
        const data = await res.json()
        const newArchetype = data.archetype || data
        setArchetypes(prev => [...prev, newArchetype])
        toast({ title: "Arquétipo salvo!", description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado a partir da sua busca.` })
      } else {
        const error = await res.json()
        toast({ title: "Erro ao salvar arquétipo", description: error.detail || error.error || "Não foi possível salvar o arquétipo.", variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "Erro ao salvar arquétipo", description: "Ocorreu um erro de conexão. Tente novamente.", variant: "destructive" })
    } finally {
      setIsCreatingFromSearch(false)
    }
  }, [hasParsedEntities, buildSearchSpec, generateArchetypeName, naturalSearchValue, toast])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    if (!description.trim()) return
    setIsCreatingArchetype(true)
    try {
      const generatedName = generateArchetypeName()
      if (hasParsedEntities()) {
        const searchSpec = buildSearchSpec()
        const payload = { search_spec: searchSpec, name: generatedName, description, emoji: "🎯" }
        const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        })
        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast({ title: "Arquétipo criado", description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          toast({ title: "Erro ao criar arquétipo", description: error.detail || error.error || "Não foi possível criar o arquétipo.", variant: "destructive" })
        }
      } else {
        const payload: Record<string, unknown> = { description, name: generatedName, emoji: "🎯" }
        const res = await fetch('/api/backend-proxy/search/archetypes/from-description/', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        })
        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast({ title: "Arquétipo criado", description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          toast({ title: "Erro ao criar arquétipo", description: error.detail || error.error || "Não foi possível criar o arquétipo.", variant: "destructive" })
        }
      }
    } catch (error) {
      toast({ title: "Erro ao criar arquétipo", description: "Ocorreu um erro de conexão. Tente novamente.", variant: "destructive" })
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec, toast])

  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    const query = (arch as ArchetypeData & { query?: string }).query || arch.criteria?.query || ""
    setEditArchetypeQuery(query as string)
    setEditArchetypeDescription(arch.description || "")
    const emoji = (arch as ArchetypeData & { emoji?: string }).emoji || arch.criteria?.emoji || "🎯"
    setEditArchetypeEmoji(String(emoji))
    const tags: string[] = []
    const criteria = arch.criteria || {}
    if (criteria.job_title) tags.push(String(criteria.job_title))
    if (criteria.location) tags.push(String(criteria.location))
    if (criteria.seniority) tags.push(String(criteria.seniority))
    if (criteria.industry) tags.push(String(criteria.industry))
    if (criteria.skills && Array.isArray(criteria.skills)) tags.push(...criteria.skills)
    setEditArchetypeTags(tags)
    setNewTagInput("")
  }, [])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setNewTagInput("")
  }, [])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return
    setIsSavingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${editingArchetype.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editArchetypeName.trim(), query: editArchetypeQuery.trim(),
          description: editArchetypeDescription.trim() || null, emoji: editArchetypeEmoji || "🎯",
          tags: editArchetypeTags.length > 0 ? editArchetypeTags : null
        })
      })
      if (res.ok) {
        const updated = await res.json()
        setArchetypes(prev => prev.map(a => a.id === editingArchetype.id ? { ...a, ...updated } : a))
        closeEditArchetype()
        toast({ title: "Arquétipo atualizado", description: `"${editArchetypeName}" foi salvo com sucesso.` })
      } else {
        const error = await res.json()
        toast({ title: "Erro ao atualizar arquétipo", description: error.detail || error.error || "Não foi possível salvar as alterações.", variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "Erro ao atualizar arquétipo", description: "Ocorreu um erro de conexão. Tente novamente.", variant: "destructive" })
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, closeEditArchetype, toast])

  const openDeleteArchetypeDialog = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setArchetypeToDelete({ id: arch.id, name: arch.name })
    setShowDeleteArchetypeDialog(true)
  }, [])

  const confirmDeleteArchetype = useCallback(async () => {
    if (!archetypeToDelete) return
    const archId = archetypeToDelete.id
    const archName = archetypeToDelete.name
    setIsDeletingArchetype(archId)
    setShowDeleteArchetypeDialog(false)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${archId}/`, { method: 'DELETE' })
      if (res.ok) {
        setArchetypes(prev => prev.filter(a => a.id !== archId))
        toast({ title: "Arquétipo excluído", description: `"${archName}" foi removido com sucesso.` })
      } else {
        const error = await res.json()
        toast({ title: "Erro ao excluir arquétipo", description: error.detail || error.error || "Não foi possível excluir o arquétipo.", variant: "destructive" })
      }
    } catch (error) {
      toast({ title: "Erro ao excluir arquétipo", description: "Ocorreu um erro de conexão. Tente novamente.", variant: "destructive" })
    } finally {
      setIsDeletingArchetype(null)
      setArchetypeToDelete(null)
    }
  }, [archetypeToDelete, toast])

  const addSimilarProfile = useCallback((url: string, type: 'linkedin' | 'cv' = 'linkedin', filename?: string) => {
    if (similarProfiles.length >= 3) return
    if (similarProfiles.some(p => p.url === url)) return
    setSimilarProfiles(prev => [...prev, { url, type, filename }])
  }, [similarProfiles])

  const removeSimilarProfile = useCallback((url: string) => {
    setSimilarProfiles(prev => prev.filter(p => p.url !== url))
  }, [])

  const addSimilarUrl = useCallback(() => {
    if (similarUrls.length < MAX_SIMILAR_URLS) {
      setSimilarUrls(prev => [...prev, ""])
    }
  }, [similarUrls.length])

  const removeSimilarUrl = useCallback((index: number) => {
    setSimilarUrls(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [])

  const updateSimilarUrl = useCallback((index: number, value: string) => {
    setSimilarUrls(prev => {
      const newUrls = [...prev]
      newUrls[index] = value
      return newUrls
    })
  }, [])

  const handleCvUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    const newFiles = Array.from(files).slice(0, MAX_CV_FILES - similarCvFiles.length)
    setSimilarCvFiles(prev => [...prev, ...newFiles].slice(0, MAX_CV_FILES))
  }, [similarCvFiles.length])

  const removeCvFile = useCallback((index: number) => {
    setSimilarCvFiles(prev => prev.filter((_, i) => i !== index))
    setCombinedSuggestions([])
    setShowCombinedSuggestions(false)
  }, [])

  const removeSuggestion = useCallback((keyword: string) => {
    setCombinedSuggestions(prev => prev.filter(k => k !== keyword))
  }, [])

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
        method: "POST", body: formData
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
  }, [similarUrls, similarCvFiles])

  const handleAutocompleteKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showAutocomplete || autocompleteSuggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev => prev < autocompleteSuggestions.length - 1 ? prev + 1 : 0)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev => prev > 0 ? prev - 1 : autocompleteSuggestions.length - 1)
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
  }, [showAutocomplete, autocompleteSuggestions, selectedAutocompleteIndex])

  const filteredArchetypes = useMemo(() => {
    if (!archetypeSearchFilter.trim()) return archetypes
    const filter = archetypeSearchFilter.toLowerCase()
    return archetypes.filter(a =>
      (a.name || '').toLowerCase().includes(filter) ||
      (a.department || '').toLowerCase().includes(filter) ||
      (a.hired_candidate?.name || '').toLowerCase().includes(filter)
    )
  }, [archetypes, archetypeSearchFilter])

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

  const searchTags: SearchTag[] = useMemo(() => [
    { key: "location" as keyof BackendEntities, label: "Localização", icon: MapPin, filled: !!parsedEntities.location, value: parsedEntities.location },
    { key: "job_title" as keyof BackendEntities, label: "Cargo", icon: Briefcase, filled: !!parsedEntities.job_title, value: parsedEntities.job_title },
    { key: "years_experience" as keyof BackendEntities, label: "Experiência", icon: Clock, filled: !!parsedEntities.years_experience, value: parsedEntities.years_experience },
    { key: "industry" as keyof BackendEntities, label: "Setor", icon: Building2, filled: !!parsedEntities.industry, value: parsedEntities.industry },
    { key: "skills" as keyof BackendEntities, label: "Habilidades", icon: Code, filled: !!(parsedEntities.skills && parsedEntities.skills.length > 0), value: parsedEntities.skills?.join(", ") }
  ], [parsedEntities])

  const filledTagsCount = useMemo(() => searchTags.filter(t => t.filled).length, [searchTags])

  const getTagColors = useCallback((key: string, filled: boolean) => {
    if (!filled) return { bg: "var(--gray-50)", text: "var(--gray-400)", iconBg: "var(--gray-400)" }
    switch (key) {
      case 'job_title':
        return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
      case 'location':
        return { bg: "var(--gray-50)", text: "var(--wedo-purple)", iconBg: "var(--wedo-purple)" }
      case 'skills':
        return { bg: "var(--gray-50)", text: "var(--status-success)", iconBg: "var(--wedo-green-light)" }
      case 'years_experience':
        return { bg: "var(--gray-50)", text: "var(--status-warning)", iconBg: "var(--wedo-orange)" }
      case 'industry':
        return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
      default:
        return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
    }
  }, [])

  const removeCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.filter(c => c.id !== id))
  }

  const toggleCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.map(c =>
      c.id === id ? { ...c, active: !c.active } : c
    ))
  }

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
      setExtractedCriteria(prev => {
        const manuallyModified = prev.filter(c => !c.active)
        const newlyExtracted: SearchCriterion[] = []
        const locations = ['são paulo', 'rio de janeiro', 'belo horizonte', 'curitiba', 'porto alegre', 'brasília', 'sp', 'rj']
        for (const loc of locations) {
          if (queryLower.includes(loc)) {
            const id = `loc-${loc.replace(/\s/g, '-')}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({ id, type: 'location', label: 'Localização', value: loc.charAt(0).toUpperCase() + loc.slice(1), active: true })
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
            newlyExtracted.push({ id, type: 'experience', label: 'Experiência', value: `${years}+ anos`, active: true })
          }
        }
        const skills = ['python', 'react', 'node', 'java', 'typescript', 'javascript', 'aws', 'docker', 'kubernetes', 'sql', 'figma', 'ux', 'ui', 'angular', 'vue', 'spring', 'django', 'flask', 'fastapi']
        for (const skill of skills) {
          if (queryLower.includes(skill)) {
            const id = `skill-${skill}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({ id, type: 'skills', label: 'Skills', value: skill.charAt(0).toUpperCase() + skill.slice(1), active: true })
            }
          }
        }
        const languages = ['inglês', 'espanhol', 'francês', 'alemão', 'english', 'spanish', 'fluente', 'avançado']
        for (const lang of languages) {
          if (queryLower.includes(lang)) {
            const id = `lang-${lang}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({ id, type: 'language', label: 'Idioma', value: lang.charAt(0).toUpperCase() + lang.slice(1), active: true })
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
        for (const [key, value] of Object.entries(seniorities)) {
          if (queryLower.includes(key)) {
            const id = `seniority-${key.replace(/\s/g, '-')}`
            const existing = prev.find(c => c.id === id)
            if (!existing) {
              newlyExtracted.push({ id, type: 'job_title', label: 'Senioridade', value, active: true })
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

  const buildSearchSpecFromEntities = useMemo(() => {
    if (!parsedEntities || Object.keys(parsedEntities).length === 0) return null
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
    toast({ title: "Arquétipo salvo", description: `"${newArchetype.name}" foi adicionado aos seus arquétipos.` })
  }

  return {
    toast,
    showGlobalSearchOptions,
    isExpanded, setIsExpanded,
    showPremiumAutocomplete, setShowPremiumAutocomplete,
    inputValue, setInputValue,
    isListening, setIsListening,
    isProcessing, setIsProcessing,
    lastCommand, setLastCommand,
    commandHistory, setCommandHistory,
    showHistory, setShowHistory,
    showBooleanMode, setShowBooleanMode,
    naturalSearchValue, setNaturalSearchValue,
    booleanSearchValue, setBooleanSearchValue,
    activeSearchTab, setActiveSearchTab,
    jobDescriptionText, setJobDescriptionText,
    selectedArquetipo, setSelectedArquetipo,
    similarProfileUrl, setSimilarProfileUrl,
    searchSource, setSearchSource,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    pearchSearchType, setPearchSearchType,
    candidateLimit, setCandidateLimit,
    requireEmails, setRequireEmails,
    requirePhoneNumbers, setRequirePhoneNumbers,
    handleSourceChange,
    confirmSourceChange,
    promptEnhancement, setPromptEnhancement,
    isEnhancingPrompt,
    promptEnhancementDismissed,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    filterLocation, setFilterLocation,
    filterExperience, setFilterExperience,
    filterSeniority, setFilterSeniority,
    filterWorkModel, setFilterWorkModel,
    showAdvancedFiltersModal, setShowAdvancedFiltersModal,
    advancedFilters, setAdvancedFilters,
    isParsingEntities,
    searchAnalysis,
    autocompleteSuggestions, setAutocompleteSuggestions,
    showAutocomplete, setShowAutocomplete,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    autocompleteEnabled, setAutocompleteEnabled,
    parsedEntities,
    similarUrls, setSimilarUrls,
    similarCvFiles, setSimilarCvFiles,
    isAnalyzingProfiles,
    combinedSuggestions,
    showCombinedSuggestions,
    cvFileInputRef,
    MAX_SIMILAR_URLS,
    MAX_CV_FILES,
    similarProfiles,
    combinedProfileKeywords,
    archetypes, setArchetypes,
    closedJobsForArchetype,
    archetypeSearchFilter, setArchetypeSearchFilter,
    isCreatingArchetype,
    newArchetypeDescription, setNewArchetypeDescription,
    selectedJobForArchetype, setSelectedJobForArchetype,
    editingArchetype,
    editArchetypeName, setEditArchetypeName,
    editArchetypeQuery, setEditArchetypeQuery,
    editArchetypeDescription, setEditArchetypeDescription,
    editArchetypeEmoji, setEditArchetypeEmoji,
    editArchetypeTags, setEditArchetypeTags,
    newTagInput, setNewTagInput,
    isSavingArchetype,
    isDeletingArchetype,
    showDeleteArchetypeDialog, setShowDeleteArchetypeDialog,
    archetypeToDelete,
    showSaveArchetypeModal, setShowSaveArchetypeModal,
    isCreatingFromSearch,
    extractedCriteria, setExtractedCriteria,
    creditEstimate,
    searchTags,
    filledTagsCount,
    getTagColors,
    filteredArchetypes,
    parseEntitiesFromQuery,
    fetchAutocomplete,
    fetchPromptEnhancement,
    handleFileAnalyzed,
    handleAudioTranscription,
    handlePremiumAutocompleteSelect,
    handleAutocompleteKeyDown,
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
    removeCriterion,
    toggleCriterion,
    extractCriteriaFromQuery,
    extractionTimeoutRef,
    buildSearchQueryFromCriteria,
    executeSearchWithCriteria,
    buildSearchSpecFromEntities,
    canSaveAsArchetype,
    handleArchetypeSaved,
  }
}
