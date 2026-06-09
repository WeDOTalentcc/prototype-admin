// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

// Mock sonner to avoid side effects
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() } }))

import { useRevealContact } from '../useRevealContact'
import { useCandidatesStore } from '@/stores/candidates-store'

beforeEach(() => {
  useCandidatesStore.setState({ revealedContacts: {} })
  vi.restoreAllMocks()
})

const pearchCandidate1 = {
  id: 'c1',
  name: 'Ana Silva',
  source: 'pearch',
  pearch_profile_id: 'pearch-1',
  linkedin_url: 'https://linkedin.com/in/anasilva',
  current_title: 'Engenheira',
  current_company: 'XPTO',
  avatar_url: null,
  email: null,
  phone: null,
} as any

const pearchCandidate2 = {
  id: 'c2',
  name: 'Bob Costa',
  source: 'pearch',
  pearch_profile_id: 'pearch-2',
  linkedin_url: 'https://linkedin.com/in/bobcosta',
  current_title: 'Dev',
  current_company: 'ABC',
  avatar_url: null,
  email: null,
  phone: null,
} as any

describe('useRevealContact — handleBulkReveal via bulk endpoint', () => {
  it('deve chamar /api/backend-proxy/search/reveal/bulk/ UMA VEZ (não N vezes por candidato)', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
      const u = String(url)
      if (u.includes('reveal/bulk')) {
        return {
          ok: true,
          json: async () => ({
            results: [
              { success: true, candidate_id: 'c1', reveal_type: 'email', email: 'ana@test.com', credits_remaining: 8 },
              { success: true, candidate_id: 'c2', reveal_type: 'email', email: 'bob@test.com', credits_remaining: 6 },
            ],
            revealed_count: 2,
            unavailable_count: 0,
            timeout_count: 0,
          }),
        } as any
      }
      return { ok: false, json: async () => ({}) } as any
    })

    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate1, pearchCandidate2])
    })

    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    // Must call bulk endpoint exactly once, not one call per candidate
    const bulkCalls = fetchSpy.mock.calls.filter(([url]) =>
      String(url).includes('reveal/bulk')
    )
    expect(bulkCalls).toHaveLength(1)
    expect(bulkCalls[0][0]).toBe('/api/backend-proxy/search/reveal/bulk/')

    // Must NOT call the individual reveal endpoint
    const individualRevealCalls = fetchSpy.mock.calls.filter(([url]) => {
      const u = String(url)
      return u.includes('search/reveal') && !u.includes('bulk') && !u.includes('persist')
    })
    expect(individualRevealCalls).toHaveLength(0)
  })

  it('deve usar method POST no endpoint bulk', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
      if (String(url).includes('reveal/bulk')) {
        return {
          ok: true,
          json: async () => ({ results: [], revealed_count: 0, unavailable_count: 0, timeout_count: 0 }),
        } as any
      }
      return { ok: false, json: async () => ({}) } as any
    })

    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate1])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    const bulkCall = fetchSpy.mock.calls.find(([url]) => String(url).includes('reveal/bulk'))
    expect(bulkCall).toBeDefined()
    expect(bulkCall![1]).toMatchObject({ method: 'POST' })
  })

  it('deve usar AbortController — fetch com signal no bulk reveal', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
      if (String(url).includes('reveal/bulk')) {
        return {
          ok: true,
          json: async () => ({ results: [], revealed_count: 0, unavailable_count: 0, timeout_count: 0 }),
        } as any
      }
      return { ok: false, json: async () => ({}) } as any
    })

    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate1])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    const bulkCall = fetchSpy.mock.calls.find(([url]) => String(url).includes('reveal/bulk'))
    expect(bulkCall).toBeDefined()
    // AbortController.signal deve estar presente nas options do fetch
    expect(bulkCall![1]).toHaveProperty('signal')
    expect(bulkCall![1]!.signal).toBeInstanceOf(AbortSignal)
  })

  it('deve atualizar revealedContacts para todos os candidatos com sucesso via bulk', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
      if (String(url).includes('reveal/bulk')) {
        return {
          ok: true,
          json: async () => ({
            results: [
              { success: true, candidate_id: 'c1', reveal_type: 'email', email: 'ana@test.com', credits_remaining: 8 },
              { success: true, candidate_id: 'c2', reveal_type: 'email', email: 'bob@test.com', credits_remaining: 6 },
            ],
            revealed_count: 2,
            unavailable_count: 0,
            timeout_count: 0,
          }),
        } as any
      }
      // persist-revealed fire-and-forget
      return { ok: true, json: async () => ({ success: true, is_new: true }) } as any
    })

    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate1, pearchCandidate2])
    })

    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    // Both candidates should now have email in revealed contacts
    const store = useCandidatesStore.getState()
    expect(store.revealedContacts['c1']?.email).toBe('ana@test.com')
    expect(store.revealedContacts['c2']?.email).toBe('bob@test.com')
  })

  it('deve enviar items corretos no body do bulk — um item por candidato×tipo', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
      if (String(url).includes('reveal/bulk')) {
        return {
          ok: true,
          json: async () => ({ results: [], revealed_count: 0, unavailable_count: 0, timeout_count: 0 }),
        } as any
      }
      return { ok: false, json: async () => ({}) } as any
    })

    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate1, pearchCandidate2])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    const bulkCall = fetchSpy.mock.calls.find(([url]) => String(url).includes('reveal/bulk'))
    expect(bulkCall).toBeDefined()
    const body = JSON.parse(bulkCall![1]!.body as string)
    expect(body).toHaveProperty('items')
    expect(body.items).toHaveLength(2)
    expect(body.items[0]).toMatchObject({ candidate_id: 'c1', reveal_type: 'email' })
    expect(body.items[1]).toMatchObject({ candidate_id: 'c2', reveal_type: 'email' })
  })
})
