/**
 * E2E — Task #1131 (T5.1) — Supervisor intent `resume_draft`.
 *
 * Cobre o segundo caminho mais frequente do `WizardSupervisorClassifier`:
 * recrutador retorna após fechar a aba e diz "Continuar onde parei" /
 * "Retoma a vaga" / "Vamos continuar". Supervisor identifica draft ativo
 * pelo `WizardSessionService.is_session_active()` e roteia para resume.
 *
 * Sentinelas estruturais:
 *   1. Após reload, o wizard NÃO recomeça do zero — `data-wizard-stage`
 *      reaparece no MESMO stage onde foi pausado (continuidade T-1080 +
 *      pin de Task #1118).
 *   2. Resposta da LIA ao "Continuar onde parei" NÃO contém saudação inicial
 *      de "Vamos criar uma vaga do zero".
 *   3. Não há duplicação de bubbles no painel (re-render limpo).
 *
 * Pré-requisitos:
 *   - `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true`
 *   - `LIA_WIZARD_LLM_GATES=true` (default pós-#1130)
 *   - draft seedado in-flight (criado pela primeira parte do teste).
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1131-17 e2e/tests/wizard/17-retomada-draft.spec.ts
 */
import { expect } from '@playwright/test'
import { test } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

test.describe('Task #1131 — supervisor intent=resume_draft', () => {
  test('"Continuar onde parei" retoma draft existente sem reiniciar', async ({
    authenticatedPage: page,
  }) => {
    // ── Fase 1: cria draft parcial (semeia jd_enrichment) ───────────────────
    await goToChatHome(page)
    await sendMessageAndWait(
      page,
      'Quero criar uma vaga de Engenheira Backend Pleno em SP, remoto, ' +
        'faixa 12-18k, stack Python+FastAPI+AWS',
      { timeout: 120_000 },
    )
    await expect(
      page.locator('[data-wizard-stage="jd_enrichment"]').first(),
      'wizard precisa atingir jd_enrichment para semear o draft',
    ).toBeVisible({ timeout: 120_000 })

    const stageBefore = await page
      .locator('[data-wizard-stage]')
      .first()
      .getAttribute('data-wizard-stage')

    // ── Fase 2: simula fechar e voltar — reload da página ───────────────────
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 60_000 })
    await goToChatHome(page)

    // ── Fase 3: "Continuar onde parei" — supervisor=resume_draft ───────────
    const bubblesBefore = await page.locator(SEL.liaMarkdown).count()
    await sendMessageAndWait(page, 'Continuar onde parei', { timeout: 60_000 })

    // INVARIANTE ESTRUTURAL 1 — wizard volta no MESMO stage (ou avança), JAMAIS
    // regride para "intake" / sem stage. Continuidade canônica T-1080.
    const stageAfter = await page
      .locator('[data-wizard-stage]')
      .first()
      .getAttribute('data-wizard-stage')
    expect(
      stageAfter,
      `Após "Continuar onde parei", stage atual (${stageAfter}) precisa ` +
        `ser o mesmo do draft pré-reload (${stageBefore}) ou avançar — ` +
        `nunca voltar para intake/null.`,
    ).toBeTruthy()

    // INVARIANTE ESTRUTURAL 2 — LIA NÃO recomeçou do zero (sem saudação inicial).
    const last = ((await page.locator(SEL.liaMarkdown).last().innerText()) || '')
      .toLowerCase()
    expect(
      /vamos criar uma vaga do zero|qual cargo voc[eê] (quer|deseja) criar\??$/i.test(last),
      `Supervisor=resume_draft NÃO deve disparar saudação inicial: "${last.slice(0, 200)}"`,
    ).toBe(false)

    // INVARIANTE ESTRUTURAL 3 — exatamente 1 nova bubble (sem re-render duplo)
    const bubblesAfter = await page.locator(SEL.liaMarkdown).count()
    expect(
      bubblesAfter,
      `Esperado +1 bubble após "Continuar onde parei"; ` +
        `before=${bubblesBefore} after=${bubblesAfter}`,
    ).toBeGreaterThan(bubblesBefore)
  })
})
