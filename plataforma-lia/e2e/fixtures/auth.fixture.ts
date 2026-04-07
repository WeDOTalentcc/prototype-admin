import { test as base, expect, Page } from '@playwright/test';

export interface AuthFixture {
  authenticatedPage: Page;
  login: (email?: string, password?: string) => Promise<void>;
}

export const test = base.extend<AuthFixture>({
  authenticatedPage: async ({ page, context }, use) => {
    await context.addCookies([
      {
        name: 'lia_access_token',
        value: 'e2e-test-token',
        domain: 'localhost',
        path: '/',
      },
      {
        name: 'lia_auth_method',
        value: 'jwt',
        domain: 'localhost',
        path: '/',
      },
    ]);

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await use(page);
  },

  login: async ({ page, context }, use) => {
    const loginFn = async (_email?: string, _password?: string) => {
      await context.addCookies([
        {
          name: 'lia_access_token',
          value: 'e2e-test-token',
          domain: 'localhost',
          path: '/',
        },
        {
          name: 'lia_auth_method',
          value: 'jwt',
          domain: 'localhost',
          path: '/',
        },
      ]);

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
    };

    await use(loginFn);
  },
});

export { expect };
