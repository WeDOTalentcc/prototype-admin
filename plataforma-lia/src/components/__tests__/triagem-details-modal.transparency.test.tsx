import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import type { WSIResultDetails } from '@/services/lia-api'
import type { Candidate } from '@/components/pages/candidates/types'

vi.mock('@/components/triagem-details/triagem-scores-panel', () => ({
  TriagemScoresPanel: () => <div data-testid="stub-scores-panel" />,
}))
vi.mock('@/components/triagem-details/triagem-comparativo-tab', () => ({
  TriagemComparativoTab: () => <div data-testid="stub-comparativo" />,
}))
vi.mock('@/components/triagem-details/triagem-summary-bar', () => ({
  TriagemSummaryBar: () => <div data-testid="stub-summary-bar" />,
}))
vi.mock('@/components/triagem-details/triagem-details-header', () => ({
  TriagemDetailsHeader: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="stub-header">
      <button onClick={onClose}>close</button>
    </div>
  ),
}))
vi.mock('@/components/triagem-details/triagem-parecer-tab', () => ({
  TriagemParecerTab: () => <div data-testid="stub-parecer" />,
}))
vi.mock('@/components/triagem-details/triagem-details-footer', () => ({
  TriagemDetailsFooter: () => <div data-testid="stub-footer" />,
}))

vi.mock('@/components/wsi/eligibility-results-section', () => ({
  EligibilityResultsSection: ({ results }: { results: unknown[] }) => (
    <div data-testid="stub-eligibility-section">
      {results.length} resultados de elegibilidade
    </div>
  ),
}))

vi.mock('@/components/triagem-details/useTriagemDetailsState', async () => {
  const actual = await vi.importActual<
    typeof import('@/components/triagem-details/useTriagemDetailsState')
  >('@/components/triagem-details/useTriagemDetailsState')
  return {
    ...actual,
    useTriagemDetailsState: vi.fn(),
  }
})

import { useTriagemDetailsState } from '@/components/triagem-details/useTriagemDetailsState'
import { TriagemDetailsModal } from '@/components/triagem-details-modal'

const mockedHook = useTriagemDetailsState as unknown as ReturnType<typeof vi.fn>

const baseCandidate: Candidate = {
  id: 'cand-1',
  candidateId: 'cand-1',
  name: 'Marina Andrade',
  email: 'marina@example.com',
  phone: '+55 11 99999-0000',
} as Candidate

function makeResponse(
  overrides: Partial<WSIResultDetails['responses'][number]> = {},
): WSIResultDetails['responses'][number] {
  return {
    competency: 'Comunicação',
    response_text: 'Resposta exemplo do candidato.',
    scores: {
      autodeclaration: 7.5,
      context: 7.0,
      bloom_level: 3,
      dreyfus_level: 3,
      final_score: 7.2,
    },
    evidences: [],
    red_flags: [],
    consistency_penalty: 0,
    justification: 'Justificativa.',
    question: {
      text: 'Pergunta exemplo?',
      framework: 'star',
      type: 'behavioral',
      weight: 1,
      expected_signals: [],
      sequence: 1,
    },
    ...overrides,
  }
}

function makeDetails(overrides: Partial<WSIResultDetails> = {}): WSIResultDetails {
  return {
    result_id: 'res-1',
    session_id: 'sess-1',
    candidate_id: 'cand-1',
    job_vacancy_id: 'vac-1',
    scores: {
      technical_wsi: 7.5,
      behavioral_wsi: 7.0,
      overall_wsi: 7.3,
      classification: 'alto',
    },
    session: {
      screening_type: 'voice',
      mode: 'compact',
    },
    responses: [makeResponse()],
    ...overrides,
  }
}

function setHookReturn(details: WSIResultDetails | null) {
  const expanded = new Set<string>([
    'responses',
    'resp-0',
    'resp-1',
    'breakdown-0',
    'breakdown-1',
  ])
  mockedHook.mockReturnValue({
    activeTab: 'triagem',
    setActiveTab: vi.fn(),
    expandedSections: expanded,
    toggleSection: vi.fn(),
    loading: false,
    error: null,
    details,
    ranking: null,
    vacancyRanking: null,
    feedbackStatus: null,
    sendingFeedback: false,
    feedbackSuccess: false,
    feedbackError: null,
    approving: false,
    setApproving: vi.fn(),
    rejecting: false,
    setRejecting: vi.fn(),
    confirmReject: false,
    setConfirmReject: vi.fn(),
    f11Report: null,
    bigFiveHint: null,
    setBigFiveHint: vi.fn(),
    copiedFeedback: false,
    setCopiedFeedback: vi.fn(),
    handleSendFeedback: vi.fn(),
    decision: undefined,
    decisionNormalized: undefined,
    isPendingDecision: false,
    canTriggerFeedback: false,
    feedbackAlreadySent: false,
  })
}

function renderModal(extraProps: Partial<React.ComponentProps<typeof TriagemDetailsModal>> = {}) {
  return render(
    <TriagemDetailsModal
      candidate={baseCandidate}
      isOpen
      onClose={() => {}}
      jobVacancyId="vac-1"
      {...extraProps}
    />,
  )
}

describe('TriagemDetailsModal — transparência WSI', () => {
  beforeEach(() => {
    mockedHook.mockReset()
  })

  it('payload legado renderiza igual ao comportamento anterior — sem banner, sem badge, sem breakdown', () => {
    setHookReturn(makeDetails())
    renderModal()

    expect(
      screen.queryByText(/Análise semântica não disponível para/i),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('Sem Camada 2')).not.toBeInTheDocument()
    expect(screen.queryByText('Como cheguei nesta nota')).not.toBeInTheDocument()
  })

  it('payload misto: banner global, badge somente nas degraded, breakdown somente onde há ajustes', () => {
    setHookReturn(
      makeDetails({
        responses: [
          makeResponse({
            competency: 'Comunicação',
            degraded_quality: true,
            layer2_degraded_reason: 'Timeout no provedor LLM',
            penalty_breakdown: { superficial: 0.5, red_flag: 0.3 },
            bonus_breakdown: { specificity: 0.2 },
          }),
          makeResponse({
            competency: 'Liderança',
            scores: {
              autodeclaration: 8.0,
              context: 8.5,
              bloom_level: 4,
              dreyfus_level: 4,
              final_score: 8.4,
            },
          }),
        ],
        degraded_quality: true,
        degraded_count: 1,
        degraded_reasons: ['Timeout no provedor LLM em 1 resposta'],
      }),
    )

    renderModal()

    expect(
      screen.getByText(/Análise semântica não disponível para 1 resposta/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/Timeout no provedor LLM em 1 resposta/i)).toBeInTheDocument()

    expect(screen.getAllByText('Sem Camada 2')).toHaveLength(1)

    expect(screen.getAllByText('Como cheguei nesta nota')).toHaveLength(1)

    expect(screen.getByText('Resposta superficial')).toBeInTheDocument()
    expect(screen.getByText('Sinal de alerta (red flag)')).toBeInTheDocument()
    expect(screen.getByText('Especificidade (exemplos concretos)')).toBeInTheDocument()
  })

  it('todas as respostas saudáveis: nem banner nem badge aparecem', () => {
    setHookReturn(
      makeDetails({
        responses: [
          makeResponse({ competency: 'A' }),
          makeResponse({ competency: 'B' }),
        ],
      }),
    )
    renderModal()

    expect(
      screen.queryByText(/Análise semântica não disponível/i),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('Sem Camada 2')).not.toBeInTheDocument()
    expect(screen.queryByText('Como cheguei nesta nota')).not.toBeInTheDocument()
  })

  it('eligibilityResults com itens: seção de elegibilidade é renderizada', () => {
    setHookReturn(makeDetails())
    renderModal({
      eligibilityResults: [
        {
          id: 'q1',
          question: 'Você possui CNH categoria B válida?',
          answer: 'Sim, possuo CNH B.',
          passed: true,
          is_eliminatory: true,
        },
        {
          id: 'q2',
          question: 'Você tem disponibilidade para início imediato?',
          answer: 'Sim, posso iniciar em até 10 dias.',
          passed: true,
          is_eliminatory: false,
        },
      ],
    })

    expect(screen.getByTestId('stub-eligibility-section')).toBeInTheDocument()
    expect(screen.getByText(/2 resultados de elegibilidade/i)).toBeInTheDocument()
  })

  it('eligibilityResults omitido: seção de elegibilidade não aparece', () => {
    setHookReturn(makeDetails())
    renderModal()

    expect(screen.queryByTestId('stub-eligibility-section')).not.toBeInTheDocument()
  })

  it('eligibilityResults vazio: seção de elegibilidade não aparece', () => {
    setHookReturn(makeDetails())
    renderModal({ eligibilityResults: [] })

    expect(screen.queryByTestId('stub-eligibility-section')).not.toBeInTheDocument()
  })
})
