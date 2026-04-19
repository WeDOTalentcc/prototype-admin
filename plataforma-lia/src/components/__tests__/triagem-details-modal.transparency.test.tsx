/**
 * Audit task #535 — Testes de UI: Transparência WSI no modal Triagem
 *
 * Cobertura:
 *  1. Payload LEGADO (sem novos campos de transparência) — não renderiza
 *     banner global "Análise semântica não disponível", nem badge por
 *     resposta "Sem Camada 2", nem o bloco "Como cheguei nesta nota".
 *  2. Payload MISTO — algumas respostas com `degraded_quality=true`,
 *     outras sem; algumas com `penalty_breakdown`/`bonus_breakdown`,
 *     outras sem. Valida que o banner global aparece, o badge por resposta
 *     aparece só nas degraded, e o bloco "Como cheguei nesta nota" aparece
 *     só onde há penalidade/bônus.
 *
 * Garantias regressivas: Tasks #528 (backend transparency) e #529 (UI modal
 * triagem) — sem isso, qualquer regressão silenciosa nesses campos pode
 * esconder o banner LGPD/EU AI Act ou quebrar o breakdown granular.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { WSIResultDetails } from '@/services/lia-api'
import type { Candidate } from '@/components/pages/candidates/types'

// ─── Mock dos sub-componentes pesados (mantemos TriagemResponsesSection real) ─
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

// ─── Mock parcial do hook: preserva helpers, sobrescreve apenas a função hook ─
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

// ─── Helpers de fixture ───────────────────────────────────────────────────────

const baseCandidate: Candidate = {
  id: 'cand-1',
  candidateId: 'cand-1',
  name: 'Marina Andrade',
  email: 'marina@example.com',
  phone: '+55 11 99999-0000',
} as Candidate

function makeResponse(overrides: Partial<WSIResultDetails['responses'][number]> = {}): WSIResultDetails['responses'][number] {
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
  // Simula seções expandidas (responses + primeira resposta + breakdown-0)
  // para que o conteúdo testado esteja visível sem cliques adicionais.
  const expanded = new Set<string>(['responses', 'resp-0', 'resp-1', 'breakdown-0', 'breakdown-1'])
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

function renderModal() {
  return render(
    <TriagemDetailsModal
      candidate={baseCandidate}
      isOpen
      onClose={() => {}}
      jobVacancyId="vac-1"
    />,
  )
}

// ─── Testes ───────────────────────────────────────────────────────────────────

describe('TriagemDetailsModal — transparência LGPD/EU AI Act', () => {
  beforeEach(() => {
    mockedHook.mockReset()
  })

  it('payload legado (sem campos novos) não renderiza banner LGPD, não mostra badge "Sem Camada 2" e o breakdown indica que não houve ajustes', () => {
    setHookReturn(makeDetails())
    renderModal()

    // Banner global LGPD/EU AI Act ausente.
    expect(
      screen.queryByText(/Análise semântica não disponível para/i),
    ).not.toBeInTheDocument()

    // Badge "Sem Camada 2" ausente em qualquer resposta.
    expect(screen.queryByText('Sem Camada 2')).not.toBeInTheDocument()

    // O cabeçalho "Como cheguei nesta nota" SEMPRE é renderizado por
    // explicabilidade (comentário do componente). Sem penalty/bonus, o
    // corpo deve indicar explicitamente que não houve ajustes.
    expect(screen.getByText('Como cheguei nesta nota')).toBeInTheDocument()
    expect(
      screen.getByText(/Nenhuma penalidade ou bônus aplicado/i),
    ).toBeInTheDocument()
    // Sem rótulos de penalidade conhecidos no payload legado.
    expect(screen.queryByText('Resposta superficial')).not.toBeInTheDocument()
    expect(screen.queryByText('Especificidade (exemplos concretos)')).not.toBeInTheDocument()
  })

  it('payload misto: banner aparece globalmente, badge só nas respostas degraded e breakdown só onde há ajustes', async () => {
    const responses = [
      // Resposta 0 — degraded + tem penalidades + bônus → badge + breakdown
      makeResponse({
        competency: 'Comunicação',
        degraded_quality: true,
        layer2_degraded_reason: 'Timeout no provedor LLM',
        penalty_breakdown: { superficial: 0.5, red_flag: 0.3 },
        bonus_breakdown: { specificity: 0.2 },
      }),
      // Resposta 1 — saudável + sem ajustes → sem badge, sem breakdown
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
    ]
    setHookReturn(
      makeDetails({
        responses,
        degraded_quality: true,
        degraded_count: 1,
        degraded_reasons: ['Timeout no provedor LLM em 1 resposta'],
      }),
    )

    renderModal()

    // (1) Banner global aparece com o count correto.
    expect(
      screen.getByText(/Análise semântica não disponível para 1 resposta/i),
    ).toBeInTheDocument()
    // Razão é listada.
    expect(screen.getByText(/Timeout no provedor LLM em 1 resposta/i)).toBeInTheDocument()

    // (2) Badge "Sem Camada 2" — exatamente uma ocorrência (apenas a resposta 0).
    const badges = screen.getAllByText('Sem Camada 2')
    expect(badges).toHaveLength(1)

    // (3) Cabeçalho "Como cheguei nesta nota" aparece para AMBAS as respostas
    //     (sempre presente para auditoria/explicabilidade).
    const breakdownHeaders = screen.getAllByText('Como cheguei nesta nota')
    expect(breakdownHeaders).toHaveLength(2)

    // (4) Penalidades e bônus aparecem APENAS na resposta 0, com rótulos
    //     legíveis em PT-BR (mapeamento PENALTY_LABELS / BONUS_LABELS).
    expect(screen.getByText('Resposta superficial')).toBeInTheDocument()
    expect(screen.getByText('Sinal de alerta (red flag)')).toBeInTheDocument()
    expect(screen.getByText('Especificidade (exemplos concretos)')).toBeInTheDocument()

    // (5) Resposta 1 (saudável) mostra a copy de "sem ajustes".
    expect(
      screen.getByText(/Nenhuma penalidade ou bônus aplicado/i),
    ).toBeInTheDocument()
  })

  it('quando todas as respostas estão saudáveis, banner global não aparece mesmo com campo agregado ausente', () => {
    setHookReturn(
      makeDetails({
        responses: [
          makeResponse({ competency: 'A' }),
          makeResponse({ competency: 'B' }),
        ],
        // degraded_quality não é setado → banner não deve aparecer
      }),
    )
    renderModal()

    expect(
      screen.queryByText(/Análise semântica não disponível/i),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('Sem Camada 2')).not.toBeInTheDocument()
  })
})

// Silencia warning não-relacionado (userEvent não usado, mas mantido para
// futura expansão sem reorganizar imports).
void userEvent
void within
