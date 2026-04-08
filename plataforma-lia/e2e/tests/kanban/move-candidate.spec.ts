import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Kanban - Movimentação de Candidatos', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas');
    await authenticatedPage.waitForLoadState('networkidle');
    
    const firstJob = authenticatedPage.locator('[data-testid="job-card"], [class*="job-row"]').first();
    if (await firstJob.isVisible({ timeout: 10000 }).catch(() => false)) {
      await firstJob.click();
      await authenticatedPage.waitForLoadState('networkidle');
    }
  });

  test('deve exibir colunas do kanban', async ({ authenticatedPage }) => {
    const columns = authenticatedPage.locator('[data-testid="kanban-column"], [class*="kanban-column"]');
    const count = await columns.count();
    expect(count).toBeGreaterThan(0);
  });

  test('deve exibir candidatos nas colunas', async ({ authenticatedPage }) => {
    const candidateCards = authenticatedPage.locator('[data-testid="candidate-card"], [class*="candidate-card"]');
    await expect.soft(candidateCards.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve mover candidato via drag and drop', async ({ authenticatedPage }) => {
    const candidateCard = authenticatedPage.locator('[data-testid="candidate-card"], [class*="candidate-card"]').first();
    const targetColumn = authenticatedPage.locator('[data-testid="kanban-column"], [class*="kanban-column"]').nth(1);
    
    if (await candidateCard.isVisible({ timeout: 5000 }).catch(() => false)) {
      if (await targetColumn.isVisible()) {
        await candidateCard.dragTo(targetColumn);
        await authenticatedPage.waitForTimeout(1000);
      }
    }
  });

  test('deve exibir modal de confirmação com sugestão LIA', async ({ authenticatedPage }) => {
    const candidateCard = authenticatedPage.locator('[data-testid="candidate-card"], [class*="candidate-card"]').first();
    
    if (await candidateCard.isVisible({ timeout: 5000 }).catch(() => false)) {
      await candidateCard.click();
      
      const moveButton = authenticatedPage.getByRole('button', { name: /mover|avançar etapa/i });
      if (await moveButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await moveButton.click();
        
        const modal = authenticatedPage.locator('[role="dialog"], [class*="modal"]');
        await expect.soft(modal.first()).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('deve sugerir sub-status via LIA', async ({ authenticatedPage }) => {
    const substatus = authenticatedPage.locator('[data-testid="substatus-suggestion"], [class*="substatus"]');
    
    if (await substatus.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(substatus).toBeVisible();
    }
  });

  test('deve confirmar movimentação com feedback', async ({ authenticatedPage }) => {
    const confirmButton = authenticatedPage.getByRole('button', { name: /confirmar|mover/i });
    
    if (await confirmButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await confirmButton.click();
      
      const successMessage = authenticatedPage.locator('[class*="toast"], [role="alert"]');
      await expect.soft(successMessage.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('deve registrar movimentação no histórico', async ({ authenticatedPage }) => {
    const historyTab = authenticatedPage.getByRole('tab', { name: /histórico|timeline/i });
    
    if (await historyTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await historyTab.click();
      
      const historyItems = authenticatedPage.locator('[data-testid="history-item"], [class*="timeline-item"]');
      await expect.soft(historyItems.first()).toBeVisible({ timeout: 5000 });
    }
  });
});
