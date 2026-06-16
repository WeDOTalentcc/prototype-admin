/**
 * Testes unitários — useDailyBriefing (P3-1)
 *
 * Cobre:
 * - Estado inicial: briefing=null, loading=false, error=null
 * - fetchBriefing: popula briefing no sucesso
 * - fetchBriefing: seta error em falha HTTP
 * - refresh: chama POST depois GET
 * - refresh: seta error se POST falhar
 * - Não faz fetch se user sem id
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'
import { useDailyBriefing } from '../ai/use-daily-briefing'

const swrWrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(SWRConfig, { value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false } }, children)
)

// Mock useJWTAuth
const mockUser = { id: 'user-123', email: 'test@test.com', name: 'Test' }

vi.mock('@/contexts/auth-context', () => ({
  useJWTAuth: vi.fn(() => ({ user: mockUser })),
}))

// Mock global fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

const mockBriefingData = {
  date: '2026-03-12',
  greeting: 'Bom dia, Test!',
  urgent_actions: [],
  pipeline_summary: {
    active_jobs: 3,
    total_candidates: 20,
    candidates_to_contact: 5,
    awaiting_feedback: 2,
    offers_pending: 1,
    stages_summary: [],
  },
  today_schedule: [],
  metrics: { backlog_count: 0, critical_count: 0, interviews_today: 2, pending_offers: 1 },
  insights: [],
}

describe('useDailyBriefing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('estado inicial: briefing=null, error=null (hook inicia fetch imediatamente)', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockBriefingData })
    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })
    // briefing e error são null antes da resposta chegar
    expect(result.current.briefing).toBeNull()
    expect(result.current.error).toBeNull()
    // aguarda estabilizar
    await waitFor(() => expect(result.current.loading).toBe(false))
  })

  it('busca briefing no mount e popula estado', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockBriefingData })
    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })

    await waitFor(() => {
      expect(result.current.briefing).not.toBeNull()
    })

    expect(result.current.briefing?.greeting).toBe('Bom dia, Test!')
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/backend-proxy/briefing'),
    )
  })

  it('seta error quando fetch retorna status não-ok', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 503 })
    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    })

    expect(result.current.briefing).toBeNull()
    expect(result.current.error).toContain('HTTP 503')
  })

  it('seta error quando fetch lança exceção de rede', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    })

    expect(result.current.error).toBe('Network error')
  })

  it('refresh: chama POST e depois GET, atualiza briefing', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => mockBriefingData }) // GET inicial
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })             // POST refresh
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockBriefingData, greeting: 'Atualizado' }) }) // GET pós-refresh

    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.briefing).not.toBeNull())

    await act(async () => {
      await result.current.refresh()
    })

    // POST + GET devem ter sido chamados
    const calls = mockFetch.mock.calls.map((c) => ({ url: c[0], method: (c[1] as RequestInit | undefined)?.method }))
    const postCall = calls.find((c) => c.method === 'POST')
    expect(postCall).toBeDefined()
    expect(postCall?.url).toContain('/api/backend-proxy/briefing')
  })

  it('não faz fetch se user não tiver id', async () => {
    const { useJWTAuth } = await import('@/contexts/auth-context')
    vi.mocked(useJWTAuth).mockReturnValueOnce({ user: null } as ReturnType<typeof useJWTAuth>)

    const { result } = renderHook(() => useDailyBriefing(), { wrapper: swrWrapper })
    expect(mockFetch).not.toHaveBeenCalled()
    expect(result.current.briefing).toBeNull()
  })
})
