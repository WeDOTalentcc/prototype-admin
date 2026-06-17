import { HideViewedScope, HideViewedPeriod } from '@/components/search/advanced-filters-modal'

export interface ViewedCandidatesFilter {
  scope: HideViewedScope
  period: HideViewedPeriod
  projectId?: string
  userId?: string
  userEmail?: string
  companyId?: string
}

export interface ViewedCandidatesResponse {
  candidate_ids: string[]
  count: number
}

function isShortlistScope(scope: HideViewedScope): boolean {
  return scope.startsWith('shortlisted_')
}

export async function getViewedCandidateIds(
  filter: ViewedCandidatesFilter
): Promise<string[]> {
  if (filter.scope === "dont_hide") {
    return []
  }

  try {
    const response = await fetch('/api/backend-proxy/candidates/viewed/filtered', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scope: filter.scope,
        period: filter.period,
        project_id: filter.projectId,
        user_id: filter.userId,
        user_email: filter.userEmail,
        company_id: filter.companyId,
      }),
    })

    if (!response.ok) {
      return []
    }

    const data: ViewedCandidatesResponse = await response.json()
    return data.candidate_ids || []
  } catch (error) {
    return []
  }
}

export async function getShortlistedCandidateIds(
  scope: HideViewedScope,
  userId: string,
  companyId: string,
  projectId?: string,
  period: HideViewedPeriod = 'all_time',
  userEmail?: string
): Promise<string[]> {
  if (!isShortlistScope(scope)) {
    return []
  }

  return getViewedCandidateIds({
    scope,
    period,
    projectId,
    userId,
    userEmail,
    companyId,
  })
}

export function filterOutViewedCandidates<T extends { id: string }>(
  candidates: T[],
  viewedIds: string[]
): T[] {
  if (!viewedIds.length) return candidates
  
  const viewedSet = new Set(viewedIds)
  return candidates.filter(candidate => !viewedSet.has(candidate.id))
}

export async function markCandidateAsViewed(
  candidateId: string,
  projectId?: string
): Promise<boolean> {
  try {
    const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        viewed_at: new Date().toISOString(),
      }),
    })

    return response.ok
  } catch (error) {
    return false
  }
}

export async function markCandidateAsShortlisted(
  candidateId: string,
  projectId?: string
): Promise<boolean> {
  try {
    const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/shortlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        shortlisted_at: new Date().toISOString(),
      }),
    })

    return response.ok
  } catch (error) {
    return false
  }
}
