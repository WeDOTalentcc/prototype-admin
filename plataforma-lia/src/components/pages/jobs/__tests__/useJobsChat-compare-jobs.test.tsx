/**
 * Tests — useJobsChat compare_jobs ui_action routing (P0.2 anti-ghost)
 *
 * Regression guard for the ghost-action sensor (scripts/check_ui_action_handlers.py).
 * The BE producer `jobs_management_assistant_service` emits
 * `ui_action: "compare_jobs"` via resolve_jobs_ui_action("comparar_vagas").
 * Before this fix the FE had no handler, so the action was silently discarded
 * (same class as the lia_field_toggles ghost-setting). The canonical fix routes
 * it to the existing JobCompareModal through the `openCompareModal` callback — in
 * BOTH the direct response path (handleAICommand) and the cross-surface listener
 * (handleJobsUIAction), mirroring how `filter_jobs` / `start_job_wizard` work.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

const mockCall = vi.fn()
let capturedUnhandledListener:
  | ((action: string, params: Record<string, unknown>) => void)
  | null = null

vi.mock('@/lib/api/kanban-assistant', () => ({
  callOrchestratedJobsManagement: (...args: unknown[]) => mockCall(...args),
}))
vi.mock('@/contexts/lia-float-context', () => ({
  useLiaFloat: () => ({ open: vi.fn() }),
}))
vi.mock('@/hooks/company/useCompanyId', () => ({
  useCompanyId: () => ({ companyId: 'company-test' }),
}))
vi.mock('@/hooks/chat/useUnhandledUIActionListener', () => ({
  useUnhandledUIActionListener: (
    cb: (a: string, p: Record<string, unknown>) => void,
  ) => {
    capturedUnhandledListener = cb
  },
}))
vi.mock('@/hooks/ai/use-lia-suggestions', () => ({
  useLiaSuggestions: () => ({ suggestions: [], loading: false, refresh: vi.fn() }),
  useJobInsights: () => ({ insights: [], generateInsights: vi.fn(), loading: false }),
  useLiaExpandedPrompt: () => ({
    sendPrompt: vi.fn(),
    response: null,
    loading: false,
    followUpSuggestions: [],
  }),
}))
vi.mock('next/navigation', () => ({
  useSearchParams: () => ({ get: () => null, toString: () => '' }),
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => '/jobs',
}))

import { useJobsChat } from '../hooks/useJobsChat'

function makeOptions(overrides: Record<string, unknown> = {}) {
  return {
    filteredJobs: [],
    allJobs: [],
    selectedJobsForBatch: new Set<number>(),
    loadBackendJobs: vi.fn().mockResolvedValue(undefined),
    setActiveFilter: vi.fn(),
    ...overrides,
  }
}

describe('useJobsChat — compare_jobs ui_action (anti-ghost)', () => {
  beforeEach(() => {
    mockCall.mockReset()
    capturedUnhandledListener = null
  })

  it('routes a compare_jobs response to openCompareModal (direct path)', async () => {
    const openCompareModal = vi.fn()
    mockCall.mockResolvedValue({
      success: true,
      content: 'Comparando vagas',
      agent_used: 'jobs_mgmt',
      intent_detected: 'comparar_vagas',
      confidence: 0.9,
      suggested_prompts: [],
      ui_action: 'compare_jobs',
      ui_action_params: { job_ids: [11, 22] },
    })

    const { result } = renderHook(() =>
      useJobsChat(makeOptions({ openCompareModal }) as never),
    )

    await act(async () => {
      await result.current.actions.handleAICommand('compare as vagas 11 e 22')
    })

    expect(openCompareModal).toHaveBeenCalledWith([11, 22])
  })

  it('routes a compare_jobs cross-surface event to openCompareModal (listener path)', () => {
    const openCompareModal = vi.fn()
    renderHook(() => useJobsChat(makeOptions({ openCompareModal }) as never))

    expect(capturedUnhandledListener).toBeTypeOf('function')
    act(() => {
      capturedUnhandledListener?.('compare_jobs', { job_ids: [3, 4] })
    })

    expect(openCompareModal).toHaveBeenCalledWith([3, 4])
  })

  it('opens compare with no ids when params omit job_ids (producer sends null params)', async () => {
    const openCompareModal = vi.fn()
    mockCall.mockResolvedValue({
      success: true,
      content: 'Comparando',
      agent_used: 'jobs_mgmt',
      intent_detected: 'comparar_vagas',
      confidence: 0.9,
      suggested_prompts: [],
      ui_action: 'compare_jobs',
      ui_action_params: null,
    })

    const { result } = renderHook(() =>
      useJobsChat(makeOptions({ openCompareModal }) as never),
    )

    await act(async () => {
      await result.current.actions.handleAICommand('compare')
    })

    expect(openCompareModal).toHaveBeenCalledWith(undefined)
  })
})
