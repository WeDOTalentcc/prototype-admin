/**
 * Helpers para testes de capabilities da LIA.
 *
 * Convenções:
 *   - Cada capability vira um test isolado que envia 1 prompt via chat
 *   - Validação primária: POST /chat/message retorna 200 + content não-vazio
 *   - Validação secundária (opcional): intent detectado, entities presentes
 *
 * Uso:
 *   test("lista vagas abertas", async ({ page }) => {
 *     const result = await sendPromptAndCapture(page, "liste minhas vagas abertas")
 *     expectCapabilitySuccess(result, { shouldMention: ["vaga"] })
 *   })
 */
import { expect, type Page, type Response } from "@playwright/test"

export interface ChatCapture {
  /** Status HTTP da requisição */
  status: number
  /** Body JSON de /chat/message */
  body: {
    content?: string
    conversation_id?: string
    message_metadata?: {
      intent?: string
      entities?: Record<string, unknown>
      context_data?: { type?: string; title?: string }
    }
    [key: string]: unknown
  }
  /** Tempo total da resposta em ms */
  durationMs: number
}

/**
 * Abre o chat no modo Sidebar/Full caso não esteja visível.
 */
export async function ensureChatOpen(page: Page) {
  const textarea = page.locator('textarea[placeholder*="LIA"]').first()
  if (!(await textarea.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: /Conversar|Chat LIA/i }).first().click().catch(() => {})
    await textarea.waitFor({ state: "visible", timeout: 5000 })
  }
  return textarea
}

/**
 * Envia um prompt e captura o resultado do /chat/message.
 * Funciona tanto para WebSocket quanto REST (no REST, captura request/response;
 * no WS, faz poll de UI até aparecer a última mensagem do assistant).
 */
export async function sendPromptAndCapture(
  page: Page,
  prompt: string,
  timeoutMs = 20000,
): Promise<ChatCapture> {
  const textarea = await ensureChatOpen(page)
  await textarea.fill(prompt)

  const start = Date.now()

  // Tenta capturar o POST /chat/message (caminho REST/SSE)
  const responsePromise = page
    .waitForResponse(
      (res: Response) =>
        res.url().includes("/api/backend-proxy/chat/message") &&
        res.request().method() === "POST",
      { timeout: timeoutMs },
    )
    .catch(() => null)

  await page.getByRole("button", { name: /enviar mensagem/i }).click()

  const res = await responsePromise
  const durationMs = Date.now() - start

  if (!res) {
    // Fallback: WebSocket — esperar última mensagem do assistant aparecer no DOM
    const lastAssistantMsg = page
      .locator('[data-role="assistant"], [data-testid="assistant-message"]')
      .last()
    await lastAssistantMsg.waitFor({ state: "visible", timeout: timeoutMs })
    const content = (await lastAssistantMsg.textContent()) || ""
    return {
      status: 200,
      body: { content },
      durationMs: Date.now() - start,
    }
  }

  const body = await res.json().catch(() => ({}))
  return { status: res.status(), body, durationMs }
}

/**
 * Asserções padrão de sucesso de uma capability.
 *
 * @param result   Output de sendPromptAndCapture
 * @param opts     Expectativas opcionais (palavras que devem aparecer, tool esperada, etc)
 */
export function expectCapabilitySuccess(
  result: ChatCapture,
  opts: {
    shouldMention?: string[]
    shouldNotMention?: string[]
    expectedIntent?: string | RegExp
    minContentLength?: number
    allowLenientFail?: boolean // para capabilities com alto custo (ex: Pearch) — permitir "não implementado" como aceitável
  } = {},
) {
  const {
    shouldMention = [],
    shouldNotMention = [],
    expectedIntent,
    minContentLength = 10,
    allowLenientFail = false,
  } = opts

  // 1) HTTP: 200 OK sempre. 502 é regressão do BUG-01.
  expect(
    result.status,
    `Esperava 200, recebi ${result.status}. Body: ${JSON.stringify(result.body).slice(0, 300)}`,
  ).toBe(200)

  // 2) content existe e tem conteúdo mínimo
  const content = (result.body.content || "").trim()
  if (allowLenientFail && content.length === 0) {
    // Capability pode retornar vazio em cenários sem dados — não falhar
    return
  }
  expect(
    content.length,
    `Content vazio ou muito curto (${content.length} chars). Content: "${content.slice(0, 200)}"`,
  ).toBeGreaterThanOrEqual(minContentLength)

  // 3) menções obrigatórias
  const lowerContent = content.toLowerCase()
  for (const word of shouldMention) {
    expect(
      lowerContent.includes(word.toLowerCase()),
      `Esperava "${word}" em content. Recebi: "${content.slice(0, 300)}"`,
    ).toBe(true)
  }

  // 4) menções proibidas (PII, hallucination, bias)
  for (const word of shouldNotMention) {
    expect(
      lowerContent.includes(word.toLowerCase()),
      `Content NÃO deveria mencionar "${word}". Content: "${content.slice(0, 300)}"`,
    ).toBe(false)
  }

  // 5) intent detectado (se aplicável)
  if (expectedIntent) {
    const actualIntent = result.body.message_metadata?.intent || ""
    if (expectedIntent instanceof RegExp) {
      expect(
        expectedIntent.test(actualIntent),
        `Intent esperado ~${expectedIntent}, obtido "${actualIntent}"`,
      ).toBe(true)
    } else {
      expect(actualIntent).toBe(expectedIntent)
    }
  }
}

/**
 * Navega para uma página do app via sidebar (usa text match no botão do menu).
 */
export async function navigateToPage(page: Page, pageName: string) {
  await page
    .getByRole("button", { name: new RegExp(`^${pageName}`, "i") })
    .first()
    .click()
  await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {})
  await page.waitForTimeout(800) // deixa animação terminar
}

/**
 * Prepara o grid de resultados — coleta PASS/FAIL por capability para reporter.
 */
export interface CapabilityResult {
  id: string
  prompt: string
  domain: string
  status: "PASS" | "FAIL" | "SKIP"
  durationMs: number
  errorMessage?: string
}

export const capabilityResults: CapabilityResult[] = []

export function recordResult(r: CapabilityResult) {
  capabilityResults.push(r)
}
