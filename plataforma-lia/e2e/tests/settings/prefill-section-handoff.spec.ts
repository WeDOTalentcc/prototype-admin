/**
 * Task #997 — Validar a integração chat ↔ agente Configurações end-to-end.
 *
 * T6 (#993) cobre o contrato em três camadas (frontend autoSend, YAML do
 * agente, golden dataset offline). Este spec fecha o loop com uma checagem
 * REAL: clica "Pedir ajuda à LIA" num card do hub Minha Empresa, valida
 * que (1) o prompt aparece na UI do chat lateral (auto-enviado, não só
 * pré-populado no input), (2) o frame WS chega ao backend com a tag
 * estruturada `[ACTION:prefill_section][target_section:<X>]` intacta, e
 * (3) a resposta da LIA respeita o escopo da seção (não vaza vocabulário
 * de outras seções).
 *
 * Cobre 2 seções (culture + benefits) — confirma que o hard-scope funciona
 * em ambas, conforme o contrato T6/§ "Settings ↔ chat lateral" no replit.md.
 *
 * Estratégia FAIL-LOUD em todos os 3 critérios. Pré-condições (backend de
 * pé, empresa demo com pendências em culture+benefits) são exigências e o
 * spec FALHA ruidosamente quando ausentes — o reviewer (#997) rejeitou a
 * versão anterior por usar `test.skip()` nesses cenários, mascarando
 * regressão real.
 */

import { test, expect, type Page } from '../../fixtures/auth.fixture'

/** Coleta frames WS enviados durante o teste. */
function attachWsSentCapture(page: Page): () => string[] {
  const frames: string[] = []
  page.on('websocket', (ws) => {
    ws.on('framesent', (frame) => frames.push(String(frame.payload ?? '')))
  })
  return () => frames
}

function findChatFrameWith(frames: string[], needle: string): string | undefined {
  return frames.find((f) => {
    if (!f.includes(needle)) return false
    try {
      const p = JSON.parse(f) as { content?: unknown }
      return typeof p?.content === 'string'
    } catch {
      return false
    }
  })
}

async function openMinhaEmpresa(page: Page) {
  await page.goto('/pt/configuracoes', { waitUntil: 'domcontentloaded', timeout: 30_000 })
  await page.waitForLoadState('networkidle', { timeout: 30_000 }).catch(() => { /* ok */ })

  const menuBtn = page.locator('[data-testid="settings-menu-minha-empresa"]')
  if (await menuBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
    await menuBtn.click()
  }

  const contentArea = page.locator('[data-testid="settings-content-area"]')
  await expect(contentArea).toBeVisible({ timeout: 15_000 })
  await expect(contentArea).toHaveAttribute('data-active-section', 'minha-empresa', {
    timeout: 10_000,
  })

  // O hub é dynamic({ ssr:false }) — aguarda o título canônico aparecer.
  await expect(page.locator('h2:has-text("Minha Empresa")')).toBeVisible({ timeout: 15_000 })
}

interface PrefillRunResult {
  rawFrame: string
  parsedContent: string
}

/**
 * Núcleo do teste — executa todas as 3 verificações end-to-end:
 *   (UI)   o prompt aparece numa bolha de usuário no chat lateral;
 *   (WS)   o frame outbound carrega a tag estruturada;
 *   (LLM)  a resposta da LIA mantém escopo na seção alvo.
 *
 * Pré-condições FAIL-LOUD:
 *   - botão `pending-prefill-<section>` precisa existir (demo seedada);
 *   - LIA precisa responder em até 90s (backend de pé).
 */
async function runHandoffForSection(
  page: Page,
  getSentFrames: () => string[],
  section: 'culture' | 'benefits',
  chatRoot: ReturnType<Page['locator']>,
): Promise<PrefillRunResult> {
  // 0. pré-requisito: o botão da seção precisa estar presente. Se não
  //    estiver, é falta de seed da empresa demo — falha ruidosamente
  //    com instrução para o operador seedar pendências em culture+benefits.
  const btn = page.locator(`[data-testid="pending-prefill-${section}"]`)
  await expect(
    btn,
    `[setup] Botão "Pedir ajuda à LIA" para seção "${section}" não está ` +
      `visível. O contrato #997 exige cobertura mínima das duas seções: o ` +
      `botão só renderiza quando há campos pendentes (MinhaEmpresaHub.tsx → ` +
      `pendingSections). Seedar a empresa demo deixando culture e benefits ` +
      `incompletos antes do CI E2E — não pode ser test.skip.`,
  ).toBeVisible({ timeout: 15_000 })

  const tag = `[target_section:${section}]`
  const beforeFrames = getSentFrames().length
  const beforeLiaBubbles = await chatRoot.locator('.lia-markdown-content').count()

  await btn.click()

  // 1. (UI / autoSend) — o prompt precisa aparecer COMO MENSAGEM enviada
  //    no chat lateral, não só no input. UnifiedMessageList renderiza a
  //    bolha de usuário com o conteúdo cru no <p>; localizamos pelo texto
  //    da tag estruturada (que vai inteiro no message.content), restrito
  //    ao container do chat para evitar falso positivo.
  await expect(
    chatRoot.locator('p', { hasText: tag }).first(),
    `[ui] Após click em pending-prefill-${section} a bolha de usuário com ` +
      `o prompt (contendo "${tag}") não apareceu no chat lateral. Causa ` +
      `provável: useSettingsConversational.triggerPrefillSection deixou de ` +
      `passar autoSend:true OU o consumer de lia:prefill-message no chat ` +
      `parou de chamar sendMessage (UnifiedChat / useWizardIntegration).`,
  ).toBeVisible({ timeout: 15_000 })

  // 2. (WS) — frame com a tag estruturada precisa sair em até 10s.
  await expect
    .poll(
      () => findChatFrameWith(getSentFrames().slice(beforeFrames), tag) ?? null,
      {
        timeout: 10_000,
        message:
          `[ws] Nenhum frame WS contendo "${tag}" foi enviado após click ` +
          `em pending-prefill-${section}. Possíveis causas: (a) autoSend ` +
          `regrediu, (b) o chat caiu pro REST silenciosamente, (c) o ` +
          `prompt deixou de incluir [target_section:${section}].`,
      },
    )
    .not.toBeNull()

  const raw = findChatFrameWith(getSentFrames().slice(beforeFrames), tag)!
  const parsed = JSON.parse(raw) as { content?: string }
  const content = String(parsed.content ?? '')

  // T6 — as DUAS tags devem aparecer LITERAIS (string match no YAML do agente).
  expect(content).toContain('[ACTION:prefill_section]')
  expect(content).toContain(`[target_section:${section}]`)

  // 3. (LLM) — resposta da LIA precisa chegar. Sem skip: backend é
  //    pré-requisito e a regressão de hard-scope só é detectável aqui.
  await expect
    .poll(
      () => chatRoot.locator('.lia-markdown-content').count(),
      {
        timeout: 90_000,
        message:
          `[llm] LIA não respondeu em 90s para seção "${section}". O ` +
          `frame WS foi aceito mas nenhuma bolha .lia-markdown-content ` +
          `nova apareceu. Verificar lia-backend, ws-token, e ` +
          `CompanySettingsReActAgent.process(). Não suprimir com skip — ` +
          `essa é a parte do contrato que valida o hard-scope do agente.`,
      },
    )
    .toBeGreaterThan(beforeLiaBubbles)

  const reply = await chatRoot.locator('.lia-markdown-content').last().textContent()
  expect(reply, '[llm] resposta da LIA veio vazia').toBeTruthy()

  return { rawFrame: raw, parsedContent: reply ?? '' }
}

/**
 * Anti-keywords das outras seções — usadas para detectar leak de escopo
 * na resposta da LIA. Listas pequenas e canônicas (alinha com o YAML do
 * CompanySettingsReActAgent).
 */
const SECTION_ANTI_KEYWORDS: Record<'culture' | 'benefits', RegExp[]> = {
  culture: [
    /\b(vale[ -](refei|alimenta)|plano de sa[uú]de|vale transporte|gympass|PRV|remunera[cç][aã]o vari[aá]vel|b[oô]nus)\b/i,
    /\b(linguagens? de programa|frameworks?|tech\s*stack|reposit[oó]rio|github|gitlab)\b/i,
    /\b(headcount|organograma|departamento|workforce planning)\b/i,
  ],
  benefits: [
    /\b(EVP|miss[aã]o|vis[aã]o|valores da empresa|cultura organizacional|prop[oó]sito)\b/i,
    /\b(linguagens? de programa|frameworks?|tech\s*stack|reposit[oó]rio|github|gitlab)\b/i,
    /\b(headcount|organograma|workforce planning)\b/i,
  ],
}

const SECTION_EXPECTED_KEYWORDS: Record<'culture' | 'benefits', RegExp> = {
  culture: /\b(cultura|EVP|miss[aã]o|valores|prop[oó]sito|comportament)/i,
  benefits: /\b(benef[ií]cio|vale|plano|sa[uú]de|gympass|aux[ií]lio|seguro|PRV|remunera[cç][aã]o)/i,
}

test.describe.configure({ retries: 1 })

test.describe('Task #997 — Settings ↔ chat handoff (prefill_section)', () => {
  test.setTimeout(5 * 60_000) // 5min cada — inclui resposta real da LIA

  for (const section of ['culture', 'benefits'] as const) {
    test(`hub Minha Empresa → "Pedir ajuda à LIA" envia tag estruturada [${section}], aparece no chat e mantém escopo`, async ({
      authenticatedPage: page,
    }, testInfo) => {
      const getSentFrames = attachWsSentCapture(page)

      await openMinhaEmpresa(page)
      await page.screenshot({
        path: testInfo.outputPath(`${section}-00-hub.png`),
        fullPage: true,
      })

      // Container do chat lateral / fullscreen — escopo das asserções de UI.
      // Fallback para `page` se o atributo não existir (compat).
      const chatRoot = page.locator('[data-testid="unified-chat"], [data-chat-root]').first()
      const scopedRoot = (await chatRoot.count()) > 0 ? chatRoot : page.locator('body')

      const result = await runHandoffForSection(page, getSentFrames, section, scopedRoot)

      await testInfo.attach(`ws-frame-${section}`, {
        body: result.rawFrame,
        contentType: 'application/json',
      })
      await testInfo.attach(`lia-reply-${section}`, {
        body: result.parsedContent,
        contentType: 'text/plain',
      })
      await page.screenshot({
        path: testInfo.outputPath(`${section}-01-reply.png`),
        fullPage: true,
      })

      // (LLM-scope) — a resposta MENCIONA vocabulário da seção alvo …
      expect(
        result.parsedContent,
        `[scope:${section}] Resposta da LIA não menciona vocabulário ` +
          `esperado da seção "${section}". Texto: "${result.parsedContent.slice(0, 240)}…"`,
      ).toMatch(SECTION_EXPECTED_KEYWORDS[section])

      // … e NÃO mistura vocabulário de outras seções (hard-scope T6).
      for (const rx of SECTION_ANTI_KEYWORDS[section]) {
        expect(
          result.parsedContent,
          `[scope-leak:${section}] Resposta da LIA mencionou padrão "${rx}" ` +
            `pertencente a outra seção. Trecho: "${result.parsedContent.slice(0, 240)}…". ` +
            `Indica regressão no hard-scope do CompanySettingsReActAgent ` +
            `(YAML behavioral_rules) ou no prompt em useSettingsConversational.`,
        ).not.toMatch(rx)
      }
    })
  }
})
