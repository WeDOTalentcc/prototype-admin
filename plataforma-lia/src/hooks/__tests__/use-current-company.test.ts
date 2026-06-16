/**
 * Tests — useCurrentCompany
 * Covers:
 * - loading is true on initial render
 * - company and companyId are set after successful fetch
 * - error is set when fetch returns non-ok response
 * - refetch triggers a new fetch
 * - company is null and loading is false on fetch failure
 */
import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { useCurrentCompany } from '../use-current-company'

const swrWrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(SWRConfig, {
    value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false }
  }, children)

const MOCK_COMPANY = {
  id: 'comp-123',
  name: 'Acme Corp',
  trade_name: 'Acme',
  logo_url: 'https://example.com/logo.png',
  plan_id: 'plan-pro',
  status: 'active',
}

global.fetch = vi.fn()

describe('useCurrentCompany', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('loading is true on initial render', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    expect(result.current.loading).toBe(true)
  })

  it('company is null on initial render', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    expect(result.current.company).toBeNull()
  })

  it('companyId is null on initial render', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    expect(result.current.companyId).toBeNull()
  })

  it('error is null on initial render', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    expect(result.current.error).toBeNull()
  })

  // ── Successful fetch ──────────────────────────────────────────────────────

  it('sets company after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.company).toEqual(MOCK_COMPANY)
  })

  it('sets companyId from company.id after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.companyId).toBe('comp-123')
  })

  it('loading is false after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
  })

  it('error is null after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBeNull()
  })

  // ── Non-ok response ───────────────────────────────────────────────────────

  it('sets error when fetch returns non-ok response', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 403,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it('error message contains HTTP status on non-ok response', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 403,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toContain('403')
  })

  // ── Fetch failure (network error) ─────────────────────────────────────────

  it('company is null on fetch failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.company).toBeNull()
  })

  it('loading is false on fetch failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
  })

  it('companyId is null on fetch failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'))
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.companyId).toBeNull()
  })

  // ── refetch ────────────────────────────────────────────────────────────────

  it('refetch triggers a new fetch call', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    const callsAfterMount = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.length
    await result.current.refetch()
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect((global.fetch as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callsAfterMount)
  })

  it('refetch is a function', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_COMPANY,
    })
    const { result } = renderHook(() => useCurrentCompany(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(typeof result.current.refetch).toBe('function')
  })
})
