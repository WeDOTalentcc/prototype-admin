/**
 * @vitest-environment jsdom
 *
 * Task #305 — coverage for the shared 401/403 → relogin redirect now applied
 * to every `/api/lia/*` helper in `wsi-api.ts`. We exercise one of the
 * functions originally left out of bug #303 (`wsiGetCandidateResults`) to
 * make sure the new shared helper kicks in.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import {
  wsiGetCandidateResults,
  wsiGetSession,
} from '@/services/lia-api/wsi-api'

describe('wsi-api shared session handler (task #305)', () => {
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

  it('wsiGetCandidateResults: 401 attaches status and triggers the relogin redirect', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Authentication required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetCandidateResults('cand-1')).rejects.toMatchObject({
      status: 401,
      message: 'Authentication required',
    })

    expect(hrefSetter).toHaveBeenCalledTimes(1)
    expect(hrefSetter).toHaveBeenCalledWith('/login?reason=session_expired')
  })

  it('wsiGetCandidateResults: 5xx attaches status without redirecting', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'kaboom' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetCandidateResults('cand-1')).rejects.toMatchObject({
      status: 503,
      message: 'kaboom',
    })
    expect(hrefSetter).not.toHaveBeenCalled()
  })

  it('wsiGetSession: 403 also redirects to relogin', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Forbidden' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetSession('sess-1')).rejects.toMatchObject({
      status: 403,
      message: 'Forbidden',
    })
    expect(hrefSetter).toHaveBeenCalledWith('/login?reason=session_expired')
  })

  it('does not redirect when already on the login page', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new Proxy(
        { pathname: '/login', href: '' },
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

    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Authentication required' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(wsiGetCandidateResults('cand-1')).rejects.toMatchObject({ status: 401 })
    expect(hrefSetter).not.toHaveBeenCalled()
  })
})
