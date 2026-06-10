/**
 * B4 — Fix fire-and-forget sem aviso em useKanbanCandidateDecisions
 *
 * Garante que falhas no handle-trigger/candidate-hired mostram toast.warning
 * e que sucesso NÃO mostra toast.warning.
 *
 * Ambiente: unit (node) — sem DOM. Hook é pura lógica async, sem JSX.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const toastSuccess = vi.fn()
const toastError = vi.fn()
const toastWarning = vi.fn()

// Mock toast object passed directly via ctx (not via sonner import)
const mockToast = {
  success: toastSuccess,
  error: toastError,
  warning: toastWarning,
}

// ---------------------------------------------------------------------------
// Minimal context builder
// ---------------------------------------------------------------------------

function buildCtx() {
  return {
    toast: mockToast as unknown as typeof import('sonner').toast,
    job: { id: 'job-123' },
    dynamicStages: [],
    setCandidatesData: vi.fn((updater: (prev: Record<string, unknown[]>) => Record<string, unknown[]>) => {
      updater({})
    }),
    setShowDecisionFlowModal: vi.fn(),
    setDecisionFlowCandidate: vi.fn(),
    decisionFlowCandidate: {
      id: 'cand-1',
      name: 'João Silva',
      email: 'joao@email.com',
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

describe('useKanbanCandidateDecisions — B4 side-effects toast', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('test_side_effects_failure_shows_toast: toast.warning quando handle-trigger retorna !ok', async () => {
    let callCount = 0
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      callCount++
      if (typeof url === 'string' && url.includes('handle-trigger/candidate-hired')) {
        return { ok: false, status: 503, json: async () => ({}) }
      }
      // transition/execute — sucesso
      return { ok: true, json: async () => ({}) }
    }))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')

    const ctx = buildCtx()
    const { handleDecisionFlowConfirm } = useKanbanCandidateDecisions(ctx)

    await handleDecisionFlowConfirm('confirm_hire')

    expect(toastWarning).toHaveBeenCalledTimes(1)
    expect(toastWarning).toHaveBeenCalledWith(
      expect.stringContaining('Contrata'),
      expect.objectContaining({
        description: expect.stringContaining('Email de boas-vindas'),
      })
    )

    vi.unstubAllGlobals()
  })

  it('test_side_effects_success_no_warning_toast: sem toast.warning quando side-effects retornam ok', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({}),
    })))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')

    const ctx = buildCtx()
    const { handleDecisionFlowConfirm } = useKanbanCandidateDecisions(ctx)

    await handleDecisionFlowConfirm('confirm_hire')

    expect(toastWarning).not.toHaveBeenCalled()
    expect(toastSuccess).toHaveBeenCalledWith(
      expect.stringContaining('contratado'),
      expect.any(Object)
    )

    vi.unstubAllGlobals()
  })
})
