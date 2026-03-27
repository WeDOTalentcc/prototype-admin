import { renderHook, act } from '@testing-library/react'
import { useProactiveInsights } from '../use-proactive-insights'

const MOCK_INSIGHTS = [
  { id: 'i1', title: 'Candidato inativo', message: 'Carlos não respondeu em 3 dias', urgency: 'high', type: 'candidate_follow_up', action_url: null, created_at: '2026-03-15T00:00:00' },
  { id: 'i2', title: 'Pipeline lento', message: 'Entrevistas agendadas há >5 dias', urgency: 'normal', type: 'pipeline_alert', action_url: null, created_at: '2026-03-15T00:00:00' },
]

global.fetch = jest.fn()

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
    jest.clearAllMocks()
    Object.keys(mockSessionStorage).forEach(k => delete mockSessionStorage[k])
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('fetches insights on mount', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_INSIGHTS,
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'company-1')
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
      useProactiveInsights('job-1', null)
    )

    await act(async () => { await Promise.resolve() })
    expect(global.fetch).not.toHaveBeenCalled()
    expect(result.current.insights).toHaveLength(0)
  })

  it('dismiss removes insight from visible list and persists to sessionStorage', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_INSIGHTS,
    })

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'company-1')
    )

    await act(async () => { await Promise.resolve() })
    expect(result.current.insights).toHaveLength(2)

    act(() => { result.current.dismiss('i1') })

    expect(result.current.insights).toHaveLength(1)
    expect(result.current.insights[0].id).toBe('i2')
    expect(mockSessionStorage['proactive_dismissed_insights']).toContain('i1')
  })

  it('filters by job_id in URL when jobId provided', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    renderHook(() => useProactiveInsights('job-42', 'comp-1'))
    await act(async () => { await Promise.resolve() })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('job_id=job-42')
    )
  })

  it('returns empty array on fetch failure (fail-silent)', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network'))

    const { result } = renderHook(() =>
      useProactiveInsights('job-1', 'comp-1')
    )
    await act(async () => { await Promise.resolve() })

    expect(result.current.insights).toHaveLength(0)
  })

  it('auto-refreshes every 5 minutes', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValue({ ok: true, json: async () => [] })

    renderHook(() => useProactiveInsights('job-1', 'comp-1'))

    await act(async () => { await Promise.resolve() })
    expect(global.fetch).toHaveBeenCalledTimes(1)

    await act(async () => { jest.advanceTimersByTime(5 * 60 * 1000) })
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })
})
