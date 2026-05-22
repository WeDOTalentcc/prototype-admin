/**
 * Test helpers canonical pra persistence assertions.
 *
 * Pattern: fill → save → reload → assert preservado. Esse é o
 * round-trip que comprova persistência REAL (BD + GET refresh),
 * complementar aos sensors de validação (`canonical-fix`, ADR-001,
 * etc) que só cobrem write path.
 *
 * ⚠ Selectors canonical em Configurações > Minha Empresa NÃO usam
 * `data-field` uniformemente hoje (auditoria 2026-05-21). Os helpers
 * abaixo aceitam `Locator` ou seletor para permitir que cada test
 * use a estratégia adequada (text/role/aria) enquanto o frontend
 * não padroniza `data-field` em todos os inputs editáveis. TODO
 * em backlog: adicionar `data-field="<canonical_key>"` em
 * `MinhaEmpresaCard.tsx:144` (input edit-in-place) + cards
 * irmãos. Quando isso acontecer, simplificar estes helpers.
 */
import { expect, type Locator, type Page } from '@playwright/test'

const SAVE_TOAST_RE = /^(Salvo|Salvas?|Sucesso|Configurações atualizadas)/i

/**
 * Aguarda confirmação visual de save bem-sucedido (toast | spinner
 * desaparecer | botão voltar pro estado "Editar").
 */
export async function waitForSaveSuccess(page: Page, timeoutMs = 8_000): Promise<void> {
  // Tenta 3 sinais canonical em paralelo. Primeiro a resolver vence.
  await Promise.race([
    page.getByText(SAVE_TOAST_RE).first().waitFor({ state: 'visible', timeout: timeoutMs }),
    page.locator('[data-testid="save-success"]').first().waitFor({ state: 'visible', timeout: timeoutMs }),
    // Spinner de salvar deve sumir
    page.locator('[data-testid="save-btn"] svg.animate-spin').first().waitFor({
      state: 'hidden',
      timeout: timeoutMs,
    }),
  ]).catch(() => {
    // Last resort: dá 1s pro re-render — alguns saves não emitem toast,
    // só fecham o modo "editing" (vide `MinhaEmpresaCard.tsx`).
    return page.waitForTimeout(1_000)
  })
}

/**
 * Assert canonical: fill em input edit-in-place + save + reload +
 * value preservado após GET refresh.
 *
 * @param page   — Playwright Page já autenticado
 * @param input  — Locator do <input> editável (NÃO o botão "Editar")
 * @param saveBtn — Locator do botão "Salvar" / check icon
 * @param value  — Valor a injetar
 */
export async function assertInputPersistsAfterRefresh(
  page: Page,
  input: Locator,
  saveBtn: Locator,
  value: string,
): Promise<void> {
  await expect(input).toBeVisible({ timeout: 10_000 })
  await input.fill(value)
  await saveBtn.click()
  await waitForSaveSuccess(page)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })
}

/**
 * Assert canonical pra ToggleSwitch (`role="switch"`): flip + wait
 * PATCH + reload + state preservado.
 *
 * Usa `role="switch"` + `aria-checked` (pattern canonical do
 * `LearningLoopsPanel.ToggleSwitch` e `LiaFieldsConfigPanel`).
 */
export async function assertSwitchPersistsAfterRefresh(
  page: Page,
  ariaLabel: string,
): Promise<{ before: boolean; after: boolean }> {
  const sw = page.getByRole('switch', { name: ariaLabel }).first()
  await expect(sw, `[setup] switch "${ariaLabel}" não está visível`).toBeVisible({ timeout: 10_000 })
  const before = (await sw.getAttribute('aria-checked')) === 'true'
  await sw.click()
  // PATCH é fire-and-forget — esperamos network idle como proxy de "salvou"
  await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })
  const swAfter = page.getByRole('switch', { name: ariaLabel }).first()
  await expect(swAfter).toBeVisible({ timeout: 10_000 })
  const after = (await swAfter.getAttribute('aria-checked')) === 'true'
  expect(
    after,
    `[persistence FAIL] switch "${ariaLabel}" voltou pra ${before} após reload (esperado: ${!before})`,
  ).toBe(!before)
  return { before, after }
}

/**
 * Restore helper: flipa de volta pra estado inicial. Usar em
 * `test.afterEach` quando o test mutou state compartilhado.
 */
export async function restoreSwitch(page: Page, ariaLabel: string, desired: boolean): Promise<void> {
  const sw = page.getByRole('switch', { name: ariaLabel }).first()
  if (!(await sw.isVisible({ timeout: 3_000 }).catch(() => false))) return
  const current = (await sw.getAttribute('aria-checked')) === 'true'
  if (current !== desired) {
    await sw.click()
    await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => { /* ok */ })
  }
}
