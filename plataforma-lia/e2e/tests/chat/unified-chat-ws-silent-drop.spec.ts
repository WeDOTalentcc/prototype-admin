/**
 * Guard-rail: Unified Chat — WS aceita o send mas nunca responde (Task #383, F2).
 *
 * Cenário do bug auditado em
 * `plataforma-lia/docs/audits/unified-chat-no-response-2026-04-17.md` (F2):
 *   - O WebSocket está "connected" do ponto de vista da UI.
 *   - `wsSend` é chamado, `ws.send()` retorna sem erro.
 *   - Mas o backend nunca emite `thinking`/`message` (frame engolido,
 *     proxy buferizou, ou socket fechou silenciosamente após o send).
 *   - Antes do fix: spinner "LIA digitando" eterno, nenhuma bolha.
 *   - Depois do fix: o watchdog em `useChatMessages` cai pro REST, surface
 *     a bolha "Conexão instável com a LIA. Tentando novamente..." e a
 *     resposta REST aparece em seguida.
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

test.describe('Unified Chat — WS silent drop (Task #383)', () => {
  test('WS conectado mas sem resposta deve cair no REST com bolha de aviso', async ({ page, context }, testInfo) => {
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

    // 1) Stub a classe `WebSocket` global ANTES de qualquer script da app rodar.
    //    O fake socket abre normalmente (transportMode passa a "ws", isConnected
    //    vira true), aceita `send()` sem erro, mas NUNCA dispara `onmessage`.
    //    Isso é exatamente o cenário F2: send aceito, zero respostas.
    // 2) Reduz o timeout do watchdog pra acelerar o teste sem mascarar a regressão.
    await page.addInitScript(() => {
      ;(window as unknown as { __LIA_WS_RESPONSE_TIMEOUT_MS?: number }).__LIA_WS_RESPONSE_TIMEOUT_MS = 1500

      class SilentWebSocket {
        url: string
        readyState = 0
        onopen: ((ev: Event) => unknown) | null = null
        onmessage: ((ev: MessageEvent) => unknown) | null = null
        onerror: ((ev: Event) => unknown) | null = null
        onclose: ((ev: CloseEvent) => unknown) | null = null
        binaryType: BinaryType = 'blob'
        bufferedAmount = 0
        extensions = ''
        protocol = ''
        static readonly CONNECTING = 0
        static readonly OPEN = 1
        static readonly CLOSING = 2
        static readonly CLOSED = 3
        readonly CONNECTING = 0
        readonly OPEN = 1
        readonly CLOSING = 2
        readonly CLOSED = 3

        constructor(url: string | URL) {
          this.url = url.toString()
          setTimeout(() => {
            this.readyState = 1
            try { this.onopen?.(new Event('open')) } catch { /* swallow */ }
          }, 5)
        }
        send(_data: string | ArrayBufferLike | Blob | ArrayBufferView) {
          // Engole o frame deliberadamente — backend "nunca recebeu" / nunca responde.
        }
        close() {
          this.readyState = 3
          try { this.onclose?.(new CloseEvent('close', { code: 1000 })) } catch { /* swallow */ }
        }
        addEventListener(type: string, fn: EventListenerOrEventListenerObject) {
          const handler = typeof fn === 'function' ? fn : (e: Event) => fn.handleEvent(e)
          ;(this as unknown as Record<string, unknown>)[`on${type}`] = handler
        }
        removeEventListener() { /* no-op */ }
        dispatchEvent() { return true }
      }
      ;(window as unknown as { WebSocket: unknown }).WebSocket = SilentWebSocket
    })

    // O ws-token do dev-auto-login pode falhar em CI; respondemos um token fake
    // pra que `useChatSocket` libere o handshake com nosso fake WS.
    await context.route('**/api/auth/ws-token', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'fake-test-token', authMode: 'dev-auto-login' }),
      }),
    )

    // O fallback REST deve devolver uma resposta válida — assim, quando o
    // watchdog disparar, vemos a bolha REST aparecer (prova que o fallback
    // funcionou de ponta a ponta).
    let restCalls = 0
    await context.route('**/api/backend-proxy/chat/message', (route) => {
      restCalls += 1
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          content: 'Resposta REST de fallback (Task #383).',
          conversation_id: 'test-conv-383',
        }),
      })
    })

    await page.goto(CHAT_URL)
    await page.waitForLoadState('networkidle').catch(() => undefined)
    await page.waitForTimeout(1500)

    const input = await findInput(page)
    expect(input, 'input do chat unificado deve existir em /chat').not.toBeNull()
    if (!input) return

    await input.click()
    await input.fill('oi')
    await input.press('Enter')

    // O watchdog está configurado pra 1500ms; espera ~6s pelo fallback.
    const fallbackBubble = page.locator(
      'text=/Conexão instável|Resposta REST de fallback|Tentando novamente/i',
    ).first()

    let appeared = false
    try {
      await fallbackBubble.waitFor({ state: 'visible', timeout: 8000 })
      appeared = true
    } catch {
      appeared = false
    }

    await page.screenshot({ path: 'e2e/screenshots/unified-chat-ws-silent-drop-383.png', fullPage: true })
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
      'Quando o WS aceita o send mas nunca responde, o watchdog F2 deve renderizar a bolha de aviso e/ou a resposta REST de fallback.',
    ).toBe(true)
    expect(restCalls, 'O fallback REST deve ter sido acionado pelo watchdog F2.').toBeGreaterThan(0)
  })

  test('WS vivo (pong keep-alive) mas sem `thinking`/`message` ainda deve cair no REST', async ({ page, context }, testInfo) => {
    const consoleLines: string[] = []
    page.on('console', (m) => consoleLines.push(`[${m.type()}] ${m.text()}`))
    page.on('pageerror', (e) => consoleLines.push(`[pageerror] ${e.message}`))

    // Cenário "false-negative" levantado no code review do #383: o socket
    // continua emitindo `pong` periodicamente (parece vivo), mas nunca emite
    // `thinking`/`message` para o último envio. O watchdog NÃO pode contar
    // `pong` como prova de resposta — caso contrário o silent drop continua.
    await page.addInitScript(() => {
      ;(window as unknown as { __LIA_WS_RESPONSE_TIMEOUT_MS?: number }).__LIA_WS_RESPONSE_TIMEOUT_MS = 1500

      class PongOnlyWebSocket {
        url: string
        readyState = 0
        onopen: ((ev: Event) => unknown) | null = null
        onmessage: ((ev: MessageEvent) => unknown) | null = null
        onerror: ((ev: Event) => unknown) | null = null
        onclose: ((ev: CloseEvent) => unknown) | null = null
        binaryType: BinaryType = 'blob'
        bufferedAmount = 0
        extensions = ''
        protocol = ''
        static readonly CONNECTING = 0
        static readonly OPEN = 1
        static readonly CLOSING = 2
        static readonly CLOSED = 3
        readonly CONNECTING = 0
        readonly OPEN = 1
        readonly CLOSING = 2
        readonly CLOSED = 3
        private pongTimer: ReturnType<typeof setInterval> | null = null

        constructor(url: string | URL) {
          this.url = url.toString()
          setTimeout(() => {
            this.readyState = 1
            try { this.onopen?.(new Event('open')) } catch { /* swallow */ }
            // Emite `pong` a cada 200ms — socket "vivo mas surdo" pra mensagens.
            this.pongTimer = setInterval(() => {
              if (this.readyState !== 1) return
              try {
                this.onmessage?.(new MessageEvent('message', { data: JSON.stringify({ type: 'pong' }) }))
              } catch { /* swallow */ }
            }, 200)
          }, 5)
        }
        send(_data: string | ArrayBufferLike | Blob | ArrayBufferView) {
          // Engole o frame deliberadamente.
        }
        close() {
          this.readyState = 3
          if (this.pongTimer) { clearInterval(this.pongTimer); this.pongTimer = null }
          try { this.onclose?.(new CloseEvent('close', { code: 1000 })) } catch { /* swallow */ }
        }
        addEventListener(type: string, fn: EventListenerOrEventListenerObject) {
          const handler = typeof fn === 'function' ? fn : (e: Event) => fn.handleEvent(e)
          ;(this as unknown as Record<string, unknown>)[`on${type}`] = handler
        }
        removeEventListener() { /* no-op */ }
        dispatchEvent() { return true }
      }
      ;(window as unknown as { WebSocket: unknown }).WebSocket = PongOnlyWebSocket
    })

    await context.route('**/api/auth/ws-token', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'fake-test-token', authMode: 'dev-auto-login' }),
      }),
    )

    let restCalls = 0
    await context.route('**/api/backend-proxy/chat/message', (route) => {
      restCalls += 1
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          content: 'Resposta REST de fallback (pong-only) (Task #383).',
          conversation_id: 'test-conv-383-pong',
        }),
      })
    })

    await page.goto(CHAT_URL)
    await page.waitForLoadState('networkidle').catch(() => undefined)
    await page.waitForTimeout(1500)

    const input = await findInput(page)
    expect(input, 'input do chat unificado deve existir em /chat').not.toBeNull()
    if (!input) return

    await input.click()
    await input.fill('oi pong')
    await input.press('Enter')

    const fallbackBubble = page.locator(
      'text=/Conexão instável|Resposta REST de fallback|Tentando novamente/i',
    ).first()

    let appeared = false
    try {
      await fallbackBubble.waitFor({ state: 'visible', timeout: 8000 })
      appeared = true
    } catch {
      appeared = false
    }

    await page.screenshot({ path: 'e2e/screenshots/unified-chat-ws-pong-only-383.png', fullPage: true })
    await testInfo.attach('console.log', {
      body: consoleLines.join('\n') || '(empty)',
      contentType: 'text/plain',
    })

    expect(
      appeared,
      'Mesmo com WS vivo (pong keep-alive), a ausência de `thinking`/`message` deve disparar o fallback F2.',
    ).toBe(true)
    expect(restCalls, 'Fallback REST deve ter sido chamado mesmo com pong em loop.').toBeGreaterThan(0)
  })
})
