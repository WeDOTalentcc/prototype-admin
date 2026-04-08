"use client"

import { useState, useCallback, useEffect, useMemo, useRef } from "react"
import {
  Settings, Briefcase, Building2, Code, GraduationCap,
  Globe, Search, Zap, UserCheck
} from "lucide-react"
import { calculateCreditsLocally, CreditEstimate } from "@/lib/api/candidate-search"
import type {
  SaveDestination,
  SearchSource,
  SearchFilters,
} from "../advancedFiltersTypes"
import { normalizeFiltersFromServer } from "../advancedFiltersUtils"

export type { SaveDestination, SearchSource, SearchFilters }
export { convertToPearchFilters } from "../advancedFiltersUtils"
export { normalizeFiltersFromServer } from "../advancedFiltersUtils"
export type { HideViewedScope, HideViewedPeriod } from "../advancedFiltersTypes"

interface AdvancedFiltersModalProps {
  isOpen: boolean
  onClose: () => void
  onApply: (filters: SearchFilters, options?: { searchSource?: SearchSource }) => void
  onSave?: (filters: SearchFilters, destination: SaveDestination) => void
  initialFilters?: SearchFilters
  estimatedMatches?: number
  candidateLimit?: number
  defaultSaveDestination?: SaveDestination
  sortBy?: string
  onSortByChange?: (value: string) => void
}

export function useAdvancedFiltersCore(props: AdvancedFiltersModalProps) {
  const {
    isOpen,
    onClose,
    onApply,
    onSave,
    initialFilters = {},
    estimatedMatches,
    candidateLimit = 15,
    defaultSaveDestination = "search_history",
    sortBy = 'relevance',
    onSortByChange
  } = props
  const [filters, setFilters] = useState<SearchFilters>(initialFilters)
  const [saveDestination, setSaveDestination] = useState<SaveDestination>(defaultSaveDestination)
  const [isDestinationOpen, setIsDestinationOpen] = useState(false)
  const [searchSource, setSearchSource] = useState<SearchSource>("local")
  const isLocalSearch = searchSource === "local"
  const [showCreditConfirm, setShowCreditConfirm] = useState(false)
  const [pendingSearch, setPendingSearch] = useState<(() => void) | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [activeSection, setActiveSection] = useState<string>("searchSource")

  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({
    searchSource: null,
    ppiOptions: null,
    general: null,
    profile: null,
    job: null,
    company: null,
    skills: null,
    education: null,
    languages: null
  })

  const sidebarCategories = [
    { key: "searchSource", label: "Origem da Busca", icon: Search },
    { key: "ppiOptions", label: "Opções de Busca", icon: Settings },
    { key: "general", label: "Geral", icon: Settings },
    { key: "profile", label: "Perfil Profissional", icon: UserCheck },
    { key: "job", label: "Cargo", icon: Briefcase },
    { key: "company", label: "Empresa", icon: Building2 },
    { key: "skills", label: "Habilidades", icon: Code },
    { key: "education", label: "Formação", icon: GraduationCap },
    { key: "languages", label: "Idiomas", icon: Globe },
  ]

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const observers: IntersectionObserver[] = []
    const visibleSections = new Set<string>()

    Object.keys(sectionRefs.current).forEach((sectionKey) => {
      const element = sectionRefs.current[sectionKey]
      if (!element) return

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              visibleSections.add(sectionKey)
            } else {
              visibleSections.delete(sectionKey)
            }
            const orderedSections = sidebarCategories.map(c => c.key)
            for (const section of orderedSections) {
              if (visibleSections.has(section)) {
                setActiveSection(section)
                break
              }
            }
          })
        },
        {
          root: container,
          rootMargin: "-20% 0px -70% 0px",
          threshold: 0
        }
      )

      observer.observe(element)
      observers.push(observer)
    })

    return () => {
      observers.forEach((observer) => observer.disconnect())
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- sidebarCategories is a stable constant defined inline
  }, [isOpen])

  const scrollToSection = useCallback((sectionKey: string) => {
    const element = sectionRefs.current[sectionKey]
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      const normalizedFilters = normalizeFiltersFromServer(initialFilters as Record<string, unknown>)
      setFilters(normalizedFilters)
    }
  }, [isOpen, initialFilters])

  const updateFilter = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string | string[] | number | boolean | null
  ) => {
    setFilters(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
  }, [])

  const addToArray = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => {
    if (!value.trim()) return
    setFilters(prev => {
      const categoryObj = prev[category] as Record<string, unknown> | undefined
      const currentArray = (categoryObj?.[key as string] as string[]) || []
      if (currentArray.includes(value.trim())) return prev
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [key]: [...currentArray, value.trim()]
        }
      }
    })
  }, [])

  const removeFromArray = useCallback(<T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => {
    setFilters(prev => {
      const categoryObj = prev[category] as Record<string, unknown> | undefined
      const currentArray = (categoryObj?.[key as string] as string[]) || []
      return {
        ...prev,
        [category]: {
          ...prev[category],
          [key]: currentArray.filter((v: string) => v !== value)
        }
      }
    })
  }, [])

  const resetFilters = useCallback(() => {
    setFilters({})
    setSearchSource("local")
  }, [])

  const handleApply = useCallback(() => {
    if (searchSource === "global" || searchSource === "hybrid") {
      setPendingSearch(() => () => {
        onApply(filters, { searchSource })
      })
      setShowCreditConfirm(true)
    } else {
      onApply(filters, { searchSource })
    }
  }, [filters, searchSource, onApply])

  const handleConfirmSearch = useCallback(() => {
    setIsSearching(true)
    if (pendingSearch) {
      pendingSearch()
    }
    setShowCreditConfirm(false)
    setPendingSearch(null)
    setIsSearching(false)
  }, [pendingSearch])

  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    Object.values(filters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && value !== false &&
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
  }, [filters])

  const creditEstimate = useMemo((): CreditEstimate => {
    const opts = filters.ppiOptions || {}
    return calculateCreditsLocally({
      searchType: opts.searchType || "fast",
      limit: candidateLimit,
      highFreshness: opts.highFreshness || false,
      requireEmails: opts.requireEmails || false,
      showEmails: opts.showEmails || false,
      requirePhoneNumbers: opts.requirePhoneNumbers || false,
      showPhoneNumbers: opts.showPhoneNumbers || false,
      requirePhonesOrEmails: opts.requirePhonesOrEmails || false
    })
  }, [filters.ppiOptions, candidateLimit])

  return {
    activeSection,
    candidateLimit,
    addToArray,
    creditEstimate,
    filters,
    getActiveFiltersCount,
    handleApply,
    handleConfirmSearch,
    isDestinationOpen,
    isLocalSearch,
    isSearching,
    onClose,
    onSave,
    removeFromArray,
    resetFilters,
    saveDestination,
    scrollContainerRef,
    scrollToSection,
    searchSource,
    sectionRefs,
    setFilters,
    setIsDestinationOpen,
    setSaveDestination,
    setSearchSource,
    setShowCreditConfirm,
    showCreditConfirm,
    sidebarCategories,
    updateFilter,
  }
}
