import type { KanbanCandidate } from '../types'

export interface KanbanFilterCriteria {
  searchQuery?: string
  kanbanScoreMin?: number | null
  kanbanStatusFilter?: string | null
  kanbanWorkModelFilter?: string | null
  kanbanOriginFilter?: string[] | null
}

export function filterKanbanCandidates(
  candidates: KanbanCandidate[],
  filters: KanbanFilterCriteria
): KanbanCandidate[] {
  return candidates.filter(candidate => {
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase()
      const nameMatch = candidate.name?.toLowerCase().includes(query)
      const emailMatch = candidate.email?.toLowerCase().includes(query)
      const roleMatch = candidate.role?.toLowerCase().includes(query)
      const companyMatch = (candidate.currentCompany || candidate.company)?.toLowerCase().includes(query)
      const locationMatch = candidate.location?.toLowerCase().includes(query)
      const skillsMatch = candidate.skills?.some(skill => skill.toLowerCase().includes(query))
      
      if (!nameMatch && !emailMatch && !roleMatch && !companyMatch && !locationMatch && !skillsMatch) {
        return false
      }
    }

    if (filters.kanbanScoreMin != null && filters.kanbanScoreMin > 0) {
      const candidateScore = candidate.score ?? candidate.fitScore ?? 0
      if (candidateScore < filters.kanbanScoreMin) {
        return false
      }
    }

    if (filters.kanbanStatusFilter) {
      const candidateStatus = (candidate.status || candidate.subStatus || '').toLowerCase().replace(/ /g, '_')
      if (candidateStatus !== filters.kanbanStatusFilter.toLowerCase()) {
        return false
      }
    }

    if (filters.kanbanWorkModelFilter) {
      const workModel = (candidate.workModel || '').toLowerCase()
      if (workModel !== filters.kanbanWorkModelFilter.toLowerCase()) {
        return false
      }
    }

    if (filters.kanbanOriginFilter && filters.kanbanOriginFilter.length > 0) {
      const candidateOrigin = (candidate.origin || '').toLowerCase()
      if (!candidateOrigin || !filters.kanbanOriginFilter.includes(candidateOrigin)) {
        return false
      }
    }

    return true
  })
}
