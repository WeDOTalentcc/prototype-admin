import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWizardFlow } from '../useWizardFlow'

describe('useWizardFlow — FairnessGuard wiring (regression)', () => {
  beforeEach(() => {
    try { localStorage.clear() } catch { /* jsdom */ }
  })

  it('captures dropped_questions and fairness_warning from a wsi_questions stage payload dispatched on the window', () => {
    const { result } = renderHook(() => useWizardFlow())

    expect(result.current.stageData).toEqual({})

    act(() => {
      window.dispatchEvent(
        new CustomEvent('lia:wizard-stage-payload', {
          detail: {
            type: 'wizard_stage',
            stage: 'wsi_questions',
            data: {
              questions: [],
              dropped_questions: [
                {
                  question: 'Qual sua idade?',
                  category: 'autodeclaracao',
                  blocked_terms: ['idade'],
                  fairness_category: 'age',
                  message: 'Pergunta removida pelo guarda de fairness.',
                },
              ],
              fairness_warning: {
                kind: 'questions_dropped',
                title: 'Perguntas removidas pela LIA',
                message: '1 pergunta foi removida por conter termos discriminatorios.',
                category: 'age',
                blocked_terms: ['idade'],
                dropped_count: 1,
              },
            },
            completeness: 0.5,
            requires_approval: true,
          },
        }),
      )
    })

    expect(result.current.currentStage).toBe('wsi_questions')
    expect(result.current.requiresApproval).toBe(true)

    const data = result.current.stageData as Record<string, unknown>
    expect(Array.isArray(data.dropped_questions)).toBe(true)
    expect((data.dropped_questions as unknown[]).length).toBe(1)
    expect((data.dropped_questions as Array<Record<string, unknown>>)[0].question).toBe(
      'Qual sua idade?',
    )

    const warning = data.fairness_warning as Record<string, unknown>
    expect(warning).toMatchObject({
      kind: 'questions_dropped',
      title: 'Perguntas removidas pela LIA',
      dropped_count: 1,
    })
  })

  it('hydrates fairness data when handleStagePayload is invoked directly', () => {
    const { result } = renderHook(() => useWizardFlow())

    act(() => {
      result.current.handleStagePayload({
        type: 'wizard_stage',
        stage: 'wsi_questions',
        data: {
          questions: [],
          dropped_questions: [
            {
              question: 'Voce e casado?',
              category: 'autodeclaracao',
              blocked_terms: ['casado'],
              fairness_category: 'marital_status',
              message: 'Pergunta removida pelo guarda de fairness.',
            },
          ],
          fairness_warning: {
            kind: 'questions_dropped',
            title: 'Pergunta removida',
            message: '1 pergunta com termo discriminatorio foi removida.',
            blocked_terms: ['casado'],
            dropped_count: 1,
          },
        },
        completeness: 0.6,
        requires_approval: true,
      })
    })

    const data = result.current.stageData as Record<string, unknown>
    const warning = data.fairness_warning as Record<string, unknown>
    expect(warning.title).toBe('Pergunta removida')
    expect((data.dropped_questions as Array<Record<string, unknown>>)[0].question).toBe(
      'Voce e casado?',
    )
  })

  it('overwrites previous wsi fairness data when a non-wsi stage payload arrives next', () => {
    const { result } = renderHook(() => useWizardFlow())

    act(() => {
      window.dispatchEvent(
        new CustomEvent('lia:wizard-stage-payload', {
          detail: {
            type: 'wizard_stage',
            stage: 'wsi_questions',
            data: {
              questions: [],
              fairness_warning: { kind: 'questions_dropped', title: 'one', message: 'one', dropped_count: 1 },
            },
            completeness: 0.5,
            requires_approval: false,
          },
        }),
      )
    })

    expect((result.current.stageData as Record<string, unknown>).fairness_warning).toBeDefined()

    act(() => {
      window.dispatchEvent(
        new CustomEvent('lia:wizard-stage-payload', {
          detail: {
            type: 'wizard_stage',
            stage: 'jd_enrichment',
            data: { jd_enriched: { titulo_padronizado: 'X' } },
            completeness: 0.2,
            requires_approval: false,
          },
        }),
      )
    })

    expect(result.current.currentStage).toBe('jd_enrichment')
    // Stage data is replaced (not merged) on STAGE_UPDATE — fairness_warning
    // from the previous wsi_questions payload no longer leaks into the
    // jd_enrichment stage data.
    expect((result.current.stageData as Record<string, unknown>).fairness_warning).toBeUndefined()
  })
})
