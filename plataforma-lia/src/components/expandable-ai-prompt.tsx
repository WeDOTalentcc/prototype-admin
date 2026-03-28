"use client"

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useTemplateSuggestions } from "@/hooks/use-template-suggestions"
import { TemplateSuggestionToast, useTemplateSuggestionQueue } from "@/components/template-suggestion-toast"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LIAIcon } from "@/components/ui/lia-icon"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from "@/components/ui/quick-action-chips"
import { Card, CardContent } from "@/components/ui/card"
import { useCreditEstimator, formatCreditCost, getCostLevel, getCostColor, CREDIT_COSTS } from "@/hooks/useCreditEstimator"
import { AdvancedFiltersModal, type SearchFilters } from "@/components/search/advanced-filters-modal"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
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
import {
  Brain, Mic, Send, ChevronDown, ChevronUp, X,
  Users, Mail, MessageSquare, Calendar, Target, Phone,
  Search, Filter, Star, Plus, Zap,
  FileText, Code, Check, Lightbulb, Globe, Home, Coins, AlertCircle,
  Briefcase, Linkedin, TrendingUp, AlertTriangle, Info, Wand2, 
  CheckCircle2, Upload, MapPin, Clock, Building2,
  Pencil, Trash2, Loader2, Table2
} from "lucide-react"
import { PromptSuggestionsPopover } from "@/components/ui/prompt-suggestions-popover"
import { LiaQueriesGuide } from "@/components/ui/lia-queries-guide"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { FileUploadButton, type FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { PremiumAutocomplete } from "@/components/ui/premium-autocomplete"
import { useToast } from "@/hooks/use-toast"
import { SaveArchetypeModal } from "@/components/search/save-archetype-modal"
import type { SearchSpec } from "@/lib/api/candidate-search"

interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

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

// Cores padronizadas por contexto - Paleta Pastel
const CONTEXT_COLORS: Record<string, {
  border: string
  bg: string
  headerText: string
  headerBg: string
}> = {
  candidates: {
    border: 'var(--wedo-green-light)',
    bg: 'var(--wedo-green-bg-10)',
    headerText: 'var(--status-success)',
    headerBg: 'var(--wedo-green-bg-15)'
  },
  jobs: {
    border: 'var(--gray-400)',
    bg: 'var(--gray-bg-05)',
    headerText: 'var(--gray-600)',
    headerBg: 'var(--gray-bg-10)'
  }
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
  criteria?: any
}

interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

interface ContextPillData {
  icon: React.ReactNode
  primaryText: string
  secondaryText: string
  onDismiss?: () => void
}

interface JobContext {
  id?: string
  title?: string
  status?: string
}

interface ExpandableAIPromptProps {
  selectedCandidates: any[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: any
  onClose?: () => void
  // AI-First props
  contextPill?: ContextPillData
  quickActions?: QuickAction[]
  // Job context for suggestions
  jobContext?: JobContext
  // Page context for showing appropriate queries guide
  pageContext?: 'candidates' | 'jobs'
}

export function ExpandableAIPrompt({
  selectedCandidates,
  onCommand,
  filteredCount,
  totalCount,
  forceExpanded = false,
  candidateContext = null,
  onClose,
  contextPill,
  quickActions = [],
  jobContext,
  pageContext = 'candidates'
}: ExpandableAIPromptProps) {
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const { toast } = useToast()
  
  // Only show global/hybrid options after settings are loaded AND global search is enabled
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
  
  // Sistema de 6 abas de busca avançada
  type SearchTab = 'natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
  type SearchSource = 'local' | 'global' | 'hybrid'
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('natural')
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [selectedArquetipo, setSelectedArquetipo] = useState<string | null>(null)
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")
  
  // Controle de fonte de busca e créditos
  const [searchSource, setSearchSource] = useState<SearchSource>('local')
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [pearchSearchType, setPearchSearchType] = useState<'fast' | 'pro'>('fast')
  const [candidateLimit, setCandidateLimit] = useState(15)
  
  // Filtros de contato (Email/Telefone)
  const [requireEmails, setRequireEmails] = useState(false)
  const [requirePhoneNumbers, setRequirePhoneNumbers] = useState(false)
  
  // Reset search source to local if global search is disabled
  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])
  
  // Handler para mudança de fonte de busca com confirmação de créditos
  const handleSourceChange = (newSource: 'local' | 'hybrid' | 'global') => {
    if (newSource === 'local') {
      setSearchSource('local')
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  // Confirmar mudança de fonte após aceitar modal
  const confirmSourceChange = () => {
    if (pendingSourceChange) {
      setSearchSource(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }
  
  // Prompt Enhancement (sugestões de IA para melhorar a busca)
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
  
  // Filtros avançados (aba Filtros)
  const [filterLocation, setFilterLocation] = useState("")
  const [filterExperience, setFilterExperience] = useState("any")
  const [filterSeniority, setFilterSeniority] = useState("any")
  const [filterWorkModel, setFilterWorkModel] = useState("any")
  
  // Modal de filtros avançados
  const [showAdvancedFiltersModal, setShowAdvancedFiltersModal] = useState(false)
  const [advancedFilters, setAdvancedFilters] = useState<SearchFilters>({
    ppiOptions: {},
    general: {},
    locations: {},
    job: {},
    company: {},
    skills: {},
    education: {},
    languages: {}
  })
  
  // API-based entity parsing and analysis
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)
  
  // Autocomplete via API
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AutocompleteSuggestion[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(0)
  const autocompleteCache = useRef<Map<string, AutocompleteSuggestion[]>>(new Map())
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true)
  
  // Parsed entities from API (for always-visible tags)
  const [parsedEntities, setParsedEntities] = useState<BackendEntities>({})
  
  // Similar mode with multiple profiles (new pattern like SmartSearchInput)
  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const cvFileInputRef = useRef<HTMLInputElement>(null)
  const MAX_SIMILAR_URLS = 2
  const MAX_CV_FILES = 2
  
  // Legacy similar profiles state (for backwards compatibility)
  const [similarProfiles, setSimilarProfiles] = useState<SimilarProfile[]>([])
  const [combinedProfileKeywords, setCombinedProfileKeywords] = useState<string[]>([])
  
  // Archetypes from API
  const [archetypes, setArchetypes] = useState<ArchetypeData[]>([])
  const [closedJobsForArchetype, setClosedJobsForArchetype] = useState<any[]>([])
  const [archetypeSearchFilter, setArchetypeSearchFilter] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [newArchetypeDescription, setNewArchetypeDescription] = useState("")
  const [selectedJobForArchetype, setSelectedJobForArchetype] = useState<string | null>(null)
  
  // Archetype edit/delete states
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
  
  // Save archetype from search modal
  const [showSaveArchetypeModal, setShowSaveArchetypeModal] = useState(false)
  
  // Loading state for creating archetype from active search
  const [isCreatingFromSearch, setIsCreatingFromSearch] = useState(false)
  
  // Hook de estimativa de créditos 
  const creditEstimator = useCreditEstimator()
  
  // Carregar saldo ao montar e quando mudar a fonte
  useEffect(() => {
    if (searchSource !== 'local') {
      creditEstimator.fetchBalance().catch(console.error)
    }
  }, [searchSource])
  
  // Carregar arquétipos e vagas fechadas ao montar
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
  
  // API-based entity parsing with debounce
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
        
        // Store raw entities for always-visible tags
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
  }, [])
  
  // Prompt Enhancement via API
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
  }, [toast, parseEntitiesFromQuery])

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
  }, [toast, parseEntitiesFromQuery])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    setNaturalSearchValue(suggestion)
    setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery])
  
  // Prompt Enhancement com debounce - dispara quando o usuário digita na aba natural
  useEffect(() => {
    if (activeSearchTab !== 'natural' || !naturalSearchValue || naturalSearchValue.length < 10) {
      setPromptEnhancement(null)
      return
    }
    
    // Reset dismissed state se a query mudou significativamente
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
  
  // Autocomplete via API with cache
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
        const suggestions: AutocompleteSuggestion[] = items.map((item: any) => ({
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
  
  // Combined profile analysis
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
  
  // Create archetype from job
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
  }, [])
  
  // Helper function to check if there are meaningful parsed entities
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

  // Build search_spec from parsedEntities and advancedFilters
  const buildSearchSpec = useCallback(() => {
    const spec: Record<string, unknown> = {}
    
    // Primary data from parsed entities
    if (parsedEntities.job_title) spec.job_title = parsedEntities.job_title
    if (parsedEntities.location) spec.location = parsedEntities.location
    if (parsedEntities.seniority) spec.seniority = parsedEntities.seniority
    if (parsedEntities.industry) spec.industry = parsedEntities.industry
    if (parsedEntities.company) spec.company = parsedEntities.company
    if (parsedEntities.years_experience) spec.years_experience = parsedEntities.years_experience
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      spec.skills = parsedEntities.skills
    }
    
    // Add relevant advanced filters if present
    if (advancedFilters.locations?.locations && advancedFilters.locations.locations.length > 0) {
      spec.locations = advancedFilters.locations.locations
    }
    if (advancedFilters.job?.titles && advancedFilters.job.titles.length > 0) {
      spec.job_titles = advancedFilters.job.titles
    }
    if (advancedFilters.job?.levels && advancedFilters.job.levels.length > 0) {
      spec.seniority_levels = advancedFilters.job.levels
    }
    if (advancedFilters.skills?.skillItems && advancedFilters.skills.skillItems.length > 0) {
      spec.required_skills = advancedFilters.skills.skillItems.map(s => s.name)
    }
    if (advancedFilters.languages?.languages && advancedFilters.languages.languages.length > 0) {
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

  // Generate archetype name from parsed entities
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

  // Create archetype directly from active search using from-search endpoint
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
  }, [hasParsedEntities, buildSearchSpec, generateArchetypeName, naturalSearchValue, toast])

  // Create archetype from description with structured data
  const createArchetypeFromDescription = useCallback(async (description: string) => {
    if (!description.trim()) return
    
    setIsCreatingArchetype(true)
    try {
      const generatedName = generateArchetypeName()
      
      // If we have parsed entities, use the from-search endpoint for better structured data
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
        // Fallback to from-description endpoint when no entities available
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
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec, toast])
  
  // Open archetype edit modal
  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    // Backend returns query at top level in ArchetypeDTO, not in criteria
    const query = (arch as any).query || arch.criteria?.query || ""
    setEditArchetypeQuery(query)
    setEditArchetypeDescription(arch.description || "")
    const emoji = (arch as any).emoji || arch.criteria?.emoji || "🎯"
    setEditArchetypeEmoji(emoji)
    // Extract tags from criteria or query
    const tags: string[] = []
    const criteria = arch.criteria || {}
    if (criteria.job_title) tags.push(criteria.job_title)
    if (criteria.location) tags.push(criteria.location)
    if (criteria.seniority) tags.push(criteria.seniority)
    if (criteria.industry) tags.push(criteria.industry)
    if (criteria.skills && Array.isArray(criteria.skills)) {
      tags.push(...criteria.skills)
    }
    setEditArchetypeTags(tags)
    setNewTagInput("")
  }, [])

  // Close archetype edit modal
  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setNewTagInput("")
  }, [])

  // Save archetype changes
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
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, closeEditArchetype, toast])

  // Open delete confirmation dialog
  const openDeleteArchetypeDialog = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setArchetypeToDelete({ id: arch.id, name: arch.name })
    setShowDeleteArchetypeDialog(true)
  }, [])

  // Confirm delete archetype
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
  }, [archetypeToDelete, toast])
  
  // Add similar profile (LinkedIn URL or CV)
  const addSimilarProfile = useCallback((url: string, type: 'linkedin' | 'cv' = 'linkedin', filename?: string) => {
    if (similarProfiles.length >= 3) return
    if (similarProfiles.some(p => p.url === url)) return
    
    setSimilarProfiles(prev => [...prev, { url, type, filename }])
  }, [similarProfiles])
  
  // Remove similar profile
  const removeSimilarProfile = useCallback((url: string) => {
    setSimilarProfiles(prev => prev.filter(p => p.url !== url))
  }, [])
  
  // Similar tab helper functions (new pattern like SmartSearchInput)
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
    // Allow analysis with at least 1 source (CV or URL)
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
        
        // Store additional profile data for use in search
        if (data.title) {
          setCombinedProfileKeywords(prev => {
            const combined = [...keywords]
            if (data.title && !combined.includes(data.title)) combined.push(data.title)
            if (data.location && !combined.includes(data.location)) combined.push(data.location)
            return combined
          })
        }
        
        // Auto-populate natural search with combined profile
        if (keywords.length > 0) {
          const searchQuery = keywords.slice(0, 6).join(', ')
          setNaturalSearchValue(searchQuery)
        }
      } else {
        const errorText = await response.text()
      }
    } catch (error) {
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles])
  
  // Handle autocomplete keyboard navigation
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
  }, [showAutocomplete, autocompleteSuggestions, selectedAutocompleteIndex])
  
  // Filter archetypes
  const filteredArchetypes = useMemo(() => {
    if (!archetypeSearchFilter.trim()) return archetypes
    const filter = archetypeSearchFilter.toLowerCase()
    return archetypes.filter(a => 
      (a.name || '').toLowerCase().includes(filter) ||
      (a.department || '').toLowerCase().includes(filter) ||
      (a.hired_candidate?.name || '').toLowerCase().includes(filter)
    )
  }, [archetypes, archetypeSearchFilter])
  
  // Estimativa de créditos em tempo real usando o hook
  const creditEstimate = useMemo(() => {
    if (searchSource === 'local') {
      return { total: 0, perCandidate: 0, isLocal: true, canAfford: true }
    }
    
    // Usar estimativa local como base (atualizada quando API responder)
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
    
    // Verificar se pode pagar com base no saldo disponível
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
  
  // Always-visible search tags (5 criteria like SmartSearchInput)
  interface SearchTag {
    key: keyof BackendEntities
    label: string
    icon: typeof MapPin
    filled: boolean
    value?: string
  }
  
  const searchTags: SearchTag[] = useMemo(() => [
    { key: "location", label: "Localização", icon: MapPin, filled: !!parsedEntities.location, value: parsedEntities.location },
    { key: "job_title", label: "Cargo", icon: Briefcase, filled: !!parsedEntities.job_title, value: parsedEntities.job_title },
    { key: "years_experience", label: "Experiência", icon: Clock, filled: !!parsedEntities.years_experience, value: parsedEntities.years_experience },
    { key: "industry", label: "Setor", icon: Building2, filled: !!parsedEntities.industry, value: parsedEntities.industry },
    { key: "skills", label: "Habilidades", icon: Code, filled: !!(parsedEntities.skills && parsedEntities.skills.length > 0), value: parsedEntities.skills?.join(", ") }
  ], [parsedEntities])
  
  const filledTagsCount = useMemo(() => searchTags.filter(t => t.filled).length, [searchTags])
  
  // Helper function for tag colors (ElevenLabs/WedoTalent pattern)
  const getTagColors = useCallback((key: string, filled: boolean) => {
    if (!filled) return { bg: 'var(--gray-50)', text: 'var(--gray-400)', iconBg: 'var(--gray-400)' }
    switch (key) {
      case 'job_title':
        return { bg: 'var(--gray-50)', text: 'var(--gray-600)', iconBg: 'var(--gray-600)' }
      case 'location':
        return { bg: 'var(--gray-50)', text: 'var(--wedo-purple)', iconBg: 'var(--wedo-purple)' }
      case 'skills':
        return { bg: 'var(--gray-50)', text: 'var(--status-success)', iconBg: 'var(--wedo-green-light)' }
      case 'years_experience':
        return { bg: 'var(--gray-50)', text: 'var(--status-warning)', iconBg: 'var(--wedo-orange)' }
      case 'industry':
        return { bg: 'var(--gray-50)', text: 'var(--gray-600)', iconBg: 'var(--gray-600)' }
      default:
        return { bg: 'var(--gray-50)', text: 'var(--gray-600)', iconBg: 'var(--gray-600)' }
    }
  }, [])
  
  // Critérios extraídos (pills)
  interface SearchCriterion {
    id: string
    type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
    label: string
    value: string
    active: boolean
  }
  const [extractedCriteria, setExtractedCriteria] = useState<SearchCriterion[]>([])
  
  // Handler para remover critério
  const removeCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.filter(c => c.id !== id))
  }
  
  // Handler para toggle critério
  const toggleCriterion = (id: string) => {
    setExtractedCriteria(prev => prev.map(c => 
      c.id === id ? { ...c, active: !c.active } : c
    ))
  }
  
  // Referência para debounce da extração
  const extractionTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)
  const lastQueryRef = React.useRef<string>('')
  
  // Extração incremental de critérios com debounce - mescla com estado anterior
  const extractCriteriaFromQuery = React.useCallback((query: string) => {
    // Debounce de 300ms para evitar race conditions
    if (extractionTimeoutRef.current) {
      clearTimeout(extractionTimeoutRef.current)
    }
    
    extractionTimeoutRef.current = setTimeout(() => {
      const queryLower = query.toLowerCase().trim()
      
      // Evitar re-execução para mesma query
      if (queryLower === lastQueryRef.current) return
      lastQueryRef.current = queryLower
      
      setExtractedCriteria(prev => {
        // Manter critérios existentes que foram modificados manualmente
        const manuallyModified = prev.filter(c => !c.active)
        const newlyExtracted: SearchCriterion[] = []
        
        // Extrair localização
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
        
        // Extrair experiência
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
        
        // Extrair skills
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
        
        // Extrair idioma
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
        
        // Extrair senioridade
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
              newlyExtracted.push({
                id,
                type: 'job_title',
                label: 'Senioridade',
                value,
                active: true
              })
            }
            break
          }
        }
        
        // Mesclar: manter existentes ativos + manter desativados manualmente + adicionar novos
        const existingActive = prev.filter(c => c.active)
        const merged = [...existingActive, ...manuallyModified]
        
        // Adicionar novos critérios que não existem
        for (const newCrit of newlyExtracted) {
          if (!merged.find(c => c.id === newCrit.id)) {
            merged.push(newCrit)
          }
        }
        
        return merged
      })
    }, 300)
  }, [])
  
  // Cleanup do timeout ao desmontar
  React.useEffect(() => {
    return () => {
      if (extractionTimeoutRef.current) {
        clearTimeout(extractionTimeoutRef.current)
      }
    }
  }, [])
  
  // Construir query de busca a partir dos critérios ativos
  const buildSearchQueryFromCriteria = React.useCallback(() => {
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
  
  // Executar busca com critérios ativos
  const executeSearchWithCriteria = React.useCallback(() => {
    const searchQuery = buildSearchQueryFromCriteria()
    if (searchQuery.trim()) {
      onCommand(searchQuery, 'natural_search')
    }
  }, [buildSearchQueryFromCriteria, onCommand])

  // Sistema de templates inteligente
  const templateSuggestions = useTemplateSuggestions()
  const suggestionQueue = useTemplateSuggestionQueue()

  // Controlar expansão forçada
  useEffect(() => {
    if (forceExpanded !== undefined) {
      setIsExpanded(forceExpanded)
    }
  }, [forceExpanded])

  // Verificar execução de template salvo
  useEffect(() => {
    const executeTemplate = sessionStorage.getItem('lia-execute-template')
    if (executeTemplate) {
      try {
        const template = JSON.parse(executeTemplate)
        setInputValue(template.command)
        setIsExpanded(true)

        // Executar automaticamente após delay
        setTimeout(() => {
          handleSubmit(new Event('submit') as any)
        }, 1000)

        sessionStorage.removeItem('lia-execute-template')
      } catch (error) {
      }
    }
  }, [])

  // 🔖 Carregar templates salvos
  const [savedTemplates, setSavedTemplates] = useState<any[]>([])

  useEffect(() => {
    const templates = localStorage.getItem('lia-templates')
    if (templates) {
      try {
        const parsed = JSON.parse(templates)
        // Pegar apenas os 3 templates mais usados
        const topTemplates = parsed
          .sort((a: any, b: any) => b.usageCount - a.usageCount)
          .slice(0, 3)
        setSavedTemplates(topTemplates)
      } catch (error) {
      }
    }
  }, [])

  // 🧠 Sugestões inteligentes baseadas no contexto - EXPANDIDO
  const getSmartSuggestions = () => {
    // Sugestões específicas para candidato individual (quando clicou na LIA)
    if (candidateContext) {
      return [
        {
          id: 'analyze_profile',
          icon: '🔍',
          label: `Analisar perfil completo de ${candidateContext.name}`,
          description: 'Análise detalhada de competências, fit cultural e potencial',
          action: 'analyze_individual_profile'
        },
        {
          id: 'generate_interview_questions',
          icon: '❓',
          label: 'Gerar roteiro de entrevista personalizado',
          description: 'Perguntas técnicas e comportamentais baseadas no perfil',
          action: 'generate_interview_questions'
        },
        {
          id: 'draft_email',
          icon: '📧',
          label: 'Rascunhar convite personalizado',
          description: 'Email de convite customizado para o candidato',
          action: 'draft_personalized_email'
        },
        {
          id: 'compare_with_role',
          icon: '⚖️',
          label: 'Comparar com requisitos da vaga',
          description: 'Match detalhado com job description',
          action: 'compare_with_job_requirements'
        },
        {
          id: 'predict_success',
          icon: '🎯',
          label: 'Predizer sucesso na posição',
          description: 'Análise preditiva baseada em dados históricos',
          action: 'predict_candidate_success'
        },
        {
          id: 'salary_benchmark',
          icon: '💰',
          label: 'Benchmark salarial personalizado',
          description: 'Comparação com mercado baseada no perfil específico',
          action: 'salary_benchmark'
        }
      ]
    }

    const selectedCount = selectedCandidates.length
    const allSuggestions: any[] = []

    // 🔖 Templates salvos (aparecem primeiro quando relevantes)
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

    // EXPANDIDO: Sem candidatos selecionados - sugestões avançadas de busca e gestão
    if (selectedCount === 0) {
      const advancedSuggestions = [
        // Buscas Inteligentes Avançadas
        {
          id: 'smart_search_ai',
          icon: '🧠',
          label: 'Busca inteligente com IA',
          description: 'Descreva o perfil ideal e a LIA encontra candidatos similares',
          action: 'ai_smart_search',
          category: 'search'
        },
        {
          id: 'boolean_search_expert',
          icon: '🔧',
          label: 'Busca booleana avançada',
          description: 'Construtor visual de queries complexas para LinkedIn/Github',
          action: 'boolean_search_builder',
          category: 'search'
        },
        {
          id: 'passive_candidates',
          icon: '🕵️',
          label: 'Identificar candidatos passivos',
          description: 'Encontrar talentos que não estão procurando ativamente',
          action: 'find_passive_candidates',
          category: 'search'
        },
        {
          id: 'competitor_analysis',
          icon: '🏢',
          label: 'Mapear concorrentes e talentos',
          description: 'Análise de empresas similares e seus melhores profissionais',
          action: 'competitor_talent_mapping',
          category: 'search'
        },

        // Gestão e Organização Avançada
        {
          id: 'pipeline_automation',
          icon: '⚙️',
          label: 'Automatizar pipeline de talentos',
          description: 'Configurar fluxos automáticos para diferentes perfis',
          action: 'setup_pipeline_automation',
          category: 'automation'
        },
        {
          id: 'email_sequences',
          icon: '📬',
          label: 'Sequências de email inteligentes',
          description: 'Campanhas de nurturing personalizadas por segmento',
          action: 'create_email_sequences',
          category: 'automation'
        },
        {
          id: 'calendar_optimization',
          icon: '📅',
          label: 'Otimizar agenda de entrevistas',
          description: 'Sugerir melhor organização e horários mais eficientes',
          action: 'optimize_interview_calendar',
          category: 'automation'
        },

        // Analytics e Insights
        {
          id: 'market_trends',
          icon: '📈',
          label: 'Análise de tendências do mercado',
          description: 'Insights sobre salários, demanda e escassez de talentos',
          action: 'analyze_market_trends',
          category: 'analytics'
        },
        {
          id: 'diversity_analysis',
          icon: '🌈',
          label: 'Análise de diversidade e inclusão',
          description: 'Métricas D&I e sugestões para melhorar representatividade',
          action: 'diversity_inclusion_analysis',
          category: 'analytics'
        },
        {
          id: 'conversion_funnels',
          icon: '🎯',
          label: 'Análise de funis de conversão',
          description: 'Identificar gargalos e oportunidades de melhoria',
          action: 'analyze_conversion_funnels',
          category: 'analytics'
        },
        {
          id: 'predictive_hiring',
          icon: '🔮',
          label: 'Previsões de contratação',
          description: 'Predizer necessidades futuras baseado em crescimento',
          action: 'predictive_hiring_analysis',
          category: 'analytics'
        },

        // Ferramentas Especializadas
        {
          id: 'interview_scorecards',
          icon: '📋',
          label: 'Criar scorecards de entrevista',
          description: 'Formulários estruturados para avaliação consistente',
          action: 'create_interview_scorecards',
          category: 'tools'
        },
        {
          id: 'reference_automation',
          icon: '📞',
          label: 'Automatizar checagem de referências',
          description: 'Templates e fluxos para verificação de background',
          action: 'automate_reference_checks',
          category: 'tools'
        },
        {
          id: 'onboarding_preparation',
          icon: '🎯',
          label: 'Preparar onboarding personalizado',
          description: 'Planos customizados baseados no perfil do novo hire',
          action: 'prepare_custom_onboarding',
          category: 'tools'
        },

        // Inteligência Competitiva
        {
          id: 'salary_intelligence',
          icon: '💎',
          label: 'Inteligência salarial avançada',
          description: 'Benchmarks detalhados por região, experiência e skills',
          action: 'advanced_salary_intelligence',
          category: 'intelligence'
        },
        {
          id: 'skill_gap_analysis',
          icon: '🔍',
          label: 'Análise de lacunas de habilidades',
          description: 'Identificar skills em falta no time e no mercado',
          action: 'skill_gap_analysis',
          category: 'intelligence'
        },
        {
          id: 'employer_branding',
          icon: '✨',
          label: 'Otimizar employer branding',
          description: 'Sugestões para melhorar atratividade da empresa',
          action: 'optimize_employer_branding',
          category: 'intelligence'
        }
      ]

      // Retornar sugestões variadas (8-10 por vez, rotacionando)
      const shuffled = advancedSuggestions.sort(() => 0.5 - Math.random())
      allSuggestions.push(...shuffled.slice(0, 10))
      return allSuggestions
    }

    // 1 candidato selecionado - ações individuais expandidas
    if (selectedCount === 1) {
      const candidate = selectedCandidates[0]
      const candidateName = candidate.name || 'Candidato'
      const candidateScore = candidate.liaAnalysis?.score || candidate.score || 0

      const individualSuggestions = [
        {
          id: 'send_personalized_email',
          icon: '📧',
          label: `Enviar convite personalizado para ${candidateName}`,
          description: 'Email customizado baseado no perfil e interesses',
          action: 'send_personalized_email'
        },
        {
          id: 'schedule_interview',
          icon: '📅',
          label: 'Agendar entrevista estratégica',
          description: 'Escolher melhor horário e formato baseado no perfil',
          action: 'schedule_strategic_interview'
        },
        {
          id: 'deep_profile_analysis',
          icon: '🔬',
          label: 'Análise profunda do perfil',
          description: 'Investigação completa de competências e fit cultural',
          action: 'deep_profile_analysis'
        },
        {
          id: 'salary_negotiation_prep',
          icon: '💰',
          label: 'Preparar negociação salarial',
          description: 'Estratégia e faixas baseadas no perfil específico',
          action: 'prepare_salary_negotiation'
        },
        {
          id: 'reference_check_strategy',
          icon: '📋',
          label: 'Estratégia de referências',
          description: 'Plano para checagem de background e referências',
          action: 'plan_reference_checks'
        },
        {
          id: 'competitor_intel',
          icon: '🕵️',
          label: 'Intel sobre empresa atual',
          description: 'Pesquisa sobre empresa e possíveis motivadores',
          action: 'research_current_company'
        }
      ]

      // Sugestões condicionais baseadas no score
      if (candidateScore >= 85) {
        individualSuggestions.push({
          id: 'fast_track_vip',
          icon: '⚡',
          label: 'Fast-track VIP',
          description: 'Processo acelerado para candidato excepcional',
          action: 'vip_fast_track'
        })
      }

      if (candidateScore < 70) {
        individualSuggestions.push({
          id: 'improvement_coaching',
          icon: '📚',
          label: 'Coaching para candidato',
          description: 'Sugestões de desenvolvimento para melhorar fit',
          action: 'candidate_coaching_suggestions'
        })
      }

      return individualSuggestions
    }

    // Múltiplos candidatos - ações em lote expandidas
    const batchSuggestions = [
      {
        id: 'bulk_email_campaign',
        icon: '📧',
        label: `Campanha de email para ${selectedCount} candidatos`,
        description: 'Emails personalizados em massa com A/B testing',
        action: 'bulk_email_campaign'
      },
      {
        id: 'comparative_analysis',
        icon: '📊',
        label: `Análise comparativa detalhada`,
        description: 'Relatório completo comparando perfis selecionados',
        action: 'detailed_comparative_analysis'
      },
      {
        id: 'interview_coordination',
        icon: '🗓️',
        label: 'Coordenar entrevistas em lote',
        description: 'Otimizar agenda para múltiplas entrevistas',
        action: 'coordinate_batch_interviews'
      },
      {
        id: 'shortlist_creation',
        icon: '⭐',
        label: 'Criar shortlist inteligente',
        description: 'Ranking automático baseado em critérios específicos',
        action: 'create_intelligent_shortlist'
      },
      {
        id: 'diversity_check',
        icon: '🌈',
        label: 'Verificar diversidade do grupo',
        description: 'Análise D&I do conjunto de candidatos selecionados',
        action: 'check_group_diversity'
      },
      {
        id: 'salary_range_analysis',
        icon: '💰',
        label: 'Análise de faixas salariais',
        description: 'Comparar expectativas e definir estratégia de ofertas',
        action: 'analyze_salary_ranges'
      },
      {
        id: 'rejection_management',
        icon: '💔',
        label: 'Gestão inteligente de rejeições',
        description: 'Feedback personalizado e manutenção de relacionamento',
        action: 'manage_intelligent_rejections'
      }
    ]

    return batchSuggestions
  }

  const suggestions = getSmartSuggestions()

  // 🎯 Placeholder dinâmico baseado no contexto
  const getPlaceholder = () => {
    // Contexto específico do candidato (quando clicou na LIA de um candidato)
    if (candidateContext) {
      return `O que gostaria de fazer com ${candidateContext.name}? Ex: analisar perfil, enviar email, agendar entrevista, comparar com outros...`
    }

    const selectedCount = selectedCandidates.length

    if (selectedCount === 0) {
      return "Peça à LIA para filtrar candidatos, fazer buscas específicas, analisar perfis, enviar emails, agendar entrevistas, comparar candidatos..."
    }

    if (selectedCount === 1) {
      return `O que fazer com ${selectedCandidates[0].name}?`
    }

    return `${selectedCount} candidatos selecionados. Como proceder?`
  }

  // 🎙️ Voice input simulation
  const handleVoiceToggle = () => {
    setIsListening(!isListening)
    if (!isListening) {
      setTimeout(() => {
        setInputValue("Enviar convite para desenvolvedores selecionados")
        setIsListening(false)
      }, 2000)
    }
  }

  // ⌨️ Atalhos de teclado
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape para fechar
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false)
        setShowHistory(false)
      }

      // Ctrl+K para focar no prompt
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault()
        setIsExpanded(true)
        // Focar no input após um tick
        setTimeout(() => {
          const input = document.querySelector('input[placeholder*="LIA"]') as HTMLInputElement
          input?.focus()
        }, 100)
      }

      // Ctrl+H para mostrar histórico
      if (e.ctrlKey && e.key === 'h' && isExpanded && commandHistory.length > 0) {
        e.preventDefault()
        setShowHistory(!showHistory)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isExpanded, showHistory, commandHistory.length])

  // 📝 Submit do prompt
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isProcessing) {
      setIsProcessing(true)
      setLastCommand(inputValue)

      // Registrar comando no sistema de templates
      templateSuggestions.addCommand(inputValue, getAdvancedFilters(), ['text_command'])

      // Adicionar ao histórico local
      setCommandHistory(prev => [inputValue, ...prev.slice(0, 4)])

      // Simular processamento
      setTimeout(() => {
        onCommand(inputValue, 'text_command')
        setInputValue("")
        setIsExpanded(false)
        setIsProcessing(false)

        // Verificar se deve sugerir template
        checkForTemplateSuggestions()
      }, 1500)
    }
  }

  // ✨ Clique em sugestão
  const handleSuggestionClick = (suggestion: any) => {
    if (!isProcessing) {
      setIsProcessing(true)
      setLastCommand(suggestion.label)

      // Tratamento especial para templates salvos
      if (suggestion.isTemplate) {
        executeTemplate(suggestion.template)
        return
      }

      // Registrar comando no sistema de templates
      templateSuggestions.addCommand(suggestion.label, getAdvancedFilters(), [suggestion.action])

      // Adicionar ao histórico local
      setCommandHistory(prev => [suggestion.label, ...prev.slice(0, 4)])

      // Simular processamento
      setTimeout(() => {
        onCommand(suggestion.label, suggestion.action)
        setIsExpanded(false)
        setIsProcessing(false)

        // Verificar se deve sugerir template
        checkForTemplateSuggestions()
      }, 1200)
    }
  }

  // 🔖 Executar template salvo
  const executeTemplate = (template: any) => {
    // Incrementar contador de uso
    const templates = JSON.parse(localStorage.getItem('lia-templates') || '[]')
    const updatedTemplates = templates.map((t: any) =>
      t.id === template.id
        ? { ...t, usageCount: t.usageCount + 1, updatedAt: new Date() }
        : t
    )
    localStorage.setItem('lia-templates', JSON.stringify(updatedTemplates))

    // Executar ações do template
    setTimeout(() => {
      onCommand(template.command, template.actions[0] || 'execute_template')
      setIsExpanded(false)
      setIsProcessing(false)
    }, 1000)
  }

  // Helper para obter filtros avançados (mock)
  const getAdvancedFilters = () => {
    // Em uma implementação real, isso viria do contexto da página
    return {
      selectedCandidates: selectedCandidates.length,
      contextType: 'candidates',
      filteredCount,
      totalCount
    }
  }

  // Verificar e mostrar sugestões de template
  const checkForTemplateSuggestions = () => {
    const pendingSuggestions = templateSuggestions.getPendingSuggestions()

    pendingSuggestions.forEach(suggestion => {
      if (templateSuggestions.shouldShowSuggestion(suggestion)) {
        suggestionQueue.addSuggestion(suggestion)
        templateSuggestions.markSuggestionAsShown(suggestion.id)
      }
    })
  }
  
  // Convert parsedEntities to SearchSpec for save archetype modal
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
  
  // Check if we can save as archetype (has query or parsed entities)
  const canSaveAsArchetype = useMemo(() => {
    return naturalSearchValue.trim().length > 3 || 
           (parsedEntities && Object.values(parsedEntities).some(v => v && (Array.isArray(v) ? v.length > 0 : true)))
  }, [naturalSearchValue, parsedEntities])
  
  // Handler for successful archetype save
  const handleArchetypeSaved = (newArchetype: any) => {
    setArchetypes(prev => [...prev, newArchetype])
    toast({
      title: "Arquétipo salvo",
      description: `"${newArchetype.name}" foi adicionado aos seus arquétipos.`
    })
  }

  // 📜 Usar comando do histórico
  const handleHistoryCommand = (command: string) => {
    setInputValue(command)
    setShowHistory(false)
  }

  // 📊 Status info
  const getStatusInfo = () => {
    const selectedCount = selectedCandidates.length

    if (selectedCount > 0) {
      return {
        text: `${selectedCount} selecionado${selectedCount > 1 ? 's' : ''}`,
        color: 'text-gray-700',
        bgColor: 'bg-gray-50 border-gray-100'
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
      color: 'text-gray-600',
      bgColor: 'bg-white border-gray-100'
    }
  }

  const statusInfo = getStatusInfo()

  return (
    <div className="space-y-3">

      {/* Candidato Específico Preview */}
      {candidateContext && (
        <div className="bg-wedo-green-light/5 rounded-md p-3 border border-wedo-green-light/20">
          <div className="flex items-center gap-2 mb-2">
            <LIAIcon size="sm" />
            <span className="text-base-ui font-semibold text-gray-800">
              Análise LIA para candidato específico
            </span>
          </div>
          <div className="flex items-center gap-3 bg-white rounded-md px-3 py-2 border border-gray-100">
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-wedo-green-light/10 text-wedo-green-light text-sm">
                {candidateContext.name?.split(' ').map((n: string) => n[0]).join('') || 'C'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-medium text-gray-800 text-base-ui">
                {candidateContext.name}
              </div>
              <div className="text-xs text-gray-800 dark:text-gray-200">
                {candidateContext.position} • Score: {candidateContext.liaAnalysis?.score || candidateContext.score}%
              </div>
            </div>
            <Badge className="bg-wedo-green-light/10 text-wedo-green-light border-0 text-micro">
              Foco Individual
            </Badge>
          </div>
        </div>
      )}

      {/* Candidatos Selecionados Preview */}
      {!candidateContext && selectedCandidates.length > 0 && (
        <div className="bg-gray-50 rounded-md p-3 border border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-gray-600" />
            <span className="text-base-ui font-semibold text-gray-800">
              {selectedCandidates.length} candidato{selectedCandidates.length > 1 ? 's' : ''} selecionado{selectedCandidates.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCandidates.slice(0, 3).map((candidate, index) => (
              <div key={index} className="flex items-center gap-1 bg-white rounded-md px-2 py-1 border border-gray-100">
                <Avatar className="w-4 h-4">
                  <AvatarFallback className="bg-gray-200 text-gray-700 text-xs">
                    {candidate.name?.charAt(0) || 'C'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-xs text-gray-800 dark:text-gray-200">
                  {candidate.name || `Candidato ${index + 1}`}
                </span>
              </div>
            ))}
            {selectedCandidates.length > 3 && (
              <div className="px-2 py-1 bg-gray-100 rounded-full text-xs text-gray-800 dark:text-gray-200">
                +{selectedCandidates.length - 3} mais
              </div>
            )}
          </div>
        </div>
      )}

      {/* Prompt Principal */}
      <div className={`transition-all duration-300 ${statusInfo.bgColor} rounded-md border ${statusInfo.bgColor.includes('border') ? '' : 'border-gray-100'} overflow-hidden`}>

        {/* Campo de input compacto */}
        <div className="p-3">
          <form onSubmit={handleSubmit} className="flex items-center gap-3">

            {/* LIA Icon */}
            <LIAIcon
              size="lg"
              animate={isProcessing}
              className={`flex-shrink-0 transition-all duration-300 ${isProcessing ? 'scale-110' : ''}`}
            />

            {/* Input Field */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => !isProcessing && setIsExpanded(true)}
              placeholder={isProcessing ? "LIA processando..." : getPlaceholder()}
              disabled={isProcessing}
              className={`flex-1 bg-transparent text-gray-950 dark:text-gray-50 placeholder-gray-500 text-xs focus:outline-none ${
                isProcessing ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            />

            {/* Seletor de Origem de Busca - Sempre Visível (Compacto) */}
            <div className="flex items-center gap-0.5 mr-1.5">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                      className={`p-1.5 rounded-md transition-all ${
                        searchSource === 'local' 
                          ? 'bg-gray-200' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-600'}`} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs">Base Local (Gratuito)</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              {showGlobalSearchOptions && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleSourceChange('hybrid'); }}
                        className={`p-1.5 rounded-md transition-all ${
                          searchSource === 'hybrid' 
                            ? 'bg-gray-200' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-600'}`} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs">Local + Global (1 créd/cand)</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              
              {showGlobalSearchOptions && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleSourceChange('global'); }}
                        className={`p-1.5 rounded-md transition-all ${
                          searchSource === 'global' 
                            ? 'bg-gray-200' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-600'}`} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs">Busca Global (1 créd/cand)</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              
              {/* Separador visual */}
              <div className="w-px h-4 bg-gray-200 mx-1" />
              
              {/* Toggle Email */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                      className={`p-1.5 rounded-md transition-all ${
                        requireEmails 
                          ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-micro text-gray-400">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              {/* Toggle Telefone */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                      className={`p-1.5 rounded-md transition-all ${
                        requirePhoneNumbers 
                          ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                          : 'hover:bg-gray-100'
                      }`}
                    >
                      <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            {/* Status Info */}
            <div className={`text-xs ${statusInfo.color} flex items-center gap-1`}>
              <span>●</span>
              {statusInfo.text}
            </div>

            {/* Suggestions & Queries Guide Buttons */}
            <div className="flex items-center gap-0.5">
              <PromptSuggestionsPopover
                onSelect={(command) => {
                  setInputValue(command)
                  setIsExpanded(true)
                }}
                context={{
                  hasJob: !!jobContext?.id,
                  jobTitle: jobContext?.title,
                  selectedCandidatesCount: selectedCandidates.length,
                  currentPage: pageContext
                }}
              />
              
              {pageContext === 'candidates' ? (
                <CandidateQueriesGuide
                  onSelectQuery={(query) => {
                    setInputValue(query)
                    setIsExpanded(true)
                  }}
                />
              ) : (
                <LiaQueriesGuide
                  onSelectQuery={(query) => {
                    setInputValue(query)
                    setIsExpanded(true)
                  }}
                />
              )}
            </div>

            {/* File Upload Button */}
            <FileUploadButton
              onFilesSelected={() => {}}
              onFileAnalyzed={handleFileAnalyzed}
              maxFiles={2}
              acceptedTypes=".pdf,.doc,.docx,.txt"
              showPreview={false}
              autoAnalyze={true}
            />

            {/* Audio Record Button */}
            <AudioRecordButton
              onTranscription={handleAudioTranscription}
              maxDuration={60}
            />

            {/* Close/Expand/Send Button */}
            {candidateContext && onClose ? (
              <button
                type="button"
                onClick={onClose}
                className="w-8 h-8 lia-btn-secondary rounded-md flex items-center justify-center transition-colors bg-gray-800" style={{color: 'white'}}
                title="Fechar análise do candidato"
              >
                <X className="w-4 h-4" />
              </button>
            ) : (
              <button
                type={inputValue.trim() ? "submit" : "button"}
                onClick={inputValue.trim() ? undefined : () => setIsExpanded(!isExpanded)}
                className="w-8 h-8 lia-btn-primary flex items-center justify-center"
              >
                {inputValue.trim() ? <Send className="w-4 h-4" /> :
                 isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            )}
          </form>
        </div>

        {/* Área Expandida - REORGANIZADA SEM DUPLICAÇÃO */}
        {isExpanded && (
          <div className="lia-prompt-expanded space-y-4" style={{backgroundColor: 'var(--gray-100)'}}>

            {/* AI-First Context Pills + Quick Actions */}
            {(contextPill || quickActions.length > 0) && (
              <div className="p-4 pb-0 border-b border-b-gray-200">
                {contextPill && (
                  <div className="mb-3">
                    <ContextPill
                      icon={contextPill.icon}
                      primaryText={contextPill.primaryText}
                      secondaryText={contextPill.secondaryText}
                      onDismiss={contextPill.onDismiss}
                    />
                  </div>
                )}
                
                {quickActions.length > 0 && (
                  <div>
                    <div className="text-xs mb-2 lia-body">
                      Ações rápidas:
                    </div>
                    <QuickActionChips actions={quickActions} />
                  </div>
                )}
              </div>
            )}

            {/* 🧠 PESQUISA AVANÇADA - Sistema de 6 Abas */}
            <div className="p-4 pb-0">
              {/* Header com LIA Icon e Controles de Fonte/Créditos */}
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <LIAIcon size="sm" />
                  <span className="text-sm lia-heading">Pesquisa Avançada</span>
                </div>
                
                <div className="flex items-center gap-3">
                  {/* Seletor de Fonte de Busca */}
                  <div className="lia-tabs-container flex items-center gap-1">
                    <button
                      onClick={() => setSearchSource('local')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'local' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar apenas na base local (sem consumo de créditos)"
                    >
                      <Home className="w-3 h-3" />
                      <span className="hidden sm:inline">Local</span>
                    </button>
                    <button
                      onClick={() => handleSourceChange('hybrid')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'hybrid' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar na base local + Base Global (consome créditos para resultados externos)"
                    >
                      <Zap className="w-3 h-3" />
                      <span className="hidden sm:inline">Híbrido</span>
                    </button>
                    <button
                      onClick={() => handleSourceChange('global')}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-all ${
                        searchSource === 'global' 
                          ? 'lia-tab-active' 
                          : 'lia-tab'
                      }`}
                      title="Buscar apenas na Base Global (800M+ perfis, consome créditos)"
                    >
                      <Globe className="w-3 h-3" />
                      <span className="hidden sm:inline">Global</span>
                    </button>
                  </div>
                  
                  {/* Estimativa de Créditos em Tempo Real */}
                  <div className="relative group">
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs ${
                      creditEstimate.isLocal 
                        ? 'bg-status-success/10 text-status-success' 
                        : !creditEstimate.canAfford
                          ? 'bg-status-error/10 text-status-error'
                          : getCostLevel(creditEstimate.total) === 'low' 
                            ? 'bg-status-success/10 text-status-success'
                            : getCostLevel(creditEstimate.total) === 'medium'
                              ? 'bg-status-warning/10 text-status-warning'
                              : 'bg-status-error/10 text-status-error'
                    }`}>
                      <Coins className="w-3 h-3" />
                      <span className="font-medium">
                        {creditEstimate.isLoading ? (
                          '...'
                        ) : creditEstimate.isLocal ? (
                          'Gratuito'
                        ) : (
                          `~${creditEstimate.total} créditos`
                        )}
                      </span>
                      {!creditEstimate.isLocal && !creditEstimate.canAfford && (
                        <AlertCircle className="w-3 h-3 text-status-error" />
                      )}
                    </div>
                    
                    {/* Tooltip de Detalhes de Créditos */}
                    <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block z-50">
                      <div className="bg-gray-900 text-white px-3 py-2 rounded-md text-xs min-w-[220px]">
                        <div className="font-semibold mb-2 flex items-center gap-1.5">
                          <Coins className="w-3.5 h-3.5 text-status-warning" />
                          Estimativa de Custo
                        </div>
                        {creditEstimate.isLocal ? (
                          <div className="text-status-success">
                            Busca local gratuita - sem consumo de créditos
                          </div>
                        ) : (
                          <div className="space-y-1.5">
                            {/* Saldo disponível */}
                            {creditEstimate.availableCredits !== undefined && (
                              <div className="flex justify-between pb-1.5 border-b border-gray-700">
                                <span className="text-gray-300">Saldo disponível:</span>
                                <span className={`font-medium ${
                                  creditEstimate.canAfford ? 'text-status-success' : 'text-status-error'
                                }`}>
                                  {creditEstimate.availableCredits} créditos
                                </span>
                              </div>
                            )}
                            <div className="flex justify-between">
                              <span className="text-gray-300">Tipo de busca:</span>
                              <span className="font-medium">{pearchSearchType === 'fast' ? 'Rápida' : 'Profissional'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-300">Por candidato:</span>
                              <span className="font-medium">{creditEstimate.perCandidate} créditos</span>
                            </div>
                            <div className="flex justify-between pt-1.5 border-t border-gray-700">
                              <span className="text-gray-300">Total ({candidateLimit} cand.):</span>
                              <span className={`font-bold ${getCostColor(getCostLevel(creditEstimate.total))}`}>
                                {creditEstimate.total} créditos
                              </span>
                            </div>
                            {!creditEstimate.canAfford && (
                              <div className="text-xs text-status-error mt-1.5 pt-1.5 border-t border-gray-700 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                Saldo insuficiente para esta busca
                              </div>
                            )}
                          </div>
                        )}
                        <div className="absolute bottom-full right-4 border-4 border-transparent border-b-gray-900"></div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Contador de critérios */}
                  <span className="text-xs text-gray-600 hidden md:inline">
                    {filledTagsCount}/5 critérios
                  </span>
                </div>
              </div>
              
              {/* 6 Abas de Pesquisa */}
              <div className="flex items-center gap-1.5 mb-3 overflow-x-auto pb-1">
                <button
                  onClick={() => setActiveSearchTab('natural')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'natural'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  IA Natural
                </button>
                <button
                  onClick={() => setActiveSearchTab('similar')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'similar'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Users className="w-3 h-3" />
                  Similar
                </button>
                <button
                  onClick={() => setActiveSearchTab('job-description')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'job-description'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <FileText className="w-3 h-3" />
                  D. Cargo
                </button>
                <button
                  onClick={() => setActiveSearchTab('boolean')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'boolean'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Code className="w-3 h-3" />
                  Boleana
                </button>
                <button
                  onClick={() => setActiveSearchTab('filtros')}
                  className={`flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    activeSearchTab === 'filtros'
                      ? 'lia-pill-active'
                      : 'lia-pill'
                  }`}
                >
                  <Filter className="w-3 h-3" />
                  Filtros
                </button>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href="/funil?expandedSearch=true"
                        className="ml-1 p-1.5 rounded-md hover:bg-gray-100 transition-all border border-gray-200"
                      >
                        <Table2 className="w-3.5 h-3.5 text-gray-500" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p className="text-xs font-medium">Abrir em Tabela</p>
                      <p className="text-micro text-gray-400">Ir para resultados de busca</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Conteúdo da Aba Ativa */}
              <div className="mb-3">
                {/* Aba: Quem você procura? (IA Natural) */}
                {activeSearchTab === 'natural' && (
                  <div>
                    <div className="relative">
                      <input
                        type="text"
                        value={naturalSearchValue}
                        onChange={(e) => {
                          const value = e.target.value
                          setNaturalSearchValue(value)
                          
                          if (value.length >= 2) {
                            setShowPremiumAutocomplete(true)
                          } else {
                            setShowPremiumAutocomplete(false)
                          }
                          
                          if (extractionTimeoutRef.current) {
                            clearTimeout(extractionTimeoutRef.current)
                          }
                          
                          extractionTimeoutRef.current = setTimeout(() => {
                            parseEntitiesFromQuery(value)
                            if (autocompleteEnabled) {
                              fetchAutocomplete(value)
                            }
                          }, 400)
                        }}
                        onKeyDown={handleAutocompleteKeyDown}
                        onFocus={() => {
                          if (naturalSearchValue.length >= 2) {
                            setShowPremiumAutocomplete(true)
                          }
                        }}
                        onBlur={() => setTimeout(() => {
                          setShowAutocomplete(false)
                          setShowPremiumAutocomplete(false)
                        }, 200)}
                        placeholder="Descreva o candidato ideal em linguagem natural..."
                        className="lia-input w-full px-4 py-2.5 text-sm pr-[180px]"
                      />
                      
                      {/* Ícones de Fonte e Contato dentro do input */}
                      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                        {/* Fonte de busca: Local / Híbrido / Global */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  searchSource === 'local' 
                                    ? 'bg-gray-200' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-500'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Base Local</p>
                              <p className="text-micro text-gray-400">Gratuito</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {showGlobalSearchOptions && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); handleSourceChange('hybrid'); }}
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'hybrid' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {showGlobalSearchOptions && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); handleSourceChange('global'); }}
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'global' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Base Global</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Contato: Email / Telefone */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requireEmails 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-micro text-gray-400">{requireEmails ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requirePhoneNumbers 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Botão de Buscar */}
                        <button 
                          className="w-7 h-7 lia-btn-primary flex items-center justify-center"
                          onClick={() => executeSearchWithCriteria()}
                        >
                          <Search className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      
                      {/* Autocomplete Dropdown */}
                      {showAutocomplete && autocompleteSuggestions.length > 0 && (
                        <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-100 rounded-md z-50 max-h-48 overflow-y-auto">
                          {autocompleteSuggestions.map((suggestion, index) => (
                            <button
                              key={index}
                              onClick={() => {
                                setNaturalSearchValue(prev => {
                                  const words = prev.split(' ')
                                  words.pop()
                                  const insertValue = suggestion.insert_text || suggestion.text
                                  return [...words, insertValue].join(' ') + ' '
                                })
                                setShowAutocomplete(false)
                              }}
                              className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between transition-colors ${
                                selectedAutocompleteIndex === index 
                                  ? 'bg-gray-100' 
                                  : 'hover:bg-gray-50'
                              }`}
                            >
                              <span style={{color: 'var(--gray-950)'}}>{suggestion.text}</span>
                              <span className="text-xs text-gray-400">{suggestion.category}</span>
                            </button>
                          ))}
                          <div className="px-3 py-1.5 text-xs flex items-center justify-between text-gray-400" style={{borderTop: '1px solid var(--overlay-05)'}}>
                            <span>Use ↑↓ para navegar, Tab para selecionar</span>
                            <span>Esc para fechar</span>
                          </div>
                        </div>
                      )}
                      
                      {/* Premium Autocomplete - Company-based suggestions */}
                      <PremiumAutocomplete
                        query={naturalSearchValue}
                        onSelect={handlePremiumAutocompleteSelect}
                        isOpen={showPremiumAutocomplete && naturalSearchValue.length >= 2 && !showAutocomplete}
                        onClose={() => setShowPremiumAutocomplete(false)}
                      />
                    </div>
                    
                    {/* Prompt Enhancement Card */}
                    {promptEnhancement && !showAutocomplete && (
                      <div 
                        className="mt-2 p-3 rounded-md border transition-all bg-gray-200/20" style={{ borderColor: 'var(--wedo-cyan-border)' }}
                      >
                        <div className="flex items-start gap-2">
                          <Wand2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="text-xs font-medium text-gray-700">Sugestão da LIA</span>
                              {isEnhancingPrompt && (
                                <div className="w-3 h-3 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" />
                              )}
                            </div>
                            <p className="text-sm text-gray-800 dark:text-gray-200 mb-2">{promptEnhancement.enhanced_query}</p>
                            {promptEnhancement.explanation && (
                              <p className="text-xs text-gray-500 mb-2">{promptEnhancement.explanation}</p>
                            )}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={handleAcceptEnhancement}
                                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors bg-gray-900" style={{color: 'white'}}
                              >
                                <Check className="w-3 h-3" />
                                Usar sugestão
                              </button>
                              <button
                                onClick={handleDismissEnhancement}
                                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                              >
                                <X className="w-3 h-3" />
                                Ignorar
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Indicador de Fonte de Busca */}
                    {searchSource === 'local' && (
                      <div className="flex items-center gap-1.5 mt-2 mb-1">
                        <div 
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                          style={{backgroundColor: 'var(--wedo-cyan-bg-08)', 
                            border: '1px solid var(--wedo-cyan-bg-20)'}}
                        >
                          <Home className="w-3 h-3" />
                          <span>Base Local</span>
                        </div>
                        <span className="text-xs text-gray-400">
                          Busca apenas na sua base de dados
                        </span>
                      </div>
                    )}
                    
                    {/* Tags de Critérios - Sempre Visíveis (5 critérios como SmartSearchInput) */}
                    <div className="flex flex-wrap items-center gap-1.5 mt-2">
                      {searchTags.map((tag) => {
                        const colors = getTagColors(tag.key, tag.filled)
                        const TagIcon = tag.icon
                        
                        return (
                          <div
                            key={tag.key}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-all"
                            style={{backgroundColor: colors.bg,
                              color: colors.text}}
                            title={tag.value}
                          >
                            <div 
                              className="flex items-center justify-center w-4 h-4 rounded-md"
                              style={{backgroundColor: tag.filled ? `${colors.iconBg}30` : 'transparent'}}
                            >
                              <TagIcon className="w-3 h-3" style={{color: tag.filled ? colors.iconBg : colors.text}} />
                            </div>
                            <span className="font-medium">{tag.label}</span>
                            {tag.filled && tag.value && (
                              <>
                                <span style={{opacity: 0.5}}>·</span>
                                <span className="max-w-20 truncate font-normal" style={{opacity: 0.85}}>{tag.value}</span>
                              </>
                            )}
                          </div>
                        )
                      })}
                      
                      {isParsingEntities && (
                        <div className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-400">
                          <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                          Analisando...
                        </div>
                      )}
                      
                      {/* Botão Assistente de Busca - Consolidado com toggle */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() => setAutocompleteEnabled(!autocompleteEnabled)}
                              className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:opacity-90",
                                autocompleteEnabled 
                                  ? "bg-gray-900 text-white" 
                                  : "bg-gray-100 text-gray-500"
                              )}
                             
                            >
                              <Brain className={`w-3.5 h-3.5 ${autocompleteEnabled ? 'text-wedo-cyan' : 'text-gray-400'}`} />
                              <span className="font-medium text-xs">
                                Assistente de Busca
                              </span>
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="max-w-panel-sm p-3 max-w-panel-sm p-3 border-gray-300 dark:border-gray-600">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Brain className="w-4 h-4 text-wedo-cyan" />
                                  <span className="font-semibold text-sm" style={{color: autocompleteEnabled ? 'var(--status-success)' : 'var(--status-error)'}}>
                                    {autocompleteEnabled ? 'Ativado' : 'Desativado'}
                                  </span>
                                </div>
                                <span className="text-micro px-2 py-0.5 rounded-full" style={{backgroundColor: autocompleteEnabled ? 'var(--status-success-bg)' : 'var(--status-error-bg)',
                                  color: autocompleteEnabled ? 'var(--status-success)' : 'var(--status-error)'}}>
                                  {autocompleteEnabled ? 'ON' : 'OFF'}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium text-sm text-gray-800 dark:text-gray-100">
                                  Assistente de Busca Inteligente
                                </span>
                              </div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Enquanto você descreve o perfil, a LIA analisa e sugere melhorias:
                              </p>
                              <ul className="text-xs space-y-1 text-gray-500 dark:text-gray-400">
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Indica critérios faltantes</span>
                                </li>
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Sugere sinônimos e termos relacionados</span>
                                </li>
                                <li className="flex items-start gap-1.5">
                                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <span>Alerta sobre buscas muito amplas ou restritivas</span>
                                </li>
                              </ul>
                              <p className="text-micro pt-1 border-t text-gray-500 dark:text-gray-400 border-gray-300 dark:border-gray-600">
                                {autocompleteEnabled ? 'Clique para desativar' : 'Clique para ativar'}
                              </p>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      {/* Botão Salvar como Arquétipo */}
                      {canSaveAsArchetype && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                onClick={() => setShowSaveArchetypeModal(true)}
                                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all hover:opacity-90 bg-gray-200/30" style={{ border: '1px solid var(--wedo-cyan-border)' }}
                              >
                                <Target className="w-3 h-3" />
                                <span className="font-medium">Salvar Arquétipo</span>
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none !duration-0">
                              <p className="text-xs font-medium">Salvar busca como arquétipo</p>
                              <p className="text-xs text-gray-300">Reutilize esta busca no futuro</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                    
                    {/* Análise de Qualidade da Busca */}
                    {naturalSearchValue && searchAnalysis && (
                      <div className="space-y-2 pt-2 mt-2 border-t border-gray-300 dark:border-gray-600">
                        {/* Barra de completude */}
                        <div className="flex items-center gap-3">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                                Qualidade da busca
                              </span>
                              <span 
                                className="text-xs font-bold"
                                style={{color: searchAnalysis.completeness_score >= 60 
                                    ? 'var(--status-success)' 
                                    : searchAnalysis.completeness_score >= 40 
                                      ? 'var(--status-warning)' 
                                      : 'var(--status-error)'}}
                              >
                                {searchAnalysis.completeness_score}%
                              </span>
                            </div>
                            <div className="h-1.5 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800">
                              <div 
                                className="h-full rounded-full transition-all duration-500"
                                style={{width: `${searchAnalysis.completeness_score}%`,
                                  backgroundColor: searchAnalysis.completeness_score >= 60 
                                    ? 'var(--status-success)' 
                                    : searchAnalysis.completeness_score >= 40 
                                      ? 'var(--status-warning)' 
                                      : 'var(--status-error)'}}
                              />
                            </div>
                          </div>
                          {searchAnalysis.next_recommended_action && (
                            <div 
                              className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs bg-wedo-cyan/[0.08]"
                            >
                              <TrendingUp className="w-3 h-3" />
                              <span>{searchAnalysis.next_recommended_action}</span>
                            </div>
                          )}
                        </div>
                        
                        {/* Alertas inteligentes */}
                        {searchAnalysis.alerts.length > 0 && (
                          <div className="space-y-1.5">
                            {searchAnalysis.alerts.slice(0, 2).map((alert, index) => (
                              <div 
                                key={index}
                                className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs text-gray-500 dark:text-gray-400"
                                style={{backgroundColor: alert.severity === 'warning'
                                    ? 'var(--status-warning-bg-08)'
                                    : 'var(--wedo-cyan-bg-08)'}}
                              >
                                {alert.severity === 'warning' ? (
                                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
                                ) : (
                                  <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                                )}
                                <div className="flex-1 min-w-0">
                                  <span>{alert.message}</span>
                                  {alert.suggestion && (
                                    <button
                                      onClick={() => {
                                        if (alert.action_value) {
                                          setNaturalSearchValue(naturalSearchValue + ', ' + alert.action_value)
                                        }
                                      }}
                                      className="ml-1 font-medium hover:underline text-gray-700"
                                    >
                                      {alert.suggestion}
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Sugestões (cobrindo: Location, Job Title, Experience, Industry, Skills) */}
                    <div className="mt-3">
                      <p className="text-xs text-gray-800 mb-1.5">Sugestões:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {[
                          'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
                          'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis',
                          'Data Scientist Sênior híbrido, 4+ anos em e-commerce, Python e ML',
                          'Tech Lead em Campinas, 7+ anos em startups, React e liderança de times'
                        ].map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => {
                              setNaturalSearchValue(suggestion)
                              parseEntitiesFromQuery(suggestion)
                            }}
                            className="px-2.5 py-1.5 text-xs rounded-full border border-gray-100 bg-white text-gray-600 hover:border-gray-400 hover:text-gray-800 hover:transition-all text-left"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Similar - Pattern like SmartSearchInput */}
                {activeSearchTab === 'similar' && (
                  <div className="space-y-3">
                    {/* URL inputs - up to 2 URLs */}
                    {similarUrls.map((url, index) => (
                      <div key={index} className="relative">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2">
                          <Linkedin className="w-4 h-4 text-gray-600" />
                        </div>
                        <input
                          type="text"
                          value={url}
                          onChange={(e) => updateSimilarUrl(index, e.target.value)}
                          placeholder={index === 0 ? "Cole a URL do LinkedIn ou ID do candidato..." : "Cole outra URL para combinar perfis..."}
                          className="lia-input w-full pl-10 pr-20 py-2.5 text-sm"
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                          {index > 0 && (
                            <button
                              onClick={() => removeSimilarUrl(index)}
                              className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-status-error/10 transition-colors"
                            >
                              <X className="w-3.5 h-3.5 text-status-error" />
                            </button>
                          )}
                          {index === similarUrls.length - 1 && similarUrls.length < MAX_SIMILAR_URLS && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    onClick={addSimilarUrl}
                                    className="h-8 px-3 rounded-md text-sm font-bold hover:bg-gray-800 hover:text-white transition-colors text-gray-700 bg-gray-100"
                                  >
                                    + URL
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="top" className="text-xs max-w-sidebar-content">
                                  Adicione até 2 perfis para a LIA criar um perfil ideal combinado
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* CV Upload section with separator */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-200" />
                      <span className="text-xs text-gray-600 px-2">ou</span>
                      <div className="flex-1 h-px bg-gray-200" />
                    </div>

                    <div className="relative">
                      <input
                        ref={cvFileInputRef}
                        type="file"
                        accept=".pdf,.doc,.docx"
                        multiple
                        onChange={handleCvUpload}
                        className="hidden"
                      />
                      {similarCvFiles.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {similarCvFiles.map((file, index) => (
                            <div 
                              key={index}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs"
                              style={{backgroundColor: 'var(--gray-100)'}}
                            >
                              <FileText className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                              <span className="max-w-[150px] truncate">{file.name}</span>
                              <button onClick={() => removeCvFile(index)} className="hover:text-status-error">
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                          {similarCvFiles.length < MAX_CV_FILES && (
                            <button
                              onClick={() => cvFileInputRef.current?.click()}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium hover:bg-gray-100 transition-colors border border-gray-200"
                              style={{backgroundColor: 'var(--gray-100)'}}
                            >
                              <Upload className="w-3 h-3" />
                              + CV
                            </button>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => cvFileInputRef.current?.click()}
                          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-100 transition-colors border border-gray-200"
                          style={{backgroundColor: 'var(--gray-100)'}}
                        >
                          <Upload className="w-3.5 h-3.5" />
                          Arraste CVs aqui ou clique para upload (máx. 2)
                        </button>
                      )}
                    </div>

                    {/* Analyze button - Shows when 2+ sources */}
                    {hasMultipleSources() && !showCombinedSuggestions && (
                      <button
                        onClick={analyzeProfiles}
                        disabled={isAnalyzingProfiles}
                        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-medium text-white disabled:opacity-50 bg-gray-900"
                      >
                        {isAnalyzingProfiles ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Analisando perfis...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-3.5 h-3.5" />
                            Analisar e combinar perfis com LIA
                          </>
                        )}
                      </button>
                    )}

                    {/* Combined Suggestions Box */}
                    {showCombinedSuggestions && combinedSuggestions.length > 0 && (
                      <div className="p-3 rounded-md space-y-2 border border-gray-200" style={{backgroundColor: "var(--gray-50)"}}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            <span className="text-xs font-medium text-gray-800">
                              Perfil Ideal sugerido pela LIA
                            </span>
                          </div>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="w-3.5 h-3.5 text-gray-600" />
                              </TooltipTrigger>
                              <TooltipContent side="top" className="text-xs max-w-[280px]">
                                A LIA analisou os perfis e combinou skills, experiências e senioridade em comum. Edite ou remova tags antes de buscar.
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {combinedSuggestions.map((keyword) => (
                            <div
                              key={keyword}
                              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium group border border-gray-200 bg-white"
                            >
                              <span className="text-gray-700">{keyword}</span>
                              <button
                                onClick={() => removeSuggestion(keyword)}
                                className="opacity-50 group-hover:opacity-100 hover:text-status-error transition-opacity"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          Baseado em {similarUrls.filter(u => u.trim()).length + similarCvFiles.length} perfis: skills em comum e pontos fortes combinados.
                        </p>
                      </div>
                    )}

                    {/* Search Button */}
                    <button
                      onClick={() => {
                        const validUrls = similarUrls.filter(u => u.trim())
                        if (validUrls.length > 0 || similarCvFiles.length > 0) {
                          const query = validUrls.join(', ')
                          onCommand(query, 'find_similar')
                        }
                      }}
                      disabled={similarUrls.filter(u => u.trim()).length === 0 && similarCvFiles.length === 0}
                      className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{backgroundColor: (similarUrls.filter(u => u.trim()).length > 0 || similarCvFiles.length > 0) ? "var(--gray-950)" : "var(--gray-200)",
                        color: (similarUrls.filter(u => u.trim()).length > 0 || similarCvFiles.length > 0) ? "var(--white)" : "var(--gray-400)"}}
                    >
                      <Search className="w-4 h-4" />
                      {hasMultipleSources() ? "Buscar com perfil combinado" : "Buscar candidatos similares"}
                    </button>

                    {/* Dica contextual padronizada */}
                    <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          <strong>Dica:</strong> Cole 1 a 2 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, a LIA combina as melhores características e sugere palavras-chave para encontrar candidatos similares.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Job Description */}
                {activeSearchTab === 'job-description' && (
                  <div className="space-y-3">
                    <p className="text-xs text-gray-800 dark:text-gray-200">Cole a descrição da vaga para extrair requisitos automaticamente</p>
                    <textarea
                      value={jobDescriptionText}
                      onChange={(e) => setJobDescriptionText(e.target.value)}
                      placeholder="Cole aqui a descrição completa da vaga..."
                      className="lia-input w-full px-4 py-2.5 text-sm resize-none"
                      rows={3}
                    />
                    <div className="flex justify-between items-center">
                      {/* Dica contextual */}
                      <div className="flex items-start gap-2 flex-1">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs lia-body">
                          <strong>Dica:</strong> Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.
                        </p>
                      </div>
                      <button 
                        className="ml-3 px-3 py-1.5 lia-btn-primary text-xs disabled:opacity-50"
                        onClick={() => jobDescriptionText.trim() && onCommand(jobDescriptionText, 'extract_from_jd')}
                        disabled={!jobDescriptionText.trim()}
                      >
                        <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
                        Extrair Requisitos
                      </button>
                    </div>
                  </div>
                )}

                {/* Aba: Boolean */}
                {activeSearchTab === 'boolean' && (
                  <div className="space-y-3">
                    <p className="text-xs lia-body">Use operadores booleanos para buscas precisas</p>
                    <div className="relative">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2">
                        <Code className="w-4 h-4 text-gray-600" />
                      </div>
                      <input
                        type="text"
                        value={booleanSearchValue}
                        onChange={(e) => setBooleanSearchValue(e.target.value)}
                        placeholder='(Python OR Java) AND "São Paulo" NOT junior'
                        className="lia-input w-full pl-10 pr-[180px] py-2.5 text-sm font-mono"
                      />
                      
                      {/* Ícones de Fonte e Contato dentro do input */}
                      <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                        {/* Fonte de busca: Local / Híbrido / Global */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setSearchSource('local'); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  searchSource === 'local' 
                                    ? 'bg-gray-200' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Home className={`w-3.5 h-3.5 ${searchSource === 'local' ? 'text-gray-700' : 'text-gray-500'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Base Local</p>
                              <p className="text-micro text-gray-400">Gratuito</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {showGlobalSearchOptions && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); handleSourceChange('hybrid'); }}
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'hybrid' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Zap className={`w-3.5 h-3.5 ${searchSource === 'hybrid' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Híbrido (Local + Global)</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {showGlobalSearchOptions && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); handleSourceChange('global'); }}
                                  className={`p-1.5 rounded-md transition-all ${
                                    searchSource === 'global' 
                                      ? 'bg-gray-200' 
                                      : 'hover:bg-gray-100'
                                  }`}
                                >
                                  <Globe className={`w-3.5 h-3.5 ${searchSource === 'global' ? 'text-gray-700' : 'text-gray-500'}`} />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom">
                                <p className="text-xs font-medium">Base Global</p>
                                <p className="text-micro text-gray-400">1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Contato: Email / Telefone */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequireEmails(!requireEmails); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requireEmails 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Mail className={`w-3.5 h-3.5 ${requireEmails ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-micro text-gray-400">{requireEmails ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setRequirePhoneNumbers(!requirePhoneNumbers); }}
                                className={`p-1.5 rounded-md transition-all ${
                                  requirePhoneNumbers 
                                    ? 'bg-wedo-green-light/15 ring-1 ring-wedo-green-light' 
                                    : 'hover:bg-gray-100'
                                }`}
                              >
                                <Phone className={`w-3.5 h-3.5 ${requirePhoneNumbers ? 'text-wedo-green-light' : 'text-gray-400'}`} />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom">
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-micro text-gray-400">{requirePhoneNumbers ? 'Ativo' : '+1 crédito se ativo'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {/* Separador */}
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        
                        {/* Botão de Buscar */}
                        <button 
                          className="w-7 h-7 lia-btn-primary flex items-center justify-center disabled:opacity-50"
                          onClick={() => booleanSearchValue.trim() && onCommand(booleanSearchValue, 'boolean_search')}
                          disabled={!booleanSearchValue.trim()}
                        >
                          <Search className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      <span className="text-xs" style={{color: 'var(--gray-400)'}}>Operadores:</span>
                      {['AND', 'OR', 'NOT', '( )', '" "'].map((op) => (
                        <button
                          key={op}
                          onClick={() => setBooleanSearchValue(prev => prev + ' ' + op + ' ')}
                          className="lia-pill font-mono"
                          style={{padding: '2px 8px'}}
                        >
                          {op}
                        </button>
                      ))}
                    </div>
                    {/* Dica contextual */}
                    <div className="p-2.5 rounded-md" style={{backgroundColor: 'var(--wedo-cyan-bg-06)'}}>
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600" />
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND "São Paulo"
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Aba: Filtros */}
                {activeSearchTab === 'filtros' && (
                  <div className="space-y-3">
                    <p className="text-xs lia-body">Configure filtros avançados para refinar sua busca</p>
                    
                    {/* Resumo de filtros ativos */}
                    {(() => {
                      const activeCount = [
                        advancedFilters.locations?.locations?.length || 0,
                        advancedFilters.job?.titles?.length || 0,
                        advancedFilters.job?.levels?.length || 0,
                        advancedFilters.company?.companyItems?.length || 0,
                        advancedFilters.skills?.skillItems?.length || 0,
                        advancedFilters.education?.degrees?.length || 0,
                        advancedFilters.languages?.languages?.length || 0,
                        advancedFilters.general?.minExperience ? 1 : 0,
                        advancedFilters.general?.maxExperience ? 1 : 0
                      ].reduce((a, b) => a + b, 0)
                      
                      return activeCount > 0 ? (
                        <div className="p-2.5 rounded-md bg-gray-50 border border-gray-100">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                              {activeCount} filtro{activeCount > 1 ? 's' : ''} ativo{activeCount > 1 ? 's' : ''}
                            </span>
                            <button
                              onClick={() => setAdvancedFilters({
                                ppiOptions: {},
                                general: {},
                                locations: {},
                                job: {},
                                company: {},
                                skills: {},
                                education: {},
                                languages: {}
                              })}
                              className="text-xs text-gray-800 dark:text-gray-200 hover:text-status-error"
                            >
                              Limpar
                            </button>
                          </div>
                        </div>
                      ) : null
                    })()}
                    
                    {/* Botão para abrir modal completo */}
                    <button 
                      className="w-full px-4 py-3 bg-white border-2 border-dashed border-gray-100 rounded-md hover:border-gray-300 hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                      onClick={() => setShowAdvancedFiltersModal(true)}
                    >
                      <Filter className="w-4 h-4 text-gray-800" />
                      <span className="text-xs text-gray-800">Abrir Filtros Avançados</span>
                    </button>
                    
                    {/* Botão de aplicar filtros */}
                    <button 
                      className="w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs rounded-md transition-colors flex items-center justify-center gap-2"
                      onClick={() => {
                        onCommand(JSON.stringify(advancedFilters), 'apply_filters')
                      }}
                    >
                      <Search className="w-3.5 h-3.5" />
                      Buscar com Filtros
                    </button>
                  </div>
                )}

                {/* Aba: Arquétipos */}
                {activeSearchTab === 'arquetipos' && (
                  <div className="space-y-4">
                    {/* Seção: Criar Arquétipo com contexto de busca */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Criar Novo Arquétipo</span>
                        {naturalSearchValue && (
                          <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-gray-600 dark:text-gray-400 border-gray-900 dark:border-gray-50">
                            Busca ativa detectada
                          </Badge>
                        )}
                      </div>
                      
                      {/* Pré-preenchimento com contexto de busca */}
                      {naturalSearchValue && (
                        <div className="p-3 rounded-md border border-wedo-cyan/30 bg-wedo-cyan/5">
                          <div className="flex items-start gap-2 mb-2">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan mt-0.5" />
                            <span className="text-xs text-gray-600">Contexto da busca atual:</span>
                          </div>
                          <p className="text-sm text-gray-800 mb-2">{naturalSearchValue}</p>
                          
                          {/* Tags de entidades extraídas */}
                          {Object.keys(parsedEntities).length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-2">
                              {parsedEntities.job_title && (
                                <Badge variant="secondary" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-gray-300 dark:border-gray-600">
                                  {parsedEntities.job_title}
                                </Badge>
                              )}
                              {parsedEntities.location && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  <MapPin className="w-2.5 h-2.5 mr-0.5" />
                                  {parsedEntities.location}
                                </Badge>
                              )}
                              {parsedEntities.seniority && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  {parsedEntities.seniority}
                                </Badge>
                              )}
                              {parsedEntities.industry && (
                                <Badge variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  <Building2 className="w-2.5 h-2.5 mr-0.5" />
                                  {parsedEntities.industry}
                                </Badge>
                              )}
                              {parsedEntities.skills && parsedEntities.skills.map((skill, idx) => (
                                <Badge key={idx} variant="secondary" className="text-micro bg-gray-50 text-gray-700 border-gray-200">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          )}
                          
                          {/* Botão primário: Salvar busca como arquétipo (quando há entidades) */}
                          {hasParsedEntities() ? (
                            <button
                              onClick={createArchetypeFromActiveSearch}
                              disabled={isCreatingFromSearch}
                              className="mt-3 w-full px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs rounded-md transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isCreatingFromSearch ? (
                                <>
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  Salvando arquétipo...
                                </>
                              ) : (
                                <>
                                  <Target className="w-3.5 h-3.5" />
                                  Salvar Busca como Arquétipo
                                </>
                              )}
                            </button>
                          ) : (
                            <button
                              onClick={() => {
                                setNewArchetypeDescription(naturalSearchValue)
                              }}
                              className="mt-3 w-full px-3 py-1.5 bg-gray-100 text-gray-800 dark:text-gray-200 text-xs rounded-md hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5"
                            >
                              <Plus className="w-3 h-3" />
                              Usar como base para novo arquétipo
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* Divisor quando há busca ativa */}
                      {naturalSearchValue && hasParsedEntities() && (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-px bg-gray-200" />
                          <span className="text-micro text-gray-400">ou crie do zero com LIA</span>
                          <div className="flex-1 h-px bg-gray-200" />
                        </div>
                      )}
                      
                      {/* Campo de descrição para criar arquétipo (opção secundária) */}
                      <div className="relative">
                        <textarea
                          value={newArchetypeDescription}
                          onChange={(e) => setNewArchetypeDescription(e.target.value)}
                          placeholder="Descreva o perfil ideal: cargo, habilidades, experiência..."
                          className="lia-input w-full px-3 py-2.5 text-sm resize-none"
                          rows={2}
                        />
                      </div>
                      
                      <button
                        onClick={() => createArchetypeFromDescription(newArchetypeDescription)}
                        disabled={isCreatingArchetype || !newArchetypeDescription.trim()}
                        className="w-full px-3 py-2 bg-gray-900 text-white text-xs rounded-md hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isCreatingArchetype ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Criando arquétipo...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-3.5 h-3.5" />
                            Criar Arquétipo com LIA
                          </>
                        )}
                      </button>
                    </div>
                    
                    {/* Divisor */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-200" />
                      <span className="text-xs text-gray-500">ou selecione um existente</span>
                      <div className="flex-1 h-px bg-gray-200" />
                    </div>
                    
                    {/* Lista de Arquétipos Existentes */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Meus Arquétipos</span>
                        <Badge variant="outline" className="text-micro">
                          {filteredArchetypes.length} {filteredArchetypes.length === 1 ? 'arquétipo' : 'arquétipos'}
                        </Badge>
                      </div>
                      
                      {/* Campo de busca */}
                      {archetypes.length > 3 && (
                        <div className="relative">
                          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                          <input
                            type="text"
                            value={archetypeSearchFilter}
                            onChange={(e) => setArchetypeSearchFilter(e.target.value)}
                            placeholder="Buscar arquétipos..."
                            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                          />
                        </div>
                      )}
                      
                      {/* Cards de Arquétipos */}
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {filteredArchetypes.length === 0 ? (
                          <div className="text-center py-6 text-gray-500">
                            <Target className="w-8 h-8 mx-auto mb-2 opacity-30" />
                            <p className="text-xs">Nenhum arquétipo encontrado</p>
                            <p className="text-micro text-gray-400 mt-1">Crie um novo acima para começar</p>
                          </div>
                        ) : (
                          filteredArchetypes.map((arch) => (
                            <div
                              key={arch.id}
                              className="group relative p-3 rounded-md border border-gray-100 bg-white hover:border-gray-400 hover:transition-all cursor-pointer"
                              onClick={() => {
                                setSelectedArquetipo(arch.id)
                                const query = (arch as any).query || arch.criteria?.query || arch.description || ""
                                if (query) {
                                  onCommand(query, 'archetype_search')
                                }
                              }}
                            >
                              {/* Edit/Delete buttons */}
                              <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={(e) => openEditArchetype(arch, e)}
                                  className="p-1 rounded-md hover:bg-gray-100 transition-colors"
                                  title="Editar arquétipo"
                                >
                                  <Pencil className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                                </button>
                                <button
                                  onClick={(e) => openDeleteArchetypeDialog(arch, e)}
                                  disabled={isDeletingArchetype === arch.id}
                                  className="p-1 rounded-md hover:bg-status-error/10 transition-colors"
                                  title="Excluir arquétipo"
                                >
                                  {isDeletingArchetype === arch.id ? (
                                    <Loader2 className="w-3.5 h-3.5 text-gray-400 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-status-error" />
                                  )}
                                </button>
                              </div>
                              
                              <div className="flex items-start gap-2.5 pr-16">
                                <span className="text-lg flex-shrink-0">
                                  {(arch as any).emoji || "🎯"}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-gray-800 truncate">
                                    {arch.name}
                                  </div>
                                  {arch.description && (
                                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                                      {arch.description}
                                    </p>
                                  )}
                                  {arch.department && (
                                    <Badge variant="outline" className="mt-1.5 text-micro">
                                      {arch.department}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Dica contextual */}
              <div className="flex items-start gap-2 p-2 bg-gray-50 rounded-md mb-3 border border-gray-100">
                <Lightbulb className="w-3.5 h-3.5 text-gray-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-800 dark:text-gray-200">
                  {activeSearchTab === 'natural' && 'Dica: Para melhores resultados, seja específico sobre skills, senioridade e localização.'}
                  {activeSearchTab === 'similar' && 'Dica: Cole o link do LinkedIn de um candidato que você considera ideal.'}
                  {activeSearchTab === 'job-description' && 'Dica: Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.'}
                  {activeSearchTab === 'boolean' && 'Dica: Use aspas para termos exatos e parênteses para agrupar condições.'}
                  {activeSearchTab === 'filtros' && 'Dica: Combine filtros para refinar sua busca de forma precisa.'}
                  {activeSearchTab === 'arquetipos' && 'Dica: Use arquétipos para salvar perfis ideais e reutilizar em buscas futuras.'}
                </p>
              </div>
            </div>

            {/* 💡 SUGESTÕES CONTEXTUAIS EXPANDIDAS - Seção Principal */}
            <div className="px-4 pb-0">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <LIAIcon size="sm" />
                  <span className="text-sm font-medium text-gray-950 dark:text-gray-50">💡 Sugestões Inteligentes</span>
                  <Badge variant="outline" className="text-xs">
                    {suggestions.length} disponíveis
                  </Badge>
                </div>

                {commandHistory.length > 0 && (
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    className="text-xs text-gray-600 hover:text-gray-700 flex items-center gap-1 transition-colors"
                  >
                    📜 Histórico ({commandHistory.length})
                  </button>
                )}
              </div>

              {/* Histórico de Comandos */}
              {showHistory && commandHistory.length > 0 && (
                <div className="mb-4 p-3 bg-gray-50 rounded-md border">
                  <h4 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Comandos Recentes</h4>
                  <div className="space-y-1">
                    {commandHistory.map((command, index) => (
                      <button
                        key={index}
                        onClick={() => handleHistoryCommand(command)}
                        disabled={isProcessing}
                        className={`w-full text-left text-xs p-2 rounded-md hover:bg-white transition-colors ${
                          isProcessing ? 'opacity-50' : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        📝 {command}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Grid de Sugestões Inteligentes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isProcessing}
                    className={`flex items-start gap-3 p-3 text-left rounded-md border border-gray-100 bg-white transition-all group ${
                      isProcessing
                        ? 'opacity-50 cursor-not-allowed'
                        : 'hover:border-gray-400 hover:'
                    }`}
                  >
                    <span className="text-lg flex-shrink-0">{suggestion.icon}</span>
                    <div className="flex-1">
                      <div className="text-base-ui font-semibold text-gray-800 group-hover:text-gray-700">
                        {suggestion.label}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {suggestion.description}
                      </div>
                      {suggestion.category && (
                        <Badge className="mt-2 text-micro bg-gray-100 text-gray-800 dark:text-gray-200 border-0">
                          {suggestion.category}
                        </Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 💬 ENTRADA DE TEXTO - Seção Inferior */}
            <div className="px-4 pb-4">
              {/* Voice Listening Indicator */}
              {isListening && (
                <div className="flex items-center gap-2 text-sm text-status-error bg-status-error/10 p-2 rounded-md mb-3">
                  <div className="w-2 h-2 bg-status-error rounded-full animate-pulse"></div>
                  <span>🎙️ Ouvindo... Fale seu comando</span>
                </div>
              )}

              {/* Processing Indicator */}
              {isProcessing && (
                <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 p-2 rounded-md mb-3 border border-gray-100">
                  <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full animate-pulse"></div>
                  <span>🧠 LIA processando: "{lastCommand}"</span>
                </div>
              )}

              <div className="text-xs text-gray-800 dark:text-gray-200 text-center pt-2 space-y-1">
                <div>💡 LIA aprende com seus padrões para sugerir ações mais precisas</div>
                <div className="flex justify-center gap-4">
                  <span>⌨️ Esc para fechar</span>
                  <span>Ctrl+K para focar</span>
                  {commandHistory.length > 0 && <span>Ctrl+H para histórico</span>}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast de Sugestão de Template */}
      <TemplateSuggestionToast
        suggestion={suggestionQueue.currentSuggestion}
        onCreateTemplate={(suggestion) => {
          // Abrir página de templates com dados pre-populados
          const templateData = {
            name: `Template: ${suggestion.command.substring(0, 30)}...`,
            command: suggestion.command,
            complexity: suggestion.complexity,
            estimatedTime: suggestion.estimatedTime
          }
          sessionStorage.setItem('lia-create-template', JSON.stringify(templateData))
          window.location.href = '/?page=templates'
          suggestionQueue.clearCurrentSuggestion()
        }}
        onDismiss={(suggestionId) => {
          templateSuggestions.dismissSuggestion(suggestionId)
          suggestionQueue.clearCurrentSuggestion()
        }}
        onNotAskAgain={() => {
          templateSuggestions.updateSettings({ enabled: false })
          suggestionQueue.clearCurrentSuggestion()
        }}
      />

      {/* Modal de Filtros Avançados */}
      <AdvancedFiltersModal
        isOpen={showAdvancedFiltersModal}
        onClose={() => setShowAdvancedFiltersModal(false)}
        initialFilters={advancedFilters}
        onApply={(filters) => {
          setAdvancedFilters(filters)
          setShowAdvancedFiltersModal(false)
          onCommand(JSON.stringify(filters), 'apply_filters')
        }}
      />

      {/* Modal de Edição de Arquétipo */}
      {editingArchetype && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={closeEditArchetype}
        >
          <div 
            className="bg-white rounded-md p-5 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
            className="border border-gray-200"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{color: "var(--gray-950)"}}>
                Editar Arquétipo
              </h3>
              <button
                onClick={closeEditArchetype}
                className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4" style={{color: "var(--gray-400)"}} />
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="w-16">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Emoji</label>
                  <input
                    type="text"
                    value={editArchetypeEmoji}
                    onChange={(e) => setEditArchetypeEmoji(e.target.value)}
                    maxLength={4}
                    className="w-full rounded-md px-2 py-2 text-center text-lg focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Nome</label>
                  <input
                    type="text"
                    value={editArchetypeName}
                    onChange={(e) => setEditArchetypeName(e.target.value)}
                    placeholder="Nome do arquétipo"
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Query de Busca</label>
                <textarea
                  value={editArchetypeQuery}
                  onChange={(e) => setEditArchetypeQuery(e.target.value)}
                  placeholder="Ex: Desenvolvedor Python Sênior São Paulo"
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-gray-200"
                />
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Descrição (opcional)</label>
                <textarea
                  value={editArchetypeDescription}
                  onChange={(e) => setEditArchetypeDescription(e.target.value)}
                  placeholder="Breve descrição do perfil ideal..."
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-gray-200"
                />
              </div>

              {/* Tags Section */}
              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Tags</label>
                
                {/* Existing tags as removable chips */}
                {editArchetypeTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {editArchetypeTags.map((tag, index) => (
                      <Badge 
                        key={index} 
                        variant="secondary" 
                        className="text-xs bg-gray-100 text-gray-800 dark:text-gray-200 pr-1 flex items-center gap-1"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => setEditArchetypeTags(prev => prev.filter((_, i) => i !== index))}
                          className="ml-0.5 rounded-full hover:bg-gray-200 p-0.5 transition-colors"
                        >
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
                
                {/* Input to add new tags */}
                <div className="relative">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newTagInput.trim()) {
                        e.preventDefault()
                        if (!editArchetypeTags.includes(newTagInput.trim())) {
                          setEditArchetypeTags(prev => [...prev, newTagInput.trim()])
                        }
                        setNewTagInput("")
                      }
                    }}
                    placeholder="Digite e pressione Enter para adicionar..."
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-gray-200"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-micro text-gray-400">
                    Enter ↵
                  </span>
                </div>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <Button
                onClick={closeEditArchetype}
                variant="outline"
                className="flex-1"
                style={{color: "var(--gray-400)"}}
              >
                Cancelar
              </Button>
              <Button
                onClick={saveArchetype}
                disabled={isSavingArchetype || !editArchetypeName}
                className="flex-1"
                style={{backgroundColor: editArchetypeName ? "var(--gray-950)" : "var(--gray-200)",
                  color: editArchetypeName ? "white" : "var(--gray-400)"}}
              >
                {isSavingArchetype ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-1.5" />
                    Salvar
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação para Exclusão de Arquétipo */}
      <AlertDialog open={showDeleteArchetypeDialog} onOpenChange={setShowDeleteArchetypeDialog}>
        <AlertDialogContent 
          className="sm:max-w-[320px] w-[85vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-4 rounded-md border" 
          style={{backgroundColor: 'var(--gray-50)'}}
        >
          <AlertDialogHeader>
            <AlertDialogTitle className="text-base font-semibold text-gray-800 flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-status-error" />
              Excluir Arquétipo
            </AlertDialogTitle>
            <AlertDialogDescription className="text-sm text-gray-600">
              Tem certeza que deseja excluir o arquétipo{' '}
              <span className="font-medium text-gray-800">"{archetypeToDelete?.name}"</span>?
              <br />
              <span className="text-xs text-gray-500 mt-1 block">
                Esta ação não pode ser desfeita.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 mt-4">
            <AlertDialogCancel 
              onClick={() => {
                setShowDeleteArchetypeDialog(false)
                setArchetypeToDelete(null)
              }}
              className="flex-1 h-9 text-sm px-3 rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteArchetype}
              className="flex-1 h-9 text-sm px-3 rounded-md text-white flex items-center justify-center gap-1.5"
              style={{backgroundColor: 'var(--status-error)'}}
            >
              <Trash2 className="w-3.5 h-3.5" />
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent 
          className="sm:max-w-sidebar-content w-[80vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-3 rounded-md border" 
          style={{backgroundColor: 'var(--gray-100)'}}
        >
          <div className="space-y-2" style={{fontSize: '10px', lineHeight: '1.4'}}>
            <div className="flex items-center gap-1.5">
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-3 h-3 text-gray-600" />
              ) : (
                <Globe className="w-3 h-3 text-status-warning" />
              )}
              <h3 className="font-semibold text-xs text-gray-800">
                {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
              </h3>
            </div>
            
            <p className="text-micro text-gray-500">
              {pendingSourceChange === 'hybrid' 
                ? 'Combina base local + global (800M+ perfis).'
                : 'Acessa 800M+ perfis profissionais.'}
            </p>
            
            <div className="bg-white rounded-md p-2 space-y-1 border border-gray-100">
              {pendingSourceChange === 'hybrid' && (
                <div className="flex justify-between text-micro">
                  <span className="text-gray-600">Local:</span>
                  <span className="font-medium text-wedo-green-light">Grátis</span>
                </div>
              )}
              <div className="flex justify-between text-micro">
                <span className="text-gray-600">Global:</span>
                <span className="font-medium text-status-warning">1 cr/candidato</span>
              </div>
              <div className="flex justify-between text-micro pt-1 border-t border-gray-100">
                <span className="font-medium text-gray-800 dark:text-gray-200">Total estimado:</span>
                <span className="font-semibold text-status-warning">1 cr/candidato</span>
              </div>
            </div>
            
            <div className="flex gap-1.5 pt-1">
              <button
                onClick={() => {
                  setShowSourceChangeModal(false)
                  setPendingSourceChange(null)
                }}
                className="flex-1 h-6 text-micro px-2 rounded-full bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSourceChange}
                className="flex-1 h-6 text-micro px-2 rounded-full text-white flex items-center justify-center gap-1 bg-gray-900"
              >
                {pendingSourceChange === 'hybrid' ? (
                  <>
                    <Zap className="w-2.5 h-2.5" />
                    Ativar
                  </>
                ) : (
                  <>
                    <Globe className="w-2.5 h-2.5" />
                    Ativar
                  </>
                )}
              </button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Save Archetype Modal */}
      <SaveArchetypeModal
        open={showSaveArchetypeModal}
        onClose={() => setShowSaveArchetypeModal(false)}
        searchSpec={buildSearchSpecFromEntities}
        query={naturalSearchValue}
        onSuccess={handleArchetypeSaved}
      />
    </div>
  )
}
