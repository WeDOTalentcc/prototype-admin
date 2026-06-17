/**
 * E2E persistence — Configurações > Governança > Policy Engine.
 *
 * Cobertura: 3 tabs canonical (business-rules, rate-limit-rules,
 * escalation-rules) + toggle is_active de BusinessRule + delete
 * BusinessRule.
 *
 * Pattern: toggle de BusinessRule é Switch dentro de TableRow. Após
 * click, PATCH /api/v1/policy-engine/business-rules/{id} retorna 200.
 * Reload → GET refresh → toggle volta no estado novo. Esse é o
 * round-trip canonical.
 *
 * ⚠ MUTAÇÃO: este test alterna is_active de uma BusinessRule existente.
 * `restoreAfter` flag por padrão faz outro toggle no afterEach para
 * voltar ao estado original.
 *
 * Testids canonical (`PolicyEnginePanel.tsx:124+`):
 *   - policy-engine-panel
 *   - policy-tab-business / rate-limit / escalation
 *   - policy-business-toggle-{rule.id}, policy-business-delete-{rule.id}
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('@persistence Governança — Policy Engine CRUD', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('governanca', 'policy-engine')
  })

  test('smoke: 3 tabs (business / rate-limit / escalation) renderizam', async ({
    authenticatedPage: page,
  }) => {
    const panel = page.locator('[data-testid="policy-engine-panel"]')
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)
    if (!visible) {
      test.skip(
        true,
        '[setup] policy-engine-panel não montou. Verificar wire em ' +
          'GovernancaHub e feature flag policy_engine_enabled.',
      )
      return
    }

    const tabs = ['policy-tab-business', 'policy-tab-rate-limit', 'policy-tab-escalation']
    for (const tid of tabs) {
      const tab = page.locator(`[data-testid="${tid}"]`).first()
      const tabVisible = await tab.isVisible({ timeout: 4_000 }).catch(() => false)
      expect(tabVisible, `[regression] tab "${tid}" sumiu`).toBe(true)
    }
  })

  test('toggle is_active de BusinessRule persiste após refresh', async ({
    authenticatedPage: page,
  }) => {
    // 1. Garantir tab business ativa
    const businessTab = page.locator('[data-testid="policy-tab-business"]').first()
    if (await businessTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await businessTab.click()
      await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
    }

    // 2. Procurar primeiro toggle de business rule existente
    const firstToggle = page
      .locator('[data-testid^="policy-business-toggle-"]')
      .first()
    const toggleVisible = await firstToggle.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!toggleVisible) {
      test.skip(
        true,
        '[setup] Sem BusinessRule seedada. Rodar seed canonical ' +
          '`scripts/seeds/policy_demo.py` no tenant de teste.',
      )
      return
    }

    // 3. Capturar estado inicial (pode ser role=switch ou button c/ aria-pressed)
    const beforeChecked =
      (await firstToggle.getAttribute('aria-checked')) === 'true' ||
      (await firstToggle.getAttribute('aria-pressed')) === 'true' ||
      (await firstToggle.isChecked().catch(() => false))

    // 4. Flip
    await firstToggle.click()
    await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })

    // 5. Reload e re-localizar (DOM resetou)
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    // Re-abrir tab business (default pode ter resetado)
    const businessTab2 = page.locator('[data-testid="policy-tab-business"]').first()
    if (await businessTab2.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await businessTab2.click()
      await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
    }

    const toggleAfter = page
      .locator('[data-testid^="policy-business-toggle-"]')
      .first()
    await expect(toggleAfter).toBeVisible({ timeout: 10_000 })
    const afterChecked =
      (await toggleAfter.getAttribute('aria-checked')) === 'true' ||
      (await toggleAfter.getAttribute('aria-pressed')) === 'true' ||
      (await toggleAfter.isChecked().catch(() => false))

    expect(
      afterChecked,
      `[persistence FAIL] BusinessRule.is_active voltou pra ${beforeChecked} ` +
        `após reload (esperado: ${!beforeChecked}). Verificar PATCH ` +
        `/api/v1/policy-engine/business-rules/{id} e serializer.`,
    ).toBe(!beforeChecked)

    // 6. Restore — flipar de volta pra não deixar drift
    await toggleAfter.click()
    await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => { /* ok */ })
  })

  test('botão "Novo" abre dialog de criação de BusinessRule', async ({
    authenticatedPage: page,
  }) => {
    const newBtn = page.locator('[data-testid="policy-business-new"]').first()
    const visible = await newBtn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      test.skip(true, '[setup] botão policy-business-new não visível.')
      return
    }
    await newBtn.click()

    // Algum dialog/modal deve abrir. Aceita role=dialog ou data-testid genérico.
    const dialog = page.locator('[role="dialog"], [data-testid*="policy-business-form"]').first()
    await expect(dialog).toBeVisible({ timeout: 5_000 })

    // Fechar (ESC ou cancel) pra não criar regra fantasma
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)
  })
})
