/**
 * Fixture de auth leve para o E2E do Recrutar > Vagas pipeline.
 *
 * O auth.fixture.ts canônico navega para /pt/chat após autenticar, e em
 * dev mode esse rota renderiza o chat unificado (heavy: WebSocket +
 * lazy panels) que não termina domcontentloaded em <30s. Para os testes
 * desta sprint que SÓ precisam de auth + navegar para /pt/recrutar,
 * pulamos o /pt/chat e deixamos o teste decidir onde landar.
 *
 * Espelho mínimo de e2e/fixtures/auth.fixture.ts (Task #1053): chama o
 * backend direto (POST /api/v1/auth/login) e seta lia_access_token, sem
 * depender de LIA_DEV_AUTO_LOGIN no FE.
 */
import { test as base, expect, Page, APIRequestContext, BrowserContext } from '@playwright/test'

let AUTH_DOMAIN = 'localhost'
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname
  }
} catch {
  console.warn(`Invalid PLAYWRIGHT_BASE_URL: "${process.env.PLAYWRIGHT_BASE_URL}"`)
}

const DEMO_EMAIL = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
const DEMO_PASSWORD = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'
const BACKEND_URL =
  process.env.LIA_BACKEND_URL ||
  process.env.BACKEND_URL ||
  'http://127.0.0.1:8001'

export interface RecrutarAuthFixture {
  authenticatedPage: Page
}

async function fetchDemoAccessToken(request: APIRequestContext): Promise<string> {
  const url = `${BACKEND_URL}/api/v1/auth/login`
  const response = await request.post(url, {
    data: { email: DEMO_EMAIL, password: DEMO_PASSWORD },
    headers: { 'Content-Type': 'application/json' },
    failOnStatusCode: false,
    timeout: 15_000,
  })
  if (!response.ok()) {
    const body = await response.text().catch(() => '<unreadable>')
    throw new Error(
      `recrutar-auth: backend ${url} returned ${response.status()}; body: ${body.slice(0, 200)}`,
    )
  }
  const payload = await response.json()
  const token = payload?.access_token || payload?.data?.access_token
  if (!token || typeof token !== 'string') {
    throw new Error(
      `recrutar-auth: backend response missing access_token (keys: ${Object.keys(payload || {}).join(',') || 'none'})`,
    )
  }
  return token
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
    { name: 'lia_auth_method', value: 'jwt', domain: AUTH_DOMAIN, path: '/' },
  ])
}

export const test = base.extend<RecrutarAuthFixture>({
  authenticatedPage: async ({ page, context, request }, use) => {
    const accessToken = await fetchDemoAccessToken(request)
    await seedAuthCookies(context, accessToken)
    // No pre-navigation — let the test decide where to land.
    await use(page)
  },
})

export { expect }
