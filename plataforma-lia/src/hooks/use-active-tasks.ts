/**
 * useActiveTasks — fetches the current user's in-progress tasks via SWR.
 *
 * Onda 30 D: connects TaskContextBar to GET /api/v1/tasks/?status=in_progress
 * (FastAPI). Auto-refreshes every 30s. Maps backend TaskResponse to the
 * frontend ActiveTask shape consumed by TaskContextBar.
 *
 * Backend contract (TaskResponse):
 *   { id, title, task_type, status, priority, created_at, updated_at }
 *
 * Frontend shape (ActiveTask):
 *   { id, title, type, progress?, lastUpdated }
 */
'use client'

import useSWR from 'swr'

export type ActiveTaskType =
  | 'vacancy_creation'
  | 'screening'
  | 'calibration'
  | 'general'

export interface ActiveTask {
  id: string
  title: string
  type: ActiveTaskType
  /** 0-100, derived from backend status */
  progress?: number
  /** ISO-8601 timestamp (uses updated_at when available, else created_at) */
  lastUpdated: string
}

interface TaskResponse {
  id: string
  title: string
  task_type?: string | null
  status?: string | null
  priority?: string | null
  created_at?: string | null
  updated_at?: string | null
}

interface UseActiveTasksReturn {
  tasks: ActiveTask[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const REFRESH_MS = 30_000
const ENDPOINT = '/api/backend-proxy/v1/tasks?status=in_progress&limit=20'

const jsonFetcher = async (url: string): Promise<TaskResponse[]> => {
  const r = await fetch(url, { credentials: 'include' })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  const data: unknown = await r.json()
  // Tolerate either a bare list or {items: [...]} envelope
  if (Array.isArray(data)) return data as TaskResponse[]
  if (data && typeof data === 'object' && 'items' in data) {
    const items = (data as { items?: unknown }).items
    if (Array.isArray(items)) return items as TaskResponse[]
  }
  return []
}

function mapTaskType(raw: string | null | undefined): ActiveTaskType {
  if (!raw) return 'general'
  const normalized = raw.toLowerCase()
  if (normalized.includes('vacancy') || normalized.includes('job_creation')) {
    return 'vacancy_creation'
  }
  if (normalized.includes('screening') || normalized.includes('triagem')) {
    return 'screening'
  }
  if (normalized.includes('calibrat')) return 'calibration'
  return 'general'
}

function mapProgress(status: string | null | undefined): number | undefined {
  if (!status) return undefined
  switch (status.toUpperCase()) {
    case 'PENDING':
      return 0
    case 'IN_PROGRESS':
      return 50
    case 'COMPLETED':
      return 100
    default:
      return undefined
  }
}

export function adaptTaskResponse(raw: TaskResponse): ActiveTask {
  return {
    id: raw.id,
    title: raw.title,
    type: mapTaskType(raw.task_type),
    progress: mapProgress(raw.status),
    lastUpdated: raw.updated_at ?? raw.created_at ?? new Date().toISOString(),
  }
}

export function useActiveTasks(): UseActiveTasksReturn {
  const { data, error, isLoading, mutate } = useSWR<TaskResponse[]>(
    ENDPOINT,
    jsonFetcher,
    {
      refreshInterval: REFRESH_MS,
      revalidateOnFocus: true,
      // keep previous list during refetch so the dropdown does not flash empty
      keepPreviousData: true,
    },
  )

  const tasks: ActiveTask[] = (data ?? []).map(adaptTaskResponse)

  return {
    tasks,
    isLoading,
    error: error instanceof Error ? error.message : null,
    refetch: async () => {
      await mutate()
    },
  }
}
