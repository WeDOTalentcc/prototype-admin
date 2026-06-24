import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { addCandidatesToPipeline } from '../candidates-api'

describe('addCandidatesToPipeline — G2: deve enviar job_vacancy_id (não job_id)', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, added_count: 2 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )
    vi.stubGlobal('fetch', fetchSpy)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('envia job_vacancy_id no body (não job_id legado)', async () => {
    await addCandidatesToPipeline({
      candidate_ids: ['cand-1', 'cand-2'],
      job_vacancy_id: 'vaga-uuid-123',
    })

    expect(fetchSpy).toHaveBeenCalledOnce()
    const [, init] = fetchSpy.mock.calls[0]
    const body = JSON.parse(init.body as string)

    expect(body).toHaveProperty('job_vacancy_id', 'vaga-uuid-123')
    expect(body).not.toHaveProperty('job_id')
  })

  it('inclui candidate_ids e source opcionais no body', async () => {
    await addCandidatesToPipeline({
      candidate_ids: ['cand-a'],
      job_vacancy_id: 'vaga-abc',
      source: 'funil',
    })

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body as string)
    expect(body.candidate_ids).toEqual(['cand-a'])
    expect(body.job_vacancy_id).toBe('vaga-abc')
    expect(body.source).toBe('funil')
    expect(body).not.toHaveProperty('job_id')
  })
})
