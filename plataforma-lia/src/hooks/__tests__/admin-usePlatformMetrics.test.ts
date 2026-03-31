/**
 * Tests — usePlatformMetrics
 *
 * Covers:
 * - Returns isLoading: true initially
 * - Maps service response to expected return shape (metrics.revenue, metrics.clients, etc.)
 * - Returns error when service throws
 * - refetch() calls the service again
 */
import React from 'react'
import { SWRConfig } from 'swr'
import { renderHook, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { usePlatformMetrics } from '@/hooks/admin/usePlatformMetrics'

vi.mock('@/services/admin/saas-metrics-service', () => ({
  saasMetricsClientService: {
    getPlatformMetrics: vi.fn(),
  },
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

import { saasMetricsClientService, ApiClientError } from '@/services/admin/saas-metrics-service'

const swrWrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(SWRConfig, {
    value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false },
  }, children)

const MOCK_PLATFORM_METRICS = {
  revenue: {
    mrr: 50000,
    arr: 600000,
    growthRate: 5.2,
    mrrChange: 2500,
  },
  clients: {
    activeClients: 40,
    trialClients: 5,
    churnedClients: 2,
    totalClients: 47,
    churnRate: 1.8,
  },
  usage: {
    totalAITokens: 1000000,
    totalUsers: 200,
    avgTokensPerClient: 25000,
    activeSessionsToday: 35,
  },
  costs: {
    infrastructureCost: 3000,
    aiApiCost: 1500,
    totalMonthlyCost: 4500,
    costPerClient: 112.5,
  },
  lastUpdated: '2026-03-30T10:00:00Z',
}

describe('usePlatformMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns isLoading: true initially', () => {
    ;(saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>)
      .mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => usePlatformMetrics(), { wrapper: swrWrapper })
    expect(result.current.isLoading).toBe(true)
  })

  it('maps service response to expected return shape', async () => {
    ;(saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>)
      .mockResolvedValue(MOCK_PLATFORM_METRICS)
    const { result } = renderHook(() => usePlatformMetrics(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.metrics).not.toBeNull()
    expect(result.current.metrics!.revenue).toEqual(MOCK_PLATFORM_METRICS.revenue)
    expect(result.current.metrics!.clients).toEqual(MOCK_PLATFORM_METRICS.clients)
    expect(result.current.metrics!.usage).toEqual(MOCK_PLATFORM_METRICS.usage)
    expect(result.current.metrics!.costs).toEqual(MOCK_PLATFORM_METRICS.costs)
    expect(result.current.error).toBeNull()
  })

  it('returns error string when service throws ApiClientError', async () => {
    const apiErr = new ApiClientError({
      message: 'Forbidden',
      status: 403,
      isAuthError: false,
      isForbidden: true,
      isNetworkError: false,
    })
    ;(saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>)
      .mockRejectedValue(apiErr)
    const { result } = renderHook(() => usePlatformMetrics(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBe('Forbidden')
    expect(result.current.metrics).toBeNull()
  })

  it('returns error string when service throws generic Error', async () => {
    ;(saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>)
      .mockRejectedValue(new Error('Network failure'))
    const { result } = renderHook(() => usePlatformMetrics(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBe('Network failure')
  })

  it('refetch() calls the service again', async () => {
    ;(saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>)
      .mockResolvedValue(MOCK_PLATFORM_METRICS)
    const { result } = renderHook(() => usePlatformMetrics(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const callsBefore = (saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>).mock.calls.length
    await result.current.refetch()
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect((saasMetricsClientService.getPlatformMetrics as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callsBefore)
  })
})
