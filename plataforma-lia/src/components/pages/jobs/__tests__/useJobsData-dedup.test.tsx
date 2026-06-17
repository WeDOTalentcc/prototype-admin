/**
 * Tests — `useJobsData` concurrency dedup + 429 mapping (Task #345)
 *
 * - Two synchronous calls to `loadBackendJobs` must result in a SINGLE backend
 *   request (the second call joins the in-flight promise instead of spawning
 *   a parallel one). This prevents the focus listener + initial mount effect
 *   from amplifying server load and triggering the 429 cascade.
 * - When the API throws a 429 `HttpError` with `retryAfterMs`, the hook must
 *   surface the user-facing "muitas requisições" message — not the raw
 *   "Failed to load jobs" string.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

const mockListJobVacancies = vi.fn()
const mockGetOverview = vi.fn()

vi.mock('@/services/lia-api', async () => {
  // Re-export the real HttpError so `instanceof` checks inside the hook work.
  const real = await vi.importActual<typeof import('@/services/lia-api/base')>(
    '@/services/lia-api/base',
  )
  return {
    HttpError: real.HttpError,
    liaApi: {
      listJobVacancies: (...args: unknown[]) => mockListJobVacancies(...args),
      getJobVacanciesOverview: (...args: unknown[]) => mockGetOverview(...args),
    },
  }
})

vi.mock('@/lib/pricing', () => ({ formatBRL: (n: number) => `R$ ${n}` }))

import { useJobsData } from '../hooks/useJobsData'
import { HttpError } from '@/services/lia-api/base'

describe('useJobsData — concurrency dedup', () => {
  beforeEach(() => {
    mockListJobVacancies.mockReset()
    mockGetOverview.mockReset()
    mockGetOverview.mockResolvedValue({
      my_jobs: { active: 0, completed: 0, time_to_fill_avg: 0, candidates_interviewed: 0, conversion_rate: 0, candidates_in_funnel: 0, interviews_last_7d: 0, offers_sent: 0 },
      active_jobs: { total: 0, avg_days_open: 0, at_risk: 0, by_urgency: {}, empty_pipeline: 0, deadline_soon: 0 },
      all_jobs: { time_to_fill_avg_90d: 0, success_rate: 0, hired_last_30d: 0, hired_last_90d: 0, within_sla_pct: 0, by_department: {}, trend_weeks: [] },
      insights: [],
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('dedupes concurrent loadBackendJobs calls into a single backend request', async () => {
    let resolveList: ((v: unknown) => void) | null = null
    mockListJobVacancies.mockImplementation(
      () => new Promise((resolve) => { resolveList = resolve }),
    )

    const { result } = renderHook(() => useJobsData())

    // Initial mount triggers one load. Now fire two more in parallel.
    await act(async () => {
      void result.current.actions.loadBackendJobs()
      void result.current.actions.loadBackendJobs()
    })

    // Mount + 2 explicit calls = still ONE backend request — the parallel
    // calls joined the in-flight promise instead of spawning new fetches.
    expect(mockListJobVacancies).toHaveBeenCalledTimes(1)

    await act(async () => {
      resolveList?.({ items: [], source: 'backend' })
    })

    await waitFor(() => {
      expect(result.current.state.isLoadingJobs).toBe(false)
    })
  })

  it('a 429 from listJobVacancies surfaces the rate-limit message (not "Failed to load jobs")', async () => {
    mockListJobVacancies.mockRejectedValue(
      new HttpError(429, 'Failed to fetch job vacancies: Too Many Requests', { retryAfterMs: 4000 }),
    )

    const { result } = renderHook(() => useJobsData())

    await waitFor(() => {
      expect(result.current.state.isLoadingJobs).toBe(false)
    })

    expect(result.current.state.jobsError).toMatch(/Muitas requisições/i)
    expect(result.current.state.jobsError).toMatch(/4s/)
    // Hook called the API exactly once — no internal retry storm now that the
    // local fetchWithRetry is gone (resilience lives in the transport layer).
    expect(mockListJobVacancies).toHaveBeenCalledTimes(1)
  })
})
