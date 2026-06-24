import React from "react"
import { setLiaPagination } from "@/lib/lia-context-store"
import type { Candidate } from "../types"
import type { TableFilters } from "@/hooks/candidates/use-candidate-filters"

type FilterMatchCandidate = {
  skills?: string[]
  location?: string
  position?: string
  current_title?: string
  current_company?: string
  level?: string
  workHistory?: Array<{ company?: string }>
}

/**
 * Fase 3: grau de match dos filtros ativos (exatidao da referencia).
 * Conta quantas CONDICOES de filtro multi-valor o candidato satisfaz
 * (ex: skills [python, aws] -> 2 se casa as duas). Usado como re-score
 * DENTRO do conjunto ja filtrado: quem satisfaz mais condicoes sobe.
 * Espelha a logica de match de useCandidatesFilterSort (includes, case-insensitive).
 */
export function countActiveFilterMatches(
  candidate: FilterMatchCandidate,
  tableFilters: { skills?: string[]; locations?: string[]; jobTitles?: string[]; companies?: string[]; seniorityLevels?: string[] },
  advancedFilters: Record<string, string[]>,
): number {
  const lc = (s: unknown) => String(s ?? "").toLowerCase()
  const candSkills = (candidate.skills || []).map(lc)
  const candLoc = lc(candidate.location)
  const candTitle = lc(candidate.position || candidate.current_title)
  const candCompany = lc(candidate.workHistory?.[0]?.company || candidate.current_company)
  let matches = 0
  for (const sf of [...(tableFilters.skills || []), ...(advancedFilters.skills || [])]) {
    if (candSkills.some((cs) => cs.includes(lc(sf)))) matches++
  }
  for (const lf of [...(tableFilters.locations || []), ...(advancedFilters.locations || [])]) {
    if (candLoc.includes(lc(lf))) matches++
  }
  for (const tf of [...(tableFilters.jobTitles || []), ...(advancedFilters.job_titles || [])]) {
    if (candTitle.includes(lc(tf))) matches++
  }
  for (const cf of [...(tableFilters.companies || []), ...(advancedFilters.companies || [])]) {
    if (candCompany.includes(lc(cf))) matches++
  }
  for (const sl of (tableFilters.seniorityLevels || [])) {
    if (candTitle.includes(lc(sl)) || lc(candidate.level).includes(lc(sl))) matches++
  }
  return matches
}

export interface UseCandidatesFilterSortParams {
  candidates: Candidate[]
  searchTerm: string
  hasSearchResults: boolean
  quickFilters: Set<string>
  columnFilters: {
    position: string[]
    company: string[]
    location: string[]
    scoreRange: string[]
    bigFive?: Record<string, string>
  }
  advancedFilters: Record<string, string[]>
  tableFilters: TableFilters
  sortBy: string
  sortOrder: 'asc' | 'desc'
  searchSortBy: string
  searchFeedbacks: Record<string, string>
  displayedResultsCount: number
  showSearchResults: boolean
  currentPage: number
  itemsPerPage: number
  showOnlyNew?: boolean
  viewedCandidateIds?: Set<string>
}

export function useCandidatesFilterSort(params: UseCandidatesFilterSortParams) {
  const {
    candidates, searchTerm, hasSearchResults, quickFilters,
    columnFilters, advancedFilters, tableFilters,
    sortBy, sortOrder, searchSortBy, searchFeedbacks,
    displayedResultsCount, showSearchResults, currentPage, itemsPerPage,
    showOnlyNew, viewedCandidateIds,
  } = params

  const filteredCandidates = candidates.filter(candidate => {
    if (showOnlyNew && viewedCandidateIds?.has(candidate.id)) {
      return false
    }

    if (tableFilters.locations.length > 0) {
      const loc = candidate.location || ''
      const city = candidate.location_city || ''
      const state = candidate.location_state || ''
      const matchesLocation = tableFilters.locations.some(filterLoc => {
        const filterLower = filterLoc.toLowerCase()
        return loc.toLowerCase().includes(filterLower) ||
               city.toLowerCase().includes(filterLower) ||
               state.toLowerCase().includes(filterLower)
      })
      if (!matchesLocation) return false
    }

    if (tableFilters.jobTitles.length > 0) {
      const title = candidate.current_title || candidate.position || ''
      const matchesTitle = tableFilters.jobTitles.some(filterTitle =>
        title.toLowerCase().includes(filterTitle.toLowerCase())
      )
      if (!matchesTitle) return false
    }

    if (tableFilters.skills.length > 0) {
      const candidateSkills = candidate.technical_skills || candidate.skills || []
      const hasMatchingSkill = tableFilters.skills.some(filterSkill =>
        candidateSkills.some(cs => cs.toLowerCase().includes(filterSkill.toLowerCase()))
      )
      if (!hasMatchingSkill) return false
    }

    if (tableFilters.industries.length > 0) {
      const industry = (candidate as Candidate & { industry?: string }).industry || ''
      const matchesIndustry = tableFilters.industries.some(filterIndustry =>
        industry.toLowerCase().includes(filterIndustry.toLowerCase())
      )
      if (!matchesIndustry) {
        const company = candidate.current_company || ''
        const matchesCompanyIndustry = tableFilters.industries.some(filterIndustry =>
          company.toLowerCase().includes(filterIndustry.toLowerCase())
        )
        if (!matchesCompanyIndustry) return false
      }
    }

    if (tableFilters.seniorityLevels.length > 0) {
      const level = candidate.seniority_level || ''
      const position = candidate.position || ''
      const matchesSeniority = tableFilters.seniorityLevels.some(filterLevel => 
        level.toLowerCase().includes(filterLevel.toLowerCase()) ||
        position.toLowerCase().includes(filterLevel.toLowerCase())
      )
      if (!matchesSeniority) return false
    }

    if (tableFilters.companies && tableFilters.companies.length > 0) {
      const company = candidate.current_company || ''
      const matchesCompany = tableFilters.companies.some(filterCompany =>
        company.toLowerCase().includes(filterCompany.toLowerCase())
      )
      if (!matchesCompany) {
        const workHistoryCompany = candidate.workHistory?.[0]?.company || ''
        const matchesWorkHistory = tableFilters.companies.some(filterCompany =>
          workHistoryCompany.toLowerCase().includes(filterCompany.toLowerCase())
        )
        if (!matchesWorkHistory) return false
      }
    }

    if (searchTerm && !hasSearchResults && !searchTerm.startsWith('empresa:') && !searchTerm.startsWith('empresas:')) {
      const search = searchTerm.toLowerCase()
      const matches =
        candidate.name.toLowerCase().includes(search) ||
        candidate.position.toLowerCase().includes(search) ||
        (candidate.candidateId && candidate.candidateId.toLowerCase().includes(search)) ||
        candidate.skills.some(skill => skill.toLowerCase().includes(search))
      if (!matches) return false
    }

    if (searchTerm.startsWith('empresa:"') || searchTerm.startsWith('empresas:')) {
      const companyMatch = searchTerm.match(/empresa:"([^"]+)"/) || searchTerm.match(/empresas:(.+)/)
      if (companyMatch) {
        const searchCompanies = companyMatch[1].split(',').map(c => c.trim())
        const candidateCompany = candidate.workHistory?.[0]?.company || ''
        if (!searchCompanies.some(company =>
          candidateCompany.toLowerCase().includes(company.toLowerCase())
        )) {
          return false
        }
      }
    }

    if (quickFilters.size > 0) {
      const hasQuickFilter = Array.from(quickFilters).some(filter => {
        switch (filter) {
          case 'frontend':
            return candidate.skills.some(skill => ['React', 'Vue', 'Angular', 'JavaScript'].includes(skill))
          case 'backend':
            return candidate.skills.some(skill => ['Node.js', 'Python', 'Java', 'PHP'].includes(skill))
          case 'design':
            return candidate.skills.some(skill => ['Figma', 'Sketch', 'Adobe', 'Design'].includes(skill))
          case 'senior':
            return candidate.experience >= 5
          case 'remoto':
            return candidate.location.includes('Remoto') || candidate.location.includes('Remote')
          default:
            return true
        }
      })
      if (!hasQuickFilter) return false
    }

    if (columnFilters.position.length > 0 && !columnFilters.position.includes(candidate.position)) {
      return false
    }

    if (columnFilters.company.length > 0) {
      const company = candidate.workHistory?.[0]?.company || ''
      if (!columnFilters.company.includes(company)) return false
    }

    if (columnFilters.location.length > 0 && !columnFilters.location.includes(candidate.location)) {
      return false
    }

    if (columnFilters.scoreRange.length > 0) {
      const score = candidate.liaAnalysis?.score || candidate.score
      let scoreRange: string
      if (score >= 90) scoreRange = '90-100%'
      else if (score >= 80) scoreRange = '80-89%'
      else if (score >= 70) scoreRange = '70-79%'
      else scoreRange = '60-69%'
      if (!columnFilters.scoreRange.includes(scoreRange)) return false
    }

    if (columnFilters.bigFive) {
      const hasActiveBigFiveFilters = Object.values(columnFilters.bigFive).some(v => v && v !== '')
      if (hasActiveBigFiveFilters) {
        const bigFive = candidate.bigFive
        if (!bigFive) return false
        const getLevel = (score: number) => {
          if (score >= 80) return 'alto'
          if (score >= 60) return 'medio'
          return 'baixo'
        }
        for (const [dimension, filterLevel] of Object.entries(columnFilters.bigFive)) {
          if (filterLevel && filterLevel !== '') {
            const score = bigFive[dimension as keyof typeof bigFive]
            if (!score || getLevel(score) !== filterLevel) return false
          }
        }
      }
    }

    if (advancedFilters.work_models.length > 0) {
      const workModelFilters = advancedFilters.work_models.filter(filter =>
        ['remoto', 'híbrido', 'presencial'].includes(filter)
      )
      if (workModelFilters.length > 0 && !workModelFilters.includes(candidate.workModel)) return false
    }

    if (advancedFilters.skills.length > 0) {
      const hasSkill = advancedFilters.skills.some(skill =>
        candidate.skills.some(candidateSkill =>
          candidateSkill.toLowerCase().includes(skill.toLowerCase())
        )
      )
      if (!hasSkill) return false
    }

    if (advancedFilters.companies.length > 0) {
      const candidateCompany = candidate.workHistory?.[0]?.company || ''
      const hasCompany = advancedFilters.companies.some(company =>
        candidateCompany.toLowerCase().includes(company.toLowerCase())
      )
      if (!hasCompany) return false
    }

    if (advancedFilters.locations.length > 0) {
      const hasLocation = advancedFilters.locations.some(location =>
        candidate.location.toLowerCase().includes(location.toLowerCase())
      )
      if (!hasLocation) return false
    }

    if (advancedFilters.job_titles.length > 0) {
      const hasJobTitle = advancedFilters.job_titles.some(title =>
        candidate.position.toLowerCase().includes(title.toLowerCase())
      )
      if (!hasJobTitle) return false
    }

    if (tableFilters.hasEmail) {
      if (!(candidate.email || candidate.has_email)) return false
    }
    if (tableFilters.hasPhone) {
      if (!(candidate.phone || candidate.mobile_phone || candidate.has_phone)) return false
    }
    if (tableFilters.hasLinkedin) {
      if (!(candidate.linkedin_url || candidate.linkedin)) return false
    }
    if (tableFilters.remoteOnly) {
      const isRemote = candidate.workModel === 'remoto' || 
                       candidate.is_remote || 
                       candidate.location?.toLowerCase().includes('remoto')
      if (!isRemote) return false
    }
    if (tableFilters.minExperience !== undefined) {
      const experience = candidate.experience || candidate.years_of_experience || 0
      if (experience < tableFilters.minExperience) return false
    }
    if (tableFilters.maxExperience !== undefined) {
      const experience = candidate.experience || candidate.years_of_experience || 0
      if (experience > tableFilters.maxExperience) return false
    }
    if (tableFilters.minScore !== undefined) {
      const score = candidate.liaAnalysis?.score || candidate.score || candidate.lia_score || 0
      if (score < tableFilters.minScore) return false
    }
    if (tableFilters.maxScore !== undefined) {
      const score = candidate.liaAnalysis?.score || candidate.score || candidate.lia_score || 0
      if (score > tableFilters.maxScore) return false
    }
    if (tableFilters.workModels.length > 0) {
      if (!tableFilters.workModels.includes(candidate.workModel)) return false
    }
    if (tableFilters.contractTypes.length > 0) {
      if (!tableFilters.contractTypes.includes(candidate.contractType)) return false
    }
    if (tableFilters.sources.length > 0) {
      const source = candidate.source || ''
      const matchesSource = tableFilters.sources.some(filterSource =>
        source.toLowerCase().includes(filterSource.toLowerCase())
      )
      if (!matchesSource) return false
    }
    if (tableFilters.hasGithub) {
      if (!candidate.github_url) return false
    }
    if (tableFilters.hasPortfolio) {
      if (!candidate.portfolio_url) return false
    }
    if (tableFilters.softSkills.length > 0) {
      const candidateSoftSkills = candidate.soft_skills || []
      const hasMatchingSoftSkill = tableFilters.softSkills.some(skill =>
        candidateSoftSkills.some(cs => cs.toLowerCase().includes(skill.toLowerCase()))
      )
      if (!hasMatchingSoftSkill) return false
    }
    if (tableFilters.certifications.length > 0) {
      const candidateCertifications = candidate.certifications || []
      const hasMatchingCertification = tableFilters.certifications.some(cert =>
        candidateCertifications.some(cc => cc.toLowerCase().includes(cert.toLowerCase()))
      )
      if (!hasMatchingCertification) return false
    }
    if (tableFilters.willingToRelocate !== null) {
      if (candidate.willing_to_relocate !== tableFilters.willingToRelocate) return false
    }
    if (tableFilters.mobility !== null) {
      if (candidate.mobility !== tableFilters.mobility) return false
    }
    if (tableFilters.updatedAtFrom) {
      const updatedAt = candidate.updated_at ? new Date(candidate.updated_at) : null
      if (!updatedAt || updatedAt < new Date(tableFilters.updatedAtFrom)) return false
    }
    if (tableFilters.updatedAtTo) {
      const updatedAt = candidate.updated_at ? new Date(candidate.updated_at) : null
      if (!updatedAt || updatedAt > new Date(tableFilters.updatedAtTo)) return false
    }
    if (tableFilters.lastContactedFrom) {
      const lastContacted = candidate.last_contacted_at ? new Date(candidate.last_contacted_at) : null
      if (!lastContacted || lastContacted < new Date(tableFilters.lastContactedFrom)) return false
    }
    if (tableFilters.lastContactedTo) {
      const lastContacted = candidate.last_contacted_at ? new Date(candidate.last_contacted_at) : null
      if (!lastContacted || lastContacted > new Date(tableFilters.lastContactedTo)) return false
    }

    return true
  })

  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    let aValue: string | number | boolean | undefined = a[sortBy as keyof Candidate] as string | number | boolean | undefined
    let bValue: string | number | boolean | undefined = b[sortBy as keyof Candidate] as string | number | boolean | undefined

    if (sortBy === 'score_lia') {
      aValue = a.liaAnalysis?.score || a.score
      bValue = b.liaAnalysis?.score || b.score
    }

    if (sortBy === 'match_score') {
      // P1-4: a coluna "Match" exibe candidate.score; o id 'match_score' nao
      // existe no objeto Candidate. Mapeia para o score real para a ordenacao
      // por header funcionar (antes caia em a['match_score']=undefined = no-op).
      aValue = a.lia_score ?? a.score ?? 0
      bValue = b.lia_score ?? b.score ?? 0
    }

    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = (bValue as string).toLowerCase()
    }

    const aComp = aValue as string | number
    const bComp = bValue as string | number
    if (sortOrder === 'asc') {
      return aComp > bComp ? 1 : -1
    } else {
      return aComp < bComp ? 1 : -1
    }
  })

  const getPaginatedCandidates = () => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return {
      candidates: sortedCandidates.slice(startIndex, endIndex),
      total: sortedCandidates.length,
      totalPages: Math.ceil(sortedCandidates.length / itemsPerPage)
    }
  }

  const paginatedCandidates = getPaginatedCandidates().candidates

  // P0-2 (2026-06-18): keep LIA aware of pagination state
  React.useEffect(() => {
    const totalPages = Math.ceil(sortedCandidates.length / itemsPerPage)
    setLiaPagination({
      current_page: currentPage,
      total_pages: totalPages,
      page_size: itemsPerPage,
      total_items: sortedCandidates.length,
    })
    return () => setLiaPagination(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, itemsPerPage, sortedCandidates])

  const searchDisplayCandidates = React.useMemo(() => {
    const sorted = [...sortedCandidates]
    
    switch (searchSortBy) {
      case 'score_desc':
        sorted.sort((a, b) => (b.lia_score || b.score || 0) - (a.lia_score || a.score || 0))
        break
      case 'score_asc':
        sorted.sort((a, b) => (a.lia_score || a.score || 0) - (b.lia_score || b.score || 0))
        break
      case 'name_asc':
        sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        break
      case 'name_desc':
        sorted.sort((a, b) => (b.name || '').localeCompare(a.name || ''))
        break
      case 'experience_desc':
        sorted.sort((a, b) => (b.experience || b.years_of_experience || 0) - (a.experience || a.years_of_experience || 0))
        break
      default:
        break
    }
    
    // Fase 3: re-score local por grau de match dos filtros ativos (estavel:
    // preserva a ordem do switch como desempate; feedback tier abaixo domina).
    sorted.sort(
      (a, b) =>
        countActiveFilterMatches(b as FilterMatchCandidate, tableFilters, advancedFilters) -
        countActiveFilterMatches(a as FilterMatchCandidate, tableFilters, advancedFilters),
    )
    const feedbackKeys = Object.keys(searchFeedbacks)
    if (feedbackKeys.length > 0) {
      sorted.sort((a, b) => {
        const fbA = searchFeedbacks[a.id]
        const fbB = searchFeedbacks[b.id]
        const priorityA = fbA === 'like' ? 0 : fbA === 'dislike' ? 2 : 1
        const priorityB = fbB === 'like' ? 0 : fbB === 'dislike' ? 2 : 1
        return priorityA - priorityB
      })
    }
    
    return sorted.slice(0, displayedResultsCount)
  }, [sortedCandidates, searchSortBy, displayedResultsCount, searchFeedbacks, tableFilters, advancedFilters])

  const visibleCandidates = showSearchResults ? searchDisplayCandidates : paginatedCandidates

  return {
    filteredCandidates,
    sortedCandidates,
    paginatedCandidates,
    searchDisplayCandidates,
    visibleCandidates,
    getPaginatedCandidates,
  }
}
