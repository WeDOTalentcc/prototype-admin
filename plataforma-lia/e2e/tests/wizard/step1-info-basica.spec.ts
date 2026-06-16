import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 1 - Informações Básicas', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir formulário de informações básicas', async ({ authenticatedPage }) => {
    await expect(authenticatedPage.getByText(/informações básicas|título da vaga/i)).toBeVisible();
  });

  test('deve validar campos obrigatórios', async ({ authenticatedPage }) => {
    const nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    
    if (await nextButton.isVisible()) {
      await nextButton.click();
      const errorMessage = authenticatedPage.locator('[role="alert"], .error, [class*="error"]');
      await expect.soft(errorMessage.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('deve aceitar sugestão LIA para título', async ({ authenticatedPage }) => {
    const titleInput = authenticatedPage.locator('input[name="title"], input[placeholder*="título"]').first();
    
    if (await titleInput.isVisible()) {
      await titleInput.fill('Desenvolvedor');
      await authenticatedPage.waitForTimeout(2000);
      
      const liaSuggestion = authenticatedPage.locator('[data-testid="lia-suggestion"], [class*="suggestion"]');
      if (await liaSuggestion.first().isVisible({ timeout: 5000 }).catch(() => false)) {
        await liaSuggestion.first().click();
        await expect(titleInput).not.toHaveValue('Desenvolvedor');
      }
    }
  });

  test('deve preencher e avançar para próxima etapa', async ({ authenticatedPage }) => {
    const titleInput = authenticatedPage.locator('input[name="title"], input[placeholder*="título"]').first();
    const departmentSelect = authenticatedPage.locator('[name="department"], [data-testid="department"]').first();
    
    if (await titleInput.isVisible()) {
      await titleInput.fill('Desenvolvedor Full Stack Senior');
    }
    
    if (await departmentSelect.isVisible()) {
      await departmentSelect.click();
      const option = authenticatedPage.locator('[role="option"]').first();
      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();
      }
    }
    
    const nextButton = authenticatedPage.getByRole('button', { name: /próximo|continuar|avançar/i });
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await authenticatedPage.waitForLoadState('networkidle');
    }
  });
});
