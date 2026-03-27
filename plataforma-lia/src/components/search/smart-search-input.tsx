"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { 
  Check, MapPin, Briefcase, Clock, Building2, Code, X, Search, 
  FileText, Binary, Users, Upload, Filter, AlertCircle,
  Globe, GraduationCap, DollarSign, Star, Target, ChevronRight,
  User, Award, Loader2, GripVertical, Lightbulb, Linkedin, Info,
  AlertTriangle, CheckCircle2, HelpCircle, Wand2, TrendingUp, Plus, Brain,
  Pencil, Trash2, MoreHorizontal, Home, Zap, Mail, Phone, Table2,
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

export interface ParsedEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

export type SearchSource = "local" | "global" | "hybrid"

export interface SmartSearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => void
  onCancel: () => void
  onOpenFilters?: () => void
  onGoToResults?: () => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  activeFiltersCount?: number
  searchSource?: SearchSource
  onSearchSourceChange?: (source: SearchSource) => void
  requireEmails?: boolean
  onRequireEmailsChange?: (value: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (value: boolean) => void
}

export type SearchMode = "natural" | "similar" | "jd" | "boolean" | "archetypes"

export interface ArchetypeCandidate {
  id: string
  name: string
  current_title?: string
  years_experience?: number
  skills?: string[]
  hired_at?: string
}

export interface ArchetypeVacancy {
  id: string
  title: string
  department?: string
  closed_at?: string
  hired_candidate?: ArchetypeCandidate
}

export interface SearchMetadata {
  mode: SearchMode
  booleanQuery?: string
  jobDescription?: string
  similarProfileUrl?: string
  similarProfileUrls?: string[]
  combinedProfile?: CombinedProfileSuggestion
  archetypeVacancyId?: string
  archetypeCandidateId?: string
  archetypeProfile?: ArchetypeCandidate
  filters?: Record<string, any>
  searchText?: string
}

export interface CombinedProfileSuggestion {
  keywords: string[]
  title?: string
  seniority?: string
  skills_technical?: string[]
  skills_soft?: string[]
  industries?: string[]
  location?: string
  summary?: string
}

interface SearchTag {
  key: keyof ParsedEntities
  label: string
  icon: React.ElementType
  filled: boolean
  value?: string
}

interface SearchAlert {
  type: string
  severity: "info" | "warning" | "error"
  message: string
  suggestion?: string
  action_label?: string
  action_value?: string
}

interface SearchAnalysis {
  completeness_score: number
  filled_criteria: string[]
  missing_criteria: string[]
  alerts: SearchAlert[]
  enrichment_suggestions: Record<string, string[]>
  next_recommended_action?: string
}

interface AutocompleteItem {
  text: string
  category: string
  icon: string
  description?: string
  insert_text: string
}

interface AutocompleteResponse {
  items: AutocompleteItem[]
  context_hint?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""

// Sugestões cobrindo os 5 critérios: Location, Job Title, Experience, Industry, Skills
const SEARCH_SUGGESTIONS = [
  'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
  'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis'
]

export function SmartSearchInput({
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
}: SmartSearchInputProps) {
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  
  // Only show global/hybrid options after settings are loaded AND global search is enabled
  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled
  const [mode, setMode] = useState<SearchMode>("natural")
  const [entities, setEntities] = useState<ParsedEntities>({})
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [booleanError, setBooleanError] = useState<string | null>(null)
  const [jdContent, setJdContent] = useState("")
  const [similarUrl, setSimilarUrl] = useState("")
  const [similarUrls, setSimilarUrls] = useState<string[]>([""])
  const [similarCvFiles, setSimilarCvFiles] = useState<File[]>([])
  const [combinedSuggestions, setCombinedSuggestions] = useState<string[]>([])
  const [isAnalyzingProfiles, setIsAnalyzingProfiles] = useState(false)
  const [showCombinedSuggestions, setShowCombinedSuggestions] = useState(false)
  const [archetypeVacancies, setArchetypeVacancies] = useState<ArchetypeVacancy[]>([])
  const [selectedArchetype, setSelectedArchetype] = useState<ArchetypeVacancy | null>(null)
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(false)
  const [archetypeSearch, setArchetypeSearch] = useState("")
  const [archetypeTab, setArchetypeTab] = useState<"list" | "create">("list")
  const [archetypeCreateMode, setArchetypeCreateMode] = useState<"job" | "description">("job")
  const [closedJobSuggestions, setClosedJobSuggestions] = useState<any[]>([])
  const [isLoadingClosedJobs, setIsLoadingClosedJobs] = useState(false)
  const [jobSearchQuery, setJobSearchQuery] = useState("")
  const [jobSearchResults, setJobSearchResults] = useState<Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: any[] | null
  }>>([])
  const [isSearchingJobs, setIsSearchingJobs] = useState(false)
  const [archetypeDescription, setArchetypeDescription] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [editingArchetype, setEditingArchetype] = useState<any | null>(null)
  const [editArchetypeName, setEditArchetypeName] = useState("")
  const [editArchetypeQuery, setEditArchetypeQuery] = useState("")
  const [editArchetypeDescription, setEditArchetypeDescription] = useState("")
  const [editArchetypeEmoji, setEditArchetypeEmoji] = useState("")
  const [editArchetypeTags, setEditArchetypeTags] = useState<string[]>([])
  const [editArchetypeSkills, setEditArchetypeSkills] = useState<string[]>([])
  const [editArchetypeSeniority, setEditArchetypeSeniority] = useState("")
  const [editArchetypeIndustry, setEditArchetypeIndustry] = useState("")
  const [editArchetypeExperienceMin, setEditArchetypeExperienceMin] = useState<number | null>(null)
  const [editArchetypeLocation, setEditArchetypeLocation] = useState("")
  const [editArchetypeWorkModel, setEditArchetypeWorkModel] = useState("")
  const [editArchetypeLanguages, setEditArchetypeLanguages] = useState<string[]>([])
  const [editArchetypeEmploymentType, setEditArchetypeEmploymentType] = useState("")
  const [newLanguageInput, setNewLanguageInput] = useState("")
  const [newTagInput, setNewTagInput] = useState("")
  const [newSkillInput, setNewSkillInput] = useState("")
  const [isSavingArchetype, setIsSavingArchetype] = useState(false)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState<string | null>(null)
  const [showArchetypeActions, setShowArchetypeActions] = useState<string | null>(null)
  const [expandedArchetypeId, setExpandedArchetypeId] = useState<string | null>(null)
  const [skillSuggestions, setSkillSuggestions] = useState<string[]>([])
  const [isLoadingSkillSuggestions, setIsLoadingSkillSuggestions] = useState(false)
  const [isFindingSimilarSkills, setIsFindingSimilarSkills] = useState(false)
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([])
  const [isLoadingTagSuggestions, setIsLoadingTagSuggestions] = useState(false)
  const [isFindingSimilarTags, setIsFindingSimilarTags] = useState(false)
  const [aiSuggestedSkills, setAiSuggestedSkills] = useState<string[]>([])
  const [selectedAiSkills, setSelectedAiSkills] = useState<string[]>([])
  const [showSkillSuggestions, setShowSkillSuggestions] = useState(false)
  const [aiSuggestedTags, setAiSuggestedTags] = useState<string[]>([])
  const [selectedAiTags, setSelectedAiTags] = useState<string[]>([])
  const [showTagSuggestions, setShowTagSuggestions] = useState(false)
  const [industrySearchQuery, setIndustrySearchQuery] = useState("")
  const [isIndustryDropdownOpen, setIsIndustryDropdownOpen] = useState(false)
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
  const [similarSearchPrompt, setSimilarSearchPrompt] = useState("")
  const [jdSearchPrompt, setJdSearchPrompt] = useState("")
  const [booleanFinalPrompt, setBooleanFinalPrompt] = useState("")
  const [archetypeSearchPrompt, setArchetypeSearchPrompt] = useState("")
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

  const MAX_SIMILAR_URLS = 3
  const MAX_CV_FILES = 2

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
    if (!value || filledCount === 0) {
      return null
    }

    let segments: { text: string; type: 'normal' | 'job_title' | 'location' | 'skills' | 'experience' | 'industry' }[] = []
    let remainingText = value
    const usedRanges: { start: number; end: number }[] = []

    const entityMatches: { value: string; type: 'job_title' | 'location' | 'skills' | 'experience' | 'industry'; start: number; end: number }[] = []

    if (entities.job_title) {
      const idx = value.toLowerCase().indexOf(entities.job_title.toLowerCase())
      if (idx !== -1) {
        entityMatches.push({ value: entities.job_title, type: 'job_title', start: idx, end: idx + entities.job_title.length })
      }
    }
    if (entities.location) {
      const idx = value.toLowerCase().indexOf(entities.location.toLowerCase())
      if (idx !== -1) {
        entityMatches.push({ value: entities.location, type: 'location', start: idx, end: idx + entities.location.length })
      }
    }
    if (entities.years_experience) {
      const idx = value.toLowerCase().indexOf(entities.years_experience.toLowerCase())
      if (idx !== -1) {
        entityMatches.push({ value: entities.years_experience, type: 'experience', start: idx, end: idx + entities.years_experience.length })
      }
    }
    if (entities.industry) {
      const idx = value.toLowerCase().indexOf(entities.industry.toLowerCase())
      if (idx !== -1) {
        entityMatches.push({ value: entities.industry, type: 'industry', start: idx, end: idx + entities.industry.length })
      }
    }
    if (entities.skills && entities.skills.length > 0) {
      entities.skills.forEach(skill => {
        const idx = value.toLowerCase().indexOf(skill.toLowerCase())
        if (idx !== -1) {
          entityMatches.push({ value: skill, type: 'skills', start: idx, end: idx + skill.length })
        }
      })
    }

    entityMatches.sort((a, b) => a.start - b.start)

    let lastEnd = 0
    entityMatches.forEach(match => {
      const overlaps = usedRanges.some(r => 
        (match.start >= r.start && match.start < r.end) || 
        (match.end > r.start && match.end <= r.end)
      )
      if (!overlaps) {
        if (match.start > lastEnd) {
          segments.push({ text: value.substring(lastEnd, match.start), type: 'normal' })
        }
        segments.push({ text: value.substring(match.start, match.end), type: match.type })
        usedRanges.push({ start: match.start, end: match.end })
        lastEnd = match.end
      }
    })

    if (lastEnd < value.length) {
      segments.push({ text: value.substring(lastEnd), type: 'normal' })
    }

    if (segments.length === 0) {
      segments = [{ text: value, type: 'normal' }]
    }

    const getHighlightStyle = (type: string) => {
      switch (type) {
        case 'job_title':
          return { borderRadius: '3px', padding: '0 2px' }
        case 'location':
          return { backgroundColor: '#F3EAFF', color: '#7C3AED', borderRadius: '3px', padding: '0 2px' }
        case 'skills':
          return { backgroundColor: '#E5F5EB', color: '#2D6A4F', borderRadius: '3px', padding: '0 2px' }
        case 'experience':
          return { backgroundColor: '#FDF4E8', color: '#B8860B', borderRadius: '3px', padding: '0 2px' }
        case 'industry':
          return { backgroundColor: '#E8F1FD', color: '#2563EB', borderRadius: '3px', padding: '0 2px' }
        default:
          return {}
      }
    }

    return (
      <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {segments.map((seg, idx) => (
          <span 
            key={idx} 
            style={seg.type !== 'normal' ? getHighlightStyle(seg.type) : {}}
            className={seg.type !== 'normal' ? 'font-medium' : ''}
          >
            {seg.text}
          </span>
        ))}
      </span>
    )
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
      console.error("Error parsing query:", error)
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
      console.error("Error analyzing search:", error)
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
      console.error("Error fetching prompt enhancement:", error)
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
        console.error("Error fetching autocomplete:", error)
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

  const loadArchetypes = useCallback(async () => {
    setIsLoadingArchetypes(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`)
      if (response.ok) {
        const data = await response.json()
        setArchetypeVacancies(data.archetypes || [])
      }
    } catch (error) {
      console.error("Error loading archetypes:", error)
    } finally {
      setIsLoadingArchetypes(false)
    }
  }, [])

  const loadClosedJobSuggestions = useCallback(async () => {
    setIsLoadingClosedJobs(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/suggestions/closed-jobs?limit=5`)
      if (response.ok) {
        const data = await response.json()
        setClosedJobSuggestions(data.suggestions || [])
      }
    } catch (error) {
      console.error("Error loading closed job suggestions:", error)
    } finally {
      setIsLoadingClosedJobs(false)
    }
  }, [])

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
        const filtered = jobs.filter((job: any) => 
          job.title?.toLowerCase().includes(queryLower) ||
          job.id?.toLowerCase().includes(queryLower) ||
          job.department?.toLowerCase().includes(queryLower)
        )
        setJobSearchResults(filtered.slice(0, 10))
      }
    } catch (error) {
      console.error("Error searching jobs:", error)
      setJobSearchResults([])
    } finally {
      setIsSearchingJobs(false)
    }
  }, [])

  const openArchetypeFromJob = useCallback((job: any) => {
    const skills: string[] = []
    if (job.technical_requirements && Array.isArray(job.technical_requirements)) {
      job.technical_requirements.forEach((req: any) => {
        if (req.skill) skills.push(req.skill)
        else if (typeof req === 'string') skills.push(req)
      })
    }

    const seniorityMap: Record<string, string> = {
      "Júnior": "junior",
      "Junior": "junior",
      "Pleno": "pleno",
      "Sênior": "senior",
      "Senior": "senior",
      "Especialista": "senior",
      "Lead": "lead",
      "Tech Lead": "lead",
      "Staff": "staff",
      "Principal": "principal",
      "Gerente": "manager",
      "Diretor": "director"
    }

    setEditingArchetype({ id: null, is_default: false, fromJob: true, jobId: job.id })
    setEditArchetypeName(job.title || "")
    setEditArchetypeQuery(`${job.title || ""} ${job.department ? `${job.department}` : ""}`.trim())
    setEditArchetypeDescription(job.description?.slice(0, 300) || "")
    setEditArchetypeEmoji("🎯")
    setEditArchetypeTags([job.department, job.status].filter(Boolean))
    setEditArchetypeSkills(skills.slice(0, 10))
    setEditArchetypeSeniority(seniorityMap[job.seniority_level] || "")
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
  }, [])

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
      console.error("Error creating archetype from job:", error)
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [loadArchetypes])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    setIsCreatingArchetype(true)
    try {
      // Try to extract info using AI
      const response = await fetch('/api/ai/extract-archetype-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      })
      
      let extractedData: any = {}
      if (response.ok) {
        extractedData = await response.json()
      }
      
      // Open modal with extracted or default data
      setEditingArchetype({ id: null, is_default: false, fromDescription: true })
      setEditArchetypeName(extractedData.name || "Novo Arquétipo")
      setEditArchetypeQuery(extractedData.query || description)
      setEditArchetypeDescription(description)
      setEditArchetypeEmoji(extractedData.emoji || "🎯")
      setEditArchetypeTags(extractedData.tags || [])
      setEditArchetypeSkills(extractedData.skills || [])
      setEditArchetypeSeniority(extractedData.seniority || "")
      setEditArchetypeIndustry(extractedData.industry || "")
      setEditArchetypeExperienceMin(extractedData.experience_years_min || null)
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
      console.error("Error extracting archetype info:", error)
      // Fallback: open modal with description as query
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
  }, [])

  const openEditArchetype = useCallback((arch: any, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || arch.title || "")
    setEditArchetypeQuery(arch.query || "")
    setEditArchetypeDescription(arch.description || "")
    setEditArchetypeEmoji(arch.emoji || "🎯")
    setEditArchetypeTags(arch.tags || [])
    setEditArchetypeSkills(arch.filters?.skills || [])
    setEditArchetypeSeniority(arch.seniority || arch.filters?.seniority || "")
    setEditArchetypeIndustry(arch.industry || "")
    setEditArchetypeExperienceMin(arch.filters?.experience_years_min || null)
    setEditArchetypeLocation(arch.filters?.location || "")
    setEditArchetypeWorkModel(arch.filters?.work_model || "")
    setEditArchetypeLanguages(arch.filters?.languages || [])
    setEditArchetypeEmploymentType(arch.filters?.employment_type || "")
    setNewTagInput("")
    setNewSkillInput("")
    setNewLanguageInput("")
    setShowArchetypeActions(null)
  }, [])

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
  }, [])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return
    
    setIsSavingArchetype(true)
    try {
      const filters: Record<string, any> = {}
      if (editArchetypeSkills.length > 0) filters.skills = editArchetypeSkills
      if (editArchetypeSeniority) filters.seniority = editArchetypeSeniority
      if (editArchetypeExperienceMin !== null && editArchetypeExperienceMin > 0) {
        filters.experience_years_min = editArchetypeExperienceMin
      }
      if (editArchetypeLocation) {
        filters.location = editArchetypeLocation
      }
      if (editArchetypeWorkModel) {
        filters.work_model = editArchetypeWorkModel
      }
      if (editArchetypeLanguages.length > 0) {
        filters.languages = editArchetypeLanguages
      }
      if (editArchetypeEmploymentType) {
        filters.employment_type = editArchetypeEmploymentType
      }

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
        console.error("Error saving archetype:", error)
        alert(error.detail || "Erro ao salvar arquétipo")
      }
    } catch (error) {
      console.error("Error saving archetype:", error)
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills, editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin, editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages, editArchetypeEmploymentType, loadArchetypes, closeEditArchetype])

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
        console.error("Error deleting archetype:", error)
        alert(error.detail || "Erro ao excluir arquétipo")
      }
    } catch (error) {
      console.error("Error deleting archetype:", error)
    } finally {
      setIsDeletingArchetype(null)
      setShowArchetypeActions(null)
    }
  }, [loadArchetypes, selectedArchetype])

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

  const addSuggestion = useCallback((keyword: string) => {
    if (!combinedSuggestions.includes(keyword)) {
      setCombinedSuggestions(prev => [...prev, keyword])
    }
  }, [combinedSuggestions])

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
      console.error("Error analyzing profiles:", error)
      const mockKeywords = ["Sênior", "Python", "AWS", "Data Engineer", "Fintech", "SQL", "Spark"]
      setCombinedSuggestions(mockKeywords)
      setShowCombinedSuggestions(true)
    } finally {
      setIsAnalyzingProfiles(false)
    }
  }, [similarUrls, similarCvFiles])

  const hasMultipleSources = useCallback(() => {
    const validUrls = similarUrls.filter(url => url.trim().length > 0)
    return validUrls.length + similarCvFiles.length >= 2
  }, [similarUrls, similarCvFiles])

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

  const buildArchetypePrompt = useCallback((arch: any): string => {
    const parts: string[] = []
    
    if (arch.query) {
      parts.push(arch.query)
    }
    
    if (arch.filters?.skills && arch.filters.skills.length > 0) {
      parts.push(`Skills: ${arch.filters.skills.join(", ")}`)
    } else if (arch.tags && arch.tags.length > 0) {
      parts.push(`Tags: ${arch.tags.join(", ")}`)
    }
    
    if (arch.seniority) {
      const seniorityMap: Record<string, string> = {
        junior: "Júnior",
        pleno: "Pleno", 
        senior: "Sênior",
        lead: "Lead/Tech Lead",
        staff: "Staff",
        principal: "Principal",
        manager: "Gerente",
        director: "Diretor",
        executive: "Executivo"
      }
      parts.push(`Senioridade: ${seniorityMap[arch.seniority] || arch.seniority}`)
    }
    
    if (arch.industry) {
      const industryMap: Record<string, string> = {
        technology: "Tecnologia",
        fintech: "Fintech/Finanças",
        healthcare: "Saúde",
        education: "Educação",
        ecommerce: "E-commerce/Varejo",
        logistics: "Logística",
        consulting: "Consultoria",
        manufacturing: "Indústria/Manufatura",
        agritech: "Agronegócio",
        other: "Outro"
      }
      parts.push(`Indústria: ${industryMap[arch.industry] || arch.industry}`)
    }
    
    if (arch.filters?.experience_years_min) {
      parts.push(`${arch.filters.experience_years_min}+ anos de experiência`)
    }
    
    if (parts.length === 0) {
      return `Buscar candidatos similares ao arquétipo "${arch.name || arch.title}"`
    }
    
    return parts.join(", ")
  }, [])

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
      console.error("Error reading file:", error)
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
      console.error("Error searching vacancies:", error)
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
      console.error("Error fetching full vacancy:", error)
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

  // Reusable SearchScopeControls component
  const SearchScopeControls = ({ showSearchButton = false, onSearch }: { showSearchButton?: boolean; onSearch?: () => void }) => (
    <div className="flex items-center gap-1 flex-shrink-0">
      {/* Source selectors: Local, Hybrid, Global */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange?.('local'); }}
              className={cn(
                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                searchSource === 'local' 
                  ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                  : "hover:bg-gray-100"
              )}
              style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
            >
              <Home className="w-4 h-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
            <p className="text-xs font-medium">Seu banco de talentos</p>
            <p className="text-xs text-gray-300">Gratuito • Local</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      
      {showGlobalSearchOptions && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                  searchSource === 'hybrid' 
                    ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                    : "hover:bg-gray-100"
                )}
                style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
              >
                <Zap className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
              <p className="text-xs font-medium">Expanda sua busca</p>
              <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                  searchSource === 'global' 
                    ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                    : "hover:bg-gray-100"
                )}
                style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
              >
                <Globe className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
              <p className="text-xs font-medium">Alcance global</p>
              <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
      
      {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
      {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
        <>
          <div className="w-px h-4 bg-gray-200 mx-0.5" />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                    requireEmails 
                      ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                      : "hover:bg-gray-100"
                  )}
                  style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                >
                  <Mail className="w-3.5 h-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                <p className="text-xs font-medium">Apenas com Email</p>
                <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                    requirePhoneNumbers 
                      ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                      : "hover:bg-gray-100"
                  )}
                  style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                >
                  <Phone className="w-3.5 h-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                <p className="text-xs font-medium">Apenas com Telefone</p>
                <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </>
      )}
      
      {/* Search Button */}
      {showSearchButton && onSearch && (
        <>
          <div className="w-px h-4 bg-gray-200 mx-0.5" />
          <Button
            onClick={onSearch}
            disabled={!canSubmit() || isLoading}
            size="sm"
            className="h-8 w-8 p-0 rounded-md transition-all hover:scale-105"
            style={{ 
              backgroundColor: canSubmit() ? "#111827" : "var(--eleven-bg-tertiary)",
              color: canSubmit() ? "white" : "var(--eleven-text-secondary)"
            }}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          </Button>
        </>
      )}
    </div>
  )

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

  const canSubmit = () => {
    if (isLoading) return false
    switch (mode) {
      case "natural":
        return value.trim().length > 0
      case "boolean":
        // If user has typed something, the preview prompt should also have content
        // This prevents submission when user manually clears the preview textarea
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

  const filteredArchetypes = archetypeVacancies.filter(v => {
    const searchLower = archetypeSearch.toLowerCase()
    const title = v.title || ''
    const hiredName = v.hired_candidate?.name || ''
    const department = v.department || ''
    return title.toLowerCase().includes(searchLower) ||
      hiredName.toLowerCase().includes(searchLower) ||
      department.toLowerCase().includes(searchLower)
  })

  return (
    <div 
      ref={containerRef}
      className={cn("space-y-4 relative", className)}
      style={{ width: panelWidth }}
    >
      <div 
        className="rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700"
        style={{ 
          backgroundColor: "#FFFFFF"
        }}
      >
        {/* Mode tabs - Estilo pill/tag elegante */}
        <div 
          className="flex items-center gap-2 px-4 py-3 overflow-x-auto border-b border-gray-200"
          style={{ backgroundColor: "#FFFFFF" }}
        >
          {modes.map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all",
                mode === m.key 
                  ? "" 
                  : "hover:bg-gray-100 dark:hover:bg-gray-800"
              )}
              style={mode === m.key 
                ? { 
                    backgroundColor: "#1f2937",
                    color: "white",
                    fontFamily: '"Open Sans", sans-serif'
                  } 
                : { color: "#4b5563", fontFamily: '"Open Sans", sans-serif' }
              }
            >
              <m.icon className="w-3.5 h-3.5" />
              {m.label}
            </button>
          ))}

          {/* Filters button - ao lado de Arquétipos - shows dynamic count from parsed entities */}
          {onOpenFilters && (
            <button
              onClick={onOpenFilters}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all hover:bg-gray-100 dark:hover:bg-gray-800",
                (activeFiltersCount > 0 || filledCount > 0) && "ring-1 ring-gray-900/20"
              )}
              style={{ 
                color: (activeFiltersCount > 0 || filledCount > 0) ? "#111827" : "#374151",
                backgroundColor: (activeFiltersCount > 0 || filledCount > 0) ? "rgba(229, 231, 235, 0.3)" : "transparent"
              }}
            >
              <Filter className="w-3.5 h-3.5" />
              Filtros
              {(activeFiltersCount > 0 || filledCount > 0) && (
                <Badge 
                  className="ml-1 h-4 min-w-4 px-1 flex items-center justify-center text-xs bg-gray-900" style={{ color: "white" }}
                >
                  {Math.max(activeFiltersCount, filledCount)}
                </Badge>
              )}
            </button>
          )}

          {/* Botão para ir direto para página de resultados */}
          {onGoToResults && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={onGoToResults}
                    className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-all text-gray-700"
                  >
                    <Table2 className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                  <p className="text-xs font-medium">Ir para Resultados</p>
                  <p className="text-xs text-gray-300">Buscar direto na tabela expandida</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Content area - changes based on mode */}
        <div className="p-4" style={{ backgroundColor: "#FFFFFF" }}>
          {/* Natural search mode */}
          {mode === "natural" && (
            <div className="space-y-3">
              <div className="relative">
                {/* Ghost Text Overlay - positioned over textarea */}
                {ghostTextSuffix && !showAutocomplete && (
                  <div 
                    ref={ghostOverlayRef}
                    className="absolute inset-0 pointer-events-none rounded-md px-4 py-3 pr-28 text-base-ui min-h-[56px] overflow-hidden"
                    style={{ 
                      fontFamily: '"Open Sans", sans-serif',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      zIndex: 1,
                    }}
                    aria-hidden="true"
                  >
                    <span style={{ color: 'transparent' }}>{value}</span>
                    <span className="text-gray-400">{ghostTextSuffix}</span>
                  </div>
                )}
                {/* Actual textarea - fully functional for editing */}
                <textarea
                  ref={textareaRef}
                  value={value}
                  onChange={(e) => onChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onScroll={(e) => {
                    if (ghostOverlayRef.current) {
                      ghostOverlayRef.current.scrollTop = e.currentTarget.scrollTop
                    }
                  }}
                  placeholder={getPlaceholder()}
                  className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[56px] transition-all border relative"
                  style={{ 
                    backgroundColor: ghostTextSuffix && !showAutocomplete ? "transparent" : "#FFFFFF",
                    color: "#1a1a1a",
                    caretColor: "#1a1a1a",
                    fontFamily: '"Open Sans", sans-serif',
                    zIndex: 2,
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#D1D5DB"
                    e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#E5E7EB"
                    e.currentTarget.style.boxShadow = "none"
                    setTimeout(() => setShowAutocomplete(false), 200)
                  }}
                  rows={2}
                  disabled={isLoading}
                />
                {/* Seletor de Origem de Busca + Filtros de Contato - Próximo ao search */}
                {onSearchSourceChange && (
                  <div className="absolute right-12 bottom-2.5 flex items-center gap-1 flex-shrink-0" style={{ zIndex: 10 }}>
                    {/* Source selectors: Local, Hybrid, Global */}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                            className={cn(
                              "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                              searchSource === 'local' 
                                ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                : "hover:bg-gray-100"
                            )}
                            style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                          >
                            <Home className="w-4 h-4" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                          <p className="text-xs font-medium">Seu banco de talentos</p>
                          <p className="text-xs text-gray-300">Gratuito • Local</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    {showGlobalSearchOptions && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                searchSource === 'hybrid' 
                                  ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                  : "hover:bg-gray-100"
                              )}
                              style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                            >
                              <Zap className="w-4 h-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Expanda sua busca</p>
                            <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                searchSource === 'global' 
                                  ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                  : "hover:bg-gray-100"
                              )}
                              style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                            >
                              <Globe className="w-4 h-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Alcance global</p>
                            <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                    
                    {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                    {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                      <>
                        <div className="w-px h-4 bg-gray-200 mx-0.5" />
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  requireEmails 
                                    ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                              >
                                <Mail className="w-3.5 h-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  requirePhoneNumbers 
                                    ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                              >
                                <Phone className="w-3.5 h-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </>
                    )}
                    
                    {/* Separador visual */}
                    <div className="w-px h-5 bg-gray-200 mx-1" />
                    
                    {/* Botão Microfone */}
                    <AudioRecordButton
                      onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
                      className="p-1.5 rounded-md hover:bg-gray-100"
                    />
                  </div>
                )}

                {/* Microfone quando não há seletor de origem */}
                {!onSearchSourceChange && (
                  <div className="absolute right-12 bottom-2.5 flex items-center" style={{ zIndex: 10 }}>
                    <AudioRecordButton
                      onTranscription={(text) => onChange(value ? `${value} ${text}` : text)}
                      className="p-1.5 rounded-md hover:bg-gray-100"
                    />
                  </div>
                )}

                <Button
                  onClick={handleSubmit}
                  disabled={!canSubmit()}
                  size="sm"
                  className="absolute right-2.5 bottom-2.5 h-8 w-8 p-0 rounded-md transition-all hover:scale-105"
                  style={{ 
                    backgroundColor: canSubmit() ? "#111827" : "var(--eleven-bg-tertiary)",
                    color: canSubmit() ? "white" : "var(--eleven-text-secondary)",
                    zIndex: 10
                  }}
                >
                  <Search className="w-4 h-4" />
                </Button>

                {/* Autocomplete inline - lista vertical compacta */}
                {showAutocomplete && autocompleteItems.length > 0 && (
                <div 
                  className="absolute top-full left-0 right-0 mt-0.5 rounded-md border border-gray-200 flex flex-col gap-0 z-10 max-h-52 overflow-hidden"
                  style={{
                    backgroundColor: "#FFFFFF",
                    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.07)"
                  }}
                >
                  {/* Header com toggle e botão fechar */}
                  <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      <span className="text-micro font-medium text-gray-500">Sugestões</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setAutocompleteEnabled(false)}
                        className="text-micro text-gray-400 hover:text-gray-600 transition-colors"
                        title="Desativar sugestões"
                      >
                        Desativar
                      </button>
                      <button
                        onClick={() => {
                          setShowAutocomplete(false)
                          setAutocompleteItems([])
                        }}
                        className="p-0.5 rounded hover:bg-gray-100 transition-colors"
                        title="Fechar lista"
                      >
                        <X className="w-3 h-3 text-gray-400" />
                      </button>
                    </div>
                  </div>
                  <div className="py-1 overflow-y-auto max-h-40">
                  {autocompleteItems.slice(0, 6).map((item, index) => {
                    const IconComponent = 
                      item.icon === "code" ? Code :
                      item.icon === "briefcase" ? Briefcase :
                      item.icon === "map-pin" ? MapPin :
                      item.icon === "building" ? Building2 :
                      item.icon === "award" ? Award :
                      item.icon === "home" ? Building2 :
                      item.icon === "globe" ? Globe :
                      item.icon === "target" ? Target :
                      item.icon === "users" ? Users :
                      item.icon === "layers" ? Building2 :
                      item.icon === "zap" ? TrendingUp :
                      item.icon === "brain" ? Brain :
                      item.icon === "database" ? Binary :
                      item.icon === "bar-chart" ? TrendingUp :
                      item.icon === "layout" ? FileText :
                      item.icon === "smartphone" ? Binary :
                      item.icon === "cloud" ? Globe :
                      item.icon === "settings" ? Code :
                      item.icon === "box" ? Binary :
                      item.icon === "coffee" ? Code :
                      item.icon === "file-code" ? Code :
                      item.icon === "clipboard" ? FileText :
                      item.icon === "pen-tool" ? Star :
                      item.icon === "dollar-sign" ? DollarSign :
                      item.icon === "credit-card" ? DollarSign :
                      item.icon === "message-circle" ? Globe :
                      item.icon === "book" ? GraduationCap :
                      Brain

                    const getCategoryColor = (category: string) => {
                      const cat = category.toLowerCase()
                      if (cat.includes('cargo') || cat.includes('título') || cat.includes('job')) 
                        return { bg: '#F3F4F6', accent: '#374151' }
                      if (cat.includes('local') || cat.includes('cidade') || cat.includes('região')) 
                        return { bg: '#F3EAFF', accent: '#8B5CF6' }
                      if (cat.includes('skill') || cat.includes('tecnologia') || cat.includes('ferramenta')) 
                        return { bg: '#E5F5EB', accent: '#5DA47A' }
                      if (cat.includes('experiência') || cat.includes('senioridade') || cat.includes('anos')) 
                        return { bg: '#FDF4E8', accent: '#E5A853' }
                      if (cat.includes('setor') || cat.includes('indústria') || cat.includes('área')) 
                        return { bg: '#E8F1FD', accent: '#3B82F6' }
                      return { bg: '#F5F8FA', accent: '#374151' }
                    }
                    const catColor = getCategoryColor(item.category)
                    const isSelected = selectedAutocompleteIndex === index

                    return (
                      <button
                        key={`${item.text}-${index}`}
                        onClick={() => handleAutocompleteSelect(item)}
                        onMouseEnter={() => setSelectedAutocompleteIndex(index)}
                        className={cn(
                          "flex items-center gap-2 px-3 py-1.5 text-left transition-colors w-full",
                          isSelected ? "bg-gray-50" : "hover:bg-gray-50"
                        )}
                      >
                        <IconComponent 
                          className="w-3.5 h-3.5 flex-shrink-0" 
                          style={{ color: catColor.accent }}
                        />
                        <span 
                          className="text-xs font-medium flex-1 truncate text-gray-950 dark:text-gray-50"
                        >
                          {item.text}
                        </span>
                        <span 
                          className="text-micro text-gray-500 flex-shrink-0"
                        >
                          {item.category}
                        </span>
                      </button>
                    )
                  })}
                  </div>
                </div>
                )}

                {/* Ghost Text Tab hint */}
                {ghostTextSuffix && !showAutocomplete && (
                  <div 
                    className="absolute -bottom-5 right-3 flex items-center gap-1 text-micro text-gray-400"
                  >
                    <kbd className="px-1 py-0.5 rounded-full bg-gray-100 text-micro font-mono">Tab</kbd>
                    <span>para aceitar</span>
                  </div>
                )}

              </div>

              {/* Fallback Suggestion Card - shown BELOW the textarea container when enhanced query doesn't start with user text */}
              {ghostTextInfo.showFallbackCard && ghostTextInfo.fullEnhancement && !showAutocomplete && (
                <div 
                  className="rounded-md border px-3 py-2 flex items-center gap-2"
                  style={{
                    backgroundColor: 'rgba(229, 231, 235, 0.2)',
                    borderColor: 'rgba(96, 190, 209, 0.3)',
                  }}
                >
                  <Wand2 className="w-3.5 h-3.5 flex-shrink-0 text-gray-700" />
                  <div className="flex-1 min-w-0">
                    <span className={textStyles.description}>Sugestão: </span>
                    <span className="text-xs text-gray-800">{ghostTextInfo.fullEnhancement}</span>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={handleAcceptEnhancement}
                      className="flex items-center gap-1 px-2 py-1 rounded-full text-micro font-medium hover:bg-wedo-cyan/15 transition-colors text-gray-700"
                    >
                      <kbd className="px-1 py-0.5 rounded-full bg-gray-100 text-micro font-mono">Tab</kbd>
                      <span>Aceitar</span>
                    </button>
                    <button
                      onClick={handleDismissEnhancement}
                      className="flex items-center justify-center w-5 h-5 rounded hover:bg-gray-100 transition-colors text-gray-400"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )}

              {/* Tags de critérios extraídos - Cores ElevenLabs/WedoTalent */}
              <div className="flex flex-wrap items-center gap-1.5">
                {tags.map((tag) => {
                  const getTagColors = (key: string, filled: boolean) => {
                    if (!filled) return { bg: '#F3F4F6', text: '#1F2937', iconBg: '#6B7280' }
                    switch (key) {
                      case 'job_title':
                        return { bg: '#F3F4F6', text: '#374151', iconBg: '#374151' }
                      case 'location':
                        return { bg: '#F3EAFF', text: '#7C3AED', iconBg: '#8B5CF6' }
                      case 'skills':
                        return { bg: '#E5F5EB', text: '#2D6A4F', iconBg: '#5DA47A' }
                      case 'years_experience':
                        return { bg: '#FDF4E8', text: '#B8860B', iconBg: '#E5A853' }
                      case 'industry':
                        return { bg: '#E8F1FD', text: '#2563EB', iconBg: '#3B82F6' }
                      default:
                        return { bg: '#F3F4F6', text: '#374151', iconBg: '#374151' }
                    }
                  }
                  const colors = getTagColors(tag.key, tag.filled)
                  
                  return (
                    <div
                      key={tag.key}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs transition-all"
                      style={{ 
                        backgroundColor: colors.bg,
                        color: colors.text,
                        fontFamily: '"Open Sans", sans-serif'
                      }}
                      title={tag.value}
                    >
                      <div 
                        className="flex items-center justify-center w-4 h-4 rounded"
                        style={{ backgroundColor: tag.filled ? `${colors.iconBg}30` : 'transparent' }}
                      >
                        <tag.icon className="w-3 h-3" style={{ color: tag.filled ? colors.iconBg : colors.text }} />
                      </div>
                      <span className="font-medium">{tag.label}</span>
                      {tag.filled && tag.value && (
                        <>
                          <span style={{ opacity: 0.5 }}>·</span>
                          <span className="max-w-[80px] truncate font-normal" style={{ opacity: 0.85 }}>{tag.value}</span>
                        </>
                      )}
                    </div>
                  )
                })}

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
                        style={{ fontFamily: '"Open Sans", sans-serif' }}
                      >
                        <Brain className={`w-3.5 h-3.5 ${autocompleteEnabled ? 'text-wedo-cyan' : 'text-gray-400'}`} />
                        <span className="font-medium text-xs">
                          Assistente de Busca
                        </span>
                      </button>
                    </TooltipTrigger>
                    <TooltipContent 
                      side="bottom" 
                      className="max-w-[300px] p-3"
                      style={{ backgroundColor: "white", border: "1px solid var(--eleven-border)" }}
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-wedo-cyan" />
                            <span className="font-semibold text-sm" style={{ color: autocompleteEnabled ? '#22C55E' : '#EF4444' }}>
                              {autocompleteEnabled ? 'Ativado' : 'Desativado'}
                            </span>
                          </div>
                          <span className="text-micro px-2 py-0.5 rounded-full" style={{ 
                            backgroundColor: autocompleteEnabled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: autocompleteEnabled ? '#22C55E' : '#EF4444'
                          }}>
                            {autocompleteEnabled ? 'ON' : 'OFF'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-sm" style={{ color: "var(--eleven-text-primary)" }}>
                            Assistente de Busca Inteligente
                          </span>
                        </div>
                        <p className="text-xs text-gray-800 dark:text-gray-200">
                          Enquanto você descreve o perfil, a LIA analisa e sugere melhorias:
                        </p>
                        <ul className="text-xs space-y-1 text-gray-800 dark:text-gray-200">
                          <li className="flex items-start gap-1.5">
                            <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                            <span>Indica critérios faltantes</span>
                          </li>
                          <li className="flex items-start gap-1.5">
                            <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                            <span>Sugere sinônimos e termos relacionados</span>
                          </li>
                          <li className="flex items-start gap-1.5">
                            <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-700" />
                            <span>Alerta sobre buscas muito amplas ou restritivas</span>
                          </li>
                        </ul>
                        <p className="text-micro pt-1 border-t text-gray-500" style={{ borderColor: "var(--eleven-border)" }}>
                          {autocompleteEnabled ? 'Clique para desativar' : 'Clique para ativar'}
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Indicador de análise - aparece depois do assistente */}
                {isParsingEntities && (
                  <div 
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                    style={{ 
                      backgroundColor: "rgba(229, 231, 235, 0.3)"
                    }}
                  >
                    <div 
                      className="w-3 h-3 border-2 border-t-transparent rounded-full animate-spin" 
                      style={{ borderTopColor: "transparent" }}
                    />
                    <span>Analisando...</span>
                  </div>
                )}
              </div>

              {/* Assistente de Busca - Barra de completude e alertas */}
              {value && searchAnalysis && (
                <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--eleven-border)" }}>
                  {/* Barra de completude */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                          Qualidade da busca
                        </span>
                        <span 
                          className="text-xs font-bold"
                          style={{ 
                            color: searchAnalysis.completeness_score >= 60 
                              ? "#22c55e" 
                              : searchAnalysis.completeness_score >= 40 
                                ? "#f59e0b" 
                                : "#ef4444" 
                          }}
                        >
                          {searchAnalysis.completeness_score}%
                        </span>
                      </div>
                      <div 
                        className="h-1.5 rounded-full overflow-hidden"
                        style={{ backgroundColor: "var(--eleven-bg-tertiary)" }}
                      >
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{ 
                            width: `${searchAnalysis.completeness_score}%`,
                            backgroundColor: searchAnalysis.completeness_score >= 60 
                              ? "#22c55e" 
                              : searchAnalysis.completeness_score >= 40 
                                ? "#f59e0b" 
                                : "#ef4444"
                          }}
                        />
                      </div>
                    </div>
                    {searchAnalysis.next_recommended_action && (
                      <div 
                        className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs"
                        style={{ 
                          backgroundColor: "rgba(96, 190, 209, 0.08)"
                        }}
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
                          className="flex items-start gap-2 px-2.5 py-2 rounded-full text-xs"
                          style={{ 
                            backgroundColor: alert.severity === "warning" 
                              ? "rgba(245, 158, 11, 0.08)" 
                              : "rgba(96, 190, 209, 0.08)",
                            color: "var(--eleven-text-secondary)"
                          }}
                        >
                          {alert.severity === "warning" ? (
                            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-500" />
                          ) : (
                            <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                          )}
                          <div className="flex-1 min-w-0">
                            <span>{alert.message}</span>
                            {alert.suggestion && (
                              <button
                                onClick={() => {
                                  if (alert.action_value) {
                                    onChange(value + ", " + alert.action_value)
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

                  {/* Sugestões de enriquecimento - Inline scroll se necessário */}
                  {Object.keys(searchAnalysis.enrichment_suggestions).length > 0 && (
                    <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                      <span className="text-xs text-gray-950 dark:text-gray-50 font-medium whitespace-nowrap" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                        Adicionar:
                      </span>
                      <div className="flex gap-1.5 flex-nowrap">
                        {Object.entries(searchAnalysis.enrichment_suggestions).flatMap(([category, items]) =>
                          items.slice(0, 5).map((item) => (
                            <button
                              key={`${category}-${item}`}
                              onClick={() => onChange(value + ", " + item)}
                              className="px-2 py-0.5 rounded-full text-xs font-medium transition-all hover:scale-105 border border-gray-200 whitespace-nowrap flex-shrink-0"
                              style={{ 
                                backgroundColor: "#FFFFFF",
                                fontFamily: '"Open Sans", sans-serif'
                              }}
                            >
                              + {item}
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Sugestões de busca - Horizontal lado a lado */}
              {!value && (
                <div className="pt-1 w-full flex items-start gap-2">
                  <span className="text-xs text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap mt-0.5" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                    Sugestões:
                  </span>
                  <div className="flex items-center gap-2 flex-nowrap overflow-x-auto">
                    {SEARCH_SUGGESTIONS.map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => onChange(suggestion)}
                        className="px-2.5 py-0.5 text-xs text-gray-800 dark:text-gray-200 hover:text-gray-900 dark:hover:text-gray-50 bg-gray-50 hover:bg-gray-100 rounded-full border border-gray-200 transition-all whitespace-nowrap flex-shrink-0"
                        style={{ fontFamily: '"Open Sans", sans-serif' }}
                        title={suggestion}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Similar profile mode - Combined Profile Feature */}
          {mode === "similar" && (
            <div className="space-y-3">
              {/* URL inputs */}
              {similarUrls.map((url, index) => (
                <div key={index} className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2">
                    <Linkedin className="w-3.5 h-3.5 text-[#0077B5]" />
                  </div>
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => updateSimilarUrl(index, e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={index === 0 ? "Cole a URL do LinkedIn ou ID do candidato..." : "Cole outra URL para combinar perfis..."}
                    className="w-full rounded-md pl-9 pr-20 py-2.5 text-base-ui focus:outline-none transition-all border"
                    style={{ 
                      backgroundColor: "#FFFFFF",
                      color: "#1a1a1a",
                      fontFamily: "'Open Sans', sans-serif"
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#D1D5DB"
                      e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "#E5E7EB"
                      e.currentTarget.style.boxShadow = "none"
                    }}
                    disabled={isLoading}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    {index > 0 && (
                      <button
                        onClick={() => removeSimilarUrl(index)}
                        className="p-1 rounded hover:bg-red-50 transition-colors"
                      >
                        <X className="w-3 h-3 text-red-400" />
                      </button>
                    )}
                    {index === similarUrls.length - 1 && similarUrls.length < MAX_SIMILAR_URLS && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={addSimilarUrl}
                              className="px-2 py-1 rounded-full text-xs font-medium hover:bg-gray-900 hover:text-white dark:hover:bg-gray-100 dark:hover:text-gray-900 transition-colors"
                              style={{ 
                                backgroundColor: "rgba(229, 231, 235, 0.3)"
                              }}
                            >
                              + URL
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="text-xs max-w-[200px] !animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            Adicione até 3 perfis para a LIA criar um perfil ideal combinado
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                  </div>
                </div>
              ))}

              {/* CV Upload section */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-micro text-gray-400 uppercase tracking-wider">ou</span>
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
                        className="flex items-center gap-2 px-2.5 py-1.5 rounded-full text-xs"
                        style={{ backgroundColor: "#F8F9FA", fontFamily: "'Open Sans', sans-serif" }}
                      >
                        <FileText className="w-3 h-3 text-gray-500" />
                        <span className="max-w-[150px] truncate text-gray-800 dark:text-gray-200">{file.name}</span>
                        <button onClick={() => removeCvFile(index)} className="hover:text-red-500">
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </div>
                    ))}
                    {similarCvFiles.length < MAX_CV_FILES && (
                      <button
                        onClick={() => cvFileInputRef.current?.click()}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium hover:bg-gray-100 transition-colors border"
                        style={{ backgroundColor: "#FFFFFF", fontFamily: "'Open Sans', sans-serif" }}
                      >
                        <Upload className="w-3 h-3" />
                        + CV
                      </button>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => cvFileInputRef.current?.click()}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-md text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors border border-dashed"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Arraste CVs aqui ou clique para upload (máx. 2)
                  </button>
                )}
              </div>

              {/* Analyze button - Shows when 2+ sources */}
              {hasMultipleSources() && !showCombinedSuggestions && (
                <Button
                  onClick={analyzeProfiles}
                  disabled={isAnalyzingProfiles}
                  className="w-full text-xs h-9 bg-gray-900"
                >
                  {isAnalyzingProfiles ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                      Analisando perfis...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-3.5 h-3.5 mr-2" />
                      Analisar e combinar perfis com LIA
                    </>
                  )}
                </Button>
              )}

              {/* Combined Suggestions Box */}
              {showCombinedSuggestions && combinedSuggestions.length > 0 && (
                <div className="p-3 rounded-md space-y-2 border border-gray-200" style={{ backgroundColor: "#F8FCFD" }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      <span className="text-xs font-medium" style={{ color: "var(--eleven-text-primary)" }}>
                        Perfil Ideal sugerido pela LIA
                      </span>
                    </div>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <HelpCircle className="w-3.5 h-3.5 text-gray-600" />
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
                        className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium group border border-gray-200"
                        style={{ backgroundColor: "white" }}
                      >
                        <span className="text-gray-700">{keyword}</span>
                        <button
                          onClick={() => removeSuggestion(keyword)}
                          className="opacity-50 group-hover:opacity-100 hover:text-red-500 transition-opacity"
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

              {/* Preview/Edit do Prompt - Similar Mode with integrated controls */}
              {combinedSuggestions.length > 0 && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-gray-700" />
                      <span className="text-xs font-medium" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                        Preview do prompt de busca
                      </span>
                    </div>
                    <span className="text-micro text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>editável</span>
                  </div>
                  <div className="relative">
                    <textarea
                      value={similarSearchPrompt}
                      onChange={(e) => setSimilarSearchPrompt(e.target.value)}
                      placeholder="Descreva o perfil que deseja buscar..."
                      className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-all border"
                      style={{ 
                        backgroundColor: "#FFFFFF",
                        color: "#1a1a1a",
                        fontFamily: "'Open Sans', sans-serif"
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = "#D1D5DB"
                        e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = "#E5E7EB"
                        e.currentTarget.style.boxShadow = "none"
                      }}
                      rows={2}
                    />
                    {/* Ícones de escopo posicionados absolutamente dentro do textarea */}
                    {onSearchSourceChange && (
                      <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1" style={{ zIndex: 10 }}>
                        <div className="flex items-center gap-1">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                    searchSource === 'local' 
                                      ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                      : "hover:bg-gray-100"
                                  )}
                                  style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                                >
                                  <Home className="w-4 h-4" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Seu banco de talentos</p>
                                <p className="text-xs text-gray-300">Gratuito • Local</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          
                          {showGlobalSearchOptions && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                      searchSource === 'hybrid' 
                                        ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                        : "hover:bg-gray-100"
                                    )}
                                    style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                                  >
                                    <Zap className="w-4 h-4" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Expanda sua busca</p>
                                  <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                      searchSource === 'global' 
                                        ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                        : "hover:bg-gray-100"
                                    )}
                                    style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                                  >
                                    <Globe className="w-4 h-4" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Alcance global</p>
                                  <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                          
                          {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                          {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                            <>
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      type="button"
                                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                        requireEmails 
                                          ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                          : "hover:bg-gray-100"
                                      )}
                                      style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                                    >
                                      <Mail className="w-3.5 h-3.5" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Apenas com Email</p>
                                    <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                              
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      type="button"
                                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                        requirePhoneNumbers 
                                          ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                          : "hover:bg-gray-100"
                                      )}
                                      style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                                    >
                                      <Phone className="w-3.5 h-3.5" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Apenas com Telefone</p>
                                    <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </>
                          )}
                          
                          {/* Botão de busca com hint */}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={handleSubmit}
                                  disabled={!canSubmit() || isLoading}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md transition-all",
                                    canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                                  )}
                                  style={{ color: canSubmit() ? '#6B7280' : '#D1D5DB' }}
                                >
                                  {isLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Search className="w-4 h-4" />
                                  )}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Buscar Similares</p>
                                <p className="text-xs text-gray-300">Encontra candidatos com perfil similar</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                        {/* Hint abaixo dos ícones */}
                        <span className="text-micro text-gray-400 italic">buscar similares</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Search Scope Controls + Search Button - Only show when no preview textarea */}
              {combinedSuggestions.length === 0 && (
                <div className="relative">
                  <textarea
                    value={similarSearchPrompt}
                    onChange={(e) => setSimilarSearchPrompt(e.target.value)}
                    placeholder="Edite o prompt de busca ou adicione perfis acima..."
                    className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[56px] transition-all border"
                    style={{ 
                      backgroundColor: "#FFFFFF",
                      color: "#1a1a1a",
                      fontFamily: "'Open Sans', sans-serif"
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#D1D5DB"
                      e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "#E5E7EB"
                      e.currentTarget.style.boxShadow = "none"
                    }}
                    rows={2}
                  />
                  {/* Ícones de escopo posicionados absolutamente dentro do textarea */}
                  {onSearchSourceChange && (
                    <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1" style={{ zIndex: 10 }}>
                      <div className="flex items-center gap-1">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  searchSource === 'local' 
                                    ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                              >
                                <Home className="w-4 h-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Seu banco de talentos</p>
                              <p className="text-xs text-gray-300">Gratuito • Local</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        {showGlobalSearchOptions && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                    searchSource === 'hybrid' 
                                      ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                      : "hover:bg-gray-100"
                                  )}
                                  style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                                >
                                  <Zap className="w-4 h-4" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Expanda sua busca</p>
                                <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                    searchSource === 'global' 
                                      ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                      : "hover:bg-gray-100"
                                  )}
                                  style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                                >
                                  <Globe className="w-4 h-4" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Alcance global</p>
                                <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        
                        {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                        {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                          <>
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                      requireEmails 
                                        ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                        : "hover:bg-gray-100"
                                    )}
                                    style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                                  >
                                    <Mail className="w-3.5 h-3.5" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Apenas com Email</p>
                                  <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                            
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                      requirePhoneNumbers 
                                        ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                        : "hover:bg-gray-100"
                                    )}
                                    style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                                  >
                                    <Phone className="w-3.5 h-3.5" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Apenas com Telefone</p>
                                  <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </>
                        )}
                        
                        {/* Botão de busca com hint */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={handleSubmit}
                                disabled={!canSubmit() || isLoading}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md transition-all",
                                  canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                                )}
                                style={{ color: canSubmit() ? '#6B7280' : '#D1D5DB' }}
                              >
                                {isLoading ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Search className="w-4 h-4" />
                                )}
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Buscar Similares</p>
                              <p className="text-xs text-gray-300">Encontra candidatos com perfil similar</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
                      {/* Hint abaixo dos ícones */}
                      <span className="text-micro text-gray-400 italic">buscar similares</span>
                    </div>
                  )}
                </div>
              )}

              {/* Dica contextual padronizada */}
              <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                  <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <strong>Dica:</strong> Cole 1 a 3 links do LinkedIn ou faça upload de até 2 CVs. Com 2+ perfis, a LIA combina as melhores características e sugere palavras-chave para encontrar candidatos similares.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Job Description mode */}
          {mode === "jd" && (
            <div className="space-y-3">
              {/* Buscar vaga existente */}
              <div className="relative">
                <div className="flex items-center justify-between mb-1.5">
                  <span 
                    className="text-xs font-medium"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    Buscar vaga existente
                  </span>
                  <span className="text-micro text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>opcional</span>
                </div>
                
                {selectedVacancy ? (
                  <div 
                    className="flex items-center justify-between p-2.5 rounded-md border"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)' }}
                  >
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-6 h-6 rounded-full flex items-center justify-center bg-gray-200"
                      >
                        <Briefcase className="w-3 h-3 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-base-ui font-medium text-gray-800" style={{ fontFamily: "'Open Sans', sans-serif" }}>{selectedVacancy.title}</p>
                        {selectedVacancy.job_id && (
                          <p className="text-micro text-gray-500" style={{ fontFamily: "'Open Sans', sans-serif" }}>ID: {selectedVacancy.job_id}</p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={clearSelectedVacancy}
                      className="p-1 rounded hover:bg-gray-100 transition-colors"
                    >
                      <X className="w-3.5 h-3.5 text-gray-400" />
                    </button>
                  </div>
                ) : (
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 -translate-y-1/2">
                      {isSearchingVacancies ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />
                      ) : (
                        <Search className="w-3.5 h-3.5 text-gray-400" />
                      )}
                    </div>
                    <input
                      type="text"
                      value={jdVacancySearch}
                      onChange={(e) => setJdVacancySearch(e.target.value)}
                      placeholder="Digite o nome ou ID da vaga..."
                      className="w-full pl-9 pr-4 py-2.5 text-base-ui rounded-md border focus:outline-none transition-all"
                      style={{ 
                        backgroundColor: 'var(--gray-50)',
                        color: 'var(--gray-950)',
                        fontFamily: "'Open Sans', sans-serif"
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = "#D1D5DB"
                        e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = "#E5E7EB"
                        e.currentTarget.style.boxShadow = "none"
                      }}
                    />
                    
                    {/* Resultados da busca */}
                    {showVacancyResults && jdVacancyResults.length > 0 && (
                      <div 
                        className="absolute z-50 top-full left-0 right-0 mt-1 rounded-md border overflow-hidden"
                        style={{ backgroundColor: 'var(--gray-50)' }}
                      >
                        {jdVacancyResults.map((vacancy) => (
                          <button
                            key={vacancy.id}
                            onClick={() => handleSelectVacancy(vacancy)}
                            className="w-full p-2.5 text-left hover:bg-gray-50 transition-colors border-b last:border-b-0 border border-gray-200"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <p className="text-base-ui font-medium text-gray-800 truncate" style={{ fontFamily: "'Open Sans', sans-serif" }}>{vacancy.title}</p>
                                  <Badge 
                                    variant="outline" 
                                    className="text-micro px-1.5 py-0 h-4 flex-shrink-0"
                                    style={{ 
                                      borderColor: vacancy.status === 'Ativa' ? '#22c55e' : '#9ca3af',
                                      color: vacancy.status === 'Ativa' ? '#22c55e' : '#6b7280'
                                    }}
                                  >
                                    {vacancy.status}
                                  </Badge>
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                  {vacancy.job_id && (
                                    <span className="text-micro text-gray-500" style={{ fontFamily: "'Open Sans', sans-serif" }}>ID: {vacancy.job_id}</span>
                                  )}
                                  <span className="text-micro text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>{formatDate(vacancy.created_at)}</span>
                                </div>
                                {vacancy.description_preview && (
                                  <p className="text-xs text-gray-500 mt-1 line-clamp-2" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                    {vacancy.description_preview}
                                  </p>
                                )}
                              </div>
                              <ChevronRight className="w-3.5 h-3.5 text-gray-300 flex-shrink-0 mt-0.5" />
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {showVacancyResults && jdVacancySearch.length >= 2 && jdVacancyResults.length === 0 && !isSearchingVacancies && (
                      <div 
                        className="absolute z-50 top-full left-0 right-0 mt-1 p-2.5 rounded-md border text-center"
                        style={{ backgroundColor: 'var(--gray-50)' }}
                      >
                        <p className="text-base-ui text-gray-500" style={{ fontFamily: "'Open Sans', sans-serif" }}>Nenhuma vaga encontrada</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Divisor */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-micro text-gray-400 uppercase tracking-wider">ou</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              {/* Cole a descrição da vaga */}
              <div className="flex items-center justify-between mb-1.5">
                <span 
                  className="text-xs font-medium"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  Cole a descrição da vaga
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.doc,.docx,.pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs h-6 px-2"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  <Upload className="w-3 h-3 mr-1" />
                  Upload
                </Button>
              </div>
              
              {/* Textarea com ícones de escopo posicionados absolutamente (como Natural e Boolean) */}
              <div className="relative">
                <textarea
                  value={jdContent}
                  onChange={(e) => {
                    setJdContent(e.target.value)
                    if (e.target.value !== jdContent) {
                      setSelectedVacancy(null)
                    }
                  }}
                  placeholder={getPlaceholder()}
                  className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[100px] transition-all border"
                  style={{ 
                    backgroundColor: "#FFFFFF",
                    color: "#1a1a1a",
                    fontFamily: "'Open Sans', sans-serif"
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#D1D5DB"
                    e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#E5E7EB"
                    e.currentTarget.style.boxShadow = "none"
                  }}
                  disabled={isLoading}
                />
                {/* Ícones de escopo + botão de busca posicionados absolutamente dentro do textarea */}
                {onSearchSourceChange && (
                  <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1" style={{ zIndex: 10 }}>
                    <div className="flex items-center gap-1">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                searchSource === 'local' 
                                  ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                  : "hover:bg-gray-100"
                              )}
                              style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                            >
                              <Home className="w-4 h-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Seu banco de talentos</p>
                            <p className="text-xs text-gray-300">Gratuito • Local</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      {showGlobalSearchOptions && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  searchSource === 'hybrid' 
                                    ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                              >
                                <Zap className="w-4 h-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Expanda sua busca</p>
                              <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  searchSource === 'global' 
                                    ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                              >
                                <Globe className="w-4 h-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Alcance global</p>
                              <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      
                      {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                      {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                        <>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                    requireEmails 
                                      ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                      : "hover:bg-gray-100"
                                  )}
                                  style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                                >
                                  <Mail className="w-3.5 h-3.5" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Apenas com Email</p>
                                <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                  className={cn(
                                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                    requirePhoneNumbers 
                                      ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                      : "hover:bg-gray-100"
                                  )}
                                  style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                                >
                                  <Phone className="w-3.5 h-3.5" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                <p className="text-xs font-medium">Apenas com Telefone</p>
                                <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </>
                      )}
                      
                      {/* Botão de busca com hint */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={handleSubmit}
                              disabled={!canSubmit() || isLoading}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md transition-all",
                                canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                              )}
                              style={{ color: canSubmit() ? '#6B7280' : '#D1D5DB' }}
                            >
                              {isLoading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Search className="w-4 h-4" />
                              )}
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Extrair e Buscar</p>
                            <p className="text-xs text-gray-300">Extrai requisitos e busca candidatos</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    {/* Hint abaixo dos ícones */}
                    <span className="text-micro text-gray-400 italic">extrair e buscar</span>
                  </div>
                )}
              </div>

              {/* Preview/Edit do Prompt - JD Mode */}
              {jdContent.trim().length > 0 && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-gray-700" />
                      <span className="text-xs font-medium" style={{ color: "var(--eleven-text-primary)" }}>
                        Preview do prompt de busca
                      </span>
                    </div>
                    <span className="text-micro text-gray-400">editável</span>
                  </div>
                  <textarea
                    value={jdSearchPrompt}
                    onChange={(e) => setJdSearchPrompt(e.target.value)}
                    placeholder="O prompt será gerado a partir da descrição da vaga..."
                    className="w-full resize-none rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 min-h-[60px]"
                    style={{ 
                      border: "1px solid var(--eleven-border)",
                      backgroundColor: "#F8FCFD",
                      color: "var(--eleven-text-primary)"
                    }}
                    rows={2}
                  />
                </div>
              )}

              {/* Dica contextual padronizada */}
              <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                  <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <strong>Dica:</strong> Selecione uma vaga existente ou cole a JD completa para extrair automaticamente requisitos técnicos e comportamentais.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Boolean mode */}
          {mode === "boolean" && (
            <div className="space-y-3">
              {/* Container principal com textarea e controles posicionados absolutamente (como Natural) */}
              <div className="relative">
                <div className="absolute left-3 top-3">
                  <Binary className="w-4 h-4 text-gray-700" />
                </div>
                <textarea
                  ref={textareaRef}
                  value={value}
                  onChange={(e) => onChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={getPlaceholder()}
                  className={cn(
                    "w-full resize-none rounded-md pl-10 pr-28 py-3 text-sm font-mono focus:outline-none min-h-[56px] transition-all border",
                    booleanError && "ring-2 ring-red-300"
                  )}
                  style={{ 
                    borderColor: booleanError ? "#fca5a5" : "#E5E7EB",
                    backgroundColor: "#FFFFFF",
                    color: "#1a1a1a"
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#D1D5DB"
                    e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = booleanError ? "#fca5a5" : "#E5E7EB"
                    e.currentTarget.style.boxShadow = "none"
                  }}
                  rows={2}
                  disabled={isLoading}
                />
                {/* Ícones de escopo posicionados absolutamente dentro do textarea (como Natural) */}
                {onSearchSourceChange && (
                  <div className="absolute right-3 bottom-2.5 flex items-center gap-1 flex-shrink-0" style={{ zIndex: 10 }}>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                            className={cn(
                              "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                              searchSource === 'local' 
                                ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                : "hover:bg-gray-100"
                            )}
                            style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                          >
                            <Home className="w-4 h-4" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                          <p className="text-xs font-medium">Seu banco de talentos</p>
                          <p className="text-xs text-gray-300">Gratuito • Local</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    {showGlobalSearchOptions && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                searchSource === 'hybrid' 
                                  ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                  : "hover:bg-gray-100"
                              )}
                              style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                            >
                              <Zap className="w-4 h-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Expanda sua busca</p>
                            <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                              className={cn(
                                "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                searchSource === 'global' 
                                  ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                  : "hover:bg-gray-100"
                              )}
                              style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                            >
                              <Globe className="w-4 h-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                            <p className="text-xs font-medium">Alcance global</p>
                            <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                    
                    {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                    {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                      <>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  requireEmails 
                                    ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                              >
                                <Mail className="w-3.5 h-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Apenas com Email</p>
                              <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                className={cn(
                                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                  requirePhoneNumbers 
                                    ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                    : "hover:bg-gray-100"
                                )}
                                style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                              >
                                <Phone className="w-3.5 h-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                              <p className="text-xs font-medium">Apenas com Telefone</p>
                              <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </>
                    )}
                    
                    {/* Botão de busca */}
                    <button
                      type="button"
                      onClick={handleSubmit}
                      disabled={!canSubmit() || isLoading}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md transition-all",
                        canSubmit() ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                      )}
                      style={{ color: canSubmit() ? '#6B7280' : '#D1D5DB' }}
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                )}
              </div>
              
              {booleanError && (
                <div className="flex items-center gap-2 text-xs text-red-500">
                  <AlertCircle className="w-3.5 h-3.5" />
                  {booleanError}
                </div>
              )}
              
              <div className="flex flex-wrap gap-2">
                <span className="text-xs" style={{ color: "var(--eleven-text-secondary)" }}>Operadores:</span>
                {["AND", "OR", "NOT", "(", ")"].map((op) => (
                  <button
                    key={op}
                    onClick={() => onChange(value + (value ? " " : "") + op + " ")}
                    className="px-2 py-0.5 rounded text-xs font-mono hover:bg-gray-100 transition-colors"
                    style={{ 
                      backgroundColor: "var(--eleven-bg-tertiary)",
                      color: "var(--eleven-text-secondary)"
                    }}
                  >
                    {op}
                  </button>
                ))}
              </div>
              
              {/* Dica contextual padronizada */}
              <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                  <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições. Ex: (Python OR Java) AND "São Paulo"
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Archetypes mode */}
          {mode === "archetypes" && (
            <div className="space-y-2">
              {/* Tabs: Lista / Criar - Padrão ElevenLabs */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setArchetypeTab("list")}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                    archetypeTab === "list" 
                      ? "bg-gray-100 ring-1 ring-gray-400" 
                      : "bg-white ring-1 ring-[#E5E7EB] hover:bg-gray-50"
                  )}
                  style={{ 
                    color: archetypeTab === "list" ? "#1a1a1a" : "#6B7280",
                    fontFamily: "'Open Sans', sans-serif"
                  }}
                >
                  <Target className="w-3 h-3" />
                  Arquétipos
                </button>
                <button
                  onClick={() => setArchetypeTab("create")}
                  className="flex items-center gap-1 h-7 px-3 rounded-md text-xs font-medium transition-all ring-1 ring-gray-300 hover:ring-gray-400 hover:bg-gray-50"
                  style={{ 
                    backgroundColor: "white",
                    fontFamily: "'Open Sans', sans-serif"
                  }}
                >
                  <Plus className="w-3 h-3" />
                  Criar Novo
                </button>
              </div>

              {/* Lista de Arquétipos */}
              {archetypeTab === "list" && (
                <>
                  <div className="relative">
                    <div className="absolute left-2.5 top-1/2 -translate-y-1/2">
                      <Search className="w-3.5 h-3.5" style={{ color: "var(--eleven-text-secondary)" }} />
                    </div>
                    <input
                      type="text"
                      value={archetypeSearch}
                      onChange={(e) => setArchetypeSearch(e.target.value)}
                      placeholder="Buscar arquétipos..."
                      className="w-full rounded-md pl-8 pr-3 py-2 text-xs focus:outline-none focus:ring-2"
                      style={{ 
                        border: "1px solid var(--eleven-border)",
                        backgroundColor: "var(--eleven-bg-main)",
                        color: "var(--eleven-text-primary)"
                      }}
                    />
                  </div>

                  {isLoadingArchetypes ? (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 className="w-5 h-5 animate-spin text-gray-700" />
                      <span className="ml-2 text-sm" style={{ color: "var(--eleven-text-secondary)" }}>
                        Carregando arquétipos...
                      </span>
                    </div>
                  ) : filteredArchetypes.length === 0 ? (
                    <div className="text-center py-6">
                      <Target className="w-8 h-8 mx-auto mb-2" style={{ color: "var(--eleven-text-secondary)" }} />
                      <p className="text-sm" style={{ color: "var(--eleven-text-secondary)" }}>
                        {archetypeVacancies.length === 0 
                          ? "Nenhum arquétipo encontrado"
                          : "Nenhum arquétipo corresponde à busca"
                        }
                      </p>
                      <Button
                        onClick={() => setArchetypeTab("create")}
                        variant="ghost"
                        size="sm"
                        className="mt-3 bg-gray-100"
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" />
                        Criar Arquétipo
                      </Button>
                    </div>
                  ) : (
                    <div className="max-h-[280px] overflow-y-auto space-y-1">
                      {filteredArchetypes.map((arch: any) => {
                        const isExpanded = expandedArchetypeId === arch.id
                        return (
                          <div
                            key={arch.id}
                            className={cn(
                              "group relative w-full rounded-md text-left transition-all cursor-pointer",
                              isExpanded
                                ? "bg-gray-50 ring-1 ring-gray-900/20"
                                : selectedArchetype?.id === arch.id 
                                  ? "bg-gray-50 ring-1 ring-gray-900/20" 
                                  : "bg-white hover:bg-gray-50"
                            )}
                            style={{ 
                              border: isExpanded || selectedArchetype?.id === arch.id 
                                ? "1px solid #D1D5DB" 
                                : "1px solid #E5E7EB"
                            }}
                          >
                            <div 
                              className="px-3 py-2.5"
                              onClick={() => {
                                setExpandedArchetypeId(isExpanded ? null : arch.id)
                              }}
                            >
                              <div className="flex items-center gap-2">
                                <span className="text-base-ui flex-shrink-0">{arch.emoji || "🎯"}</span>
                                <span 
                                  className="font-semibold text-xs truncate text-gray-800"
                                >
                                  {arch.name || arch.title}
                                </span>
                                {arch.is_default && (
                                  <span 
                                    className="text-micro px-1.5 py-0.5 rounded-full flex-shrink-0 font-medium"
                                    style={{ backgroundColor: "rgba(96,190,209,0.15)" }}
                                  >
                                    Padrão
                                  </span>
                                )}
                                {!isExpanded && arch.tags && arch.tags.length > 0 && (
                                  <div className="flex items-center gap-1 ml-auto flex-shrink-0 group-hover:hidden">
                                    {arch.tags.slice(0, 2).map((tag: string, idx: number) => (
                                      <span 
                                        key={idx} 
                                        className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                                      >
                                        {tag}
                                      </span>
                                    ))}
                                    {arch.tags.length > 2 && (
                                      <span className="text-micro px-1 py-0.5 text-gray-400">
                                        +{arch.tags.length - 2}
                                      </span>
                                    )}
                                  </div>
                                )}
                                <div className="ml-auto flex items-center gap-1 flex-shrink-0">
                                  {isExpanded ? (
                                    <ChevronUp className="w-3.5 h-3.5 text-gray-700" />
                                  ) : (
                                    <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                                  )}
                                </div>
                              </div>
                              {!isExpanded && arch.description && (
                                <p 
                                  className="mt-1 pl-[21px] text-micro line-clamp-1" 
                                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                                >
                                  {arch.description}
                                </p>
                              )}
                            </div>
                            
                            {isExpanded && (
                              <div className="px-3 pb-3 space-y-2 border-t border-t-gray-200" style={{ paddingTop: "10px" }}>
                                {arch.description && (
                                  <p className="text-micro" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                    {arch.description}
                                  </p>
                                )}
                                
                                <div className="space-y-1">
                                  <span className="text-micro font-medium text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                    Query de Busca
                                  </span>
                                  <p 
                                    className="text-xs p-2 rounded" 
                                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                                  >
                                    {arch.query || "Sem query definida"}
                                  </p>
                                </div>
                                
                                {arch.tags && arch.tags.length > 0 && (
                                  <div className="space-y-1">
                                    <span className="text-micro font-medium text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                      Tags
                                    </span>
                                    <div className="flex flex-wrap gap-1">
                                      {arch.tags.map((tag: string, idx: number) => (
                                        <span 
                                          key={idx} 
                                          className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                                        >
                                          {tag}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {arch.filters?.skills && arch.filters.skills.length > 0 && (
                                  <div className="space-y-1">
                                    <span className="text-micro font-medium text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                      Skills
                                    </span>
                                    <div className="flex flex-wrap gap-1">
                                      {arch.filters.skills.map((skill: string, idx: number) => (
                                        <span 
                                          key={idx} 
                                          className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                                        >
                                          {skill}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                <div className="flex flex-wrap gap-2 text-micro" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                  {arch.seniority && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Senioridade:</span>
                                      <span className="font-medium capitalize text-gray-700">{arch.seniority}</span>
                                    </div>
                                  )}
                                  {arch.industry && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Indústria:</span>
                                      <span className="font-medium capitalize text-gray-700">{arch.industry}</span>
                                    </div>
                                  )}
                                  {arch.filters?.experience_years_min && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Experiência:</span>
                                      <span className="font-medium text-gray-700">{arch.filters.experience_years_min}+ anos</span>
                                    </div>
                                  )}
                                  {arch.filters?.location && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Localização:</span>
                                      <span className="font-medium text-gray-700">{arch.filters.location}</span>
                                    </div>
                                  )}
                                  {arch.filters?.work_model && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Modelo:</span>
                                      <span className="font-medium text-gray-700">
                                        {arch.filters.work_model === 'remote' ? 'Remoto' : 
                                         arch.filters.work_model === 'hybrid' ? 'Híbrido' : 
                                         arch.filters.work_model === 'onsite' ? 'Presencial' : arch.filters.work_model}
                                      </span>
                                    </div>
                                  )}
                                  {arch.filters?.employment_type && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-gray-400">Contrato:</span>
                                      <span className="font-medium text-gray-700">
                                        {arch.filters.employment_type === 'clt' ? 'CLT' : 
                                         arch.filters.employment_type === 'pj' ? 'PJ' : 
                                         arch.filters.employment_type === 'intern' ? 'Estágio' : 
                                         arch.filters.employment_type === 'temporary' ? 'Temporário' : 
                                         arch.filters.employment_type === 'freelancer' ? 'Freelancer' : arch.filters.employment_type}
                                      </span>
                                    </div>
                                  )}
                                </div>
                                {arch.filters?.languages && arch.filters.languages.length > 0 && (
                                  <div className="space-y-1">
                                    <span className="text-micro font-medium text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                                      Idiomas
                                    </span>
                                    <div className="flex flex-wrap gap-1">
                                      {arch.filters.languages.map((lang: string, idx: number) => (
                                        <span 
                                          key={idx} 
                                          className="px-1.5 py-0.5 rounded-full text-micro bg-gray-100"
                                        >
                                          {lang}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                <div className="flex items-center gap-2 pt-2 mt-1 border-t border-t-gray-100">
                                  <Button
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      setSelectedArchetype(arch)
                                      setArchetypeSearchPrompt(buildArchetypePrompt(arch))
                                      setExpandedArchetypeId(null)
                                    }}
                                    className="flex-1 text-xs h-8 bg-gray-800" style={{ color: "white", fontFamily: "'Open Sans', sans-serif" }}
                                  >
                                    <Check className="w-3 h-3 mr-1" />
                                    Usar Arquétipo
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => openEditArchetype(arch, e)}
                                    className="text-xs h-8"
                                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                                  >
                                    <Pencil className="w-3 h-3 mr-1" />
                                    Editar
                                  </Button>
                                  {!arch.is_default && (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={(e) => deleteArchetype(arch.id, e)}
                                      disabled={isDeletingArchetype === arch.id}
                                      className="text-xs px-2"
                                      style={{ color: "#ef4444" }}
                                    >
                                      {isDeletingArchetype === arch.id ? (
                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                      ) : (
                                        <Trash2 className="w-3.5 h-3.5" />
                                      )}
                                    </Button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Preview/Edit do Prompt - Archetypes Mode with integrated controls */}
                  {selectedArchetype && archetypeSearchPrompt && (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-gray-700" />
                          <span className="text-xs font-medium" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                            Preview do prompt de busca
                          </span>
                        </div>
                        <span className="text-micro text-gray-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>editável</span>
                      </div>
                      <div className="relative">
                        <textarea
                          value={archetypeSearchPrompt}
                          onChange={(e) => setArchetypeSearchPrompt(e.target.value)}
                          placeholder="Descreva o perfil do arquétipo..."
                          className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-all border"
                          style={{ 
                            backgroundColor: "#FFFFFF",
                            color: "#1a1a1a",
                            fontFamily: "'Open Sans', sans-serif"
                          }}
                          onFocus={(e) => {
                            e.currentTarget.style.borderColor = "#D1D5DB"
                            e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                          }}
                          onBlur={(e) => {
                            e.currentTarget.style.borderColor = "#E5E7EB"
                            e.currentTarget.style.boxShadow = "none"
                          }}
                          rows={2}
                        />
                        {/* Ícones de escopo posicionados absolutamente dentro do textarea */}
                        {onSearchSourceChange && (
                          <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1" style={{ zIndex: 10 }}>
                            <div className="flex items-center gap-1">
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      type="button"
                                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                        searchSource === 'local' 
                                          ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                          : "hover:bg-gray-100"
                                      )}
                                      style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                                    >
                                      <Home className="w-4 h-4" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Seu banco de talentos</p>
                                    <p className="text-xs text-gray-300">Gratuito • Local</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                              
                              {showGlobalSearchOptions && (
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        type="button"
                                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                                        className={cn(
                                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                          searchSource === 'hybrid' 
                                            ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                            : "hover:bg-gray-100"
                                        )}
                                        style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                                      >
                                        <Zap className="w-4 h-4" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                      <p className="text-xs font-medium">Expanda sua busca</p>
                                      <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                                        className={cn(
                                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                          searchSource === 'global' 
                                            ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                            : "hover:bg-gray-100"
                                        )}
                                        style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                                      >
                                        <Globe className="w-4 h-4" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                      <p className="text-xs font-medium">Alcance global</p>
                                      <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              )}
                              
                              {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                              {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                                <>
                                  <TooltipProvider>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <button
                                          type="button"
                                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                          className={cn(
                                            "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                            requireEmails 
                                              ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                              : "hover:bg-gray-100"
                                          )}
                                          style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                                        >
                                          <Mail className="w-3.5 h-3.5" />
                                        </button>
                                      </TooltipTrigger>
                                      <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                        <p className="text-xs font-medium">Apenas com Email</p>
                                        <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                  
                                  <TooltipProvider>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <button
                                          type="button"
                                          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                          className={cn(
                                            "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                            requirePhoneNumbers 
                                              ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                              : "hover:bg-gray-100"
                                          )}
                                          style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                                        >
                                          <Phone className="w-3.5 h-3.5" />
                                        </button>
                                      </TooltipTrigger>
                                      <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                        <p className="text-xs font-medium">Apenas com Telefone</p>
                                        <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                </>
                              )}
                              
                              {/* Botão de busca com hint */}
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      type="button"
                                      onClick={handleSubmit}
                                      disabled={!selectedArchetype || isLoading}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md transition-all",
                                        selectedArchetype ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                                      )}
                                      style={{ color: selectedArchetype ? '#6B7280' : '#D1D5DB' }}
                                    >
                                      {isLoading ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                      ) : (
                                        <Search className="w-4 h-4" />
                                      )}
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Buscar Arquétipo</p>
                                    <p className="text-xs text-gray-300">Encontra perfis similares ao arquétipo</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </div>
                            {/* Hint abaixo dos ícones */}
                            <span className="text-micro text-gray-400 italic">buscar arquétipo</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Search Scope Controls + Search Button - Only show when no archetype selected */}
                  {(!selectedArchetype || !archetypeSearchPrompt) && (
                    <div className="relative">
                      <textarea
                        value={archetypeSearchPrompt}
                        onChange={(e) => setArchetypeSearchPrompt(e.target.value)}
                        placeholder={selectedArchetype ? `Buscar perfis similares a "${selectedArchetype.title}"...` : "Selecione um arquétipo acima para buscar..."}
                        className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[56px] transition-all border"
                        style={{ 
                          backgroundColor: "#FFFFFF",
                          color: "#1a1a1a",
                          fontFamily: "'Open Sans', sans-serif"
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = "#D1D5DB"
                          e.currentTarget.style.boxShadow = "0 0 0 2px rgba(96, 190, 209, 0.12)"
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = "#E5E7EB"
                          e.currentTarget.style.boxShadow = "none"
                        }}
                        rows={2}
                        disabled={!selectedArchetype}
                      />
                      {/* Ícones de escopo posicionados absolutamente dentro do textarea */}
                      {onSearchSourceChange && (
                        <div className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1" style={{ zIndex: 10 }}>
                          <div className="flex items-center gap-1">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onSearchSourceChange('local'); }}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                      searchSource === 'local' 
                                        ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                        : "hover:bg-gray-100"
                                    )}
                                    style={{ color: searchSource === 'local' ? '#5DA47A' : '#6B7280' }}
                                  >
                                    <Home className="w-4 h-4" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Seu banco de talentos</p>
                                  <p className="text-xs text-gray-300">Gratuito • Local</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                            
                            {showGlobalSearchOptions && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button
                                      type="button"
                                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('hybrid'); }}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                        searchSource === 'hybrid' 
                                          ? "bg-[rgba(209,153,96,0.15)] ring-1 ring-wedo-orange" 
                                          : "hover:bg-gray-100"
                                      )}
                                      style={{ color: searchSource === 'hybrid' ? '#D19960' : '#6B7280' }}
                                    >
                                      <Zap className="w-4 h-4" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Expanda sua busca</p>
                                    <p className="text-xs text-gray-300">Local + Global • 1 crédito/candidato</p>
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
                                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSourceChange('global'); }}
                                      className={cn(
                                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                        searchSource === 'global' 
                                          ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20" 
                                          : "hover:bg-gray-100"
                                      )}
                                      style={{ color: searchSource === 'global' ? '#111827' : '#6B7280' }}
                                    >
                                      <Globe className="w-4 h-4" />
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                    <p className="text-xs font-medium">Alcance global</p>
                                    <p className="text-xs text-gray-300">800M+ candidatos • 1 crédito/candidato</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                            
                            {/* Contact Filters: Email, Phone - Only show for global/hybrid searches */}
                            {(searchSource === 'global' || searchSource === 'hybrid') && onRequireEmailsChange && onRequirePhoneNumbersChange && (
                              <>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        type="button"
                                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequireEmailsChange(!requireEmails); }}
                                        className={cn(
                                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                          requireEmails 
                                            ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                            : "hover:bg-gray-100"
                                        )}
                                        style={{ color: requireEmails ? '#5DA47A' : '#9CA3AF' }}
                                      >
                                        <Mail className="w-3.5 h-3.5" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                      <p className="text-xs font-medium">Apenas com Email</p>
                                      <p className="text-xs text-gray-300">{requireEmails ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                                
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <button
                                        type="button"
                                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onRequirePhoneNumbersChange(!requirePhoneNumbers); }}
                                        className={cn(
                                          "flex items-center justify-center p-1.5 rounded-md text-xs transition-all",
                                          requirePhoneNumbers 
                                            ? "bg-[rgba(93,164,122,0.15)] ring-1 ring-wedo-green" 
                                            : "hover:bg-gray-100"
                                        )}
                                        style={{ color: requirePhoneNumbers ? '#5DA47A' : '#9CA3AF' }}
                                      >
                                        <Phone className="w-3.5 h-3.5" />
                                      </button>
                                    </TooltipTrigger>
                                    <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                      <p className="text-xs font-medium">Apenas com Telefone</p>
                                      <p className="text-xs text-gray-300">{requirePhoneNumbers ? 'Ativo (+1 crédito)' : 'Clique para ativar (+1 crédito)'}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </>
                            )}
                            
                            {/* Botão de busca com hint */}
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    type="button"
                                    onClick={handleSubmit}
                                    disabled={!selectedArchetype || isLoading}
                                    className={cn(
                                      "flex items-center justify-center p-1.5 rounded-md transition-all",
                                      selectedArchetype ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                                    )}
                                    style={{ color: selectedArchetype ? '#6B7280' : '#D1D5DB' }}
                                  >
                                    {isLoading ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <Search className="w-4 h-4" />
                                    )}
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="bottom" className="!animate-none" style={{ animation: 'none', transitionDuration: '0ms' }}>
                                  <p className="text-xs font-medium">Buscar Arquétipo</p>
                                  <p className="text-xs text-gray-300">Encontra perfis similares ao arquétipo</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                          {/* Hint abaixo dos ícones */}
                          <span className="text-micro text-gray-400 italic">buscar arquétipo</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Dica contextual compacta */}
                  <div className="px-2 py-1.5 rounded-md bg-gray-50 border border-gray-200">
                    <div className="flex items-center gap-1.5">
                      <Lightbulb className="w-3 h-3 flex-shrink-0 text-gray-700" />
                      <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                        <strong>Dica:</strong> Arquétipos são perfis baseados em contratações bem-sucedidas.
                      </p>
                    </div>
                  </div>
                </>
              )}

              {/* Criar Novo Arquétipo */}
              {archetypeTab === "create" && (
                <div className="space-y-3">
                  {/* Sub-tabs: Vaga Fechada / Descrição */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setArchetypeCreateMode("job")}
                      className={cn(
                        "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-all border border-gray-200",
                        archetypeCreateMode === "job" 
                          ? "bg-gray-100 ring-1 ring-gray-400" 
                          : "bg-white hover:bg-gray-50"
                      )}
                      style={{ color: archetypeCreateMode === "job" ? "#1F2937" : "var(--eleven-text-secondary)" }}
                    >
                      <Briefcase className="w-3.5 h-3.5 inline mr-1.5" />
                      A partir de Vaga
                    </button>
                    <button
                      onClick={() => setArchetypeCreateMode("description")}
                      className={cn(
                        "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-all border border-gray-200",
                        archetypeCreateMode === "description" 
                          ? "bg-gray-100 ring-1 ring-gray-400" 
                          : "bg-white hover:bg-gray-50"
                      )}
                      style={{ color: archetypeCreateMode === "description" ? "#1F2937" : "var(--eleven-text-secondary)" }}
                    >
                      <FileText className="w-3.5 h-3.5 inline mr-1.5" />
                      A partir de Descrição
                    </button>
                  </div>

                  {/* A partir de Vaga */}
                  {archetypeCreateMode === "job" && (
                    <div className="space-y-2">
                      <p className="text-xs" style={{ color: "var(--eleven-text-secondary)", fontFamily: "'Open Sans', sans-serif" }}>
                        Busque por nome ou ID da vaga para criar um arquétipo:
                      </p>
                      
                      {/* Input de busca */}
                      <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: "#999" }} />
                        <input
                          type="text"
                          value={jobSearchQuery}
                          onChange={(e) => {
                            setJobSearchQuery(e.target.value)
                            searchJobsForArchetype(e.target.value)
                          }}
                          placeholder="Buscar vaga por nome ou ID..."
                          className="w-full pl-8 pr-3 py-2 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}
                        />
                        {isSearchingJobs && (
                          <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 animate-spin text-gray-700" />
                        )}
                      </div>

                      {/* Lista de vagas encontradas */}
                      {jobSearchQuery.trim() && (
                        <div className="max-h-[200px] overflow-y-auto space-y-1.5 rounded-md border border-gray-200">
                          {isSearchingJobs ? (
                            <div className="flex items-center justify-center py-4">
                              <Loader2 className="w-4 h-4 animate-spin text-gray-700" />
                              <span className="ml-2 text-xs" style={{ color: "var(--eleven-text-secondary)" }}>
                                Buscando vagas...
                              </span>
                            </div>
                          ) : jobSearchResults.length === 0 ? (
                            <div className="text-center py-4 px-3">
                              <Briefcase className="w-5 h-5 mx-auto mb-1.5" style={{ color: "#ccc" }} />
                              <p className="text-xs" style={{ color: "#999" }}>
                                Nenhuma vaga encontrada para "{jobSearchQuery}"
                              </p>
                            </div>
                          ) : (
                            jobSearchResults.map((job) => (
                              <button
                                key={job.id}
                                onClick={() => openArchetypeFromJob(job)}
                                className="w-full p-2.5 text-left transition-all hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                              >
                                <div className="flex items-start gap-2">
                                  <Briefcase className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-600" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <p className="font-medium text-xs truncate" style={{ color: "#1a1a1a", fontFamily: "'Open Sans', sans-serif" }}>
                                        {job.title}
                                      </p>
                                      <span 
                                        className="px-1.5 py-0.5 rounded-full text-micro font-medium"
                                        style={{ 
                                          backgroundColor: job.status === "Publicada" ? "rgba(34, 197, 94, 0.15)" : 
                                                          job.status === "Encerrada" ? "rgba(156, 163, 175, 0.2)" : 
                                                          "rgba(245, 158, 11, 0.15)",
                                          color: job.status === "Publicada" ? "#16a34a" : 
                                                job.status === "Encerrada" ? "#6B7280" : 
                                                "#D97706"
                                        }}
                                      >
                                        {job.status}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      <span className="text-micro" style={{ color: "#666" }}>
                                        ID: {job.id.slice(0, 8)}...
                                      </span>
                                      {job.department && (
                                        <>
                                          <span className="text-micro" style={{ color: "#ccc" }}>•</span>
                                          <span className="text-micro" style={{ color: "#666" }}>{job.department}</span>
                                        </>
                                      )}
                                      {job.seniority_level && (
                                        <>
                                          <span className="text-micro" style={{ color: "#ccc" }}>•</span>
                                          <span className="text-micro" style={{ color: "#666" }}>{job.seniority_level}</span>
                                        </>
                                      )}
                                    </div>
                                    <p className="text-micro mt-0.5" style={{ color: "#999" }}>
                                      Criada em {new Date(job.created_at).toLocaleDateString('pt-BR')}
                                    </p>
                                    {job.description && (
                                      <p className="text-micro mt-1 line-clamp-2" style={{ color: "#666" }}>
                                        {job.description.slice(0, 120)}{job.description.length > 120 ? "..." : ""}
                                      </p>
                                    )}
                                  </div>
                                  <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "#ccc" }} />
                                </div>
                              </button>
                            ))
                          )}
                        </div>
                      )}

                      {/* Mensagem inicial quando não há busca */}
                      {!jobSearchQuery.trim() && (
                        <div className="text-center py-4 px-3 rounded-md border border-dashed border-gray-200">
                          <Search className="w-5 h-5 mx-auto mb-1.5" style={{ color: "#ccc" }} />
                          <p className="text-xs" style={{ color: "#999" }}>
                            Digite o nome ou ID da vaga para buscar
                          </p>
                        </div>
                      )}
                      
                      {/* Dica contextual padronizada */}
                      <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                          <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                            <strong>Dica:</strong> Selecione uma vaga para preencher automaticamente os dados do arquétipo. Você poderá editar antes de salvar.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* A partir de Descrição */}
                  {archetypeCreateMode === "description" && (
                    <div className="space-y-2">
                      <p className="text-xs" style={{ color: "var(--eleven-text-secondary)", fontFamily: "'Open Sans', sans-serif" }}>
                        Descreva o perfil ideal que deseja buscar:
                      </p>
                      <textarea
                        value={archetypeDescription}
                        onChange={(e) => setArchetypeDescription(e.target.value)}
                        placeholder="Ex: Desenvolvedor Python sênior com experiência em machine learning e cloud AWS, preferencialmente com background em fintechs..."
                        rows={3}
                        className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 resize-none"
                        style={{ 
                          border: "1px solid var(--eleven-border)",
                          backgroundColor: "var(--eleven-bg-main)",
                          color: "var(--eleven-text-primary)"
                        }}
                      />
                      <Button
                        onClick={() => createArchetypeFromDescription(archetypeDescription)}
                        disabled={archetypeDescription.length < 20 || isCreatingArchetype}
                        size="sm"
                        className="w-full"
                        style={{ 
                          backgroundColor: archetypeDescription.length >= 20 ? "#111827" : "var(--eleven-bg-tertiary)",
                          color: archetypeDescription.length >= 20 ? "white" : "var(--eleven-text-secondary)"
                        }}
                      >
                        {isCreatingArchetype ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            Criando...
                          </>
                        ) : (
                          <>
                            <Brain className="w-4 h-4 mr-1 text-wedo-cyan" />
                            Criar Arquétipo com LIA
                          </>
                        )}
                      </Button>
                      
                      {/* Dica contextual padronizada */}
                      <div className="p-2.5 rounded-md bg-gray-50 border border-gray-200">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
                          <p className="text-xs text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                            <strong>Dica:</strong> Descreva o perfil ideal e a LIA vai extrair automaticamente cargo, senioridade e skills para criar o arquétipo.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>


      {mode === "natural" && filledCount === 0 && value.length > 0 && (
        <p 
          className="text-xs px-1"
          style={{ color: "var(--eleven-text-secondary)" }}
        >
          Dica: Inclua cargo, localização e skills para melhores resultados
        </p>
      )}

      {/* Modal de Edição de Arquétipo - Padrão ElevenLabs/WeDo Talent */}
      {editingArchetype && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={closeEditArchetype}
        >
          <div 
            className="bg-white rounded-md w-full max-w-[700px] mx-3 max-h-[85vh] overflow-y-auto"
            style={{ fontFamily: "'Open Sans', sans-serif" }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header - Padrão ElevenLabs */}
            <div className="flex items-center gap-3 px-5 py-4 border-b border border-gray-200">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: "rgba(96, 190, 209, 0.15)" }}
              >
                <Target className="w-5 h-5 text-gray-700" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold" style={{ color: "#1a1a1a" }}>
                  {editingArchetype?.id ? "Editar Arquétipo" : "Criar Arquétipo"}
                </h3>
                <p className="text-xs truncate" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  {editArchetypeName || "Novo perfil de candidato ideal"}
                </p>
              </div>
              <button
                onClick={closeEditArchetype}
                className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="px-5 py-4 space-y-4">
              {/* Seção 1: Identificação - espaçamento reduzido para proporcionalidade */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-base-ui font-semibold text-gray-700">1</span>
                  <h4 className="text-xs font-semibold text-gray-800">Identificação do Arquétipo</h4>
                </div>
                
                {/* Nome e Emoji */}
                <div className="flex gap-2">
                  <div className="w-14">
                    <label className="text-micro font-medium mb-0.5 block text-gray-500">Emoji</label>
                    <input
                      type="text"
                      value={editArchetypeEmoji}
                      onChange={(e) => setEditArchetypeEmoji(e.target.value)}
                      maxLength={4}
                      className="w-full rounded-md px-2 py-1.5 text-center text-base focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-micro font-medium mb-0.5 block text-gray-500">
                      Nome do Arquétipo
                    </label>
                    <input
                      type="text"
                      value={editArchetypeName}
                      onChange={(e) => setEditArchetypeName(e.target.value)}
                      placeholder="Ex: Tech Lead, Product Manager..."
                      className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    />
                  </div>
                </div>

                {/* Query de Busca */}
                <div>
                  <label className="text-micro font-medium mb-0.5 block text-gray-500">
                    Query de Busca
                  </label>
                  <textarea
                    value={editArchetypeQuery}
                    onChange={(e) => setEditArchetypeQuery(e.target.value)}
                    placeholder="Ex: Tech Lead com experiência em gestão de equipes, arquitetura de sistemas, 8+ anos em desenvolvimento"
                    rows={2}
                    className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none border border-gray-200"
                  />
                </div>

                {/* Descrição */}
                <div>
                  <label className="text-micro font-medium mb-0.5 block text-gray-500">Descrição</label>
                  <textarea
                    value={editArchetypeDescription}
                    onChange={(e) => setEditArchetypeDescription(e.target.value)}
                    placeholder="Líder técnico com experiência em gestão de equipes e arquitetura de sistemas"
                    rows={2}
                    className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none border border-gray-200"
                  />
                </div>
              </div>

              {/* Seção 2: Requisitos */}
              <div className="space-y-3 pt-2 border-t border-t-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base-ui font-semibold text-gray-700">2</span>
                  <h4 className="text-xs font-semibold text-gray-800">Requisitos do Perfil</h4>
                </div>
                
                {/* Grid de 2 colunas: (Senioridade + Exp Min) | (Indústria) */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Coluna 1: Senioridade + Experiência */}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs font-medium mb-1 block text-gray-500">Senioridade</label>
                      <select
                        value={editArchetypeSeniority}
                        onChange={(e) => setEditArchetypeSeniority(e.target.value)}
                        className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                      >
                        <option value="">-</option>
                        <option value="junior">Júnior</option>
                        <option value="pleno">Pleno</option>
                        <option value="senior">Sênior</option>
                        <option value="lead">Lead</option>
                        <option value="staff">Staff</option>
                        <option value="principal">Principal</option>
                        <option value="manager">Gerente</option>
                        <option value="director">Diretor</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium mb-1 block text-gray-500">Exp. Mínima</label>
                      <input
                        type="number"
                        min={0}
                        max={30}
                        value={editArchetypeExperienceMin ?? ""}
                        onChange={(e) => setEditArchetypeExperienceMin(e.target.value ? parseInt(e.target.value) : null)}
                        placeholder="Anos"
                        className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                      />
                    </div>
                  </div>
                  
                  {/* Coluna 2: Indústria (searchable dropdown) */}
                  <div className="relative">
                    <label className="text-xs font-medium mb-1 block text-gray-500">Indústria</label>
                  <button
                    type="button"
                    onClick={() => setIsIndustryDropdownOpen(!isIndustryDropdownOpen)}
                    className="w-full rounded px-2 py-1.5 text-xs text-left flex items-center justify-between focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200"
                  >
                    <span style={{ color: editArchetypeIndustry ? "#1a1a1a" : "#999" }}>
                      {editArchetypeIndustry 
                        ? (INDUSTRIES.find(i => i.key === editArchetypeIndustry)?.labelPt || editArchetypeIndustry)
                        : "Selecionar..."}
                    </span>
                    <ChevronDown className="w-3 h-3" style={{ color: "#999" }} />
                  </button>
                  {isIndustryDropdownOpen && (
                    <div className="absolute z-10 mt-1 w-full bg-white rounded-md border border-gray-200 max-h-[200px] overflow-hidden">
                      <div className="p-2 border-b border-gray-100 sticky top-0 bg-white">
                        <input
                          type="text"
                          value={industrySearchQuery}
                          onChange={(e) => setIndustrySearchQuery(e.target.value)}
                          placeholder="Buscar setor..."
                          className="w-full rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200"
                          autoFocus
                        />
                      </div>
                      <div className="max-h-[150px] overflow-y-auto">
                        <button
                          type="button"
                          onClick={() => {
                            setEditArchetypeIndustry("")
                            setIsIndustryDropdownOpen(false)
                            setIndustrySearchQuery("")
                          }}
                          className="w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50"
                          style={{ color: "#999" }}
                        >
                          - Nenhum -
                        </button>
                        {Object.entries(INDUSTRY_CATEGORIES).map(([catKey, catLabel]) => {
                          const categoryIndustries = INDUSTRIES
                            .filter(i => i.category === catKey)
                            .filter(i => 
                              !industrySearchQuery.trim() || 
                              i.labelPt.toLowerCase().includes(industrySearchQuery.toLowerCase()) ||
                              i.key.toLowerCase().includes(industrySearchQuery.toLowerCase())
                            )
                          if (categoryIndustries.length === 0) return null
                          return (
                            <div key={catKey}>
                              <div className="px-3 py-1 text-micro font-semibold uppercase tracking-wide bg-gray-50">
                                {catLabel.labelPt}
                              </div>
                              {categoryIndustries.map(industry => (
                                <button
                                  key={industry.key}
                                  type="button"
                                  onClick={() => {
                                    setEditArchetypeIndustry(industry.key)
                                    setIsIndustryDropdownOpen(false)
                                    setIndustrySearchQuery("")
                                  }}
                                  className={`w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 ${editArchetypeIndustry === industry.key ? "bg-gray-100 dark:bg-gray-800" : ""}`}
                                >
                                  {industry.labelPt}
                                </button>
                              ))}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  </div>
                </div>
                
                {/* Localização e Modelo de Trabalho */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium mb-1 flex items-center gap-1 text-gray-500">
                      <MapPin className="w-3 h-3 text-gray-700" />
                      Localização
                    </label>
                    <input
                      type="text"
                      value={editArchetypeLocation}
                      onChange={(e) => setEditArchetypeLocation(e.target.value)}
                      placeholder="São Paulo, Brasil..."
                      className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium mb-1 flex items-center gap-1 text-gray-500">
                      <Building2 className="w-3 h-3 text-gray-700" />
                      Modelo de Trabalho
                    </label>
                    <select
                      value={editArchetypeWorkModel}
                      onChange={(e) => setEditArchetypeWorkModel(e.target.value)}
                      className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    >
                      <option value="">Qualquer</option>
                      <option value="remote">Remoto</option>
                      <option value="hybrid">Híbrido</option>
                      <option value="onsite">Presencial</option>
                    </select>
                  </div>
                </div>

                {/* Idiomas e Tipo de Contrato */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium mb-1 flex items-center gap-1 text-gray-500">
                      <Globe className="w-3 h-3 text-gray-700" />
                      Idiomas
                    </label>
                    <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-gray-200">
                      {editArchetypeLanguages.map((lang, idx) => (
                        <span 
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                          style={{ backgroundColor: "rgba(96, 190, 209, 0.15)", fontFamily: "'Open Sans', sans-serif" }}
                        >
                          {lang}
                          <button
                            type="button"
                            onClick={() => setEditArchetypeLanguages(prev => prev.filter((_, i) => i !== idx))}
                            className="hover:bg-gray-100 dark:bg-gray-800 rounded-full p-0.5"
                          >
                            <X className="w-3 h-3 text-gray-700" />
                          </button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      value={newLanguageInput}
                      onChange={(e) => setNewLanguageInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newLanguageInput.trim()) {
                          e.preventDefault()
                          if (!editArchetypeLanguages.includes(newLanguageInput.trim())) {
                            setEditArchetypeLanguages(prev => [...prev, newLanguageInput.trim()])
                          }
                          setNewLanguageInput("")
                        }
                      }}
                      placeholder="Inglês, Espanhol..."
                      className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium mb-1 flex items-center gap-1 text-gray-500">
                      <Briefcase className="w-3 h-3 text-gray-600" />
                      Tipo de Contrato
                    </label>
                    <select
                      value={editArchetypeEmploymentType}
                      onChange={(e) => setEditArchetypeEmploymentType(e.target.value)}
                      className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-gray-200"
                    >
                      <option value="">Qualquer</option>
                      <option value="clt">CLT</option>
                      <option value="pj">PJ</option>
                      <option value="intern">Estágio</option>
                      <option value="temporary">Temporário</option>
                      <option value="freelancer">Freelancer</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Seção 3: Competências */}
              <div className="space-y-3 pt-2 border-t border-t-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base-ui font-semibold text-gray-700">3</span>
                  <h4 className="text-xs font-semibold text-gray-800">Competências Técnicas</h4>
                </div>
                
                {/* Skills */}
                <div>
                  <label className="text-xs font-medium mb-1 flex items-center gap-1.5 text-gray-500">
                    <Code className="w-3.5 h-3.5 text-gray-700" />
                    Skills
                    <span className="text-micro font-normal text-gray-400">(habilidades técnicas: Python, React, AWS...)</span>
                  </label>
                <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-gray-200">
                  {editArchetypeSkills.map((skill, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                      style={{ backgroundColor: "rgba(96, 190, 209, 0.15)", fontFamily: "'Open Sans', sans-serif" }}
                    >
                      {skill}
                      <button
                        type="button"
                        onClick={() => setEditArchetypeSkills(prev => prev.filter((_, i) => i !== idx))}
                        className="hover:bg-gray-100 dark:bg-gray-800 rounded-full p-0.5"
                      >
                        <X className="w-3 h-3 text-gray-700" />
                      </button>
                    </span>
                  ))}
                  {editArchetypeSkills.length === 0 && (
                    <span className="text-xs text-gray-400">Nenhuma skill</span>
                  )}
                </div>
                <div className="relative">
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={newSkillInput}
                      onChange={(e) => {
                        setNewSkillInput(e.target.value)
                        if (e.target.value.length >= 2) {
                          searchSemanticSkills(e.target.value, editArchetypeSkills)
                          setShowSkillSuggestions(true)
                        } else {
                          clearSemanticSkillSuggestions()
                          setShowSkillSuggestions(false)
                        }
                      }}
                      onFocus={() => {
                        if (newSkillInput.length >= 2 && semanticSkillSuggestions.length > 0) {
                          setShowSkillSuggestions(true)
                        }
                      }}
                      onBlur={() => {
                        setTimeout(() => setShowSkillSuggestions(false), 200)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newSkillInput.trim()) {
                          e.preventDefault()
                          if (!editArchetypeSkills.includes(newSkillInput.trim())) {
                            setEditArchetypeSkills(prev => [...prev, newSkillInput.trim()])
                          }
                          setNewSkillInput("")
                          clearSemanticSkillSuggestions()
                          setShowSkillSuggestions(false)
                        }
                      }}
                      placeholder="Digite e pressione Enter..."
                      className="flex-1 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}
                    />
                    <button
                      type="button"
                      onClick={async () => {
                        if (editArchetypeSkills.length === 0) return
                        setIsFindingSimilarSkills(true)
                        setAiSuggestedSkills([])
                        setSelectedAiSkills([])
                        try {
                          const response = await fetch('/api/ai/suggest-similar-skills', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ skills: editArchetypeSkills })
                          })
                          if (response.ok) {
                            const data = await response.json()
                            if (data.suggestions?.length > 0) {
                              const newSkills = data.suggestions
                                .filter((s: string) => !editArchetypeSkills.map(sk => sk.toLowerCase()).includes(s.toLowerCase()))
                                .slice(0, 10)
                              setAiSuggestedSkills(newSkills)
                            }
                          }
                        } catch (error) {
                          console.error('Error finding similar skills:', error)
                        } finally {
                          setIsFindingSimilarSkills(false)
                        }
                      }}
                      disabled={editArchetypeSkills.length === 0 || isFindingSimilarSkills}
                      className="px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors disabled:opacity-50"
                      style={{ backgroundColor: editArchetypeSkills.length > 0 ? "rgba(96, 190, 209, 0.15)" : "#F5F5F5", color: editArchetypeSkills.length > 0 ? "#111827" : "#999" }}
                      title="Buscar skills similares com IA"
                    >
                      {isFindingSimilarSkills ? <Loader2 className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3 text-wedo-cyan" />}
                      Similares
                    </button>
                  </div>
                  {showSkillSuggestions && semanticSkillSuggestions.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-[150px] overflow-y-auto">
                      {isLoadingSemanticSkills && (
                        <div className="flex items-center justify-center py-2">
                          <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
                        </div>
                      )}
                      {semanticSkillSuggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-50 transition-colors flex items-center gap-1.5"
                          onMouseDown={(e) => {
                            e.preventDefault()
                            if (!editArchetypeSkills.includes(suggestion.term)) {
                              setEditArchetypeSkills(prev => [...prev, suggestion.term])
                            }
                            setNewSkillInput("")
                            clearSemanticSkillSuggestions()
                            setShowSkillSuggestions(false)
                          }}
                        >
                          <Code className="w-3 h-3 text-gray-400" />
                          <span style={{ color: "#1a1a1a" }}>{suggestion.term}</span>
                          {suggestion.is_synonym && (
                            <span className="text-micro px-1 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">sinônimo</span>
                          )}
                          {suggestion.is_related && (
                            <span className="text-micro px-1 py-0.5 rounded-full bg-green-50 text-green-600">relacionado</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {aiSuggestedSkills.length > 0 && (
                  <div className="mt-2 p-2 rounded-md" style={{ backgroundColor: "rgba(96, 190, 209, 0.08)", border: "1px solid rgba(96, 190, 209, 0.3)" }}>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      <span className="text-micro font-medium text-gray-700">Sugestões de IA</span>
                      <button
                        type="button"
                        onClick={() => {
                          setAiSuggestedSkills([])
                          setSelectedAiSkills([])
                        }}
                        className="ml-auto p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                      >
                        <X className="w-3 h-3 text-gray-700" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {aiSuggestedSkills.map((skill, idx) => {
                        const isSelected = selectedAiSkills.includes(skill)
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setSelectedAiSkills(prev => prev.filter(s => s !== skill))
                              } else {
                                setSelectedAiSkills(prev => [...prev, skill])
                              }
                            }}
                            className={cn(
                              "px-1.5 py-0.5 rounded-full text-micro transition-all cursor-pointer text-wedo-cyan-dark",
                              isSelected ? "ring-2 ring-gray-900/20" : ""
                            )}
                            style={{ 
                              backgroundColor: isSelected ? "rgba(96, 190, 209, 0.25)" : "rgba(96, 190, 209, 0.15)"
                            }}
                          >
                            {skill}
                          </button>
                        )
                      })}
                    </div>
                    {selectedAiSkills.length > 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditArchetypeSkills(prev => [...prev, ...selectedAiSkills.filter(s => !prev.includes(s))])
                          setAiSuggestedSkills(prev => prev.filter(s => !selectedAiSkills.includes(s)))
                          setSelectedAiSkills([])
                        }}
                        className="mt-2 w-full py-1 rounded text-micro font-medium transition-colors bg-gray-900" style={{ color: "white" }}
                      >
                        Adicionar {selectedAiSkills.length} Selecionado{selectedAiSkills.length > 1 ? 's' : ''}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Tags */}
              <div>
                <label className="text-xs font-medium mb-1 flex items-center gap-1.5 text-gray-500">
                  <Tag className="w-3.5 h-3.5 text-gray-700" />
                  Tags
                  <span className="text-micro font-normal text-gray-400">(categorias: liderança, estratégia, backend...)</span>
                </label>
                <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-gray-200">
                  {editArchetypeTags.map((tag, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                      style={{ fontFamily: "'Open Sans', sans-serif" }}
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => setEditArchetypeTags(prev => prev.filter((_, i) => i !== idx))}
                        className="hover:bg-gray-300 rounded-full p-0.5"
                      >
                        <X className="w-3 h-3 text-gray-500" />
                      </button>
                    </span>
                  ))}
                  {editArchetypeTags.length === 0 && (
                    <span className="text-xs text-gray-400">Nenhuma tag</span>
                  )}
                </div>
                <div className="relative">
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={newTagInput}
                      onChange={(e) => {
                        setNewTagInput(e.target.value)
                        if (e.target.value.length >= 2) {
                          searchSemanticTags(e.target.value, editArchetypeTags)
                          setShowTagSuggestions(true)
                        } else {
                          clearSemanticTagSuggestions()
                          setShowTagSuggestions(false)
                        }
                      }}
                      onFocus={() => {
                        if (newTagInput.length >= 2 && semanticTagSuggestions.length > 0) {
                          setShowTagSuggestions(true)
                        }
                      }}
                      onBlur={() => {
                        setTimeout(() => setShowTagSuggestions(false), 200)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newTagInput.trim()) {
                          e.preventDefault()
                          if (!editArchetypeTags.includes(newTagInput.trim())) {
                            setEditArchetypeTags(prev => [...prev, newTagInput.trim()])
                          }
                          setNewTagInput("")
                          clearSemanticTagSuggestions()
                          setShowTagSuggestions(false)
                        }
                      }}
                      placeholder="Digite e pressione Enter..."
                      className="flex-1 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}
                    />
                    <button
                      type="button"
                      onClick={async () => {
                        if (editArchetypeTags.length === 0) return
                        setIsFindingSimilarTags(true)
                        setAiSuggestedTags([])
                        setSelectedAiTags([])
                        try {
                          const response = await fetch('/api/ai/suggest-similar-skills', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ skills: editArchetypeTags })
                          })
                          if (response.ok) {
                            const data = await response.json()
                            if (data.suggestions?.length > 0) {
                              const newTags = data.suggestions
                                .filter((s: string) => !editArchetypeTags.map(t => t.toLowerCase()).includes(s.toLowerCase()))
                                .slice(0, 10)
                              setAiSuggestedTags(newTags)
                            }
                          }
                        } catch (error) {
                          console.error('Error finding similar tags:', error)
                        } finally {
                          setIsFindingSimilarTags(false)
                        }
                      }}
                      disabled={editArchetypeTags.length === 0 || isFindingSimilarTags}
                      className="px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors disabled:opacity-50"
                      style={{ backgroundColor: editArchetypeTags.length > 0 ? "rgba(96, 190, 209, 0.15)" : "#F5F5F5", color: editArchetypeTags.length > 0 ? "#111827" : "#999" }}
                      title="Buscar tags similares com IA"
                    >
                      {isFindingSimilarTags ? <Loader2 className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3 text-wedo-cyan" />}
                      Similares
                    </button>
                  </div>
                  {showTagSuggestions && semanticTagSuggestions.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-[150px] overflow-y-auto">
                      {isLoadingSemanticTags && (
                        <div className="flex items-center justify-center py-2">
                          <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
                        </div>
                      )}
                      {semanticTagSuggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-50 transition-colors flex items-center gap-1.5"
                          onMouseDown={(e) => {
                            e.preventDefault()
                            if (!editArchetypeTags.includes(suggestion.term)) {
                              setEditArchetypeTags(prev => [...prev, suggestion.term])
                            }
                            setNewTagInput("")
                            clearSemanticTagSuggestions()
                            setShowTagSuggestions(false)
                          }}
                        >
                          <Tag className="w-3 h-3 text-gray-400" />
                          <span style={{ color: "#1a1a1a" }}>{suggestion.term}</span>
                          {suggestion.is_synonym && (
                            <span className="text-micro px-1 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">sinônimo</span>
                          )}
                          {suggestion.is_related && (
                            <span className="text-micro px-1 py-0.5 rounded-full bg-green-50 text-green-600">relacionado</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {aiSuggestedTags.length > 0 && (
                  <div className="mt-2 p-2 rounded-md" style={{ backgroundColor: "rgba(96, 190, 209, 0.08)", border: "1px solid rgba(96, 190, 209, 0.3)" }}>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      <span className="text-micro font-medium text-gray-700">Sugestões de IA</span>
                      <button
                        type="button"
                        onClick={() => {
                          setAiSuggestedTags([])
                          setSelectedAiTags([])
                        }}
                        className="ml-auto p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                      >
                        <X className="w-3 h-3 text-gray-700" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {aiSuggestedTags.map((tag, idx) => {
                        const isSelected = selectedAiTags.includes(tag)
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setSelectedAiTags(prev => prev.filter(t => t !== tag))
                              } else {
                                setSelectedAiTags(prev => [...prev, tag])
                              }
                            }}
                            className={cn(
                              "px-1.5 py-0.5 rounded-full text-micro transition-all cursor-pointer text-wedo-cyan-dark",
                              isSelected ? "ring-2 ring-gray-900/20" : ""
                            )}
                            style={{ 
                              backgroundColor: isSelected ? "rgba(96, 190, 209, 0.25)" : "rgba(96, 190, 209, 0.15)"
                            }}
                          >
                            {tag}
                          </button>
                        )
                      })}
                    </div>
                    {selectedAiTags.length > 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditArchetypeTags(prev => [...prev, ...selectedAiTags.filter(t => !prev.includes(t))])
                          setAiSuggestedTags(prev => prev.filter(t => !selectedAiTags.includes(t)))
                          setSelectedAiTags([])
                        }}
                        className="mt-2 w-full py-1 rounded text-micro font-medium transition-colors bg-gray-900" style={{ color: "white" }}
                      >
                        Adicionar {selectedAiTags.length} Selecionado{selectedAiTags.length > 1 ? 's' : ''}
                      </button>
                    )}
                  </div>
                )}
              </div>
              </div>

            </div>

            {/* Footer - Padrão ElevenLabs */}
            <div className="flex items-center justify-between px-5 py-4 border-t bg-gray-50">
              <p className="text-xs text-gray-500">
                Campos obrigatórios: Nome e Query
              </p>
              <div className="flex gap-2">
                <button
                  onClick={closeEditArchetype}
                  className="px-4 py-2 rounded-md text-xs font-medium transition-colors hover:bg-gray-200 border border-gray-200" style={{ backgroundColor: "transparent" }}
                >
                  Cancelar
                </button>
                <button
                  onClick={saveArchetype}
                  disabled={isSavingArchetype || !editArchetypeName || !editArchetypeQuery}
                  className="px-4 py-2 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  style={{ 
                    backgroundColor: editArchetypeName && editArchetypeQuery ? "#1F2937" : "#E5E7EB",
                    color: editArchetypeName && editArchetypeQuery ? "white" : "#9CA3AF"
                  }}
                >
                  {isSavingArchetype ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      {editingArchetype?.id ? "Salvando..." : "Criando..."}
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      {editingArchetype?.id ? "Salvar" : "Criar Arquétipo"}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent 
          className="sm:max-w-[320px] w-[85vw] p-4 rounded-md border" 
          style={{ backgroundColor: 'var(--gray-50)', fontFamily: '"Open Sans", sans-serif' }}
        >
          <AlertDialogTitle className="sr-only">
            {pendingSourceChange === 'hybrid' ? 'Ativar Busca Híbrida' : 'Ativar Busca Global'}
          </AlertDialogTitle>
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: pendingSourceChange === 'hybrid' ? 'rgba(96, 190, 209, 0.15)' : 'rgba(217, 119, 6, 0.15)' }}
              >
                {pendingSourceChange === 'hybrid' ? (
                  <Zap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                ) : (
                  <Globe className="w-4 h-4 text-amber-600" />
                )}
              </div>
              <div>
                <h3 className="font-semibold text-base-ui text-gray-800">
                  {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
                </h3>
                <p className="text-micro text-gray-500">
                  {pendingSourceChange === 'hybrid' 
                    ? 'Combina base local + global (800M+ perfis).'
                    : 'Acessa 800M+ perfis profissionais.'}
                </p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-md p-3 space-y-2 border border-gray-100">
              {pendingSourceChange === 'hybrid' && (
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Local:</span>
                  <span className="font-medium text-emerald-600">Grátis</span>
                </div>
              )}
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Global:</span>
                <span className="font-medium text-amber-600">1 cr/candidato</span>
              </div>
              <div className="flex justify-between text-xs pt-2 border-t border-gray-200">
                <span className="font-medium text-gray-800 dark:text-gray-200">Total estimado:</span>
                <span className="font-semibold text-amber-600">1 cr/candidato</span>
              </div>
            </div>
            
            <div className="flex gap-2.5 pt-1">
              <button
                onClick={() => {
                  setShowSourceChangeModal(false)
                  setPendingSourceChange(null)
                }}
                className="flex-1 h-8 text-xs px-3 rounded-md bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSourceChange}
                className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors hover:opacity-90 bg-gray-900"
              >
                {pendingSourceChange === 'hybrid' ? (
                  <>
                    <Zap className="w-3.5 h-3.5" />
                    Ativar
                  </>
                ) : (
                  <>
                    <Globe className="w-3.5 h-3.5" />
                    Ativar
                  </>
                )}
              </button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default SmartSearchInput
