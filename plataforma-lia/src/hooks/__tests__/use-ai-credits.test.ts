/**
 * Tests — useAiCredits
 *
 * Covers:
 * - Initial loading state
 * - Successful fetch sets balance and summary
 * - Partial failure (balance ok, summary fails)
 * - Network error sets error string
 * - refetch resets error and reloads data
 * - isLoading is false after fetch completes
 */
import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'
import { useAiCredits } from '../use-ai-credits'

const swrWrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(SWRConfig, { value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false } }, children)
)

const MOCK_BALANCE = {
  id: 'bal-1',
  company_id: 'comp-1',
  monthly_limit: 100000,
  current_usage: 25000,
  period_start: '2026-03-01',
  period_end: '2026-03-31',
  overage_allowed: false,
  usage_percentage: 25,
  remaining_tokens: 75000,
  updated_at: '2026-03-15T10:00:00Z',
}

const MOCK_SUMMARY = {
  total_tokens: 25000,
  total_cost_cents: 500,
  total_operations: 42,
  period: '2026-03',
}

global.fetch = vi.fn()

describe('useAiCredits', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('starts with isLoading true', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    expect(result.current.isLoading).toBe(true)
  })

  it('starts with balance null', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    expect(result.current.balance).toBeNull()
  })

  it('starts with summary null', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    expect(result.current.summary).toBeNull()
  })

  it('starts with error null', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    expect(result.current.error).toBeNull()
  })

  // ── Successful fetch ──────────────────────────────────────────────────────

  it('sets balance after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.balance).toEqual(MOCK_BALANCE)
  })

  it('sets summary after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.summary).toEqual(MOCK_SUMMARY)
  })

  it('isLoading is false after fetch completes', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('error is null after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeNull()
  })

  // ── Partial fetch failure ─────────────────────────────────────────────────

  it('sets balance when only balance fetch succeeds', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: false, status: 500 })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.balance).toEqual(MOCK_BALANCE)
    expect(result.current.summary).toBeNull()
  })

  it('sets summary when only summary fetch succeeds', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: false, status: 403 })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.balance).toBeNull()
    expect(result.current.summary).toEqual(MOCK_SUMMARY)
  })

  // ── Network error ─────────────────────────────────────────────────────────

  it('sets error on network failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it('error message reflects the network error thrown', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'))
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBe('fail')
  })

  // ── refetch ────────────────────────────────────────────────────────────────

  it('refetch reloads data', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValue({ ok: true, json: async () => MOCK_BALANCE })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(typeof result.current.refetch).toBe('function')
    await result.current.refetch()
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('refetch clears previous error', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BALANCE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_SUMMARY })
    const { result } = renderHook(() => useAiCredits(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.error).toBeTruthy())
    await result.current.refetch()
    await waitFor(() => expect(result.current.error).toBeNull())
  })
})
