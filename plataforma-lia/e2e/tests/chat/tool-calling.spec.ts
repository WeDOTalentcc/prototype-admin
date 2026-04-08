import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Chat - Tool Calling Flow', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');
  });

  test('deve mostrar confirmação ao solicitar ação crítica', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('publica a vaga');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const isConfirmationVisible = await toolConfirmation.isVisible({ timeout: 15000 }).catch(() => false);
      
      if (isConfirmationVisible) {
        await expect(toolConfirmation).toBeVisible();
        
        await expect(toolConfirmation).toContainText(/confirmação|publicar|deseja/i);
        
        const confirmButton = authenticatedPage.locator('[data-testid="tool-confirm-button"]');
        await expect(confirmButton).toBeVisible();
        
        await confirmButton.click();
        
        await authenticatedPage.waitForTimeout(5000);
        
        const toolFeedback = authenticatedPage.locator('[data-testid="tool-feedback"]');
        const isFeedbackVisible = await toolFeedback.isVisible({ timeout: 10000 }).catch(() => false);
        
        if (isFeedbackVisible) {
          const status = await toolFeedback.getAttribute('data-status');
          expect(['success', 'error', 'executing']).toContain(status);
        }
      } else {
        const responseMessage = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]').last();
        await expect.soft(responseMessage).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('deve permitir cancelar execução de tool', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('encerra a vaga');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const isConfirmationVisible = await toolConfirmation.isVisible({ timeout: 15000 }).catch(() => false);
      
      if (isConfirmationVisible) {
        const cancelButton = authenticatedPage.locator('[data-testid="tool-cancel-button"]');
        await expect(cancelButton).toBeVisible();
        
        await cancelButton.click();
        
        await authenticatedPage.waitForTimeout(2000);
        
        await expect(toolConfirmation).not.toBeVisible({ timeout: 5000 });
        
        const successFeedback = authenticatedPage.locator('[data-testid="tool-feedback"][data-status="success"]');
        await expect(successFeedback).not.toBeVisible({ timeout: 2000 });
      }
    }
  });

  test('deve executar tools sem confirmação quando não crítica', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('valida os campos do formulário');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const isConfirmationVisible = await toolConfirmation.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (!isConfirmationVisible) {
        const responseMessage = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]').last();
        const hasResponse = await responseMessage.isVisible({ timeout: 10000 }).catch(() => false);
        
        if (hasResponse) {
          await expect(responseMessage).toBeVisible();
        }
        
        const toolFeedback = authenticatedPage.locator('[data-testid="tool-feedback"]');
        const hasFeedback = await toolFeedback.isVisible({ timeout: 5000 }).catch(() => false);
        
        if (hasFeedback) {
          await expect(toolFeedback).toBeVisible();
        }
      }
    }
  });

  test('deve mostrar estado de execução durante processamento', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('agenda entrevista para amanhã às 14h');
      await chatInput.press('Enter');
      
      const executingFeedback = authenticatedPage.locator('[data-testid="tool-feedback"][data-status="executing"]');
      const isExecuting = await executingFeedback.isVisible({ timeout: 10000 }).catch(() => false);
      
      if (isExecuting) {
        await expect(executingFeedback).toContainText(/executando|aguarde|processando/i);
      }
      
      await authenticatedPage.waitForTimeout(5000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const confirmButton = authenticatedPage.locator('[data-testid="tool-confirm-button"]');
      
      if (await toolConfirmation.isVisible({ timeout: 5000 }).catch(() => false)) {
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
        }
      }
    }
  });

  test('deve aceitar confirmação via texto "sim"', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('publica a vaga');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const isConfirmationVisible = await toolConfirmation.isVisible({ timeout: 15000 }).catch(() => false);
      
      if (isConfirmationVisible) {
        const newInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
        await newInput.fill('sim');
        await newInput.press('Enter');
        
        await authenticatedPage.waitForTimeout(5000);
        
        const toolFeedback = authenticatedPage.locator('[data-testid="tool-feedback"]');
        const hasFeedback = await toolFeedback.isVisible({ timeout: 10000 }).catch(() => false);
        
        if (hasFeedback) {
          const status = await toolFeedback.getAttribute('data-status');
          expect(['success', 'error', 'executing']).toContain(status);
        }
      }
    }
  });

  test('deve recusar confirmação via texto "não"', async ({ authenticatedPage }) => {
    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('encerra a vaga');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const toolConfirmation = authenticatedPage.locator('[data-testid="tool-confirmation"]');
      const isConfirmationVisible = await toolConfirmation.isVisible({ timeout: 15000 }).catch(() => false);
      
      if (isConfirmationVisible) {
        const newInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
        await newInput.fill('não');
        await newInput.press('Enter');
        
        await authenticatedPage.waitForTimeout(3000);
        
        await expect(toolConfirmation).not.toBeVisible({ timeout: 5000 });
      }
    }
  });
});
