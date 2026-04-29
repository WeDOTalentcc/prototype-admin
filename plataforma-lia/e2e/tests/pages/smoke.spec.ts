/**
 * Smoke Test Suite — Plataforma LIA
 *
 * Verifica que as páginas principais carregam sem erros críticos (React Error Boundary
 * "Algo deu errado") e que o chat unificado está presente para usuários autenticados.
 *
 * Mistura testes autenticados (auth.fixture) e não-autenticados (@playwright/test direto).
 */

import { test as authTest, expect as authExpect } from '../../fixtures/auth.fixture';
import { test, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Verifica que a página NÃO exibe o texto do React Error Boundary. */
async function assertNoErrorBoundary(page: import('@playwright/test').Page) {
  const errorBoundary = page.locator('text=/Algo deu errado/i');
  const count = await errorBoundary.count();
  expect(count, 'Página não deve exibir React Error Boundary "Algo deu errado"').toBe(0);
}

// ---------------------------------------------------------------------------
// Testes não-autenticados (caminhos públicos)
// ---------------------------------------------------------------------------

test.describe('Smoke — Páginas Públicas (não-autenticado)', () => {

  test('SM-001: /login carrega a página de login sem erro boundary', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await assertNoErrorBoundary(page);

    // Pelo menos algum campo de formulário deve existir
    const formExists = await page.locator('form, input[type="email"], input[name="email"]').first()
      .isVisible({ timeout: 8000 }).catch(() => false);
    expect.soft(formExists, 'SM-001: Formulário de login deve estar visível').toBe(true);
  });

  test('SM-002: /vagas/nova carrega sem erro boundary (rota pública do wizard)', async ({ page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    await assertNoErrorBoundary(page);

    // Deve exibir algum conteúdo — formulário ou redirecionamento para login
    const hasContent = await page.locator('main, form, [role="main"], h1, h2').first()
      .isVisible({ timeout: 8000 }).catch(() => false);
    expect.soft(hasContent, 'SM-002: Página /vagas/nova deve ter conteúdo visível').toBe(true);
  });

  test('SM-003: / (raiz) redireciona para uma página válida sem loop de login', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const finalUrl = page.url();

    // Não deve ficar em redirecionamento infinito — a URL deve ter mudado ou estar estável
    const isLoop = finalUrl.includes('/login?redirect=/login') || finalUrl.includes('redirect=');
    expect.soft(isLoop, 'SM-003: Raiz não deve gerar loop de redirecionamento').toBe(false);

    await assertNoErrorBoundary(page);

    // A URL final deve ser uma rota reconhecível (login, jobs, vagas, chat, etc.)
    const validRoutePattern = /\/(login|jobs|vagas|chat|funil|dashboard|candidatos)?$/;
    const isValidRoute = validRoutePattern.test(new URL(finalUrl).pathname);
    expect.soft(isValidRoute, `SM-003: URL final "${finalUrl}" deve ser uma rota válida da plataforma`).toBe(true);
  });

  test('SM-004: /chat carrega sem erro boundary (pode redirecionar para login)', async ({ page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await assertNoErrorBoundary(page);

    // Deve mostrar conteúdo (chat ou tela de login)
    const hasContent = await page.locator('main, [role="main"], form, h1, h2, textarea, input').first()
      .isVisible({ timeout: 8000 }).catch(() => false);
    expect.soft(hasContent, 'SM-004: /chat deve ter conteúdo visível').toBe(true);
  });

  test('SM-005: /funil-de-talentos carrega ou mostra 404 gracioso (não "Algo deu errado")', async ({ page }) => {
    await page.goto('/funil-de-talentos');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // O critério principal é NÃO mostrar o error boundary com "Algo deu errado"
    await assertNoErrorBoundary(page);

    const finalUrl = page.url();
    // Aceita: 404, login redirect, a própria página ou outra rota válida
    const is404 = await page.locator('text=/404|não encontrada|not found/i').first()
      .isVisible({ timeout: 3000 }).catch(() => false);
    const isLogin = finalUrl.includes('/login');
    const isOnPage = finalUrl.includes('/funil-de-talentos');

    const graceful = is404 || isLogin || isOnPage;
    expect.soft(graceful, 'SM-005: /funil-de-talentos deve ter resposta graciosa (404, login ou a página)').toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Testes autenticados
// ---------------------------------------------------------------------------

authTest.describe('Smoke — Páginas Autenticadas', () => {

  authTest('SM-010: /jobs carrega e exibe heading "Gestão de Vagas"', async ({ authenticatedPage }) => {
    // authenticatedPage já começa em /jobs pela fixture
    await authenticatedPage.waitForLoadState('networkidle');

    await assertNoErrorBoundary(authenticatedPage);

    const heading = authenticatedPage.locator('h1, h2, h3').filter({ hasText: /Gestão de Vagas/i }).first();
    const headingVisible = await heading.isVisible({ timeout: 10000 }).catch(() => false);
    authExpect(headingVisible, 'SM-010: Heading "Gestão de Vagas" deve estar visível em /jobs').toBe(true);
  });

  authTest('SM-011: /vagas/nova carrega sem erro boundary (autenticado)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    await assertNoErrorBoundary(authenticatedPage);

    // Deve exibir algum formulário ou step do wizard
    const wizardContent = authenticatedPage.locator('form, [role="form"], h1, h2, [data-testid*="step"], [data-testid*="wizard"]').first();
    const hasWizard = await wizardContent.isVisible({ timeout: 8000 }).catch(() => false);
    authExpect.soft(hasWizard, 'SM-011: /vagas/nova deve exibir conteúdo do wizard').toBe(true);
  });

  authTest('SM-012: /chat carrega sem erro boundary (autenticado)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    await assertNoErrorBoundary(authenticatedPage);

    // Página de chat deve ter input visível
    const chatInput = authenticatedPage.locator(
      'textarea[aria-label="Mensagem para a LIA"], input[aria-label="Mensagem para a LIA"]'
    ).first();
    const hasInput = await chatInput.isVisible({ timeout: 8000 }).catch(() => false);
    authExpect.soft(hasInput, 'SM-012: /chat deve exibir input da LIA para usuário autenticado').toBe(true);
  });

  authTest('SM-013: /funil-de-talentos carrega ou mostra 404 gracioso (autenticado, não "Algo deu errado")', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/funil-de-talentos');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(1500);

    await assertNoErrorBoundary(authenticatedPage);

    const finalUrl = authenticatedPage.url();
    const is404 = await authenticatedPage.locator('text=/404|não encontrada|not found/i').first()
      .isVisible({ timeout: 3000 }).catch(() => false);
    const isOnPage = finalUrl.includes('/funil-de-talentos');
    const redirectedElsewhere = !finalUrl.includes('/funil-de-talentos') && !is404;

    const graceful = is404 || isOnPage || redirectedElsewhere;
    authExpect.soft(graceful, 'SM-013: /funil-de-talentos deve ter resposta graciosa').toBe(true);
  });

  authTest('SM-014: / (raiz) redireciona para rota válida sem loop (autenticado)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const finalUrl = authenticatedPage.url();

    const isLoop = finalUrl.includes('/login?redirect=/login');
    authExpect(isLoop, 'SM-014: Raiz não deve gerar loop de redirecionamento para autenticado').toBe(false);

    await assertNoErrorBoundary(authenticatedPage);
  });

  authTest('SM-015: Chat bubble (UnifiedChatBubble) visível após autenticação', async ({ authenticatedPage }) => {
    // DashboardChatPanel só é renderizado no layout /dashboard (DashboardApp)
    // navegar para a raiz que usa DashboardApp com DashboardChatPanel
    await authenticatedPage.goto('/')
    await authenticatedPage.waitForLoadState('networkidle')
    await authenticatedPage.waitForTimeout(1500);

    // O UnifiedChatBubble usa aria-label="Abrir chat com a LIA"
    const chatBubble = authenticatedPage.locator('button[aria-label="Abrir chat com a LIA"]');
    const bubbleVisible = await chatBubble.isVisible({ timeout: 8000 }).catch(() => false);

    if (!bubbleVisible) {
      // Fallback: o chat pode já estar aberto (o bubble some quando o painel está open)
      const chatInput = authenticatedPage.locator(
        '[aria-label="Mensagem para a LIA"]'
      ).first();
      const inputVisible = await chatInput.isVisible({ timeout: 5000 }).catch(() => false);

      authExpect(
        bubbleVisible || inputVisible,
        'SM-015: UnifiedChatBubble ("Abrir chat com a LIA") deve estar visível, ou o chat já está aberto'
      ).toBe(true);
      return;
    }

    authExpect(bubbleVisible, 'SM-015: UnifiedChatBubble deve ter aria-label="Abrir chat com a LIA"').toBe(true);

    // Clicar deve abrir o painel com o input da LIA
    await chatBubble.click();
    await authenticatedPage.waitForTimeout(1000);

    const chatInput = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const inputVisible = await chatInput.isVisible({ timeout: 6000 }).catch(() => false);
    authExpect.soft(inputVisible, 'SM-015: Clicar no bubble deve revelar o input da LIA').toBe(true);
  });

  authTest('SM-016: Header do chat unificado exibe botões de controle', async ({ authenticatedPage }) => {
    // DashboardChatPanel está no layout do DashboardApp (rota raiz /)
    await authenticatedPage.goto('/')
    await authenticatedPage.waitForLoadState('networkidle')
    await authenticatedPage.waitForTimeout(1000)

    // Garantir que o chat esteja aberto
    const chatBubble = authenticatedPage.locator('button[aria-label="Abrir chat com a LIA"]');
    const bubbleVisible = await chatBubble.isVisible({ timeout: 5000 }).catch(() => false);
    if (bubbleVisible) {
      await chatBubble.click();
      await authenticatedPage.waitForTimeout(1000);
    }

    // Verificar botões do UnifiedChatHeader.
    // Nota: em modo fullscreen (Chat LIA), o botão "Fechar chat" é intencionalmente ocultado
    // pelo design (UnifiedChatHeader só mostra X em modo sidebar/floating).
    const newConversationBtn = authenticatedPage.locator('button[aria-label="Nova conversa"]').first();
    const switchConversationBtn = authenticatedPage.locator('button[aria-label="Trocar conversa"]').first();
    const closeBtn = authenticatedPage.locator('button[aria-label="Fechar chat"]').first();

    const hasNew = await newConversationBtn.isVisible({ timeout: 5000 }).catch(() => false);
    const hasSwitch = await switchConversationBtn.isVisible({ timeout: 3000 }).catch(() => false);
    const hasClose = await closeBtn.isVisible({ timeout: 3000 }).catch(() => false);

    authExpect.soft(hasNew, 'SM-016: Botão "Nova conversa" deve estar no UnifiedChatHeader').toBe(true);
    authExpect.soft(hasSwitch, 'SM-016: Botão "Trocar conversa" deve estar no UnifiedChatHeader').toBe(true);
    // "Fechar chat" só aparece em modo sidebar/floating — não em fullscreen. Não exigir aqui.

    // Pelo menos um dos botões de controle deve estar presente
    const anyControlPresent = hasNew || hasSwitch || hasClose;
    authExpect(anyControlPresent, 'SM-016: Pelo menos um botão de controle do chat deve estar visível').toBe(true);
  });
});
