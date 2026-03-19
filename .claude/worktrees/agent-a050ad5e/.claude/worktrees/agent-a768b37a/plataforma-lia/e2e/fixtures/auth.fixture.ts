import { test as base, expect, Page } from '@playwright/test';

export interface AuthFixture {
  authenticatedPage: Page;
  login: (email?: string, password?: string) => Promise<void>;
}

export const test = base.extend<AuthFixture>({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    
    if (await emailInput.isVisible()) {
      await emailInput.fill(process.env.TEST_USER_EMAIL || 'teste@wedotalent.com');
      await passwordInput.fill(process.env.TEST_USER_PASSWORD || 'teste123');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {});
    }
    
    await use(page);
  },

  login: async ({ page }, use) => {
    const loginFn = async (email?: string, password?: string) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      const emailInput = page.locator('input[type="email"], input[name="email"]');
      const passwordInput = page.locator('input[type="password"], input[name="password"]');
      
      if (await emailInput.isVisible()) {
        await emailInput.fill(email || process.env.TEST_USER_EMAIL || 'teste@wedotalent.com');
        await passwordInput.fill(password || process.env.TEST_USER_PASSWORD || 'teste123');
        await page.click('button[type="submit"]');
        await page.waitForLoadState('networkidle');
      }
    };
    
    await use(loginFn);
  },
});

export { expect };
