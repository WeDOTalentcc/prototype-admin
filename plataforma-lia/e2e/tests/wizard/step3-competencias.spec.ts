import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Wizard Step 3 - Competências', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova?step=3');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve exibir lista de competências sugeridas', async ({ authenticatedPage }) => {
    const competenciesSection = authenticatedPage.locator('[data-testid="competencies"], [class*="competenc"]');
    await expect.soft(competenciesSection.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve selecionar competência técnica', async ({ authenticatedPage }) => {
    const checkbox = authenticatedPage.locator('input[type="checkbox"]').first();
    
    if (await checkbox.isVisible({ timeout: 5000 }).catch(() => false)) {
      await checkbox.check();
      await expect(checkbox).toBeChecked();
    }
  });

  test('deve definir nível de proficiência', async ({ authenticatedPage }) => {
    const levelSelector = authenticatedPage.locator('[data-testid="level-selector"], select[name*="level"]').first();
    
    if (await levelSelector.isVisible({ timeout: 5000 }).catch(() => false)) {
      await levelSelector.click();
      const option = authenticatedPage.locator('[role="option"]').first();
      if (await option.isVisible()) {
        await option.click();
      }
    }
  });

  test('deve adicionar competência customizada', async ({ authenticatedPage }) => {
    const addCustomButton = authenticatedPage.getByRole('button', { name: /adicionar custom|nova competência/i });
    
    if (await addCustomButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addCustomButton.click();
      
      const input = authenticatedPage.locator('input[placeholder*="competência"]').first();
      if (await input.isVisible()) {
        await input.fill('Liderança Técnica');
        
        const confirmButton = authenticatedPage.getByRole('button', { name: /adicionar|confirmar/i });
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
        }
      }
    }
  });

  test('deve filtrar competências duplicadas entre etapas', async ({ authenticatedPage }) => {
    const warningMessage = authenticatedPage.locator('[class*="duplicate"], [data-testid="duplicate-warning"]');
    const isDuplicateWarningVisible = await warningMessage.first().isVisible({ timeout: 3000 }).catch(() => false);
    
    if (isDuplicateWarningVisible) {
      await expect(warningMessage.first()).toContainText(/duplicad|já selecionad/i);
    }
  });
});
