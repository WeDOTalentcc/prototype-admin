/**
 * Task #379 — Garantir que mensagens nunca somem quando o WebSocket está
 * fechando entre dois envios.
 *
 * Diferença para o guard-rail #383 (`unified-chat-ws-silent-drop.spec.ts`):
 *   - Lá o WS fica vivo mas "surdo" (engole o frame).
 *   - Aqui o WS responde normalmente à primeira mensagem, depois transita
 *     para CLOSING/CLOSED (cenário de reconexão / proxy edge derrubando o
 *     socket). Antes do fix da F2 em `useChatTransport.sendMessage`, o
 *     segundo envio era engolido em silêncio (readyState !== OPEN → return
 *     false, sem fallback) — a mensagem do usuário sumia e o spinner "LIA
 *     digitando" ficava preso.
 *   - Esperado: o segundo envio cai automaticamente no caminho REST e a
 *     resposta aparece normalmente.
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

test.describe('Unified Chat — WS fechando entre mensagens (Task #379)', () => {
  test('1ª msg via WS → socket fecha → 2ª msg deve cair no REST sem sumir', async ({ page, context }, testInfo) => {
    const consoleLines: string[] = []
    page.on('console', (m) => consoleLines.push(`[${m.type()}] ${m.text()}`))
    page.on('pageerror', (e) => consoleLines.push(`[pageerror] ${e.message}`))

    // Stub do WebSocket: responde corretamente à primeira mensagem (event
    // `thinking` + `message`), e depois muda `readyState` para CLOSING. A
    // partir daí, qualquer envio precisa cair no REST — caso contrário a
    // mensagem do usuário desaparece.
    await page.addInitScript(() => {
      ;(window as unknown as { __LIA_WS_RESPONSE_TIMEOUT_MS?: number }).__LIA_WS_RESPONSE_TIMEOUT_MS = 1500

      class ClosingAfterFirstSendWebSocket {
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
        private sendsServed = 0

        constructor(url: string | URL) {
          this.url = url.toString()
          setTimeout(() => {
            this.readyState = 1
            try { this.onopen?.(new Event('open')) } catch { /* swallow */ }
          }, 5)
        }
        send(_data: string | ArrayBufferLike | Blob | ArrayBufferView) {
          this.sendsServed += 1
          if (this.sendsServed === 1) {
            // Responde normalmente à primeira mensagem.
            setTimeout(() => {
              try {
                this.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify({ type: 'thinking' }),
                }))
                this.onmessage?.(new MessageEvent('message', {
                  data: JSON.stringify({
                    type: 'message',
                    content: 'Resposta WS da primeira mensagem.',
                  }),
                }))
              } catch { /* swallow */ }
              // Depois da primeira resposta, simula o socket entrando em
              // CLOSING (proxy edge derrubando, reconexão iminente, etc).
              this.readyState = 2 // CLOSING
            }, 30)
            return
          }
          // Qualquer envio subsequente nunca deveria chegar aqui — o cliente
          // precisa enxergar `readyState !== OPEN` e cair no REST. Se chegar,
          // o teste falha pelo restCalls=0 abaixo.
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
      ;(window as unknown as { WebSocket: unknown }).WebSocket = ClosingAfterFirstSendWebSocket
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
          content: 'Resposta REST de fallback (Task #379).',
          conversation_id: 'test-conv-379',
        }),
      })
    })

    await page.goto(CHAT_URL)
    await page.waitForLoadState('networkidle').catch(() => undefined)
    await page.waitForTimeout(1500)

    const input = await findInput(page)
    expect(input, 'input do chat unificado deve existir em /chat').not.toBeNull()
    if (!input) return

    // 1ª mensagem — vai pelo WS, recebe resposta normal.
    await input.click()
    await input.fill('primeira mensagem')
    await input.press('Enter')

    await page
      .locator('text=/Resposta WS da primeira mensagem/i')
      .first()
      .waitFor({ state: 'visible', timeout: 8000 })

    // 2ª mensagem — o socket está em CLOSING. Não pode sumir.
    await input.click()
    await input.fill('segunda mensagem após WS fechar')
    await input.press('Enter')

    const restBubble = page.locator('text=/Resposta REST de fallback \\(Task #379\\)/i').first()
    await restBubble.waitFor({ state: 'visible', timeout: 8000 })

    // Indicador "LIA digitando" não pode ficar preso depois do fallback.
    // Asserção *dura* — se sobrar spinner, o teste falha (esse é o sintoma
    // visível do bug que a Task #379 quer eliminar).
    const typingIndicator = page.locator('text=/LIA digitando|digitando/i').first()
    await expect(typingIndicator).toBeHidden({ timeout: 5000 })

    await page.screenshot({ path: 'e2e/screenshots/unified-chat-ws-closing-379.png', fullPage: true })
    await testInfo.attach('console.log', {
      body: consoleLines.join('\n') || '(empty)',
      contentType: 'text/plain',
    })

    expect(
      restCalls,
      'A 2ª mensagem deve ter sido reenviada via REST quando o WS estava em CLOSING.',
    ).toBeGreaterThan(0)
  })
})
