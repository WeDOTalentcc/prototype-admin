/**
 * Test Suite — Sidebar Recrutar (expandable menu)
 *
 * Cobre o novo comportamento do item "Recrutar" do sidebar:
 *   - Clicar em "Recrutar" navega para /recrutar (Pipeline Overview) E expande os sub-itens.
 *   - Auto-expansão quando o usuário navega direto para /jobs (Vagas) ou /funil-de-talentos.
 *   - Sub-itens "Vagas" e "Funil de Talentos" ficam visíveis após a expansão.
 *   - Tooltips do sidebar colapsado mostram os novos labels (Conversar / Decidir / Recrutar).
 *   - Navegação por teclado expande Recrutar e ativa Vagas / Funil de Talentos.
 *
 * Assume locale pt-BR (auth fixture já navega para /pt/chat).
 */

import { test, expect } from '../../fixtures/auth.fixture';
import type { Page, Locator } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sidebarRoot(page: Page): Locator {
  // O Sidebar usa <aside aria-label="Menu principal"> (key labels.mainMenu).
  return page.getByRole('complementary', { name: /Menu principal|Main menu/i }).first();
}

function recrutarButton(page: Page): Locator {
  return sidebarRoot(page).getByRole('button', { name: /^Recrutar$/i }).first();
}

function sidebarButton(page: Page, name: RegExp): Locator {
  return sidebarRoot(page).getByRole('button', { name }).first();
}

/**
 * Garante que o sidebar do dashboard está montado antes de cada asserção.
 * Falha de forma determinística se a rota não renderiza o shell autenticado.
 */
async function expectSidebarMounted(page: Page) {
  await expect(
    sidebarRoot(page),
    'Sidebar do dashboard (aside aria-label="Menu principal") deve estar montado',
  ).toBeVisible({ timeout: 15000 });
}

async function expectRecrutarExpanded(page: Page) {
  const vagas = sidebarButton(page, /^Vagas$/i);
  const funil = sidebarButton(page, /^Funil de Talentos$/i);
  await expect(vagas, 'Sub-item "Vagas" deve estar visível quando Recrutar está expandido').toBeVisible({ timeout: 8000 });
  await expect(funil, 'Sub-item "Funil de Talentos" deve estar visível quando Recrutar está expandido').toBeVisible({ timeout: 8000 });
}

/**
 * Colapsa o sidebar clicando no botão de toggle (title = "Retrair menu (Ctrl+B)" em pt-BR).
 * Idempotente: se já estiver colapsado, o teste pode chamar novamente sem efeito.
 */
async function collapseSidebar(page: Page) {
  const toggle = sidebarRoot(page).locator('button[title*="Retrair menu"]').first();
  if (await toggle.isVisible({ timeout: 2000 }).catch(() => false)) {
    await toggle.click();
    // Após colapsar, o título do botão muda para "Expandir menu".
    await expect(
      sidebarRoot(page).locator('button[title*="Expandir menu"]').first(),
      'Toggle deve mudar para "Expandir menu" após colapsar',
    ).toBeVisible({ timeout: 5000 });
  }
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

test.describe('Sidebar — Recrutar (expandable + navigateOnClick)', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.waitForLoadState('domcontentloaded');
    await expectSidebarMounted(authenticatedPage);
  });

  test('SR-001: Item "Recrutar" coexiste com "Conversar" e "Decidir" no menu Operacional', async ({ authenticatedPage }) => {
    const conversar = sidebarButton(authenticatedPage, /^Conversar$/i);
    const decidir = sidebarButton(authenticatedPage, /^Decidir$/i);
    const recrutar = recrutarButton(authenticatedPage);

    await expect(conversar, 'SR-001: botão "Conversar" deve estar visível').toBeVisible({ timeout: 10000 });
    await expect(decidir, 'SR-001: botão "Decidir" deve estar visível').toBeVisible({ timeout: 10000 });
    await expect(recrutar, 'SR-001: botão "Recrutar" deve estar visível').toBeVisible({ timeout: 10000 });
  });

  test('SR-002: Clicar em "Recrutar" navega para /recrutar E expande os sub-itens', async ({ authenticatedPage }) => {
    const recrutar = recrutarButton(authenticatedPage);
    await expect(recrutar).toBeVisible({ timeout: 10000 });

    // Antes do clique, sub-itens NÃO devem estar visíveis.
    const vagasBefore = sidebarButton(authenticatedPage, /^Vagas$/i);
    expect.soft(
      await vagasBefore.isVisible({ timeout: 1500 }).catch(() => false),
      'SR-002: sub-item "Vagas" não deve estar visível antes do clique em Recrutar',
    ).toBe(false);

    await recrutar.click();

    // 1) Navegação para /recrutar (com ou sem locale prefix).
    await authenticatedPage.waitForURL(/\/recrutar(?:\/|\?|$)/, { timeout: 10000 });
    expect(authenticatedPage.url(), 'SR-002: URL final deve incluir /recrutar').toMatch(/\/recrutar(?:\/|\?|$)/);

    // 2) Expansão.
    await expectRecrutarExpanded(authenticatedPage);
  });

  test('SR-003: Navegar direto para /jobs auto-expande Recrutar e marca Vagas como ativo', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/jobs', { waitUntil: 'domcontentloaded' });
    await authenticatedPage.waitForLoadState('networkidle').catch(() => {});
    await expectSidebarMounted(authenticatedPage);

    await expectRecrutarExpanded(authenticatedPage);

    const vagas = sidebarButton(authenticatedPage, /^Vagas$/i);
    await expect(vagas).toBeVisible();
    await expect(
      vagas,
      'SR-003: "Vagas" deve estar marcado como ativo (font-semibold) ao acessar /jobs direto',
    ).toHaveClass(/font-semibold/);
  });

  test('SR-004: Navegar direto para /funil-de-talentos auto-expande Recrutar e marca Funil como ativo', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/funil-de-talentos', { waitUntil: 'domcontentloaded' });
    await authenticatedPage.waitForLoadState('networkidle').catch(() => {});
    // /funil-de-talentos é uma rota canônica autenticada (renderiza CandidatesPage no
    // shell DashboardApp, conforme replit.md "Funil de Talentos canônico"). A sidebar
    // DEVE estar montada — falha dura se não estiver.
    await expectSidebarMounted(authenticatedPage);

    await expectRecrutarExpanded(authenticatedPage);

    const funil = sidebarButton(authenticatedPage, /^Funil de Talentos$/i);
    await expect(
      funil,
      'SR-004: "Funil de Talentos" deve estar marcado como ativo (font-semibold) ao acessar /funil-de-talentos direto',
    ).toHaveClass(/font-semibold/);
  });

  test('SR-005: Sidebar colapsado mostra tooltips com os novos labels Conversar / Decidir / Recrutar', async ({ authenticatedPage }) => {
    await collapseSidebar(authenticatedPage);

    const conversar = sidebarButton(authenticatedPage, /^Conversar$/i);
    const decidir = sidebarButton(authenticatedPage, /^Decidir$/i);
    const recrutar = recrutarButton(authenticatedPage);

    await expect(conversar).toBeVisible();
    await expect(decidir).toBeVisible();
    await expect(recrutar).toBeVisible();

    // O atributo `title` é o tooltip nativo do MenuItem em modo colapsado
    // (sidebar.tsx usa `title={isCollapsed && !shouldShowContent ? translatedLabel : undefined}`).
    await expect(
      conversar,
      'SR-005: tooltip do item "Conversar" não deve mais usar o label legado "Chat LIA"',
    ).toHaveAttribute('title', /^Conversar$/);
    await expect(
      decidir,
      'SR-005: tooltip do item "Decidir" não deve mais usar o label legado "Tarefas"',
    ).toHaveAttribute('title', /^Decidir$/);
    await expect(
      recrutar,
      'SR-005: tooltip do item "Recrutar" não deve mais usar o label legado "Visão do Funil"',
    ).toHaveAttribute('title', /^Recrutar$/);
  });

  test('SR-006: Navegação por teclado: focar Recrutar, pressionar Enter, expande e navega', async ({ authenticatedPage }) => {
    const recrutar = recrutarButton(authenticatedPage);
    await expect(recrutar).toBeVisible({ timeout: 10000 });

    // Focar o botão programaticamente (equivalente a chegar nele via Tab) e
    // ativar com Enter — caminho de teclado canônico para um <button>.
    await recrutar.focus();
    await expect(recrutar).toBeFocused();
    await authenticatedPage.keyboard.press('Enter');

    await authenticatedPage.waitForURL(/\/recrutar(?:\/|\?|$)/, { timeout: 10000 });
    await expectRecrutarExpanded(authenticatedPage);

    // Em seguida, focar "Vagas" (sub-item) e ativá-lo via Space — outro caminho
    // de teclado válido para <button>. Deve navegar para /jobs.
    const vagas = sidebarButton(authenticatedPage, /^Vagas$/i);
    await vagas.focus();
    await expect(vagas).toBeFocused();
    await authenticatedPage.keyboard.press('Space');

    await authenticatedPage.waitForURL(/\/jobs(?:\/|\?|$)/, { timeout: 10000 });
    expect(authenticatedPage.url(), 'SR-006: ativar Vagas via teclado deve navegar para /jobs').toMatch(/\/jobs(?:\/|\?|$)/);
  });

  test('SR-007: Clicar duas vezes em "Recrutar" alterna a expansão (toggle)', async ({ authenticatedPage }) => {
    const recrutar = recrutarButton(authenticatedPage);
    await expect(recrutar).toBeVisible({ timeout: 10000 });

    // Primeiro clique: expande + navega.
    await recrutar.click();
    await authenticatedPage.waitForURL(/\/recrutar(?:\/|\?|$)/, { timeout: 10000 }).catch(() => {});
    await expectRecrutarExpanded(authenticatedPage);

    // Segundo clique: toggle deve colapsar (sub-itens somem).
    await recrutar.click();
    const vagas = sidebarButton(authenticatedPage, /^Vagas$/i);
    await expect(
      vagas,
      'SR-007: segundo clique em "Recrutar" deve colapsar os sub-itens',
    ).toBeHidden({ timeout: 5000 });
  });
});
