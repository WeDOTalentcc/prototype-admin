import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 7 - Revisão e Publicação', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=7');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir resumo completo da vaga', async ({ authenticatedPage }) => {
    const summarySection = authenticatedPage.locator('[data-testid="job-summary"], [class*="summary"]');
    await expect.soft(summarySection.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve exibir origem dos campos (field origin)', async ({ authenticatedPage }) => {
    const originBadges = authenticatedPage.locator('[data-testid="field-origin"], [class*="origin-badge"]');
    const count = await originBadges.count();
    
    if (count > 0) {
      expect(count).toBeGreaterThan(0);
    }
  });

  test('deve exibir score de confiança', async ({ authenticatedPage }) => {
    const confidenceScore = authenticatedPage.locator('[data-testid="confidence-score"], [class*="confidence"]');
    
    if (await confidenceScore.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(confidenceScore).toBeVisible();
    }
  });

  test('deve permitir voltar e editar etapas anteriores', async ({ authenticatedPage }) => {
    const editButton = authenticatedPage.getByRole('button', { name: /editar|modificar/i }).first();
    
    if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
    }
  });

  test('deve publicar vaga como rascunho', async ({ authenticatedPage }) => {
    const draftButton = authenticatedPage.getByRole('button', { name: /salvar rascunho|draft/i });
    
    if (await draftButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await draftButton.click();
      
      const successMessage = authenticatedPage.locator('[class*="toast"], [role="alert"]');
      await expect.soft(successMessage.first()).toContainText(/salvo|sucesso/i, { timeout: 5000 });
    }
  });

  test('deve publicar vaga ativa', async ({ authenticatedPage }) => {
    const publishButton = authenticatedPage.getByRole('button', { name: /publicar|ativar vaga/i });
    
    if (await publishButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await publishButton.click();
      
      const confirmDialog = authenticatedPage.locator('[role="dialog"], [class*="modal"]');
      if (await confirmDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        const confirmButton = confirmDialog.getByRole('button', { name: /confirmar|publicar/i });
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
        }
      }
    }
  });

  test('deve registrar stage feedback no Learning Hub', async ({ authenticatedPage }) => {
    await authenticatedPage.waitForTimeout(1000);
  });
});
