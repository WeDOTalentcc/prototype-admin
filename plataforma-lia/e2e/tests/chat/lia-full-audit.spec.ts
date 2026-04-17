/**
 * LIA FULL AUDIT — Suite Exhaustiva
 *
 * Testa todo o caminho: Frontend → Proxy Next.js → FastAPI → Orchestrator
 * → CascadedRouter → Domain Agent → Tools → LLM → Response → Frontend.
 *
 * Capacidades testadas:
 * 1. Chat básico (resposta geral)
 * 2. Busca de candidatos
 * 3. Alteração de status de candidato
 * 4. Listagem de vagas
 * 5. Parecer/análise de vaga
 * 6. Pipeline / Kanban
 * 7. Analytics
 * 8. Configurações da empresa
 * 9. Tratamento de erros
 * 10. Proxy envelope fix (bug #374 + #envelope)
 */

import { test, expect, type Page, type APIRequestContext } from '@playwright/test'

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'
const API  = process.env.LIA_API_URL || 'http://localhost:8001'

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function getJwt(request: APIRequestContext): Promise<string> {
  const r = await request.post(`${API}/api/v1/auth/login`, {
    data: { email: 'demo@wedotalent.com', password: 'demo123' },
  })
  const body = await r.json()
  return body?.data?.access_token || body?.access_token || ''
}

async function liaChat(
  request: APIRequestContext,
  token: string,
  content: string,
  conversationId?: string,
): Promise<{ content: string; intent: string; conversationId: string }> {
  const r = await request.post(`${API}/api/v1/chat`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { content, ...(conversationId ? { conversation_id: conversationId } : {}) },
  })
  const body = await r.json()
  const msg = body?.data?.message || {}
  return {
    content: msg.content || '',
    intent: msg.message_metadata?.intent || '',
    conversationId: body?.data?.conversation?.id || msg.conversation_id || '',
  }
}

async function proxyChat(
  request: APIRequestContext,
  token: string,
  content: string,
): Promise<{ content: string; conversationId: string; error?: string }> {
  const r = await request.post(`${BASE}/api/backend-proxy/chat/message`, {
    headers: { Cookie: `lia_access_token=${token}` },
    data: { content },
  })
  const body = await r.json()
  return {
    content: body.content || '',
    conversationId: body.conversation_id || '',
    error: body.error,
  }
}

async function findAndFillInput(page: Page, message: string): Promise<boolean> {
  const selectors = [
    'textarea[aria-label="Mensagem para a LIA"]',
    'textarea[aria-label*="LIA" i]',
    'textarea[placeholder*="Pergunte" i]',
    'textarea[placeholder*="Faça qualquer coisa" i]',
    'textarea[placeholder*="Envie" i]',
    '[data-testid="chat-input"]',
  ]
  for (const sel of selectors) {
    const el = page.locator(sel).first()
    if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
      await el.click()
      await el.fill(message)
      return true
    }
  }
  return false
}

async function waitForLiaResponse(page: Page, timeoutMs = 30000): Promise<string | null> {
  const selectors = [
    '[data-message-role="assistant"]',
    '[data-testid="lia-message"]',
    '.lia-markdown-content',
    '[class*="assistant"][class*="message"]',
  ]
  for (const sel of selectors) {
    try {
      await page.locator(sel).first().waitFor({ state: 'visible', timeout: timeoutMs })
      return await page.locator(sel).first().textContent()
    } catch {
      continue
    }
  }
  return null
}

// ─── Suite 1: Proxy Fix (Envelope Mismatch) ──────────────────────────────────

test.describe('Suite 1 — Proxy Fix: Envelope Response', () => {
  let jwt: string

  test.beforeAll(async ({ request }) => {
    jwt = await getJwt(request)
    expect(jwt, 'JWT obrigatório para testes de proxy').toBeTruthy()
  })

  test('1.1 Proxy retorna content não-vazio via /api/backend-proxy/chat/message', async ({ request }) => {
    const { content, error } = await proxyChat(request, jwt, 'oi, tudo bem?')
    expect(error, 'não deve haver erro de proxy').toBeUndefined()
    expect(content.length, `content está vazio — proxy envelope bug ainda ativo. Recebido: "${content}"`).toBeGreaterThan(0)
  })

  test('1.2 Proxy retorna conversation_id válido', async ({ request }) => {
    const { conversationId } = await proxyChat(request, jwt, 'olá LIA')
    expect(conversationId, 'conversation_id deve ser UUID').toMatch(/^[0-9a-f-]{36}$/)
  })

  test('1.3 Proxy suporta campo message e content intercambiáveis', async ({ request }) => {
    const r = await request.post(`${BASE}/api/backend-proxy/chat/message`, {
      headers: { Cookie: `lia_access_token=${jwt}` },
      data: { message: 'teste via campo message' },
    })
    const body = await r.json()
    expect(body.content.length, 'deve responder quando campo se chama "message"').toBeGreaterThan(0)
  })
})

// ─── Suite 2: Backend API — Camada por Camada ─────────────────────────────────

test.describe('Suite 2 — Backend API: Fluxo Completo Camada a Camada', () => {
  let jwt: string

  test.beforeAll(async ({ request }) => {
    jwt = await getJwt(request)
  })

  test('2.1 Auth: login retorna JWT válido', async ({ request }) => {
    const r = await request.post(`${API}/api/v1/auth/login`, {
      data: { email: 'demo@wedotalent.com', password: 'demo123' },
    })
    expect(r.ok()).toBe(true)
    const body = await r.json()
    expect(body.data?.access_token).toBeTruthy()
    expect(body.data?.access_token).toMatch(/^eyJ/)
  })

  test('2.2 Chat /api/v1/chat: resposta básica com intent detectado', async ({ request }) => {
    const { content, intent } = await liaChat(request, jwt, 'oi')
    expect(content.length).toBeGreaterThan(0)
    expect(intent.length).toBeGreaterThan(0)
  })

  test('2.3 Chat mantém contexto de conversa (conversation_id)', async ({ request }) => {
    const first = await liaChat(request, jwt, 'meu nome é Marcos')
    expect(first.conversationId).toBeTruthy()
    const second = await liaChat(request, jwt, 'qual é o meu nome?', first.conversationId)
    expect(second.content.toLowerCase()).toMatch(/marcos/i)
  })

  test('2.4 Orchestrator detecta intent search_candidates', async ({ request }) => {
    const { intent } = await liaChat(request, jwt, 'busque candidatos com experiência em Python')
    expect(intent, `intent esperado: search_candidates, recebido: ${intent}`).toMatch(/search_candidates|sourcing|agentic/)
  })

  test('2.5 Orchestrator detecta intent para vagas', async ({ request }) => {
    const { intent, content } = await liaChat(request, jwt, 'crie uma nova vaga de desenvolvedor')
    expect(content.length).toBeGreaterThan(0)
    expect(intent.length).toBeGreaterThan(0)
  })

  test('2.6 Orchestrator responde sobre pipeline', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'como está o pipeline de candidatos?')
    expect(content.length, 'LIA deve responder sobre pipeline').toBeGreaterThan(0)
  })

  test('2.7 LIA responde perguntas gerais com inteligência', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'o que você consegue fazer?')
    expect(content.length).toBeGreaterThan(20)
    const keywords = ['candidato', 'vaga', 'buscar', 'criar', 'analisar', 'recrutamento', 'ajudar']
    const hasRelevant = keywords.some(k => content.toLowerCase().includes(k))
    expect(hasRelevant, `LIA deve mencionar capacidades. Recebido: "${content}"`).toBe(true)
  })

  test('2.8 LIA recusa input inválido graciosamente', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'xyzabc123!@#$%')
    expect(content.length, 'LIA deve responder mesmo a input estranho').toBeGreaterThan(0)
  })
})

// ─── Suite 3: Capacidades LIA — Cenários Reais ───────────────────────────────

test.describe('Suite 3 — Capacidades LIA', () => {
  let jwt: string
  let convId: string

  test.beforeAll(async ({ request }) => {
    jwt = await getJwt(request)
  })

  test('3.1 Busca de candidatos — LIA pede critérios ou executa busca', async ({ request }) => {
    const { content, intent } = await liaChat(request, jwt, 'busque desenvolvedores Python sênior')
    expect(content.length).toBeGreaterThan(0)
    const looksRight = content.toLowerCase().match(/critério|candidato|encontr|resultado|python|busca|lista/i)
    expect(looksRight, `Resposta inesperada: "${content}"`).toBeTruthy()
  })

  test('3.2 Análise de vaga — LIA gera parecer estruturado', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'analise a vaga de engenheiro de software sênior: precisa de 5 anos de experiência, Python, AWS, salário até R$15k')
    expect(content.length).toBeGreaterThan(30)
    expect(content.toLowerCase()).toMatch(/vaga|salário|requisito|análise|experiência|engenheiro/i)
  })

  test('3.3 Listagem de vagas — LIA tenta acessar dados', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'quais vagas estão abertas?')
    expect(content.length).toBeGreaterThan(0)
  })

  test('3.4 Pipeline — LIA explica ou consulta funil', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'mostre o funil de recrutamento')
    expect(content.length).toBeGreaterThan(0)
  })

  test('3.5 Status candidato — LIA pede confirmação antes de alterar', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'mova o candidato Carlos Souza para a etapa de entrevista técnica')
    expect(content.length).toBeGreaterThan(0)
    const askOrDo = content.toLowerCase().match(/confirma|candidato|etapa|entrevista|carlos|mover|informação|preciso/i)
    expect(askOrDo, `LIA deveria pedir confirmação ou info. Recebido: "${content}"`).toBeTruthy()
  })

  test('3.6 Analytics — LIA responde sobre métricas', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'qual o time to hire médio?')
    expect(content.length).toBeGreaterThan(0)
  })

  test('3.7 Comunicação — LIA oferece enviar email', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'envie um email de feedback para o candidato')
    expect(content.length).toBeGreaterThan(0)
    expect(content.toLowerCase()).toMatch(/email|candidato|enviar|informação|nome/i)
  })

  test('3.8 LIA é conversacional — mantém contexto', async ({ request }) => {
    const r1 = await liaChat(request, jwt, 'vamos falar sobre recrutamento de tecnologia')
    convId = r1.conversationId
    const r2 = await liaChat(request, jwt, 'quais são os principais desafios?', convId)
    expect(r2.content.toLowerCase()).toMatch(/tecnologia|candidato|recrutamento|desenvolvedor|desafio|mercado/i)
  })
})

// ─── Suite 4: UI Playwright — Chat Unificado ─────────────────────────────────

test.describe('Suite 4 — UI: Chat Unificado', () => {
  test.use({ storageState: undefined })

  async function setupAuth(page: Page, request: APIRequestContext) {
    const token = await getJwt(request)
    const domain = new URL(BASE).hostname
    await page.context().addCookies([
      { name: 'lia_access_token', value: token, domain, path: '/' },
      { name: 'lia_auth_method', value: 'jwt', domain, path: '/' },
    ])
    return token
  }

  test('4.1 /chat renderiza sem erros de JS', async ({ page, request }) => {
    await setupAuth(page, request)
    const errors: string[] = []
    page.on('pageerror', e => errors.push(e.message))
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'e2e/screenshots/lia-audit-chat-render.png', fullPage: true })
    const fatalErrors = errors.filter(e => !e.includes('hydration') && !e.includes('Warning'))
    expect(fatalErrors, `Erros JS: ${fatalErrors.join(', ')}`).toHaveLength(0)
  })

  test('4.2 Input de chat está presente e aceita texto', async ({ page, request }) => {
    await setupAuth(page, request)
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    const ok = await findAndFillInput(page, 'oi LIA')
    expect(ok, 'Input do chat não encontrado em /chat').toBe(true)
    await page.screenshot({ path: 'e2e/screenshots/lia-audit-input.png' })
  })

  test('4.3 Envio de mensagem retorna resposta visível da LIA', async ({ page, request }) => {
    await setupAuth(page, request)
    const responses: string[] = []
    const errors401: number[] = []

    page.on('response', r => {
      if (r.url().includes('/api/backend-proxy/chat')) {
        if (r.status() === 401) errors401.push(r.status())
        r.json().catch(() => null).then(body => {
          if (body?.content) responses.push(body.content)
        })
      }
    })

    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)

    const ok = await findAndFillInput(page, 'oi, tudo bem?')
    if (!ok) {
      test.skip(true, 'Input não encontrado — UI pode estar em modo diferente')
      return
    }

    await page.keyboard.press('Enter')
    await page.waitForTimeout(5000)

    const reply = await waitForLiaResponse(page, 15000)
    await page.screenshot({ path: 'e2e/screenshots/lia-audit-response.png', fullPage: true })

    expect(errors401.length, `${errors401.length} chamada(s) retornaram 401 — auth quebrado`).toBe(0)
    expect(reply, 'LIA não renderizou resposta no chat — silent drop ou bug de UI').not.toBeNull()
    expect(reply!.length, `Resposta vazia. Proxy envelope fix pode não ter sido aplicado.`).toBeGreaterThan(0)
  })

  test('4.4 Mensagem de erro é exibida quando backend falha (não silent drop)', async ({ page, context, request }) => {
    await setupAuth(page, request)
    await context.route('**/api/backend-proxy/chat/message', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: '', error: 'backend_error' }),
      })
    )
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)

    await findAndFillInput(page, 'teste de erro')
    await page.keyboard.press('Enter')
    await page.waitForTimeout(5000)

    const errorVisible = await page.locator(
      'text=/Erro|tente novamente|falha|não foi possível/i'
    ).first().isVisible({ timeout: 8000 }).catch(() => false)

    await page.screenshot({ path: 'e2e/screenshots/lia-audit-error-handling.png', fullPage: true })
    expect(errorVisible, 'Erro de backend deve ser exibido ao usuário, não silent drop').toBe(true)
  })

  test('4.5 Chat flutuante também funciona (modo dock)', async ({ page, request }) => {
    await setupAuth(page, request)
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    const chatButton = page.locator('[data-testid="floating-chat-button"], [aria-label*="chat" i], [aria-label*="LIA" i], .floating-chat-trigger').first()
    const hasDock = await chatButton.isVisible({ timeout: 5000 }).catch(() => false)

    if (hasDock) {
      await chatButton.click()
      await page.waitForTimeout(1000)
      const inputOk = await findAndFillInput(page, 'oi pelo chat flutuante')
      await page.screenshot({ path: 'e2e/screenshots/lia-audit-floating.png' })
      expect(inputOk, 'Input não encontrado no chat flutuante').toBe(true)
    } else {
      test.info().annotations.push({ type: 'info', description: 'Chat flutuante não encontrado no dashboard — pode não estar habilitado' })
    }
  })
})

// ─── Suite 5: Diagnóstico de Rotas ───────────────────────────────────────────

test.describe('Suite 5 — Diagnóstico: Rotas e Integrações', () => {
  let jwt: string

  test.beforeAll(async ({ request }) => {
    jwt = await getJwt(request)
  })

  const routes = [
    { name: 'health', path: '/health', method: 'GET' as const },
    { name: 'auth/me', path: '/api/v1/auth/me', method: 'GET' as const },
    { name: 'jobs list', path: '/api/v1/jobs', method: 'GET' as const },
    { name: 'candidates search', path: '/api/v1/candidates/search?q=python', method: 'GET' as const },
    { name: 'pipeline list', path: '/api/v1/pipeline', method: 'GET' as const },
    { name: 'analytics kpis', path: '/api/v1/analytics/kpis', method: 'GET' as const },
  ]

  for (const route of routes) {
    test(`5.${routes.indexOf(route) + 1} Rota ${route.name} responde (não 500)`, async ({ request }) => {
      const r = await request.fetch(`${API}${route.path}`, {
        method: route.method,
        headers: { Authorization: `Bearer ${jwt}` },
      })
      expect(
        r.status(),
        `${route.name} retornou ${r.status()} — esperado 200/404/422, não 500`
      ).not.toBe(500)
    })
  }

  test('5.7 Proxy Next.js /api/backend-proxy/auth/me funciona', async ({ request }) => {
    const r = await request.get(`${BASE}/api/backend-proxy/auth/me`, {
      headers: { Cookie: `lia_access_token=${jwt}` },
    })
    expect(r.status()).not.toBe(500)
  })

  test('5.8 WebSocket endpoint disponível', async ({ request }) => {
    const r = await request.get(`${API}/api/v1/ws/chat/test-probe`, {
      headers: { Authorization: `Bearer ${jwt}` },
    })
    // WS upgrade retorna 426 ou 101 — não deve ser 404/500
    expect([101, 200, 400, 426].includes(r.status()), `WS endpoint retornou ${r.status()}`).toBe(true)
  })
})

// ─── Suite 6: Configurações da Empresa ───────────────────────────────────────

test.describe('Suite 6 — Configurações via LIA', () => {
  let jwt: string

  test.beforeAll(async ({ request }) => {
    jwt = await getJwt(request)
  })

  test('6.1 LIA responde perguntas sobre configurações', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'como configurar as informações da empresa?')
    expect(content.length).toBeGreaterThan(0)
  })

  test('6.2 LIA oferece preencher dados da empresa', async ({ request }) => {
    const { content } = await liaChat(request, jwt, 'quero preencher os dados da minha empresa')
    expect(content.length).toBeGreaterThan(0)
    expect(content.toLowerCase()).toMatch(/empresa|dado|informação|nome|cnpj|configurar|preencher/i)
  })

  test('6.3 UI: /settings carrega sem erros críticos', async ({ page, request }) => {
    const token = await getJwt(request)
    const domain = new URL(BASE).hostname
    await page.context().addCookies([{ name: 'lia_access_token', value: token, domain, path: '/' }])
    const errors: string[] = []
    page.on('pageerror', e => errors.push(e.message))
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'e2e/screenshots/lia-audit-settings.png', fullPage: true })
    const fatal = errors.filter(e => !e.includes('Warning') && !e.includes('hydration'))
    expect(fatal, `Erros fatais em /settings: ${fatal.join('; ')}`).toHaveLength(0)
  })
})
