/**
 * Fixture de auth leve para o E2E do Recrutar > Vagas pipeline.
 *
 * O auth.fixture.ts canônico navega para /pt/chat após o ws-token, e em
 * dev mode esse rota renderiza o chat unificado (heavy: WebSocket +
 * lazy panels) que não termina domcontentloaded em <30s. Para os testes
 * desta sprint que SÓ precisam de auth + navegar para /pt/recrutar,
 * pulamos o /pt/chat e deixamos o teste decidir onde landar.
 *
 * Espelho mínimo de e2e/fixtures/auth.fixture.ts — copia o padrão
 * dev-auto-login mas omite a goto /pt/chat.
 */
import { test as base, expect, Page } from '@playwright/test'

let AUTH_DOMAIN = 'localhost'
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname
  }
} catch {
  console.warn(`Invalid PLAYWRIGHT_BASE_URL: "${process.env.PLAYWRIGHT_BASE_URL}"`)
}

export interface RecrutarAuthFixture {
  authenticatedPage: Page
}

async function ensureRealDevAuth(context: import('@playwright/test').BrowserContext) {
  const response = await context.request.get('/api/auth/ws-token', {
    failOnStatusCode: false,
  })
  if (!response.ok()) {
    const body = await response.text().catch(() => '<unreadable>')
    throw new Error(
      `recrutar-auth: /api/auth/ws-token ${response.status()}; body: ${body.slice(0, 200)}`,
    )
  }
}

export const test = base.extend<RecrutarAuthFixture>({
  authenticatedPage: async ({ page, context }, use) => {
    await context.addCookies([
      { name: 'lia_auth_method', value: 'jwt', domain: AUTH_DOMAIN, path: '/' },
    ])
    await ensureRealDevAuth(context)
    // No pre-navigation — let the test decide where to land.
    await use(page)
  },
})

export { expect }
