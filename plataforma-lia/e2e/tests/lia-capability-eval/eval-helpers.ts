import { test as base, Page, expect } from '@playwright/test';

export const CHAT_INPUT = 'textarea[aria-label="Mensagem para a LIA"], textarea[aria-label="Digite sua mensagem para a LIA"]';
export const CHAT_SEND = 'button[aria-label="Enviar mensagem"]';
export const TYPING_INDICATOR = '[data-testid="typing-indicator"], .typing-indicator';
export const LIA_MESSAGE = '.lia-markdown-content';

export const EVAL_TIMEOUT = 60_000;
export const STREAM_POLL_INTERVAL = 500;

let AUTH_DOMAIN = 'localhost';
try {
  if (process.env.PLAYWRIGHT_BASE_URL) {
    AUTH_DOMAIN = new URL(process.env.PLAYWRIGHT_BASE_URL).hostname;
  }
} catch {}

export interface EvalFixture {
  evalPage: Page;
}

export const test = base.extend<EvalFixture>({
  evalPage: async ({ page, context }, use) => {
    await context.addCookies([
      {
        name: 'lia_access_token',
        value: 'e2e-test-token',
        domain: AUTH_DOMAIN,
        path: '/',
      },
      {
        name: 'lia_auth_method',
        value: 'jwt',
        domain: AUTH_DOMAIN,
        path: '/',
      },
    ]);

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const chatInput = page.locator(CHAT_INPUT).first();
    await chatInput.waitFor({ state: 'visible', timeout: 15_000 });
    await use(page);
  },
});

export { expect };

export type EvalClassification =
  | 'AÇÃO EXECUTADA'
  | 'RESPOSTA COERENTE'
  | 'FALHA'
  | 'ALUCINAÇÃO'
  | 'SEM RESPOSTA';

export interface EvalResult {
  testId: string;
  domain: string;
  prompt: string;
  response: string;
  classification: EvalClassification;
  durationMs: number;
  reason?: string;
}

const evalResults: EvalResult[] = [];

export function recordEval(result: EvalResult): void {
  evalResults.push(result);
}

export function getEvalResults(): EvalResult[] {
  return evalResults;
}

export async function sendPromptAndWait(
  page: Page,
  prompt: string,
  timeoutMs = EVAL_TIMEOUT,
): Promise<{ response: string; durationMs: number }> {
  const start = Date.now();

  const messagesBefore = await page.locator(LIA_MESSAGE).count();

  const input = page.locator(CHAT_INPUT).first();
  await input.waitFor({ state: 'visible', timeout: 10_000 });
  await input.fill(prompt);

  const sendBtn = page.locator(CHAT_SEND).first();
  await sendBtn.click();

  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const currentCount = await page.locator(LIA_MESSAGE).count();
    if (currentCount > messagesBefore) break;

    const typing = page.locator(TYPING_INDICATOR);
    const typingVisible = await typing.isVisible().catch(() => false);
    if (typingVisible) break;

    await page.waitForTimeout(STREAM_POLL_INTERVAL);
  }

  while (Date.now() < deadline) {
    const typing = page.locator(TYPING_INDICATOR);
    const typingVisible = await typing.isVisible().catch(() => false);
    if (!typingVisible) {
      await page.waitForTimeout(1_000);
      const stillTyping = await typing.isVisible().catch(() => false);
      if (!stillTyping) break;
    }
    await page.waitForTimeout(STREAM_POLL_INTERVAL);
  }

  await page.waitForTimeout(500);

  const messagesAfter = await page.locator(LIA_MESSAGE).count();
  if (messagesAfter <= messagesBefore) {
    return { response: '', durationMs: Date.now() - start };
  }

  const newMessage = page.locator(LIA_MESSAGE).nth(messagesAfter - 1);
  const response = (await newMessage.textContent()) || '';
  return { response, durationMs: Date.now() - start };
}

export async function captureResponse(page: Page): Promise<string> {
  const messages = page.locator(LIA_MESSAGE);
  const count = await messages.count();
  if (count === 0) return '';
  const last = messages.nth(count - 1);
  return (await last.textContent()) || '';
}

export const captureLastLiaResponse = captureResponse;

export function classifyResponse(
  response: string,
  positivePatterns: RegExp[],
  negativePatterns: RegExp[] = [/erro\b/i, /error\b/i, /falha\b/i, /não consegui/i],
): EvalClassification {
  if (!response || response.trim().length === 0) return 'SEM RESPOSTA';

  const hallucinationPatterns = [
    /inventei|imaginei|criei.*dados.*fictícios/i,
    /não.*exist.*mas.*aqui/i,
  ];
  for (const h of hallucinationPatterns) {
    if (h.test(response)) return 'ALUCINAÇÃO';
  }

  const systemErrorPatterns = [
    /erro interno/i, /internal error/i, /traceback/i,
    /exception/i, /stack trace/i,
  ];
  for (const e of systemErrorPatterns) {
    if (e.test(response)) return 'FALHA';
  }

  const actionIndicators = [
    /executad[oa]/i, /sucesso/i, /movid[oa]/i, /criad[oa]/i,
    /enviad[oa]/i, /agendad[oa]/i, /pausada/i, /fechada/i,
    /duplicada/i, /reaberta/i, /atualizado/i, /aplicada/i,
    /cadastrad[oa]/i, /iniciada/i, /cancelad[oa]/i,
    /confirmação/i, /deseja confirmar/i,
  ];
  const hasAction = actionIndicators.some(p => p.test(response));
  if (hasAction) return 'AÇÃO EXECUTADA';

  for (const neg of negativePatterns) {
    if (neg.test(response)) return 'FALHA';
  }

  let matchCount = 0;
  for (const pos of positivePatterns) {
    if (pos.test(response)) matchCount++;
  }

  if (matchCount >= Math.ceil(positivePatterns.length * 0.3)) return 'RESPOSTA COERENTE';
  return 'FALHA';
}

export function assertNoError(response: string): void {
  expect(response.length).toBeGreaterThan(0);
  const errorPatterns = [
    /erro interno/i, /internal error/i, /500/,
    /traceback/i, /exception/i, /stack trace/i,
  ];
  for (const p of errorPatterns) {
    expect(response).not.toMatch(p);
  }
}

export function assertContainsAny(response: string, keywords: string[]): void {
  const lower = response.toLowerCase();
  const found = keywords.some(k => lower.includes(k.toLowerCase()));
  expect(found).toBe(true);
}

export function assertContainsAll(response: string, keywords: string[]): void {
  const lower = response.toLowerCase();
  for (const k of keywords) {
    expect(lower).toContain(k.toLowerCase());
  }
}

export function assertIsActionResponse(response: string): void {
  assertNoError(response);
  assertMinLength(response);
  const actionIndicators = [
    /confirmação/i, /confirmar/i, /executad[oa]/i, /sucesso/i,
    /movid[oa]/i, /criad[oa]/i, /enviad[oa]/i, /agendad[oa]/i,
    /qual\s+(candidato|vaga|campo)/i, /para\s+qual/i,
    /deseja\s+(confirmar|continuar|prosseguir)/i,
  ];
  const hasAction = actionIndicators.some(p => p.test(response));
  const isClarification = /qual|especifi|detalh|esclarecer|informar/i.test(response);
  expect(hasAction || isClarification).toBe(true);
}

export function assertIsDenial(response: string): void {
  assertNoError(response);
  assertMinLength(response);
  const denialPatterns = [
    /não posso/i, /não consigo/i, /fora.*escopo/i,
    /não.*permitido/i, /não.*possível/i, /ajudar.*recrutamento/i,
    /como assistente/i, /minha função/i, /posso ajudar/i,
  ];
  const isDenial = denialPatterns.some(p => p.test(response));
  const isRedirect = /posso ajudar|como posso|em que posso/i.test(response);
  expect(isDenial || isRedirect).toBe(true);
}

export function assertMinLength(response: string, minChars = 20): void {
  expect(response.length).toBeGreaterThanOrEqual(minChars);
}

export async function takeEvalScreenshot(page: Page, testId: string): Promise<void> {
  await page.screenshot({
    path: `e2e/reports/${testId}.png`,
    fullPage: false,
  });
}
