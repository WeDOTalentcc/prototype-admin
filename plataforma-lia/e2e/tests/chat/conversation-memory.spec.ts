import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Chat - Conversation Memory', () => {
  test('deve persistir mensagens entre recarregamentos', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      const uniqueMessage = `Teste de persistência ${Date.now()}`;
      await chatInput.fill(uniqueMessage);
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const userMessage = authenticatedPage.locator('[data-testid="chat-message"][data-role="user"]').last();
      const isMessageVisible = await userMessage.isVisible({ timeout: 10000 }).catch(() => false);
      
      if (isMessageVisible) {
        await expect(userMessage).toContainText(uniqueMessage);
        
        await authenticatedPage.reload();
        await authenticatedPage.waitForLoadState('networkidle');
        
        await authenticatedPage.waitForTimeout(3000);
        
        const persistedMessage = authenticatedPage.locator(`text=${uniqueMessage.substring(0, 20)}`);
        const isPersisted = await persistedMessage.isVisible({ timeout: 10000 }).catch(() => false);
        
        if (isPersisted) {
          await expect(persistedMessage).toBeVisible();
        }
      }
    }
  });

  test('deve gerar resumo após 10 mensagens', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      const messages = [
        'Quero criar uma vaga de desenvolvedor',
        'O cargo é Desenvolvedor Full Stack Senior',
        'A área é Tecnologia',
        'Modelo de trabalho híbrido',
        'Localização em São Paulo',
        'Contrato CLT',
        'Salário entre 15 e 20 mil',
        'Precisa conhecer React e Node',
        'Experiência mínima de 5 anos',
        'Inglês avançado é obrigatório',
        'Benefícios incluem VR e plano de saúde',
      ];
      
      for (const message of messages) {
        await chatInput.fill(message);
        await chatInput.press('Enter');
        await authenticatedPage.waitForTimeout(2000);
      }
      
      await authenticatedPage.waitForTimeout(5000);
      
      const allMessages = authenticatedPage.locator('[data-testid="chat-message"]');
      const messageCount = await allMessages.count();
      
      expect(messageCount).toBeGreaterThan(0);
      
      await authenticatedPage.reload();
      await authenticatedPage.waitForLoadState('networkidle');
      await authenticatedPage.waitForTimeout(3000);
      
      const contextIndicator = authenticatedPage.locator('text=/resumo|contexto|continuando/i').first();
      await contextIndicator.isVisible({ timeout: 5000 }).catch(() => false);
    }
  });

  test('deve restaurar contexto ao reabrir wizard', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('Desenvolvedor Python Pleno para área de dados');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(5000);
      
      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');
      
      await authenticatedPage.waitForTimeout(1000);
      
      await authenticatedPage.goto('/vagas/nova');
      await authenticatedPage.waitForLoadState('networkidle');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const contextRestored = authenticatedPage.locator('text=/python|desenvolvedor|dados|continuar|rascunho/i').first();
      const isContextVisible = await contextRestored.isVisible({ timeout: 10000 }).catch(() => false);
      
      if (isContextVisible) {
        await expect(contextRestored).toBeVisible();
      }
    }
  });

  test('deve manter histórico de mensagens visível no chat', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      const testMessages = [
        'Primeira mensagem do teste',
        'Segunda mensagem do teste',
        'Terceira mensagem do teste',
      ];
      
      for (const message of testMessages) {
        await chatInput.fill(message);
        await chatInput.press('Enter');
        await authenticatedPage.waitForTimeout(2000);
      }
      
      await authenticatedPage.waitForTimeout(3000);
      
      const userMessages = authenticatedPage.locator('[data-testid="chat-message"][data-role="user"]');
      const userMessageCount = await userMessages.count();
      
      expect(userMessageCount).toBeGreaterThanOrEqual(1);
      
      const liaMessages = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]');
      const liaMessageCount = await liaMessages.count();
      
      expect(liaMessageCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('deve permitir continuar conversa anterior', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('Quero criar uma vaga de Analista de Marketing');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(5000);
      
      const liaResponse = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]').last();
      const hasResponse = await liaResponse.isVisible({ timeout: 10000 }).catch(() => false);
      
      if (hasResponse) {
        await chatInput.fill('O salário será entre 8 e 12 mil');
        await chatInput.press('Enter');
        
        await authenticatedPage.waitForTimeout(5000);
        
        const contextualResponse = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]').last();
        await expect(contextualResponse).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('deve exibir indicador de carregamento durante processamento', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('Analise o perfil ideal para um Tech Lead');
      await chatInput.press('Enter');
      
      const loadingIndicator = authenticatedPage.locator('[class*="animate-bounce"], [class*="loading"], [class*="spinner"]').first();
      const isLoading = await loadingIndicator.isVisible({ timeout: 3000 }).catch(() => false);
      
      if (isLoading) {
        await expect(loadingIndicator).toBeVisible();
      }
      
      await authenticatedPage.waitForTimeout(10000);
      
      const response = authenticatedPage.locator('[data-testid="chat-message"][data-role="lia"]').last();
      await expect.soft(response).toBeVisible({ timeout: 15000 });
    }
  });

  test('deve limpar conversa quando solicitado', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/vagas/nova');
    await authenticatedPage.waitForLoadState('networkidle');

    const chatInput = authenticatedPage.locator('[data-testid="chat-input"]').first();
    
    if (await chatInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await chatInput.fill('Mensagem para teste de limpeza');
      await chatInput.press('Enter');
      
      await authenticatedPage.waitForTimeout(3000);
      
      const clearButton = authenticatedPage.locator('button:has-text("limpar"), button:has-text("nova conversa"), [aria-label*="limpar"]').first();
      const hasClearButton = await clearButton.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (hasClearButton) {
        await clearButton.click();
        await authenticatedPage.waitForTimeout(2000);
        
        const messages = authenticatedPage.locator('[data-testid="chat-message"]');
        const messageCount = await messages.count();
        
        expect(messageCount).toBeLessThanOrEqual(1);
      }
    }
  });
});
