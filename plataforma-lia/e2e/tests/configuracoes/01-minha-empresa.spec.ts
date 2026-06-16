/**
 * Task #1017 — Spec dedicado pra Configurações → Minha Empresa.
 *
 * Cobre o caminho completo que falhava silenciosamente em produção:
 *
 *  1. /pt/configuracoes carrega sem 500 (resp. canônica do
 *     SettingsRouteClient — wrapper "use client" fino).
 *  2. O hub "Minha Empresa" renderiza COM dados (mesmo quando o
 *     perfil tem `is_default=NULL` — bug do round-trip PATCH→GET
 *     coberto pela sentinela
 *     `tests/integration/agents/test_company_profile_roundtrip_t1017.py`).
 *  3. O CTA "Pedir ajuda à LIA" do bloco `basic` envia tag
 *     estruturada `[ACTION:prefill_section][target_section:basic]`
 *     pelo WebSocket (handoff Settings ↔ chat lateral — contrato T6
 *     #993).
 *  4. A LIA responde sem perguntar nome/setor/plano da empresa
 *     (anti-padrões do `CompanySettingsReActAgent` em
 *     `app/prompts/domains/company_settings.yaml`).
 *
 * Por que um spec separado do `prefill-section-handoff.spec.ts`?
 *   * Aquele cobre as 7 seções × 2 viewports (matriz 14 cenários,
 *     ~5min cada). Este é o "smoke gate" rápido só pra `basic` —
 *     deve fechar em < 90s e roda em PRs como gate canário antes
 *     da matriz cara. Falha aqui ⇒ matriz inteira está quebrada.
 *   * Foco específico do bug Task #1017: garantir que o hub
 *     renderiza mesmo no estado "perfil legado com is_default=NULL"
 *     (sem 500 no backend).
 */
import { expect, test } from '../../fixtures/auth.fixture'

test.describe.configure({ retries: 1 })

test.describe('Task #1017 — Configurações / Minha Empresa (smoke)', () => {
  test.setTimeout(120_000)

  test('hub renderiza, CTA "Pedir ajuda à LIA" envia [target_section:basic] e LIA responde sem repetir tenant', async ({
    authenticatedPage: page,
  }, testInfo) => {
    // ── Capture WS frames antes de qualquer interação ─────────────
    const sentFrames: string[] = []
    page.on('websocket', (ws) => {
      ws.on('framesent', (frame) => sentFrames.push(String(frame.payload ?? '')))
    })

    // ── 1. Carregar /pt/configuracoes sem 500 ─────────────────────
    const responses: Array<{ url: string; status: number }> = []
    page.on('response', (resp) => {
      const url = resp.url()
      if (url.includes('/api/v1/company/profile') || url.includes('/configuracoes')) {
        responses.push({ url, status: resp.status() })
      }
    })

    await page.goto('/pt/configuracoes', {
      waitUntil: 'domcontentloaded',
      timeout: 30_000,
    })
    await page
      .waitForLoadState('networkidle', { timeout: 30_000 })
      .catch(() => { /* ok */ })

    // Bug Task #1017: GET /api/v1/company/profile retornava 500 quando
    // `is_default=NULL` no banco. O fix está no validator
    // `convert_none_to_false` em `app/schemas/company.py`. Aqui
    // checamos que NENHUMA resposta de profile veio com 5xx — falha
    // ruidosa pra evitar regressão silenciosa.
    const profile5xx = responses.filter(
      (r) => r.url.includes('/api/v1/company/profile') && r.status >= 500,
    )
    expect(
      profile5xx,
      `[regressão T1017] GET ${profile5xx.map((r) => r.url).join(', ')} ` +
        `retornou 5xx. Provável causa: regressão no validator ` +
        `convert_none_to_false (app/schemas/company.py) — perfis com ` +
        `is_default=NULL voltam a quebrar serialização Pydantic.`,
    ).toEqual([])

    // ── 2. Abrir hub "Minha Empresa" via menu canônico ────────────
    const menuBtn = page.locator('[data-testid="settings-menu-minha-empresa"]')
    if (await menuBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await menuBtn.click()
    }
    const contentArea = page.locator('[data-testid="settings-content-area"]')
    await expect(contentArea).toBeVisible({ timeout: 15_000 })
    await expect(contentArea).toHaveAttribute(
      'data-active-section',
      'minha-empresa',
      { timeout: 10_000 },
    )
    await expect(page.locator('h2:has-text("Minha Empresa")')).toBeVisible({
      timeout: 15_000,
    })

    await page.screenshot({
      path: testInfo.outputPath('01-hub-rendered.png'),
      fullPage: true,
    })

    // ── 3. CTA "Pedir ajuda à LIA" do bloco `basic` ───────────────
    const ctaBasic = page.locator('[data-testid="pending-prefill-basic"]')
    await expect(
      ctaBasic,
      `[setup] CTA "Pedir ajuda à LIA" do bloco basic não está ` +
        `visível. O hub só renderiza esse botão quando há campos ` +
        `pendentes — rodar \`python -m scripts.seeds.demo_company\` ` +
        `pra garantir demo limpa com pendências.`,
    ).toBeVisible({ timeout: 15_000 })

    const tag = '[target_section:basic]'
    const beforeFrames = sentFrames.length
    await ctaBasic.click()

    // (UI) — bolha do usuário aparece no chat lateral
    const chatRoot = page
      .locator('[data-testid="unified-chat"], [data-chat-root]')
      .first()
    const scopedRoot =
      (await chatRoot.count()) > 0 ? chatRoot : page.locator('body')
    await expect(
      scopedRoot.locator('p', { hasText: tag }).first(),
      `[ui] Bolha de usuário com "${tag}" não apareceu no chat ` +
        `lateral após o click. Provável regressão em ` +
        `useSettingsConversational.triggerPrefillSection (autoSend).`,
    ).toBeVisible({ timeout: 15_000 })

    // (WS) — frame outbound carrega as 2 tags estruturais
    await expect
      .poll(
        () => {
          const slice = sentFrames.slice(beforeFrames)
          return slice.find((f) => f.includes(tag)) ?? null
        },
        {
          timeout: 10_000,
          message:
            `[ws] Nenhum frame WS contendo "${tag}" foi enviado em 10s ` +
            `após o click. Causas: autoSend regrediu ou o consumer de ` +
            `lia:prefill-message no chat parou de chamar sendMessage.`,
        },
      )
      .not.toBeNull()

    const wsFrame = sentFrames
      .slice(beforeFrames)
      .find((f) => f.includes(tag))!
    const parsed = JSON.parse(wsFrame) as { content?: string }
    const content = String(parsed.content ?? '')
    expect(content).toContain('[ACTION:prefill_section]')
    expect(content).toContain('[target_section:basic]')

    // ── 4. LIA responde sem perguntar tenant ──────────────────────
    const beforeBubbles = await scopedRoot
      .locator('.lia-markdown-content')
      .count()
    await expect
      .poll(
        () => scopedRoot.locator('.lia-markdown-content').count(),
        {
          timeout: 90_000,
          message:
            `[llm] LIA não respondeu em 90s ao prefill basic. Verificar ` +
            `lia-backend, ws-token e CompanySettingsReActAgent.process().`,
        },
      )
      .toBeGreaterThan(beforeBubbles)

    const reply =
      (await scopedRoot
        .locator('.lia-markdown-content')
        .last()
        .textContent()) ?? ''
    expect(reply, '[llm] resposta da LIA veio vazia').toBeTruthy()

    // Anti-padrões T-B / T-E — agente NÃO pode perguntar nome,
    // setor, plano ou headcount da empresa (já estão no
    // tenant_context_snippet). Estes são os símbolos do bug "LIA
    // pergunta company_id no chat" que o Task #1017 também guarda.
    const TENANT_ASK_PATTERNS: RegExp[] = [
      /\bqual\s+(é\s+)?(o\s+)?(nome|setor|porte|tamanho|plano)\s+da\s+empresa/i,
      /\bem\s+qual\s+empresa\s+você\s+trabalha\b/i,
      /\binforme\s+(o\s+)?company[_\s]?id\b/i,
      /\bquantos\s+funcion[áa]rios\b/i,
    ]
    for (const rx of TENANT_ASK_PATTERNS) {
      expect(
        reply,
        `[regressão T-B] LIA perguntou tenant via padrão ${rx} — viola ` +
          `TenantAwareAgentMixin (strict). Trecho: "${reply.slice(0, 240)}…"`,
      ).not.toMatch(rx)
    }

    // Foco esperado da seção `basic`
    expect(
      reply,
      `[scope] resposta da LIA não menciona vocabulário da seção ` +
        `basic (website/linkedin/telefone/email/endereço). Trecho: ` +
        `"${reply.slice(0, 240)}…"`,
    ).toMatch(
      /\b(website|linkedin|telefone|e-?mail|endere[cç]o|raz[aã]o\s+social|cnpj|fundac|logo)\b/i,
    )

    await page.screenshot({
      path: testInfo.outputPath('02-lia-reply.png'),
      fullPage: true,
    })
  })
})
