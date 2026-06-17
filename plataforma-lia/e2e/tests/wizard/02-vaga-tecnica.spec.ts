/**
 * Cenário A — Vaga técnica (Engenheiro Pleno).
 *
 * Fluxo linear chat-driven: greeting → seniority → setor/quantidade → tile
 * técnico → must-haves → salário → modo WSI compacto → aceitar WSI →
 * Review → publicar. Asserts em invariantes estruturais (selectors AUDIT
 * Seção 1), não em wording exato da LIA.
 *
 * Nenhum testid novo é assumido em produção.
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

test.describe('Cenário A — Vaga técnica (Engenheiro Pleno)', () => {
  test.setTimeout(15 * 60_000) // 15 min — fluxo completo com LLM real

  test('A — fluxo linear até publicação', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      // 1. dashboard
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'A-00-dashboard')

      // 2. greeting
      await sendMessageAndWait(
        page,
        'Quero criar uma vaga de Engenheiro de Software Pleno'
      )
      await captureMilestone(page, testInfo, 'A-01-greeting')

      // 3. confirma seniority
      await sendMessageAndWait(page, 'confirma')

      // 4. setor + quantidade + prazo
      await sendMessageAndWait(page, 'Engenharia, 2 vagas, prazo 30 dias')
      await captureMilestone(page, testInfo, 'A-02-setor')

      // 5. tile técnico — FAIL-LOUD: card precisa aparecer
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer após setor/quantidade/prazo'
      ).toBeVisible({ timeout: 30_000 })

      const technical = page.locator(
        '[data-testid="wizard-template-option-technical"]'
      )
      await expect(technical, 'tile "technical" deve estar visível').toBeVisible({
        timeout: 5_000,
      })
      await technical.click()
      await captureMilestone(page, testInfo, 'A-03-template')

      // 6. must-haves
      await sendMessageAndWait(
        page,
        'React, TypeScript, Node.js, comunicação, autonomia'
      )

      // 7. salário
      await sendMessageAndWait(page, 'R$ 12.000')

      // 8. modo WSI compacto
      await sendMessageAndWait(page, 'compacta')

      // 9. WsiQuestionsPanel canônico abre (Onda 33)
      await expectPanelOpens(page, 'wsi')
      await captureMilestone(page, testInfo, 'A-04-wsi')

      // 10. WSI cards entre 3 e 8 (faixa realista de LLM, não exact)
      const wsiCount = await page.locator(SEL.wsiRow).count()
      expect(
        wsiCount,
        `WSI compact deve ter 3-8 perguntas (got ${wsiCount})`
      ).toBeGreaterThanOrEqual(3)
      expect(wsiCount).toBeLessThanOrEqual(8)

      // 11. role="listitem" (drag-reorder Onda 33)
      const listItems = await page.locator('[role="listitem"]').count()
      expect(
        listItems,
        'Onda 33 — WSI rows usam role="listitem" para drag-reorder'
      ).toBeGreaterThanOrEqual(wsiCount)

      // 12. LGPD — nenhuma WSI deve perguntar dado protegido
      await assertNoLgpdViolation(page)

      // 13. aceitar WSI
      await sendMessageAndWait(page, 'aceitar')

      // 14. ReviewPanel canônico
      await expectPanelOpens(page, 'review')
      await captureMilestone(page, testInfo, 'A-05-review')

      // 15. quality_score >= 60 (tolerante: pode não vir)
      const score = await extractQualityScore(page)
      if (score !== null) {
        expect(score, `quality_score deve ser >= 60 (got ${score})`).toBeGreaterThanOrEqual(60)
      }

      // 16. publicar
      const publishBtn = page.getByRole('button', {
        name: /publicar|publish/i,
      }).first()
      if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await publishBtn.click()
      } else {
        await sendMessageAndWait(page, 'publicar')
      }
      await captureMilestone(page, testInfo, 'A-06-publicada')

      // 17. body contém "publicada" OR "criada" OR "sucesso"
      await expect
        .poll(async () => {
          const body = await page.locator('body').innerText()
          return /publicad|criad|sucesso/i.test(body)
        }, { timeout: 30_000 })
        .toBe(true)

      // 18. assertNoAiSlop
      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
