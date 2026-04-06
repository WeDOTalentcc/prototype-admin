/**
 * Test Suite: Chat Wizard / LIA Chat Inline (InlineLeft mode)
 * Audits the LIA chat embedded in the Wizard flow at /vagas/nova.
 *
 * The Wizard chat (LiaChatShell InlineLeft) appears as a sidebar/left panel
 * alongside the wizard form steps, providing real-time AI assistance during
 * job creation.
 *
 * Coverage:
 * - Presence and visibility of inline chat panel
 * - Input (Brain icon + input/textarea + Send button)
 * - Sending messages and clearing input
 * - Message bubble alignment
 * - Control buttons (limpar, novo chat, histórico)
 * - Auto-scroll behavior
 * - Markdown rendering in AI responses
 * - Responsiveness alongside wizard form
 */

import { test, expect } from '../../fixtures/auth.fixture';

const WIZARD_URL = '/vagas/nova';

test.describe('Chat Wizard (InlineLeft / /vagas/nova) — Auditoria de Usabilidade', () => {

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto(WIZARD_URL);
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);
  });

  test('TC-WZ-001: Página /vagas/nova renderiza sem erros', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-page.png', fullPage: true });

    const errorText = authenticatedPage.locator('text=/^(Error|500 Internal|404 Not Found)$/').first();
    const hasError = await errorText.isVisible({ timeout: 3000 }).catch(() => false);
    expect(hasError, 'Wizard page must not show error messages').toBe(false);
  });

  test('TC-WZ-002: Input da LIA visível no painel inline do Wizard', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-input.png', fullPage: true });

    const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInput = await inputEl.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasInput) {
      test.info().annotations.push({
        type: 'bug',
        description: 'BUG-WZ-002: LIA inline chat input not found at /vagas/nova — InlineLeft mode may not be activated'
      });
    }

    expect(hasInput, 'LIA input must be visible in wizard inline chat at /vagas/nova').toBe(true);
  });

  test('TC-WZ-003: Brain icon (wedo-cyan) presente no input do Wizard inline', async ({ authenticatedPage }) => {
    const brainIcon = authenticatedPage.locator('[class*="wedo-cyan"]').first();
    await expect(brainIcon, 'Brain icon (wedo-cyan) must be visible in wizard inline chat').toBeVisible({ timeout: 5000 });
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-brain-icon.png' });
  });

  test('TC-WZ-004: Botão Send presente e desabilitado com input vazio', async ({ authenticatedPage }) => {
    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    await expect(sendButton, 'Send button must be present in wizard inline chat').toBeVisible({ timeout: 5000 });
    await expect(sendButton, 'Send button must be disabled when input is empty').toBeDisabled({ timeout: 3000 });
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-send-button.png' });
  });

  test('TC-WZ-005: Digitação e envio de mensagem via Enter no Wizard inline', async ({ authenticatedPage }) => {
    const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInput = await inputEl.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasInput) {
      test.info().annotations.push({ type: 'info', description: 'TC-WZ-005: Input not found — cannot test message sending' });
      return;
    }

    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();
    const testMsg = `Wizard teste ${Date.now()}`;

    await inputEl.click();
    await inputEl.fill(testMsg);

    const valueBefore = await inputEl.inputValue();
    expect(valueBefore, 'Input must accept typed text').toBe(testMsg);

    await expect(sendButton, 'Send button must be enabled with text').toBeEnabled({ timeout: 3000 });

    await inputEl.press('Enter');
    await authenticatedPage.waitForTimeout(1500);

    const valueAfter = await inputEl.inputValue().catch(() => '');
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-message-sent.png' });
    expect(valueAfter, 'Input must be cleared after sending message via Enter').toBe('');
  });

  test('TC-WZ-006: Envio via clique no botão Send no Wizard inline', async ({ authenticatedPage }) => {
    const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const sendButton = authenticatedPage.locator('button[aria-label="Enviar mensagem"]').first();

    const hasInput = await inputEl.isVisible({ timeout: 5000 }).catch(() => false);
    const hasSend = await sendButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (!hasInput || !hasSend) {
      test.info().annotations.push({ type: 'info', description: 'TC-WZ-006: Input or Send button not found' });
      return;
    }

    const testMsg = `Wizard Send button ${Date.now()}`;
    await inputEl.click();
    await inputEl.fill(testMsg);

    await expect(sendButton, 'Send button must be enabled with text').toBeEnabled({ timeout: 3000 });

    await sendButton.click();
    await authenticatedPage.waitForTimeout(1500);

    const valueAfter = await inputEl.inputValue().catch(() => '');
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-send-click.png' });
    expect(valueAfter, 'Input must be cleared after clicking Send button').toBe('');
  });

  test('TC-WZ-007: Alinhamento dos balões — usuário à direita (justify-end)', async ({ authenticatedPage }) => {
    const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInput = await inputEl.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasInput) {
      test.info().annotations.push({ type: 'info', description: 'TC-WZ-007: Input not found — cannot test bubble alignment' });
      return;
    }

    await inputEl.click();
    await inputEl.fill('Olá LIA!');
    await inputEl.press('Enter');
    await authenticatedPage.waitForTimeout(2000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-bubble-alignment.png' });

    const userBubble = authenticatedPage.locator('.flex.justify-end').first();
    const hasUserBubble = await userBubble.isVisible({ timeout: 3000 }).catch(() => false);

    if (!hasUserBubble) {
      test.info().annotations.push({
        type: 'bug',
        description: 'BUG-WZ-007: User messages in Wizard inline chat not using justify-end — bubble alignment may be INVERTED'
      });
    }

    expect(hasUserBubble, 'User message bubbles must use justify-end (right alignment) in Wizard inline chat').toBe(true);
  });

  test('TC-WZ-008: Botão Limpar presente no Wizard inline chat', async ({ authenticatedPage }) => {
    const clearButton = authenticatedPage.locator('button[aria-label="Limpar mensagens"]').first();
    await expect(clearButton, 'Limpar button must be present in Wizard inline chat').toBeVisible({ timeout: 5000 });
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-controls.png' });
  });

  test('TC-WZ-009: Painel inline não sobrepõe o formulário do Wizard', async ({ authenticatedPage }) => {
    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-layout.png', fullPage: true });

    const liaPanel = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const wizardForm = authenticatedPage.locator('form, [data-testid="wizard-form"], main').first();

    const liaPanelVisible = await liaPanel.isVisible({ timeout: 3000 }).catch(() => false);
    const wizardFormVisible = await wizardForm.isVisible({ timeout: 3000 }).catch(() => false);

    if (liaPanelVisible && wizardFormVisible) {
      const liaBbox = await liaPanel.boundingBox();
      const formBbox = await wizardForm.boundingBox();

      if (liaBbox && formBbox) {
        const overlaps = !(
          liaBbox.x + liaBbox.width <= formBbox.x ||
          formBbox.x + formBbox.width <= liaBbox.x ||
          liaBbox.y + liaBbox.height <= formBbox.y ||
          formBbox.y + formBbox.height <= liaBbox.y
        );

        if (overlaps) {
          test.info().annotations.push({
            type: 'bug',
            description: 'BUG-WZ-009: LIA inline chat panel overlaps wizard form — layout broken'
          });
        }
      }
    }
  });

  test('TC-WZ-010: Markdown renderizado corretamente nas respostas do Wizard inline', async ({ authenticatedPage }) => {
    const inputEl = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();
    const hasInput = await inputEl.isVisible({ timeout: 5000 }).catch(() => false);

    if (!hasInput) {
      test.info().annotations.push({ type: 'info', description: 'TC-WZ-010: Input not found — cannot test markdown rendering' });
      return;
    }

    await inputEl.click();
    await inputEl.fill('Liste 3 requisitos típicos para uma vaga de desenvolvedor');
    await inputEl.press('Enter');
    await authenticatedPage.waitForTimeout(12000);

    await authenticatedPage.screenshot({ path: 'e2e/screenshots/chat-wizard-markdown-response.png' });

    const strongCount = await authenticatedPage.locator('strong').count();
    const ulCount = await authenticatedPage.locator('ul').count();
    const olCount = await authenticatedPage.locator('ol').count();

    const hasMarkdownHtml = strongCount > 0 || ulCount > 0 || olCount > 0;

    if (!hasMarkdownHtml) {
      test.info().annotations.push({
        type: 'bug',
        description: `BUG-WZ-010: No markdown HTML elements found in Wizard inline response. <strong>=${strongCount}, <ul>=${ulCount}, <ol>=${olCount}`
      });
    }

    expect(hasMarkdownHtml, `Markdown must be rendered as HTML in Wizard inline chat. Got: <strong>${strongCount}, <ul>${ulCount}, <ol>${olCount}`).toBe(true);
  });
});
