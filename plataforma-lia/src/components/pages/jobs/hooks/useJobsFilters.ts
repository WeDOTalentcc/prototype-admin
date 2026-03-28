"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { useJobFiltersPersistence, type SavedSearch } from "@/hooks/useJobFiltersPersistence"
import type { Job, JobFilters } from "@/components/jobs"

interface AdvancedFilters {
  [key: string]: string[]
  job_titles: string[]
  departments: string[]
  locations: string[]
  work_models: string[]
  job_types: string[]
  seniority_levels: string[]
  salary_ranges: string[]
  status: string[]
  stages: string[]
  priorities: string[]
  managers: string[]
  benefits: string[]
  requirements: string[]
  industries: string[]
  budget_ranges: string[]
  urgency_levels: string[]
  contract_duration: string[]
  team_size: string[]
}

const defaultAdvancedFilters: AdvancedFilters = {
  job_titles: [],
  departments: [],
  locations: [],
  work_models: [],
  job_types: [],
  seniority_levels: [],
  salary_ranges: [],
  status: [],
  stages: [],
  priorities: [],
  managers: [],
  benefits: [],
  requirements: [],
  industries: [],
  budget_ranges: [],
  urgency_levels: [],
  contract_duration: [],
  team_size: [],
}

export interface UseJobsFiltersState {
  searchTerm: string
  selectedStatusFilter: string
  activeFilter: string
  selectedDaysFilter: string
  advancedFilters: AdvancedFilters
  expandedSections: Set<string>
  booleanSearch: string
  searchHistory: string[]
  savedSearches: SavedSearch[]
  showSearchHistory: boolean
  showSavedSearches: boolean
  showAdvancedSearch: boolean
  searchSuggestions: string[]
  showSuggestions: boolean
  selectedTemplate: string
  jobFilters: JobFilters
  showTableFiltersPanel: boolean
  dashboardPeriod: '1m' | '3m' | '6m' | '9m' | '12m'
}

export interface UseJobsFiltersActions {
  setSearchTerm: (term: string) => void
  setSelectedStatusFilter: (status: string) => void
  setActiveFilter: (filter: string) => void
  setSelectedDaysFilter: (days: string) => void
  setAdvancedFilters: React.Dispatch<React.SetStateAction<AdvancedFilters>>
  setBooleanSearch: (search: string) => void
  setShowAdvancedSearch: (show: boolean) => void
  setJobFilters: React.Dispatch<React.SetStateAction<JobFilters>>
  setShowTableFiltersPanel: (show: boolean) => void
  setDashboardPeriod: (period: '1m' | '3m' | '6m' | '9m' | '12m') => void
  setSelectedTemplate: (template: string) => void
  handleSearch: (query: string) => void
  handleAISearch: (query: string, aiResults?: any) => void
  clearAllFilters: () => void
  toggleAdvancedFilter: (category: string, value: string) => void
  removeAdvancedFilter: (category: string, value: string) => void
  toggleSection: (section: string) => void
  getActiveAdvancedFiltersCount: () => number
  getActiveJobFiltersCount: () => number
  handleStatusFilterChange: (status: string) => void
  handleTemplateSelection: (persona: string) => void
  filterJobs: (allJobs: Job[], pinnedJobs: Set<number>) => Job[]
}

export interface UseJobsFiltersReturn {
  state: UseJobsFiltersState
  actions: UseJobsFiltersActions
  persistence: ReturnType<typeof useJobFiltersPersistence>
}

export function useJobsFilters(): UseJobsFiltersReturn {
  const persistence = useJobFiltersPersistence()
  const {
    filtersState: persistedFilters,
    updateFilter: updatePersistedFilter,
    savedSearches: persistedSavedSearches,
    isLoaded: filtersLoaded,
  } = persistence

  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('todas')
  const [activeFilter, setActiveFilter] = useState<string>('visao-geral')
  const [selectedDaysFilter, setSelectedDaysFilter] = useState<string>('todas')
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>(defaultAdvancedFilters)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['job_details', 'location_work']))
  const [booleanSearch, setBooleanSearch] = useState("")
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [showSearchHistory, setShowSearchHistory] = useState(false)
  const [showSavedSearches, setShowSavedSearches] = useState(false)
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState("")
  const [jobFilters, setJobFilters] = useState<JobFilters>({})
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)
  const [dashboardPeriod, setDashboardPeriod] = useState<'1m' | '3m' | '6m' | '9m' | '12m'>('3m')

  const hasRestoredFilters = useRef(false)
  useEffect(() => {
    if (filtersLoaded && !hasRestoredFilters.current) {
      hasRestoredFilters.current = true
      setSelectedStatusFilter(persistedFilters.selectedStatusFilter)
      setSelectedDaysFilter(persistedFilters.selectedDaysFilter)
      setAdvancedFilters(persistedFilters.advancedFilters)
      setBooleanSearch(persistedFilters.booleanSearch)
      setSearchTerm(persistedFilters.searchTerm)
      setSavedSearches(persistedSavedSearches)
    }
  }, [filtersLoaded])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('selectedStatusFilter', selectedStatusFilter)
  }, [selectedStatusFilter, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('selectedDaysFilter', selectedDaysFilter)
  }, [selectedDaysFilter, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('advancedFilters', advancedFilters)
  }, [advancedFilters, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('booleanSearch', booleanSearch)
  }, [booleanSearch, filtersLoaded, updatePersistedFilter])

  useEffect(() => {
    if (!filtersLoaded || !hasRestoredFilters.current) return
    updatePersistedFilter('searchTerm', searchTerm)
  }, [searchTerm, filtersLoaded, updatePersistedFilter])

  const handleSearch = (query: string) => {
    setSearchTerm(query)
  }

  const handleAISearch = (query: string, _aiResults?: any) => {
    setSearchTerm(query)
  }

  const clearAllFilters = () => {
    setSearchTerm("")
    setAdvancedFilters(defaultAdvancedFilters)
    setBooleanSearch("")
  }

  const toggleAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => {
      const currentValues = prev[category] || []
      const newValues = currentValues.includes(value)
        ? currentValues.filter(v => v !== value)
        : [...currentValues, value]
      return { ...prev, [category]: newValues }
    })
  }

  const removeAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => ({
      ...prev,
      [category]: prev[category].filter(v => v !== value)
    }))
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(section)) {
        newExpanded.delete(section)
      } else {
        newExpanded.add(section)
      }
      return newExpanded
    })
  }

  const getActiveAdvancedFiltersCount = () => {
    return Object.values(advancedFilters).reduce((count, filters) => count + filters.length, 0)
  }

  const getActiveJobFiltersCount = (): number => {
    let count = 0
    if (jobFilters.status?.statuses?.length) count += jobFilters.status.statuses.length
    if (jobFilters.status?.priorities?.length) count += jobFilters.status.priorities.length
    if (jobFilters.status?.stages?.length) count += jobFilters.status.stages.length
    if (jobFilters.position?.workModels?.length) count += jobFilters.position.workModels.length
    if (jobFilters.position?.levels?.length) count += jobFilters.position.levels.length
    if (jobFilters.position?.locations?.length) count += jobFilters.position.locations.length
    if (jobFilters.team?.departments?.length) count += jobFilters.team.departments.length
    if (jobFilters.team?.recruiters?.length) count += jobFilters.team.recruiters.length
    if (jobFilters.team?.managers?.length) count += jobFilters.team.managers.length
    if (jobFilters.publishing?.channels?.length) count += jobFilters.publishing.channels.length
    if (jobFilters.publishing?.unpublished) count += 1
    if (jobFilters.funnel?.emptyPipeline) count += 1
    if (jobFilters.metrics?.lowConversion) count += 1
    if (jobFilters.metrics?.minNPS) count += 1
    if (jobFilters.metrics?.maxDaysOpen) count += 1
    return count
  }

  const handleStatusFilterChange = (status: string) => {
    setSelectedStatusFilter(status)
  }

  const handleTemplateSelection = (persona: string) => {
    setSelectedTemplate(persona)
    switch (persona) {
      case "Vagas Tech Sênior":
        setAdvancedFilters(prev => ({
          ...prev,
          job_titles: ["Desenvolvedor Frontend", "Desenvolvedor Backend", "Tech Lead"],
          seniority_levels: ["Sênior", "Especialista"],
          departments: ["Tecnologia"],
          salary_ranges: ["R$ 10.000 - R$ 15.000", "R$ 15.000+"]
        }))
        setBooleanSearch("(Frontend OR Backend OR Tech Lead) AND Senior")
        break
      case "Vagas Design":
        setAdvancedFilters(prev => ({
          ...prev,
          job_titles: ["UX Designer", "UI Designer", "Product Designer"],
          departments: ["Design"],
          seniority_levels: ["Pleno", "Sênior"]
        }))
        setBooleanSearch("UX OR UI OR Product AND Design")
        break
      case "Vagas Remotas":
        setAdvancedFilters(prev => ({
          ...prev,
          work_models: ["Remoto"],
          locations: ["Qualquer lugar", "Remoto"]
        }))
        setBooleanSearch("Remoto OR Remote")
        break
      case "Vagas Urgentes":
        setAdvancedFilters(prev => ({
          ...prev,
          priorities: ["Alta"],
          urgency_levels: ["5", "4"],
          status: ["Ativa"]
        }))
        setBooleanSearch("Urgente OR Imediato")
        break
      case "Vagas Júnior":
        setAdvancedFilters(prev => ({
          ...prev,
          seniority_levels: ["Júnior", "Trainee"],
          salary_ranges: ["R$ 3.000 - R$ 6.000", "R$ 6.000 - R$ 10.000"]
        }))
        setBooleanSearch("Junior OR Júnior OR Trainee")
        break
    }
  }

  const filterJobs = (allJobs: Job[], pinnedJobs: Set<number>): Job[] => {
    return allJobs.filter(job => {
      let matchesActiveFilter = true
      if (activeFilter === 'ativas') {
        matchesActiveFilter = job.status === 'Ativa'
      } else if (activeFilter === 'urgentes') {
        matchesActiveFilter = job.urgencyLevel >= 4
      } else if (activeFilter === 'paralisadas') {
        matchesActiveFilter = job.status === 'Paralisada'
      } else if (activeFilter === 'concluidas') {
        matchesActiveFilter = job.status === 'Concluída'
      } else if (activeFilter === 'canceladas') {
        matchesActiveFilter = job.status === 'Cancelada'
      }
      if (!matchesActiveFilter) return false

      let matchesStatus = true
      if (selectedStatusFilter !== 'todas') {
        matchesStatus = job.status === selectedStatusFilter
      }

      const searchLower = searchTerm.toLowerCase()
      let matchesSearch = searchTerm === "" ||
        job.jobId.toLowerCase().includes(searchLower) ||
        job.title.toLowerCase().includes(searchLower) ||
        job.department.toLowerCase().includes(searchLower) ||
        job.location.toLowerCase().includes(searchLower) ||
        job.type.toLowerCase().includes(searchLower) ||
        job.level.toLowerCase().includes(searchLower) ||
        job.salary.toLowerCase().includes(searchLower) ||
        job.description.toLowerCase().includes(searchLower) ||
        job.manager.toLowerCase().includes(searchLower) ||
        job.managerEmail.toLowerCase().includes(searchLower) ||
        job.recruiter.toLowerCase().includes(searchLower) ||
        job.recruiterEmail.toLowerCase().includes(searchLower) ||
        job.requirements.some(req => req.toLowerCase().includes(searchLower)) ||
        job.benefits.some(benefit => benefit.toLowerCase().includes(searchLower)) ||
        (job.tags || []).some(tag => tag.toLowerCase().includes(searchLower)) ||
        (job.technicalRequirements || []).some((tr: any) =>
          tr.technology?.toLowerCase().includes(searchLower) ||
          tr.category?.toLowerCase().includes(searchLower)
        ) ||
        (job.languages || []).some((lang: any) =>
          lang.language?.toLowerCase().includes(searchLower)
        ) ||
        (job.behavioralCompetencies || []).some((bc: any) =>
          bc.competency?.toLowerCase().includes(searchLower)
        ) ||
        (job.targetSector || '').toLowerCase().includes(searchLower) ||
        (job.targetSegment || '').toLowerCase().includes(searchLower) ||
        job.status.toLowerCase().includes(searchLower) ||
        job.priority.toLowerCase().includes(searchLower) ||
        job.stage.toLowerCase().includes(searchLower)

      if (booleanSearch.trim()) {
        const booleanLower = booleanSearch.toLowerCase()
        const jobText = [
          job.title, job.department, job.location, job.type,
          job.level, job.description, job.manager,
          ...job.requirements, ...job.benefits
        ].join(' ').toLowerCase()

        if (booleanLower.includes(' and ')) {
          const terms = booleanLower.split(' and ')
          matchesSearch = terms.every(term => jobText.includes(term.trim()))
        } else if (booleanLower.includes(' or ')) {
          const terms = booleanLower.split(' or ')
          matchesSearch = terms.some(term => jobText.includes(term.trim()))
        } else {
          matchesSearch = jobText.includes(booleanLower)
        }
      }

      let matchesAdvancedFilters = true
      if (advancedFilters.job_titles.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_titles.some(title =>
          job.title.toLowerCase().includes(title.toLowerCase()))
      }
      if (advancedFilters.departments.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.departments.some(dept =>
          job.department.toLowerCase().includes(dept.toLowerCase()))
      }
      if (advancedFilters.locations.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.locations.some(location =>
          job.location.toLowerCase().includes(location.toLowerCase()))
      }
      if (advancedFilters.work_models.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.work_models.some(model =>
          job.workModel.toLowerCase().includes(model.toLowerCase()))
      }
      if (advancedFilters.job_types.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_types.some(type =>
          job.type.toLowerCase().includes(type.toLowerCase()))
      }
      if (advancedFilters.seniority_levels.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.seniority_levels.some(level =>
          job.level.toLowerCase().includes(level.toLowerCase()))
      }
      if (advancedFilters.status.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.status.some(status =>
          job.status.toLowerCase().includes(status.toLowerCase()))
      }
      if (advancedFilters.stages.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.stages.some(stage =>
          job.stage.toLowerCase().includes(stage.toLowerCase()))
      }
      if (advancedFilters.priorities.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.priorities.some(priority =>
          job.priority.toLowerCase().includes(priority.toLowerCase()))
      }
      if (advancedFilters.managers.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.managers.some(manager =>
          job.manager.toLowerCase().includes(manager.toLowerCase()))
      }
      if (advancedFilters.benefits.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.benefits.some(benefit =>
          job.benefits.some(jobBenefit => jobBenefit.toLowerCase().includes(benefit.toLowerCase())))
      }
      if (advancedFilters.requirements.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.requirements.some(requirement =>
          job.requirements.some(jobReq => jobReq.toLowerCase().includes(requirement.toLowerCase())))
      }
      if (advancedFilters.budget_ranges.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.budget_ranges.some(range => {
          const budget = job.budget || 0
          switch (range) {
            case "Até R$ 50.000": return budget <= 50000
            case "R$ 50.000 - R$ 100.000": return budget >= 50000 && budget <= 100000
            case "R$ 100.000+": return budget >= 100000
            default: return false
          }
        })
      }
      if (advancedFilters.urgency_levels.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.urgency_levels.some(level =>
          job.urgencyLevel.toString() === level)
      }
      if (advancedFilters.contract_duration.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.contract_duration.some(duration =>
          job.type.toLowerCase().includes(duration.toLowerCase()))
      }

      let matchesInlineFilters = true
      if (jobFilters.status?.statuses?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.statuses.includes(job.status)
      }
      if (jobFilters.status?.priorities?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.priorities.includes(job.priority)
      }
      if (jobFilters.status?.stages?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.stages.includes(job.stage)
      }
      if (jobFilters.position?.workModels?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.workModels.includes(job.workModel)
      }
      if (jobFilters.position?.levels?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.levels.some(level =>
          job.level.toLowerCase().includes(level.toLowerCase()))
      }
      if (jobFilters.team?.departments?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.departments.some(dept =>
          job.department.toLowerCase().includes(dept.toLowerCase()))
      }
      if (jobFilters.team?.recruiters?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.recruiters.some(recruiter =>
          job.recruiter.toLowerCase().includes(recruiter.toLowerCase()))
      }
      if (jobFilters.team?.managers?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.managers.some(manager =>
          job.manager.toLowerCase().includes(manager.toLowerCase()))
      }
      if (jobFilters.position?.locations?.length) {
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.locations.some(loc =>
          job.location.toLowerCase().includes(loc.toLowerCase()) ||
          (loc.toLowerCase() === 'remoto' && job.workModel === 'remoto'))
      }
      if (jobFilters.publishing?.channels?.length) {
        const publishedChannels: string[] = []
        if (job.publishedLinkedIn) publishedChannels.push('linkedin')
        if (job.publishedWebsite) publishedChannels.push('website')
        if (job.publishedIndeed) publishedChannels.push('indeed')
        matchesInlineFilters = matchesInlineFilters && jobFilters.publishing.channels.some(channel =>
          publishedChannels.includes(channel))
      }
      if (jobFilters.publishing?.unpublished) {
        matchesInlineFilters = matchesInlineFilters &&
          !job.publishedLinkedIn && !job.publishedWebsite && !job.publishedIndeed
      }
      if (jobFilters.funnel?.emptyPipeline) {
        matchesInlineFilters = matchesInlineFilters && job.funnel.total === 0
      }
      if (jobFilters.metrics?.lowConversion) {
        const conversionRate = job.funnel.total > 0 ? (job.funnel.hired / job.funnel.total) : 0
        matchesInlineFilters = matchesInlineFilters && conversionRate < 0.1
      }
      if (jobFilters.metrics?.minNPS) {
        matchesInlineFilters = matchesInlineFilters && job.nps >= jobFilters.metrics.minNPS
      }
      if (jobFilters.metrics?.maxDaysOpen) {
        const daysOpenCalc = Math.floor(
          (new Date().getTime() - new Date(job.openDate).getTime()) / (1000 * 60 * 60 * 24))
        matchesInlineFilters = matchesInlineFilters && daysOpenCalc <= jobFilters.metrics.maxDaysOpen
      }

      return matchesStatus && matchesSearch && matchesAdvancedFilters && matchesInlineFilters
    }).sort((a, b) => {
      const aIsPinned = pinnedJobs.has(a.id)
      const bIsPinned = pinnedJobs.has(b.id)
      if (aIsPinned && !bIsPinned) return -1
      if (!aIsPinned && bIsPinned) return 1
      return 0
    })
  }

  return {
    state: {
      searchTerm,
      selectedStatusFilter,
      activeFilter,
      selectedDaysFilter,
      advancedFilters,
      expandedSections,
      booleanSearch,
      searchHistory,
      savedSearches,
      showSearchHistory,
      showSavedSearches,
      showAdvancedSearch,
      searchSuggestions,
      showSuggestions,
      selectedTemplate,
      jobFilters,
      showTableFiltersPanel,
      dashboardPeriod,
    },
    actions: {
      setSearchTerm,
      setSelectedStatusFilter,
      setActiveFilter,
      setSelectedDaysFilter,
      setAdvancedFilters,
      setBooleanSearch,
      setShowAdvancedSearch,
      setJobFilters,
      setShowTableFiltersPanel,
      setDashboardPeriod,
      setSelectedTemplate,
      handleSearch,
      handleAISearch,
      clearAllFilters,
      toggleAdvancedFilter,
      removeAdvancedFilter,
      toggleSection,
      getActiveAdvancedFiltersCount,
      getActiveJobFiltersCount,
      handleStatusFilterChange,
      handleTemplateSelection,
      filterJobs,
    },
    persistence,
  }
}
