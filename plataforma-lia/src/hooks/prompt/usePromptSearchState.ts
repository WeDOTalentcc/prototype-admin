"use client"

import { useState, useCallback, useEffect } from "react"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchTab, PromptSearchSource as SearchSource } from "@/hooks/ui/usePromptState"

export interface UsePromptSearchStateReturn {
  showGlobalSearchOptions: boolean
  isExpanded: boolean
  setIsExpanded: (v: boolean) => void
  showPremiumAutocomplete: boolean
  setShowPremiumAutocomplete: (v: boolean) => void
  inputValue: string
  setInputValue: (v: string) => void
  isListening: boolean
  setIsListening: (v: boolean) => void
  isProcessing: boolean
  setIsProcessing: (v: boolean) => void
  lastCommand: string
  setLastCommand: (v: string) => void
  commandHistory: string[]
  setCommandHistory: React.Dispatch<React.SetStateAction<string[]>>
  showHistory: boolean
  setShowHistory: (v: boolean) => void
  showBooleanMode: boolean
  setShowBooleanMode: (v: boolean) => void
  naturalSearchValue: string
  setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  booleanSearchValue: string
  setBooleanSearchValue: (v: string) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (v: SearchTab) => void
  jobDescriptionText: string
  setJobDescriptionText: (v: string) => void
  selectedArquetipo: string | null
  setSelectedArquetipo: (v: string | null) => void
  similarProfileUrl: string
  setSimilarProfileUrl: (v: string) => void
  searchSource: SearchSource
  setSearchSource: (v: SearchSource) => void
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  setPendingSourceChange: (v: 'hybrid' | 'global' | null) => void
  pearchSearchType: 'fast'
  setPearchSearchType: (v: 'fast') => void
  candidateLimit: number
  setCandidateLimit: (v: number) => void
  requireEmails: boolean
  setRequireEmails: (v: boolean) => void
  requirePhoneNumbers: boolean
  setRequirePhoneNumbers: (v: boolean) => void
  filterLocation: string
  setFilterLocation: (v: string) => void
  filterExperience: string
  setFilterExperience: (v: string) => void
  filterSeniority: string
  setFilterSeniority: (v: string) => void
  filterWorkModel: string
  setFilterWorkModel: (v: string) => void
  showAdvancedFiltersModal: boolean
  setShowAdvancedFiltersModal: (v: boolean) => void
  advancedFilters: SearchFilters
  setAdvancedFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  handleSourceChange: (newSource: 'local' | 'hybrid' | 'global') => void
  confirmSourceChange: () => void
}

export function usePromptSearchState(forceExpanded = false): UsePromptSearchStateReturn {
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

  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])

  const handleSourceChange = useCallback((newSource: 'local' | 'hybrid' | 'global') => {
    if (newSource === 'local') {
      setSearchSource('local')
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }, [])

  const confirmSourceChange = useCallback(() => {
    if (pendingSourceChange) {
      setSearchSource(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }, [pendingSourceChange])

  return {
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
    filterLocation, setFilterLocation,
    filterExperience, setFilterExperience,
    filterSeniority, setFilterSeniority,
    filterWorkModel, setFilterWorkModel,
    showAdvancedFiltersModal, setShowAdvancedFiltersModal,
    advancedFilters, setAdvancedFilters,
    handleSourceChange,
    confirmSourceChange,
  }
}
