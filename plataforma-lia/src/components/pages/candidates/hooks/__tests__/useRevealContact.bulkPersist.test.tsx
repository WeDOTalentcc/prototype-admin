import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useRevealContact } from '../useRevealContact'
import { useCandidatesStore } from '@/stores/candidates-store'

beforeEach(() => {
  useCandidatesStore.setState({ revealedContacts: {} })
  vi.restoreAllMocks()
})

const pearchCandidate = {
  id: 'cand-1',
  name: 'Ana Silva',
  source: 'pearch',
  pearch_profile_id: 'pearch-id-1',
  linkedin_url: 'https://linkedin.com/in/anasilva',
  current_title: 'Engenheira',
  current_company: 'XPTO',
  avatar_url: null,
  email: null,
  phone: null,
} as any

const localCandidate = {
  id: 'cand-2',
  name: 'Bruno Costa',
  source: 'local',
  pearch_profile_id: null,
  linkedin_url: null,
  email: null,
  phone: null,
} as any

// Mock uses the bulk endpoint shape: { results: [...], revealed_count, ... }
function mockFetch(revealSuccess = true, persistSuccess = true) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
    const u = String(url)
    if (u.includes('persist-revealed')) {
      return { ok: true, json: async () => ({ success: persistSuccess, is_new: true }) } as any
    }
    if (u.includes('reveal/bulk')) {
      // Return bulk endpoint shape
      return {
        ok: true,
        json: async () => revealSuccess
          ? {
              results: [
                { success: true, candidate_id: 'cand-1', reveal_type: 'email', email: 'ana@empresa.com', phone: null, credits_remaining: 10 },
              ],
              revealed_count: 1,
              unavailable_count: 0,
              timeout_count: 0,
            }
          : {
              results: [
                { success: false, candidate_id: 'cand-1', reveal_type: 'email', message: 'nao disponivel' },
              ],
              revealed_count: 0,
              unavailable_count: 1,
              timeout_count: 0,
            },
      } as any
    }
    return { ok: false, json: async () => ({}) } as any
  })
}

// Mock for local candidate: bulk returns empty results (no reveal for local)
function mockFetchLocalOnly() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
    const u = String(url)
    if (u.includes('persist-revealed')) {
      return { ok: true, json: async () => ({ success: true, is_new: true }) } as any
    }
    if (u.includes('reveal/bulk')) {
      return {
        ok: true,
        json: async () => ({
          results: [
            { success: false, candidate_id: 'cand-2', reveal_type: 'email', message: 'nao disponivel' },
          ],
          revealed_count: 0,
          unavailable_count: 1,
          timeout_count: 0,
        }),
      } as any
    }
    return { ok: false, json: async () => ({}) } as any
  })
}

// Mock for multiple candidates bulk
function mockFetchMultiple() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (url: any) => {
    const u = String(url)
    if (u.includes('persist-revealed')) {
      return { ok: true, json: async () => ({ success: true, is_new: true }) } as any
    }
    if (u.includes('reveal/bulk')) {
      return {
        ok: true,
        json: async () => ({
          results: [
            { success: true, candidate_id: 'cand-1', reveal_type: 'email', email: 'ana@empresa.com', credits_remaining: 10 },
            // local candidate not returned as success (pearch-only reveal)
            { success: true, candidate_id: 'cand-3', reveal_type: 'email', email: 'cand3@empresa.com', credits_remaining: 8 },
          ],
          revealed_count: 2,
          unavailable_count: 0,
          timeout_count: 0,
        }),
      } as any
    }
    return { ok: false, json: async () => ({}) } as any
  })
}

describe('handleBulkReveal — persist Pearch contacts', () => {
  it('chama persist-revealed para candidato pearch apos reveal bem-sucedido', async () => {
    const fetchSpy = mockFetch()
    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    const persistCalls = fetchSpy.mock.calls.filter(([url]) =>
      String(url).includes('persist-revealed')
    )
    expect(persistCalls).toHaveLength(1)
    const body = JSON.parse(persistCalls[0][1]?.body as string)
    expect(body.pearch_id).toBe('pearch-id-1')
    expect(body.email).toBe('ana@empresa.com')
  })

  it('nao chama persist-revealed para candidato local', async () => {
    const fetchSpy = mockFetchLocalOnly()
    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([localCandidate])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    const persistCalls = fetchSpy.mock.calls.filter(([url]) =>
      String(url).includes('persist-revealed')
    )
    expect(persistCalls).toHaveLength(0)
  })

  it('persiste todos os candidatos pearch em bulk de multiplos', async () => {
    const fetchSpy = mockFetchMultiple()
    const pearch2 = { ...pearchCandidate, id: 'cand-3', pearch_profile_id: 'pearch-id-3' }
    const { result } = renderHook(() =>
      useRevealContact({ setCreditsRemaining: vi.fn() })
    )

    act(() => {
      result.current.actions.openBulkRevealModal([pearchCandidate, localCandidate, pearch2])
    })
    await act(async () => {
      await result.current.actions.handleBulkReveal(['email'])
    })

    // Wait for fire-and-forget persist calls to complete
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50))
    })

    const persistCalls = fetchSpy.mock.calls.filter(([url]) =>
      String(url).includes('persist-revealed')
    )
    expect(persistCalls).toHaveLength(2)
  })
})
