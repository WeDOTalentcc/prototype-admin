/**
 * Test Suite: Chat Flutuante / LiaChatPanel
 * Audits the floating chat panel accessible via the LIA floating button.
 */

import { test, expect } from '../../fixtures/auth.fixture';
import type { Locator } from '@playwright/test';

test.describe('Chat Flutuante (LiaChatPanel) — Auditoria de Usabilidade', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);
  });

  test('TC-CF-001: Input da LIA visível no painel flutuante', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[placeholder*="Envie mensagem"]',
    ];

    let found = false;
    for (const selector of inputSelectors) {
      if (await authenticatedPage.locator(selector).isVisible({ timeout: 5000 }).catch(() => false)) {
        found = true;
        break;
      }
    }

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-page-initial.png', fullPage: true });
    expect(found, 'LIA input must be visible in chat panel').toBe(true);
  });

  test('TC-CF-002: Botão de limpar mensagens presente no painel flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-controles.png' });

    const clearButton = authenticatedPage.locator('button[aria-label="Limpar mensagens"]').first();
    await expect(clearButton, 'Limpar button must be present in floating panel').toBeVisible({ timeout: 5000 });
  });

  test('TC-CF-003: Botão de fechar chat presente no painel flutuante', async ({ authenticatedPage }) => {
    const closeButton = authenticatedPage.locator('button[aria-label="Fechar chat"], [data-dismiss="true"]').first();
    await expect(closeButton, 'Fechar button must be present in floating panel').toBeVisible({ timeout: 5000 });
  });

  test('TC-CF-004: Botão novo chat presente no painel flutuante', async ({ authenticatedPage }) => {
    const newChatButton = authenticatedPage.locator('button[aria-label="Iniciar novo chat"]').first();
    await expect(newChatButton, 'Novo Chat button must be present in floating panel').toBeVisible({ timeout: 5000 });
  });

  test('TC-CF-005: Botão histórico presente no painel flutuante', async ({ authenticatedPage }) => {
    const historyButton = authenticatedPage.locator('button[aria-label="Ver histórico de conversas"]').first();
    await expect(historyButton, 'Histórico button must be present in floating panel').toBeVisible({ timeout: 5000 });
  });

  test('TC-CF-006: Botão expandir chat presente no painel flutuante', async ({ authenticatedPage }) => {
    const expandButton = authenticatedPage.locator('button[aria-label="Expandir chat"]').first();
    await expect(expandButton, 'Expandir button must be present in floating panel').toBeVisible({ timeout: 5000 });
  });

  test('TC-CF-007: Digitação e envio de mensagem no painel flutuante', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[placeholder*="Envie mensagem"]',
    ];

    let input: Locator | null = null;
    for (const selector of inputSelectors) {
      const el = authenticatedPage.locator(selector).first();
      if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
        input = el;
        break;
      }
    }

    expect(input, 'Input must be found in floating chat').not.toBeNull();

    const testMsg = `Teste flutuante ${Date.now()}`;
    await input!.click();
    await input!.fill(testMsg);

    const value = await input!.inputValue();
    expect(value, 'Input must accept typed text').toBe(testMsg);

    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    await expect(sendButton, 'Send button must be enabled with text').toBeEnabled({ timeout: 3000 });

    await input!.press('Enter');
    await authenticatedPage.waitForTimeout(1500);

    const valueAfter = await input!.inputValue().catch(() => '');
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-mensagem-enviada.png' });
    expect(valueAfter, 'Input must be cleared after Enter (message sent)').toBe('');
  });

  test('TC-CF-008: Botão Send desabilitado com input vazio', async ({ authenticatedPage }) => {
    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();

    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await input.fill('');
      await expect(sendButton, 'Send button must be disabled when input is empty').toBeDisabled({ timeout: 3000 });
    }

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-send-disabled.png' });
  });

  test('TC-CF-009: Alinhamento dos balões — user à direita (justify-end)', async ({ authenticatedPage }) => {
    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await input.click();
      await input.fill('Olá LIA!');
      await input.press('Enter');
      await authenticatedPage.waitForTimeout(2000);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-alinhamento-baloes.png' });

      const userBubbles = authenticatedPage.locator('.flex.justify-end').first();
      await expect(userBubbles, 'User messages must use justify-end (right alignment)').toBeVisible({ timeout: 5000 });
    }
  });

  test('TC-CF-010: Painel flutuante na posição fixed com z-index adequado', async ({ authenticatedPage }) => {
    const chatPanel = authenticatedPage.locator('[role="dialog"][aria-label*="Chat LIA"]').first();
    const isPanelOpen = await chatPanel.isVisible({ timeout: 3000 }).catch(() => false);

    if (isPanelOpen) {
      const position = await authenticatedPage.evaluate(() => {
        const el = document.querySelector('[role="dialog"][aria-label*="Chat LIA"]');
        if (!el) return null;
        const style = window.getComputedStyle(el);
        return { position: style.position, zIndex: parseInt(style.zIndex) };
      });

      if (position) {
        expect(position.position, 'Floating panel must use position: fixed').toBe('fixed');
        expect(position.zIndex, 'Floating panel z-index must be >= 50').toBeGreaterThanOrEqual(50);
      }

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-posicao.png' });
    }
  });

  test('TC-CF-011: Histórico de conversas abre e fecha corretamente', async ({ authenticatedPage }) => {
    const historyBtn = authenticatedPage.locator('button[aria-label="Ver histórico de conversas"]').first();
    await expect(historyBtn).toBeVisible({ timeout: 5000 });

    await historyBtn.click();
    await authenticatedPage.waitForTimeout(1000);
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-historico.png' });

    const historySectionTitle = authenticatedPage.locator('text=/Conversas recentes/i').first();
    await expect(historySectionTitle, 'History section should appear after clicking history button').toBeVisible({ timeout: 3000 });

    await historyBtn.click();
    await authenticatedPage.waitForTimeout(500);

    const historyGone = await historySectionTitle.isVisible({ timeout: 1000 }).catch(() => false);
    expect(historyGone, 'History section should hide after toggling history button').toBe(false);
  });

  test('TC-CF-012: Ciclo completo de abertura e fechamento do painel flutuante via botão flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(1000);

    const floatTriggerSelectors = [
      'button[aria-label="Abrir chat LIA"]',
      'button[aria-label="Abrir chat"]',
      '[data-testid="lia-float-button"]',
    ];

    let floatButton: Locator | null = null;
    for (const sel of floatTriggerSelectors) {
      const btn = authenticatedPage.locator(sel).first();
      if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
        floatButton = btn;
        break;
      }
    }

    if (!floatButton) {
      test.info().annotations.push({
        type: 'info',
        description: 'TC-CF-012: Floating trigger button not found (chat may already be open by default on /vagas). Validating that panel is visible and closable.'
      });

      const closeBtn = authenticatedPage.locator('[data-dismiss="true"], button[aria-label="Fechar chat"]').first();
      const hasClose = await closeBtn.isVisible({ timeout: 5000 }).catch(() => false);
      expect(hasClose, 'If chat is open by default, close button must be present').toBe(true);

      await closeBtn.click();
      await authenticatedPage.waitForTimeout(500);
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-close-lifecycle.png' });
      return;
    }

    await floatButton.click();
    await authenticatedPage.waitForTimeout(800);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-opened-via-float-button.png' });

    const input = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    await expect(input, 'Chat panel input must be visible after clicking float trigger button').toBeVisible({ timeout: 5000 });

    const closeBtn = authenticatedPage.locator('[data-dismiss="true"], button[aria-label="Fechar chat"]').first();
    const hasClose = await closeBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasClose) {
      await closeBtn.click();
      await authenticatedPage.waitForTimeout(500);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-closed-via-button.png' });

      const inputAfterClose = await input.isVisible({ timeout: 1500 }).catch(() => false);
      expect(inputAfterClose, 'Chat panel must be closed (input hidden) after clicking close button').toBe(false);
    }
  });

  test('TC-CF-013: Contexto do chat mantido ao navegar entre páginas', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInput = await input.isVisible({ timeout: 3000 }).catch(() => false);

    if (!hasInput) {
      test.info().annotations.push({ type: 'info', description: 'TC-CF-013: Chat panel not visible at /vagas — cannot test context persistence' });
      return;
    }

    const testMsg = `Contexto ${Date.now()}`;
    await input.click();
    await input.fill(testMsg);
    await input.press('Enter');
    await authenticatedPage.waitForTimeout(2000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-before-navigation.png' });

    await authenticatedPage.goto('/candidatos');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-flutuante-after-navigation.png' });

    const inputAfterNav = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInputAfterNav = await inputAfterNav.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasInputAfterNav) {
      test.info().annotations.push({
        type: 'bug',
        description: 'BUG-CF-013: Floating chat panel disappeared after page navigation — context not persisted'
      });
    }

    expect(hasInputAfterNav, 'Floating chat panel must remain visible and functional across page navigation').toBe(true);
  });
});
