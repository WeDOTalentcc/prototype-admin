import { render, renderHook, screen, act } from '@testing-library/react'
import { WizardProvider } from '../WizardContext'
import { WSIQuestionsStage } from '../stages/WSIQuestionsStage'
import { useWizardFlow } from '@/components/unified-chat/wizard/useWizardFlow'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/stores/wizard-store', () => ({
  useWizardStore: vi.fn(() => ({
    draft: null,
    draftId: null,
    setDraft: vi.fn(),
    setDraftId: vi.fn(),
    clearDraft: vi.fn(),
  })),
}))

vi.mock('@/hooks/company/useCompanyBenefits', () => ({
  useCompanyBenefits: () => ({ benefits: [], isLoading: false, error: null }),
}))

describe('WSIQuestionsStage — FairnessGuard banner wiring', () => {
  it('renders the banner from a wizard_stage payload dispatched on the window', () => {
    render(
      <WizardProvider>
        <WSIQuestionsStage />
      </WizardProvider>,
    )

    // Initially nothing dropped → no banner.
    expect(screen.queryByTestId('wsi-fairness-warning')).not.toBeInTheDocument()

    // Simulate the WS handler bridging an `ws_stage_payload` for `wsi_questions`
    // with FairnessGuard drops.
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

    const banner = screen.getByTestId('wsi-fairness-warning')
    expect(banner).toBeInTheDocument()
    expect(banner).toHaveTextContent('Perguntas removidas pela LIA')
    expect(banner).toHaveTextContent('1 pergunta foi removida')
    expect(banner).toHaveTextContent('Qual sua idade?')
    expect(banner).toHaveTextContent('idade')
  })

  it('ignores payloads for non-wsi_questions stages', () => {
    render(
      <WizardProvider>
        <WSIQuestionsStage />
      </WizardProvider>,
    )

    act(() => {
      window.dispatchEvent(
        new CustomEvent('lia:wizard-stage-payload', {
          detail: {
            type: 'wizard_stage',
            stage: 'jd_enrichment',
            data: {
              fairness_warning: {
                kind: 'input_blocked',
                title: 'Should not appear',
                message: 'noop',
                dropped_count: 0,
              },
            },
            completeness: 0.2,
            requires_approval: false,
          },
        }),
      )
    })

    expect(screen.queryByTestId('wsi-fairness-warning')).not.toBeInTheDocument()
  })

  it('hydrates the banner when useWizardFlow.handleStagePayload is invoked', () => {
    render(
      <WizardProvider>
        <WSIQuestionsStage />
      </WizardProvider>,
    )

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

    const banner = screen.getByTestId('wsi-fairness-warning')
    expect(banner).toHaveTextContent('Pergunta removida')
    expect(banner).toHaveTextContent('Voce e casado?')
    expect(banner).toHaveTextContent('casado')
  })
})
