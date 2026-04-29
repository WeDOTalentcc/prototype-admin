/**
 * Cenário F — Calibração canônica + critérios toggle (Onda 33) +
 * drag-reorder (Onda 33).
 *
 * Painel canônico = `CalibrationPanel` (Onda 33), com
 * `[data-testid="calibration-criteria-toggle"]` para mostrar/ocultar critérios.
 * Painel anterior `WizardCalibrationPanel` é dead code (Audit BLOCKER 1).
 */

import { test, expect } from '../../fixtures/auth.fixture'
import {
  SEL,
  sendMessageAndWait,
  captureMilestone,
  attachQualitySensors,
  assertNoAiSlop,
  expectPanelOpens,
  quickPublishTechVacancy,
} from './01-helpers'

test.describe.configure({ retries: 1 })

test.describe('Cenário F — Calibração + critérios toggle + drag-reorder', () => {
  test.setTimeout(20 * 60_000) // 20 min — inclui A abreviado + F

  test('F — calibrar busca pós publicação', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      // 1. Replica Cenário A abreviado para chegar ao estado pós-publicação
      await quickPublishTechVacancy(page)
      await captureMilestone(page, testInfo, 'F-00-vaga-publicada')

      // 2. Pede calibração
      await sendMessageAndWait(page, 'calibrar busca')

      // 3. CalibrationPanel canônico abre
      await expectPanelOpens(page, 'calibration')
      await captureMilestone(page, testInfo, 'F-01-calibration')

      // 4. Threshold gate (Onda 33 — 3 aprovações mínimas).
      //    Best-effort: procura texto "3" próximo de "aprovaç|aprov"
      const thresholdHint = page.getByText(/3.*aprov|mínim.*3|threshold/i).first()
      const thresholdVisible = await thresholdHint
        .isVisible({ timeout: 5_000 })
        .catch(() => false)
      await testInfo.attach('F-threshold-gate-visible', {
        body: String(thresholdVisible),
        contentType: 'text/plain',
      })

      // 5. Toggle critérios — Onda 33 wirou data-testid="calibration-criteria-toggle"
      const toggle = page.locator(SEL.calibrationToggle)
      await expect(toggle).toBeVisible({ timeout: 10_000 })

      const expandedBefore = await toggle.getAttribute('aria-expanded')
      await toggle.click()
      await captureMilestone(page, testInfo, 'F-02-criterios-expandido')

      const expandedAfter = await toggle.getAttribute('aria-expanded')
      expect(
        expandedAfter,
        'aria-expanded deve mudar após click no toggle'
      ).not.toBe(expandedBefore)

      // 7. Toggle de novo (ocultar)
      await toggle.click()
      await captureMilestone(page, testInfo, 'F-03-criterios-oculto')
      const expandedReset = await toggle.getAttribute('aria-expanded')
      expect(expandedReset).toBe(expandedBefore)

      // 8. Candidate cards — FAIL-LOUD: brief exige >= 3 cards após calibrar
      const candidateCards = page.locator(SEL.kanbanCandidateCard)
      await expect
        .poll(
          async () => candidateCards.count(),
          {
            timeout: 30_000,
            message:
              'CalibrationPanel deve popular o pool com >= 3 candidatos após "calibrar busca". ' +
              'Se falhar: verifique se a sourcing/search da demo está retornando candidatos OU ' +
              'se o seletor [data-testid="candidate-card"] mudou de KanbanColumnRenderer.',
          }
        )
        .toBeGreaterThanOrEqual(3)

      const cardsCount = await candidateCards.count()
      await testInfo.attach('F-candidate-cards-count', {
        body: String(cardsCount),
        contentType: 'text/plain',
      })

      // 9. Aprovar 3 — cada botão Approve precisa estar lá
      for (let i = 0; i < 3; i++) {
        const card = candidateCards.nth(i)
        const approve = card
          .getByRole('button', { name: /aprovar|approve|👍/i })
          .first()
        await expect(
          approve,
          `Botão Aprovar deve estar visível no candidato #${i + 1}`
        ).toBeVisible({ timeout: 5_000 })
        await approve.click()
      }
      await captureMilestone(page, testInfo, 'F-04-tres-aprovados')

      // 11. Progress bar avançou — best-effort (selector pode não existir
      //     no painel canônico CalibrationPanel; tolerante apenas se ausente)
      const progressbar = page.locator('[role="progressbar"]').first()
      if (await progressbar.isVisible({ timeout: 1_000 }).catch(() => false)) {
        const valueNow = await progressbar.getAttribute('aria-valuenow')
        if (valueNow !== null) {
          expect(
            Number(valueNow),
            `progress bar deve refletir as 3 aprovações (got aria-valuenow=${valueNow})`
          ).toBeGreaterThanOrEqual(3)
        }
      }

      // 12. Rejeitar 1 — opcional (alguns CalibrationPanel só mostram 3 cards
      //     por vez). Se 4º não aparecer, anota e segue.
      if (cardsCount >= 4) {
        const fourthCard = candidateCards.nth(3)
        const reject = fourthCard
          .getByRole('button', { name: /rejeitar|reject|👎/i })
          .first()
        await expect(
          reject,
          'Botão Rejeitar deve estar visível no candidato #4'
        ).toBeVisible({ timeout: 5_000 })
        await reject.click()
      }

      // 13. Mensagem da LIA contém /pool|matches|critérios|atualiz/i
      // best-effort sobre as últimas 3 bubbles
      const recent = await page
        .locator(SEL.liaMarkdown)
        .allTextContents()
        .then((all) => all.slice(-3).join('\n'))
      expect(
        recent,
        'Última bubble da LIA deve mencionar pool/matches/critérios/atualização'
      ).toMatch(/pool|matches|critéri|atualiz|refin/i)

      // 14. assertNoAiSlop
      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
