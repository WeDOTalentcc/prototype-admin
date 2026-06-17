"use client"

import React, { useState, useMemo, useRef, useCallback } from "react"
import {
  MapPin, Briefcase, Clock, Building2, Code
} from "lucide-react"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import { useEAPCallbacks } from "./useEAPCallbacks"
import { useEAPEffects } from "./useEAPEffects"
import { toast } from "sonner"

interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
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
  query?: string
  emoji?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown> & { query?: string }
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
  selectedCandidates: Record<string, unknown>[]
  onCommand: (command: string, action: string) => void
  filteredCount: number
  totalCount: number
  forceExpanded?: boolean
  candidateContext?: Record<string, unknown>
  onClose?: () => void
  contextPill?: ContextPillData
  quickActions?: Array<{ id: string; label: string; icon?: React.ReactNode; action?: string }>
  jobContext?: JobContext
  pageContext?: 'candidates' | 'jobs'
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

export const CONTEXT_COLORS: Record<string, {
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
    border: 'var(--lia-text-tertiary)',
    bg: 'var(--lia-bg-secondary)',
    headerText: 'var(--lia-text-secondary)',
    headerBg: 'var(--lia-bg-secondary)'
  }
}

export function useExpandableAIPromptCore(props: ExpandableAIPromptProps) {
  const {

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

  } = props
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
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
  
  type SearchTab = 'natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
  type SearchSource = 'local' | 'global' | 'hybrid'
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('natural')
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [selectedArquetipo, setSelectedArquetipo] = useState<string | null>(null)
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")
  
  const [searchSource, setSearchSource] = useState<SearchSource>('local')
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [pearchSearchType, setPearchSearchType] = useState<'fast'>('fast')
  const [candidateLimit, setCandidateLimit] = useState(15)
  
  const [requireEmails, setRequireEmails] = useState(false)
  const [requirePhoneNumbers, setRequirePhoneNumbers] = useState(false)
  
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
    ppiOptions: {}, general: {}, locations: {}, job: {}, company: {}, skills: {}, education: {}, languages: {}
  } as SearchFilters)
  
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
  const [savedTemplates, setSavedTemplates] = useState<Record<string, unknown>[]>([])

  const callbacks = useEAPCallbacks({
    parseEntitiesFromQuery: async () => {},
    parsedEntities,
    advancedFilters: advancedFilters as any,
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
    isExpanded,
    templateSuggestions: {} as Record<string, unknown>,
    suggestionQueue: {} as Record<string, unknown>,
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
  })

  const effects = useEAPEffects({
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
    fetchPromptEnhancement: callbacks.fetchPromptEnhancement,
    handleSubmit: callbacks.handleSubmit,
  })

  const filteredArchetypes = useMemo(() => {
    if (!archetypeSearchFilter.trim()) return archetypes
    const filter = archetypeSearchFilter.toLowerCase()
    return archetypes.filter(a => 
      (a.name || '').toLowerCase().includes(filter) ||
      (a.department || '').toLowerCase().includes(filter) ||
      (a.hired_candidate?.name || '').toLowerCase().includes(filter)
    )
  }, [archetypes, archetypeSearchFilter])
  
  const searchTags = useMemo(() => [
    { key: "location" as const, label: "Localização", icon: MapPin, filled: !!parsedEntities.location, value: parsedEntities.location },
    { key: "job_title" as const, label: "Cargo", icon: Briefcase, filled: !!parsedEntities.job_title, value: parsedEntities.job_title },
    { key: "years_experience" as const, label: "Experiência", icon: Clock, filled: !!parsedEntities.years_experience, value: parsedEntities.years_experience },
    { key: "industry" as const, label: "Setor", icon: Building2, filled: !!parsedEntities.industry, value: parsedEntities.industry },
    { key: "skills" as const, label: "Habilidades", icon: Code, filled: !!(parsedEntities.skills && parsedEntities.skills.length > 0), value: parsedEntities.skills?.join(", ") }
  ], [parsedEntities])
  
  const filledTagsCount = useMemo(() => searchTags.filter(t => t.filled).length, [searchTags])
  
  const getTagColors = React.useCallback((key: string, filled: boolean) => {
    if (!filled) return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-tertiary)', iconBg: 'var(--lia-text-tertiary)', iconBgLight: 'var(--lia-bg-secondary)' }
    switch (key) {
      case 'job_title':
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-secondary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
      case 'location':
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--wedo-purple)', iconBg: 'var(--wedo-purple)', iconBgLight: 'var(--wedo-purple-bg-10)' }
      case 'skills':
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--status-success)', iconBg: 'var(--wedo-green-light)', iconBgLight: 'var(--wedo-green-bg-10)' }
      case 'years_experience':
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--status-warning)', iconBg: 'var(--wedo-orange)', iconBgLight: 'var(--wedo-orange-bg-15)' }
      case 'industry':
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-secondary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
      default:
        return { bg: 'var(--lia-bg-secondary)', text: 'var(--lia-text-secondary)', iconBg: 'var(--lia-text-secondary)', iconBgLight: 'var(--lia-bg-secondary)' }
    }
  }, [])

  const suggestions = callbacks.getSmartSuggestions()
  const statusInfo = effects.getStatusInfo(selectedCandidates, filteredCount, totalCount)

  return {
    MAX_CV_FILES,
    searchTags,
    suggestions,
    MAX_SIMILAR_URLS,
    activeSearchTab,
    addSimilarUrl: callbacks.addSimilarUrl,
    advancedFilters,
    analyzeProfiles: callbacks.analyzeProfiles,
    archetypeSearchFilter,
    archetypeToDelete,
    archetypes,
    autocompleteEnabled,
    autocompleteSuggestions,
    booleanSearchValue,
    buildSearchSpecFromEntities: callbacks.buildSearchSpecFromEntities,
    canSaveAsArchetype: callbacks.canSaveAsArchetype,
    candidateContext,
    candidateLimit,
    closeEditArchetype: callbacks.closeEditArchetype,
    combinedSuggestions,
    commandHistory,
    confirmDeleteArchetype: callbacks.confirmDeleteArchetype,
    confirmSourceChange: callbacks.confirmSourceChange,
    contextPill,
    createArchetypeFromActiveSearch: callbacks.createArchetypeFromActiveSearch,
    createArchetypeFromDescription: callbacks.createArchetypeFromDescription,
    creditEstimate: effects.creditEstimate,
    cvFileInputRef,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeTags,
    editingArchetype,
    executeSearchWithCriteria: callbacks.executeSearchWithCriteria,
    extractionTimeoutRef: effects.extractionTimeoutRef,
    fetchAutocomplete: callbacks.fetchAutocomplete,
    filledTagsCount,
    filteredArchetypes,
    getPlaceholder: callbacks.getPlaceholder,
    getTagColors,
    handleAcceptEnhancement: callbacks.handleAcceptEnhancement,
    handleArchetypeSaved: callbacks.handleArchetypeSaved,
    handleAudioTranscription: callbacks.handleAudioTranscription,
    handleAutocompleteKeyDown: callbacks.handleAutocompleteKeyDown,
    handleCvUpload: callbacks.handleCvUpload,
    handleDismissEnhancement: callbacks.handleDismissEnhancement,
    handleFileAnalyzed: callbacks.handleFileAnalyzed,
    handleHistoryCommand: callbacks.handleHistoryCommand,
    handlePremiumAutocompleteSelect: callbacks.handlePremiumAutocompleteSelect,
    handleSourceChange: callbacks.handleSourceChange,
    handleSubmit: callbacks.handleSubmit,
    handleSuggestionClick: callbacks.handleSuggestionClick,
    hasMultipleSources: callbacks.hasMultipleSources,
    hasParsedEntities: callbacks.hasParsedEntities,
    inputValue,
    isAnalyzingProfiles,
    isCreatingArchetype,
    isCreatingFromSearch,
    isDeletingArchetype,
    isEnhancingPrompt,
    isExpanded,
    isListening,
    isParsingEntities,
    isProcessing,
    isSavingArchetype,
    jobContext,
    jobDescriptionText,
    lastCommand,
    naturalSearchValue,
    newArchetypeDescription,
    newTagInput,
    onClose,
    onCommand,
    openDeleteArchetypeDialog: callbacks.openDeleteArchetypeDialog,
    openEditArchetype: callbacks.openEditArchetype,
    pageContext,
    parseEntitiesFromQuery: callbacks.parseEntitiesFromQueryCb,
    parsedEntities,
    pearchSearchType,
    pendingSourceChange,
    promptEnhancement,
    quickActions,
    removeCvFile: callbacks.removeCvFile,
    removeSimilarUrl: callbacks.removeSimilarUrl,
    removeSuggestion: callbacks.removeSuggestion,
    requireEmails,
    requirePhoneNumbers,
    saveArchetype: callbacks.saveArchetype,
    searchAnalysis,
    searchSource,
    selectedAutocompleteIndex,
    selectedCandidates,
    setActiveSearchTab,
    setAdvancedFilters,
    setArchetypeSearchFilter,
    setArchetypeToDelete,
    setAutocompleteEnabled,
    setBooleanSearchValue,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeTags,
    setInputValue,
    setIsExpanded,
    setJobDescriptionText,
    setNaturalSearchValue,
    setNewArchetypeDescription,
    setNewTagInput,
    setPendingSourceChange,
    setRequireEmails,
    setRequirePhoneNumbers,
    setSearchSource,
    setSelectedArquetipo,
    setShowAdvancedFiltersModal,
    setShowAutocomplete,
    setShowDeleteArchetypeDialog,
    setShowHistory,
    setShowPremiumAutocomplete,
    setShowSaveArchetypeModal,
    setShowSourceChangeModal,
    showAdvancedFiltersModal,
    showAutocomplete,
    showCombinedSuggestions,
    showDeleteArchetypeDialog,
    showGlobalSearchOptions,
    showHistory,
    showPremiumAutocomplete,
    showSaveArchetypeModal,
    showSourceChangeModal,
    similarCvFiles,
    similarUrls,
    statusInfo,
    suggestionQueue: effects.suggestionQueue,
    templateSuggestions: effects.templateSuggestions,
    updateSimilarUrl: callbacks.updateSimilarUrl,
  }
}
