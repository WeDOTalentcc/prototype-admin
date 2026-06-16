/**
 * Hotfix P0 (2026-05-25): jsonFetcher canonical envelope unwrap
 *
 * Bug: proxy Next /api/backend-proxy/agent-template-catalog/* retorna envelope
 * {ok, data, meta}. Antes do fix, hooks recebiam o envelope inteiro e .filter()
 * crashava em consumer (TemplateGallery). Fetcher agora desempacota .data
 * quando shape match, mantém defensive pra array direto.
 */
import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { SWRConfig } from 'swr'

import {
  useAgentCategories,
  useAgentSectors,
  useAgentTemplateCatalog,
} from '../agents/use-agent-template-catalog'

const swrWrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(
    SWRConfig,
    { value: { dedupingInterval: 0, provider: () => new Map(), revalidateOnFocus: false } },
    children,
  )

const ENVELOPE_CATEGORIES = {
  ok: true,
  data: [
    { id: 'screening', label_pt: 'Triagem', label_en: 'Screening', icon: 'Filter', sort_order: 1, is_active: true },
    { id: 'sourcing', label_pt: 'Captação', label_en: 'Sourcing', icon: 'Search', sort_order: 2, is_active: true },
  ],
  meta: { count: 2 },
}

const ENVELOPE_SECTORS = {
  ok: true,
  data: [
    { id: 'tech', label_pt: 'Tecnologia', label_en: 'Technology', sort_order: 1, is_active: true },
  ],
}

const ENVELOPE_TEMPLATES = {
  ok: true,
  data: [
    { id: 'tpl-1', slug: 'tpl-1', name: 'Template 1', description: 'desc' },
  ],
}

global.fetch = vi.fn()

describe('useAgentTemplateCatalog hooks — envelope canonical unwrap (P0 hotfix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useAgentCategories desempacota envelope canonical {ok, data, meta} -> array', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(JSON.stringify(ENVELOPE_CATEGORIES), { status: 200 }),
    )
    const { result } = renderHook(() => useAgentCategories(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data[0]?.id).toBe('screening')
  })

  it('useAgentSectors desempacota envelope canonical -> array', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(JSON.stringify(ENVELOPE_SECTORS), { status: 200 }),
    )
    const { result } = renderHook(() => useAgentSectors(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data[0]?.id).toBe('tech')
  })

  it('useAgentTemplateCatalog desempacota envelope canonical -> array', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(JSON.stringify(ENVELOPE_TEMPLATES), { status: 200 }),
    )
    const { result } = renderHook(() => useAgentTemplateCatalog(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data[0]?.slug).toBe('tpl-1')
  })

  it('defensive: backend retornando array direto (sem envelope) ainda funciona', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(
        JSON.stringify([{ id: 'raw', label_pt: 'Raw', label_en: 'Raw', icon: 'X', sort_order: 1, is_active: true }]),
        { status: 200 },
      ),
    )
    const { result } = renderHook(() => useAgentCategories(), { wrapper: swrWrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(Array.isArray(result.current.data)).toBe(true)
    expect(result.current.data[0]?.id).toBe('raw')
  })
})
