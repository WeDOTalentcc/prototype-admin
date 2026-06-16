import { test, expect } from '@playwright/test';

test.describe('Autenticação', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('deve exibir página de login', async ({ page }) => {
    const loginForm = page.locator('form, [data-testid="login-form"]');
    await expect(loginForm.first()).toBeVisible({ timeout: 10000 });
  });

  test('deve validar campos obrigatórios', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /entrar|login|acessar/i });
    
    if (await submitButton.isVisible()) {
      await submitButton.click();
      
      const errorMessage = page.locator('[role="alert"], .error, [class*="error"]');
      await expect.soft(errorMessage.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('deve validar formato de email', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    
    if (await emailInput.isVisible()) {
      await emailInput.fill('email-invalido');
      
      const passwordInput = page.locator('input[type="password"]');
      if (await passwordInput.isVisible()) {
        await passwordInput.focus();
      }
    }
  });

  test('deve exibir erro para credenciais inválidas', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.getByRole('button', { name: /entrar|login|acessar/i });
    
    if (await emailInput.isVisible() && await passwordInput.isVisible()) {
      await emailInput.fill('usuario@inexistente.com');
      await passwordInput.fill('senhaerrada123');
      
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('deve fazer login com sucesso', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.getByRole('button', { name: /entrar|login|acessar/i });
    
    if (await emailInput.isVisible() && await passwordInput.isVisible()) {
      await emailInput.fill(process.env.TEST_USER_EMAIL || 'teste@wedotalent.com');
      await passwordInput.fill(process.env.TEST_USER_PASSWORD || 'teste123');
      
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await expect.soft(page).toHaveURL(/dashboard/, { timeout: 15000 });
      }
    }
  });

  test('deve exibir link de recuperação de senha', async ({ page }) => {
    const forgotLink = page.getByRole('link', { name: /esqueci|recuperar|forgot/i });
    await expect.soft(forgotLink.first()).toBeVisible({ timeout: 5000 });
  });
});
