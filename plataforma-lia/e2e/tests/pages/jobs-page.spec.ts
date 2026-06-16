/**
 * Test Suite: Página /jobs — Gestão de Vagas
 *
 * Testes focados na página de listagem de vagas:
 * - Ausência de React Error Boundary
 * - Heading principal
 * - Botão "Nova Vaga"
 * - Filtros de navegação (tabs/abas)
 * - Lista de vagas ou empty state gracioso
 * - Ação de criação de nova vaga (modal ou wizard)
 */

import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Página /jobs — Gestão de Vagas', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    // A fixture já navega para /jobs; garantir que a página está totalmente carregada.
    await authenticatedPage.waitForLoadState('networkidle');
    // Aguardar hidratação do React e possíveis chamadas de API iniciais.
    await authenticatedPage.waitForTimeout(2000);
  });

  // -------------------------------------------------------------------------
  // JP-001: Sem React Error Boundary
  // -------------------------------------------------------------------------
  test('JP-001: /jobs renderiza sem React Error Boundary ("Algo deu errado")', async ({ authenticatedPage }) => {
    const errorBoundary = authenticatedPage.locator('text=/Algo deu errado/i');
    const boundaryCount = await errorBoundary.count();

    expect(
      boundaryCount,
      'JP-001: A página /jobs não deve exibir o React Error Boundary "Algo deu errado"'
    ).toBe(0);

    // Garantir também que não há erros genéricos de servidor
    const serverError = await authenticatedPage.locator('text=/500 Internal|Something went wrong/i').count();
    expect.soft(serverError, 'JP-001: Não deve haver erro 500 na página').toBe(0);
  });

  // -------------------------------------------------------------------------
  // JP-002: Heading "Gestão de Vagas"
  // -------------------------------------------------------------------------
  test('JP-002: Heading "Gestão de Vagas" está visível', async ({ authenticatedPage }) => {
    const heading = authenticatedPage
      .locator('h1, h2, h3, [role="heading"]')
      .filter({ hasText: /Gestão de Vagas/i })
      .first();

    const isVisible = await heading.isVisible({ timeout: 10000 }).catch(() => false);

    if (!isVisible) {
      // Captura de tela para diagnóstico em caso de falha
      await authenticatedPage.screenshot({
        path: 'e2e/screenshots/jobs-page-heading-missing.png',
        fullPage: true,
      });
    }

    expect(isVisible, 'JP-002: Heading "Gestão de Vagas" deve estar visível em /jobs').toBe(true);
  });

  // -------------------------------------------------------------------------
  // JP-003: Botão "Nova Vaga" presente
  // -------------------------------------------------------------------------
  test('JP-003: Botão "Nova Vaga" está visível', async ({ authenticatedPage }) => {
    const novaVagaBtn = authenticatedPage
      .getByRole('button', { name: /Nova Vaga/i })
      .first();

    // Fallback: pode ser um link estilizado como botão
    const novaVagaLink = authenticatedPage
      .getByRole('link', { name: /Nova Vaga/i })
      .first();

    const btnVisible = await novaVagaBtn.isVisible({ timeout: 8000 }).catch(() => false);
    const linkVisible = await novaVagaLink.isVisible({ timeout: 3000 }).catch(() => false);

    const isVisible = btnVisible || linkVisible;

    expect.soft(isVisible, 'JP-003: Botão ou link "Nova Vaga" deve estar presente na página /jobs').toBe(true);

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/jobs-page-nova-vaga-btn.png',
    });
  });

  // -------------------------------------------------------------------------
  // JP-004: Filtros de navegação presentes (tabs / abas)
  // -------------------------------------------------------------------------
  test('JP-004: Filtros de navegação (tabs/abas) estão presentes', async ({ authenticatedPage }) => {
    // Seletores comuns para sistemas de tabs em shadcn/ui e Radix
    const tabSelectors = [
      '[role="tablist"]',
      '[role="tab"]',
      'nav[aria-label]',
      // Texto de aba esperado: "Visão Geral", "Ativas", "Encerradas", etc.
      'button:has-text("Visão Geral")',
      'button:has-text("Ativas")',
      'button:has-text("Todas")',
      '[data-testid*="tab"]',
      '[data-testid*="filter"]',
    ];

    let foundTab = false;
    let foundSelector = '';

    for (const selector of tabSelectors) {
      const el = authenticatedPage.locator(selector).first();
      if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
        foundTab = true;
        foundSelector = selector;
        break;
      }
    }

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/jobs-page-navigation-filters.png',
    });

    if (!foundTab) {
      test.info().annotations.push({
        type: 'info',
        description: 'JP-004: Nenhum seletor de tab/filtro encontrado — a UI pode usar dropdowns ou outro padrão de navegação.',
      });
    }

    expect.soft(foundTab, `JP-004: Deve haver filtros/tabs de navegação na página /jobs (tentados: ${tabSelectors.join(', ')})`).toBe(true);

    if (foundTab) {
      test.info().annotations.push({
        type: 'info',
        description: `JP-004: Tab/filtro encontrado com seletor: "${foundSelector}"`,
      });
    }
  });

  // -------------------------------------------------------------------------
  // JP-005: Lista de vagas renderiza ou exibe empty state gracioso
  // -------------------------------------------------------------------------
  test('JP-005: Lista de vagas renderiza ou exibe empty state gracioso', async ({ authenticatedPage }) => {
    // Esperar possível carregamento de dados via API
    await authenticatedPage.waitForTimeout(3000);

    // Padrões possíveis para itens de vaga na lista
    const jobItemSelectors = [
      '[data-testid*="job-card"]',
      '[data-testid*="job-item"]',
      '[data-testid*="vaga"]',
      'article',
      '[role="listitem"]',
      'li[class*="job"]',
      'li[class*="vaga"]',
      '.job-card',
    ];

    // Padrões possíveis para empty state
    const emptyStateSelectors = [
      'text=/Nenhuma vaga/i',
      'text=/Sem vagas/i',
      'text=/Nenhum resultado/i',
      'text=/vaga encontrada/i',
      'text=/Crie sua primeira/i',
      '[data-testid*="empty"]',
      '[data-testid*="empty-state"]',
    ];

    let hasJobItems = false;
    let hasEmptyState = false;

    for (const selector of jobItemSelectors) {
      const count = await authenticatedPage.locator(selector).count();
      if (count > 0) {
        hasJobItems = true;
        test.info().annotations.push({
          type: 'info',
          description: `JP-005: ${count} item(ns) de vaga encontrado(s) com seletor "${selector}"`,
        });
        break;
      }
    }

    if (!hasJobItems) {
      for (const selector of emptyStateSelectors) {
        const visible = await authenticatedPage.locator(selector).first()
          .isVisible({ timeout: 3000 }).catch(() => false);
        if (visible) {
          hasEmptyState = true;
          test.info().annotations.push({
            type: 'info',
            description: `JP-005: Empty state encontrado com seletor "${selector}"`,
          });
          break;
        }
      }
    }

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/jobs-page-list-state.png',
      fullPage: true,
    });

    // A página é válida se tem itens OU se tem empty state. Não pode ser nenhum dos dois
    // (o que indicaria que o conteúdo não carregou de forma nenhuma).
    const hasValidContent = hasJobItems || hasEmptyState;

    expect.soft(
      hasValidContent,
      'JP-005: /jobs deve exibir lista de vagas ou mensagem de empty state — conteúdo não carregou'
    ).toBe(true);

    // Também garantir que não aparece o error boundary nesta fase de carregamento
    const errorBoundary = await authenticatedPage.locator('text=/Algo deu errado/i').count();
    expect(
      errorBoundary,
      'JP-005: Error boundary não deve aparecer durante carregamento da lista'
    ).toBe(0);
  });

  // -------------------------------------------------------------------------
  // JP-006: Clicar em "Nova Vaga" abre modal ou navega para o wizard
  // -------------------------------------------------------------------------
  test('JP-006: Clicar em "Nova Vaga" abre modal ou navega para o wizard', async ({ authenticatedPage }) => {
    const novaVagaBtn = authenticatedPage
      .getByRole('button', { name: /Nova Vaga/i })
      .first();

    const novaVagaLink = authenticatedPage
      .getByRole('link', { name: /Nova Vaga/i })
      .first();

    const btnVisible = await novaVagaBtn.isVisible({ timeout: 8000 }).catch(() => false);
    const linkVisible = await novaVagaLink.isVisible({ timeout: 3000 }).catch(() => false);

    if (!btnVisible && !linkVisible) {
      test.info().annotations.push({
        type: 'info',
        description: 'JP-006: Botão/link "Nova Vaga" não encontrado — pulando teste de interação.',
      });
      // Soft fail: o teste de presença (JP-003) já trata esse caso
      return;
    }

    const urlBefore = authenticatedPage.url();

    if (btnVisible) {
      await novaVagaBtn.click();
    } else {
      await novaVagaLink.click();
    }

    await authenticatedPage.waitForTimeout(1500);

    const urlAfter = authenticatedPage.url();
    const urlChanged = urlAfter !== urlBefore;

    // Verificar se abriu um modal (dialog)
    const modalVisible = await authenticatedPage
      .locator('[role="dialog"]')
      .first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);

    // Verificar se navegou para o wizard (/vagas/nova ou similar)
    const navigatedToWizard = urlAfter.includes('/vagas/nova') || urlAfter.includes('/nova');

    // Verificar se exibe conteúdo de criação de vaga (formulário step 1)
    const hasWizardContent = await authenticatedPage
      .locator('h1, h2, h3, [role="heading"]')
      .filter({ hasText: /nova vaga|criar vaga|informações básicas|título da vaga/i })
      .first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/jobs-page-nova-vaga-action.png',
      fullPage: true,
    });

    const actionWorked = modalVisible || navigatedToWizard || hasWizardContent || urlChanged;

    expect(
      actionWorked,
      'JP-006: Clicar em "Nova Vaga" deve abrir modal, navegar para wizard ou exibir conteúdo de criação'
    ).toBe(true);

    if (modalVisible) {
      test.info().annotations.push({ type: 'info', description: 'JP-006: Modal de nova vaga aberto com sucesso.' });
    }
    if (navigatedToWizard) {
      test.info().annotations.push({ type: 'info', description: `JP-006: Navegou para o wizard: ${urlAfter}` });
    }
  });

  // -------------------------------------------------------------------------
  // JP-007: Página não exibe erros de console críticos (verify estrutura básica)
  // -------------------------------------------------------------------------
  test('JP-007: Estrutura básica da página está presente (main, nav ou similar)', async ({ authenticatedPage }) => {
    // Verificar que a página tem estrutura semântica básica
    const mainContent = authenticatedPage.locator('main, [role="main"], #main-content').first();
    const hasMain = await mainContent.isVisible({ timeout: 8000 }).catch(() => false);

    expect.soft(hasMain, 'JP-007: Página /jobs deve ter elemento <main> ou role="main"').toBe(true);

    // Verificar que não há skeleton loaders infinitos (loading state travado)
    await authenticatedPage.waitForTimeout(3000);
    const skeletonCount = await authenticatedPage
      .locator('[data-testid*="skeleton"], [class*="skeleton"], [aria-label*="carregando"]')
      .count();

    // Soft check: se há muitos skeletons após 5s, pode indicar loading travado
    expect.soft(
      skeletonCount,
      `JP-007: Após 5s, não deveria haver ${skeletonCount} skeleton(s) — pode indicar loading state travado`
    ).toBeLessThan(10);

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/jobs-page-structure.png',
      fullPage: false,
    });
  });
});
