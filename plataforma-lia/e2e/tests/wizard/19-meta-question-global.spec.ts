/**
 * E2E — Task #1131 (T5.1) — Supervisor intent `meta_question` (short-circuit).
 *
 * Cobre o caminho de pergunta "como funciona X" feita FORA do fluxo de
 * preenchimento. O supervisor deve INTERCEPTAR (short-circuit determinístico)
 * e responder via `wizard_meta_question_helper` (Sonnet stage-aware) SEM
 * invocar o `JobCreationGraph`.
 *
 * Sentinelas estruturais:
 *   1. `data-wizard-stage` NÃO aparece — graph NÃO foi invocado.
 *   2. `wizard-progress-bar` NÃO fica visível.
 *   3. LIA responde com conteúdo informativo sobre WSI/triagem (sensor
 *      heurístico: menciona "wsi" OU "triagem" OU "perguntas").
 *   4. Resposta NÃO tem padrão de "Quero abrir vaga" / "qual cargo".
 *
 * Carve-out documentado em docs/architecture/wizard-flow.md §7.3:
 * meta_question NÃO roda FairnessGuard L1 antes do classifier (supervisor é
 * router de intent, não produtor de resposta) — este spec valida o behavior,
 * a sentinela offline de governança vive em test_wizard_supervisor_t1127.py.
 *
 * Pré-requisitos:
 *   - `LIA_WIZARD_SUPERVISOR_CLASSIFIER=true`
 *
 * Como rodar:
 *   bash plataforma-lia/scripts/run-pw-cenario.sh \
 *     pw-cenario-1131-19 e2e/tests/wizard/19-meta-question-global.spec.ts
 */
import { expect } from '@playwright/test'
import { test } from '../../fixtures/auth.fixture'
import { goToChatHome, sendMessageAndWait, SEL } from './01-helpers'

const META_QUESTIONS = [
  'Como funciona a triagem WSI?',
  'O que é triagem compacta vs completa?',
  'Quantas perguntas tem o WSI compacto?',
]

test.describe('Task #1131 — supervisor intent=meta_question short-circuit', () => {
  for (const question of META_QUESTIONS) {
    test(`"${question}" → short-circuit (graph NÃO é invocado)`, async ({
      authenticatedPage: page,
    }) => {
      await goToChatHome(page)
      await sendMessageAndWait(page, question, { timeout: 60_000 })

      // Pequena janela para qualquer race com wizard que se apresse a renderizar.
      await page.waitForTimeout(4_000)

      // INVARIANTE ESTRUTURAL 1 — graph NÃO foi invocado.
      const anyStage = await page
        .locator('[data-wizard-stage]')
        .first()
        .isVisible({ timeout: 2_000 })
        .catch(() => false)
      expect(
        anyStage,
        `Supervisor=meta_question deve SHORT-CIRCUIT. Se data-wizard-stage ` +
          `apareceu para "${question}", o supervisor classificou erradamente.`,
      ).toBe(false)

      // INVARIANTE ESTRUTURAL 2 — progress bar NÃO aparece.
      const progressVisible = await page
        .locator(SEL.wizardProgressBar)
        .isVisible({ timeout: 2_000 })
        .catch(() => false)
      expect(progressVisible, 'progress bar NÃO deve abrir em meta_question').toBe(false)

      // INVARIANTE 3 — LIA respondeu com conteúdo informativo (heurística).
      const last = ((await page.locator(SEL.liaMarkdown).last().innerText()) || '')
        .toLowerCase()
      const informative = /wsi|triagem|pergunta|compact|complet|skill|comportament/i.test(last)
      expect(
        informative,
        `LIA precisa responder informativamente a "${question}". ` +
          `Resposta: "${last.slice(0, 300)}"`,
      ).toBe(true)

      // INVARIANTE 4 — anti-confusão: NÃO disparou criação de vaga.
      expect(
        /vamos (criar|abrir) uma vaga|qual cargo voc[eê] (quer|deseja) criar/i.test(last),
        `LIA NÃO deve oferecer criar vaga em meta_question: "${last.slice(0, 200)}"`,
      ).toBe(false)
    })
  }
})
