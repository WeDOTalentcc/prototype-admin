/**
 * Tests — useRecruitmentStages
 *
 * Covers:
 * - isLoading true initially
 * - stages list loads on success
 * - activeStages filters inactive stages
 * - interviewStages excludes system stages
 * - falls back to DEFAULT_STAGES on HTTP error
 * - sets error on HTTP failure
 * - sets error on network failure  
 * - refetch reloads data
 * - sla object exposed with correct fields
 * - calculateDeadline returns a date string
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useRecruitmentStages } from '../use-recruitment-stages'

// Mock the DEFAULT_STAGES dependency
vi.mock('@/components/settings/RecruitmentJourneyConfig', () => ({
  DEFAULT_STAGES: [
    { id: 'default-1', name: 'Triagem', display_name: 'Triagem', order: 1, isActive: true, sla: 3, type: 'system', notes: '', sub_statuses: [] },
    { id: 'default-2', name: 'Entrevista', display_name: 'Entrevista', order: 2, isActive: true, sla: 5, type: 'default', notes: '', sub_statuses: [] },
  ],
}))

const MOCK_PIPELINE_RESPONSE = {
  pipeline: [
    { id: 's1', name: 'Triagem', display_name: 'Triagem', stage_order: 1, is_active: true, sla_hours: 72, stage_category: 'system', sub_statuses: [] },
    { id: 's2', name: 'Entrevista', display_name: 'Entrevista', stage_order: 2, is_active: true, sla_hours: 120, stage_category: 'catalog', sub_statuses: [] },
    { id: 's3', name: 'Oferta', display_name: 'Oferta', stage_order: 3, is_active: false, sla_hours: 48, stage_category: 'custom', sub_statuses: [] },
  ],
}

describe('useRecruitmentStages', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts with isLoading true', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useRecruitmentStages())
    expect(result.current.isLoading).toBe(true)
  })

  it('starts with empty stages array', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useRecruitmentStages())
    expect(result.current.stages).toEqual([])
  })

  it('starts with null error', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useRecruitmentStages())
    expect(result.current.error).toBeNull()
  })

  it('sets isLoading false after successful fetch', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('loads stages from pipeline response', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.stages).toHaveLength(3)
    expect(result.current.stages[0].id).toBe('s1')
  })

  it('activeStages only includes isActive=true stages', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.activeStages).toHaveLength(2)
    expect(result.current.activeStages.every(s => s.isActive)).toBe(true)
  })

  it('interviewStages excludes system type stages', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const nonSystem = result.current.interviewStages
    expect(nonSystem.every(s => s.type !== 'system')).toBe(true)
  })

  it('falls back to DEFAULT_STAGES on HTTP error', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.stages.length).toBeGreaterThan(0)
  })

  it('sets error on HTTP failure', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it('sets error on network failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network down'))
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it('exposes refetch function', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(typeof result.current.refetch).toBe('function')
  })

  it('refetch reloads data', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const callsBefore = mockFetch.mock.calls.length
    await result.current.refetch()
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(mockFetch.mock.calls.length).toBeGreaterThan(callsBefore)
  })

  it('exposes sla object with required fields', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.sla).toHaveProperty('screeningSLA')
    expect(result.current.sla).toHaveProperty('shortlistSLA')
    expect(result.current.sla).toHaveProperty('totalSLA')
    expect(typeof result.current.sla.calculateDeadline).toBe('function')
  })

  it('calculateDeadline returns a date string', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => MOCK_PIPELINE_RESPONSE })
    const { result } = renderHook(() => useRecruitmentStages())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const deadline = result.current.sla.calculateDeadline(7)
    expect(typeof deadline).toBe('string')
    expect(deadline).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})
