"use client"

import { useState, useRef } from "react"
import { Brain, Users, FileText, Binary, Target, MapPin, Briefcase, Clock, Building2, Code } from "lucide-react"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import { useSemanticSearch } from "@/hooks/search/useSemanticSearch"
import { useSmartSearchArchetypes } from "./useSmartSearchArchetypes"
import { useSmartSearchSimilar } from "./useSmartSearchSimilar"
import {
  type ParsedEntities,
  type SearchSource,
  type SmartSearchInputProps,
  type SearchMode,
  type SearchAnalysis,
  type AutocompleteItem,
  type SearchTag,
} from "./smartSearchConstants"

export interface PromptEnhancementData {
  enhanced_query: string
  explanation: string
  confidence: number
  suggestions?: Array<{ label: string; value: string; category: string }>
}

export interface VacancyResult {
  id: string
  job_id: string | null
  title: string
  status: string
  created_at: string
  description_preview: string | null
}

export interface SelectedVacancy {
  id: string
  title: string
  job_id: string | null
}

export function useSearchState(props: SmartSearchInputProps) {
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
  const [promptEnhancement, setPromptEnhancement] = useState<PromptEnhancementData | null>(null)
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [promptEnhancementDismissed, setPromptEnhancementDismissed] = useState(false)
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [jdVacancySearch, setJdVacancySearch] = useState("")
  const [jdVacancyResults, setJdVacancyResults] = useState<VacancyResult[]>([])
  const [isSearchingVacancies, setIsSearchingVacancies] = useState(false)
  const [selectedVacancy, setSelectedVacancy] = useState<SelectedVacancy | null>(null)
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

  const archetypes = useSmartSearchArchetypes()
  const similar = useSmartSearchSimilar()

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

  const tags: SearchTag[] = [
    { key: "location", label: "Localização", icon: MapPin, filled: !!entities.location, value: entities.location },
    { key: "job_title", label: "Cargo", icon: Briefcase, filled: !!entities.job_title, value: entities.job_title },
    { key: "years_experience", label: "Experiência", icon: Clock, filled: !!entities.years_experience, value: entities.years_experience },
    { key: "industry", label: "Setor", icon: Building2, filled: !!entities.industry, value: entities.industry },
    { key: "skills", label: "Habilidades", icon: Code, filled: !!(entities.skills && entities.skills.length > 0), value: entities.skills?.join(", ") }
  ]

  const filledCount = tags.filter(t => t.filled).length

  const modes: { key: SearchMode; label: string; icon: React.ElementType }[] = [
    { key: "natural", label: "Linguagem Natural", icon: Brain },
    { key: "similar", label: "Similar", icon: Users },
    { key: "jd", label: "Descrição da Vaga", icon: FileText },
    { key: "boolean", label: "Boolean", icon: Binary },
    { key: "archetypes", label: "Arquétipos", icon: Target }
  ]

  return {
    value, onChange, onSubmit, onCancel, onOpenFilters, onGoToResults,
    isLoading, placeholder, className, activeFiltersCount,
    searchSource, onSearchSourceChange, requireEmails, onRequireEmailsChange,
    requirePhoneNumbers, onRequirePhoneNumbersChange,
    showGlobalSearchOptions,
    mode, setMode, entities, setEntities, isParsingEntities, setIsParsingEntities,
    booleanError, setBooleanError, jdContent, setJdContent,
    searchAnalysis, setSearchAnalysis, isAnalyzing, setIsAnalyzing,
    showAssistantTip, setShowAssistantTip,
    autocompleteItems, setAutocompleteItems, showAutocomplete, setShowAutocomplete,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    usedAutocompleteTerms, setUsedAutocompleteTerms,
    autocompleteEnabled, setAutocompleteEnabled,
    promptEnhancement, setPromptEnhancement,
    isEnhancingPrompt, setIsEnhancingPrompt,
    promptEnhancementDismissed, setPromptEnhancementDismissed,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    jdVacancySearch, setJdVacancySearch,
    jdVacancyResults, setJdVacancyResults,
    isSearchingVacancies, setIsSearchingVacancies,
    selectedVacancy, setSelectedVacancy,
    showVacancyResults, setShowVacancyResults,
    jdSearchPrompt, setJdSearchPrompt,
    booleanFinalPrompt, setBooleanFinalPrompt,
    jdVacancySearchTimeoutRef, dismissedQueryRef, enhanceTimeoutRef,
    panelWidth, textareaRef, ghostOverlayRef,
    parseTimeoutRef, analyzeTimeoutRef,
    autocompleteTimeoutRef, autocompleteAbortRef, autocompleteCache,
    fileInputRef, cvFileInputRef, containerRef,
    archetypes, similar,
    semanticSkillSuggestions, isLoadingSemanticSkills, searchSemanticSkills, clearSemanticSkillSuggestions,
    semanticTagSuggestions, isLoadingSemanticTags, searchSemanticTags, clearSemanticTagSuggestions,
    tags, filledCount, modes,
  }
}

export type SearchStateReturn = ReturnType<typeof useSearchState>
