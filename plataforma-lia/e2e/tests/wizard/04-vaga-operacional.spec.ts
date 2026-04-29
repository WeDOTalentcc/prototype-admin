/**
 * Cenário C — Vaga operacional (mass hiring — atendentes loja).
 *
 * Mesma trilha do A com:
 *   - greeting "50 atendentes" → tile sugerido em {mass_hiring, operational}
 *   - WSI compact (3-8 cards)
 *   - Salário R$ 1.800 + comissão
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

test.describe('Cenário C — Vaga operacional (mass hiring)', () => {
  test.setTimeout(15 * 60_000)

  test('C — 50 atendentes loja', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'C-00-dashboard')

      await sendMessageAndWait(
        page,
        'Preciso contratar 50 atendentes para nossa loja'
      )
      await captureMilestone(page, testInfo, 'C-01-greeting')

      await sendMessageAndWait(page, 'confirma')
      await sendMessageAndWait(page, 'Operações, 50 vagas, prazo 45 dias')
      await captureMilestone(page, testInfo, 'C-02-setor')

      // FAIL-LOUD: card precisa aparecer
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer após setor/quantidade/prazo'
      ).toBeVisible({ timeout: 30_000 })

      const massHiring = page.locator(
        '[data-testid="wizard-template-option-mass_hiring"]'
      )
      const operational = page.locator(
        '[data-testid="wizard-template-option-operational"]'
      )

      // Brief Cenário C: tile sugerido em {mass_hiring, operational}
      const massVisible = await massHiring.isVisible({ timeout: 5_000 }).catch(() => false)
      const opVisible = await operational.isVisible({ timeout: 5_000 }).catch(() => false)
      expect(
        massVisible || opVisible,
        'tile mass_hiring OU operational deve estar visível para 50 atendentes'
      ).toBe(true)

      // Anotar qual foi escolhido (informação útil pro REPORT.md)
      const target = massVisible ? massHiring : operational
      const targetId = massVisible ? 'mass_hiring' : 'operational'
      const targetSuggested = await target.getAttribute('data-suggested')
      await testInfo.attach(`C-tile-chosen`, {
        body: `id=${targetId} data-suggested=${targetSuggested}`,
        contentType: 'text/plain',
      })

      // FAIL-LOUD: o tile escolhido DEVE ser o sugerido (mass hiring esperado)
      expect(
        targetSuggested,
        `tile "${targetId}" deve ser o sugerido (data-suggested=true) para 50 atendentes`
      ).toBe('true')

      await target.click()
      await captureMilestone(page, testInfo, 'C-03-template')

      await sendMessageAndWait(
        page,
        'atendimento ao cliente, vendas, comunicação, proatividade, ensino médio'
      )
      await sendMessageAndWait(page, 'R$ 1.800 + comissão')
      await sendMessageAndWait(page, 'compacta')

      await expectPanelOpens(page, 'wsi')
      await captureMilestone(page, testInfo, 'C-04-wsi')

      const wsiCount = await page.locator(SEL.wsiRow).count()
      expect(wsiCount).toBeGreaterThanOrEqual(3)
      expect(wsiCount).toBeLessThanOrEqual(8)

      await assertNoLgpdViolation(page)

      await sendMessageAndWait(page, 'aceitar')

      await expectPanelOpens(page, 'review')
      await captureMilestone(page, testInfo, 'C-05-review')

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
      await captureMilestone(page, testInfo, 'C-06-publicada')

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
