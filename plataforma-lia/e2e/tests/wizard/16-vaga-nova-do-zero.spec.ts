/**
 * E2E — Task #1131 (T5.1) — Supervisor intent `create_new`.
 *
 * Cobre o caminho mais frequente do `WizardSupervisorClassifier` (Task #1127):
 * recrutador inicia chat com "Quero abrir uma vaga …". Supervisor identifica
 * que não há draft ativo e roteia para o `JobCreationGraph` no nó `intake`.
 *
 * Sentinelas estruturais (anti-slop, fail-loud):
 *   1. `data-wizard-stage="jd_enrichment"` aparece dentro de 120s — prova
 *      que o supervisor NÃO short-circuitou e o graph foi de fato invocado.
 *   2. Resposta da LIA NÃO contém padrão de meta_question
 *      ("como funciona", "o que é triagem") — anti-confusão de intent.
 *   3. Wizard progress bar fica visível (`SEL.wizardProgressBar`).
 *
 * NÃO depende de wording exato (LLM não-determinístico) — invariante é
 * estrutural via `data-wizard-stage` (mesmo sensor usado em 14-resume-via-
 * interrupt.spec.ts).
 *
 * Pré-requisitos:
 *   - `lia-backend` (FastAPI :8001) com `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true`
 *   - `dev-server` (Next.js :5000)
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1131-16 e2e/tests/wizard/16-vaga-nova-do-zero.spec.ts
 */
import { expect } from '@playwright/test'
import { test } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

test.describe('Task #1131 — supervisor intent=create_new', () => {
  test('roteia "Quero abrir uma vaga …" para JobCreationGraph → jd_enrichment', async ({
    authenticatedPage: page,
  }) => {
    await goToChatHome(page)

    await sendMessageAndWait(
      page,
      'Quero abrir uma vaga de Engenheira Backend Pleno em São Paulo, ' +
        'remoto, faixa 12-18k, stack Python + FastAPI + AWS',
      { timeout: 120_000 },
    )

    // INVARIANTE ESTRUTURAL 1 — supervisor rotou para o graph, não short-circuit.
    // `data-wizard-stage="jd_enrichment"` é emitido pelo painel ao receber
    // `ws_stage_payload` com esse stage (mesmo sensor de 14-resume).
    const stage = page.locator('[data-wizard-stage="jd_enrichment"]').first()
    await expect(
      stage,
      'supervisor=create_new precisa atingir jd_enrichment. ' +
        'Verifique LIA_WIZARD_SUPERVISOR_CLASSIFIER=true no backend.',
    ).toBeVisible({ timeout: 120_000 })

    // INVARIANTE ESTRUTURAL 2 — progress bar do wizard fica visível.
    await expect(
      page.locator(SEL.wizardProgressBar),
      'wizard progress bar deve estar visível após criação iniciada',
    ).toBeVisible({ timeout: 10_000 })

    // ANTI-CONFUSÃO DE INTENT — resposta NÃO pode soar como meta_question
    // ("como funciona X"). Esse padrão indica que o supervisor classificou
    // erradamente como meta_question e short-circuitou.
    const bubbles = page.locator(SEL.liaMarkdown)
    const last = ((await bubbles.last().innerText()) || '').toLowerCase()
    expect(
      /^como funciona|^o que (é|e) (a )?triagem wsi|^posso te explicar/i.test(last),
      `Após "Quero abrir uma vaga", LIA respondeu como meta_question: "${last.slice(0, 200)}"`,
    ).toBe(false)
  })
})
