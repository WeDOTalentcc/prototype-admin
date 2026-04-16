/**
 * Bug #303 — coverage for the WSI scores 401 → relogin redirect and
 * for the kanban hook silently swallowing the error instead of letting
 * it bubble into the React error overlay.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'

import { wsiGetCandidatesScores } from '@/services/lia-api/wsi-api'
import { useKanbanDataEffects } from '../useKanbanDataEffects'

const ROUTER_PUSH = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: ROUTER_PUSH, refresh: vi.fn() }),
}))

vi.mock('@/services/lia-api', () => ({
  liaApi: {
    wsiGetCandidatesScores: vi.fn(),
  },
}))

import { liaApi } from '@/services/lia-api'

const mockedScores = liaApi.wsiGetCandidatesScores as unknown as ReturnType<typeof vi.fn>

describe('wsiGetCandidatesScores (bug #303)', () => {
  const realLocation = window.location
  let hrefSetter: ReturnType<typeof vi.fn>

  beforeEach(() => {
    hrefSetter = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new Proxy(
        { pathname: '/pt/jobs/abc', href: '' },
        {
          set(target, prop, value) {
            if (prop === 'href') hrefSetter(value)
            ;(target as Record<string | symbol, unknown>)[prop] = value
            return true
          },
          get(target, prop) {
            return (target as Record<string | symbol, unknown>)[prop]
          },
        },
      ),
    })
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: realLocation })
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('throws an Error with status=401 and triggers the relogin redirect', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ error: 'Authentication required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetCandidatesScores('job-1')).rejects.toMatchObject({
      status: 401,
    })

    expect(hrefSetter).toHaveBeenCalledTimes(1)
    expect(hrefSetter).toHaveBeenCalledWith('/login?reason=session_expired')
  })

  it('attaches status and detail for 5xx without redirecting', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'kaboom' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetCandidatesScores('job-1')).rejects.toMatchObject({
      status: 503,
      message: 'kaboom',
    })
    expect(hrefSetter).not.toHaveBeenCalled()
  })
})

describe('useKanbanDataEffects (bug #303)', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    mockedScores.mockReset()
    // saturation-status fetch — keep it cheap and resolved.
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response('null', { status: 200, headers: { 'Content-Type': 'application/json' } }),
      ),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  function renderEffects() {
    const setCandidatesData = vi.fn((fn: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>) => fn({ stage: [{ id: 'c1' }] }))
    const chatScrollRef = { current: null }
    return renderHook(() =>
      useKanbanDataEffects({
        job: { id: 'j1', backendId: 'j1' } as Record<string, unknown>,
        candidatesData: { stage: [{ id: 'c1' }] },
        setCandidatesData: setCandidatesData as unknown as (
          fn: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>,
        ) => void,
        isLoadingCandidates: false,
        currentJob: { id: 'j1', backendId: 'j1' } as Record<string, unknown>,
        allTableCandidates: [{ id: 'c1' }],
        chatScrollRef: chatScrollRef as unknown as React.RefObject<HTMLElement | null>,
        liaMessages: [],
        isLiaLoading: false,
        setUnifiedModalCandidate: vi.fn(),
        setUnifiedModalType: vi.fn(),
        setUnifiedModalOpen: vi.fn(),
      }),
    )
  }

  it('does not console.error or rethrow when wsi scores reject with 401', async () => {
    const err = Object.assign(new Error('Authentication required'), { status: 401 })
    mockedScores.mockRejectedValueOnce(err)

    renderEffects()

    await waitFor(() => expect(mockedScores).toHaveBeenCalled())
    // Give the rejected promise a tick to settle.
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('swallows 5xx errors so the board keeps rendering', async () => {
    const err = Object.assign(new Error('boom'), { status: 503 })
    mockedScores.mockRejectedValueOnce(err)

    renderEffects()

    await waitFor(() => expect(mockedScores).toHaveBeenCalled())
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
