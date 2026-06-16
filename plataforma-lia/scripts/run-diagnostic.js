#!/usr/bin/env node
/**
 * LIA Unified Diagnostic Battery — Orchestrator
 *
 * Usage (via npm):
 *   npm run diagnostic                       # full battery
 *   npm run diagnostic -- --stage smoke      # preflight + smoke only
 *   npm run diagnostic -- --stage critical   # preflight + smoke + critical
 *   npm run diagnostic -- --grep @d4         # only D4 scenarios
 *   npm run diagnostic -- --k 3              # pass^k with k=3 instead of 5
 *   npm run diagnostic -- --bail             # stop on first stage failure
 *   npm run diagnostic -- --no-python        # skip golden/persona Python stages
 *
 * Stages (in order):
 *   preflight → smoke → critical → agentic → passk → persona → golden
 *
 * Environment variables:
 *   PLAYWRIGHT_BASE_URL   Frontend URL (default: http://localhost:5000)
 *   LIA_BACKEND_URL       Backend URL  (default: http://localhost:8001)
 *   ANTHROPIC_API_KEY     LLM key (required for judge + simulator)
 *   AGENTIC_PASS_K        k for pass^k (default: 5)
 *   LIA_TEST_TOKEN        JWT for the seed recruiter (required for preflight PF-02–PF-04)
 *   DIAGNOSTIC_STAGE      Override --stage from env
 */
'use strict';
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '../..');
const PLATAFORMA = path.resolve(__dirname, '..');
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const REPORT_DIR = path.join(PLATAFORMA, 'playwright-report', 'diagnostic');
const DOCS_REPORT_DIR = path.join(REPO_ROOT, 'docs', 'eval', 'reports');

// ── Argument parsing ─────────────────────────────────────────────────────────

const args = process.argv.slice(2);
function flag(name) { return args.includes(`--${name}`); }
function option(name, fallback) {
  const idx = args.indexOf(`--${name}`);
  return idx >= 0 && idx + 1 < args.length
    ? args[idx + 1]
    : (process.env[name.toUpperCase().replace(/-/g, '_')] || fallback || '');
}

const STAGE    = option('stage', process.env.DIAGNOSTIC_STAGE || 'full');
const GREP     = option('grep', '');
const PASS_K   = option('k', process.env.AGENTIC_PASS_K || '5');
const BAIL     = flag('bail');
const NO_PYTHON = flag('no-python');
// When set, SM-07 and SM-08 are NOT skipped even when E2E_ADMIN_TOKEN /
// E2E_CANDIDATE_TOKEN are absent — the tests run and fail naturally,
// making 3-role smoke a hard gate (useful for release-grade CI runs).
const REQUIRE_ALL_ROLES = flag('require-all-roles') || process.env.REQUIRE_ALL_ROLES === '1';

const STAGES_FULL = ['preflight', 'smoke', 'critical', 'agentic', 'judge', 'passk', 'persona', 'golden'];
const STAGE_CUTOFFS = {
  preflight: 0, smoke: 1, critical: 2, agentic: 3, judge: 4, passk: 5, persona: 6, golden: 7, full: 7,
};
const maxStageIdx = STAGE_CUTOFFS[STAGE] !== undefined ? STAGE_CUTOFFS[STAGE] : 7;
const ACTIVE_STAGES = STAGES_FULL.filter((_, i) => i <= maxStageIdx);

// ── Helpers ──────────────────────────────────────────────────────────────────

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function log(msg) {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] ${msg}`);
}

/**
 * Run a Playwright config. Does NOT pass --reporter on the CLI so each
 * config's own reporter array (including JSON reporters) is honoured.
 */
function runPlaywright(config, opts) {
  opts = opts || {};
  const cmd = ['npx', 'playwright', 'test', '--config', config];
  if (opts.grep) cmd.push('--grep', opts.grep);

  const env = Object.assign({}, process.env, {
    AGENTIC_PASS_K: PASS_K,
    AGENTIC_RUN_ID: TIMESTAMP,
  }, opts.env || {});

  log(`Running: ${cmd.join(' ')}`);
  try {
    execSync(cmd.join(' '), {
      cwd: PLATAFORMA,
      env,
      stdio: 'inherit',
      timeout: opts.timeoutMs || 600_000,
    });
    return { ok: true, output: '' };
  } catch (err) {
    return { ok: false, output: String(err.message || err) };
  }
}

function runPython(script, extraArgs) {
  extraArgs = extraArgs || [];
  const cmd = ['python', script, ...extraArgs].join(' ');
  log(`Running: ${cmd}`);
  try {
    execSync(cmd, {
      cwd: REPO_ROOT,
      env: process.env,
      stdio: 'inherit',
      timeout: 300_000,
    });
    return { ok: true, output: '' };
  } catch (err) {
    return { ok: false, output: String(err.message || err) };
  }
}

// ── Stage runner ─────────────────────────────────────────────────────────────

const stageResults = [];

function runStage(name, fn) {
  log(`\n${'='.repeat(60)}`);
  log(`STAGE: ${name.toUpperCase()}`);
  log(`${'='.repeat(60)}`);
  const t0 = Date.now();
  let result;
  try {
    result = fn();
  } catch (err) {
    result = { ok: false, output: String(err) };
  }
  const durationMs = Date.now() - t0;
  stageResults.push({ stage: name, ok: result.ok, skipped: false, durationMs });
  persistStageResults();
  if (result.ok) {
    log(`✓ ${name} passed (${(durationMs / 1000).toFixed(1)}s)`);
  } else {
    log(`✗ ${name} FAILED (${(durationMs / 1000).toFixed(1)}s)`);
  }
  return result.ok;
}

function skipStage(name) {
  stageResults.push({ stage: name, ok: true, skipped: true, durationMs: 0 });
  persistStageResults();
  log(`  ⟳ ${name} skipped (out of scope for stage="${STAGE}")`);
}

function persistStageResults() {
  ensureDir(REPORT_DIR);
  const summary = {
    run_id: TIMESTAMP,
    stage: STAGE,
    pass_k: PASS_K,
    stages: stageResults,
  };
  fs.writeFileSync(
    path.join(REPORT_DIR, 'stage-results.json'),
    JSON.stringify(summary, null, 2),
    'utf-8'
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const totalStart = Date.now();
  ensureDir(REPORT_DIR);
  ensureDir(DOCS_REPORT_DIR);
  ensureDir(path.join(REPORT_DIR, 'artifacts'));

  log(`\nLIA Unified Diagnostic Battery`);
  log(`Run ID   : ${TIMESTAMP}`);
  log(`Stage    : ${STAGE} → [${ACTIVE_STAGES.join(' → ')}]`);
  log(`Grep     : ${GREP || '(all)'}`);
  log(`Pass^k   : ${PASS_K}`);
  log(`Bail     : ${BAIL}`);
  log(`Base URL : ${process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000'}`);
  log(`Backend  : ${process.env.LIA_BACKEND_URL || 'http://localhost:8001'}`);
  log(`\n`);

  // Record all stages as pending so the report has full stage list
  for (const s of STAGES_FULL) {
    if (!ACTIVE_STAGES.includes(s)) skipStage(s);
  }

  // PREFLIGHT
  if (ACTIVE_STAGES.includes('preflight')) {
    const ok = runStage('preflight', () =>
      runPlaywright('e2e/tests/preflight/preflight.config.ts')
    );
    if (!ok) {
      log('\n[ABORT] Pre-flight failed — fix the issues above before continuing.\n');
      generateReport();
      process.exit(1);
    }
  }

  // SMOKE
  if (ACTIVE_STAGES.includes('smoke')) {
    const ok = runStage('smoke', () =>
      runPlaywright('e2e/tests/smoke/smoke.config.ts', {
        grep: GREP || '@smoke',
        env: {
          DIAGNOSTIC_RUN_ID: TIMESTAMP,
          REQUIRE_ALL_ROLES: REQUIRE_ALL_ROLES ? '1' : '',
        },
      })
    );
    if (!ok && BAIL) { log('\n[BAIL] Stopping.\n'); generateReport(); process.exit(1); }
  }

  // CRITICAL (agentic, pass^k=1 so it's fast)
  if (ACTIVE_STAGES.includes('critical')) {
    const ok = runStage('critical', () =>
      runPlaywright('e2e/tests/agentic-eval/agentic.config.ts', {
        grep: GREP || '@critical',
        env: { AGENTIC_PASS_K: '1' },
        timeoutMs: 900_000,
      })
    );
    if (!ok && BAIL) { log('\n[BAIL] Stopping.\n'); generateReport(); process.exit(1); }
  }

  // FULL AGENTIC D1–D10 (pass^k=1, all scenarios)
  if (ACTIVE_STAGES.includes('agentic')) {
    const ok = runStage('agentic', () =>
      runPlaywright('e2e/tests/agentic-eval/agentic.config.ts', {
        grep: GREP || '',
        env: { AGENTIC_PASS_K: '1' },
        timeoutMs: 3_600_000,
      })
    );
    if (!ok && BAIL) { log('\n[BAIL] Stopping.\n'); generateReport(); process.exit(1); }
  }

  // JUDGE — score D1–D10 dimensions via judge_agentic.py (or eval_judge.py fallback)
  if (ACTIVE_STAGES.includes('judge')) {
    if (NO_PYTHON) {
      log('  ⟳ judge skipped (--no-python)');
      stageResults.push({ stage: 'judge', ok: true, skipped: true, durationMs: 0 });
      persistStageResults();
    } else if (!process.env.ANTHROPIC_API_KEY && !process.env.OPENAI_API_KEY) {
      log('  ⚠ judge skipped — no LLM API key available (ANTHROPIC_API_KEY / OPENAI_API_KEY)');
      stageResults.push({ stage: 'judge', ok: true, skipped: true, durationMs: 0 });
      persistStageResults();
    } else {
      const agenticJudge = path.join(REPO_ROOT, 'lia-agent-system', 'eval', 'agentic', 'judge_agentic.py');
      const agenticRunsDir = path.join(REPO_ROOT, 'lia-agent-system', 'eval', 'agentic', 'runs');
      if (fs.existsSync(agenticJudge) && fs.existsSync(agenticRunsDir)) {
        const runs = fs.readdirSync(agenticRunsDir)
          .filter((f) => f.endsWith('.json') && !f.endsWith('_judged.json'))
          .sort().reverse();
        if (runs.length > 0) {
          const latestRun = path.join(agenticRunsDir, runs[0]);
          runStage('judge', () => runPython(agenticJudge, [latestRun]));
        } else {
          log('  ⚠ judge skipped — no agentic run JSON found yet. Run agentic stage first.');
          stageResults.push({ stage: 'judge', ok: true, skipped: true, durationMs: 0 });
          persistStageResults();
        }
      } else {
        log(`  ⚠ judge_agentic.py not found at ${agenticJudge} — skipping`);
        stageResults.push({ stage: 'judge', ok: true, skipped: true, durationMs: 0 });
        persistStageResults();
      }
    }
  }

  // PASS^K — replay @passk subset k times for D9 consistency
  if (ACTIVE_STAGES.includes('passk')) {
    const ok = runStage('passk', () =>
      runPlaywright('e2e/tests/agentic-eval/agentic.config.ts', {
        grep: GREP || '@passk',
        env: {
          AGENTIC_PASS_K: PASS_K,
          AGENTIC_RUN_ID: `${TIMESTAMP}-passk`,
        },
        timeoutMs: 3_600_000,
      })
    );
    if (!ok && BAIL) { log('\n[BAIL] Stopping.\n'); generateReport(); process.exit(1); }
    // Run judge on the passk results as well
    if (!NO_PYTHON && (process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY)) {
      const agenticJudge = path.join(REPO_ROOT, 'lia-agent-system', 'eval', 'agentic', 'judge_agentic.py');
      const agenticRunsDir = path.join(REPO_ROOT, 'lia-agent-system', 'eval', 'agentic', 'runs');
      if (fs.existsSync(agenticJudge) && fs.existsSync(agenticRunsDir)) {
        const passKRuns = fs.readdirSync(agenticRunsDir)
          .filter((f) => f.includes('passk') && f.endsWith('.json') && !f.endsWith('_judged.json'))
          .sort().reverse();
        if (passKRuns.length > 0) {
          log('  Running judge on pass^k runs…');
          runPython(agenticJudge, [path.join(agenticRunsDir, passKRuns[0])]);
        }
      }
    }
  }

  // PERSONA DIAGNOSTIC
  if (ACTIVE_STAGES.includes('persona')) {
    if (NO_PYTHON) {
      log('  ⟳ persona skipped (--no-python)');
      stageResults.push({ stage: 'persona', ok: true, skipped: true, durationMs: 0 });
      persistStageResults();
    } else {
      const ok = runStage('persona', () =>
        runPlaywright('e2e/tests/persona-diagnostic/diagnostic.config.ts', {
          grep: GREP || '',
          timeoutMs: 1_200_000,
        })
      );
      if (!ok && BAIL) { log('\n[BAIL] Stopping.\n'); generateReport(); process.exit(1); }
    }
  }

  // GOLDEN (Python)
  if (ACTIVE_STAGES.includes('golden')) {
    if (NO_PYTHON) {
      log('  ⟳ golden skipped (--no-python)');
      stageResults.push({ stage: 'golden', ok: true, skipped: true, durationMs: 0 });
      persistStageResults();
    } else {
      const goldenScript = path.join(REPO_ROOT, 'lia-agent-system', 'tests', 'golden_dataset.py');
      if (fs.existsSync(goldenScript)) {
        runStage('golden', () => runPython(goldenScript));
      } else {
        log(`  ⚠ golden_dataset.py not found at ${goldenScript} — skipping`);
        stageResults.push({ stage: 'golden', ok: true, skipped: true, durationMs: 0 });
        persistStageResults();
      }
    }
  }

  generateReport();

  const totalMs = Date.now() - totalStart;
  const anyFailed = stageResults.some((s) => !s.ok && !s.skipped);
  log(`\n${'='.repeat(60)}`);
  log(`DIAGNOSTIC BATTERY COMPLETE — ${(totalMs / 60000).toFixed(1)} min`);
  log(`${'='.repeat(60)}`);
  for (const s of stageResults) {
    const icon = s.skipped ? '⟳' : (s.ok ? '✓' : '✗');
    log(`  ${icon} ${s.stage.padEnd(12)} ${s.skipped ? '(skipped)' : (s.durationMs / 1000).toFixed(1) + 's'}`);
  }
  log('');
  log(`Report: ${REPORT_DIR}/index.html`);
  log(`Markdown: ${DOCS_REPORT_DIR}/diagnostic-${TIMESTAMP}.md`);
  log('');
  if (anyFailed) {
    log('RESULT: FAIL — one or more stages failed. See report for details.');
    process.exit(1);
  } else {
    log('RESULT: PASS — all active stages completed successfully.');
    process.exit(0);
  }
}

function generateReport() {
  const reportScript = path.join(__dirname, 'build-diagnostic-report.js');
  if (!fs.existsSync(reportScript)) return;
  try {
    log('\nGenerating consolidated report…');
    execSync(`node ${reportScript} ${TIMESTAMP}`, {
      cwd: PLATAFORMA,
      env: process.env,
      stdio: 'inherit',
      timeout: 60_000,
    });
  } catch (err) {
    log(`  ⚠ Report generation error: ${err.message}`);
  }
}

main();
