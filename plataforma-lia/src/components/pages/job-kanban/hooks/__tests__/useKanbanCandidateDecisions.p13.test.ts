/**
 * P1.3 — Fix: checar data.success em transition/execute além de response.ok
 *
 * Garante que:
 * - success=false em body 200 mostra toast.error e NÃO move candidato na UI
 * - success=true move candidato e mostra toast.success
 * - !response.ok mostra toast.error sem mover candidato
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const toastSuccess = vi.fn()
const toastError = vi.fn()
const toastWarning = vi.fn()

const mockToast = {
  success: toastSuccess,
  error: toastError,
  warning: toastWarning,
}

vi.mock('@/hooks/shared/use-authenticated-user-id', () => ({
  useAuthenticatedUserId: () => ({ userId: 'user-p13', isReady: true }),
}))

// ---------------------------------------------------------------------------
// Minimal context builder
// ---------------------------------------------------------------------------

function buildCtx(overrides: Partial<ReturnType<typeof defaultCtx>> = {}) {
  return { ...defaultCtx(), ...overrides }
}

function defaultCtx() {
  return {
    toast: mockToast as unknown as typeof import('sonner').toast,
    job: { id: 'job-p13' },
    dynamicStages: [],
    setCandidatesData: vi.fn((updater: (prev: Record<string, unknown[]>) => Record<string, unknown[]>) => {
      updater({
        short_list: [{ id: 'cand-p13', name: 'Candidate P13', stage: 'short_list', status: 'pending' }],
        hired: [],
      })
    }),
    setShowDecisionFlowModal: vi.fn(),
    setDecisionFlowCandidate: vi.fn(),
    decisionFlowCandidate: {
      id: 'cand-p13',
      name: 'Candidate P13',
      email: 'candidate@test.com',
      stage: 'short_list',
      status: 'pending',
    },
    openTransition: vi.fn(),
    setTransitionInitialPrompt: vi.fn(),
    onCloseTriagem: vi.fn(),
    setRubricCandidate: vi.fn(),
    setShowRubricModal: vi.fn(),
    setRubricEvaluationData: vi.fn(),
    setDecisionFlowType: vi.fn(),
    setShowCloseVacancyModal: vi.fn(),
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('P1.3 — useKanbanCandidateDecisions transition/execute data.success check', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.stubGlobal('fetch', undefined)
  })

  it('test_transition_success_false_shows_error_toast_and_does_not_move_candidate', async () => {
    /**
     * Cenário: backend retorna HTTP 200 com success=false (ex: VacancyCandidate not found,
     * rowcount=0, ou exceção antiga swallowed). O candidato NÃO deve ser movido na UI.
     */
    const setCandidatesData = vi.fn()
    const ctx = buildCtx({ setCandidatesData })

    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ success: false, message: 'VacancyCandidate not found in this tenant', candidate_id: 'cand-p13', new_stage: 'hired' }),
    }).mockResolvedValue({
      // side-effect call (candidate-hired) — not reached, but mock anyway
      ok: true,
      json: async () => ({}),
    }))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')
    const { handleDecisionFlowConfirm } = useKanbanCandidateDecisions(ctx)

    await handleDecisionFlowConfirm('confirm_hire')

    // Should show error toast
    expect(toastError).toHaveBeenCalledOnce()
    const [title, opts] = toastError.mock.calls[0]
    expect(title).toBe('Transição não concluída')
    expect(opts?.description).toContain('VacancyCandidate not found in this tenant')

    // Should NOT move candidate (setCandidatesData should not be called with a mover)
    expect(setCandidatesData).not.toHaveBeenCalled()

    // Should NOT show success toast
    expect(toastSuccess).not.toHaveBeenCalled()
  })

  it('test_transition_http_error_shows_error_toast_and_does_not_move_candidate', async () => {
    /**
     * Cenário: backend retorna HTTP 500. FE deve mostrar toast.error e não mover candidato.
     */
    const setCandidatesData = vi.fn()
    const ctx = buildCtx({ setCandidatesData })

    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: { message: 'Erro interno ao processar transição' } }),
    }))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')
    const { handleDecisionFlowConfirm } = useKanbanCandidateDecisions(ctx)

    await handleDecisionFlowConfirm('confirm_hire')

    expect(toastError).toHaveBeenCalledOnce()
    expect(setCandidatesData).not.toHaveBeenCalled()
    expect(toastSuccess).not.toHaveBeenCalled()
  })

  it('test_transition_success_true_moves_candidate_and_shows_success_toast', async () => {
    /**
     * Cenário: backend retorna HTTP 200 com success=true. Candidato deve ser movido.
     */
    const setCandidatesData = vi.fn((updater: (prev: Record<string, unknown[]>) => Record<string, unknown[]>) => {
      updater({
        short_list: [{ id: 'cand-p13', name: 'Candidate P13', stage: 'short_list', status: 'pending' }],
        hired: [],
      })
    })
    const ctx = buildCtx({ setCandidatesData })

    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true, message: 'Candidato movido para hired', candidate_id: 'cand-p13', new_stage: 'hired' }),
      })
      .mockResolvedValue({
        // side-effect (candidate-hired automation)
        ok: true,
        json: async () => ({}),
      })
    )

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')
    const { handleDecisionFlowConfirm } = useKanbanCandidateDecisions(ctx)

    await handleDecisionFlowConfirm('confirm_hire')

    // Candidato deve ser movido
    expect(setCandidatesData).toHaveBeenCalled()

    // Toast de sucesso
    expect(toastSuccess).toHaveBeenCalled()
    const [title] = toastSuccess.mock.calls[0]
    expect(title).toBe('Candidato contratado! 🎉')

    // Sem toast de erro
    expect(toastError).not.toHaveBeenCalled()
  })
})
