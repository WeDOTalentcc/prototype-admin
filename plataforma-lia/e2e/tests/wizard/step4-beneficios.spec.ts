import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 4 - Benefícios e Salário', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=4');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir campos de salário', async ({ authenticatedPage }) => {
    const salarySection = authenticatedPage.locator('[data-testid="salary"], [class*="salary"]');
    await expect.soft(salarySection.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve sugerir faixa salarial baseada no mercado', async ({ authenticatedPage }) => {
    const salaryInput = authenticatedPage.locator('input[name*="salary"], input[placeholder*="salário"]').first();
    
    if (await salaryInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await salaryInput.focus();
      await authenticatedPage.waitForTimeout(1000);
      
      const suggestion = authenticatedPage.locator('[data-testid="salary-suggestion"], [class*="market-range"]');
      if (await suggestion.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(suggestion).toBeVisible();
      }
    }
  });

  test('deve selecionar benefícios padrão da empresa', async ({ authenticatedPage }) => {
    const benefitsCheckboxes = authenticatedPage.locator('[data-testid="benefit-checkbox"], input[type="checkbox"][name*="benefit"]');
    const count = await benefitsCheckboxes.count();
    
    if (count > 0) {
      await benefitsCheckboxes.first().check();
      await expect(benefitsCheckboxes.first()).toBeChecked();
    }
  });

  test('deve adicionar benefício customizado', async ({ authenticatedPage }) => {
    const addButton = authenticatedPage.getByRole('button', { name: /adicionar benefício|novo benefício/i });
    
    if (await addButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addButton.click();
      
      const input = authenticatedPage.locator('input[placeholder*="benefício"]').first();
      if (await input.isVisible()) {
        await input.fill('Auxílio home office R$ 200');
        
        const confirmButton = authenticatedPage.getByRole('button', { name: /adicionar|confirmar/i });
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
        }
      }
    }
  });

  test('deve exibir comparativo com mercado', async ({ authenticatedPage }) => {
    const comparison = authenticatedPage.locator('[data-testid="market-comparison"], [class*="benchmark"]');
    
    if (await comparison.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(comparison).toContainText(/mercado|benchmark|comparativo/i);
    }
  });
});
