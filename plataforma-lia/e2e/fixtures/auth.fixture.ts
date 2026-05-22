import { test as base, expect, Page, APIRequestContext, BrowserContext } from '@playwright/test';

let AUTH_DOMAIN = 'localhost';
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname;
  }
} catch {
  console.warn(`Invalid PLAYWRIGHT_BASE_URL: "${process.env.PLAYWRIGHT_BASE_URL}", falling back to localhost`);
}

const DEMO_EMAIL = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com';
const DEMO_PASSWORD = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123';
const BACKEND_URL =
  process.env.LIA_BACKEND_URL ||
  process.env.BACKEND_URL ||
  'http://127.0.0.1:8001';

export interface AuthFixture {
  authenticatedPage: Page;
  login: (email?: string, password?: string) => Promise<void>;
}

/**
 * Task #1053 — fixture self-sufficient.
 *
 * Histórico: a versão anterior chamava /api/auth/ws-token (Next.js proxy)
 * e dependia de LIA_DEV_AUTO_LOGIN=true no processo do FE. Esse env var é
 * OFF por default (post-mortem 2026-04-29 wizard-domain-hint-leak) e
 * estava só em .env.local (gitignored), então fresh checkouts e CI viam
 * 503 (`dev_auto_login_failed`) e o cenário A do wizard nunca rodava.
 *
 * Agora o fixture conversa direto com o backend (POST /api/v1/auth/login)
 * usando as credenciais do demo user e seta `lia_access_token` httpOnly
 * no contexto do browser. O endpoint /api/auth/ws-token do FE então cai
 * no primeiro ramo (cookie present → token devolvido), independente da
 * flag LIA_DEV_AUTO_LOGIN. Test harness deixa de depender de env do FE.
 */
async function fetchDemoAccessToken(request: APIRequestContext): Promise<string> {
  const url = `${BACKEND_URL}/api/v1/auth/login`;
  const response = await request.post(url, {
    data: { email: DEMO_EMAIL, password: DEMO_PASSWORD },
    headers: { 'Content-Type': 'application/json' },
    failOnStatusCode: false,
    timeout: 15_000,
  });
  if (!response.ok()) {
    const body = await response.text().catch(() => '<unreadable>');
    throw new Error(
      `auth.fixture: backend ${url} returned ${response.status()} for ${DEMO_EMAIL}. ` +
        `Body: ${body.slice(0, 300)}. ` +
        `Fix: ensure lia-agent-system is running on BACKEND_URL/LIA_BACKEND_URL ` +
        `(default http://127.0.0.1:8001) with the demo user seeded ` +
        `(DEV_AUTO_LOGIN_EMAIL/DEV_AUTO_LOGIN_PASSWORD or defaults demo@wedotalent.com / demo123).`,
    );
  }
  const payload = await response.json();
  const accessToken = payload?.access_token || payload?.data?.access_token;
  if (!accessToken || typeof accessToken !== 'string') {
    throw new Error(
      `auth.fixture: backend ${url} response missing access_token (keys: ${Object.keys(payload || {}).join(',') || 'none'})`,
    );
  }
  return accessToken;
}

async function seedAuthCookies(context: BrowserContext, accessToken: string) {
  await context.addCookies([
    {
      name: 'lia_access_token',
      value: accessToken,
      domain: AUTH_DOMAIN,
      path: '/',
      httpOnly: true,
      sameSite: 'Lax',
    },
    {
      name: 'lia_auth_method',
      value: 'jwt',
      domain: AUTH_DOMAIN,
      path: '/',
    },
  ]);
}

export const test = base.extend<AuthFixture>({
  authenticatedPage: async ({ page, context, request }, use) => {
    const accessToken = await fetchDemoAccessToken(request);
    await seedAuthCookies(context, accessToken);

    // Navigate to /pt/chat (200) — /dashboard returns 404 in dev mode.
    // Use 'domcontentloaded': fires as soon as DOM is parsed, avoiding hangs
    // from HMR websockets (which block 'load') or background network activity.
    await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    await use(page);
  },

  login: async ({ page, context, request }, use) => {
    const loginFn = async (_email?: string, _password?: string) => {
      const accessToken = await fetchDemoAccessToken(request);
      await seedAuthCookies(context, accessToken);
      await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    };
    await use(loginFn);
  },
});

export { expect };

// Re-exports to satisfy spec files that import `Page` directly from this module.
export type { Page } from '@playwright/test';

/**
 * Standalone helper for spec files that don't use the `authenticatedPage` fixture.
 * Authenticates via backend POST /api/v1/auth/login, seeds cookies, and navigates to /pt/chat.
 *
 * Note: must be called with the actual Page from the test (not the fixture-extended one).
 * Internally creates an APIRequestContext from the page's context.
 */
export async function authenticateAsRecruiter(page: Page): Promise<void> {
  const context = page.context();
  const request = context.request;
  const accessToken = await fetchDemoAccessToken(request);
  await seedAuthCookies(context, accessToken);
  await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
}
