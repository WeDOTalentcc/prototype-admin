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

/**
 * Pré-aquece o endpoint /api/auth/ws-token, que em dev (NODE_ENV !== "production")
 * cai no caminho "dev-auto-login" — chama POST /api/v1/auth/login no backend
 * com o demo user, recebe um JWT real, e seta `lia_access_token` httpOnly no
 * contexto do browser. As navegações subsequentes (`page.goto`) e o WebSocket
 * (`useChatSocket` → `/api/auth/ws-token`) passam a usar JWT válido.
 *
 * Anteriormente o fixture setava `lia_access_token=e2e-test-token` (placeholder
 * literal), o que fazia o endpoint retornar esse mesmo valor como token JWT.
 * O backend rejeitava no `decode_token`, o WS fechava, e cada teste ficava
 * preso 15min até `test.setTimeout` estourar com `useChatSocket ws-token
 * fetch failed`. Esta função substitui o cookie fake pelo fluxo canônico.
 */
async function ensureRealDevAuth(context: import('@playwright/test').BrowserContext) {
  const response = await context.request.get('/api/auth/ws-token', {
    failOnStatusCode: false,
  });
  if (!response.ok()) {
    const body = await response.text().catch(() => '<unreadable>');
    throw new Error(
      `auth.fixture: /api/auth/ws-token returned ${response.status()} (expected 200 with dev-auto-login). ` +
      `Body: ${body.slice(0, 300)}. ` +
      `Fix: ensure NODE_ENV !== "production", lia-backend running on BACKEND_URL ` +
      `(default http://127.0.0.1:8001) with demo user (DEV_AUTO_LOGIN_EMAIL/PASSWORD or default ` +
      `demo@wedotalent.com / demo123).`,
    );
  }
}

export const test = base.extend<AuthFixture>({
  authenticatedPage: async ({ page, context }, use) => {
    // Marker cookie de método: o frontend pode ler isso para decidir UI flows.
    // O JWT real é setado pelo response do /api/auth/ws-token (httpOnly).
    await context.addCookies([
      {
        name: 'lia_auth_method',
        value: 'jwt',
        domain: AUTH_DOMAIN,
        path: '/',
      },
    ]);

    await ensureRealDevAuth(context);

    // Navigate to /pt/chat (200) — /dashboard returns 404 in dev mode.
    // Use 'domcontentloaded': fires as soon as DOM is parsed, avoiding hangs
    // from HMR websockets (which block 'load') or background network activity.
    await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    await use(page);
  },

  login: async ({ page, context }, use) => {
    const loginFn = async (_email?: string, _password?: string) => {
      await context.addCookies([
        {
          name: 'lia_auth_method',
          value: 'jwt',
          domain: AUTH_DOMAIN,
          path: '/',
        },
      ]);

      await ensureRealDevAuth(context);

      await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    };

    await use(loginFn);
  },
});

export { expect };
