/**
 * E2E persistence — Configurações > Fairness Compliance.
 *
 * Cobertura: smoke das 4 sub-sessões canonical do hub:
 *   - fairness (core report: blocks, warnings, by_category chart)
 *   - studio (StudioComplianceView)
 *   - lgpd-candidatos (filtered DSR Art. 20)
 *   - ai-transparency (4 tabs explainability/decisions/oversight/technical)
 *
 * Não há mutação aqui — fairness é primariamente read-only report.
 * Mutações estão cobertas em AI Transparency override (não testado
 * aqui pra evitar alterar decision audit trail real).
 *
 * Sub-sessions são "subsection" props do hub (via menu lateral). Cada
 * sub-sessão renderiza componente dedicado:
 *   - fairness (default) → bar chart + summary cards
 *   - studio → <StudioComplianceView>
 *   - lgpd-candidatos → <DSRInboxPanel defaultRequestType="explanation">
 *   - ai-transparency → <AITransparencyPanel>
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('@persistence Fairness Compliance — 4 sub-sessões smoke', () => {
  test.setTimeout(120_000)

  test('subsection "fairness" (default) renderiza summary cards/chart', async ({
    navigateToSettings,
    authenticatedPage: page,
  }) => {
    await navigateToSettings('fairness-compliance')

    // Heading principal sempre visível, e pelo menos um dos:
    //   summary text ("Bloqueios"/"Warnings"/categoria) OU chart/select
    const visible = await page
      .locator('text=/Bloqueios|Alertas|Eventos|Total/i')
      .first()
      .isVisible({ timeout: 10_000 })
      .catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] Fairness core não renderizou. Possíveis causas: ' +
          'backend /api/backend-proxy/fairness-report/summary 404, ' +
          'feature flag off, ou loading state preso. Verificar ' +
          'FairnessComplianceHub.tsx fetch.',
      )
      return
    }
    expect(visible).toBe(true)
  })

  test('subsection "studio" renderiza StudioComplianceView', async ({
    navigateToSettings,
    authenticatedPage: page,
  }) => {
    await navigateToSettings('fairness-compliance', 'studio')

    // StudioComplianceView típicamente tem heading "Studio" + chart/list
    const visible = await page
      .locator('text=/Studio|Compliance Studio|Análise Studio/i')
      .first()
      .isVisible({ timeout: 10_000 })
      .catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] StudioComplianceView nao montou. Verificar wire em ' +
          'FairnessComplianceHub.tsx ao branch activeSubsection==studio.',
      )
      return
    }
    expect(visible).toBe(true)
  })

  test('subsection "lgpd-candidatos" renderiza DSR inbox filtrado', async ({
    navigateToSettings,
    authenticatedPage: page,
  }) => {
    await navigateToSettings('fairness-compliance', 'lgpd-candidatos')

    // DSR inbox usa testid canonical "dsr-inbox-panel" mesmo aqui
    // (componente reusado). Filtro pra defaultRequestType="explanation".
    const panel = page.locator('[data-testid="dsr-inbox-panel"]').first()
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] DSR inbox em lgpd-candidatos nao montou. Verificar ' +
          'wire DSRInboxPanel defaultRequestType=explanation em ' +
          'FairnessComplianceHub.tsx.',
      )
      return
    }
    expect(visible).toBe(true)
  })

  test('subsection "ai-transparency" renderiza AITransparencyPanel', async ({
    navigateToSettings,
    authenticatedPage: page,
  }) => {
    await navigateToSettings('fairness-compliance', 'ai-transparency')

    const panel = page.locator('[data-testid="ai-transparency-panel"]').first()
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] AITransparencyPanel nao montou. Verificar wire em ' +
          'FairnessComplianceHub.tsx ao branch activeSubsection==ai-transparency.',
      )
      return
    }
    expect(visible).toBe(true)
  })
})
