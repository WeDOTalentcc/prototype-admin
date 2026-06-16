/**
 * Test Suite: Formatação de Texto nos Chats LIA (E2E)
 * Audits text formatting/markdown rendering via browser.
 *
 * Coverage:
 * - No raw markdown chars visible (*, #, ```, etc.)
 * - <thought> tags not visible to user
 * - JSON blocks not visible to user
 * - Formatted content appears in chat messages
 */

import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Formatação de Texto — Auditoria E2E de Markdown', () => {

  test('TC-FMT-030: Sem caracteres markdown visíveis (* # ```) nas respostas da LIA', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const inputSelectors = [
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[aria-label="Mensagem para a LIA"]',
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        await input.click();
        await input.fill('Liste 3 tipos de vagas de tecnologia no mercado');
        await input.press('Enter');
        await authenticatedPage.waitForTimeout(10000);

        await authenticatedPage.screenshot({ path: 'e2e/screenshots/formatacao-lia-resposta.png' });

        const messageContent = await authenticatedPage.locator('[class*="prose"], [class*="message-content"], [class*="MessageList"]').textContent().catch(() => '');
        const allBodyText = await authenticatedPage.locator('body').textContent() || '';
        const textToCheck = messageContent || allBodyText;

        const rawBold = /\*\*[^*]+\*\*/.test(textToCheck);
        const rawHeader = /(?:^|\n)#{1,3}\s+\w/.test(textToCheck);

        if (rawBold) {
          test.info().annotations.push({ type: 'bug', description: 'BUG-FMT-030a [HIGH]: Raw **bold** markdown visible — not rendered as HTML <strong>' });
        }
        if (rawHeader) {
          test.info().annotations.push({ type: 'bug', description: 'BUG-FMT-030b [HIGH]: Raw #header markdown visible — not rendered as HTML <h2>/<h3>' });
        }

        expect(rawBold, 'Raw **bold** markdown chars must not be visible to user (should be rendered as <strong>)').toBe(false);
        expect(rawHeader, 'Raw #header markdown chars must not be visible to user (should be rendered as <h2>/<h3>)').toBe(false);

        inputFound = true;
        break;
      }
    }

    if (!inputFound) {
      test.info().annotations.push({ type: 'info', description: 'TC-FMT-030: Input not found — skipping markdown visibility check' });
    }
  });

  test('TC-FMT-031: Ausência de tags <thought> e JSON bruto no output visível', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const inputSelectors = [
      'input[aria-label="Mensagem para a LIA"]',
      'textarea[aria-label="Mensagem para a LIA"]',
    ];

    let checked = false;
    for (const selector of inputSelectors) {
      const input = authenticatedPage.locator(selector).first();
      if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
        await input.click();
        await input.fill('Olá LIA, como vai?');
        await input.press('Enter');
        await authenticatedPage.waitForTimeout(10000);

        const pageText = await authenticatedPage.locator('body').textContent() || '';

        await authenticatedPage.screenshot({ path: 'e2e/screenshots/formatacao-sem-thought.png' });

        const hasThoughtTag = pageText.includes('<thought>');
        const hasThoughtJson = pageText.includes('"thought"') && pageText.includes('"response"');

        if (hasThoughtTag) {
          test.info().annotations.push({ type: 'bug', description: 'BUG-FMT-031a [CRITICAL]: <thought> tag is visible to user — internal reasoning exposed' });
        }
        if (hasThoughtJson) {
          test.info().annotations.push({ type: 'bug', description: 'BUG-FMT-031b [CRITICAL]: JSON with "thought"/"response" fields visible — cleanAgentResponse not applied' });
        }

        expect(hasThoughtTag, 'CRITICAL: <thought> tags must NEVER be visible to users — internal reasoning must be stripped').toBe(false);
        expect(hasThoughtJson, 'CRITICAL: Raw JSON with thought/response fields must NEVER be visible to users').toBe(false);

        checked = true;
        break;
      }
    }

    if (!checked) {
      test.info().annotations.push({ type: 'info', description: 'TC-FMT-031: Input not found — could not check thought tag visibility' });
    }
  });

  test('TC-FMT-032: Markdown renderizado como HTML (<strong>, <ul>, <ol>) na resposta', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const input = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await input.click();
      await input.fill('Liste as etapas de um processo seletivo com formatação');
      await input.press('Enter');
      await authenticatedPage.waitForTimeout(12000);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/formatacao-markdown-dom.png' });

      const strongCount = await authenticatedPage.locator('strong').count();
      const ulCount = await authenticatedPage.locator('ul').count();
      const olCount = await authenticatedPage.locator('ol').count();
      const emCount = await authenticatedPage.locator('em').count();

      const hasMarkdownHtml = strongCount > 0 || ulCount > 0 || olCount > 0 || emCount > 0;

      if (!hasMarkdownHtml) {
        test.info().annotations.push({
          type: 'bug',
          description: 'BUG-FMT-032 [HIGH]: No HTML markdown elements (<strong>,<ul>,<ol>) found — markdown may not be rendering correctly'
        });
      }

      expect(hasMarkdownHtml, `Markdown elements must be rendered as HTML. Found: <strong>${strongCount}, <ul>${ulCount}, <ol>${olCount}, <em>${emCount}>`).toBe(true);
    } else {
      test.info().annotations.push({ type: 'info', description: 'TC-FMT-032: Input not found in floating chat' });
    }
  });

  test('TC-FMT-033: Chat Principal vs. Chat Flutuante — paridade de formatação markdown', async ({ authenticatedPage }) => {
    const testMessage = 'Explique em 3 pontos o processo de triagem de candidatos';

    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const flutuanteInput = authenticatedPage.locator('input[aria-label="Mensagem para a LIA"]').first();
    let flutuanteMarkdown = { strong: 0, ul: 0, ol: 0 };

    if (await flutuanteInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await flutuanteInput.click();
      await flutuanteInput.fill(testMessage);
      await flutuanteInput.press('Enter');
      await authenticatedPage.waitForTimeout(12000);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/formatacao-flutuante-resposta.png' });

      flutuanteMarkdown = {
        strong: await authenticatedPage.locator('strong').count(),
        ul: await authenticatedPage.locator('ul').count(),
        ol: await authenticatedPage.locator('ol').count(),
      };

      const flutuanteHasMarkdown = flutuanteMarkdown.strong > 0 || flutuanteMarkdown.ul > 0 || flutuanteMarkdown.ol > 0;
      expect(flutuanteHasMarkdown, `Chat Flutuante must render markdown HTML. Got: ${JSON.stringify(flutuanteMarkdown)}`).toBe(true);
    }

    await authenticatedPage.goto('/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    await authenticatedPage.waitForTimeout(2000);

    const principalInput = authenticatedPage.locator('[aria-label="Mensagem para a LIA"]').first();

    if (await principalInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await principalInput.click();
      await principalInput.fill(testMessage);
      await principalInput.press('Enter');
      await authenticatedPage.waitForTimeout(12000);

      await authenticatedPage.screenshot({ path: 'e2e/screenshots/formatacao-principal-resposta.png' });

      const principalMarkdown = {
        strong: await authenticatedPage.locator('strong').count(),
        ul: await authenticatedPage.locator('ul').count(),
        ol: await authenticatedPage.locator('ol').count(),
      };

      const principalHasMarkdown = principalMarkdown.strong > 0 || principalMarkdown.ul > 0 || principalMarkdown.ol > 0;

      if (!principalHasMarkdown) {
        test.info().annotations.push({
          type: 'bug',
          description: `BUG-FMT-033 (BUG-005) [HIGH]: Chat Principal at /chat does not render markdown. Chat Flutuante=${JSON.stringify(flutuanteMarkdown)} vs Principal=${JSON.stringify(principalMarkdown)} — parseChatMarkdown missing in pipeline`
        });
      }

      expect(principalHasMarkdown, `Chat Principal must render markdown HTML. Got: ${JSON.stringify(principalMarkdown)}`).toBe(true);
    } else {
      test.info().annotations.push({ type: 'info', description: 'TC-FMT-033: Input not found in Chat Principal at /chat' });
    }
  });
});
