/**
 * Kanban Auth Fixture
 * Faz login real no backend para obter JWT válido.
 * Uso exclusivo nos testes de kanban.
 */
import { test as base, expect, Page, BrowserContext } from '@playwright/test'

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'

let AUTH_DOMAIN = 'localhost'
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname
  }
} catch {
  AUTH_DOMAIN = 'localhost'
}

const DEMO_EMAIL    = process.env.E2E_EMAIL    || 'demo@wedotalent.com'
const DEMO_PASSWORD = process.env.E2E_PASSWORD || 'demo123'

// Job IDs conhecidos com seed data
export const KANBAN_JOBS = {
  productManager: {
    id:    '406731ad-388f-5ea5-a0b6-bdb6dadf186e',
    title: 'Product Manager',
    url:   '/pt/jobs/406731ad-388f-5ea5-a0b6-bdb6dadf186e',
  },
  techLead: {
    id:    'e603b68b-febd-50e8-84e7-7568a28fede1',
    title: 'Tech Lead — Backend',
    url:   '/pt/jobs/e603b68b-febd-50e8-84e7-7568a28fede1',
  },
}

async function getRealToken(): Promise<string | null> {
  try {
    const res = await fetch(`${BASE}/api/backend-proxy/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
      signal:  AbortSignal.timeout(10000),
    })
    if (!res.ok) {
      console.warn(`  ⚠️  Login retornou ${res.status} — tentando fallback interno`)
      // Tenta direto no FastAPI (porta 8001 via backend-proxy)
      const res2 = await fetch(`${BASE}/api/backend-proxy/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-Internal': '1' },
        body:    JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
      }).catch(() => null)
      if (!res2?.ok) return null
      const d2 = await res2.json()
      return d2.access_token || d2?.data?.access_token || null
    }
    const data = await res.json()
    return data.access_token || data?.data?.access_token || null
  } catch (err) {
    console.warn(`  ⚠️  Falha ao obter token real: ${err}`)
    return null
  }
}

async function setAuthCookies(context: BrowserContext, token: string) {
  await context.addCookies([
    { name: 'lia_access_token', value: token,  domain: AUTH_DOMAIN, path: '/' },
    { name: 'lia_auth_method',  value: 'jwt',  domain: AUTH_DOMAIN, path: '/' },
  ])
}

export interface KanbanAuthFixture {
  authenticatedPage: Page
  kanbanPage: (jobKey?: keyof typeof KANBAN_JOBS) => Promise<Page>
}

export const test = base.extend<KanbanAuthFixture>({
  authenticatedPage: async ({ page, context }, use) => {
    const token = await getRealToken()
    if (token) {
      await setAuthCookies(context, token)
      console.log('  ✓ Token real obtido e configurado')
    } else {
      // Fallback: token fake (testes sem dados reais)
      await context.addCookies([
        { name: 'lia_access_token', value: 'e2e-test-token', domain: AUTH_DOMAIN, path: '/' },
        { name: 'lia_auth_method',  value: 'jwt',            domain: AUTH_DOMAIN, path: '/' },
      ])
      console.warn('  ⚠️  Usando token fake — dados podem estar vazios')
    }
    await page.goto('/pt/jobs/406731ad-388f-5ea5-a0b6-bdb6dadf186e')
    await page.waitForLoadState('domcontentloaded')
    // Aguarda o loading do kanban terminar — o skeleton usa 'animate-pulse' e desaparece quando os dados carregam
    // Espera kanban-column (dados reais) OU tela vazia (0 candidatos)
    await page.waitForSelector('[data-testid="kanban-column"]', { timeout: 40000 }).catch(() => {})
    await use(page)
  },

  kanbanPage: async ({ page, context }, use) => {
    const token = await getRealToken()
    if (token) await setAuthCookies(context, token)

    const go = async (jobKey: keyof typeof KANBAN_JOBS = 'productManager') => {
      const job = KANBAN_JOBS[jobKey]
      await page.goto(job.url)
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('[data-testid="kanban-column"]', { timeout: 40000 }).catch(() => {})
      return page
    }
    await use(go)
  },
})

export { expect }
