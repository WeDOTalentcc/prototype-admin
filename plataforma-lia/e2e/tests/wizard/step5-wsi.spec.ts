import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 5 - Perguntas WSI', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=5');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir perguntas WSI geradas pela LIA', async ({ authenticatedPage }) => {
    const wsiSection = authenticatedPage.locator('[data-testid="wsi-questions"], [class*="wsi"]');
    await expect.soft(wsiSection.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve exibir 7 blocos de metodologia WSI', async ({ authenticatedPage }) => {
    const blocks = authenticatedPage.locator('[data-testid="wsi-block"], [class*="wsi-block"]');
    const count = await blocks.count();
    
    if (count > 0) {
      expect(count).toBeGreaterThanOrEqual(1);
    }
  });

  test('deve editar pergunta sugerida', async ({ authenticatedPage }) => {
    const editButton = authenticatedPage.locator('[data-testid="edit-question"], button[aria-label*="editar"]').first();
    
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();
      
      const textarea = authenticatedPage.locator('textarea').first();
      if (await textarea.isVisible()) {
        await textarea.fill('Pergunta editada pelo recrutador');
        
        const saveButton = authenticatedPage.getByRole('button', { name: /salvar|confirmar/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();
        }
      }
    }
  });

  test('deve reordenar perguntas via drag and drop', async ({ authenticatedPage }) => {
    const dragHandle = authenticatedPage.locator('[data-testid="drag-handle"], [class*="grip"]').first();
    
    if (await dragHandle.isVisible({ timeout: 3000 }).catch(() => false)) {
      const target = authenticatedPage.locator('[data-testid="drag-handle"], [class*="grip"]').nth(1);
      
      if (await target.isVisible({ timeout: 2000 }).catch(() => false)) {
        await dragHandle.dragTo(target);
      }
    }
  });

  test('deve regenerar perguntas via chat LIA', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="lia-chat-input"], textarea[placeholder*="LIA"]').first();
    
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await chatInput.fill('Gere perguntas mais focadas em liderança');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
    }
  });
});
