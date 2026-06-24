/**
 * @vitest-environment jsdom
 *
 * Fase 1.1 — WSI regenerate 404 fix
 * Garante que regenerateWSIQuestions usa o padrão /api/backend-proxy/api/wsi/...
 * (consistente com todas as demais chamadas do mesmo arquivo wsi-api.ts).
 *
 * Antes do fix a URL era /api/backend-proxy/wsi/regenerate-questions (faltando /api/).
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { regenerateWSIQuestions } from '@/services/lia-api/wsi-api'

describe('regenerateWSIQuestions — URL pattern', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        questions: [],
        questions_added: 0,
        questions_removed: 0,
        quality_warnings: [],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('deve chamar /api/backend-proxy/api/wsi/regenerate-questions (padrão correto)', async () => {
    await regenerateWSIQuestions({
      job_vacancy_id: 'test-job-id',
      company_id: 'test-company-id',
      current_questions: [],
      feedback: 'test feedback',
    })

    expect(fetchMock).toHaveBeenCalledOnce()
    const calledUrl: string = fetchMock.mock.calls[0][0]

    expect(calledUrl).toContain('/api/backend-proxy/api/wsi/regenerate-questions')
  })

  it('NÃO deve chamar URL sem /api/ entre backend-proxy e wsi (padrão incorreto que causa 404)', async () => {
    await regenerateWSIQuestions({
      job_vacancy_id: 'test-job-id',
      company_id: 'test-company-id',
      current_questions: [],
      feedback: 'test feedback',
    })

    expect(fetchMock).toHaveBeenCalledOnce()
    const calledUrl: string = fetchMock.mock.calls[0][0]

    // A URL quebrada era: /api/backend-proxy/wsi/regenerate-questions
    // (sem /api/ entre backend-proxy e wsi)
    expect(calledUrl).not.toMatch(/\/api\/backend-proxy\/wsi\/regenerate-questions/)
  })
})
