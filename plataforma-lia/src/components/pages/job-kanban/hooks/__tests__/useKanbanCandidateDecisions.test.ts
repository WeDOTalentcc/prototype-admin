// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useKanbanCandidateDecisions, type KanbanCandidateDecisionsContext } from '../useKanbanCandidateDecisions'
import { type KanbanCandidate } from '@/components/kanban'

// Minimal mock for toast
const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
}
vi.mock('sonner', () => ({
  toast: mockToast,
}))

const makeCandidate = (overrides: Partial<KanbanCandidate> = {}): KanbanCandidate => ({
  id: 'cand-123',
  name: 'Felipe Almeida',
  role: 'Engenheiro',
  avatar: '',
  score: 85,
  email: 'felipe@example.com',
  phone: '11999999999',
  stage: 'interview_hr',
  ...overrides,
})

const makeCtx = (overrides: Partial<KanbanCandidateDecisionsContext> = {}): KanbanCandidateDecisionsContext => {
  const setCandidatesData = vi.fn()
  const setShowDecisionFlowModal = vi.fn()
  const setDecisionFlowCandidate = vi.fn()
  const candidate = makeCandidate()
  return {
    toast: mockToast as typeof import('sonner').toast,
    job: { id: 'job-456', title: 'Engenheiro Sênior' } as any,
    dynamicStages: [],
    setCandidatesData,
    setShowDecisionFlowModal,
    setDecisionFlowCandidate,
    decisionFlowCandidate: candidate,
    openTransition: vi.fn(),
    setTransitionInitialPrompt: vi.fn(),
    onCloseTriagem: vi.fn(),
    setRubricCandidate: vi.fn(),
    setShowRubricModal: vi.fn(),
    setRubricEvaluationData: vi.fn(),
    setDecisionFlowType: vi.fn(),
    ...overrides,
  }
}

describe('useKanbanCandidateDecisions — confirm_hire branch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('test_confirm_hire_success — moves candidate to hired and calls fire-and-forget', async () => {
    const ctx = makeCtx()
    const candidate = ctx.decisionFlowCandidate!

    // Primary transition/execute returns 200
    const fetchMock = vi.spyOn(global, 'fetch')
      .mockResolvedValueOnce({ ok: true, json: async () => ({ stage: 'hired' }) } as Response)
      // fire-and-forget call
      .mockResolvedValueOnce({ ok: true } as Response)

    const { result } = renderHook(() => useKanbanCandidateDecisions(ctx))

    await act(async () => {
      await result.current.handleDecisionFlowConfirm('confirm_hire')
    })

    // transition/execute called with correct payload
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/backend-proxy/transition/execute',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          vacancy_candidate_id: candidate.id,
          to_stage: 'hired',
          action: 'lia_auto',
          action_behavior: 'conclusion_hired',
          vacancy_id: 'job-456',
          channel: 'email',
        }),
      })
    )

    // candidatesData updated (setCandidatesData called with a function)
    expect(ctx.setCandidatesData).toHaveBeenCalledTimes(1)
    const updaterFn = (ctx.setCandidatesData as ReturnType<typeof vi.fn>).mock.calls[0][0]
    const prevData = { interview_hr: [candidate], hired: [] }
    const newData = updaterFn(prevData)
    expect(newData['interview_hr']).toHaveLength(0)
    expect(newData['hired']).toHaveLength(1)
    expect(newData['hired'][0].stage).toBe('hired')

    // fire-and-forget called
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/backend-proxy/automation/handle-trigger/candidate-hired',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          candidate_id: candidate.id,
          vacancy_id: 'job-456',
          candidate_name: candidate.name,
          candidate_email: candidate.email ?? null,
        }),
      })
    )

    // toast.success called
    expect(mockToast.success).toHaveBeenCalledWith(
      'Candidato contratado!',
      expect.objectContaining({ description: expect.stringContaining(candidate.name) })
    )

    // modal closed
    expect(ctx.setShowDecisionFlowModal).toHaveBeenCalledWith(false)
    expect(ctx.setDecisionFlowCandidate).toHaveBeenCalledWith(null)
  })

  it('test_confirm_hire_http_error — shows error toast and does not update candidatesData', async () => {
    const ctx = makeCtx()

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Transição inválida' }),
    } as Response)

    const { result } = renderHook(() => useKanbanCandidateDecisions(ctx))

    await act(async () => {
      await result.current.handleDecisionFlowConfirm('confirm_hire')
    })

    expect(ctx.setCandidatesData).not.toHaveBeenCalled()
    expect(mockToast.error).toHaveBeenCalledWith(
      'Erro ao contratar',
      expect.objectContaining({ description: 'Transição inválida' })
    )
    // modal still closed
    expect(ctx.setShowDecisionFlowModal).toHaveBeenCalledWith(false)
  })

  it('test_confirm_hire_no_candidate — early return when decisionFlowCandidate is null', async () => {
    const ctx = makeCtx({ decisionFlowCandidate: null })
    const fetchMock = vi.spyOn(global, 'fetch')

    const { result } = renderHook(() => useKanbanCandidateDecisions(ctx))

    await act(async () => {
      await result.current.handleDecisionFlowConfirm('confirm_hire')
    })

    expect(fetchMock).not.toHaveBeenCalled()
    expect(mockToast.success).not.toHaveBeenCalled()
    expect(mockToast.error).not.toHaveBeenCalled()
    expect(ctx.setShowDecisionFlowModal).not.toHaveBeenCalled()
  })
})
