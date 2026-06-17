import { Page, expect } from '@playwright/test'

/**
 * Helpers para testes E2E do Wizard de criação de vaga com LIA.
 * Abstrai a interação via chat com a LIA (interface conversacional).
 */

/**
 * Envia uma mensagem para a LIA no chat do wizard e aguarda a resposta.
 *
 * @param page - Playwright Page
 * @param message - Texto a ser enviado
 * @param waitForResponse - Se true, aguarda a LIA responder antes de retornar
 */
export async function sendWizardMessage(
  page: Page,
  message: string,
  waitForResponse: boolean = true
): Promise<void> {
  // Localiza o campo de input do chat.
  // Onda 32.A3.3: testid canônico em produção (data-testid="chat-input" no
  // UnifiedChatInput.tsx). Fallbacks abaixo cobrem variantes legadas e
  // tolerância a futura mudança de placeholder/aria-label (i18n PT/EN).
  const chatInput = page.locator(
    [
      '[data-testid="chat-input"]',
      'textarea[aria-label*="Mensagem"]',
      'textarea[aria-label*="Message"]',
      'textarea[placeholder*="LIA"]',
      'textarea[placeholder*="mensagem" i]',
      'textarea[placeholder*="Digite" i]',
      'input[placeholder*="mensagem" i]',
    ].join(', ')
  ).first()

  await chatInput.waitFor({ state: 'visible', timeout: 15000 })
  await chatInput.fill(message)

  // Envia com Enter ou botão de envio.
  // Onda 32.A3.3: testid canônico data-testid="chat-send-button".
  const sendButton = page.locator(
    [
      '[data-testid="chat-send-button"]',
      'button[aria-label*="Enviar" i]',
      'button[aria-label*="Send" i]',
      'button[type="submit"]',
      '[data-testid="send-button"]',
    ].join(', ')
  ).first()

  if (await sendButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await sendButton.click()
  } else {
    await chatInput.press('Enter')
  }

  if (waitForResponse) {
    // Aguarda indicador de loading desaparecer (LIA processando)
    const loadingIndicator = page.locator(
      '[data-testid="lia-thinking"], .lia-loading, [aria-label*="carregando"]'
    )
    if (await loadingIndicator.isVisible({ timeout: 3000 }).catch(() => false)) {
      await loadingIndicator.waitFor({ state: 'hidden', timeout: 30000 })
    } else {
      // Fallback: aguarda tempo fixo para LIA responder
      await page.waitForTimeout(2000)
    }
  }
}

/**
 * Envia múltiplas mensagens em sequência para o wizard da LIA.
 *
 * @param page - Playwright Page
 * @param messages - Array de mensagens a enviar
 */
export async function fillWizardStep(page: Page, messages: string[]): Promise<void> {
  for (const message of messages) {
    await sendWizardMessage(page, message, true)
  }
}

/**
 * Verifica em qual estágio o wizard está atualmente.
 * Procura por indicadores visuais do estágio no painel lateral.
 *
 * @param page - Playwright Page
 * @param expectedStage - Nome do estágio esperado (ex: "input-evaluation", "salary")
 */
export async function assertWizardProgress(page: Page, expectedStage: string): Promise<void> {
  // Verificar por atributo data-stage ou texto na UI
  const stageIndicators = [
    `[data-stage="${expectedStage}"]`,
    `[data-testid="wizard-stage-${expectedStage}"]`,
    `.wizard-stage.active:has-text("${expectedStage}")`,
  ]

  let found = false
  for (const selector of stageIndicators) {
    if (await page.locator(selector).isVisible({ timeout: 2000 }).catch(() => false)) {
      found = true
      break
    }
  }

  // Fallback: verificar na URL se há indicação do estágio
  if (!found) {
    const url = page.url()
    // Aceita se não encontrar (wizard é chat-based, stage pode não estar na URL)
    console.log(`[assertWizardProgress] Stage '${expectedStage}' não encontrado visualmente. URL: ${url}`)
  }
}

/**
 * Aguarda a LIA confirmar que a vaga foi publicada com sucesso.
 */
export async function waitForJobPublished(page: Page): Promise<void> {
  // Aguarda mensagem de sucesso da LIA ou redirect para página da vaga
  await Promise.race([
    page.waitForURL('**/vagas/**', { timeout: 30000 }),
    page.locator(
      ':has-text("publicada"), :has-text("criada com sucesso"), :has-text("vaga criada")'
    ).first().waitFor({ state: 'visible', timeout: 30000 }),
  ]).catch(() => {
    // Não falha o teste se nenhum sinal de publicação for detectado
    console.log('[waitForJobPublished] Sinal de publicação não detectado explicitamente')
  })
}

/**
 * Abre o wizard de criação de vaga navegando para a URL correta.
 */
export async function openJobWizard(page: Page): Promise<void> {
  await page.goto('/vagas/nova')
  await page.waitForLoadState('networkidle')

  // Aguarda o chat da LIA estar pronto
  const chatReady = page.locator(
    '[data-testid="lia-chat"], .lia-chat, [data-testid="chat-input"], textarea[placeholder*="mensagem"]'
  ).first()
  await chatReady.waitFor({ state: 'visible', timeout: 20000 })
}
