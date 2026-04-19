/**
 * Agentic Eval — driver spec.
 *
 * Loads every YAML scenario from
 * `lia-agent-system/eval/agentic_cases/`, runs each one through the LIA
 * chat with the Python user-simulator playing the recruiter, captures the
 * transcript + observed tool calls, and writes one JSON output per run.
 *
 * The judge (`judge_agentic.py`) and report (`eval_report_agentic.py`)
 * consume the output downstream — see `docs/eval/AGENTIC_EVAL_PLAYBOOK.md`.
 */
import { test, expect } from '../../fixtures/auth.fixture';
import * as fs from 'fs';
import * as path from 'path';
import * as YAML from 'yaml';
import {
  openChatOnPage,
  sendOneTurn,
  SimulatorProcess,
  ChatTurnCapture,
} from './agentic-helpers';

const REPO_ROOT = path.resolve(__dirname, '../../../..');
const CASES_DIR = path.join(REPO_ROOT, 'lia-agent-system/eval/agentic_cases');
const RUNS_DIR = path.join(REPO_ROOT, 'lia-agent-system/eval/agentic/runs');
const RUN_TIMESTAMP = process.env.AGENTIC_RUN_ID
  || new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const OUT_PATH = path.join(RUNS_DIR, `agentic-${RUN_TIMESTAMP}.json`);

// Default to k=5 for any scenario tagged @passk so the D9 consistency
// dimension actually runs out of the box. Override with AGENTIC_PASS_K=1
// for a fast smoke run.
const PASS_K = parseInt(process.env.AGENTIC_PASS_K || '5', 10);
const MAX_TURNS_HARD_CAP = 8;

interface Scenario {
  id: string;
  meta?: { version?: string };
  tags?: string[];
  severity?: 'critical' | 'high' | 'medium' | 'low';
  goal?: string;
  setup_notes?: string;
  setup?: Record<string, unknown>;
  // canonical: pageContext (camelCase). page_context (snake_case) accepted as alias.
  pageContext?: { scope?: string; page?: string };
  page_context?: { scope?: string; page?: string };
  persona?: Record<string, unknown>;
  turns: { user: string }[];
  facts_you_know?: Record<string, unknown>;
  facts_you_do_not_know?: string[];
  expected_tools?: string[];
  expected_state_after?: Array<Record<string, unknown>>;
  expected_proactive_actions?: string[];
  judge_rubric?: string;
  stop_when?: string;
}

interface RunResult {
  scenario_id: string;
  run_index: number;
  tags: string[];
  severity: string;
  goal: string;
  setup_notes: string;
  scope: string;
  page: string;
  expected_tools: string[];
  expected_state_after: Array<Record<string, unknown>>;
  expected_proactive_actions: string[];
  judge_rubric?: string;
  transcript: { role: 'user' | 'lia'; content: string }[];
  observed_tools: { name: string; args?: Record<string, unknown> }[];
  total_turns: number;
  total_duration_ms: number;
  errored?: string;
}

function loadScenarios(): Scenario[] {
  if (!fs.existsSync(CASES_DIR)) return [];
  const files = fs.readdirSync(CASES_DIR).filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));
  const out: Scenario[] = [];
  for (const f of files) {
    try {
      const doc = YAML.parse(fs.readFileSync(path.join(CASES_DIR, f), 'utf-8'));
      const list = Array.isArray(doc?.scenarios) ? doc.scenarios : (Array.isArray(doc) ? doc : [doc]);
      for (const s of list) if (s && s.id) out.push(s as Scenario);
    } catch (e) {
      console.error(`Failed to parse ${f}:`, (e as Error).message);
    }
  }
  out.sort((a, b) => a.id.localeCompare(b.id));
  return out;
}

const SCENARIOS = loadScenarios();
const RESULTS: RunResult[] = [];

function persist() {
  if (!fs.existsSync(RUNS_DIR)) fs.mkdirSync(RUNS_DIR, { recursive: true });
  const meta = {
    timestamp: RUN_TIMESTAMP,
    base_url: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    pass_k: PASS_K,
    scenarios_total: SCENARIOS.length,
    scenarios_run: RESULTS.length,
  };
  fs.writeFileSync(OUT_PATH, JSON.stringify({ meta, results: RESULTS }, null, 2), 'utf-8');
}

test.describe('Agentic Eval Roteiro', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeAll(() => {
    console.log(`\n========================================`);
    console.log(`Agentic Eval — ${SCENARIOS.length} scenarios, pass^k=${PASS_K}`);
    console.log(`Run: ${RUN_TIMESTAMP}`);
    console.log(`Output: ${OUT_PATH}`);
    console.log(`========================================\n`);
  });

  for (const scenario of SCENARIOS) {
    const tagSuffix = (scenario.tags || []).map(t => `@${t}`).join(' ');
    // Determine k for this scenario: only @passk-tagged scenarios get k>1
    const isPassK = (scenario.tags || []).includes('passk');
    const runs = isPassK ? PASS_K : 1;

    for (let i = 0; i < runs; i++) {
      const label = runs > 1 ? `${scenario.id} #${i + 1}/${runs} ${tagSuffix}` : `${scenario.id} ${tagSuffix}`;
      test(label, async ({ authenticatedPage: page }) => {
        test.setTimeout(180_000);
        // Normalise pageContext (camelCase canonical) ← page_context (snake legacy).
        const ctx = scenario.pageContext || scenario.page_context || {};
        const scope = ctx.scope || 'global';
        const pagePath = ctx.page || 'chat';
        const severity = scenario.severity
          || (scenario.tags || []).find(t => ['critical', 'high', 'medium', 'low'].includes(t))
          || 'medium';

        const result: RunResult = {
          scenario_id: scenario.id,
          run_index: i,
          tags: scenario.tags || [],
          severity,
          goal: scenario.goal || '',
          setup_notes: scenario.setup_notes || '',
          scope,
          page: pagePath,
          expected_tools: scenario.expected_tools || [],
          expected_state_after: scenario.expected_state_after || [],
          expected_proactive_actions: scenario.expected_proactive_actions || [],
          judge_rubric: scenario.judge_rubric,
          transcript: [],
          observed_tools: [],
          total_turns: 0,
          total_duration_ms: 0,
        };

        const sim = new SimulatorProcess(JSON.stringify(scenario));
        const startedAt = Date.now();

        try {
          await openChatOnPage(page, scope, pagePath);

          let userMsg = await sim.opening();
          let turn = 0;
          while (userMsg && userMsg !== '[END]' && turn < MAX_TURNS_HARD_CAP) {
            turn++;
            const cap: ChatTurnCapture = await sendOneTurn(page, userMsg);
            result.transcript.push({ role: 'user', content: userMsg });
            result.transcript.push({ role: 'lia', content: cap.lia });
            result.observed_tools.push(...cap.observedTools.map(t => ({ name: t.name, args: t.args })));
            userMsg = await sim.respondTo(cap.lia);
          }
          result.total_turns = turn;
          if (userMsg && userMsg !== '[END]' && turn >= MAX_TURNS_HARD_CAP) {
            result.errored = `MAX_TURNS_REACHED (${MAX_TURNS_HARD_CAP})`;
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          result.errored = msg;
          console.log(`  ✗ ${scenario.id}#${i} ERROR: ${msg.slice(0, 200)}`);
        } finally {
          sim.close();
        }
        result.total_duration_ms = Date.now() - startedAt;
        RESULTS.push(result);
        persist();
        console.log(`  ✓ ${scenario.id}#${i} (${result.total_turns} turns, ${result.observed_tools.length} tool calls, ${result.total_duration_ms}ms)`);
        // Capture-only mode: never fail the test on response quality —
        // the judge does that downstream.
        expect(true).toBe(true);
      });
    }
  }

  test.afterAll(() => {
    persist();
    console.log(`\n========================================`);
    console.log(`Captured ${RESULTS.length} runs`);
    console.log(`File: ${OUT_PATH}`);
    console.log(`Next: python lia-agent-system/eval/agentic/judge_agentic.py ${OUT_PATH}`);
    console.log(`========================================\n`);
  });
});
