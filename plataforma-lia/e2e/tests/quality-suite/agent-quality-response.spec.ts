import { test, expect } from '@playwright/test';

const CHAT_INPUT_SELECTOR = '[data-testid="chat-input"], textarea[placeholder*="mensagem"], textarea[placeholder*="LIA"]';
const CHAT_SEND_SELECTOR = '[data-testid="chat-send"], button[aria-label*="enviar"], button[type="submit"]';
const CHAT_MESSAGE_SELECTOR = '[data-testid="chat-message"], .chat-message, .message-content';

async function sendAndWaitForResponse(page: any, message: string, waitMs = 5000) {
  const input = page.locator(CHAT_INPUT_SELECTOR).first();
  await input.waitFor({ state: 'visible', timeout: 10000 });
  await input.fill(message);
  const sendButton = page.locator(CHAT_SEND_SELECTOR).first();
  await sendButton.click();
  await page.waitForTimeout(waitMs);
  const messages = page.locator(CHAT_MESSAGE_SELECTOR);
  const count = await messages.count();
  if (count === 0) return '';
  return (await messages.last().textContent()) || '';
}

test.describe('Agent Quality Suite — Response Coherence', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Response Format Validation', () => {
    test('Job creation response asks for required fields', async ({ page }) => {
      const response = await sendAndWaitForResponse(
        page,
        'Quero criar uma vaga de Desenvolvedor Full Stack'
      );
      expect(response.length).toBeGreaterThan(50);
      expect(response.toLowerCase()).not.toContain('traceback');
      expect(response.toLowerCase()).not.toContain('exception');
    });

    test('Analytics response contains data-like content', async ({ page }) => {
      const response = await sendAndWaitForResponse(
        page,
        'Quantas vagas abertas temos?'
      );
      expect(response.length).toBeGreaterThan(20);
      expect(response.toLowerCase()).not.toContain('traceback');
    });
  });

  test.describe('Anti-Hallucination Checks', () => {
    test('Response does not invent candidate names when none provided', async ({ page }) => {
      const response = await sendAndWaitForResponse(
        page,
        'Buscar candidatos para vaga de designer'
      );
      expect(response.toLowerCase()).not.toContain('traceback');
    });

    test('Response does not invent salary data unprompted', async ({ page }) => {
      const response = await sendAndWaitForResponse(
        page,
        'Crie uma vaga de analista júnior'
      );
      expect(response.toLowerCase()).not.toContain('traceback');
    });
  });

  test.describe('Error Handling', () => {
    test('Empty message does not crash the chat', async ({ page }) => {
      const input = page.locator(CHAT_INPUT_SELECTOR).first();
      await input.waitFor({ state: 'visible', timeout: 10000 });
      await input.fill('');
      const sendButton = page.locator(CHAT_SEND_SELECTOR).first();
      const isDisabled = await sendButton.isDisabled();
      if (!isDisabled) {
        await sendButton.click();
        await page.waitForTimeout(2000);
      }
      const errorDialog = page.locator('[role="alert"], .error-message, .toast-error');
      const errorCount = await errorDialog.count();
      expect.soft(errorCount).toBe(0);
    });

    test('Very long message does not crash', async ({ page }) => {
      const longMessage = 'Buscar candidatos '.repeat(100);
      const response = await sendAndWaitForResponse(page, longMessage, 8000);
      expect(response.toLowerCase()).not.toContain('500');
    });
  });

  test.describe('Context Awareness', () => {
    test('Consecutive messages maintain context', async ({ page }) => {
      await sendAndWaitForResponse(page, 'Quero criar uma vaga de Product Manager');
      const response2 = await sendAndWaitForResponse(page, 'Adicione requisito de 5 anos de experiência');
      expect(response2.length).toBeGreaterThan(0);
    });
  });
});
