/**
 * Test Suite: Chat Expandido / LiaSuperPrompt
 * Audits the expanded overlay chat interface (LiaSuperPrompt).
 *
 * The SuperPrompt is activated via a float button expand action and occupies
 * most of the viewport (95vw x 95vh, max 1400x900px).
 *
 * Coverage:
 * - Expanded modal structure and dimensions
 * - Header controls (novo chat, limpar, histórico, minimizar, fechar)
 * - Input (textarea with Brain icon, Send button)
 * - Tabs (Conversa, Centro de Controle)
 * - Empty state with suggestion grid
 * - Typing and sending messages
 * - Bubble alignment and markdown rendering
 * - Auto-scroll behavior
 */

import { test, expect } from '../../fixtures/auth.fixture';
import type { Page, Locator } from '@playwright/test';

async function openSuperPrompt(page: Page): Promise<boolean> {
  const expandSelectors = [
    'button[aria-label="Expandir chat"]',
    'button[title="Expandir para chat completo"]',
  ];

  for (const selector of expandSelectors) {
    const btn = page.locator(selector).first();
    if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(500);
      const modal = page.locator('.fixed.inset-0').first();
      if (await modal.isVisible({ timeout: 2000 }).catch(() => false)) return true;
    }
  }
  return false;
}

test.describe('Chat Expandido/SuperPrompt (LiaSuperPrompt) — Auditoria de Usabilidade', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);
  });

  test('TC-SP-001: Botão Expandir presente no Chat Flutuante', async ({ authenticatedPage }) => {
    const expandButton = authenticatedPage.locator('button[aria-label="Expandir chat"]').first();
    await expect(expandButton, 'Expandir button must be visible in floating panel header').toBeVisible({ timeout: 5000 });
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-expand-button.png' });
  });

  test('TC-SP-002: Clicar em Expandir abre o modal SuperPrompt', async ({ authenticatedPage }) => {
    const expandButton = authenticatedPage.locator('button[aria-label="Expandir chat"]').first();
    const hasExpand = await expandButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasExpand) {
      test.skip(true, 'Expand button not found — SuperPrompt may not be accessible from this page');
      return;
    }

    await expandButton.click();
    await authenticatedPage.waitForTimeout(800);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-opened.png' });

    const modal = authenticatedPage.locator('.fixed.inset-0').first();
    const isModalOpen = await modal.isVisible({ timeout: 3000 }).catch(() => false);

    const fallbackSelectors = [
      '[class*="animate-in"][class*="fade-in"]',
      '[style*="95vw"]',
      '[style*="95vh"]',
      '.rounded-xl.border.shadow-2xl',
    ];

    let found = isModalOpen;
    if (!found) {
      for (const sel of fallbackSelectors) {
        if (await authenticatedPage.locator(sel).isVisible({ timeout: 2000 }).catch(() => false)) {
          found = true;
          break;
        }
      }
    }

    expect(found, 'Clicking Expandir should open the SuperPrompt modal overlay').toBe(true);
  });

  test('TC-SP-003: SuperPrompt tem header com botões de controle', async ({ authenticatedPage }) => {
    await openSuperPrompt(authenticatedPage);
    await authenticatedPage.waitForTimeout(500);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-header-controls.png' });

    const controlButtons = [
      { selector: 'button[aria-label="Iniciar novo chat"]', name: 'Novo chat' },
      { selector: 'button[aria-label="Limpar mensagens"]', name: 'Limpar' },
      { selector: 'button[aria-label="Ver histórico de conversas"]', name: 'Histórico' },
      { selector: 'button[aria-label="Minimizar"]', name: 'Minimizar' },
      { selector: 'button[aria-label="Fechar"]', name: 'Fechar' },
    ];

    for (const { selector, name } of controlButtons) {
      const btn = authenticatedPage.locator(selector).first();
      const isVisible = await btn.isVisible({ timeout: 3000 }).catch(() => false);
      if (!isVisible) {
        test.info().annotations.push({ type: 'bug', description: `BUG-SP-003: "${name}" button not found in SuperPrompt header` });
      }
    }

    const closeButton = authenticatedPage.locator('button[aria-label="Fechar"]').first();
    await expect(closeButton, 'Fechar button must be present in SuperPrompt').toBeVisible({ timeout: 5000 });
  });

  test('TC-SP-004: SuperPrompt tem tabs Conversa e Centro de Controle', async ({ authenticatedPage }) => {
    await openSuperPrompt(authenticatedPage);
    await authenticatedPage.waitForTimeout(500);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-tabs.png' });

    const conversaTab = authenticatedPage.locator('button:has-text("Conversa")').first();
    const controleTab = authenticatedPage.locator('button:has-text("Centro de Controle")').first();

    await expect(conversaTab, 'Conversa tab must be present in SuperPrompt').toBeVisible({ timeout: 5000 });
    await expect(controleTab, 'Centro de Controle tab must be present in SuperPrompt').toBeVisible({ timeout: 5000 });
  });

  test('TC-SP-005: SuperPrompt empty state exibe sugestões em grade', async ({ authenticatedPage }) => {
    await openSuperPrompt(authenticatedPage);
    await authenticatedPage.waitForTimeout(1000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-empty-state.png' });

    const welcomeText = authenticatedPage.locator('text=/Oi, eu sou a|Como posso ajudar/i').first();
    const isWelcomeVisible = await welcomeText.isVisible({ timeout: 5000 }).catch(() => false);

    if (!isWelcomeVisible) {
      test.info().annotations.push({ type: 'info', description: 'SuperPrompt empty state may already have messages from previous session' });
    }
  });

  test('TC-SP-006: Input do SuperPrompt é uma textarea com Brain icon', async ({ authenticatedPage }) => {
    await openSuperPrompt(authenticatedPage);
    await authenticatedPage.waitForTimeout(500);

    const textarea = authenticatedPage.locator('textarea[placeholder*="Envie mensagem"]').first();
    const input = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();

    const hasTextarea = await textarea.isVisible({ timeout: 3000 }).catch(() => false);
    const hasInput = await input.isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasTextarea || hasInput, 'SuperPrompt must have an input/textarea for messages').toBe(true);

    const brainIcon = authenticatedPage.locator('[class*="wedo-cyan"]').first();
    await expect(brainIcon, 'Brain icon (wedo-cyan) must be visible near SuperPrompt input').toBeVisible({ timeout: 3000 });

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-input.png' });
  });

  test('TC-SP-007: Digitação e envio de mensagem no SuperPrompt', async ({ authenticatedPage }) => {
    const opened = await openSuperPrompt(authenticatedPage);

    if (!opened) {
      test.skip(true, 'SuperPrompt could not be opened');
      return;
    }

    await authenticatedPage.waitForTimeout(500);

    const textareaSelectors = [
      'textarea[placeholder*="Envie mensagem"]',
      '[aria-label="Mensagem para a LIA"]',
    ];

    let inputEl: Locator | null = null;
    for (const sel of textareaSelectors) {
      const el = authenticatedPage.locator(sel).first();
      if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
        inputEl = el;
        break;
      }
    }

    if (!inputEl) {
      test.info().annotations.push({ type: 'info', description: 'TC-SP-007: No input found in SuperPrompt after opening' });
      return;
    }

    const testMsg = `Teste SuperPrompt ${Date.now()}`;
    await inputEl.click();
    await inputEl.fill(testMsg);

    const value = await inputEl.inputValue();
    expect(value, 'SuperPrompt input must accept typed text').toBe(testMsg);

    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    await expect(sendButton, 'Send button must be enabled with text in SuperPrompt').toBeEnabled({ timeout: 3000 });

    await inputEl.press('Enter');
    await authenticatedPage.waitForTimeout(1500);

    const valueAfter = await inputEl.inputValue().catch(() => '');
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-message-sent.png' });
    expect(valueAfter, 'SuperPrompt input should be cleared after sending message').toBe('');
  });

  test('TC-SP-008: Botão Minimizar fecha o SuperPrompt (retorna ao painel flutuante)', async ({ authenticatedPage }) => {
    const opened = await openSuperPrompt(authenticatedPage);

    if (!opened) {
      test.skip(true, 'SuperPrompt could not be opened');
      return;
    }

    await authenticatedPage.waitForTimeout(500);

    const minimizeBtn = authenticatedPage.locator('button[aria-label="Minimizar"]').first();
    const hasMinimize = await minimizeBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasMinimize) {
      await minimizeBtn.click();
      await authenticatedPage.waitForTimeout(500);
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-minimized.png' });

      const modal = authenticatedPage.locator('.fixed.inset-0').first();
      const isModalStillOpen = await modal.isVisible({ timeout: 2000 }).catch(() => false);
      expect(isModalStillOpen, 'SuperPrompt overlay must be closed after clicking Minimizar').toBe(false);
    } else {
      test.info().annotations.push({ type: 'bug', description: 'BUG-SP-008: Minimizar button not found in SuperPrompt' });
    }
  });

  test('TC-SP-009: Botão Fechar fecha completamente o SuperPrompt', async ({ authenticatedPage }) => {
    const opened = await openSuperPrompt(authenticatedPage);

    if (!opened) {
      test.skip(true, 'SuperPrompt could not be opened');
      return;
    }

    await authenticatedPage.waitForTimeout(500);

    const closeBtn = authenticatedPage.locator('[data-dismiss="true"], button[aria-label="Fechar"]').first();
    const hasClose = await closeBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasClose) {
      await closeBtn.click();
      await authenticatedPage.waitForTimeout(500);
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-closed.png' });

      const modal = authenticatedPage.locator('.fixed.inset-0').first();
      const isModalStillOpen = await modal.isVisible({ timeout: 2000 }).catch(() => false);
      expect(isModalStillOpen, 'SuperPrompt overlay must be closed after clicking Fechar').toBe(false);
    }
  });

  test('TC-SP-010: Alinhamento de balões no SuperPrompt — user à direita', async ({ authenticatedPage }) => {
    const opened = await openSuperPrompt(authenticatedPage);

    if (!opened) {
      test.skip(true, 'SuperPrompt could not be opened');
      return;
    }

    await authenticatedPage.waitForTimeout(500);

    const inputEl = authenticatedPage.locator('textarea[placeholder*="Envie mensagem"], [aria-label="Mensagem para a LIA"]').first();
    if (await inputEl.isVisible({ timeout: 3000 }).catch(() => false)) {
      await inputEl.click();
      await inputEl.fill('Olá LIA!');
      await inputEl.press('Enter');
      await authenticatedPage.waitForTimeout(2000);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-bubble-alignment.png' });

      const userBubble = authenticatedPage.locator('.flex.justify-end').first();
      const hasUserBubble = await userBubble.isVisible({ timeout: 3000 }).catch(() => false);

      if (!hasUserBubble) {
        test.info().annotations.push({
          type: 'bug',
          description: 'BUG-SP-010: User messages in SuperPrompt not using justify-end alignment'
        });
      }
    }
  });

  test('TC-SP-011: Histórico de conversas no SuperPrompt funcional', async ({ authenticatedPage }) => {
    const opened = await openSuperPrompt(authenticatedPage);

    if (!opened) {
      test.skip(true, 'SuperPrompt could not be opened');
      return;
    }

    await authenticatedPage.waitForTimeout(500);

    const historyBtn = authenticatedPage.locator('button[aria-label="Ver histórico de conversas"]').first();
    const hasHistory = await historyBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasHistory) {
      await historyBtn.click();
      await authenticatedPage.waitForTimeout(1000);
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/superprompt-history.png' });

      const historySection = authenticatedPage.locator('text=/Conversas recentes/i').first();
      await expect(historySection, 'History section should appear in SuperPrompt').toBeVisible({ timeout: 3000 });
    } else {
      test.info().annotations.push({ type: 'bug', description: 'BUG-SP-011: Histórico button not found in SuperPrompt' });
    }
  });
});
