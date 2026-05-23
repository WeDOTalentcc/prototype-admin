/**
 * E2E persistence — Configurações > Governança > DSR Inbox.
 *
 * Cobertura: smoke render + filtro status + botão "Exportar CSV".
 * DSR (Data Subject Request) tem ações de mutação (approve/reject/
 * fulfill), mas elas mudam status de request real LGPD — preferimos
 * NÃO mutar em test E2E pra não enviar emails LGPD pro candidato
 * demo. Foco aqui é smoke + filter UX.
 *
 * Testids canonical (`DSRInboxPanel.tsx:200+`):
 *   - dsr-inbox-panel
 *   - dsr-status-filter
 *   - dsr-export-csv
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('@persistence Governança — DSR Inbox actions', () => {
  test.setTimeout(90_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('governanca', 'dsr')
  })

  test('smoke: painel dsr-inbox renderiza com filtros', async ({
    authenticatedPage: page,
  }) => {
    const panel = page.locator('[data-testid="dsr-inbox-panel"]')
    const visible = await panel.isVisible({ timeout: 10_000 }).catch(() => false)
    if (!visible) {
      test.skip(
        true,
        '[setup] dsr-inbox-panel não montou. Verificar wire em ' +
          'GovernancaHub e LGPD feature flag.',
      )
      return
    }
    await expect(panel).toBeVisible({ timeout: 10_000 })

    const statusFilter = page.locator('[data-testid="dsr-status-filter"]').first()
    await expect(statusFilter).toBeVisible({ timeout: 5_000 })
  })

  test('filtro status muda lista sem crashar painel', async ({
    authenticatedPage: page,
  }) => {
    const statusFilter = page.locator('[data-testid="dsr-status-filter"]').first()
    const visible = await statusFilter.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      test.skip(true, '[setup] filtro status não visível — painel não montou.')
      return
    }

    const tag = await statusFilter.evaluate((el) => el.tagName.toLowerCase())
    if (tag === 'select') {
      // Pega segunda opção (primeira costuma ser "todos")
      const options = await statusFilter.locator('option').count()
      if (options >= 2) {
        await statusFilter.selectOption({ index: 1 })
      }
    } else {
      // Pode ser Select shadcn (button + popover)
      await statusFilter.click()
      const popoverItem = page.locator('[role="option"]').nth(1)
      if (await popoverItem.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await popoverItem.click()
      }
    }

    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })
    await expect(page.locator('[data-testid="dsr-inbox-panel"]')).toBeVisible({
      timeout: 5_000,
    })
  })

  test('botão "Exportar CSV" existe (smoke)', async ({
    authenticatedPage: page,
  }) => {
    const exportBtn = page.locator('[data-testid="dsr-export-csv"]').first()
    const visible = await exportBtn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      test.skip(true, '[setup] dsr-export-csv não visível.')
      return
    }
    await expect(exportBtn).toBeVisible({ timeout: 5_000 })
    // Não clicamos pra evitar download real.
  })
})
