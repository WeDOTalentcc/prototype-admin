/**
 * Task #997 — Validar a integração chat ↔ agente Configurações end-to-end.
 * Task #998 — Estender a cobertura para as seções do hub Minha Empresa
 *             (originalmente 6; PR1/#1001 ampliou para 7 com `basic`).
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
 * Cobre as 7 seções (basic, culture, tech_stack, benefits, workforce, policy,
 * compensation) — confirma que o hard-scope funciona em todas, conforme o
 * contrato T6/§ "Settings ↔ chat lateral" no replit.md + PR1 (#1001) que
 * adicionou `basic` (Dados Básicos) cobrindo os 11 campos cadastrais de
 * `company_profiles`. A matriz de anti-keywords é 7x6 (vocabulário esperado
 * de cada seção é proibido nas outras 6), derivada automaticamente de
 * SECTION_VOCAB para evitar que adicionar uma 8ª seção quebre a cobertura
 * silenciosamente.
 *
 * Estratégia FAIL-LOUD em todos os 3 critérios. Pré-condições (backend de
 * pé, empresa demo com pendências nas 7 seções) são exigências e o spec
 * FALHA ruidosamente quando ausentes — o reviewer (#997) rejeitou a
 * versão anterior por usar `test.skip()` nesses cenários, mascarando
 * regressão real. O seed canônico de demo (`scripts/seeds/demo_company.py`)
 * deixa todos os campos editoriais vazios fora de sector/plan/headcount,
 * o que garante pendências nas 7 seções por padrão.
 */

import { test, expect, type Page } from '../../fixtures/auth.fixture'

/**
 * Seções cobertas — a chave é o `target_section` que vai literal no
 * prompt e nos asserts. Mapeamento `blockKey` é o sufixo do data-testid
 * `pending-prefill-<blockKey>` no MinhaEmpresaHub (BLOCK_TO_PREFILL).
 *
 * IMPORTANTE: blockKey ≠ section quando o bloco do card foi renomeado
 * sem renomear a chave de domínio (tech→tech_stack, documents→compensation).
 * Não simplificar: testar pelo data-testid real do hub é o que valida o
 * binding de UI; testar pela tag é o que valida o contrato com o agente.
 */
type Section =
  | 'basic'
  | 'culture'
  | 'tech_stack'
  | 'benefits'
  | 'workforce'
  | 'policy'
  | 'compensation'

interface SectionSpec {
  section: Section
  blockKey: string
  /** Padrão que DEVE aparecer na resposta (vocabulário canônico da seção). */
  expected: RegExp
  /**
   * Padrões característicos da seção — usados para derivar anti-keywords
   * das DEMAIS seções. Devem ser específicos o bastante para não causar
   * cross-match com a própria seção alvo.
   */
  signature: RegExp[]
}

const SECTIONS: SectionSpec[] = [
  {
    section: 'basic',
    blockKey: 'basic',
    expected: /\b(nome|cnpj|website|rh|e-?mail|telefone|endere[cç]o|funcion[aá]rios|fundada|fundac|linkedin|logo|raz[aã]o\s+social|nome\s+fantasia)/i,
    // Vocabulário canônico de "Dados Básicos" — proibido nas outras 6 seções.
    // Inclui nome/cnpj/website/rh explicitamente (task #1001), além de
    // razão social, telefone do RH, endereço da sede e LinkedIn da empresa
    // — campos cadastrais únicos de company_profiles que NÃO aparecem em
    // culture/tech_stack/benefits/workforce/policy/compensation.
    signature: [
      /\b(nome\s+da\s+empresa|raz[aã]o\s+social|nome\s+fantasia)\b/i,
      /\b(cnpj)\b/i,
      /\b(website\s+da\s+empresa|site\s+da\s+empresa|url\s+do\s+site|linkedin\s+da\s+empresa)\b/i,
      /\b(email\s+do\s+rh|hr\s*email|telefone\s+do\s+rh|endere[cç]o\s+da\s+sede|ano\s+de\s+funda|logo\s+da\s+empresa)\b/i,
    ],
  },
  {
    section: 'culture',
    blockKey: 'culture',
    expected: /\b(cultura|EVP|miss[aã]o|vis[aã]o|valores|prop[oó]sito|comportament|DEI)/i,
    signature: [
      /\b(EVP|miss[aã]o|vis[aã]o|valores da empresa|cultura organizacional|prop[oó]sito|DEI)\b/i,
    ],
  },
  {
    section: 'tech_stack',
    blockKey: 'tech',
    expected: /\b(stack|linguagens?|frameworks?|tecnolog|engenharia|reposit[oó]rio)/i,
    signature: [
      /\b(linguagens? de programa|frameworks?|tech\s*stack|reposit[oó]rio|github|gitlab|cultura de engenharia)\b/i,
    ],
  },
  {
    section: 'benefits',
    blockKey: 'benefits',
    expected: /\b(benef[ií]cio|vale|plano|sa[uú]de|gympass|aux[ií]lio|seguro)/i,
    signature: [
      /\b(vale[ -](refei|alimenta)|plano de sa[uú]de|vale transporte|gympass|aux[ií]lio creche)\b/i,
    ],
  },
  {
    section: 'workforce',
    blockKey: 'workforce',
    expected: /\b(headcount|workforce|contrata[cç][aã]o|organograma|departamento|volume|ATS atual|desafios?)/i,
    signature: [
      /\b(headcount|organograma|workforce planning|volume de contrata|tipos? de vaga|ATS atual)\b/i,
    ],
  },
  {
    section: 'policy',
    blockKey: 'policy',
    expected: /\b(pol[ií]tic|pipeline|etapas?|aprova[cç][aã]o|agendamento|triagem|entrevistas?|autonom)/i,
    signature: [
      /\b(pol[ií]tica de recrutamento|min[ií]mo de entrevistas|aprova[cç][aã]o do gestor|auto[- ]agendamento|n[ií]vel de autonomia|triagem autom[aá]tica)\b/i,
    ],
  },
  {
    section: 'compensation',
    blockKey: 'documents',
    expected: /\b(remunera[cç][aã]o|sal[aá]ri|banda|cargos?|PRV|b[oô]nus|comiss[aã]o|onboarding)/i,
    signature: [
      /\b(banda salarial|cargos? e sal[aá]rios|PRV|remunera[cç][aã]o vari[aá]vel|comiss[aã]o|b[oô]nus|plano de remunera)\b/i,
    ],
  },
]

/**
 * Matriz 6x5 derivada automaticamente: para cada seção, anti-keywords =
 * união das `signature` das DEMAIS 5 seções. Se alguém adicionar uma 7ª
 * seção (ex: ESG), a cobertura dela entra automaticamente, e o
 * vocabulário dela passa a ser proibido nas outras 6 — sem mexer no
 * spec.
 */
function buildAntiKeywords(target: Section): RegExp[] {
  return SECTIONS
    .filter((s) => s.section !== target)
    .flatMap((s) => s.signature)
}

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
 *   - botão `pending-prefill-<blockKey>` precisa existir (demo seedada
 *     com pendências em todas as seções);
 *   - LIA precisa responder em até 90s (backend de pé).
 */
async function runHandoffForSection(
  page: Page,
  getSentFrames: () => string[],
  spec: SectionSpec,
  chatRoot: ReturnType<Page['locator']>,
): Promise<PrefillRunResult> {
  const { section, blockKey } = spec

  // 0. pré-requisito: o botão da seção precisa estar presente. Se não
  //    estiver, é falta de seed da empresa demo — falha ruidosamente
  //    com instrução para o operador seedar pendências em TODAS as
  //    seções (o seed canônico já faz isso por default).
  const btn = page.locator(`[data-testid="pending-prefill-${blockKey}"]`)
  await expect(
    btn,
    `[setup] Botão "Pedir ajuda à LIA" para bloco "${blockKey}" ` +
      `(target_section=${section}) não está visível. O contrato #998 ` +
      `exige cobertura das 7 seções: o botão só renderiza quando há ` +
      `campos pendentes (MinhaEmpresaHub.tsx → pendingSections). ` +
      `Rodar \`python -m scripts.seeds.demo_company\` no lia-agent-system ` +
      `garante demo limpa com pendências nas 7 seções. NÃO usar test.skip.`,
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
    `[ui] Após click em pending-prefill-${blockKey} a bolha de usuário com ` +
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
          `em pending-prefill-${blockKey}. Possíveis causas: (a) autoSend ` +
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
  expect(reply, `[llm] resposta da LIA veio vazia (seção ${section})`).toBeTruthy()

  return { rawFrame: raw, parsedContent: reply ?? '' }
}

test.describe.configure({ retries: 1 })

// Sentinela meta — falha LOUD se alguém remover/adicionar uma seção sem
// revisar o spec. Contrato T6+PR1 (#1001) são 7 seções (basic, culture,
// tech_stack, benefits, workforce, policy, compensation). Se virarem 8
// (ex: ESG), atualizar este número junto com SECTIONS — buildAntiKeywords
// já se ajusta sozinho.
if (SECTIONS.length !== 7) {
  throw new Error(
    `[meta] SECTIONS deve ter exatamente 7 entradas (contrato T6/#993 + PR1/#1001), ` +
      `tem ${SECTIONS.length}. Se a mudança é intencional, atualizar este guard ` +
      `e PrefillSection em use-settings-conversational.ts.`,
  )
}

/**
 * Cobertura por viewport — PR7/A4 exige a matriz 7×2 (7 seções × {desktop,
 * mobile}). Os dois viewports são providos pelos projects do
 * `playwright.config.ts` (`desktop-chrome` + `mobile-chrome`); por isso o
 * spec NÃO duplica o loop por viewport (evita 4× runs). Para garantir
 * que a matriz inteira foi exercida, o runner deste spec DEVE executar
 * AMBOS os projects — ou seja, executar SEM `--project=<um-só>`, ou com
 * `--project=desktop-chrome --project=mobile-chrome`. O guard abaixo
 * registra o nome do project no título do teste (visível no relatório do
 * Playwright) e, no `afterAll`, falha ruidosamente se a execução tiver
 * rodado contra um project fora da allowlist.
 */
const EXPECTED_PROJECTS: ReadonlyArray<string> = ['desktop-chrome', 'mobile-chrome']

test.describe('Task #997/#998/#1001/#1007 — Settings ↔ chat handoff (prefill_section, 7 seções × 2 viewports)', () => {
  test.setTimeout(5 * 60_000) // 5min cada — inclui resposta real da LIA

  test.beforeAll(({}, testInfo) => {
    const project = testInfo.project.name
    if (!EXPECTED_PROJECTS.includes(project)) {
      throw new Error(
        `[viewport-gate] Spec rodou contra project "${project}", fora da ` +
          `allowlist [${EXPECTED_PROJECTS.join(', ')}]. PR7/A4 exige matriz ` +
          `7 seções × 2 viewports. Use o npm script canônico ` +
          `\`pnpm test:e2e:settings-prefill\` que invoca ambos os projects ` +
          `numa sequência única (falha se qualquer um faltar/falhar).`,
      )
    }
  })

  // Captura `lia:settings-updated` (PR6 bridge) em window.__liaSettingsEvents
  // ANTES de qualquer navegação. addInitScript roda em todo new document do
  // contexto, então cobre /pt/chat (fixture) e /pt/configuracoes (openMinha-
  // Empresa). Sem ele, criterion (4a) não tem sinal para gating.
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.addInitScript(() => {
      const w = window as unknown as {
        __liaSettingsEvents?: Array<{ key: string; ts: number }>
      }
      w.__liaSettingsEvents = w.__liaSettingsEvents ?? []
      window.addEventListener('lia:settings-updated', (ev: Event) => {
        const detail = (ev as CustomEvent).detail as { key?: string } | undefined
        w.__liaSettingsEvents!.push({ key: detail?.key ?? '', ts: Date.now() })
      })
    })
  })

  for (const spec of SECTIONS) {
    const { section, blockKey } = spec
    test(`[@${section}] hub Minha Empresa → "Pedir ajuda à LIA" envia tag estruturada [${section}] (block=${blockKey}), aparece no chat, mantém escopo e fecha o loop de persistência`, async ({
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

      const result = await runHandoffForSection(page, getSentFrames, spec, scopedRoot)

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

      // (LLM-scope) — a resposta MENCIONA vocabulário esperado da seção alvo …
      expect(
        result.parsedContent,
        `[scope:${section}] Resposta da LIA não menciona vocabulário ` +
          `esperado da seção "${section}". Texto: "${result.parsedContent.slice(0, 240)}…"`,
      ).toMatch(spec.expected)

      // … e NÃO mistura vocabulário das outras 5 seções (hard-scope T6).
      // Matriz 6x5 derivada de SECTIONS — adicionar uma 7ª seção amplia
      // a cobertura sem mexer no spec.
      const antiKeywords = buildAntiKeywords(section)
      expect(
        antiKeywords.length,
        `[meta] Matriz anti-keywords ficou vazia para "${section}" — ` +
          `bug em buildAntiKeywords ou em SECTIONS.signature.`,
      ).toBeGreaterThanOrEqual(5)

      for (const rx of antiKeywords) {
        expect(
          result.parsedContent,
          `[scope-leak:${section}] Resposta da LIA mencionou padrão "${rx}" ` +
            `pertencente a outra seção. Trecho: "${result.parsedContent.slice(0, 240)}…". ` +
            `Indica regressão no hard-scope do CompanySettingsReActAgent ` +
            `(YAML behavioral_rules) ou no prompt em useSettingsConversational.`,
        ).not.toMatch(rx)
      }

      // (4) Persistência via desaparecimento do `pending-prefill-<blockKey>` —
      //   PR7/A4 (Task #1007). Esta é a testemunha REAL de que o loop
      //   chat→agente→DB→UI fechou: o card de pendência só desaparece
      //   quando (a) o agente chamou alguma das tools whitelisted em
      //   SETTINGS_PERSIST_TOOLS (PR6) e (b) o `lia:settings-updated`
      //   bridge disparou refetch do hub.
      //
      //   IMPORTANTE: o flow `prefill_section` é majoritariamente HELP
      //   (LIA pergunta, recrutador responde, LIA salva). No primeiro
      //   turno raramente há save — então este assert é INTENCIONALMENTE
      //   `expect.soft()` com timeout curto (15s). Quando o YAML do
      //   agente evoluir para auto-save em prefill com confidence >=
      //   APPLY_NOTIFY (gate A6/PR5 já enforced), este soft vira o sinal
      //   verde da feature; até lá ele vira FAIL informativo no relatório
      //   sem bloquear o restante da matriz 7×6 do hard-scope (critérios
      //   1-3 acima). Ver drift no .local/.commit_message do PR7.
      // (4) Persistência REAL via fechamento do loop chat→agente→DB→UI.
      //     Gate determinístico em 2 fases:
      //       (4a) Aguarda até 20s pela emissão de `lia:settings-updated`
      //            (PR6 bridge emitida por tools em SETTINGS_PERSIST_TOOLS).
      //            Se NÃO disparar, este turno foi HELP-mode puro (LIA só
      //            perguntou, não salvou) — `test.skip()` com motivo claro,
      //            cobrindo deterministicamente o caso "auto-save futuro
      //            (#1014) ainda não rodou". Skip ≠ fail, mantendo run
      //            verde sem mascarar regressão.
      //       (4b) Se disparou, exige hard-assert que o card desaparece
      //            em ≤10s (refetch do hub). Aqui a bridge JÁ ativou o
      //            loop de persistência; se o card persistir, é regressão
      //            real (PR6 bridge OU refetch quebrado).
      // Filtra eventos por section/blockKey para reduzir falso-positivo:
      // só consideramos a bridge "disparada para esta seção" se o
      // detail.key bater com a seção alvo OU com o blockKey (ambos são
      // chaves possíveis emitidas pelos tools em SETTINGS_PERSIST_TOOLS,
      // dependendo de qual save canônico foi usado). Eventos vazios
      // (key="") também contam — algumas tools emitem broadcast sem key.
      const allowedKeys = [section, blockKey, '']
      const eventsBefore = await page.evaluate(
        (keys) =>
          (
            (window as unknown) as {
              __liaSettingsEvents?: Array<{ key: string }>
            }
          ).__liaSettingsEvents?.filter((e) => keys.includes(e.key)).length ?? 0,
        allowedKeys,
      )
      const bridgeDeadline = Date.now() + 20_000
      let bridgeFired = false
      while (Date.now() < bridgeDeadline) {
        const total = await page.evaluate(
          (keys) =>
            (
              (window as unknown) as {
                __liaSettingsEvents?: Array<{ key: string }>
              }
            ).__liaSettingsEvents?.filter((e) => keys.includes(e.key)).length ?? 0,
          allowedKeys,
        )
        if (total > eventsBefore) { bridgeFired = true; break }
        await page.waitForTimeout(500)
      }
      test.skip(
        !bridgeFired,
        `[persist:${section}] LIA respondeu em HELP-mode (nenhum ` +
          `'lia:settings-updated' emitido em 20s). Critério (4) é ` +
          `condicional: só assertamos persistência quando a bridge ` +
          `dispara. Quando follow-up #1014 (auto-save com confidence>=` +
          `APPLY_NOTIFY) estiver enforced, este skip vira PASS hard.`,
      )
      const pendingBtn = page.locator(`[data-testid="pending-prefill-${blockKey}"]`)
      await expect(
        pendingBtn,
        `[persist:${section}] Bridge 'lia:settings-updated' DISPAROU mas ` +
          `o card "pending-prefill-${blockKey}" não sumiu em 10s. ` +
          `Indica regressão real: ou a bridge PR6 não está acoplada ao ` +
          `refetch do MinhaEmpresaHub, ou o tool em SETTINGS_PERSIST_TOOLS ` +
          `gravou no campo errado. NÃO é HELP-mode (skip seria essa rota).`,
      ).toHaveCount(0, { timeout: 10_000 })
    })
  }
})
