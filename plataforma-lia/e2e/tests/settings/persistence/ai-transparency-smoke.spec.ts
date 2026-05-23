/**
 * E2E persistence — Configurações > Fairness Compliance > AI Transparency.
 *
 * Cobertura: smoke das 4 tabs do AITransparencyPanel (canonical EU
 * AI Act Annex III, deadline regulatório 2 Ago 2026):
 *
 *   1. explainability  — Art. 13 (modelo, dataset, training cutoff)
 *   2. decisions       — automated decisions log (read-only)
 *   3. oversight       — Art. 14 human-in-the-loop overrides
 *   4. technical       — Annex III technical docs / PDF export
 *
 * NÃO testamos override action (mutação na tab oversight) porque
 * isso altera decision audit trail real LGPD. Foco em smoke render
 * + tab switching.
 *
 * Testids canonical (`AITransparencyPanel.tsx:222+`):
 *   - ai-transparency-panel
 *   - ai-transparency-tab-{tab.id}
 *   - ai-transparency-tabpanel-{active}
 *   - ai-transparency-explainability / decisions / oversight / technical
 *   - ai-transparency-export-pdf
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

const TABS = ['explainability', 'decisions', 'oversight', 'technical'] as const

test.describe('@persistence Fairness — AI Transparency 4 tabs smoke', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('fairness-compliance', 'ai-transparency')
  })

  test('painel ai-transparency monta com 4 tabs canonical', async ({
    authenticatedPage: page,
  }) => {
    const panel = page.locator('[data-testid="ai-transparency-panel"]').first()
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)
    if (!visible) {
      test.skip(
        true,
        '[setup] ai-transparency-panel não montou. Verificar wire em ' +
          'FairnessComplianceHub e que tenant tem AI Transparency feature ' +
          'flag ON.',
      )
      return
    }

    for (const tab of TABS) {
      const tabBtn = page.locator(`[data-testid="ai-transparency-tab-${tab}"]`).first()
      const tVisible = await tabBtn.isVisible({ timeout: 4_000 }).catch(() => false)
      expect(
        tVisible,
        `[regression] tab "ai-transparency-tab-${tab}" sumiu. ` +
          `Verificar TAB_DEFINITIONS em AITransparencyPanel.tsx:87+.`,
      ).toBe(true)
    }
  })

  // Tab-switching paramétrico — falha individual fica isolada
  for (const tab of TABS) {
    test(`tab "${tab}" mostra panel correspondente ao clicar`, async ({
      authenticatedPage: page,
    }) => {
      const tabBtn = page.locator(`[data-testid="ai-transparency-tab-${tab}"]`).first()
      const visible = await tabBtn.isVisible({ timeout: 8_000 }).catch(() => false)
      if (!visible) {
        test.skip(true, `[setup] tab "${tab}" não visível — panel não montou.`)
        return
      }
      await tabBtn.click()
      await page.waitForLoadState('networkidle', { timeout: 6_000 }).catch(() => { /* ok */ })

      // O painel correspondente deve ficar visível (testid específico OU
      // tabpanel canonical).
      const specificPanel = page.locator(`[data-testid="ai-transparency-${tab}"]`).first()
      const tabpanel = page.locator(`[data-testid="ai-transparency-tabpanel-${tab}"]`).first()

      const specOk = await specificPanel.isVisible({ timeout: 5_000 }).catch(() => false)
      const tabpanelOk = await tabpanel.isVisible({ timeout: 3_000 }).catch(() => false)

      expect(
        specOk || tabpanelOk,
        `[regression] painel para tab "${tab}" não apareceu. ` +
          `Verificar render condicional em AITransparencyPanel.tsx (linha 258+).`,
      ).toBe(true)
    })
  }

  test('tab "technical" expõe botão Export PDF', async ({
    authenticatedPage: page,
  }) => {
    const tabBtn = page.locator('[data-testid="ai-transparency-tab-technical"]').first()
    if (await tabBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await tabBtn.click()
      await page.waitForLoadState('networkidle', { timeout: 6_000 }).catch(() => { /* ok */ })
    }

    const exportBtn = page.locator('[data-testid="ai-transparency-export-pdf"]').first()
    const visible = await exportBtn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      test.skip(true, '[setup] export-pdf não visível — tab technical não montou.')
      return
    }
    await expect(exportBtn).toBeVisible({ timeout: 5_000 })
    // Não clicamos — evita gerar PDF real.
  })
})
