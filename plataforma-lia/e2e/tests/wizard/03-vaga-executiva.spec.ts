/**
 * Cenário B — Vaga executiva (Diretor de Marketing).
 *
 * Mesma trilha do A com:
 *   - greeting de Diretor → tile sugerido = "executive"
 *   - WSI mode "completa" → 8-15 cards
 *   - Salário R$ 35.000 + bônus
 */

import { test, expect } from '../../fixtures/auth.fixture'
import {
  SEL,
  goToChatHome,
  sendMessageAndWait,
  captureMilestone,
  attachQualitySensors,
  assertNoAiSlop,
  assertNoLgpdViolation,
  expectPanelOpens,
  extractQualityScore,
} from './01-helpers'

test.describe.configure({ retries: 1 })

test.describe('Cenário B — Vaga executiva (Diretor de Marketing)', () => {
  test.setTimeout(15 * 60_000)

  test('B — Diretor de Marketing com WSI completa', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'B-00-dashboard')

      await sendMessageAndWait(page, 'Vou criar vaga de Diretor de Marketing')
      await captureMilestone(page, testInfo, 'B-01-greeting')

      await sendMessageAndWait(page, 'confirma')
      await sendMessageAndWait(page, 'Marketing, 1 vaga, prazo 60 dias')
      await captureMilestone(page, testInfo, 'B-02-setor')

      // Tile executive — FAIL-LOUD: card precisa aparecer + tile deve ser o sugerido
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer após setor/quantidade/prazo'
      ).toBeVisible({ timeout: 30_000 })

      const executive = page.locator(
        '[data-testid="wizard-template-option-executive"]'
      )
      await expect(executive, 'tile "executive" deve estar visível').toBeVisible({
        timeout: 5_000,
      })

      // Brief Cenário B: "expect tile sugerido = executive"
      await expect(
        executive,
        'tile "executive" deve ser o sugerido (data-suggested=true) para vaga de Diretor'
      ).toHaveAttribute('data-suggested', 'true')

      await executive.click()
      await captureMilestone(page, testInfo, 'B-03-template')

      await sendMessageAndWait(
        page,
        'Estratégia de marca, P&L, liderança de equipe, growth, performance'
      )
      await sendMessageAndWait(page, 'R$ 35.000 + bônus')

      // Modo completa
      await sendMessageAndWait(page, 'completa')

      await expectPanelOpens(page, 'wsi')
      await captureMilestone(page, testInfo, 'B-04-wsi')

      const wsiCount = await page.locator(SEL.wsiRow).count()
      expect(
        wsiCount,
        `WSI completa deve ter 8-15 perguntas (got ${wsiCount})`
      ).toBeGreaterThanOrEqual(8)
      expect(wsiCount).toBeLessThanOrEqual(15)

      await assertNoLgpdViolation(page)

      await sendMessageAndWait(page, 'aceitar')

      await expectPanelOpens(page, 'review')
      await captureMilestone(page, testInfo, 'B-05-review')

      const score = await extractQualityScore(page)
      if (score !== null) {
        expect(score).toBeGreaterThanOrEqual(60)
      }

      const publishBtn = page.getByRole('button', {
        name: /publicar|publish/i,
      }).first()
      if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await publishBtn.click()
      } else {
        await sendMessageAndWait(page, 'publicar')
      }
      await captureMilestone(page, testInfo, 'B-06-publicada')

      await expect
        .poll(async () => {
          const body = await page.locator('body').innerText()
          return /publicad|criad|sucesso/i.test(body)
        }, { timeout: 30_000 })
        .toBe(true)

      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
