// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useKanbanTransitions } from '../useKanbanTransitions'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

describe('useKanbanTransitions — HITL approval payload (AUD-4)', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn().mockResolvedValue({
      json: async () => ({ dispatch_results: [] }),
    })
    global.fetch = fetchSpy as unknown as typeof fetch
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('envia hitl_approved=true no payload do transition/execute (o clique Confirmar = aprovacao humana)', async () => {
    const { result } = renderHook(() =>
      useKanbanTransitions({
        candidatesData: { screening: [{ id: 'c1', name: 'Maria' }] },
        setCandidatesData: vi.fn(),
        universalModalState: { candidates: [{ id: 'c1', name: 'Maria' }], actionBehavior: 'conclusion_rejected' },
        closeTransition: vi.fn(),
      }),
    )

    await act(async () => {
      await result.current.handleUniversalTransitionConfirm({
        candidateIds: ['c1'],
        toStage: 'rejected',
        subStatus: 'lacking_experience',
        action: 'lia_auto',
        prompt: '',
        channel: 'email',
        actionBehavior: 'conclusion_rejected',
      } as Parameters<typeof result.current.handleUniversalTransitionConfirm>[0])
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/backend-proxy/transition/execute',
      expect.objectContaining({ method: 'POST' }),
    )
    const body = JSON.parse((fetchSpy.mock.calls[0][1] as { body: string }).body)
    expect(body.hitl_approved).toBe(true)
    expect(body.sub_status).toBe('lacking_experience')
    expect(body.action).toBe('lia_auto')
  })
})
