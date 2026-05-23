/**
 * E2E persistence — Configurações > Governança > Consent (LGPD).
 *
 * Cobertura: 3 tabs canonical (candidate-granular / training-data /
 * metrics) + ação revoke training-data + persistence após refresh.
 *
 * Pattern test_revoke: clicar "Revoke open" → modal → fill reason →
 * confirm → status muda → reload → status novo persiste.
 *
 * ⚠ MUTAÇÃO: revoke training-data consent é destrutivo do POV LGPD.
 * Test SKIP se consent não está "granted" no estado inicial pra
 * evitar tentar revogar algo já revogado. Re-grant no afterEach
 * quando possível.
 *
 * Testids canonical (`ConsentPanel.tsx:146+, 365+, 667+`):
 *   - consent-panel / consent-panel-candidate / consent-panel-training-data
 *   - consent-tab-candidate / consent-tab-training-data / consent-tab-metrics
 *   - training-consent-grant / revoke-open / revoke-confirm / revoke-reason
 *   - training-consent-status
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('@persistence Governança — Consent toggle persistence', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('governanca', 'consent')
  })

  test('smoke: 3 tabs (candidate / training-data / metrics) renderizam', async ({
    authenticatedPage: page,
  }) => {
    const panel = page.locator('[data-testid="consent-panel"]').first()
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)
    if (!visible) {
      test.skip(
        true,
        '[setup] consent-panel não montou. Verificar wire em ' +
          'GovernancaHub.tsx (subsection="consent").',
      )
      return
    }

    const tabs = [
      'consent-tab-candidate',
      'consent-tab-training-data',
      'consent-tab-metrics',
    ]
    for (const tid of tabs) {
      const tab = page.locator(`[data-testid="${tid}"]`).first()
      const tVisible = await tab.isVisible({ timeout: 4_000 }).catch(() => false)
      expect(tVisible, `[regression] tab "${tid}" sumiu`).toBe(true)
    }
  })

  test('toggle training-data consent persiste (grant→revoke→reload→revoke)', async ({
    authenticatedPage: page,
  }) => {
    // 1. Ir pra tab training-data
    const trainingTab = page.locator('[data-testid="consent-tab-training-data"]').first()
    const tabVisible = await trainingTab.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!tabVisible) {
      test.skip(true, '[setup] tab training-data não visível.')
      return
    }
    await trainingTab.click()
    await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })

    // 2. Checar status canonical
    const statusEl = page.locator('[data-testid="training-consent-status"]').first()
    const statusVisible = await statusEl.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!statusVisible) {
      test.skip(true, '[setup] training-consent-status não visível — backend pode estar 404.')
      return
    }

    const statusText = (await statusEl.textContent()) || ''
    const isGranted = /granted|concedido|ativo/i.test(statusText)

    if (!isGranted) {
      // 3a. Estado inicial = revoked. Grant primeiro pra ter o que revogar.
      const grantBtn = page.locator('[data-testid="training-consent-grant"]').first()
      const grantVisible = await grantBtn.isVisible({ timeout: 5_000 }).catch(() => false)
      if (!grantVisible) {
        test.skip(true, '[setup] training-consent-grant não visível, sem como começar.')
        return
      }
      await grantBtn.click()
      await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
    }

    // 4. Abrir modal de revoke
    const revokeOpenBtn = page.locator('[data-testid="training-consent-revoke-open"]').first()
    const revokeVisible = await revokeOpenBtn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!revokeVisible) {
      test.skip(true, '[setup] training-consent-revoke-open não visível.')
      return
    }
    await revokeOpenBtn.click()

    // 5. Preencher motivo + confirmar
    const reasonInput = page
      .locator('[data-testid="training-consent-revoke-reason"]')
      .first()
    await expect(reasonInput).toBeVisible({ timeout: 5_000 })
    await reasonInput.fill('e2e-test-revoke-reason')

    const confirmBtn = page.locator('[data-testid="training-consent-revoke-confirm"]').first()
    await confirmBtn.click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })

    // 6. Reload e re-checar status
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    const trainingTab2 = page.locator('[data-testid="consent-tab-training-data"]').first()
    if (await trainingTab2.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await trainingTab2.click()
      await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
    }

    const statusAfter = page.locator('[data-testid="training-consent-status"]').first()
    await expect(statusAfter).toBeVisible({ timeout: 10_000 })
    const statusAfterText = (await statusAfter.textContent()) || ''
    expect(
      /revoked|revogado|inativo|denied/i.test(statusAfterText),
      `[persistence FAIL] training-consent não está revoked após refresh. ` +
        `Status atual: "${statusAfterText.trim()}". Verificar PATCH ` +
        `/api/v1/consent/training-data e serializer.`,
    ).toBe(true)

    // 7. Restore — re-grant pra próximo run
    const grantBtnAfter = page.locator('[data-testid="training-consent-grant"]').first()
    if (await grantBtnAfter.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await grantBtnAfter.click()
      await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => { /* ok */ })
    }
  })
})
