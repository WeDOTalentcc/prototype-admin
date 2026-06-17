/**
 * Tests — useNavigationPersistence
 *
 * Covers:
 * - saveJobsState persists data in localStorage
 * - getJobsState retrieves saved state
 * - saveTalentFunnelState persists funnel state
 * - getTalentFunnelState retrieves funnel state
 * - clearState removes specific section
 * - clearState without arg removes all state
 * - expired state (past TTL) is cleaned up on read
 * - missing key returns empty object
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useNavigationPersistence } from '../use-navigation-persistence'

const STORAGE_KEY = 'lia-navigation-state'

describe('useNavigationPersistence', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('returns hook with all expected functions', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    expect(typeof result.current.saveJobsState).toBe('function')
    expect(typeof result.current.getJobsState).toBe('function')
    expect(typeof result.current.saveTalentFunnelState).toBe('function')
    expect(typeof result.current.getTalentFunnelState).toBe('function')
    expect(typeof result.current.clearState).toBe('function')
  })

  it('getJobsState returns undefined when nothing saved', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    expect(result.current.getJobsState()).toBeUndefined()
  })

  it('saveJobsState persists jobId to localStorage', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveJobsState('job-123', 'kanban')
    const raw = localStorage.getItem(STORAGE_KEY)
    expect(raw).toBeTruthy()
    const parsed = JSON.parse(raw!)
    expect(parsed.jobs.lastJobId).toBe('job-123')
    expect(parsed.jobs.lastView).toBe('kanban')
  })

  it('getJobsState retrieves previously saved state', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveJobsState('job-456', 'table', 'tab-candidates')
    const state = result.current.getJobsState()
    expect(state).toBeDefined()
    expect(state!.lastJobId).toBe('job-456')
    expect(state!.lastView).toBe('table')
    expect(state!.lastTab).toBe('tab-candidates')
  })

  it('saveTalentFunnelState persists funnel tab to localStorage', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveTalentFunnelState('favorites', 'engineer')
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = JSON.parse(raw!)
    expect(parsed.talentFunnel.lastTab).toBe('favorites')
    expect(parsed.talentFunnel.lastSearchQuery).toBe('engineer')
  })

  it('getTalentFunnelState retrieves previously saved funnel state', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveTalentFunnelState('lists')
    const state = result.current.getTalentFunnelState()
    expect(state).toBeDefined()
    expect(state!.lastTab).toBe('lists')
  })

  it('clearState with section "jobs" removes only jobs state', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveJobsState('job-789')
    result.current.saveTalentFunnelState('search')
    result.current.clearState('jobs')
    expect(result.current.getJobsState()).toBeUndefined()
    expect(result.current.getTalentFunnelState()).toBeDefined()
  })

  it('clearState with section "talentFunnel" removes only funnel state', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveJobsState('job-789')
    result.current.saveTalentFunnelState('search')
    result.current.clearState('talentFunnel')
    expect(result.current.getJobsState()).toBeDefined()
    expect(result.current.getTalentFunnelState()).toBeUndefined()
  })

  it('clearState without arg removes all state from localStorage', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    result.current.saveJobsState('job-789')
    result.current.saveTalentFunnelState('search')
    result.current.clearState()
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
    expect(result.current.getJobsState()).toBeUndefined()
    expect(result.current.getTalentFunnelState()).toBeUndefined()
  })

  it('state older than TTL is ignored and cleaned up on read', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    const EIGHT_DAYS_MS = 8 * 24 * 60 * 60 * 1000
    const expired = {
      jobs: { lastJobId: 'old-job', lastView: 'kanban', timestamp: Date.now() - EIGHT_DAYS_MS },
      talentFunnel: { lastTab: 'search', timestamp: Date.now() - EIGHT_DAYS_MS },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(expired))
    expect(result.current.getJobsState()).toBeUndefined()
    expect(result.current.getTalentFunnelState()).toBeUndefined()
  })

  it('recent state within TTL is not cleaned up', () => {
    const { result } = renderHook(() => useNavigationPersistence())
    const ONE_DAY_MS = 24 * 60 * 60 * 1000
    const recent = {
      jobs: { lastJobId: 'fresh-job', lastView: 'kanban', timestamp: Date.now() - ONE_DAY_MS },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(recent))
    const state = result.current.getJobsState()
    expect(state).toBeDefined()
    expect(state!.lastJobId).toBe('fresh-job')
  })

  it('handles malformed JSON in localStorage without crashing', () => {
    localStorage.setItem(STORAGE_KEY, 'NOT_VALID_JSON')
    const { result } = renderHook(() => useNavigationPersistence())
    expect(() => result.current.getJobsState()).not.toThrow()
    expect(result.current.getJobsState()).toBeUndefined()
  })
})
