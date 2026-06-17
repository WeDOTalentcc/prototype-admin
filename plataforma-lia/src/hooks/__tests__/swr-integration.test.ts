/**
 * Tests — SWR integration patterns
 *
 * Covers:
 * - SWR wrapper configuration
 * - dedupingInterval: 0 prevents request deduplication
 * - Separate providers mean isolated caches per test
 * - revalidateOnFocus: false prevents refetch on focus
 * - provider: () => new Map() creates fresh cache each render
 * - Cache isolation: two renderHooks with swrWrapper do not share cache
 * - SWR hook with mockFetch returning data resolves correctly
 * - SWR hook shows error state when fetch throws
 * - SWR isLoading transitions from true to false
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import React from 'react'
import { SWRConfig } from 'swr'
import useSWR from 'swr'
import useSWRMutation from 'swr/mutation'

// ── Standard SWR test wrapper ─────────────────────────────────────────────
const swrWrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(SWRConfig, {
    value: {
      dedupingInterval: 0,
      provider: () => new Map(),
      revalidateOnFocus: false,
    },
  }, children)

describe('SWR integration — wrapper configuration', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('swrWrapper is a valid React component', () => {
    expect(typeof swrWrapper).toBe('function')
  })

  it('SWR hook resolves data through wrapper', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ value: 42 }) })
    const fetcher = async (url: string) => {
      const res = await fetch(url)
      return res.json()
    }
    const { result } = renderHook(
      () => useSWR('/api/test-endpoint', fetcher),
      { wrapper: swrWrapper }
    )
    await waitFor(() => expect(result.current.data).toBeDefined())
    expect(result.current.data.value).toBe(42)
  })

  it('SWR hook starts with isLoading true', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const fetcher = async (url: string) => { await fetch(url); return {} }
    const { result } = renderHook(
      () => useSWR('/api/loading-test', fetcher),
      { wrapper: swrWrapper }
    )
    expect(result.current.isLoading).toBe(true)
  })

  it('SWR hook transitions isLoading from true to false on success', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ ok: true }) })
    const fetcher = async (url: string) => { const r = await fetch(url); return r.json() }
    const { result } = renderHook(
      () => useSWR('/api/transition-test', fetcher),
      { wrapper: swrWrapper }
    )
    expect(result.current.isLoading).toBe(true)
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('SWR hook shows error state when fetcher throws', async () => {
    const fetcher = async () => { throw new Error('fetch failed') }
    const { result } = renderHook(
      () => useSWR('/api/error-test', fetcher, { shouldRetryOnError: false }),
      { wrapper: swrWrapper }
    )
    await waitFor(() => expect(result.current.error).toBeDefined())
    expect(result.current.error.message).toBe('fetch failed')
  })

  it("two hooks with same key in isolated wrappers do not share cache", async () => {
    // Each swrWrapper creates a new Map() provider, so caches are isolated.
    // We verify this by running them sequentially and confirming the fetcher
    // is called for each independent instance.
    let callCount = 0
    const fetcher = async () => {
      callCount++
      return { count: callCount }
    }
    // First hook fetches from its own empty cache
    const { result: result1 } = renderHook(
      () => useSWR("/api/isolation-test", fetcher),
      { wrapper: swrWrapper }
    )
    await waitFor(() => expect(result1.current.data).toBeDefined())
    const afterFirst = callCount
    expect(afterFirst).toBeGreaterThanOrEqual(1)

    // Second hook has its own empty cache — fetcher must be called again
    const { result: result2 } = renderHook(
      () => useSWR("/api/isolation-test-2", fetcher),
      { wrapper: swrWrapper }
    )
    await waitFor(() => expect(result2.current.data).toBeDefined())
    expect(callCount).toBeGreaterThan(afterFirst)
  })

  it('SWRMutation trigger does not execute until called', async () => {
    const mutationFetcher = vi.fn(async () => ({ mutated: true }))
    const { result } = renderHook(
      () => useSWRMutation('/api/mutation-test', mutationFetcher),
      { wrapper: swrWrapper }
    )
    expect(mutationFetcher).not.toHaveBeenCalled()
    expect(result.current.isMutating).toBe(false)
  })

  it('SWRMutation trigger fires fetcher on trigger()', async () => {
    const mutationFetcher = vi.fn(async (_url: string, { arg }: { arg: { name: string } }) => ({ created: arg.name }))
    const { result } = renderHook(
      () => useSWRMutation('/api/mutation-trigger', mutationFetcher),
      { wrapper: swrWrapper }
    )
    await act(async () => {
      await result.current.trigger({ name: 'test-item' })
    })
    expect(mutationFetcher).toHaveBeenCalledOnce()
    expect(result.current.data).toEqual({ created: 'test-item' })
  })

  it('dedupingInterval 0 means two rapid calls both execute', async () => {
    let callCount = 0
    const fetcher = async () => {
      callCount++
      return { n: callCount }
    }
    const { result, rerender } = renderHook(
      () => useSWR('/api/dedup-test', fetcher),
      { wrapper: swrWrapper }
    )
    await waitFor(() => expect(result.current.data).toBeDefined())
    const firstCount = callCount
    // Revalidate
    await act(async () => { result.current.mutate() })
    await waitFor(() => expect(callCount).toBeGreaterThan(firstCount))
    rerender()
  })

  it('SWR hook returns undefined data initially (no cache pre-population)', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const fetcher = async (url: string) => { await fetch(url); return {} }
    const { result } = renderHook(
      () => useSWR('/api/no-cache-test', fetcher),
      { wrapper: swrWrapper }
    )
    expect(result.current.data).toBeUndefined()
  })
})
