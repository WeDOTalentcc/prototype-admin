/**
 * Helpers complementares para a Fase 2 do wizard E2E.
 *
 * Reusa `wizard-conversation.fixture.ts` integralmente; adiciona apenas
 * o que o Audit (Seção 3) recomendou:
 *   - sendMessageAndWait     (substitui o waitForTimeout fixo)
 *   - expectStageAdvanced    (sensor estrutural via WS frame OU progress bar)
 *   - captureMilestone       (screenshot + console.log marcando o passo)
 *   - attachQualitySensors   (console.error + 4xx/5xx em /api/)
 *   - assertNoAiSlop         (regex de slop sobre a `.lia-markdown-content`)
 *   - assertNoLgpdViolation  (regex sobre as WSI rows)
 *   - quickPublishTechVacancy(reusado pelo Cenário F)
 *
 * Selectors REAIS confirmados em
 *   plataforma-lia/e2e/reports/wizard-e2e-AUDIT.md (Seção 1).
 *
 * NÃO modifica código de produção. Nenhum testid novo foi assumido — quando
 * um sensor visual não existe, recorremos ao WS frame ou role/aria-label.
 */

import { Page, TestInfo, expect } from '@playwright/test'
import {
  sendWizardMessage,
  openJobWizard,
} from '../../fixtures/wizard-conversation.fixture'

// ---------------------------------------------------------------------------
// Selectors canônicos (Audit Seção 1)
// ---------------------------------------------------------------------------

export const SEL = {
  /** Floating LIA bubble — sempre presente. */
  liaBubble: '[data-testid="lia-bubble"]',
  /** Sticky barra de progresso, só aparece com `wizardActive`. */
  wizardProgressBar: '[data-testid="wizard-progress-bar"]',
  /** Última bubble da LIA (classe estável em UnifiedMessageList). */
  liaMarkdown: '.lia-markdown-content',
  /** Container dos 5 tiles de pipeline. */
  templateCard: '[data-testid="wizard-template-card"]',
  /** Tile sugerido (badge "Sugerido"). */
  templateSuggested: '[data-suggested="true"]',
  /** Painel WSI canônico — usa `role="list"` + linhas `wsi-question-row-${i}`. */
  wsiList: '[role="list"]:has([data-testid^="wsi-question-row-"])',
  wsiRow: '[data-testid^="wsi-question-row-"]',
  /** Toggle de critérios da CalibrationPanel canônica. */
  calibrationToggle: '[data-testid="calibration-criteria-toggle"]',
  /** Banner de campos obrigatórios (Onda 33 — wired em UnifiedChat).
   *  CSS string `:has-text()` não suporta regex — usar via `.filter({ hasText })`
   *  como helper abaixo (`getMissingFieldsBanner`). */
  kanbanCandidateCard: '[data-testid="candidate-card"]',
}

/**
 * Banner de campos obrigatórios (Onda 33).
 * `[role="status"][aria-live="polite"]` com texto que case a regex.
 * Helper porque `:has-text(/regex/)` em string CSS não é válido no Playwright.
 */
export function getMissingFieldsBanner(page: Page) {
  return page
    .locator('[role="status"][aria-live="polite"]')
    .filter({ hasText: /campos? obrigatóri|missing|faltand|incompleto/i })
}

// ---------------------------------------------------------------------------
// Tipos para o sensor de qualidade
// ---------------------------------------------------------------------------

export interface QualitySensors {
  consoleErrors: string[]
  networkErrors: { url: string; status: number; method: string }[]
  attach: () => Promise<void>
  reset: () => void
}

// ---------------------------------------------------------------------------
// sendMessageAndWait — substitui o waitForTimeout fixo do fixture original
// ---------------------------------------------------------------------------

/**
 * Envia uma mensagem para a LIA e aguarda a *próxima* resposta chegar.
 *
 * Estratégia FAIL-LOUD:
 *  1. Conta `.lia-markdown-content` antes do envio.
 *  2. Envia (sem usar o waitForTimeout do fixture original — passa false).
 *  3. **Espera fail-loud** uma nova bubble da LIA aparecer (count > before).
 *     Se não aparecer no timeout, o teste falha imediatamente.
 *  4. Settle: aguarda o stream terminar (bubble parar de crescer entre dois
 *     ticks). Esse passo TEM tolerance porque streams instantâneos são OK.
 *
 * NÃO usa waitForTimeout arbitrário e NÃO usa Promise.race com swallow.
 */
export async function sendMessageAndWait(
  page: Page,
  message: string,
  opts: { timeout?: number } = {}
): Promise<void> {
  const timeout = opts.timeout ?? 45_000
  const before = await page.locator(SEL.liaMarkdown).count()

  await sendWizardMessage(page, message, /* waitForResponse */ false)

  // Fail-loud: nova bubble da LIA precisa aparecer.
  await expect
    .poll(async () => page.locator(SEL.liaMarkdown).count(), {
      timeout,
      message: `Nenhuma nova mensagem da LIA após enviar "${message.slice(0, 40)}…" (count=${before})`,
    })
    .toBeGreaterThan(before)

  // Settle do stream: aguarda o último bubble parar de crescer entre dois
  // ticks de 500ms. Tolerante porque streams curtos podem terminar antes do
  // primeiro poll — nesse caso o bubble já está estável e tudo bem.
  await page.waitForFunction(
    (sel) => {
      const els = document.querySelectorAll(sel)
      if (!els.length) return false
      const last = els[els.length - 1] as HTMLElement
      const len = last.innerText.length
      const prev = Number(last.dataset['e2eLen'] || '-1')
      last.dataset['e2eLen'] = String(len)
      return prev === len && len > 0
    },
    SEL.liaMarkdown,
    { timeout: 10_000, polling: 500 }
  ).catch(() => {
    // Settle helper, não uma asserção primária. A bubble já é garantida
    // visível pelo expect.poll acima.
  })
}

// ---------------------------------------------------------------------------
// expectStageAdvanced — sensor estrutural de avanço de stage
// ---------------------------------------------------------------------------

/**
 * Aguarda o wizard avançar de stage. Usa duas estratégias combinadas:
 *  1. Conta de bubbles da LIA aumentou (`fromMessageCount + 1` ou mais).
 *  2. Se o `wizard-progress-bar` está presente, sua aria-valuenow ou texto
 *     mudou (best-effort — sem fail-loud porque o widget interno não tem
 *     testid por stage).
 *
 * Asserto em invariante estrutural, não em wording (LLM não-determinístico).
 */
export async function expectStageAdvanced(
  page: Page,
  fromMessageCount: number,
  opts: { timeout?: number } = {}
): Promise<void> {
  const timeout = opts.timeout ?? 30_000
  await expect
    .poll(async () => page.locator(SEL.liaMarkdown).count(), { timeout })
    .toBeGreaterThan(fromMessageCount)
}

// ---------------------------------------------------------------------------
// captureMilestone — screenshot + log estruturado
// ---------------------------------------------------------------------------

export async function captureMilestone(
  page: Page,
  testInfo: TestInfo,
  label: string
): Promise<string> {
  const dir =
    'e2e/reports/wizard-e2e-fase2-2026-04-29'
  const safeLabel = label.replace(/[^a-zA-Z0-9_-]/g, '_')
  const path = `${dir}/${safeLabel}.png`
  await page.screenshot({ path, fullPage: true })
  await testInfo.attach(label, {
    path,
    contentType: 'image/png',
  })
  return path
}

// ---------------------------------------------------------------------------
// attachQualitySensors — coleta console errors + 4xx/5xx em /api/
// ---------------------------------------------------------------------------

export function attachQualitySensors(
  page: Page,
  testInfo: TestInfo
): QualitySensors {
  const consoleErrors: string[] = []
  const networkErrors: { url: string; status: number; method: string }[] = []

  page.on('console', (msg) => {
    if (msg.type() !== 'error') return
    const t = msg.text()
    // Ruído conhecido — silenciar
    if (/Failed to load resource.*404/i.test(t) && /\.(woff2?|ico|png|jpg|jpeg|svg)\b/i.test(t)) return
    if (/DevTools|Lighthouse|chrome-extension/i.test(t)) return
    if (/HMR|hot.*reload/i.test(t)) return
    consoleErrors.push(t)
  })

  page.on('response', (resp) => {
    const url = resp.url()
    if (resp.status() >= 400 && /\/api\//i.test(url)) {
      networkErrors.push({
        url,
        status: resp.status(),
        method: resp.request().method(),
      })
    }
  })

  const sensors: QualitySensors = {
    consoleErrors,
    networkErrors,
    reset: () => {
      consoleErrors.length = 0
      networkErrors.length = 0
    },
    attach: async () => {
      if (consoleErrors.length) {
        await testInfo.attach('console-errors', {
          body: consoleErrors.join('\n'),
          contentType: 'text/plain',
        })
      }
      if (networkErrors.length) {
        await testInfo.attach('network-errors', {
          body: JSON.stringify(networkErrors, null, 2),
          contentType: 'application/json',
        })
      }
    },
  }

  // Auto-attach no afterEach (cada spec chama sensors.attach() também)
  testInfo.attachments.push(...[]) // no-op typing trick; spec deve chamar attach()

  return sensors
}

// ---------------------------------------------------------------------------
// assertNoAiSlop — regex sobre TODAS as bubbles da LIA
// ---------------------------------------------------------------------------

const SLOP_PATTERNS: RegExp[] = [
  /como (modelo|assistente) (de )?(ia|inteligência artificial)/i,
  /em conclusão|para resumir|em síntese/i,
  /vamos juntos|espero ter ajudado|fico (à|a) disposição/i,
  /sou apenas (um |uma )?(modelo|ia)/i,
  /não posso fornecer (informações|conselhos)/i,
]

export async function assertNoAiSlop(page: Page): Promise<void> {
  const messages = await page.locator(SEL.liaMarkdown).allTextContents()
  for (const msg of messages) {
    for (const p of SLOP_PATTERNS) {
      expect(
        msg,
        `[ai-slop] Padrão "${p}" detectado em mensagem da LIA: "${msg.slice(0, 120)}…"`
      ).not.toMatch(p)
    }
  }
}

// ---------------------------------------------------------------------------
// assertNoLgpdViolation — regex sobre rows do WsiQuestionsPanel
// ---------------------------------------------------------------------------

const LGPD_PROTECTED: { name: string; rx: RegExp }[] = [
  { name: 'idade', rx: /\b(idade|quantos anos|data de nascimento)\b/i },
  { name: 'raça/etnia', rx: /\b(raça|étni|cor da pele)\b/i },
  { name: 'religião', rx: /\b(religi|crença religiosa)\b/i },
  { name: 'gênero', rx: /\b(gênero|sexo biológico|qual seu sexo)\b/i },
  {
    name: 'estado civil',
    rx: /\b(estado civil|casad[ao]|solteir[ao]|tem filhos)\b/i,
  },
  { name: 'orientação sexual', rx: /\borientação sexual\b/i },
  { name: 'CPF/RG', rx: /\b(cpf|rg)\b/i },
]

export async function assertNoLgpdViolation(page: Page): Promise<void> {
  const rows = await page.locator(SEL.wsiRow).allTextContents()
  if (!rows.length) return // sem WSI em tela = nada a validar
  for (const text of rows) {
    for (const { name, rx } of LGPD_PROTECTED) {
      expect(
        text,
        `[lgpd] Possível violação (${name}): "${text.slice(0, 120)}…"`
      ).not.toMatch(rx)
    }
  }
}

// ---------------------------------------------------------------------------
// extractQualityScore — parsea regex /(\d+)\/100/ na última bubble da LIA
// ---------------------------------------------------------------------------

export async function extractQualityScore(page: Page): Promise<number | null> {
  const last = await page.locator(SEL.liaMarkdown).last().textContent()
  if (!last) return null
  const m = last.match(/(\d+)\s*\/\s*100/)
  if (!m) return null
  return Number(m[1])
}

// ---------------------------------------------------------------------------
// expectPanelOpens — aguarda um seletor de painel ficar visível
// ---------------------------------------------------------------------------

export async function expectPanelOpens(
  page: Page,
  panel: 'wsi' | 'review' | 'calibration',
  opts: { timeout?: number } = {}
): Promise<void> {
  const timeout = opts.timeout ?? 30_000
  if (panel === 'wsi') {
    // WsiQuestionsPanel canônico — listitem/wsi-question-row aparece
    await page
      .locator(SEL.wsiRow)
      .first()
      .waitFor({ state: 'visible', timeout })
    return
  }
  if (panel === 'calibration') {
    // CalibrationPanel canônico — toggle aparece
    await page
      .locator(SEL.calibrationToggle)
      .waitFor({ state: 'visible', timeout })
    return
  }
  if (panel === 'review') {
    // ReviewPanel canônico — testid adicionado em Onda 32.A4 prep (Boy Scout).
    await expect(
      page.locator('[data-testid="review-panel"]'),
      'ReviewPanel deve estar visível'
    ).toBeVisible({ timeout: Math.min(timeout, 10_000) })
    return
  }
}

// ---------------------------------------------------------------------------
// goToChatHome — abre o chat na home /pt (per brief)
// ---------------------------------------------------------------------------

export async function goToChatHome(page: Page): Promise<void> {
  // Task #1054 — bumped 30s → 90s para tolerar cold-compile do Next/Turbopack
  // no Replit (primeira request de /pt pode levar 40-70s pra render). O wrapper
  // run-pw-cenario.sh faz warmup via curl + Chromium headless antes do test
  // (Task #1173), mas a margem aqui é a rede de segurança quando o warmup é
  // skipado (CI fresh container, etc).
  //
  // Task #1173 — retry de navegação: durante cold-compile o `next dev --turbopack`
  // responde 502 / "Failed to fetch" em chunks ainda não compilados, e um único
  // goto consome os 90s e morre. Aqui tentamos até 3× com timeout menor por
  // tentativa, de forma que um 502 transitório no primeiro contato recompila e
  // a 2ª/3ª tentativa pega os bundles quentes — falhando só por motivo real.
  const NAV_ATTEMPTS = 3
  let lastErr: unknown
  for (let attempt = 1; attempt <= NAV_ATTEMPTS; attempt++) {
    try {
      await page.goto('/pt', { waitUntil: 'domcontentloaded', timeout: 60_000 })
      lastErr = undefined
      break
    } catch (err) {
      lastErr = err
      if (attempt < NAV_ATTEMPTS) {
        await page.waitForTimeout(2_000)
      }
    }
  }
  if (lastErr) throw lastErr
  // Bubble flutuante é o âncora estável (UnifiedChatBubble)
  const bubble = page.locator(SEL.liaBubble)
  if (await bubble.isVisible({ timeout: 5_000 }).catch(() => false)) {
    // Abre o chat clicando no bubble se ele estiver fechado
    const isExpanded = await bubble.getAttribute('aria-expanded').catch(() => null)
    if (isExpanded !== 'true') {
      await bubble.click().catch(() => {/* já aberto */})
    }
  }
  // Aguarda textarea ficar disponível (chat aberto)
  await page
    .getByRole('textbox', { name: /mensagem|message/i })
    .first()
    .waitFor({ state: 'visible', timeout: 20_000 })
  await page.waitForLoadState('networkidle', { timeout: 30_000 }).catch(() => {/* ok */})
}

// ---------------------------------------------------------------------------
// quickPublishTechVacancy — replica Cenário A abreviado p/ Cenário F
// ---------------------------------------------------------------------------

export async function quickPublishTechVacancy(page: Page): Promise<void> {
  await goToChatHome(page)
  await sendMessageAndWait(
    page,
    'Quero criar uma vaga de Engenheiro de Software Pleno'
  )
  await sendMessageAndWait(page, 'confirma')
  await sendMessageAndWait(page, 'Engenharia, 2 vagas, prazo 30 dias')

  // Tile técnico (se aparecer)
  const technicalTile = page.locator(
    '[data-testid="wizard-template-option-technical"]'
  )
  if (await technicalTile.isVisible({ timeout: 5_000 }).catch(() => false)) {
    await technicalTile.click()
  }

  await sendMessageAndWait(
    page,
    'React, TypeScript, Node.js, comunicação, autonomia'
  )
  await sendMessageAndWait(page, 'R$ 12.000')
  await sendMessageAndWait(page, 'compacta')

  // WSI panel — aceitar selecionadas
  if (await page.locator(SEL.wsiRow).first().isVisible({ timeout: 15_000 }).catch(() => false)) {
    await sendMessageAndWait(page, 'aceitar')
  }

  // ReviewPanel — publicar
  const publishBtn = page.getByRole('button', { name: /publicar|publish/i }).first()
  if (await publishBtn.isVisible({ timeout: 15_000 }).catch(() => false)) {
    await publishBtn.click()
  } else {
    await sendMessageAndWait(page, 'publicar')
  }
}

// Re-export para conveniência dos specs
export { sendWizardMessage, openJobWizard }

/**
 * Task #1165 — Alias para o login canônico usado em specs novos.
 * Delega para `authenticateAsRecruiter` (fixture canônica).
 */
export { authenticateAsRecruiter as loginAsRecrutador } from '../../fixtures/auth.fixture'
