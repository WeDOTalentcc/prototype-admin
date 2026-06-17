import { renderHook, act } from '@testing-library/react'
import { useJobReport } from '../use-job-report'

const MOCK_REPORT = {
  vacancy_id: 'job-1',
  vacancy_title: 'Engenheiro de Software',
  funnel_metrics: {
    total_candidates: 50,
    screening: 30,
    interview: 15,
    final: 5,
    hired: 2,
    conversion_rate: 4.0,
    avg_time_to_hire: 18.5,
    cost_per_hire: 0,
  },
  channel_performance: [
    { channel: 'linkedin', candidates: 30, hired: 2 },
    { channel: 'website', candidates: 20, hired: 0 },
  ],
  top_candidates: [
    { name: 'Ana Silva', score: 95, status: 'interview' },
    { name: 'Carlos Mendes', score: 88, status: 'screening' },
  ],
}

global.fetch = vi.fn()

describe('useJobReport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts with null data and no loading', () => {
    const { result } = renderHook(() => useJobReport())
    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetches and returns report data', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_REPORT,
    })

    const { result } = renderHook(() => useJobReport())
    await act(async () => {
      await result.current.fetch('job-1')
    })

    expect(result.current.data).toEqual(MOCK_REPORT)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('sets loading to true during fetch', async () => {
    let resolve: (v: unknown) => void
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValueOnce(
      new Promise(r => { resolve = r })
    )

    const { result } = renderHook(() => useJobReport())
    act(() => { result.current.fetch('job-1') })

    expect(result.current.loading).toBe(true)
    await act(async () => {
      resolve!({ ok: true, json: async () => MOCK_REPORT })
    })
  })

  it('sets error on non-ok response', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 404,
    })

    const { result } = renderHook(() => useJobReport())
    await act(async () => {
      await result.current.fetch('job-1')
    })

    expect(result.current.error).toBeTruthy()
    expect(result.current.data).toBeNull()
  })

  it('sets error on network failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useJobReport())
    await act(async () => {
      await result.current.fetch('job-1')
    })

    expect(result.current.error).toBe('Network error')
  })

  it('does nothing when jobId is empty', async () => {
    const { result } = renderHook(() => useJobReport())
    await act(async () => {
      await result.current.fetch('')
    })

    expect(global.fetch).not.toHaveBeenCalled()
    expect(result.current.loading).toBe(false)
  })
})
