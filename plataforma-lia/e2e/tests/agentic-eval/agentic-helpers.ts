import { type Page, type Request, type Response } from '@playwright/test';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import * as path from 'path';

const CHAT_INPUT = 'textarea[aria-label="Mensagem para a LIA"], textarea[aria-label="Digite sua mensagem para a LIA"], textarea[placeholder*="LIA"]';
const CHAT_SEND = 'button[aria-label="Enviar mensagem"]';
const TYPING_INDICATOR = '[data-testid="typing-indicator"], .typing-indicator';
const LIA_MESSAGE = '.lia-markdown-content';

export interface ObservedToolCall {
  name: string;
  args?: Record<string, unknown>;
  ok: boolean;
  status: number;
}

export interface ChatTurnCapture {
  user: string;
  lia: string;
  durationMs: number;
  observedTools: ObservedToolCall[];
}

/**
 * Navigate an already-authenticated page to the scenario's screen and
 * open the LIA chat panel. Authentication itself is handled by the
 * shared `auth.fixture.ts` (`authenticatedPage` fixture); this helper
 * only does the page-level setup.
 */
export async function openChatOnPage(page: Page, _scope: string, pagePath: string) {
  await page.goto(`/pt/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
  const input = page.locator(CHAT_INPUT).first();
  if (!(await input.isVisible().catch(() => false))) {
    await page.getByRole('button', { name: /Conversar|Chat LIA/i }).first().click().catch(() => {});
  }
  await input.waitFor({ state: 'visible', timeout: 30_000 });
}

/**
 * Send one message, wait for LIA to settle, return the new reply text and
 * any tool calls observed via /api/v1/chat or /chat/message.
 */
export async function sendOneTurn(
  page: Page,
  message: string,
  opts: { maxWaitMs?: number; settleMs?: number; pollMs?: number } = {},
): Promise<ChatTurnCapture> {
  const maxWaitMs = opts.maxWaitMs ?? 90_000;
  const settleMs = opts.settleMs ?? 1500;
  const pollMs = opts.pollMs ?? 500;

  const observedTools: ObservedToolCall[] = [];
  // Collect every parse promise so we can await them before returning —
  // otherwise late-resolving response bodies are dropped and the tool
  // call diff under-reports (race that breaks D4/D6/D9 capture).
  const pendingParses: Promise<unknown>[] = [];
  const handler = (resp: Response) => {
    const url = resp.url();
    if (!/\/api\/v1\/chat|\/chat\/message/.test(url)) return;
    pendingParses.push(
      resp.json().then((body: any) => {
        const calls = extractToolCalls(body);
        for (const c of calls) {
          observedTools.push({ name: c.name, args: c.args, ok: resp.ok(), status: resp.status() });
        }
      }).catch(() => undefined),
    );
  };
  page.on('response', handler);

  const input = page.locator(CHAT_INPUT).first();
  const messagesBefore = await page.locator(LIA_MESSAGE).count();
  await input.fill(message);
  await page.locator(CHAT_SEND).first().click({ force: true });

  const start = Date.now();
  const deadline = start + maxWaitMs;
  let lastText = '';
  let lastChangedAt = Date.now();
  while (Date.now() < deadline) {
    const count = await page.locator(LIA_MESSAGE).count();
    if (count > messagesBefore) {
      const newMsg = page.locator(LIA_MESSAGE).nth(count - 1);
      const text = (await newMsg.textContent().catch(() => '')) || '';
      if (text !== lastText) {
        lastText = text;
        lastChangedAt = Date.now();
      } else if (text.length > 0 && Date.now() - lastChangedAt > settleMs) {
        const typing = await page.locator(TYPING_INDICATOR).first().isVisible().catch(() => false);
        if (!typing) break;
      }
    }
    await page.waitForTimeout(pollMs);
  }
  page.off('response', handler);
  // Drain in-flight response.json() parses so observedTools is complete.
  await Promise.allSettled(pendingParses);

  return {
    user: message,
    lia: lastText.trim(),
    durationMs: Date.now() - start,
    observedTools,
  };
}

function extractToolCalls(body: any): { name: string; args?: Record<string, unknown> }[] {
  if (!body || typeof body !== 'object') return [];
  const out: { name: string; args?: Record<string, unknown> }[] = [];
  const containers: any[] = [body, body?.metadata, body?.data, body?.result, body?.message];
  for (const c of containers) {
    if (!c || typeof c !== 'object') continue;
    const arr = c.tool_calls || c.tool_calls_requested || c.tools || c.actions;
    if (Array.isArray(arr)) {
      for (const t of arr) {
        if (typeof t === 'string') out.push({ name: t });
        else if (t && typeof t === 'object' && t.name) out.push({ name: t.name, args: t.arguments || t.args || t.params });
      }
    }
  }
  return out;
}

/** Spawn the Python user-simulator and return a minimal IPC client over stdio. */
export class SimulatorProcess {
  private proc: ChildProcessWithoutNullStreams;
  private buffer = '';
  private resolvers: ((s: string) => void)[] = [];

  constructor(scenarioJson: string) {
    const repoRoot = path.resolve(__dirname, '../../../..');
    const py = process.env.PYTHON_BIN || 'python3';
    const script = path.join(repoRoot, 'lia-agent-system/eval/agentic/_simulator_ipc.py');
    this.proc = spawn(py, [script], {
      env: { ...process.env, AGENTIC_SCENARIO_JSON: scenarioJson },
      cwd: repoRoot,
    });
    this.proc.stdout.setEncoding('utf-8');
    this.proc.stdout.on('data', (chunk: string) => {
      this.buffer += chunk;
      let nl: number;
      while ((nl = this.buffer.indexOf('\n')) >= 0) {
        const line = this.buffer.slice(0, nl).trim();
        this.buffer = this.buffer.slice(nl + 1);
        if (line && this.resolvers.length) {
          const r = this.resolvers.shift()!;
          r(line);
        }
      }
    });
    this.proc.stderr.on('data', (d: Buffer) => process.stderr.write(`[sim] ${d}`));
  }

  async opening(): Promise<string> {
    return this.send('OPEN');
  }

  async respondTo(liaReply: string): Promise<string> {
    return this.send(`REPLY ${JSON.stringify(liaReply)}`);
  }

  close() {
    try { this.proc.stdin.write('QUIT\n'); } catch {}
    try { this.proc.kill(); } catch {}
  }

  private send(line: string): Promise<string> {
    return new Promise((resolve) => {
      this.resolvers.push(resolve);
      this.proc.stdin.write(line + '\n');
    });
  }
}
