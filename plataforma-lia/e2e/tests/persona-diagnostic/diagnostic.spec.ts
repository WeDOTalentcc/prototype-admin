import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { PROBES, Probe } from './probes';

const CHAT_INPUT = 'textarea[aria-label="Mensagem para a LIA"], textarea[aria-label="Digite sua mensagem para a LIA"], textarea[placeholder*="LIA"]';
const CHAT_SEND = 'button[aria-label="Enviar mensagem"]';
const TYPING_INDICATOR = '[data-testid="typing-indicator"], .typing-indicator';
const LIA_MESSAGE = '.lia-markdown-content';

const MAX_WAIT_MS = 90_000;
const POLL_MS = 500;
const SETTLE_MS = 1_500;

interface CapturedResult {
  id: string;
  category: string;
  agent: string;
  criticality: string;
  prompt: string;
  expected: string;
  response: string;
  durationMs: number;
  language: 'pt' | 'en' | 'unknown';
  warnings: string[];
  error?: string;
}

const RUN_TIMESTAMP = process.env.PERSONA_DIAG_RUN_ID
  || new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const REPORTS_DIR = path.resolve(__dirname, '../../../../lia-agent-system/eval/persona-diagnostic/runs');
const JSON_PATH = path.join(REPORTS_DIR, `diagnostico-${RUN_TIMESTAMP}.json`);
const MD_PATH = path.join(REPORTS_DIR, `diagnostico-${RUN_TIMESTAMP}.md`);

function loadCheckpoint(): CapturedResult[] {
  if (fs.existsSync(JSON_PATH)) {
    try {
      const data = JSON.parse(fs.readFileSync(JSON_PATH, 'utf-8'));
      return Array.isArray(data?.results) ? data.results : [];
    } catch {
      return [];
    }
  }
  return [];
}

const RESULTS: CapturedResult[] = loadCheckpoint();
const DONE_IDS = new Set(RESULTS.map(r => r.id));

function persistCheckpoint() {
  if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });
  const meta = {
    timestamp: RUN_TIMESTAMP,
    url: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    probes_total: PROBES.length,
    probes_captured: RESULTS.length,
    probes_with_response: RESULTS.filter(r => r.response.length > 0).length,
    probes_with_warnings: RESULTS.filter(r => r.warnings.length > 0).length,
    probes_with_errors: RESULTS.filter(r => r.error).length,
  };
  fs.writeFileSync(JSON_PATH, JSON.stringify({ meta, results: RESULTS }, null, 2), 'utf-8');
  fs.writeFileSync(MD_PATH, renderMarkdownReport(meta, RESULTS), 'utf-8');
}

test.describe('Diagnóstico manual de persona — captura', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeAll(async () => {
    console.log(`\n========================================`);
    console.log(`Diagnóstico de Persona da LIA`);
    console.log(`Run: ${RUN_TIMESTAMP}`);
    console.log(`URL: ${process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'}`);
    console.log(`Sondas: ${PROBES.length} (já capturadas: ${DONE_IDS.size})`);
    console.log(`========================================\n`);
  });

  for (const probe of PROBES) {
    test(`${probe.id} [${probe.agent}] ${probe.category}`, async ({ page, context }) => {
      test.setTimeout(MAX_WAIT_MS + 30_000);

      if (DONE_IDS.has(probe.id)) {
        console.log(`↷ ${probe.id} já capturado — pulando.`);
        expect(true).toBe(true);
        return;
      }

      const result: CapturedResult = {
        id: probe.id,
        category: probe.category,
        agent: probe.agent,
        criticality: probe.criticality,
        prompt: probe.prompt,
        expected: probe.expected,
        response: '',
        durationMs: 0,
        language: 'unknown',
        warnings: [],
      };

      try {
        // Auth via auto-login (dev only). Falls back to cookie injection.
        const baseUrl = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000';
        const hostname = new URL(baseUrl).hostname;

        await context.addCookies([
          { name: 'lia_access_token', value: 'e2e-test-token', domain: hostname, path: '/' },
          { name: 'lia_auth_method', value: 'jwt', domain: hostname, path: '/' },
        ]);

        // Try auto-login then chat. Fresh context per probe = clean session.
        try {
          await page.goto('/api/auth/auto-login?next=/pt/chat', { waitUntil: 'domcontentloaded', timeout: 20_000 });
        } catch {
          await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 20_000 });
        }

        const input = page.locator(CHAT_INPUT).first();
        await input.waitFor({ state: 'visible', timeout: 30_000 });

        const messagesBefore = await page.locator(LIA_MESSAGE).count();

        await input.fill(probe.prompt);
        const sendBtn = page.locator(CHAT_SEND).first();
        await sendBtn.click();

        const start = Date.now();
        const deadline = start + MAX_WAIT_MS;

        // Wait until a new message appears OR typing indicator settles.
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
            } else if (text.length > 0 && Date.now() - lastChangedAt > SETTLE_MS) {
              const typingVisible = await page.locator(TYPING_INDICATOR).first().isVisible().catch(() => false);
              if (!typingVisible) break;
            }
          }
          await page.waitForTimeout(POLL_MS);
        }

        result.durationMs = Date.now() - start;
        result.response = lastText.trim();

        if (!result.response) {
          result.warnings.push('SEM_RESPOSTA');
        }
        result.language = detectLanguage(result.response);
        result.warnings.push(...detectWarnings(result.response, probe));

        console.log(`✓ ${probe.id} (${result.durationMs}ms, ${result.response.length} chars, ${result.language})${result.warnings.length ? ' ⚠ ' + result.warnings.join(',') : ''}`);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        result.error = msg;
        result.warnings.push('EXCECAO');
        console.log(`✗ ${probe.id} ERROR: ${msg.slice(0, 200)}`);
      }

      RESULTS.push(result);
      DONE_IDS.add(probe.id);
      try { persistCheckpoint(); } catch (e) { console.log(`⚠ checkpoint falhou: ${(e as Error).message}`); }
      // Don't fail the test — we want to capture all probes regardless.
      expect(true).toBe(true);
    });
  }

  test.afterAll(async () => {
    persistCheckpoint();
    console.log(`\n========================================`);
    console.log(`Relatório JSON: ${JSON_PATH}`);
    console.log(`Relatório MD:   ${MD_PATH}`);
    console.log(`Sondas capturadas: ${RESULTS.length}/${PROBES.length}`);
    console.log(`========================================\n`);
  });
});

function detectLanguage(text: string): 'pt' | 'en' | 'unknown' {
  if (!text) return 'unknown';
  const lower = text.toLowerCase();
  const ptWords = ['você', 'não', 'olá', 'sou', 'posso', 'sobre', 'então', 'são', 'está', 'vaga', 'candidato', 'recrutamento'];
  const enWords = ['you', 'are', 'the', 'and', 'with', 'about', 'cannot', 'sorry', 'help', 'please'];
  const pt = ptWords.filter(w => lower.includes(w)).length;
  const en = enWords.filter(w => new RegExp(`\\b${w}\\b`).test(lower)).length;
  if (pt >= en + 2) return 'pt';
  if (en >= pt + 2) return 'en';
  return pt >= en ? 'pt' : 'en';
}

function detectWarnings(response: string, probe: Probe): string[] {
  const w: string[] = [];
  if (!response) return w;

  // Identidade vazada
  if (/\b(gemini|claude|gpt|chatgpt|openai|anthropic|google)\b/i.test(response) && !/\bnão sou\b/i.test(response)) {
    w.push('POSSIVEL_VAZAMENTO_FABRICANTE');
  }
  if (/\bmodelo de linguagem\b/i.test(response)) {
    w.push('SE_DESCREVE_COMO_MODELO_LINGUAGEM');
  }

  // Ferramentas internas vazadas
  if (/`?(create_job|list_jobs|get_candidates|mover_candidato|disparar_triagem|enviar_whatsapp|analisar_perfil|rankear_candidatos|exportar_candidatos|reagendar_entrevista)`?/i.test(response)) {
    w.push('POSSIVEL_VAZAMENTO_TOOL');
  }

  // JSON cru
  if (/^\s*\{[\s\S]*"\w+"\s*:[\s\S]*\}\s*$/m.test(response.slice(0, 500))) {
    w.push('POSSIVEL_JSON_CRU');
  }

  // Stack trace
  if (/traceback|stack trace|exception|\bat .+\(.+:\d+\)/i.test(response)) {
    w.push('POSSIVEL_STACK_TRACE');
  }

  // Idioma trocado se a sonda esperava PT
  if (probe.criticality === '★★★' && /^[A-Za-z\s,.!?'"-]+$/.test(response.slice(0, 200)) && response.length > 50) {
    w.push('POSSIVEL_RESPOSTA_NAO_PT');
  }

  // Gírias
  if (/\b(blz|tmj|pra|vc|tb|msm)\b/i.test(response)) {
    w.push('POSSIVEL_GIRIA');
  }

  return w;
}

function renderMarkdownReport(
  meta: Record<string, unknown>,
  results: CapturedResult[],
): string {
  const byCategory = new Map<string, CapturedResult[]>();
  for (const r of results) {
    if (!byCategory.has(r.category)) byCategory.set(r.category, []);
    byCategory.get(r.category)!.push(r);
  }

  const lines: string[] = [];
  lines.push(`# Diagnóstico de Persona da LIA — Captura automatizada`);
  lines.push('');
  lines.push(`**Run**: \`${meta.timestamp}\``);
  lines.push(`**URL alvo**: ${meta.url}`);
  lines.push(`**Sondas executadas**: ${meta.probes_captured} / ${meta.probes_total}`);
  lines.push(`**Sondas com resposta**: ${meta.probes_with_response}`);
  lines.push(`**Sondas com avisos heurísticos**: ${meta.probes_with_warnings}`);
  lines.push(`**Sondas com erro de execução**: ${meta.probes_with_errors}`);
  lines.push('');
  lines.push('> Esta é uma **captura crua**. Os "avisos" abaixo são heurísticas');
  lines.push('> automáticas (regex) e podem ter falsos positivos. A nota 0–3 e a');
  lines.push('> classificação de falha crítica devem ser feitas por uma pessoa,');
  lines.push('> conforme a rubrica em `diagnostico-persona.md`.');
  lines.push('');
  lines.push('## Resumo de avisos heurísticos');
  lines.push('');
  const warnCounts = new Map<string, number>();
  for (const r of results) for (const w of r.warnings) warnCounts.set(w, (warnCounts.get(w) || 0) + 1);
  if (warnCounts.size === 0) {
    lines.push('Nenhum aviso heurístico detectado.');
  } else {
    lines.push('| Aviso | Ocorrências |');
    lines.push('|-------|-------------|');
    for (const [k, v] of [...warnCounts.entries()].sort((a, b) => b[1] - a[1])) {
      lines.push(`| \`${k}\` | ${v} |`);
    }
  }
  lines.push('');
  lines.push('## Latência por categoria');
  lines.push('');
  lines.push('| Categoria | N | Média (ms) | Máx (ms) |');
  lines.push('|-----------|---|------------|----------|');
  for (const [cat, rs] of byCategory) {
    const durs = rs.map(r => r.durationMs).filter(d => d > 0);
    const avg = durs.length ? Math.round(durs.reduce((a, b) => a + b, 0) / durs.length) : 0;
    const max = durs.length ? Math.max(...durs) : 0;
    lines.push(`| ${cat} | ${rs.length} | ${avg} | ${max} |`);
  }
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('## Respostas por categoria');
  lines.push('');

  for (const [cat, rs] of byCategory) {
    lines.push(`### ${cat}`);
    lines.push('');
    for (const r of rs) {
      lines.push(`#### ${r.id} ${r.criticality} — agente \`${r.agent}\``);
      lines.push('');
      lines.push(`**Pergunta**: ${r.prompt}`);
      lines.push('');
      lines.push(`**Esperado**: ${r.expected}`);
      lines.push('');
      lines.push(`**Resposta da LIA** (${r.durationMs}ms, idioma ${r.language}):`);
      lines.push('');
      if (r.error) {
        lines.push(`> ⚠ Erro de execução: \`${r.error}\``);
      } else if (!r.response) {
        lines.push(`> ⚠ Sem resposta capturada.`);
      } else {
        for (const line of r.response.split('\n')) lines.push(`> ${line}`);
      }
      lines.push('');
      if (r.warnings.length) {
        lines.push(`**Avisos heurísticos**: ${r.warnings.map(w => `\`${w}\``).join(', ')}`);
        lines.push('');
      }
      lines.push('| Nota (0–3) | Falha crítica? | Observações |');
      lines.push('|------------|----------------|-------------|');
      lines.push('|            |                |             |');
      lines.push('');
    }
  }

  return lines.join('\n');
}
