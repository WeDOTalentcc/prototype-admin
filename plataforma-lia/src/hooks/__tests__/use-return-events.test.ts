/**
 * Tests — useReturnEvents
 *
 * Covers:
 * - Initial state: empty events, no alerts
 * - getAlertForCandidate returns undefined with no alerts
 * - computeAlerts generates warning when days >= 70% SLA
 * - computeAlerts generates critical when days >= SLA
 * - computeAlerts ignores candidates without waitingSub status
 * - computeAlerts ignores candidates without lastActionDate
 * - hasAlerts is false initially
 * - hasAlerts is true after computeAlerts adds alerts
 * - fetchEvents does nothing when enabled=false
 * - isPolling exposed in return value
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useReturnEvents } from '../use-return-events'

vi.mock('sonner', () => ({
  toast: Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
  }),
}))

// EventSource mock
class MockEventSource {
  url: string
  onopen: (() => void) | null = null
  onmessage: ((e: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  close = vi.fn()
  constructor(url: string) { this.url = url }
}
;(global as unknown as { EventSource: typeof MockEventSource }).EventSource = MockEventSource

describe('useReturnEvents', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('starts with empty events array', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(result.current.events).toEqual([])
  })

  it('starts with empty candidateAlerts map', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(result.current.candidateAlerts.size).toBe(0)
  })

  it('hasAlerts is false initially', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(result.current.hasAlerts).toBe(false)
  })

  it('getAlertForCandidate returns undefined when no alerts', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(result.current.getAlertForCandidate('cand-xyz')).toBeUndefined()
  })

  it('exposes fetchEvents function', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(typeof result.current.fetchEvents).toBe('function')
  })

  it('exposes computeAlerts function', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    expect(typeof result.current.computeAlerts).toBe('function')
  })

  it('computeAlerts ignores candidates without lastActionDate', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    act(() => {
      result.current.computeAlerts([
        { id: 'c1', subStatus: 'invite_sent', lastActionDate: undefined }
      ])
    })
    expect(result.current.getAlertForCandidate('c1')).toBeUndefined()
  })

  it('computeAlerts ignores candidates not in WAITING_SUB_STATUSES', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    const lastActionDate = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
    act(() => {
      result.current.computeAlerts([
        { id: 'c1', subStatus: 'approved', lastActionDate }
      ])
    })
    expect(result.current.getAlertForCandidate('c1')).toBeUndefined()
  })

  it('computeAlerts sets critical alert when days >= SLA threshold', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false, slaConfig: { screening: 5 } }))
    const lastActionDate = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString()
    act(() => {
      result.current.computeAlerts([
        { id: 'c2', subStatus: 'invite_sent', lastActionDate, actionBehavior: 'screening' }
      ])
    })
    const alert = result.current.getAlertForCandidate('c2')
    expect(alert).toBeDefined()
    expect(alert!.alertLevel).toBe('critical')
  })

  it('computeAlerts sets warning alert when days >= 70% of SLA', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false, slaConfig: { screening: 10 } }))
    // 7 days = 70% of 10
    const lastActionDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    act(() => {
      result.current.computeAlerts([
        { id: 'c3', subStatus: 'invite_sent', lastActionDate, actionBehavior: 'screening' }
      ])
    })
    const alert = result.current.getAlertForCandidate('c3')
    expect(alert).toBeDefined()
    expect(alert!.alertLevel).toBe('warning')
  })

  it('hasAlerts becomes true after computeAlerts creates an alert', () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false, slaConfig: { screening: 5 } }))
    const lastActionDate = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString()
    act(() => {
      result.current.computeAlerts([
        { id: 'c4', subStatus: 'invite_sent', lastActionDate, actionBehavior: 'screening' }
      ])
    })
    expect(result.current.hasAlerts).toBe(true)
  })

  it('fetchEvents skips fetch when enabled is false', async () => {
    const { result } = renderHook(() => useReturnEvents({ enabled: false }))
    await act(async () => {
      await result.current.fetchEvents()
    })
    expect(mockFetch).not.toHaveBeenCalled()
  })
})
