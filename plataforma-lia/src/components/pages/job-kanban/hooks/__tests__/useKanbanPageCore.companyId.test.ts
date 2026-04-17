// @vitest-environment jsdom
/**
 * Bug #267 — the kanban page core used to read `user.company` (a field
 * that doesn't exist on AuthenticatedUser) and fall back to the literal
 * string 'demo', causing the backend to reject every proactive-insights
 * request with a UUID parsing error and silently return [].
 *
 * These tests cover the helper that now extracts the real `company_id`
 * from the auth-store user, returning null when it isn't available so
 * the proactive-insights hook can skip the remote fetch entirely.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { getCompanyIdFromUser } from '../useKanbanPageCore'
import { useProactiveInsights } from '@/hooks/ai/use-proactive-insights'

describe('getCompanyIdFromUser (bug #267)', () => {
  it('returns null when the user is not loaded yet', () => {
    expect(getCompanyIdFromUser(null)).toBeNull()
    expect(getCompanyIdFromUser(undefined)).toBeNull()
  })

  it('returns null when the user has no company_id at all', () => {
    expect(getCompanyIdFromUser({ name: 'Ada', email: 'ada@example.com' })).toBeNull()
  })

  it('returns null instead of the legacy "demo" fallback when company_id is empty', () => {
    expect(getCompanyIdFromUser({ company_id: '' })).toBeNull()
  })

  it('does not pick up the legacy "company" field (which holds the company name, not the id)', () => {
    expect(getCompanyIdFromUser({ company: 'WeDO Talent' })).toBeNull()
  })

  it('returns the real UUID when company_id is set on the user', () => {
    const uuid = '550e8400-e29b-41d4-a716-446655440000'
    expect(getCompanyIdFromUser({ company_id: uuid })).toBe(uuid)
  })

  it('ignores non-string company_id values defensively', () => {
    expect(getCompanyIdFromUser({ company_id: 42 })).toBeNull()
    expect(getCompanyIdFromUser({ company_id: { id: 'x' } })).toBeNull()
  })
})

describe('useProactiveInsights wired through the page core (bug #267)', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('does NOT issue any proactive-insights fetch when companyId is null', () => {
    // Simulate the page-core wiring: helper returns null for an
    // unloaded user, and that null is forwarded to useProactiveInsights.
    const fetchSpy = vi.fn(async () =>
      new Response('[]', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    )
    vi.stubGlobal('fetch', fetchSpy)

    const companyId = getCompanyIdFromUser(null) // null
    const { result } = renderHook(() => useProactiveInsights('job-1', companyId))

    expect(companyId).toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(result.current.insights).toEqual([])
  })

  it('does NOT fall back to the legacy "demo" string when only the company name is present', () => {
    const fetchSpy = vi.fn(async () =>
      new Response('[]', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    )
    vi.stubGlobal('fetch', fetchSpy)

    // Legacy shape: only `company` (the name) is set, no UUID.
    const companyId = getCompanyIdFromUser({ company: 'WeDO Talent' })
    renderHook(() => useProactiveInsights('job-1', companyId))

    expect(companyId).toBeNull()
    // The whole point of the bug: never hit the backend with 'demo'.
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})
