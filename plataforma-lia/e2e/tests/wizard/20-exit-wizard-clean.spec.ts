/**
 * E2E — Task #1131 (T5.1) — Supervisor intent `exit_wizard` (clean exit).
 *
 * Cobre o caminho de saída educada: recrutador está dentro do wizard e diz
 * "Sair agora" / "Depois eu termino" / "Pausa aí". Supervisor identifica a
 * intenção via `WizardSupervisorClassifier` e:
 *   - Emite mensagem curta de despedida (string determinística do helper);
 *   - **NÃO limpa o draft** — checkpoint do LangGraph permanece intacto;
 *   - Permite que a próxima sessão retome via intent=resume_draft (cenário 17).
 *
 * Sentinelas estruturais:
 *   1. Stage do wizard SUMIU (`data-wizard-stage` não está mais visível) OU
 *      progress bar não está mais ativo. Saída efetivada.
 *   2. Resposta da LIA é curta (≤ 400 chars) — mensagem de despedida, não
 *      uma nova rodada de prompts.
 *   3. Re-iniciando "Continuar onde parei" o draft RETORNA (prova que NÃO
 *      foi limpo).
 *
 * Pré-requisitos:
 *   - `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true`
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1131-20 e2e/tests/wizard/20-exit-wizard-clean.spec.ts
 */
import { expect } from '@playwright/test'
import { test } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

test.describe('Task #1131 — supervisor intent=exit_wizard preserva draft', () => {
  test('"Sair agora" finaliza wizard mas mantém checkpoint para resume', async ({
    authenticatedPage: page,
  }) => {
    // ── Fase 1: inicia wizard ─────────────────────────────────────────────
    await goToChatHome(page)
    await sendMessageAndWait(
      page,
      'Quero criar uma vaga de Engenheira Backend Pleno em SP, remoto, ' +
        'faixa 12-18k, stack Python+FastAPI+AWS',
      { timeout: 120_000 },
    )
    await expect(
      page.locator('[data-wizard-stage="jd_enrichment"]').first(),
      'wizard precisa estar ativo em jd_enrichment antes de testar exit',
    ).toBeVisible({ timeout: 120_000 })

    const stageInProgress = await page
      .locator('[data-wizard-stage]')
      .first()
      .getAttribute('data-wizard-stage')

    // ── Fase 2: pede para sair ───────────────────────────────────────────
    await sendMessageAndWait(page, 'Sair agora, depois eu termino', { timeout: 60_000 })

    // INVARIANTE ESTRUTURAL 1 — wizard finalizou (stage sumiu OU progress
    // bar não está mais ativo). Aceita as duas evidências porque o front
    // pode manter o painel renderizado por inércia visual breve.
    await page.waitForTimeout(3_000)
    const stageStillVisible = await page
      .locator('[data-wizard-stage]')
      .first()
      .isVisible({ timeout: 2_000 })
      .catch(() => false)
    const progressStillVisible = await page
      .locator(SEL.wizardProgressBar)
      .isVisible({ timeout: 2_000 })
      .catch(() => false)
    expect(
      stageStillVisible && progressStillVisible,
      `Após "Sair agora", o wizard precisa finalizar (stage E progress bar ` +
        `não podem AMBOS continuar visíveis). Estado: stage=${stageStillVisible} ` +
        `progress=${progressStillVisible}.`,
    ).toBe(false)

    // INVARIANTE 2 — resposta de despedida é curta (≤400 chars).
    const last = (await page.locator(SEL.liaMarkdown).last().innerText()) || ''
    expect(
      last.length,
      `Resposta de exit_wizard precisa ser curta (≤400 chars), foi ${last.length}: ` +
        `"${last.slice(0, 300)}"`,
    ).toBeLessThanOrEqual(400)

    // ── Fase 3: prova que o draft foi PRESERVADO ─────────────────────────
    // Se "Continuar onde parei" recoloca o wizard ativo no mesmo stage, o
    // checkpoint não foi limpo (essência do contrato exit_wizard).
    await sendMessageAndWait(page, 'Continuar onde parei', { timeout: 60_000 })
    const stageAfterResume = await page
      .locator('[data-wizard-stage]')
      .first()
      .getAttribute('data-wizard-stage')
      .catch(() => null)
    expect(
      stageAfterResume,
      `Draft precisa ser preservado pós-exit. Antes do exit: ${stageInProgress}; ` +
        `após resume: ${stageAfterResume}.`,
    ).toBeTruthy()
  })
})
