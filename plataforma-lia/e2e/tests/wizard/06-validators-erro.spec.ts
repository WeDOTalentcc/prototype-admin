/**
 * Cenário E — Banner missingFields (Onda 33).
 *
 * Onda 33 wirou o banner em UnifiedChat reusando o estilo
 * `border-status-warning/20 bg-status-warning/5` do ReviewPanel.
 * O banner é um `[role="status"][aria-live="polite"]` com texto sobre
 * "campos obrigatórios" / "missing".
 *
 * O cenário tenta forçar avanço sem fornecer dados → backend devolve
 * `missing_fields`, hook armazena, banner deve aparecer e ReviewPanel
 * NÃO deve estar visível (validator bloqueou avanço).
 */

import { test, expect } from '../../fixtures/auth.fixture'
import {
  SEL,
  goToChatHome,
  sendMessageAndWait,
  captureMilestone,
  attachQualitySensors,
  assertNoAiSlop,
  getMissingFieldsBanner,
} from './01-helpers'

test.describe.configure({ retries: 1 })

test.describe('Cenário E — Banner missingFields', () => {
  test.setTimeout(10 * 60_000)

  test('E — banner bloqueia avanço com campos faltando', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'E-00-dashboard')

      // Sem título completo → LIA pede mais info
      await sendMessageAndWait(page, 'criar vaga')
      await captureMilestone(page, testInfo, 'E-01-criar-vaga')

      await sendMessageAndWait(page, 'Engenheiro')

      // Tenta forçar pular validação
      await sendMessageAndWait(page, 'pular validação')

      // Banner deve aparecer (Onda 33 wiring)
      // FAIL-LOUD: o cenário E só faz sentido se o banner aparece
      const banner = getMissingFieldsBanner(page)
      await expect(
        banner.first(),
        'Banner missingFields (Onda 33) deve estar visível após "pular validação". ' +
          'Se falhar: verifique se o wiring da Onda 33 em UnifiedChat consome ' +
          'missingFields do useWizardIntegration (Audit BLOCKER 3).'
      ).toBeVisible({ timeout: 30_000 })
      await captureMilestone(page, testInfo, 'E-02-banner')

      // WSI panel NÃO deve estar visível (validator bloqueou avanço)
      const wsiVisible = await page
        .locator(SEL.wsiRow)
        .first()
        .isVisible({ timeout: 1_000 })
        .catch(() => false)
      expect(
        wsiVisible,
        'WsiQuestionsPanel NÃO deve abrir enquanto faltam campos obrigatórios'
      ).toBe(false)

      // ReviewPanel NÃO deve estar visível — proxy: botão Publicar do Review
      const publishBtn = page.getByRole('button', { name: /publicar|publish/i })
      const publishCount = await publishBtn.count()
      expect(
        publishCount,
        'ReviewPanel/botão Publicar NÃO deve estar disponível enquanto faltam campos'
      ).toBe(0)

      // Calibration toggle também não pode estar presente (validator bloqueia)
      const calibrationVisible = await page
        .locator(SEL.calibrationToggle)
        .isVisible({ timeout: 500 })
        .catch(() => false)
      expect(
        calibrationVisible,
        'CalibrationPanel NÃO deve abrir enquanto faltam campos obrigatórios'
      ).toBe(false)

      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
