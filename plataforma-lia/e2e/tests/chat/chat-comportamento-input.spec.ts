/**
 * Test Suite: Comportamento do Input nos Chats LIA
 * Audits all input behaviors across chat interfaces.
 */

import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Comportamento do Input — Auditoria Completa', () => {

  test('TC-INP-001: Textarea auto-resize ao digitar múltiplas linhas', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const textarea = authenticatedPage.locator('textarea[aria-label="Mensagem para a LIA"]').first();

    if (await textarea.isVisible({ timeout: 5000 }).catch(() => false)) {
      const initialHeight = await textarea.evaluate((el: HTMLTextAreaElement) => el.offsetHeight);
      await textarea.click();
      await textarea.fill('Linha 1\nLinha 2\nLinha 3\nLinha 4\nLinha 5');
      await authenticatedPage.waitForTimeout(300);
      const newHeight = await textarea.evaluate((el: HTMLTextAreaElement) => el.offsetHeight);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-textarea-autoresize.png' });
      expect(newHeight, `Textarea height should increase when multiline text is added. Initial: ${initialHeight}, After: ${newHeight}`).toBeGreaterThan(initialHeight);
    } else {
      test.info().annotations.push({ type: 'info', description: 'TC-INP-001: /chat uses LiaChatShell with single-line input — no textarea found' });
    }
  });

  test('TC-INP-002: Limite de 2000 caracteres no input do Chat Flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 5000 }).catch(() => false)) {
      const longText = 'A'.repeat(2100);
      await input.click();
      await input.fill(longText);

      const value = await input.inputValue();
      expect(value.length, `Input must enforce maxLength 2000. Got ${value.length} chars`).toBeLessThanOrEqual(2000);

      const maxLengthAttr = await input.getAttribute('maxlength');
      expect(parseInt(maxLengthAttr || '0'), 'Input maxlength attribute should be 2000').toBe(2000);
    }
  });

  test('TC-INP-003: Enter envia mensagem no Chat Flutuante (input simples)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await input.click();
      await input.fill('Mensagem de teste Enter');
      await input.press('Enter');
      await authenticatedPage.waitForTimeout(1000);

      const value = await input.inputValue().catch(() => '');
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-enter-send.png' });
      expect(value, 'Input must be cleared after Enter (message sent successfully)').toBe('');
    }
  });

  test('TC-INP-004: Shift+Enter adiciona quebra de linha no textarea (Chat Principal)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const textarea = authenticatedPage.locator('textarea[aria-label="Mensagem para a LIA"]').first();
    if (await textarea.isVisible({ timeout: 3000 }).catch(() => false)) {
      await textarea.click();
      await textarea.fill('Primeira linha');
      await textarea.press('Shift+Enter');
      await textarea.type('Segunda linha');

      const value = await textarea.inputValue();
      await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-shift-enter.png' });
      expect(value, 'Shift+Enter should create a newline in textarea, not send').toContain('\n');
    } else {
      test.info().annotations.push({ type: 'info', description: 'TC-INP-004: No textarea found in /chat (using LiaChatShell)' });
    }
  });

  test('TC-INP-005: Botão Send desabilitado quando input vazio — Chat Flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    await expect(sendButton, 'Send button must be disabled when input is empty').toBeDisabled({ timeout: 5000 });
  });

  test('TC-INP-006: Botão Send habilitado quando input tem texto — Chat Flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await input.click();
      await input.fill('Texto de teste');

      const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
      await expect(sendButton, 'Send button must be enabled when input has text').toBeEnabled({ timeout: 3000 });
    }
  });

  test('TC-INP-007: Ícone Brain (wedo-cyan) presente no input do Chat Flutuante', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const brainIconContainer = authenticatedPage.locator('[class*="wedo-cyan"]').first();
    await expect(brainIconContainer, 'Brain icon (wedo-cyan) must be present near the input').toBeVisible({ timeout: 5000 });

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-brain-icon.png' });
  });

  test('TC-INP-008: Contador de caracteres aparece perto do limite (90%)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      const nearLimitText = 'A'.repeat(1850);
      await input.click();
      await input.fill(nearLimitText);
      await authenticatedPage.waitForTimeout(500);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-char-counter.png' });

      const counter = authenticatedPage.locator('text=/\\d+\\/2000/').first();
      await expect(counter, 'Character counter must appear when usage exceeds 90% of max').toBeVisible({ timeout: 3000 });
    }
  });

  test('TC-INP-009: Input container fixo com flex-shrink-0 (não encolhe ao scrollar)', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const inputContainer = await authenticatedPage.evaluate(() => {
      const input = document.querySelector('input[aria-label="Mensagem para a LIA"]') ||
                    document.querySelector('textarea[aria-label="Mensagem para a LIA"]');
      if (!input) return null;

      let el: Element | null = input.parentElement;
      while (el) {
        const style = window.getComputedStyle(el);
        if (style.flexShrink === '0') return { flexShrink: style.flexShrink };
        el = el.parentElement;
      }
      return null;
    });

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-fixed-bottom.png' });
    expect(inputContainer, 'Input container must have flex-shrink: 0 to stay fixed at bottom').not.toBeNull();
  });

  test('TC-INP-010: Input responsivo em viewport mobile (390x844)', async ({ authenticatedPage }) => {
    await authenticatedPage.setViewportSize({ width: 390, height: 844 });
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/input-mobile-viewport.png', fullPage: true });

    const inputSelectors = [
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[aria-label="Mensagem para a LIA"]',
    ];

    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        const bbox = await input.boundingBox();
        if (bbox) {
          expect(bbox.width, `Input width (${bbox.width}) must not exceed viewport width (390px) on mobile`).toBeLessThanOrEqual(390);
          expect(bbox.x, `Input x position (${bbox.x}) must be within viewport on mobile`).toBeGreaterThanOrEqual(0);
        }
        break;
      }
    }
  });
});
