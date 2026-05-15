/**
 * Cenário D — Edge cases do wizard (Task #1057).
 *
 * Três sub-testes cobrem invariantes operacionais críticas que NÃO são
 * exercitadas pelos cenários A/B/C lineares:
 *
 *   D1 — CANCELAR mid-wizard: recrutador escreve "esquece essa vaga,
 *        cancelar" depois de já ter dado o título. Asserto: LIA responde
 *        (sem 500) e a sessão fica em estado consistente (não trava).
 *
 *   D2 — RETOMAR sessão: recrutador inicia wizard, dá 2 turnos, recarrega
 *        a página (sessionStorage do FE preserva chat session_id), e
 *        envia uma nova mensagem perguntando o que já foi capturado.
 *        Asserto: LIA menciona o cargo dado antes do reload — `wizard_session_pin`
 *        Tier 0.5 do CascadedRouter + checkpointer LangGraph restauraram
 *        o estado (sentinela Task #1051).
 *
 *   D3 — FALLBACK determinístico do JdEnrichmentService: já existe a flag
 *        canônica `LIA_JD_ENRICHMENT_TIMEOUT_S` (graph.py L336). Quando
 *        setada para "0.001" no backend, qualquer chamada ao Gemini cai
 *        no `_fallback_enrichment` + warning "fallback determinístico
 *        (timeout)". Esse subteste é TOLERANTE: roda contra o backend
 *        atual (live OU fallback) e asserta apenas que o caminho de
 *        enrichment NÃO crasha — quando rodado com o env setado, o gate
 *        pw-cenario-D no `.replit` força o caminho fallback.
 *
 * Reuso integral dos helpers canônicos. Nenhum testid novo é assumido.
 */

import { test, expect } from '../../fixtures/auth.fixture'
import {
  SEL,
  goToChatHome,
  sendMessageAndWait,
  captureMilestone,
  attachQualitySensors,
  assertNoAiSlop,
} from './01-helpers'

test.describe.configure({ retries: 1 })

test.describe('Cenário D — Edge cases (cancelar / retomar / fallback)', () => {
  test.setTimeout(15 * 60_000)

  // ─────────────────────────────────────────────────────────────────────
  // D1 — Cancelar mid-wizard
  // ─────────────────────────────────────────────────────────────────────
  test('D1 — cancelar wizard no meio mantém chat saudável', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'D1-00-dashboard')

      await sendMessageAndWait(
        page,
        'Quero criar uma vaga de Engenheiro de Software Pleno'
      )
      await captureMilestone(page, testInfo, 'D1-01-greeting')

      // Cancela ANTES de confirmar seniority — etapa mais cedo possível.
      const beforeCancel = await page.locator(SEL.liaMarkdown).count()
      await sendMessageAndWait(page, 'esquece, vamos cancelar essa vaga')
      await captureMilestone(page, testInfo, 'D1-02-cancel')

      // Invariante #1 — LIA respondeu (não travou em loading).
      const afterCancel = await page.locator(SEL.liaMarkdown).count()
      expect(
        afterCancel,
        'LIA deve responder ao pedido de cancelamento (sem trava)'
      ).toBeGreaterThan(beforeCancel)

      // Invariante #2 — chat continua interativo (próxima mensagem flui).
      const beforePing = afterCancel
      await sendMessageAndWait(page, 'oi, tudo bem?')
      const afterPing = await page.locator(SEL.liaMarkdown).count()
      expect(
        afterPing,
        'chat deve continuar interativo após cancelamento (sem 500/timeout)'
      ).toBeGreaterThan(beforePing)

      // Sentinela: nenhum 5xx em /api/ durante o cancelamento.
      const fiveXX = sensors.networkErrors.filter((e) => e.status >= 500)
      expect(
        fiveXX,
        `cancelamento NÃO deve gerar 5xx em /api/ (got ${JSON.stringify(fiveXX)})`
      ).toHaveLength(0)

      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })

  // ─────────────────────────────────────────────────────────────────────
  // D2 — Retomar sessão via wizard_session_pin
  // ─────────────────────────────────────────────────────────────────────
  test('D2 — retomar wizard após reload via wizard_session_pin', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'D2-00-dashboard')

      // Estabelece um cargo distintivo que possamos pesquisar nas respostas
      // da LIA depois do reload (case-insensitive).
      const distinctTitle = 'Analista Financeiro Pleno'
      await sendMessageAndWait(page, `Quero criar uma vaga de ${distinctTitle}`)
      await sendMessageAndWait(page, 'confirma')
      await captureMilestone(page, testInfo, 'D2-01-pre-reload')

      // RELOAD — força o FE a re-montar tudo. O `session_id` persistido em
      // sessionStorage (UnifiedChat) deve manter o mesmo thread, e o
      // wizard_session_pin Tier 0.5 do CascadedRouter deve re-rotear ao
      // domínio wizard quando a próxima mensagem chegar.
      await page.reload({ waitUntil: 'domcontentloaded', timeout: 90_000 })
      await page
        .getByRole('textbox', { name: /mensagem|message/i })
        .first()
        .waitFor({ state: 'visible', timeout: 20_000 })
      await captureMilestone(page, testInfo, 'D2-02-pos-reload')

      // Snapshot: APENAS as bubbles que existiam ANTES de mandar a próxima
      // pergunta. Tudo que aparecer DEPOIS é resposta nova pós-reload — é
      // ali que o wizard_session_pin / checkpointer precisa ser provado
      // (não no histórico textual antigo, que poderia gerar falso positivo).
      const bubblesBeforeAsk = await page.locator(SEL.liaMarkdown).count()

      // Pergunta sobre o estado capturado — força o agente a usar o
      // checkpointer (caso contrário responderia "qual cargo você quer?").
      await sendMessageAndWait(
        page,
        'qual cargo eu te disse antes? me lembra o que já temos'
      )
      await captureMilestone(page, testInfo, 'D2-03-pergunta-estado')

      // Invariante canônica: a resposta NOVA pós-reload (qualquer bubble
      // com index >= bubblesBeforeAsk) precisa mencionar o cargo. Tolerante
      // a paráfrase (substring case-insensitive sobre "Analista Financeiro"
      // — sem "Pleno" para tolerar normalização da LIA).
      const newBubbles = await page
        .locator(SEL.liaMarkdown)
        .allTextContents()
      const newOnly = newBubbles.slice(bubblesBeforeAsk).join('\n').toLowerCase()
      expect(
        newOnly.length,
        'esperava ao menos 1 bubble nova pós-reload com a resposta da LIA'
      ).toBeGreaterThan(0)
      expect(
        newOnly.includes('analista financeiro'),
        `resposta NOVA pós-reload deve lembrar o cargo "${distinctTitle}" via wizard_session_pin (got: "${newOnly.slice(0, 400)}")`
      ).toBe(true)

      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })

  // ─────────────────────────────────────────────────────────────────────
  // D3 — Fallback determinístico do JD enrichment
  // ─────────────────────────────────────────────────────────────────────
  test('D3 — JD enrichment cai em fallback sem crashar (LIA_JD_ENRICHMENT_TIMEOUT_S)', async ({
    authenticatedPage: page,
  }, testInfo) => {
    const sensors = attachQualitySensors(page, testInfo)

    try {
      await goToChatHome(page)
      await captureMilestone(page, testInfo, 'D3-00-dashboard')

      // Avança até a etapa de JD enrichment.
      await sendMessageAndWait(
        page,
        'Quero criar uma vaga de Engenheiro de Software Pleno'
      )
      await sendMessageAndWait(page, 'confirma')
      await sendMessageAndWait(page, 'Engenharia, 2 vagas, prazo 30 dias')
      await captureMilestone(page, testInfo, 'D3-01-pre-enrichment')

      // Template card precisa aparecer — caminho determinístico
      // (`_suggest_pipeline_template` em graph.py, Task #1055), independente
      // do Gemini. Se o fallback estiver ativo, o template ainda vem; se
      // o live estiver ativo, idem. Invariante: card visível.
      await expect(
        page.locator(SEL.templateCard),
        'WizardPipelineTemplateCard deve aparecer mesmo com Gemini em fallback'
      ).toBeVisible({ timeout: 60_000 })

      const technical = page.locator(
        '[data-testid="wizard-template-option-technical"]'
      )
      await expect(technical).toBeVisible({ timeout: 5_000 })
      await technical.click()

      // Sentinela: nenhum 5xx em /api/ durante o caminho de enrichment.
      // Isto é o asserto chave do D3 — fallback deve ser TRANSPARENTE
      // (LIA continua respondendo, FE continua renderizando).
      const fiveXX = sensors.networkErrors.filter((e) => e.status >= 500)
      expect(
        fiveXX,
        `JD enrichment (live OU fallback) NÃO deve gerar 5xx (got ${JSON.stringify(fiveXX)})`
      ).toHaveLength(0)

      // Continua mais 1 turno para confirmar que o pipeline segue após
      // o template (must-haves) — qualquer crash silencioso no fallback
      // de jd_enrichment apareceria aqui como timeout/no-bubble.
      const beforeMustHaves = await page.locator(SEL.liaMarkdown).count()
      await sendMessageAndWait(
        page,
        'React, TypeScript, Node.js, comunicação, autonomia'
      )
      const afterMustHaves = await page.locator(SEL.liaMarkdown).count()
      expect(
        afterMustHaves,
        'LIA deve avançar após must-haves mesmo em fallback de enrichment'
      ).toBeGreaterThan(beforeMustHaves)

      // Asserto de DETERMINISMO de fallback — só quando o gate pw-cenario-D
      // (Replit ou GH Actions matrix D) injetou o timeout agressivo. Sem
      // ele, o caminho live é OK e este asserto é skipado. Com ele, o FE
      // recebe `quality_warnings` contendo "fallback determinístico (timeout)"
      // (graph.py L361) e renderiza no painel — comprovando que o caminho
      // de fallback foi REALMENTE exercitado, não só "não-crash".
      const forcedFallback = process.env.LIA_JD_ENRICHMENT_TIMEOUT_S === '0.001'
      if (forcedFallback) {
        await expect
          .poll(async () => {
            // Regex AJUSTADA — exige a frase canônica completa que o
            // graph.py L361 emite ("fallback determinístico (timeout)"),
            // não substring solta como "timeout" que poderia bater em
            // texto de UI não-relacionado (ex.: tooltip de outro campo).
            const body = (await page.locator('body').innerText()).toLowerCase()
            return /fallback determin[ií]stico\s*\(timeout\)/.test(body)
          }, {
            timeout: 30_000,
            message:
              'LIA_JD_ENRICHMENT_TIMEOUT_S=0.001 setado mas o warning canônico "fallback determinístico (timeout)" (graph.py L361) não apareceu no DOM',
          })
          .toBe(true)

        // Task #1112 — a ProgressBar precisa marcar a etapa jd_enrichment
        // como degradada (chip "IA degradada" sobre o ponto da etapa). Sem
        // isso, o recrutador aprova um JD enriquecido só com regex achando
        // que veio do LLM. O badge persiste até o fim do wizard.
        await expect(
          page.locator('[data-testid="wizard-progress-degraded-jd_enrichment"]'),
          'badge "IA degradada" deveria aparecer na etapa jd_enrichment quando *_used_fallback=True (Task #1112)'
        ).toBeVisible({ timeout: 30_000 })
        await expect(
          page.locator('[data-testid="wizard-progress-degraded-summary"]')
            .or(page.locator('[data-testid="wizard-progress-degraded-count"]')),
          'resumo "X etapa(s) rodaram em modo degradado" deveria aparecer na ProgressBar (Task #1112)'
        ).toBeVisible({ timeout: 5_000 })

        // Task #1112 (hidden-stage gate) — `salary` é uma das 4 nodes que
        // emite *_used_fallback (graph.py L1325/L1345), mas NÃO está em
        // PLAN_VISIBLE_STAGES (não tem dot na ProgressBar). Quando o gate
        // pw-cenario-D injetar TAMBÉM `LIA_SALARY_TIMEOUT_S=0.001`, a
        // etapa precisa aparecer no LIST do summary (sem isso, o
        // recrutador aprova um benchmark de salário fallback achando
        // que veio do Pearch/Mercado).
        const forcedSalaryFallback =
          process.env.LIA_SALARY_TIMEOUT_S === '0.001'
        if (forcedSalaryFallback) {
          // Avança o wizard até passar pela etapa salary. Os turnos
          // exatos variam com o orquestrador, mas o sentinel é o list
          // item — pollar até aparecer ou estourar timeout.
          await sendMessageAndWait(page, 'Git, Docker, AWS')
          await sendMessageAndWait(page, 'pode avançar')
          await sendMessageAndWait(
            page,
            'A faixa salarial é de R$ 15.000 a R$ 22.000 CLT'
          )
          await expect(
            page.locator(
              '[data-testid="wizard-progress-degraded-list-salary"]'
            ),
            'etapa salary (oculta dos pontos) deveria aparecer no resumo de etapas degradadas quando LIA_SALARY_TIMEOUT_S=0.001 (Task #1112)'
          ).toBeVisible({ timeout: 60_000 })
        }
      }

      await assertNoAiSlop(page)
    } finally {
      await sensors.attach()
    }
  })
})
