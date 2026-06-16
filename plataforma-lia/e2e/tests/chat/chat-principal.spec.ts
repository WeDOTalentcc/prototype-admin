/**
 * Test Suite: Chat Principal (/chat)
 * Audits usability of the main full-page chat interface.
 */

import { test, expect } from '../../fixtures/auth.fixture';

const CHAT_URL = '/chat';

test.describe('Chat Principal (/chat) — Auditoria de Usabilidade', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto(CHAT_URL);
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);
  });

  test('TC-CP-001: Renderização da página /chat sem erros', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-empty-state.png', fullPage: true });

    const errorMessages = authenticatedPage.locator('text=/^(Error|500 Internal|404 Not Found)$/');
    await expect(errorMessages).toHaveCount(0);
  });

  test('TC-CP-002: Empty state exibe mensagem de boas-vindas da LIA', async ({ authenticatedPage }) => {
    const welcomeText = authenticatedPage.locator('text=/Oi, eu sou a|Como posso ajudar/i').first();
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-welcome.png', fullPage: true });

    const isVisible = await welcomeText.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      test.info().annotations.push({ type: 'bug', description: 'BUG-CP-002: Empty state welcome message not found in /chat' });
    }
    expect(isVisible, 'Empty state should display welcome message').toBe(true);
  });

  test('TC-CP-003: Input existe na página /chat', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[placeholder*="Envie mensagem"]',
      'input[placeholder*="Envie mensagem"]',
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        inputFound = true;
        break;
      }
    }

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-input.png' });
    expect(inputFound, 'Input element must be present in /chat').toBe(true);
  });

  test('TC-CP-004: Digitação no input não trava — resposta em menos de 3s para 60 chars', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[placeholder*="Envie mensagem"]',
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        await input.click();
        const typingStart = Date.now();
        await input.type('Teste de digitação para verificar se o input trava — 1234567890', { delay: 20 });
        const typingDuration = Date.now() - typingStart;

        const value = await input.inputValue();
        await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-input-typing.png' });

        expect(value.length, 'Input must accept typed text').toBeGreaterThan(0);
        expect(typingDuration, `Typing 60 chars took ${typingDuration}ms — exceeds 3000ms threshold (BUG: input freezing)`).toBeLessThan(3000);
        inputFound = true;
        break;
      }
    }

    expect(inputFound, 'Input not found in /chat').toBe(true);
  });

  test('TC-CP-005: Envio de mensagem via tecla Enter limpa o input', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[placeholder*="Envie mensagem"]',
    ];

    let sent = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        const testMessage = `Olá LIA — teste Enter ${Date.now()}`;
        await input.click();
        await input.fill(testMessage);
        const valueBefore = await input.inputValue();
        expect(valueBefore).toBe(testMessage);

        await input.press('Enter');
        await authenticatedPage.waitForTimeout(1500);

        const valueAfter = await input.inputValue().catch(() => '');
        await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-enter-sent.png' });
        expect(valueAfter, 'Input should be cleared after Enter (message sent)').toBe('');
        sent = true;
        break;
      }
    }
    expect(sent, 'Could not find input to test Enter sending').toBe(true);
  });

  test('TC-CP-006: Botão Send habilitado com texto e desabilitado sem texto', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[placeholder*="Envie mensagem"]',
    ];

    let tested = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
        const hasSendButton = await sendButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (hasSendButton) {
          await expect(sendButton, 'Send button should be disabled when input is empty').toBeDisabled();

          await input.click();
          await input.fill('Teste');
          await expect(sendButton, 'Send button should be enabled when input has text').toBeEnabled();
        }

        await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-send-button.png' });
        tested = true;
        break;
      }
    }
    expect(tested, 'Could not find input to test Send button state').toBe(true);
  });

  test('TC-CP-007: Botões de controle presentes — limpar, fechar, novo chat', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-control-buttons.png' });

    const clearButton = authenticatedPage.locator('button[aria-label="Limpar mensagens"]').first();
    const newChatButton = authenticatedPage.locator('button[aria-label="Iniciar novo chat"]').first();
    const historyButton = authenticatedPage.locator('button[aria-label="Ver histórico de conversas"]').first();

    const hasClear = await clearButton.isVisible({ timeout: 3000 }).catch(() => false);
    const hasNewChat = await newChatButton.isVisible({ timeout: 3000 }).catch(() => false);
    const hasHistory = await historyButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (!hasClear) {
      test.info().annotations.push({ type: 'bug', description: 'BUG-CP-007a: Limpar button missing in /chat — present in Flutuante (BUG-004 confirmed)' });
    }
    if (!hasNewChat) {
      test.info().annotations.push({ type: 'bug', description: 'BUG-CP-007b: Novo Chat button missing in /chat' });
    }
    if (!hasHistory) {
      test.info().annotations.push({ type: 'bug', description: 'BUG-CP-007c: Histórico button missing in /chat' });
    }

    const anyControlFound = hasClear || hasNewChat || hasHistory;
    expect(anyControlFound, 'At least one chat control button (clear/new/history) must be present').toBe(true);
  });

  test('TC-CP-007b: Envio de mensagem via clique no botão Send', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
    ];

    let tested = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
        const hasSendButton = await sendButton.isVisible({ timeout: 3000 }).catch(() => false);

        if (!hasSendButton) {
          test.info().annotations.push({ type: 'info', description: 'TC-CP-007b: No Send button with aria-label found in /chat — skipping button click test' });
          tested = true;
          break;
        }

        const testMessage = `Teste Send button ${Date.now()}`;
        await input.click();
        await input.fill(testMessage);

        await expect(sendButton, 'Send button should be enabled with text in input').toBeEnabled();

        await sendButton.click();
        await authenticatedPage.waitForTimeout(1500);

        const valueAfter = await input.inputValue().catch(() => '');
        await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-send-button-click.png' });
        expect(valueAfter, 'Input should be cleared after clicking Send button').toBe('');
        tested = true;
        break;
      }
    }
    expect(tested, 'Could not find input to test Send button click').toBe(true);
  });

  test('TC-CP-008: Auto-scroll funciona após envio de mensagens', async ({ authenticatedPage }) => {
    const inputSelectors = [
      'textarea[aria-label="Mensagem para a LIA"]',
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[placeholder*="Envie mensagem"]',
    ];

    let tested = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        for (let i = 0; i < 2; i++) {
          await input.click();
          await input.fill(`Mensagem ${i + 1} para testar auto-scroll`);
          await input.press('Enter');
          await authenticatedPage.waitForTimeout(1500);
        }

        await authenticatedPage.waitForTimeout(1000);
        await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-principal-autoscroll.png' });

        const scrollInfo = await authenticatedPage.evaluate(() => {
          const divs = Array.from(document.querySelectorAll('div'));
          const scrollable = divs.find(d => d.scrollHeight > d.clientHeight && d.clientHeight > 100);
          if (!scrollable) return null;
          return {
            scrollTop: scrollable.scrollTop,
            scrollHeight: scrollable.scrollHeight,
            clientHeight: scrollable.clientHeight,
            isAtBottom: scrollable.scrollHeight - scrollable.scrollTop <= scrollable.clientHeight + 150,
          };
        });

        if (scrollInfo) {
          expect(scrollInfo.isAtBottom, `Auto-scroll should keep view at bottom after messages. scrollTop=${scrollInfo.scrollTop}, scrollHeight=${scrollInfo.scrollHeight}`).toBe(true);
        }

        tested = true;
        break;
      }
    }
    expect(tested, 'Could not find input to test auto-scroll').toBe(true);
  });
});
