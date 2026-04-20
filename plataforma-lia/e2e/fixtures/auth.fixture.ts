import { test as base, expect, Page } from '@playwright/test';

let AUTH_DOMAIN = 'localhost';
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname;
  }
} catch {
  console.warn(`Invalid PLAYWRIGHT_BASE_URL: "${process.env.PLAYWRIGHT_BASE_URL}", falling back to localhost`);
}

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
        domain: AUTH_DOMAIN,
        path: '/',
      },
      {
        name: 'lia_auth_method',
        value: 'jwt',
        domain: AUTH_DOMAIN,
        path: '/',
      },
    ]);

    // Navigate to /pt/chat (200) — /dashboard returns 404 in dev mode.
    // Use 'load' instead of 'networkidle': dev-server HMR websockets prevent
    // networkidle from ever firing, causing a 240s fixture timeout.
    await page.goto('/pt/chat', { waitUntil: 'load', timeout: 30_000 });
    await use(page);
  },

  login: async ({ page, context }, use) => {
    const loginFn = async (_email?: string, _password?: string) => {
      await context.addCookies([
        {
          name: 'lia_access_token',
          value: 'e2e-test-token',
          domain: AUTH_DOMAIN,
          path: '/',
        },
        {
          name: 'lia_auth_method',
          value: 'jwt',
          domain: AUTH_DOMAIN,
          path: '/',
        },
      ]);

      await page.goto('/pt/chat', { waitUntil: 'load', timeout: 30_000 });
    };

    await use(loginFn);
  },
});

export { expect };
