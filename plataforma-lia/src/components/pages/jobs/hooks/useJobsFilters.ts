"use client"


import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { useState, useEffect, useRef, useMemo } from "react"
import { useJobFiltersPersistence, type JobSavedSearch as SavedSearch } from "@/hooks/jobs/useJobFiltersPersistence"
import { toast } from "sonner"
import type { Job, JobFilters } from "@/components/jobs"
import { getJobSeniority } from "@/lib/jobs/seniority"

// ---------------------------------------------------------------------------
// useJobsFilters
// Responsável por: filtros de status/dias, filtros avançados (multi-campo),
// busca textual com boolean, persistência via Zustand store, saved searches,
// filtros inline da tabela (jobFilters), filtros de navegação (tabs).
// ---------------------------------------------------------------------------

interface UseJobsFiltersOptions {
  backendJobs: Job[]
}

interface UseJobsFiltersReturn {
  state: {
    searchTerm: string
    selectedStatusFilter: string
    selectedDaysFilter: string
    activeFilter: string
    booleanSearch: string
    advancedFilters: Record<string, string[]>
    savedSearches: SavedSearch[]
    searchHistory: string[]
    showAdvancedSearch: boolean
    expandedSections: Set<string>
    showSearchHistory: boolean
    showSavedSearches: boolean
    showSuggestions: boolean
    selectedTemplate: string
    jobFilters: JobFilters
    showTableFiltersPanel: boolean
    navigationFilters: ReturnType<typeof buildNavigationFilters>
    stageFilters: ReturnType<typeof buildStageFilters>
    filteredJobs: Job[]
    statusFilters: typeof STATUS_FILTERS
  }
  actions: {
    setSearchTerm: (v: string) => void
    setSelectedStatusFilter: (v: string) => void
    setSelectedDaysFilter: (v: string) => void
    setActiveFilter: (v: string) => void
    setBooleanSearch: (v: string) => void
    setAdvancedFilters: React.Dispatch<React.SetStateAction<Record<string, string[]>>>
    setSavedSearches: React.Dispatch<React.SetStateAction<SavedSearch[]>>
    setShowAdvancedSearch: (v: boolean) => void
    setExpandedSections: React.Dispatch<React.SetStateAction<Set<string>>>
    setShowSearchHistory: (v: boolean) => void
    setShowSavedSearches: (v: boolean) => void
    setShowSuggestions: (v: boolean) => void
    setSelectedTemplate: (v: string) => void
    setJobFilters: React.Dispatch<React.SetStateAction<JobFilters>>
    setShowTableFiltersPanel: (v: boolean) => void
    handleSearch: (query: string) => void
    handleAISearch: (query: string, aiResults?: Record<string, unknown>) => void
    clearAllFilters: () => void
    clearAllJobFilters: () => void
    toggleAdvancedFilter: (category: string, value: string) => void
    removeAdvancedFilter: (category: string, value: string) => void
    toggleSection: (section: string) => void
    toggleJobFilter: (category: keyof JobFilters, field: string, value: string | number | boolean) => void
    getActiveAdvancedFiltersCount: () => number
    getActiveJobFiltersCount: () => number
    saveSearch: () => void
    saveSearchAsTemplate: (customName?: string) => void
    handleApplySavedSearch: (searchId: string) => void
    handleDeleteSavedSearch: (searchId: string) => void
    handleRenameSavedSearch: (searchId: string, newName: string) => void
    handleStatusFilterChange: (status: string) => void
    handleTemplateSelection: (persona: string) => void
    getJobCountByStatus: (status: string) => number
    getJobCountByStage: (stage: string) => number
    searchTemplates: string[]
  }
}

const STATUS_FILTERS = [
  { id: 'todas', label: 'Todas', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' },
  { id: 'Ativa', label: 'Ativas', color: 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-tertiary' },
  { id: 'Paralisada', label: 'Paralisadas', color: 'bg-lia-bg-secondary text-lia-text-primary dark:bg-lia-bg-secondary' },
  { id: 'Concluída', label: 'Concluídas', color: 'bg-lia-bg-secondary text-lia-text-primary dark:bg-lia-bg-secondary' },
  { id: 'Cancelada', label: 'Canceladas', color: 'bg-status-error/15 text-status-error dark:bg-status-error/20 dark:text-status-error' },
]

function buildNavigationFilters(backendJobs: Job[]) {
  return [
    { id: 'todas', label: 'Todas', description: 'Todas as vagas do sistema', count: backendJobs.length },
    { id: 'ativas', label: 'Ativas', description: 'Vagas abertas e em andamento', count: backendJobs.filter(j => j.status === 'Ativa').length },
    { id: 'urgentes', label: 'Urgentes', description: 'Vagas com alta prioridade de preenchimento', count: backendJobs.filter(j => j.urgencyLevel >= 4).length, highlight: true },
    // Phase 4H — ATS filter (vagas importadas do ATS)
    { id: 'ats', label: 'ATS', description: 'Vagas importadas do ATS (Gupy, Greenhouse, planilha, etc)', count: backendJobs.filter(j => j.source === 'ats_import' || j.source === 'ats_external').length },
    { id: 'paralisadas', label: 'Paralisadas', description: 'Vagas temporariamente suspensas', count: backendJobs.filter(j => j.status === 'Paralisada').length },
    { id: 'concluidas', label: 'Concluídas', description: 'Vagas com contratação finalizada', count: backendJobs.filter(j => j.status === 'Concluída').length },
    { id: 'canceladas', label: 'Canceladas', description: 'Vagas canceladas ou arquivadas', count: backendJobs.filter(j => j.status === 'Cancelada').length },
  ]
}

function buildStageFilters(backendJobs: Job[]) {
  return [
    { id: 'planejamento', label: 'Planejamento', count: backendJobs.filter(j => j.stage === 'Planejamento').length },
    { id: 'aprovacao', label: 'Aprovação', count: backendJobs.filter(j => j.stage === 'Aprovação').length },
    { id: 'publicada', label: 'Publicada', count: backendJobs.filter(j => j.stage === 'Publicada').length },
    { id: 'triagem', label: 'Triagem', count: backendJobs.filter(j => j.stage === 'Triagem').length },
    { id: 'entrevistas', label: 'Entrevistas', count: backendJobs.filter(j => j.stage === 'Entrevistas').length },
    { id: 'finalizacao', label: 'Finalização', count: backendJobs.filter(j => j.stage === 'Finalização').length },
    { id: 'encerrada', label: 'Encerrada', count: backendJobs.filter(j => j.stage === 'Encerrada').length },
  ]
}

const EMPTY_ADVANCED_FILTERS: Record<string, string[]> = {
  job_titles: [], departments: [], locations: [], work_models: [], job_types: [],
  seniority_levels: [], salary_ranges: [], status: [], stages: [], priorities: [],
  managers: [], benefits: [], requirements: [], industries: [], budget_ranges: [],
  urgency_levels: [], contract_duration: [], team_size: [],
}

export function useJobsFilters({ backendJobs }: UseJobsFiltersOptions): UseJobsFiltersReturn {
  const {
    filtersState: persistedFilters,
    updateFilter: updatePersistedFilter,
    savedSearches: persistedSavedSearches,
    saveCurrentSearch: savePersistedSearch,
    applySavedSearch: applyPersistedSearch,
    deleteSavedSearch: deletePersistedSearch,
    renameSavedSearch: renamePersistedSearch,
    getActiveFiltersCount,
    hasActiveFilters,
    isLoaded: filtersLoaded,
  } = useJobFiltersPersistence()

  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('todas')
  const [selectedDaysFilter, setSelectedDaysFilter] = useState<string>('todas')
  const [activeFilter, setActiveFilter] = useState<string>(() => {
    // Bug-fix 2026-06-10: race condition navigate+filter.
    // Quando o agente navega E filtra em sequência, o evento lia:apply_table_state
    // pode disparar antes do listener ser registrado (página ainda montando).
    // Solução: o apply_table_state também faz router.push com ?filter=X na URL,
    // e aqui lemos o valor inicial da URL no momento do mount (client-only).
    if (typeof window === "undefined") return "todas"
    return new URLSearchParams(window.location.search).get("filter") || "todas"
  })
  const [booleanSearch, setBooleanSearch] = useState("")
  const [advancedFilters, setAdvancedFilters] = useState<Record<string, string[]>>({ ...EMPTY_ADVANCED_FILTERS })
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['job_details', 'location_work']))
  const [showSearchHistory, setShowSearchHistory] = useState(false)
  const [showSavedSearches, setShowSavedSearches] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState("")
  const [jobFilters, setJobFilters] = useState<JobFilters>({})
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)

  const hasRestoredFilters = useRef(false)

  // Fase 2 (ponte in-page): a LIA filtra/busca a lista de Vagas via chat.
  // useUIAction despacha lia:apply_table_state {surface:'jobs', patch}; aqui
  // (onde o estado vive) aplicamos aos setters locais. Sem navegar/mutar dados.
  useEffect(() => {
    function handleApplyTableState(e: Event) {
      const { surface, patch } =
        (e as CustomEvent<{ surface: string; patch: Record<string, unknown> }>)
          .detail ?? {}
      if (surface !== "jobs" || !patch) return
      if (typeof patch.search === "string") setSearchTerm(patch.search)
      if (typeof patch.filter === "string") setActiveFilter(patch.filter)
    }
    window.addEventListener("lia:apply_table_state", handleApplyTableState)
    return () =>
      window.removeEventListener("lia:apply_table_state", handleApplyTableState)
  }, [])

  // Restore persisted filters once loaded
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // -------------------------------------------------------------------------
  // Derived: filteredJobs
  // -------------------------------------------------------------------------
  const filteredJobs = useMemo(() => {
    return backendJobs.filter(job => {
      // Tab navigation filtering (activeFilter)
      let matchesActiveFilter = true
      if (activeFilter === 'ativas') matchesActiveFilter = job.status === 'Ativa'
      else if (activeFilter === 'urgentes') matchesActiveFilter = job.urgencyLevel >= 4
      else if (activeFilter === 'ats') matchesActiveFilter = job.source === 'ats_import' || job.source === 'ats_external'
      else if (activeFilter === 'paralisadas') matchesActiveFilter = job.status === 'Paralisada'
      else if (activeFilter === 'concluidas') matchesActiveFilter = job.status === 'Concluída'
      else if (activeFilter === 'canceladas') matchesActiveFilter = job.status === 'Cancelada'
      if (!matchesActiveFilter) return false

      // Status filter
      let matchesStatus = true
      if (selectedStatusFilter !== 'todas') matchesStatus = job.status === selectedStatusFilter

      // Global search
      const searchLower = searchTerm.toLowerCase()
      let matchesSearch = searchTerm === "" ||
        job.jobId.toLowerCase().includes(searchLower) ||
        job.title.toLowerCase().includes(searchLower) ||
        job.department.toLowerCase().includes(searchLower) ||
        job.location.toLowerCase().includes(searchLower) ||
        job.type.toLowerCase().includes(searchLower) ||
        (getJobSeniority(job)?.toLowerCase().includes(searchLower) ?? false) ||
        job.salary.toLowerCase().includes(searchLower) ||
        job.description.toLowerCase().includes(searchLower) ||
        job.manager.toLowerCase().includes(searchLower) ||
        job.managerEmail.toLowerCase().includes(searchLower) ||
        job.recruiter.toLowerCase().includes(searchLower) ||
        job.recruiterEmail.toLowerCase().includes(searchLower) ||
        job.requirements.some(req => req.toLowerCase().includes(searchLower)) ||
        job.benefits.some(benefit => benefit.toLowerCase().includes(searchLower)) ||
        (job.tags || []).some(tag => tag.toLowerCase().includes(searchLower)) ||
        ((job.technicalRequirements || []) as Record<string, unknown>[]).some((tr) =>
          (tr.technology as string)?.toLowerCase().includes(searchLower) ||
          (tr.category as string)?.toLowerCase().includes(searchLower)
        ) ||
        ((job.languages || []) as Record<string, unknown>[]).some((lang) =>
          (lang.language as string)?.toLowerCase().includes(searchLower)
        ) ||
        ((job.behavioralCompetencies || []) as Record<string, unknown>[]).some((bc) =>
          (bc.competency as string)?.toLowerCase().includes(searchLower)
        ) ||
        (job.targetSector || '').toLowerCase().includes(searchLower) ||
        (job.targetSegment || '').toLowerCase().includes(searchLower) ||
        job.status.toLowerCase().includes(searchLower) ||
        job.priority.toLowerCase().includes(searchLower) ||
        job.stage.toLowerCase().includes(searchLower)

      // Boolean search
      if (booleanSearch.trim()) {
        const booleanLower = booleanSearch.toLowerCase()
        const jobText = [
          job.title, job.department, job.location, job.type, getJobSeniority(job) ?? '',
          job.description, job.manager, ...job.requirements, ...job.benefits,
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

      // Advanced filters
      let matchesAdvancedFilters = true
      if (advancedFilters.job_titles.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_titles.some(t => job.title.toLowerCase().includes(t.toLowerCase()))
      if (advancedFilters.departments.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.departments.some(d => job.department.toLowerCase().includes(d.toLowerCase()))
      if (advancedFilters.locations.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.locations.some(l => job.location.toLowerCase().includes(l.toLowerCase()))
      if (advancedFilters.work_models.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.work_models.some(m => job.workModel.toLowerCase().includes(m.toLowerCase()))
      if (advancedFilters.job_types.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.job_types.some(t => job.type.toLowerCase().includes(t.toLowerCase()))
      if (advancedFilters.seniority_levels.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.seniority_levels.some(l => getJobSeniority(job)?.toLowerCase().includes(l.toLowerCase()) ?? false)
      if (advancedFilters.status.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.status.some(s => job.status.toLowerCase().includes(s.toLowerCase()))
      if (advancedFilters.stages.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.stages.some(s => job.stage.toLowerCase().includes(s.toLowerCase()))
      if (advancedFilters.priorities.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.priorities.some(p => job.priority.toLowerCase().includes(p.toLowerCase()))
      if (advancedFilters.managers.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.managers.some(m => job.manager.toLowerCase().includes(m.toLowerCase()))
      if (advancedFilters.benefits.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.benefits.some(b => job.benefits.some(jb => jb.toLowerCase().includes(b.toLowerCase())))
      if (advancedFilters.requirements.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.requirements.some(r => job.requirements.some(jr => jr.toLowerCase().includes(r.toLowerCase())))
      if (advancedFilters.urgency_levels.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.urgency_levels.some(l => job.urgencyLevel.toString() === l)
      if (advancedFilters.budget_ranges.length > 0) {
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.budget_ranges.some(range => {
          const budget = job.budget || 0
          if (range === `Até ${CURRENCY_SYMBOL} 50.000`) return budget <= 50000
          if (range === `${CURRENCY_SYMBOL} 50.000 - ${CURRENCY_SYMBOL} 100.000`) return budget >= 50000 && budget <= 100000
          if (range === `${CURRENCY_SYMBOL} 100.000+`) return budget >= 100000
          return false
        })
      }
      if (advancedFilters.contract_duration.length > 0)
        matchesAdvancedFilters = matchesAdvancedFilters && advancedFilters.contract_duration.some(d => job.type.toLowerCase().includes(d.toLowerCase()))

      // Inline table filters (jobFilters)
      let matchesInlineFilters = true
      if (jobFilters.status?.statuses?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.statuses.includes(job.status)
      if (jobFilters.status?.priorities?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.priorities.includes(job.priority)
      if (jobFilters.status?.stages?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.status.stages.includes(job.stage)
      if (jobFilters.position?.workModels?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.workModels.includes(job.workModel)
      if (jobFilters.position?.levels?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.levels.some(l => getJobSeniority(job)?.toLowerCase().includes(l.toLowerCase()) ?? false)
      if (jobFilters.team?.departments?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.departments.some(d => job.department.toLowerCase().includes(d.toLowerCase()))
      if (jobFilters.team?.recruiters?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.recruiters.some(r => job.recruiter.toLowerCase().includes(r.toLowerCase()))
      if (jobFilters.team?.managers?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.team.managers.some(m => job.manager.toLowerCase().includes(m.toLowerCase()))
      if (jobFilters.position?.locations?.length)
        matchesInlineFilters = matchesInlineFilters && jobFilters.position.locations.some(loc =>
          job.location.toLowerCase().includes(loc.toLowerCase()) || (loc.toLowerCase() === 'remoto' && job.workModel === 'remoto')
        )
      if (jobFilters.publishing?.channels?.length) {
        const publishedChannels: string[] = []
        if (job.publishedLinkedIn) publishedChannels.push('linkedin')
        if (job.publishedWebsite) publishedChannels.push('website')
        if ((job as unknown as Record<string, unknown>).publishedIndeed) publishedChannels.push('indeed')
        matchesInlineFilters = matchesInlineFilters && jobFilters.publishing.channels.some(c => publishedChannels.includes(c))
      }
      if (jobFilters.publishing?.unpublished)
        matchesInlineFilters = matchesInlineFilters && !job.publishedLinkedIn && !job.publishedWebsite && !(job as unknown as Record<string, unknown>).publishedIndeed
      if (jobFilters.funnel?.emptyPipeline)
        matchesInlineFilters = matchesInlineFilters && job.funnel.total === 0
      if (jobFilters.metrics?.lowConversion) {
        const conversionRate = job.funnel.total > 0 ? (job.funnel.hired / job.funnel.total) : 0
        matchesInlineFilters = matchesInlineFilters && conversionRate < 0.1
      }
      if (jobFilters.metrics?.minNPS)
        matchesInlineFilters = matchesInlineFilters && job.nps >= (jobFilters.metrics.minNPS as number)
      if (jobFilters.metrics?.maxDaysOpen) {
        const daysOpen = Math.floor((new Date().getTime() - new Date(job.openDate).getTime()) / (1000 * 60 * 60 * 24))
        matchesInlineFilters = matchesInlineFilters && daysOpen <= (jobFilters.metrics.maxDaysOpen as number)
      }

      return matchesStatus && matchesSearch && matchesAdvancedFilters && matchesInlineFilters
    })
  }, [backendJobs, activeFilter, selectedStatusFilter, searchTerm, booleanSearch, advancedFilters, jobFilters])

  // -------------------------------------------------------------------------
  // Derived: navigation & stage filters (memoized)
  // -------------------------------------------------------------------------
  const navigationFilters = useMemo(() => buildNavigationFilters(backendJobs), [backendJobs])
  const stageFilters = useMemo(() => buildStageFilters(backendJobs), [backendJobs])

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------
  const handleSearch = (query: string) => setSearchTerm(query)
  const handleAISearch = (query: string, _aiResults?: Record<string, unknown>) => setSearchTerm(query)

  const clearAllFilters = () => {
    setSearchTerm("")
    setAdvancedFilters({ ...EMPTY_ADVANCED_FILTERS })
    setBooleanSearch("")
  }

  const clearAllJobFilters = () => setJobFilters({})

  const toggleAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => {
      const current = prev[category] || []
      return {
        ...prev,
        [category]: current.includes(value) ? current.filter(v => v !== value) : [...current, value],
      }
    })
  }

  const removeAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => ({ ...prev, [category]: prev[category].filter(v => v !== value) }))
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(section)) next.delete(section)
      else next.add(section)
      return next
    })
  }

  const getActiveAdvancedFiltersCount = () =>
    Object.values(advancedFilters).reduce((count, filters) => count + filters.length, 0)

  const getActiveJobFiltersCount = (): number => {
    let count = 0
    if (jobFilters.status?.statuses?.length) count += jobFilters.status.statuses.length
    if (jobFilters.status?.priorities?.length) count += jobFilters.status.priorities.length
    if (jobFilters.status?.stages?.length) count += jobFilters.status.stages.length
    if (jobFilters.dates?.openedWithinDays) count += 1
    if (jobFilters.dates?.closingWithinDays) count += 1
    if (jobFilters.dates?.noActivityDays) count += 1
    if (jobFilters.team?.recruiters?.length) count += jobFilters.team.recruiters.length
    if (jobFilters.team?.managers?.length) count += jobFilters.team.managers.length
    if (jobFilters.team?.departments?.length) count += jobFilters.team.departments.length
    if (jobFilters.position?.levels?.length) count += jobFilters.position.levels.length
    if (jobFilters.position?.types?.length) count += jobFilters.position.types.length
    if (jobFilters.position?.workModels?.length) count += jobFilters.position.workModels.length
    if (jobFilters.position?.locations?.length) count += jobFilters.position.locations.length
    if (jobFilters.funnel?.minCandidates) count += 1
    if (jobFilters.funnel?.maxCandidates) count += 1
    if (jobFilters.funnel?.emptyPipeline) count += 1
    if (jobFilters.funnel?.stuckInStage) count += 1
    if (jobFilters.metrics?.minNPS) count += 1
    if (jobFilters.metrics?.maxDaysOpen) count += 1
    if (jobFilters.metrics?.lowConversion) count += 1
    if (jobFilters.publishing?.channels?.length) count += jobFilters.publishing.channels.length
    if (jobFilters.publishing?.unpublished) count += 1
    return count
  }

  const toggleJobFilter = (category: keyof JobFilters, field: string, value: string | number | boolean) => {
    setJobFilters(prev => {
      const updated = { ...prev }
      const cat = (updated[category] as Record<string, unknown>) || {}
      if (typeof value === 'boolean') {
        cat[field] = value ? true : undefined
      } else if (typeof value === 'number') {
        cat[field] = value
      } else {
        const arr = (cat[field] as string[]) || []
        cat[field] = arr.includes(value) ? arr.filter((v: string) => v !== value) : [...arr, value]
      }
      updated[category] = cat
      return updated
    })
  }

  const saveSearch = () => {
    const searchQuery = `${searchTerm} ${booleanSearch}`.trim()
    if (searchQuery && !searchHistory.includes(searchQuery)) {
      setSearchHistory(prev => [searchQuery, ...prev.slice(0, 9)])
    }
  }

  const saveSearchAsTemplate = (customName?: string) => {
    const searchName = customName || selectedTemplate || "Nova Busca Salva"
    const savedSearch = savePersistedSearch(searchName)
    setSavedSearches(prev => [savedSearch, ...prev.slice(0, 9)])
    toast.success(`Busca "${searchName}" salva com sucesso!`)
  }

  const handleApplySavedSearch = (searchId: string) => {
    const search = savedSearches.find(s => s.id === searchId)
    if (search) {
      applyPersistedSearch(searchId)
      setSelectedStatusFilter(search.filters.selectedStatusFilter || 'todas')
      setSelectedDaysFilter(search.filters.selectedDaysFilter || 'todas')
      setSearchTerm(search.filters.searchTerm || search.query || '')
      setBooleanSearch(search.filters.booleanSearch || "")
      setAdvancedFilters(search.filters.advancedFilters || {})
      toast.success(`Busca "${search.name}" aplicada`)
    }
  }

  const handleDeleteSavedSearch = (searchId: string) => {
    deletePersistedSearch(searchId)
    setSavedSearches(prev => prev.filter(s => s.id !== searchId))
    toast.success("Busca removida")
  }

  const handleRenameSavedSearch = (searchId: string, newName: string) => {
    renamePersistedSearch(searchId, newName)
    setSavedSearches(prev => prev.map(s => s.id === searchId ? { ...s, name: newName } : s))
    toast.success("Busca renomeada")
  }

  const handleStatusFilterChange = (status: string) => setSelectedStatusFilter(status)

  const handleTemplateSelection = (persona: string) => {
    setSelectedTemplate(persona)
    switch (persona) {
      case "Vagas Tech Sênior":
        setAdvancedFilters(prev => ({ ...prev, job_titles: ["Desenvolvedor Frontend", "Desenvolvedor Backend", "Tech Lead"], seniority_levels: ["Sênior", "Especialista"], departments: ["Tecnologia"], salary_ranges: [`${CURRENCY_SYMBOL} 10.000 - ${CURRENCY_SYMBOL} 15.000`, `${CURRENCY_SYMBOL} 15.000+`] }))
        setBooleanSearch("(Frontend OR Backend OR Tech Lead) AND Senior")
        break
      case "Vagas Design":
        setAdvancedFilters(prev => ({ ...prev, job_titles: ["UX Designer", "UI Designer", "Product Designer"], departments: ["Design"], seniority_levels: ["Pleno", "Sênior"] }))
        setBooleanSearch("UX OR UI OR Product AND Design")
        break
      case "Vagas Remotas":
        setAdvancedFilters(prev => ({ ...prev, work_models: ["Remoto"], locations: ["Qualquer lugar", "Remoto"] }))
        setBooleanSearch("Remoto OR Remote")
        break
      case "Vagas Urgentes":
        setAdvancedFilters(prev => ({ ...prev, priorities: ["Alta"], urgency_levels: ["5", "4"], status: ["Ativa"] }))
        setBooleanSearch("Urgente OR Imediato")
        break
      case "Vagas Júnior":
        setAdvancedFilters(prev => ({ ...prev, seniority_levels: ["Júnior", "Trainee"], salary_ranges: [`${CURRENCY_SYMBOL} 3.000 - ${CURRENCY_SYMBOL} 6.000`, `${CURRENCY_SYMBOL} 6.000 - ${CURRENCY_SYMBOL} 10.000`] }))
        setBooleanSearch("Junior OR Júnior OR Trainee")
        break
    }
  }

  const getJobCountByStatus = (status: string) => {
    if (status === 'todas') return backendJobs.length
    return backendJobs.filter(j => j.status === status).length
  }

  const getJobCountByStage = (stage: string) => {
    if (stage === 'todos') return backendJobs.length
    return backendJobs.filter(j => j.stage === stage).length
  }

  const searchTemplates = [
    "Vagas Tech Sênior", "Vagas Design", "Vagas Remotas", "Vagas Urgentes", "Vagas Júnior",
    "Vagas Product Manager", "Vagas Data Science", "Vagas DevOps", "Vagas Startup", "Vagas Enterprise",
  ]

  return {
    state: {
      searchTerm, selectedStatusFilter, selectedDaysFilter, activeFilter, booleanSearch,
      advancedFilters, savedSearches, searchHistory, showAdvancedSearch, expandedSections,
      showSearchHistory, showSavedSearches, showSuggestions, selectedTemplate, jobFilters,
      showTableFiltersPanel, navigationFilters, stageFilters, filteredJobs, statusFilters: STATUS_FILTERS,
    },
    actions: {
      setSearchTerm, setSelectedStatusFilter, setSelectedDaysFilter, setActiveFilter, setBooleanSearch,
      setAdvancedFilters, setSavedSearches, setShowAdvancedSearch, setExpandedSections, setShowSearchHistory,
      setShowSavedSearches, setShowSuggestions, setSelectedTemplate, setJobFilters, setShowTableFiltersPanel,
      handleSearch, handleAISearch, clearAllFilters, clearAllJobFilters, toggleAdvancedFilter, removeAdvancedFilter,
      toggleSection, toggleJobFilter, getActiveAdvancedFiltersCount, getActiveJobFiltersCount,
      saveSearch, saveSearchAsTemplate, handleApplySavedSearch, handleDeleteSavedSearch, handleRenameSavedSearch,
      handleStatusFilterChange, handleTemplateSelection, getJobCountByStatus, getJobCountByStage, searchTemplates,
    },
  }
}
