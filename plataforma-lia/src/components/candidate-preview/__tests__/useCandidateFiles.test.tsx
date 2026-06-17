/**
 * Tests — useCandidateFiles hook
 *
 * Sensor F2.a canonical: valida que o hook usa o proxy correto
 * `/api/backend-proxy/candidates/{id}/files` e NÃO o proxy inexistente
 * `/api/backend-proxy/data_files`.
 *
 * Cobre:
 * - hook chama URL correta (candidates/{id}/files, não data_files)
 * - retorna lista de arquivos quando proxy responde OK
 * - retorna [] + toast de erro quando proxy retorna 4xx
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useCandidateFiles } from '../useCandidateFiles'

vi.mock('@/hooks/company/use-current-company', () => ({
  useCurrentCompany: () => ({ companyId: 'company-abc-123' }),
}))

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

const mockCandidate = { id: 'cand-xyz-456', name: 'João Silva' }

describe('useCandidateFiles — proxy URL canonical (F2.a sensor)', () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    fetchSpy = vi.spyOn(global, 'fetch')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('chama /api/backend-proxy/candidates/{id}/files (NÃO /data_files)', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ attachments: [], categories: [] }),
    } as Response)

    renderHook(() => useCandidateFiles(mockCandidate))

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled()
    })

    const calledUrl = fetchSpy.mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/backend-proxy/candidates/cand-xyz-456/files')
    expect(calledUrl).not.toContain('/data_files')
  })

  it('retorna lista de arquivos quando proxy responde OK', async () => {
    const mockFiles = [
      { id: 'f1', name: 'cv.pdf', file_type: 'cv', uploaded_at: '2026-05-01T00:00:00Z' },
    ]
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ attachments: mockFiles, categories: ['cv'] }),
    } as Response)

    const { result } = renderHook(() => useCandidateFiles(mockCandidate))

    await waitFor(() => {
      expect(result.current.candidateFiles).toEqual(mockFiles)
    })
    expect(result.current.fileCategories).toEqual(['cv'])
  })

  it('retorna [] + dispara toast.error quando proxy retorna 4xx', async () => {
    const { toast } = await import('sonner')

    fetchSpy.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Not found' }),
    } as Response)

    const { result } = renderHook(() => useCandidateFiles(mockCandidate))

    await waitFor(() => {
      expect(result.current.isLoadingFiles).toBe(false)
    })

    expect(result.current.candidateFiles).toEqual([])
    expect(toast.error).toHaveBeenCalledWith(
      'Erro ao carregar arquivos',
      expect.objectContaining({ description: 'Not found' })
    )
  })
})
