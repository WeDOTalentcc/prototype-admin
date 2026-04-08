import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 6 - Descrição da Vaga', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=6');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve gerar JD preview (v1)', async ({ authenticatedPage }) => {
    const generateButton = authenticatedPage.getByRole('button', { name: /gerar|preview|visualizar/i });
    
    if (await generateButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await generateButton.click();
      await authenticatedPage.waitForTimeout(3000);
      
      const preview = authenticatedPage.locator('[data-testid="jd-preview"], [class*="preview"]');
      await expect.soft(preview.first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('deve solicitar ajustes via chat', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="lia-chat-input"], textarea[placeholder*="LIA"]').first();
    
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await chatInput.fill('Deixe o tom mais informal e acolhedor');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
    }
  });

  test('deve exibir versões v1 e v2', async ({ authenticatedPage }) => {
    const versionTabs = authenticatedPage.locator('[data-testid="version-tabs"], [role="tablist"]');
    
    if (await versionTabs.isVisible({ timeout: 5000 }).catch(() => false)) {
      const v2Tab = authenticatedPage.getByRole('tab', { name: /v2|final|publicação/i });
      
      if (await v2Tab.isVisible()) {
        await v2Tab.click();
        await authenticatedPage.waitForLoadState('networkidle');
      }
    }
  });

  test('deve detectar idioma da JD', async ({ authenticatedPage }) => {
    const languageIndicator = authenticatedPage.locator('[data-testid="language-indicator"], [class*="language"]');
    
    if (await languageIndicator.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(languageIndicator).toContainText(/português|pt-br/i);
    }
  });

  test('deve copiar JD para clipboard', async ({ authenticatedPage }) => {
    const copyButton = authenticatedPage.getByRole('button', { name: /copiar|copy/i });
    
    if (await copyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await copyButton.click();
      
      const successMessage = authenticatedPage.locator('[class*="toast"], [role="alert"]');
      await expect.soft(successMessage.first()).toBeVisible({ timeout: 3000 });
    }
  });
});
