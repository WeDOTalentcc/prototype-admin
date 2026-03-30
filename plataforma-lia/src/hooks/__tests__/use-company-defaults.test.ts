/**
 * Tests — useCompanyDefaults
 *
 * Covers:
 * - Initial state (loading, empty defaults, null error)
 * - Successful full fetch (profile + culture + benefits)
 * - Profile fetch failure yields empty defaults
 * - Culture data mapping (workModel, employmentTypes, defaultLanguages)
 * - Benefits mapping and filtering inactive ones
 * - Network error sets error message
 * - refetch reloads and clears error
 */
import { renderHook, waitFor } from '@testing-library/react'
import { useCompanyDefaults } from '../use-company-defaults'

const MOCK_PROFILE = { id: 'comp-123', name: 'Acme Corp' }

const MOCK_CULTURE = {
  work_model: 'hybrid',
  employment_types: ['clt', 'pj'],
  default_languages: ['pt', 'en'],
}

const MOCK_BENEFITS_RAW = [
  { id: 'b1', name: 'Vale Refeicao', category: 'food', is_active: true },
  { id: 'b2', name: 'Plano de Saude', category: 'health', is_active: true },
  { id: 'b3', name: 'Old Benefit', category: 'misc', is_active: false },
]

global.fetch = vi.fn()

describe('useCompanyDefaults', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('starts with isLoading true', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCompanyDefaults())
    expect(result.current.isLoading).toBe(true)
  })

  it('starts with empty defaults', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCompanyDefaults())
    const d = result.current.defaults
    expect(d.workModel).toBe('')
    expect(d.employmentTypes).toEqual([])
    expect(d.defaultLanguages).toEqual([])
    expect(d.benefits).toEqual([])
  })

  it('starts with error null', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCompanyDefaults())
    expect(result.current.error).toBeNull()
  })

  // ── Successful fetch ──────────────────────────────────────────────────────

  it('isLoading is false after successful fetch', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('sets workModel from culture profile', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.defaults.workModel).toBe('hybrid')
  })

  it('sets employmentTypes from culture profile', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.defaults.employmentTypes).toEqual(['clt', 'pj'])
  })

  it('sets defaultLanguages from culture profile', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.defaults.defaultLanguages).toEqual(['pt', 'en'])
  })

  it('filters out inactive benefits', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    const benefitIds = result.current.defaults.benefits.map((b: { id: string }) => b.id)
    expect(benefitIds).toContain('b1')
    expect(benefitIds).toContain('b2')
    expect(benefitIds).not.toContain('b3')
  })

  it('benefits count matches active items', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.defaults.benefits.length).toBe(2)
  })

  // ── Profile fetch failure ─────────────────────────────────────────────────

  it('returns empty defaults when profile fetch fails', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ ok: false, status: 401 })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.defaults.workModel).toBe('')
    expect(result.current.defaults.benefits).toEqual([])
  })

  // ── Network error ─────────────────────────────────────────────────────────

  it('sets error on network failure', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network'))
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it('isLoading is false after network error', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'))
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  // ── refetch ────────────────────────────────────────────────────────────────

  it('exposes refetch function', () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCompanyDefaults())
    expect(typeof result.current.refetch).toBe('function')
  })

  it('refetch clears error and reloads', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_PROFILE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_CULTURE })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_BENEFITS_RAW })
    const { result } = renderHook(() => useCompanyDefaults())
    await waitFor(() => expect(result.current.error).toBeTruthy())
    await result.current.refetch()
    await waitFor(() => expect(result.current.error).toBeNull())
  })
})
