import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { SWRConfig } from 'swr'
import { useProactiveInsights } from '../ai/use-proactive-insights'

const swrWrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(SWRConfig, { value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false } }, children)
)

const MOCK_INSIGHTS = [
  { id: 'i1', title: 'Candidato inativo', message: 'Carlos não respondeu em 3 dias', urgency: 'high', type: 'candidate_follow_up', action_url: null, created_at: '2026-03-15T00:00:00' },
  { id: 'i2', title: 'Pipeline lento', message: 'Entrevistas agendadas há >5 dias', urgency: 'normal', type: 'pipeline_alert', action_url: null, created_at: '2026-03-15T00:00:00' },
]

global.fetch = vi.fn()

// Mock sessionStorage
const mockSessionStorage: Record<string, string> = {}
Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: (k: string) => mockSessionStorage[k] ?? null,
    setItem: (k: string, v: string) => { mockSessionStorage[k] = v },
    removeItem: (k: string) => { delete mockSessionStorage[k] },
  },
  writable: true,
})

describe('useProactiveInsights', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.keys(mockSessionStorage).forEach(k => delete mockSessionStorage[k])
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fetches insights on mount', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_INSIGHTS,
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'company-1'),
      { wrapper: swrWrapper }
    )

    await act(async () => {
      await Promise.resolve()
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('company_id=company-1')
    )
    expect(result.current.insights).toHaveLength(2)
  })

  it('does not fetch when companyId is missing', async () => {
    const { result } = renderHook(() =>
      useProactiveInsights('job-1', null),
      { wrapper: swrWrapper }
    )

    await act(async () => { await Promise.resolve() })
    expect(global.fetch).not.toHaveBeenCalled()
    expect(result.current.insights).toHaveLength(0)
  })

  it('dismiss removes insight from visible list and persists to sessionStorage', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_INSIGHTS,
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'company-1'),
      { wrapper: swrWrapper }
    )

    await act(async () => { await Promise.resolve() })
    expect(result.current.insights).toHaveLength(2)

    act(() => { result.current.dismiss('i1') })

    expect(result.current.insights).toHaveLength(1)
    expect(result.current.insights[0].id).toBe('i2')
    expect(mockSessionStorage['proactive_dismissed_insights']).toContain('i1')
  })

  it('filters by job_id in URL when jobId provided', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    renderHook(() => useProactiveInsights('job-42', 'comp-1'), { wrapper: swrWrapper })
    await act(async () => { await Promise.resolve() })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('job_id=job-42')
    )
  })

  it('returns empty array on fetch failure (fail-silent)', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network'))

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'comp-1'),
      { wrapper: swrWrapper }
    )
    await act(async () => { await Promise.resolve() })

    expect(result.current.insights).toHaveLength(0)
  })

  it('auto-refreshes every 5 minutes', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValue({ ok: true, json: async () => [] })

    renderHook(() => useProactiveInsights('job-1', 'comp-1'), { wrapper: swrWrapper })

    await act(async () => { await Promise.resolve() })
    expect(global.fetch).toHaveBeenCalledTimes(1)

    await act(async () => { vi.advanceTimersByTime(5 * 60 * 1000) })
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('returns empty array when backend response is not an array (defensive guard)', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ detail: 'Authentication required' }),
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'comp-1'),
      { wrapper: swrWrapper }
    )
    await act(async () => { await Promise.resolve() })

    expect(result.current.insights).toHaveLength(0)
  })

  // ── New tests ─────────────────────────────────────────────────────────────

  it('updates fetch URL when jobId changes', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => [],
    })

    const jobId = 'job-first'
    const { rerender } = renderHook(
      ({ jid }: { jid: string }) => useProactiveInsights(jid, 'comp-1'),
      { wrapper: swrWrapper, initialProps: { jid: 'job-first' } }
    )

    await act(async () => { await Promise.resolve() })
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('job_id=job-first')
    )

    rerender({ jid: 'job-second' })
    await act(async () => { await Promise.resolve() })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('job_id=job-second')
    )
  })

  it('dismiss persists all dismissed IDs across multiple dismiss calls', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_INSIGHTS,
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'company-1'),
      { wrapper: swrWrapper }
    )

    await act(async () => { await Promise.resolve() })
    expect(result.current.insights).toHaveLength(2)

    act(() => { result.current.dismiss('i1') })
    act(() => { result.current.dismiss('i2') })

    expect(result.current.insights).toHaveLength(0)
    expect(result.current.dismissed.has('i1')).toBe(true)
    expect(result.current.dismissed.has('i2')).toBe(true)

    const stored = JSON.parse(mockSessionStorage['proactive_dismissed_insights'] ?? '[]') as string[]
    expect(stored).toContain('i1')
    expect(stored).toContain('i2')
  })
})
