/**
 * Cenário D — Vaga estágio (Estagiário Frontend).
 *
 * Mesma trilha do A com:
 *   - greeting "estagiário frontend" → tile sugerido = "intern"
 *   - WSI compact (3-8)
 *   - Validação extra: nenhuma WSI deve mencionar "experiência de mais de 3 anos"
 *     (incompatível com vaga de estágio).
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

test.describe('Cenário D — Vaga estágio (Estagiário Frontend)', () => {
  test.setTimeout(15 * 60_000)

  test('D — estagiário frontend', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'D-00-dashboard')

      await sendMessageAndWait(
        page,
        'Quero contratar estagiário em desenvolvimento frontend'
      )
      await captureMilestone(page, testInfo, 'D-01-greeting')

      await sendMessageAndWait(page, 'confirma')
      await sendMessageAndWait(page, 'Tecnologia, 1 vaga, prazo 30 dias')
      await captureMilestone(page, testInfo, 'D-02-setor')

      // FAIL-LOUD: card precisa aparecer
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer após setor/quantidade/prazo'
      ).toBeVisible({ timeout: 30_000 })

      const intern = page.locator(
        '[data-testid="wizard-template-option-intern"]'
      )
      await expect(intern, 'tile "intern" deve estar visível').toBeVisible({
        timeout: 5_000,
      })

      // Brief Cenário D: "expect tile sugerido = intern"
      await expect(
        intern,
        'tile "intern" deve ser o sugerido (data-suggested=true) para vaga de estagiário'
      ).toHaveAttribute('data-suggested', 'true')

      await intern.click()
      await captureMilestone(page, testInfo, 'D-03-template')

      await sendMessageAndWait(
        page,
        'HTML, CSS, JavaScript básico, vontade de aprender, cursando ensino superior'
      )
      await sendMessageAndWait(page, 'R$ 1.500')
      await sendMessageAndWait(page, 'compacta')

      await expectPanelOpens(page, 'wsi')
      await captureMilestone(page, testInfo, 'D-04-wsi')

      const wsiCount = await page.locator(SEL.wsiRow).count()
      expect(wsiCount).toBeGreaterThanOrEqual(3)
      expect(wsiCount).toBeLessThanOrEqual(8)

      // Validação extra: nenhuma WSI exige experiência de >3 anos
      const wsiTexts = await page.locator(SEL.wsiRow).allTextContents()
      for (const text of wsiTexts) {
        expect(
          text,
          `WSI de estágio não deve exigir senioridade: "${text.slice(0, 100)}"`
        ).not.toMatch(
          /(experiência|atuação)\s+(de\s+)?(mais\s+de\s+)?(3|4|5|6|7|8|9|10)\+?\s*anos?/i
        )
        expect(
          text,
          `WSI de estágio não deve pedir nível pleno/sênior: "${text.slice(0, 100)}"`
        ).not.toMatch(/\b(sênior|senior|especialista|pleno)\b/i)
      }

      await assertNoLgpdViolation(page)

      await sendMessageAndWait(page, 'aceitar')

      await expectPanelOpens(page, 'review')
      await captureMilestone(page, testInfo, 'D-05-review')

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
      await captureMilestone(page, testInfo, 'D-06-publicada')

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
