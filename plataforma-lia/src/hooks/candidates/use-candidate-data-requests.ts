"use client"

import { useMemo, useCallback } from "react"
import useSWR from "swr"
import type { DataRequestStatus, RequestedField } from "@/components/ui/data-request-indicator"

export interface DataRequest {
  id: string
  candidateId: string
  jobVacancyId?: string
  status: DataRequestStatus
  fieldsRequested: RequestedField[]
  fieldsCompleted: RequestedField[]
  createdAt: string
  expiresAt: string | null
  sentAt?: string
  completedAt?: string
  lastReminderAt?: string
  reminderCount: number
}

export interface CandidateDataRequestsResponse {
  requests: DataRequest[]
  activeRequest: DataRequest | null
  hasActiveRequest: boolean
}

const API_BASE = ""

const fetcher = async (url: string): Promise<CandidateDataRequestsResponse> => {
  try {
    const res = await fetch(url)
    if (!res.ok) {
      return { requests: [], activeRequest: null, hasActiveRequest: false }
    }
    return res.json()
  } catch (e) {
    return { requests: [], activeRequest: null, hasActiveRequest: false }
  }
}

interface UseCandidateDataRequestsOptions {
  candidateId: string | undefined
  jobVacancyId?: string
  enabled?: boolean
}

interface UseCandidateDataRequestsResult {
  requests: DataRequest[]
  activeRequest: DataRequest | null
  hasActiveRequest: boolean
  isLoading: boolean
  error: Error | null
  resendRequest: (requestId: string) => Promise<boolean>
  cancelRequest: (requestId: string) => Promise<boolean>
  mutate: () => void
}

export function useCandidateDataRequests({
  candidateId,
  jobVacancyId,
  enabled = true,
}: UseCandidateDataRequestsOptions): UseCandidateDataRequestsResult {
  const shouldFetch = enabled && candidateId && candidateId.length > 0

  const queryParams = new URLSearchParams()
  if (jobVacancyId) queryParams.set('job_vacancy_id', jobVacancyId)
  const queryString = queryParams.toString()

  const endpoint = shouldFetch
    ? `/api/backend-proxy/data-requests/candidate/${candidateId}${queryString ? `?${queryString}` : ''}`
    : null

  const { data, error, isLoading, mutate } = useSWR<CandidateDataRequestsResponse>(
    endpoint,
    fetcher,
    {
      refreshInterval: 60000,
      revalidateOnFocus: true,
      dedupingInterval: 5000,
    }
  )

  const resendRequest = async (requestId: string): Promise<boolean> => {
    try {
      const res = await fetch(`/api/backend-proxy/data-requests/${requestId}/resend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (res.ok) {
        mutate()
        return true
      }
      return false
    } catch (e) {
      return false
    }
  }

  const cancelRequest = async (requestId: string): Promise<boolean> => {
    try {
      const res = await fetch(`/api/backend-proxy/data-requests/${requestId}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (res.ok) {
        mutate()
        return true
      }
      return false
    } catch (e) {
      return false
    }
  }

  return {
    requests: data?.requests || [],
    activeRequest: data?.activeRequest || null,
    hasActiveRequest: data?.hasActiveRequest || false,
    isLoading,
    error: error || null,
    resendRequest,
    cancelRequest,
    mutate,
  }
}

export function getCandidateDataRequests(
  requests: DataRequest[],
  candidateId: string
): DataRequest[] {
  return requests.filter(r => r.candidateId === candidateId)
}

export function getDataRequestStatus(
  requests: DataRequest[],
  candidateId: string
): DataRequestStatus | null {
  const candidateRequests = getCandidateDataRequests(requests, candidateId)
  if (candidateRequests.length === 0) return null

  const activeRequest = candidateRequests.find(r => 
    r.status === 'pending' || r.status === 'partial'
  )
  if (activeRequest) return activeRequest.status

  const latestRequest = candidateRequests.sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )[0]
  
  return latestRequest?.status || null
}

export function getActiveDataRequest(
  requests: DataRequest[],
  candidateId: string
): DataRequest | null {
  const candidateRequests = getCandidateDataRequests(requests, candidateId)
  return candidateRequests.find(r => 
    r.status === 'pending' || r.status === 'partial'
  ) || null
}

export function hasActiveDataRequest(
  requests: DataRequest[],
  candidateId: string
): boolean {
  return getActiveDataRequest(requests, candidateId) !== null
}

export interface BulkDataRequestInfo {
  id: string
  candidateId: string
  jobVacancyId?: string
  status: DataRequestStatus
  isBlocking: boolean
  fieldsRequested: RequestedField[]
  fieldsCompleted: RequestedField[]
  expiresAt: string | null
  createdAt: string
  reminderCount: number
}

export interface BulkCandidateDataRequestsResponse {
  items: BulkDataRequestInfo[]
  byCandidate: Record<string, BulkDataRequestInfo>
}

interface UseBulkCandidateDataRequestsOptions {
  candidateIds: string[]
  vacancyId?: string
  enabled?: boolean
}

interface UseBulkCandidateDataRequestsResult {
  dataRequestsMap: Map<string, BulkDataRequestInfo>
  isLoading: boolean
  error: Error | null
  getDataRequestForCandidate: (candidateId: string) => BulkDataRequestInfo | null
  mutate: () => void
}

const bulkFetcher = async (url: string): Promise<BulkCandidateDataRequestsResponse> => {
  try {
    const res = await fetch(url)
    if (!res.ok) {
      return { items: [], byCandidate: {} }
    }
    return res.json()
  } catch (e) {
    return { items: [], byCandidate: {} }
  }
}

export function useBulkCandidateDataRequests({
  candidateIds,
  vacancyId,
  enabled = true,
}: UseBulkCandidateDataRequestsOptions): UseBulkCandidateDataRequestsResult {
  const validIds = candidateIds.filter(id => id && id.length > 0)
  const shouldFetch = enabled && validIds.length > 0

  const queryParams = new URLSearchParams()
  if (validIds.length > 0) {
    queryParams.set('candidate_ids', validIds.join(','))
  }
  if (vacancyId) {
    queryParams.set('vacancy_id', vacancyId)
  }
  const queryString = queryParams.toString()

  const endpoint = shouldFetch
    ? `/api/backend-proxy/data-requests/by-candidates?${queryString}`
    : null

  const { data, error, isLoading, mutate } = useSWR<BulkCandidateDataRequestsResponse>(
    endpoint,
    bulkFetcher,
    {
      refreshInterval: 60000,
      revalidateOnFocus: false,
      dedupingInterval: 10000,
    }
  )

  const dataRequestsMap = useMemo(() => {
    const map = new Map<string, BulkDataRequestInfo>()
    if (data?.byCandidate) {
      Object.entries(data.byCandidate).forEach(([candidateId, info]) => {
        map.set(candidateId, info)
      })
    }
    return map
  }, [data])

  const getDataRequestForCandidate = useCallback(
    (candidateId: string): BulkDataRequestInfo | null => {
      return dataRequestsMap.get(candidateId) || null
    },
    [dataRequestsMap]
  )

  return {
    dataRequestsMap,
    isLoading,
    error: error || null,
    getDataRequestForCandidate,
    mutate,
  }
}

