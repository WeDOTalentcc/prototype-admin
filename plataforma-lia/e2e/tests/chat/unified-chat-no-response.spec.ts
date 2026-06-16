/**
 * Guard-rail: Unified Chat — "LIA não responde" (Task #374).
 *
 * Reproduz o bug auditado em
 * `plataforma-lia/docs/audits/unified-chat-no-response-2026-04-17.md`.
 *
 * Cenário: o backend (ou o middleware Next em modo dev quebrado) devolve um
 * payload sem `content` no POST /api/backend-proxy/chat/message. O front
 * `useChatMessages.sendMessage` (REST branch) hoje SUMA com a resposta
 * silenciosamente — nenhuma bolha de assistente é renderizada.
 *
 * Este teste:
 * 1. Intercepta a chamada do proxy REST e devolve um 401 idêntico ao que o
 *    `middleware.ts` (denyAccess) gera quando `dev-auto-login` falha.
 * 2. Envia "oi" no chat unificado.
 * 3. Espera por uma mensagem de assistente OU por uma mensagem de erro
 *    visível na lista.
 * 4. FALHA hoje (silent drop). Passa quando o fix F1 do plano for aplicado
 *    (qualquer JSON sem `content` deve virar mensagem de erro renderizada).
 */
import { test, expect, type Page } from '@playwright/test'

const CHAT_URL = '/chat'

const INPUT_SELECTORS = [
  'textarea[aria-label="Mensagem para a LIA"]',
  'textarea[aria-label*="LIA" i]',
  'textarea[placeholder*="Pergunte" i]',
  'textarea[placeholder*="Envie" i]',
]

async function findInput(page: Page) {
  for (const sel of INPUT_SELECTORS) {
    const loc = page.locator(sel).first()
    if (await loc.isVisible({ timeout: 4000 }).catch(() => false)) return loc
  }
  return null
}

test.describe('Unified Chat — LIA não responde (Task #374)', () => {
  test('REST sem content (401 do middleware) deve gerar mensagem visível, não silent drop', async ({ page, context }, testInfo) => {
    const consoleLines: string[] = []
    const networkLines: string[] = []
    page.on('console', (m) => consoleLines.push(`[${m.type()}] ${m.text()}`))
    page.on('pageerror', (e) => consoleLines.push(`[pageerror] ${e.message}`))
    page.on('request', (r) => {
      if (r.url().includes('/api/')) networkLines.push(`→ ${r.method()} ${r.url()}`)
    })
    page.on('response', (r) => {
      if (r.url().includes('/api/')) networkLines.push(`← ${r.status()} ${r.url()}`)
    })

    // Bloqueia o WS para forçar o ramo REST de `useChatMessages.sendMessage`.
    await context.route('**/api/v1/ws/chat/**', (route) => route.abort())

    // Simula EXATAMENTE o que `src/middleware.ts:99-103` (denyAccess) devolve
    // quando `dev-auto-login` falha em ambiente dev — payload sem `content`,
    // sem `message_metadata`, sem `needs_clarification`. É esse shape que faz
    // `useChatMessages` cair no "silent drop" hoje.
    await context.route('**/api/backend-proxy/chat/message', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Authentication required' }),
      }),
    )

    await page.goto(CHAT_URL)
    await page.waitForLoadState('networkidle').catch(() => undefined)
    await page.waitForTimeout(1500)

    const input = await findInput(page)
    expect(input, 'input do chat unificado deve existir em /chat').not.toBeNull()
    if (!input) return

    await input.click()
    await input.fill('oi')
    await input.press('Enter')

    // O bug: nada de assistente nem de erro renderizado. Esperamos qualquer
    // texto que indique que o sistema reagiu — uma bolha LIA OU um banner de
    // erro visível na lista de mensagens.
    const reply = page.locator(
      '[data-message-role="assistant"], .lia-markdown-content, [data-testid="lia-message"], text=/Erro|autentica|login|servidor|tente novamente/i',
    ).first()

    let appeared = false
    try {
      await reply.waitFor({ state: 'visible', timeout: 8000 })
      appeared = true
    } catch {
      appeared = false
    }

    await page.screenshot({ path: 'e2e/screenshots/unified-chat-no-response-374.png', fullPage: true })
    await testInfo.attach('console.log', {
      body: consoleLines.join('\n') || '(empty)',
      contentType: 'text/plain',
    })
    await testInfo.attach('network.log', {
      body: networkLines.join('\n') || '(empty)',
      contentType: 'text/plain',
    })

    expect(
      appeared,
      'LIA deve renderizar resposta OU mensagem de erro quando o proxy devolve JSON sem `content` — silent drop é o bug auditado em #374',
    ).toBe(true)
  })
})
