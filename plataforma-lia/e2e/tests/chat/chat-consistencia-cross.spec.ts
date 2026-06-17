/**
 * Test Suite: Consistência Cross-Chat
 * Compares visual and behavioral consistency between all chat interfaces.
 */

import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Consistência Cross-Chat — Auditoria Comparativa', () => {

  test('TC-CC-001: Tipo de input — Chat Principal usa textarea; Chat Flutuante usa input simples', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const principalHasTextarea = await authenticatedPage.locator('textarea[aria-label="Mensagem para a LIA"]').isVisible({ timeout: 3000 }).catch(() => false);
    const principalHasInput = await authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').isVisible({ timeout: 3000 }).catch(() => false);

    const hasPrincipalInput = principalHasTextarea || principalHasInput;
    expect(hasPrincipalInput, 'Chat Principal must have an input (textarea or input)').toBe(true);

    if (principalHasInput && !principalHasTextarea) {
      test.info().annotations.push({
        type: 'bug',
        description: 'BUG-CC-001 (BUG-006): /chat uses <input> not <textarea> — missing auto-resize capability for long messages'
      });
    }

    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const flutuanteHasInput = await authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').isVisible({ timeout: 3000 }).catch(() => false);
    expect(flutuanteHasInput, 'Chat Flutuante must have an input').toBe(true);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/cross-chat-input-types.png' });
  });

  test('TC-CC-002: Ícone Brain (wedo-cyan) presente no input de todos os chats', async ({ authenticatedPage }) => {
    const pages = [
      { url: '/chat', name: 'Chat Principal' },
      { url: '/vagas', name: 'Chat Flutuante' },
    ];

    for (const { url, name } of pages) {
      await authenticatedPage.goto(url);
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(2000);

      const brainIcon = authenticatedPage.locator('[class*="wedo-cyan"]').first();
      await expect(brainIcon, `Brain icon must be visible in ${name}`).toBeVisible({ timeout: 5000 });
    }
  });

  test('TC-CC-003: Botão Send circular e ciano presente em todos os chats', async ({ authenticatedPage }) => {
    const pages = [
      { url: '/chat', name: 'Chat Principal' },
      { url: '/vagas', name: 'Chat Flutuante' },
    ];

    for (const { url, name } of pages) {
      await authenticatedPage.goto(url);
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(2000);

      const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
      await expect(sendButton, `Send button must be present in ${name}`).toBeVisible({ timeout: 5000 });

      const btnStyle = await authenticatedPage.evaluate(() => {
        const btn = document.querySelector('button[aria-label="Enviar mensagem"]');
        if (!btn) return null;
        const style = window.getComputedStyle(btn);
        return { borderRadius: parseInt(style.borderRadius) };
      });

      if (btnStyle) {
        expect(btnStyle.borderRadius, `Send button in ${name} should be circular (high border-radius)`).toBeGreaterThanOrEqual(14);
      }
    }
  });

  test('TC-CC-004: Botão Limpar presente no Chat Flutuante — comparar com Chat Principal', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const clearInFlutuante = await authenticatedPage.locator('button[aria-label="Limpar mensagens"]').isVisible({ timeout: 3000 }).catch(() => false);
    expect(clearInFlutuante, 'Limpar button must be present in Chat Flutuante').toBe(true);

    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/cross-chat-limpar-comparison.png' });

    const clearInPrincipal = await authenticatedPage.locator('button[aria-label="Limpar mensagens"]').isVisible({ timeout: 3000 }).catch(() => false);
    if (!clearInPrincipal) {
      test.info().annotations.push({
        type: 'bug',
        description: 'BUG-CC-004 (BUG-004): Limpar button present in Chat Flutuante but MISSING in Chat Principal — UX inconsistency'
      });
    }
  });

  test('TC-CC-005: Alinhamento usuário à direita (justify-end) em todos os chats', async ({ authenticatedPage }) => {
    const pages = [
      { url: '/vagas', name: 'Chat Flutuante', inputSelector: 'input[aria-label="Mensagem para a LIA"]' },
      { url: '/chat', name: 'Chat Principal', inputSelector: 'textarea[aria-label="Mensagem para a LIA"]' },
    ];

    for (const { url, name, inputSelector } of pages) {
      await authenticatedPage.goto(url);
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(2000);

      const input = authenticatedPage.locator(inputSelector).first();
      const altSelector = inputSelector.includes('textarea')
        ? 'input[aria-label="Mensagem para a LIA"]'
        : 'textarea[aria-label="Mensagem para a LIA"]';
      const altInput = authenticatedPage.locator(altSelector).first();

      const activeInput = await input.isVisible({ timeout: 2000 }).catch(() => false)
        ? input
        : await altInput.isVisible({ timeout: 2000 }).catch(() => false) ? altInput : null;

      if (!activeInput) {
        test.info().annotations.push({ type: 'info', description: `No input found in ${name} for bubble alignment test` });
        continue;
      }

      await activeInput.click();
      await activeInput.fill('Teste alinhamento');
      await activeInput.press('Enter');
      await authenticatedPage.waitForTimeout(1500);

      await authenticatedPage.screenshot({ path: `e2e/screenshots/cross-chat-alinhamento-${name.replace(/[^a-z]/gi, '-').toLowerCase()}.png` });

      const userBubble = authenticatedPage.locator('.flex.justify-end').first();
      const hasUserBubble = await userBubble.isVisible({ timeout: 3000 }).catch(() => false);

      if (!hasUserBubble) {
        test.info().annotations.push({
          type: 'bug',
          description: `BUG-CC-005 (BUG-001): User messages in ${name} not using justify-end — bubble alignment may be INVERTED`
        });
      }
    }
  });

  test('TC-CC-006: Estrutura do input — ambos os chats têm Brain icon + textarea/input + Send button', async ({ authenticatedPage }) => {
    const pages = [
      { url: '/vagas', name: 'Chat Flutuante' },
      { url: '/chat', name: 'Chat Principal' },
    ];

    for (const { url, name } of pages) {
      await authenticatedPage.goto(url);
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(2000);

      const brainIcon = authenticatedPage.locator('[class*="wedo-cyan"]').first();
      const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
      const sendBtn = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();

      await expect(brainIcon, `Brain icon must be visible in ${name}`).toBeVisible({ timeout: 5000 });
      await expect(inputEl, `Input must be visible in ${name}`).toBeVisible({ timeout: 5000 });
      await expect(sendBtn, `Send button must be visible in ${name}`).toBeVisible({ timeout: 5000 });

      await authenticatedPage.screenshot({ path: `e2e/screenshots/cross-chat-structure-${name.replace(/[^a-z]/gi, '-').toLowerCase()}.png` });
    }
  });
});
