/**
 * Persistence test fixtures — Configurações smoke gate.
 *
 * Por que existem fixtures separadas do `auth.fixture.ts` canonical?
 *   * `auth.fixture.ts` cuida do login JWT (POST /api/v1/auth/login +
 *     seed cookies). Reusamos ele aqui.
 *   * Esta camada adiciona o navigate→subsection determinístico via
 *     o menu lateral canonical (`[data-testid="settings-menu-*"]` +
 *     `[data-testid="settings-content-area"][data-active-section=…]`)
 *     — eliminando race conditions de "click antes do mount".
 *
 * Gap fechado por estes tests: pedido original do Paulo (2026-05-21)
 *   "verificar persistência de cada campo de cada sessão e subssessão"
 *   foi atendido apenas no nível de auditoria estática (grep + ler
 *   código). Browser-level round-trip (fill → save → reload → assert)
 *   NÃO existia. Este pacote cria o pattern canonical pras próximas
 *   sprints expandirem cobertura (Governança, Fairness, Pipeline,
 *   Templates, etc).
 */
import { test as base, expect } from '../../../fixtures/auth.fixture'
import type { Page } from '@playwright/test'

export type SettingsSection =
  | 'minha-empresa'
  | 'comunicacao-alertas'
  | 'governanca'
  | 'fairness-compliance'
  | 'pipeline'
  | 'usuarios'
  | 'integracoes'
  | 'ai-credits'

export interface PersistenceFixtures {
  /**
   * Navega para `/pt/configuracoes`, abre o hub e (opcionalmente) o
   * sub-painel pedido. Espera o `data-active-section` bater como
   * sentinel de "mount completo".
   *
   * Use SEMPRE este helper em vez de `page.goto` manual — ele
   * resolve a race condition de "click antes do menu hidratar"
   * que afetou Task #1017 (vide `01-minha-empresa.spec.ts`).
   */
  navigateToSettings: (section: SettingsSection, subsection?: string) => Promise<void>
}

export const test = base.extend<PersistenceFixtures>({
  navigateToSettings: async ({ authenticatedPage }, use) => {
    await use(async (section: SettingsSection, subsection?: string) => {
      const page = authenticatedPage
      await page.goto('/pt/configuracoes', {
        waitUntil: 'domcontentloaded',
        timeout: 30_000,
      })
      await page
        .waitForLoadState('networkidle', { timeout: 30_000 })
        .catch(() => { /* ok — alguns endpoints WS ficam abertos */ })

      // Abrir hub via menu lateral canonical (data-testid pattern T1017)
      const menuBtn = page.locator(`[data-testid="settings-menu-${section}"]`)
      if (await menuBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await menuBtn.click()
      }
      const contentArea = page.locator('[data-testid="settings-content-area"]')
      await expect(contentArea).toBeVisible({ timeout: 15_000 })
      await expect(contentArea).toHaveAttribute(
        'data-active-section',
        section,
        { timeout: 10_000 },
      )

      // Sub-painel opcional (tabs internas dentro do hub)
      if (subsection) {
        const subBtn = page.locator(
          `[data-testid="settings-subtab-${subsection}"], [role="tab"][data-value="${subsection}"]`,
        )
        if (await subBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
          await subBtn.click()
          await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })
        }
      }
    })
  },
})

export { expect }
export type { Page }
