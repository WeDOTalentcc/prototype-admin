/**
 * Test Suite: Unified Chat — Auditoria Técnica (Task #292)
 *
 * Cobre: abertura de /chat, envio de mensagem, indicador "LIA digitando",
 * slash commands, fallback WS→SSE/REST e transição entre modos
 * (sidebar / floating / fullscreen).
 *
 * Observação: este arquivo NÃO usa a fixture `authenticatedPage`
 * (que injeta um token JWT fake rejeitado pelo backend). Em vez disso,
 * deixa o Next.js acionar o caminho `dev-auto-login` no endpoint
 * `/api/auth/ws-token`, que faz login demo contra o backend e devolve
 * um JWT real — condição necessária para o handshake WS completar.
 *
 * Cada teste anexa evidência (console + network log) via testInfo.attach
 * para facilitar análise de auditoria.
 */
import { test, expect, type Page, type TestInfo } from '@playwright/test'

const CHAT_URL = '/chat'

const INPUT_SELECTORS = [
  'textarea[aria-label="Mensagem para a LIA"]',
  'input[aria-label="Mensagem para a LIA"]',
  'textarea[placeholder*="Envie mensagem"]',
  'textarea[placeholder*="Pergunte"]',
]

async function findInput(page: Page) {
  for (const sel of INPUT_SELECTORS) {
    const loc = page.locator(sel).first()
    if (await loc.isVisible({ timeout: 3000 }).catch(() => false)) return loc
  }
  return null
}

/**
 * Instala listeners de console e network ANTES da navegação e devolve
 * um finalizer que, ao ser chamado, anexa os logs capturados ao relatório
 * do teste.
 */
function instrumentPage(page: Page, testInfo: TestInfo) {
  const consoleLines: string[] = []
  const networkLines: string[] = []

  page.on('console', (msg) => {
    consoleLines.push(`[${msg.type()}] ${msg.text()}`)
  })
  page.on('pageerror', (err) => {
    consoleLines.push(`[pageerror] ${err.message}`)
  })
  page.on('request', (req) => {
    const url = req.url()
    if (url.includes('/api/') || url.includes('/ws/')) {
      networkLines.push(`→ ${req.method()} ${url}`)
    }
  })
  page.on('response', (res) => {
    const url = res.url()
    if (url.includes('/api/') || url.includes('/ws/')) {
      networkLines.push(`← ${res.status()} ${res.url()}`)
    }
  })
  page.on('websocket', (ws) => {
    networkLines.push(`⇅ WS open ${ws.url()}`)
    ws.on('close', () => networkLines.push(`⇅ WS close ${ws.url()}`))
  })

  return async () => {
    await testInfo.attach('console.log', {
      body: consoleLines.join('\n') || '(no console output)',
      contentType: 'text/plain',
    })
    await testInfo.attach('network.log', {
      body: networkLines.join('\n') || '(no /api/ or /ws/ traffic)',
      contentType: 'text/plain',
    })
  }
}

async function gotoChat(page: Page) {
  await page.goto(CHAT_URL)
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(2500)
}

test.describe('Unified Chat — Auditoria (Task #292)', () => {
  test('TC-UC-001: /chat carrega e expõe data-chat-mode', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-open.png', fullPage: true })
    const chatRoot = page.locator('[data-chat-mode]').first()
    await expect(chatRoot, 'UnifiedChat root com data-chat-mode deve renderizar').toBeVisible({ timeout: 10000 })
    const mode = await chatRoot.getAttribute('data-chat-mode')
    expect(['sidebar', 'floating', 'fullscreen']).toContain(mode)
    await flush()
  })

  test('TC-UC-002: Transport conecta (ws ou sse) via /api/auth/ws-token', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)

    // Registra listeners ANTES da navegação para não perder a primeira chamada
    // a /api/auth/ws-token (que o useChatSocket dispara na montagem).
    const wsTokenPromise = page.waitForResponse(
      (r) => r.url().includes('/api/auth/ws-token'),
      { timeout: 20000 },
    ).catch(() => null)
    const wsPromise = page.waitForEvent('websocket', { timeout: 8000 }).catch(() => null)

    await gotoChat(page)

    const wsTokenResp = await wsTokenPromise
    if (!wsTokenResp) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-AUTH-01: /api/auth/ws-token não foi requisitado — useChatSocket pode não estar montado em /chat',
      })
    } else {
      expect.soft(wsTokenResp.status(), 'ws-token deve devolver 200 (dev-auto-login)').toBe(200)
    }

    const wsEvent = await wsPromise
    if (!wsEvent) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-WS-01: nenhum WebSocket aberto em 8s após carregar /chat — provável fallback para REST',
      })
    }
    await flush()
  })

  test('TC-UC-003: Envio de mensagem aciona indicador "LIA digitando"', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)

    const input = await findInput(page)
    expect(input, 'Input da LIA deve existir em /chat').not.toBeNull()
    if (!input) return

    await input.click()
    await input.fill(`Auditoria #292 — ping ${Date.now()}`)
    await input.press('Enter')

    // Múltiplos fallback selectors: texto localizado OR role=status OR data-testid
    const thinking = page.locator(
      '[data-testid="lia-thinking-indicator"], [role="status"], text=/LIA est[aá] (pensando|digitando|processando)|Pensando|thinking/i',
    ).first()
    const appeared = await thinking.isVisible({ timeout: 5000 }).catch(() => false)
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-thinking.png', fullPage: true })

    if (!appeared) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-UI-01: indicador "LIA digitando" não apareceu em 5s — nem via data-testid, role=status ou texto localizado (ver useChatMessages.setIsThinking — BUG-13)',
      })
    }
    // Audit-only: registramos a ausência como achado, sem falhar o teste.
    await flush()
  })

  test('TC-UC-004: /criar vaga é interceptado localmente (não vai ao backend)', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)

    const input = await findInput(page)
    if (!input) test.skip(true, 'Input não localizado')

    // Captura todas as requisições pro backend-proxy do chat durante o teste
    const chatMessageRequests: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/api/backend-proxy/chat/message')) {
        chatMessageRequests.push(req.postData() || '')
      }
    })

    await input!.click()
    await input!.fill('/criar vaga')
    await input!.press('Enter')
    // Aguarda tempo suficiente pra, se houvesse POST, ele aparecer
    await page.waitForTimeout(1500)

    const inputCleared = await input!.inputValue()
    expect.soft(inputCleared, 'Slash command deve limpar o input').toBe('')

    // Evidência forte: /criar vaga é interceptado em handleSlashCommand e
    // disparaSendMessage('Criar nova vaga') INTERNAMENTE — ou seja, um POST
    // com "Criar nova vaga" no body (não o /criar vaga literal).
    const sentLiteralSlash = chatMessageRequests.some((b) => b.includes('"message":"/criar vaga"'))
    if (sentLiteralSlash) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-CMD-04: "/criar vaga" foi enviado literalmente ao backend em vez de ser traduzido por useWizardIntegration',
      })
    }
    expect.soft(sentLiteralSlash, '/criar vaga não deveria chegar literal ao backend').toBe(false)
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-slash-criar-vaga.png', fullPage: true })
    await flush()
  })

  test('TC-UC-005: /job e /talent (pedidos pelo task) — gap de contrato', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)

    const input = await findInput(page)
    if (!input) test.skip(true, 'Input não localizado')

    const chatMessageRequests: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/api/backend-proxy/chat/message')) {
        chatMessageRequests.push(req.postData() || '')
      }
    })

    for (const cmd of ['/job', '/talent']) {
      await input!.click()
      await input!.fill(cmd)
      await input!.press('Enter')
      await page.waitForTimeout(1200)
    }

    // Se /job ou /talent fossem slash commands conhecidos, useWizardIntegration
    // os traduziria — o backend receberia algo DIFERENTE do literal.
    // Caso contrário, eles caem no sendChatMessage direto.
    const jobLiteral = chatMessageRequests.some((b) => b.includes('"message":"/job"'))
    const talentLiteral = chatMessageRequests.some((b) => b.includes('"message":"/talent"'))

    if (jobLiteral || talentLiteral) {
      testInfo.annotations.push({
        type: 'finding',
        description: `F-CMD-02/03: /job (literal=${jobLiteral}) e /talent (literal=${talentLiteral}) foram enviados ao backend como mensagem comum — useWizardIntegration não os reconhece. Task spec #292 pede esses comandos.`,
      })
    }
    // Audit-only: registramos o estado, não bloqueamos.
    expect.soft(jobLiteral || talentLiteral, 'audit: ao menos um literal foi enviado → gap documentado').toBe(true)
    await flush()
  })

  test('TC-UC-006: Fallback WS→REST quando WS é bloqueado', async ({ page, context }, testInfo) => {
    const flush = instrumentPage(page, testInfo)

    // Bloqueia upgrade WS ANTES da navegação para forçar o branch REST.
    // Path canônico (Task #319): /api/v1/ws/chat/{session_id}.
    await context.route('**/api/v1/ws/chat/**', (route) => route.abort())

    const restPromise = page.waitForRequest(
      (r) => r.url().includes('/api/backend-proxy/chat/message'),
      { timeout: 25000 },
    ).catch(() => null)

    await gotoChat(page)

    const input = await findInput(page)
    if (!input) test.skip(true, 'Input não localizado')

    await input!.click()
    await input!.fill(`Teste fallback REST ${Date.now()}`)
    await input!.press('Enter')

    const req = await restPromise
    if (!req) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-FALLBACK-01: após 25s sem WS, POST /api/backend-proxy/chat/message não ocorreu — useChatMessages.sendMessage pode estar preso em transportMode intermediário',
      })
    }
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-rest-fallback.png', fullPage: true })
    expect.soft(req, 'Fallback REST via backend-proxy deveria ser acionado').not.toBeNull()
    await flush()
  })

  test('TC-UC-007: Rotulagem acessível dos botões de troca de modo', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)

    const chatRoot = page.locator('[data-chat-mode]').first()
    await expect(chatRoot).toBeVisible({ timeout: 10000 })
    const initialMode = await chatRoot.getAttribute('data-chat-mode')

    const modeButtons = page.locator(
      'button[aria-label*="modo" i], button[aria-label*="mode" i], button[title*="tela cheia" i], button[title*="fullscreen" i], button[aria-label*="flutuante" i], button[aria-label*="sidebar" i]',
    )
    const count = await modeButtons.count()
    if (count === 0) {
      testInfo.annotations.push({
        type: 'finding',
        description: 'F-UI-02: nenhum botão de troca de modo encontrado via aria-label/title; UnifiedChatHeader sem rotulagem acessível padronizada',
      })
    }
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-modes.png', fullPage: true })
    expect(['sidebar', 'floating', 'fullscreen']).toContain(initialMode)
    await flush()
  })

  test('TC-UC-008: /chat abre em fullscreen por padrão', async ({ page }, testInfo) => {
    const flush = instrumentPage(page, testInfo)
    await gotoChat(page)

    const chatRoot = page.locator('[data-chat-mode]').first()
    await expect(chatRoot).toBeVisible()
    const mode = await chatRoot.getAttribute('data-chat-mode')
    if (mode !== 'fullscreen') {
      testInfo.annotations.push({
        type: 'finding',
        description: `F-UI-03: ao abrir /chat, data-chat-mode=${mode} (esperado: fullscreen). ChatPageFullscreen pode não estar forçando initialMode.`,
      })
    }
    await page.screenshot({ path: 'e2e/screenshots/unified-chat-fullscreen-initial.png', fullPage: true })
    await flush()
  })
})
