// @vitest-environment jsdom
/**
 * Bug fix — useKanbanDragDrop dispara CustomEvent "lia:open_offer_review"
 * com job?.id (inteiro legado ex: "42") em vez do backendId (UUID).
 * Backend exige job_id: UUID → retorna 422 → modal nunca abre.
 *
 * Fix: espelhar o padrão de useKanbanPageCore.ts:182 usando
 * (job as { backendId?: string })?.backendId ?? job?.id ?? "".
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useKanbanDragDrop, type KanbanDragDropContext } from '../useKanbanDragDrop'

// Mocks externos necessários para o hook
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}))

vi.mock('@/hooks/recruitment/use-recruitment-stages', () => ({
  useRecruitmentStages: () => ({ legacySubStatuses: {} }),
}))

// Helper para montar o contexto mínimo necessário
function makeCtx(overrides: Partial<KanbanDragDropContext> = {}): KanbanDragDropContext {
  return {
    draggedCandidate: null,
    setDraggedCandidate: vi.fn(),
    dragOverColumn: null,
    setDragOverColumn: vi.fn(),
    dynamicStages: [
      { id: 'sourcing', label: 'Sourcing', color: '#000', order: 0 } as never,
      { id: 'offer', label: 'Oferta', color: '#000', order: 5 } as never,
    ],
    openTransition: vi.fn(),
    pendingMove: null,
    setPendingMove: vi.fn(),
    statusModalOpen: false,
    setStatusModalOpen: vi.fn(),
    selectedSubStatus: '',
    setSelectedSubStatus: vi.fn(),
    setCandidatesData: vi.fn(),
    job: null,
    ...overrides,
  }
}

function makeCandidate(id = 'cand-uuid-001') {
  return {
    id,
    name: 'Felipe Almeida',
    email: 'felipe@example.com',
    phone: null,
    avatar: null,
    stage: 'sourcing',
    score: 85,
    role: 'Dev',
    company: 'ACME',
    currentCompany: 'ACME',
    appliedDate: '2026-01-01',
    source: 'linkedin',
    sub_status: null,
    fromColumn: 'sourcing',
  }
}

function makeDragEvent(): React.DragEvent<Element> {
  return {
    preventDefault: vi.fn(),
    dataTransfer: { effectAllowed: '', dropEffect: '' },
  } as unknown as React.DragEvent<Element>
}

describe('useKanbanDragDrop — offer drag fix (backendId UUID)', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('usa backendId como job_id no CustomEvent quando disponível', async () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const candidate = makeCandidate('cand-uuid-001')
    const ctx = makeCtx({
      draggedCandidate: candidate,
      // job com id inteiro legado E backendId UUID
      job: {
        id: '42',
        backendId: 'aabb1234-0000-0000-0000-123456789abc',
        title: 'Dev Pleno',
        status: 'active',
        stages: [],
        totalCandidates: 0,
        createdAt: '2026-01-01',
      } as never,
    })

    const { result } = renderHook(() => useKanbanDragDrop(ctx))

    await act(async () => {
      await result.current.handleDrop(makeDragEvent(), 'offer')
    })

    // Deve ter disparado o evento
    expect(dispatchSpy).toHaveBeenCalledOnce()
    const event = dispatchSpy.mock.calls[0][0] as CustomEvent<{ candidate_id: string; job_id: string }>
    expect(event.type).toBe('lia:open_offer_review')

    // job_id DEVE ser o UUID, não o inteiro "42"
    expect(event.detail.job_id).toBe('aabb1234-0000-0000-0000-123456789abc')
    expect(event.detail.job_id).not.toBe('42')

    // candidate_id correto
    expect(event.detail.candidate_id).toBe('cand-uuid-001')
  })

  it('usa id como fallback quando backendId está ausente', async () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const candidate = makeCandidate('cand-uuid-002')
    const ctx = makeCtx({
      draggedCandidate: candidate,
      // job SEM backendId — fallback usa id
      job: {
        id: 'job-uuid-sem-backendId',
        title: 'Dev Senior',
        status: 'active',
        stages: [],
        totalCandidates: 0,
        createdAt: '2026-01-01',
      } as never,
    })

    const { result } = renderHook(() => useKanbanDragDrop(ctx))

    await act(async () => {
      await result.current.handleDrop(makeDragEvent(), 'offer')
    })

    expect(dispatchSpy).toHaveBeenCalledOnce()
    const event = dispatchSpy.mock.calls[0][0] as CustomEvent<{ candidate_id: string; job_id: string }>
    expect(event.detail.job_id).toBe('job-uuid-sem-backendId')
  })

  it('nunca usa id inteiro "42" quando backendId está disponível', async () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const candidate = makeCandidate('cand-uuid-003')
    const ctx = makeCtx({
      draggedCandidate: candidate,
      job: {
        id: '42',
        backendId: 'real-uuid-ffff-0000-dead-beefcafebabe',
        title: 'PM',
        status: 'active',
        stages: [],
        totalCandidates: 0,
        createdAt: '2026-01-01',
      } as never,
    })

    const { result } = renderHook(() => useKanbanDragDrop(ctx))

    await act(async () => {
      await result.current.handleDrop(makeDragEvent(), 'offer')
    })

    const event = dispatchSpy.mock.calls[0][0] as CustomEvent<{ candidate_id: string; job_id: string }>
    // Garantia explícita: o inteiro legado nunca vaza
    expect(event.detail.job_id).not.toBe('42')
    expect(event.detail.job_id).toBe('real-uuid-ffff-0000-dead-beefcafebabe')
  })
})
