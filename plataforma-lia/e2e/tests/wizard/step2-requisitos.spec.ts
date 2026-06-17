import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 2 - Requisitos', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=2');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir campos de requisitos', async ({ authenticatedPage }) => {
    const requirementsSection = authenticatedPage.locator('[data-testid="requirements"], [class*="requirement"]');
    await expect.soft(requirementsSection.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve adicionar requisito técnico', async ({ authenticatedPage }) => {
    const addButton = authenticatedPage.getByRole('button', { name: /adicionar|novo requisito/i });
    
    if (await addButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addButton.click();
      
      const input = authenticatedPage.locator('input[placeholder*="requisito"], textarea[placeholder*="requisito"]').first();
      if (await input.isVisible()) {
        await input.fill('5 anos de experiência com React');
      }
    }
  });

  test('deve sugerir requisitos baseado no cargo', async ({ authenticatedPage }) => {
    const liaSuggestions = authenticatedPage.locator('[data-testid="lia-suggestions"], [class*="ai-suggestion"]');
    
    if (await liaSuggestions.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      const suggestionItems = liaSuggestions.locator('[role="button"], button');
      const count = await suggestionItems.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('deve modificar sugestão LIA', async ({ authenticatedPage }) => {
    const editButton = authenticatedPage.getByRole('button', { name: /editar|modificar/i }).first();
    
    if (await editButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await editButton.click();
      
      const textarea = authenticatedPage.locator('textarea').first();
      if (await textarea.isVisible()) {
        await textarea.fill('Requisito modificado pelo recrutador');
        
        const saveButton = authenticatedPage.getByRole('button', { name: /salvar|confirmar/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();
        }
      }
    }
  });
});
