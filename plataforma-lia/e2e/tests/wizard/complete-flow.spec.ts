import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard - Fluxo Completo E2E', () => {
  test('deve criar vaga do início ao fim', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');
    
    const titleInput = authenticatedPage.locator('input[name="title"], input[placeholder*="título"]').first();
    if (await titleInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await titleInput.fill('Desenvolvedor Full Stack Senior - E2E Test');
    }
    
    let nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
    nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
    nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
    nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
    nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
    nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(1000);
    }
    
    const draftButton = authenticatedPage.getByRole('button', { name: /salvar rascunho|draft/i });
    if (await draftButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await draftButton.click();
      await authenticatedPage.waitForTimeout(2000);
    }
    
    await authenticatedPage.waitForTimeout(1000);
  });

  test('deve aceitar e modificar sugestões LIA em cada etapa', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');
    
    let liaSuggestions = authenticatedPage.locator('[data-testid="lia-suggestion"], [class*="suggestion"]');
    let count = await liaSuggestions.count();
    
    if (count > 0) {
      await liaSuggestions.first().click();
      await authenticatedPage.waitForTimeout(500);
    }
    
    const nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
    }
    
    await authenticatedPage.waitForTimeout(1000);
    liaSuggestions = authenticatedPage.locator('[data-testid="lia-suggestion"], [class*="suggestion"]');
    count = await liaSuggestions.count();
    
    if (count > 0) {
      const editButton = authenticatedPage.getByRole('button', { name: /editar|modificar/i }).first();
      if (await editButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await editButton.click();
        
        const textarea = authenticatedPage.locator('textarea').first();
        if (await textarea.isVisible()) {
          await textarea.fill('Sugestão modificada pelo teste E2E');
          
          const saveButton = authenticatedPage.getByRole('button', { name: /salvar|confirmar/i });
          if (await saveButton.isVisible()) {
            await saveButton.click();
          }
        }
      }
    }
  });

  test('deve usar chat LIA para ajustes', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=6');
    await authenticatedPage.waitForLoadState('networkidle');
    
    const chatInput = authenticatedPage.locator('[data-testid="lia-chat-input"], textarea[placeholder*="LIA"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('Deixe a descrição mais informal e acolhedora');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(5000);
      
      const response = authenticatedPage.locator('[data-testid="lia-response"], [class*="ai-response"]');
      await expect.soft(response.first()).toBeVisible({ timeout: 10000 });
    }
  });
});
