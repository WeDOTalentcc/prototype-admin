/**
 * E2E — Task #1123 wizard conversational resilience.
 *
 * Sentinela end-to-end de que a LIA responde a perguntas meta /
 * off-topic / clarification SEM travar o wizard, MANTÉM contexto do
 * tenant (Demo Company / Tecnologia) e NUNCA pergunta company_id /
 * nome / setor / plano em texto livre (regressão B1).
 *
 * 3 cenários canônicos:
 *   1. Pergunta meta CURTA → classifier roda, resposta tenant-aware
 *   2. Pergunta meta LONGA (≥100 chars) → bug raiz Task #1123: classifier
 *      DEVE rodar mesmo com mensagem longa (não pode ser gateado por len)
 *   3. Off-topic mid-HITL → redirect educado, sem mutar approval
 */
import { test, expect } from '@playwright/test'
import { authenticateAsRecruiter } from '../../fixtures/auth.fixture'
import {
  openJobWizard,
  sendWizardMessage,
} from '../../fixtures/wizard-conversation.fixture'

// Anti-patterns canônicos B1/B2/B3/B4 + Task #1123 — qualquer match aborta o teste.
const TENANT_LEAK_PATTERNS: RegExp[] = [
  /informe\s+(o\s+)?company[_\s]?id/i,
  /qual\s+(é\s+)?(o\s+)?id\s+da\s+empresa/i,
  /qual\s+(é\s+)?(o\s+)?(nome|setor|porte|tamanho|plano|headcount)\s+da?\s+empresa/i,
  /\bsua\s+empresa\b/i,
  /\bdefault\b/i,
  /\bgeral\b/i,
]

const CANNED_REGRESSION_PATTERNS: RegExp[] = [
  /preciso de aprova[cç][aã]o/i,
  /\[ATENÇÃO: estado inconsistente/i,
]

async function lastAssistantText(page: any): Promise<string> {
  const last = page.locator('[data-testid="chat-message-assistant"]').last()
  await expect(last).toBeVisible({ timeout: 30_000 })
  return (await last.textContent()) || ''
}

function assertNoForbiddenPatterns(text: string, label: string): void {
  for (const re of [...TENANT_LEAK_PATTERNS, ...CANNED_REGRESSION_PATTERNS]) {
    if (re.test(text)) {
      throw new Error(
        `[${label}] resposta contém pattern proibido ${re}: ${text.slice(0, 300)}`,
      )
    }
  }
}

test.describe('Wizard — resiliência conversacional (Task #1123)', () => {
  test('Cenário 1: pergunta meta curta — classifier responde sem enriquecer', async ({ page }) => {
    test.setTimeout(120_000)
    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    await sendWizardMessage(page, 'o que você precisa pra começar?')
    const reply = await lastAssistantText(page)
    assertNoForbiddenPatterns(reply, 'meta-curta')
    // Deve terminar com pergunta de continuidade (heurística: contém '?').
    expect(reply).toMatch(/\?/)
  })

  test('Cenário 2: pergunta meta LONGA (≥100 chars) — classifier-first', async ({ page }) => {
    test.setTimeout(120_000)
    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    // Bug raiz Task #1123: antes desta task, mensagens ≥100 chars eram
    // gateadas e iam direto para enrichment LLM, perdendo a chance de
    // serem identificadas como meta_question.
    const longMeta =
      'olha eu queria entender melhor antes de começar — você precisa de ' +
      'que exatamente pra montar a vaga? me explica o processo todo aí pra ' +
      'eu saber o que preparar antes.'
    expect(longMeta.length).toBeGreaterThanOrEqual(100)
    await sendWizardMessage(page, longMeta)
    const reply = await lastAssistantText(page)
    assertNoForbiddenPatterns(reply, 'meta-longa')
    // NÃO deve ter enriquecido a pergunta meta como JD (sem cabeçalhos
    // típicos de JD enriquecida).
    expect(reply).not.toMatch(/responsabilidades:/i)
    expect(reply).not.toMatch(/requisitos:/i)
    expect(reply).toMatch(/\?/)
  })

  test('Cenário 3: off-topic mid-wizard — redirect educado', async ({ page }) => {
    test.setTimeout(120_000)
    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    await sendWizardMessage(page, 'oi, tudo bem? como tá o tempo aí?')
    const reply = await lastAssistantText(page)
    assertNoForbiddenPatterns(reply, 'off-topic')
    // Deve trazer de volta para criação da vaga.
    expect(reply.toLowerCase()).toMatch(/(vaga|jd|título|cargo|descri[cç][aã]o)/)
  })
})
