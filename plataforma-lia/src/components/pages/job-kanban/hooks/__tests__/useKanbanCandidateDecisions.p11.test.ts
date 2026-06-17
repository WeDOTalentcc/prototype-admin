/**
 * P1.1 — Fix: enviar reviewer_id nos handlers de rejeição rápida do kanban
 *
 * Garante que handleRejectCandidate e handleRejectFromScreening enviam
 * reviewer_id no payload POST /candidates/{id}/screening-decision/.
 *
 * Backend exige o campo por compliance (LGPD art.20 / EU AI Act art.14) e
 * retornava HTTP 422 — toda rejeição rápida era inoperante sem ele.
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

// Mock useAuthenticatedUserId so tests do not depend on auth context
vi.mock('@/hooks/shared/use-authenticated-user-id', () => ({
  useAuthenticatedUserId: () => ({ userId: 'user-reviewer-42', isReady: true }),
}))

// ---------------------------------------------------------------------------
// Minimal context builder
// ---------------------------------------------------------------------------

function buildCtx() {
  return {
    toast: mockToast as unknown as typeof import('sonner').toast,
    job: { id: 'job-999' },
    dynamicStages: [],
    setCandidatesData: vi.fn((updater: (prev: Record<string, unknown[]>) => Record<string, unknown[]>) => {
      updater({})
    }),
    setShowDecisionFlowModal: vi.fn(),
    setDecisionFlowCandidate: vi.fn(),
    decisionFlowCandidate: null,
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

const mockCandidate = {
  id: 'cand-p11',
  name: 'Maria Souza',
  email: 'maria@email.com',
  stage: 'funil',
  status: 'pending',
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useKanbanCandidateDecisions — P1.1 reviewer_id nos payloads de rejeição', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('test_reject_sends_reviewer_id: handleRejectCandidate inclui reviewer_id no POST', async () => {
    const capturedBodies: unknown[] = []

    vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) => {
      if (options?.body) {
        capturedBodies.push(JSON.parse(options.body as string))
      }
      return { ok: true, json: async () => ({ new_stage: 'Reprovados' }) }
    }))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')

    const ctx = buildCtx()
    const { handleRejectCandidate } = useKanbanCandidateDecisions(ctx)

    await handleRejectCandidate(mockCandidate as never)

    expect(capturedBodies).toHaveLength(1)
    const body = capturedBodies[0] as Record<string, unknown>
    expect(body.decision).toBe('rejected')
    expect(body.reviewer_id).toBe('user-reviewer-42')

    vi.unstubAllGlobals()
  })

  it('test_reject_from_screening_sends_reviewer_id: handleRejectFromScreening inclui reviewer_id no POST', async () => {
    const capturedBodies: unknown[] = []

    vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) => {
      if (options?.body) {
        capturedBodies.push(JSON.parse(options.body as string))
      }
      return { ok: true, json: async () => ({}) }
    }))

    const { useKanbanCandidateDecisions } = await import('../useKanbanCandidateDecisions')

    const ctx = buildCtx()
    const { handleRejectFromScreening } = useKanbanCandidateDecisions(ctx)

    await handleRejectFromScreening(mockCandidate as never)

    expect(capturedBodies).toHaveLength(1)
    const body = capturedBodies[0] as Record<string, unknown>
    expect(body.decision).toBe('rejected')
    expect(body.reviewer_id).toBe('user-reviewer-42')

    vi.unstubAllGlobals()
  })
})
