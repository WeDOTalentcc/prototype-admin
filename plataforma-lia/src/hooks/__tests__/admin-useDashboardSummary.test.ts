/**
 * Tests — useDashboardSummary
 *
 * Covers:
 * - Returns isLoading: true initially
 * - Returns data after successful fetch
 * - Returns error string when service throws ApiClientError
 * - refetch() calls the service again
 * - Re-fetches when startDate changes (re-render with new args)
 */
import React from 'react'
import { SWRConfig } from 'swr'
import { renderHook, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { useDashboardSummary } from '@/hooks/admin/useDashboardSummary'

vi.mock('@/services/admin/dashboard-service', () => ({
  getDashboardSummary: vi.fn(),
  ApiClientError: class ApiClientError extends Error {
    status: number
    isAuthError: boolean
    isForbidden: boolean
    isNetworkError: boolean
    constructor(err: { message: string; status: number; isAuthError: boolean; isForbidden: boolean; isNetworkError: boolean }) {
      super(err.message)
      this.name = 'ApiClientError'
      this.status = err.status
      this.isAuthError = err.isAuthError
      this.isForbidden = err.isForbidden
      this.isNetworkError = err.isNetworkError
    }
  },
}))

import { getDashboardSummary, ApiClientError } from '@/services/admin/dashboard-service'

const swrWrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(SWRConfig, {
    value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false },
  }, children)

const MOCK_SUMMARY = {
  kpis: {
    totalClients: 10,
    activeClients: 8,
    trialClients: 1,
    churnedClients: 1,
    newClientsPeriod: 3,
    mrr: 10000,
    arr: 120000,
    churnRate: 1.5,
  },
  newClients: [],
  trialClients: [],
  churnedClients: [],
}

describe('useDashboardSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns isLoading: true initially', () => {
    ;(getDashboardSummary as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useDashboardSummary(), { wrapper: swrWrapper })
    expect(result.current.isLoading).toBe(true)
  })

  it('returns data after successful fetch', async () => {
    ;(getDashboardSummary as ReturnType<typeof vi.fn>).mockResolvedValue(MOCK_SUMMARY)
    const { result } = renderHook(() => useDashboardSummary(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.data).toEqual(MOCK_SUMMARY)
    expect(result.current.error).toBeNull()
  })

  it('returns error string when service throws ApiClientError', async () => {
    const apiErr = new ApiClientError({
      message: 'Unauthorized',
      status: 401,
      isAuthError: true,
      isForbidden: false,
      isNetworkError: false,
    })
    ;(getDashboardSummary as ReturnType<typeof vi.fn>).mockRejectedValue(apiErr)
    const { result } = renderHook(() => useDashboardSummary(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBe('Unauthorized')
    expect(result.current.data).toBeNull()
  })

  it('refetch() calls the service again', async () => {
    ;(getDashboardSummary as ReturnType<typeof vi.fn>).mockResolvedValue(MOCK_SUMMARY)
    const { result } = renderHook(() => useDashboardSummary(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const callsBefore = (getDashboardSummary as ReturnType<typeof vi.fn>).mock.calls.length
    await result.current.refetch()
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect((getDashboardSummary as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callsBefore)
  })

  it('re-fetches when startDate changes', async () => {
    ;(getDashboardSummary as ReturnType<typeof vi.fn>).mockResolvedValue(MOCK_SUMMARY)
    const date1 = new Date('2026-01-01')
    const date2 = new Date('2026-02-01')
    const { result, rerender } = renderHook(
      ({ startDate }: { startDate: Date }) => useDashboardSummary(startDate),
      { wrapper: swrWrapper, initialProps: { startDate: date1 } }
    )
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const callsAfterFirst = (getDashboardSummary as ReturnType<typeof vi.fn>).mock.calls.length
    rerender({ startDate: date2 })
    await waitFor(() =>
      expect((getDashboardSummary as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callsAfterFirst)
    )
  })
})
