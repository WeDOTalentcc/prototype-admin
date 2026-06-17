#!/usr/bin/env node
/**
 * Consolidated diagnostic report builder.
 *
 * Reads outputs from all stages and produces:
 *   1. HTML report  → playwright-report/diagnostic/index.html
 *   2. Markdown     → docs/eval/reports/diagnostic-{timestamp}.md
 *   3. Tasks JSON   → playwright-report/diagnostic/proposed-tasks.json
 *      (one entry per critical/high scored finding, deduped by SHA1 hash)
 *   4. Task Markdown files → docs/eval/tasks/proposed/{hash}.md
 *      (one file per proposed task, YAML frontmatter, git-trackable)
 *
 * Scoring:
 *   - Reads `<run>_judged.json` if available; falls back to raw run JSON.
 *   - Scenarios with judgment.score >=2 = PASS
 *   - Scenarios without a judgment object = UNSCORED (shown as -1/unknown)
 *   - Pass^k (D9): per-scenario min score across all k runs; D9 dim score
 *     is the minimum per-scenario pass^k score (strictest-run rule)
 *   - Persona findings: ingested from playwright-report/diagnostic/persona-results.json
 *
 * Usage:
 *   node scripts/build-diagnostic-report.js [TIMESTAMP]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const TIMESTAMP = process.argv[2] || new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const REPO_ROOT = path.resolve(__dirname, '../..');
const PLATAFORMA = path.resolve(__dirname, '..');
const REPORT_DIR = path.join(PLATAFORMA, 'playwright-report', 'diagnostic');
const AGENTIC_DIR = path.join(REPO_ROOT, 'lia-agent-system', 'eval', 'agentic');
const RUNS_DIR = path.join(AGENTIC_DIR, 'runs');
const DOCS_REPORT_DIR = path.join(REPO_ROOT, 'docs', 'eval', 'reports');
const TASKS_DIR = path.join(REPO_ROOT, 'docs', 'eval', 'tasks', 'proposed');

// ── Helpers ───────────────────────────────────────────────────────────────────

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function findHash(scenarioId, symptom) {
  return crypto.createHash('sha1').update(`${scenarioId}|${symptom}`).digest('hex').slice(0, 12);
}

function readJson(p) {
  try {
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf-8'));
  } catch { return null; }
}

function severityOrder(s) {
  const m = { critical: 0, high: 1, medium: 2, low: 3 };
  return m[s] !== undefined ? m[s] : 9;
}

/**
 * Extract the numeric score for a result. Returns -1 if unscored (no judgment).
 * -1 means the judge has not run yet — not a pass, not a fail.
 */
function getScore(r) {
  if (r.judgment && typeof r.judgment.score === 'number') return r.judgment.score;
  if (r.errored) return 0;
  return -1;
}

// ── Load agentic results ──────────────────────────────────────────────────────

/**
 * Load agentic results bound to the current TIMESTAMP (run ID).
 * Prefers `agentic-${TIMESTAMP}_judged.json`, falls back to
 * `agentic-${TIMESTAMP}.json`, then the newest file globally.
 */
function loadAgenticResults() {
  if (!fs.existsSync(RUNS_DIR)) return [];

  // Try current-run-specific files first (most reliable)
  const candidates = [
    path.join(RUNS_DIR, `agentic-${TIMESTAMP}_judged.json`),
    path.join(RUNS_DIR, `agentic-${TIMESTAMP}.json`),
  ];
  for (const c of candidates) {
    const run = readJson(c);
    if (run && (run.results || []).length > 0) {
      console.log(`  Using agentic results: ${path.basename(c)}`);
      return run.results;
    }
  }

  // Fallback: newest file (for re-runs of report only, not mid-battery)
  const files = fs.readdirSync(RUNS_DIR).sort().reverse();
  const judgedFallback = files.find((f) => f.endsWith('_judged.json') && !f.includes('passk'));
  if (judgedFallback) {
    console.log(`  Using agentic results (fallback): ${judgedFallback}`);
    const run = readJson(path.join(RUNS_DIR, judgedFallback));
    if (run) return run.results || [];
  }
  const rawFallback = files.find((f) => f.endsWith('.json') && !f.endsWith('_judged.json') && !f.includes('passk'));
  if (rawFallback) {
    console.log(`  Using agentic results (raw fallback): ${rawFallback}`);
    const run = readJson(path.join(RUNS_DIR, rawFallback));
    if (run) return run.results || [];
  }
  return [];
}

/**
 * Load pass^k results bound to TIMESTAMP.
 */
function loadPassKResults() {
  if (!fs.existsSync(RUNS_DIR)) return [];

  const passkTs = `${TIMESTAMP}-passk`;
  const candidates = [
    path.join(RUNS_DIR, `agentic-${passkTs}_judged.json`),
    path.join(RUNS_DIR, `agentic-${passkTs}.json`),
  ];
  for (const c of candidates) {
    const run = readJson(c);
    if (run && (run.results || []).length > 0) {
      console.log(`  Using pass^k results: ${path.basename(c)}`);
      return run.results;
    }
  }

  // Fallback: newest passk file
  const files = fs.readdirSync(RUNS_DIR).sort().reverse();
  const judgedFallback = files.find((f) => f.includes('passk') && f.endsWith('_judged.json'));
  if (judgedFallback) {
    const run = readJson(path.join(RUNS_DIR, judgedFallback));
    if (run) return run.results || [];
  }
  const rawFallback = files.find((f) => f.includes('passk') && f.endsWith('.json') && !f.endsWith('_judged.json'));
  if (rawFallback) {
    const run = readJson(path.join(RUNS_DIR, rawFallback));
    if (run) return run.results || [];
  }
  return [];
}

function loadStageResults() {
  const data = readJson(path.join(REPORT_DIR, 'stage-results.json'));
  if (!data) return [];
  return data.stages || [];
}

function loadPlaywrightJson(file) {
  return readJson(path.join(REPORT_DIR, file));
}

// ── Dimension scores ──────────────────────────────────────────────────────────

const DIM_LABELS = {
  d1: 'D1 Memory', d2: 'D2 Self-knowledge', d3: 'D3 Grounding',
  d4: 'D4 Multi-step planning', d5: 'D5 Clarification', d6: 'D6 Tool robustness',
  d7: 'D7 Sensitive data', d8: 'D8 Refusal & scope',
  d9: 'D9 Consistency (pass^k)', d10: 'D10 Proactive assistance',
};

/**
 * Compute D9 pass^k per-scenario (τ-bench rule).
 *
 * For each unique scenario_id in passk results:
 *   - Collect scores across all k runs
 *   - Per-scenario pass^k score = min score across k runs
 *     (rubric: 3=all runs 3, 2=all >=2, 1=any 1, 0=any 0)
 * D9 dimension score = minimum per-scenario pass^k score (strictest-run semantics).
 */
function computePassKScore(passKResults) {
  if (!passKResults.length) return { dimScore: -1, passRate: undefined, scenarioPassed: 0, scenarioTotal: 0 };

  const byScenario = {};
  for (const r of passKResults) {
    const sid = r.scenario_id;
    if (!byScenario[sid]) byScenario[sid] = [];
    byScenario[sid].push(getScore(r));
  }

  // Per-scenario min score across all k runs (τ-bench rule)
  const perScenarioMin = Object.values(byScenario).map((scores) =>
    scores.reduce((min, s) => (s < min ? s : min), 3)
  );

  const unscored = perScenarioMin.some((s) => s < 0);
  if (unscored) return { dimScore: -1, passRate: undefined, scenarioPassed: 0, scenarioTotal: perScenarioMin.length };

  const dimScore = perScenarioMin.reduce((min, s) => (s < min ? s : min), 3);
  const scenarioPassed = perScenarioMin.filter((s) => s >= 2).length;
  const scenarioTotal = perScenarioMin.length;
  const passRate = Math.round((scenarioPassed / scenarioTotal) * 100);
  return { dimScore, passRate, scenarioPassed, scenarioTotal };
}

function computeDimensionScores(results, passKResults) {
  const { dimScore: passKDimScore, passRate: passKPassRate, scenarioPassed, scenarioTotal } = computePassKScore(passKResults);

  return Object.keys(DIM_LABELS).map((dim) => {
    if (dim === 'd9') {
      return {
        dim,
        label: DIM_LABELS[dim],
        total: scenarioTotal,        // per-scenario count (not run count)
        passed: scenarioPassed,      // scenarios where all k runs passed
        score: passKDimScore,
        passK: passKPassRate,
      };
    }

    const dimResults = results.filter((r) => (r.tags || []).includes(dim));
    const total = dimResults.length;
    if (total === 0) return { dim, label: DIM_LABELS[dim], total: 0, passed: 0, score: -1, passK: undefined };

    const scored = dimResults.filter((r) => getScore(r) >= 0);
    const passed = scored.filter((r) => getScore(r) >= 2).length;
    const scoreAvg = scored.length > 0
      ? scored.reduce((sum, r) => sum + getScore(r), 0) / scored.length
      : -1;

    return {
      dim,
      label: DIM_LABELS[dim],
      total,
      passed,
      score: scored.length > 0 ? Math.round(scoreAvg * 10) / 10 : -1,
      passK: undefined,
      unscoredCount: total - scored.length,
    };
  });
}

// ── Extract findings ──────────────────────────────────────────────────────────

function getLatestRunFile() {
  if (!fs.existsSync(RUNS_DIR)) return '';
  return fs.readdirSync(RUNS_DIR).sort().reverse()[0] || '';
}

function extractAgenticFindings(results) {
  const findings = [];
  const latestRunFile = getLatestRunFile();

  for (const r of results) {
    const score = getScore(r);
    if (score < 0) continue; // unscored — skip until judge runs
    if (score >= 2) continue;
    const sev = r.severity || 'medium';
    if (sev !== 'critical' && sev !== 'high') continue;

    const dim = (r.tags || []).find((t) => /^d\d+$/.test(t)) || 'unknown';
    const symptom = (r.judgment && r.judgment.anti_pattern_detected) || (r.errored ? 'error' : `score=${score}`);
    const h = findHash(r.scenario_id, symptom);

    // Evidence: trace file if exists, otherwise run JSON
    const traceGlob = path.join(REPORT_DIR, 'trace', `*${r.scenario_id}*.zip`);
    const traceExists = fs.existsSync(path.join(REPORT_DIR, 'trace'));
    const evidence = traceExists
      ? `playwright-report/diagnostic/trace/ (trace for ${r.scenario_id})`
      : latestRunFile
        ? `lia-agent-system/eval/agentic/runs/${latestRunFile}`
        : 'playwright-report/diagnostic/artifacts';

    findings.push({
      id: `F-AGENTIC-${h}`,
      scenarioId: r.scenario_id,
      dimension: dim,
      severity: sev,
      title: `[${dim.toUpperCase()}][${sev}] ${r.scenario_id}`,
      description:
        `**Scenario:** ${r.scenario_id}\n` +
        `**Goal:** ${r.goal || ''}\n` +
        `**Score:** ${score}/3\n` +
        `**Symptom:** ${symptom}\n` +
        (r.judgment && r.judgment.reasoning ? `**Reasoning:** ${r.judgment.reasoning}\n` : '') +
        (r.judgment && r.judgment.suggested_fix ? `**Suggested fix:** ${r.judgment.suggested_fix}\n` : ''),
      evidence,
      evidenceType: traceExists ? 'trace' : 'run-json',
      stage: 'agentic',
      hash: h,
    });
  }
  return findings;
}

function extractPlaywrightFindings(jsonFile, stageName) {
  const pw = loadPlaywrightJson(jsonFile);
  if (!pw || !pw.suites) return [];
  const findings = [];

  function walkSuites(suites) {
    for (const suite of (suites || [])) {
      for (const spec of (suite.specs || [])) {
        if (spec.ok) continue;
        const h = findHash(spec.title, stageName);
        // Evidence: screenshot/trace from attachments
        const attachments = spec.tests
          ? spec.tests.flatMap((t) => t.results || []).flatMap((r) => r.attachments || [])
          : [];
        const screenshot = attachments.find((a) => a.contentType && a.contentType.startsWith('image/'));
        const trace = attachments.find((a) => a.name === 'trace');
        const evidence = trace
          ? `playwright-report/diagnostic/trace/ (${stageName})`
          : screenshot
            ? screenshot.path || 'playwright-report/diagnostic/artifacts'
            : `playwright-report/diagnostic/${jsonFile}`;

        findings.push({
          id: `F-${stageName.toUpperCase()}-${h}`,
          scenarioId: spec.title,
          dimension: stageName,
          severity: 'critical',
          title: `[${stageName.toUpperCase()}][critical] ${spec.title}`,
          description: `**Stage:** ${stageName}\n**Test:** ${spec.title}\n**Result:** failed`,
          evidence,
          evidenceType: trace ? 'trace' : screenshot ? 'screenshot' : 'json',
          stage: stageName,
          hash: h,
        });
      }
      if (suite.suites) walkSuites(suite.suites);
    }
  }

  walkSuites(pw.suites);
  return findings;
}

function extractFindings(agenticResults, smokeJson, personaJson) {
  const seen = new Set();
  const findings = [];

  function add(f) {
    if (seen.has(f.hash)) return;
    seen.add(f.hash);
    findings.push(f);
  }

  for (const f of extractAgenticFindings(agenticResults)) add(f);
  for (const f of extractPlaywrightFindings('smoke-results.json', 'smoke')) add(f);
  if (personaJson) {
    for (const f of extractPlaywrightFindings('persona-results.json', 'persona')) add(f);
  }

  findings.sort((a, b) =>
    severityOrder(a.severity) - severityOrder(b.severity) ||
    a.dimension.localeCompare(b.dimension)
  );
  return findings;
}

// ── PROPOSED tasks as individual markdown files ───────────────────────────────

function writeTaskMarkdownFiles(findings) {
  if (!fs.existsSync(TASKS_DIR)) fs.mkdirSync(TASKS_DIR, { recursive: true });

  const tasks = findings.filter((f) => f.severity === 'critical' || f.severity === 'high');
  let created = 0;

  for (const f of tasks) {
    const mdPath = path.join(TASKS_DIR, `${f.hash}.md`);
    if (fs.existsSync(mdPath)) continue; // deduped — already tracked

    const md = [
      `---`,
      `id: ${f.id}`,
      `hash: ${f.hash}`,
      `status: PROPOSED`,
      `severity: ${f.severity}`,
      `dimension: ${f.dimension}`,
      `scenario_id: ${f.scenarioId}`,
      `stage: ${f.stage}`,
      `diagnostic_run: ${TIMESTAMP}`,
      `---`,
      ``,
      `# ${f.title}`,
      ``,
      f.description,
      ``,
      `## Evidence`,
      ``,
      `\`${f.evidence}\` (${f.evidenceType || 'artifact'})`,
      ``,
      `## Acceptance Criteria`,
      ``,
      `- [ ] Root cause identified and documented`,
      `- [ ] Fix applied and verified in agentic eval (score >= 2 for scenario \`${f.scenarioId}\`)`,
      `- [ ] No regression in adjacent dimensions`,
      ``,
    ].join('\n');

    fs.writeFileSync(mdPath, md, 'utf-8');
    created++;
  }

  return { total: tasks.length, created, updated: tasks.length - created };
}

// ── HTML report ───────────────────────────────────────────────────────────────

function buildHtml(dimScores, findings, stageRows, runDate) {
  const scored = dimScores.filter((d) => d.score >= 0);
  const passing = scored.filter((d) => d.score >= 2).length;
  const criticalFindings = findings.filter((f) => f.severity === 'critical').length;
  const anyUnscored = dimScores.some((d) => d.score < 0 && d.total > 0);

  const decisionColor = criticalFindings > 0 ? '#e74c3c'
    : anyUnscored ? '#7a82a0'
    : passing < scored.length ? '#e67e22' : '#2ecc71';
  const decisionText = criticalFindings > 0 ? '🚫 BLOCK — critical failures'
    : anyUnscored ? '⏳ PENDING JUDGE — run npm run diagnostic (judge stage) for full D1–D10'
    : passing < scored.length ? '⚠ SHIP WITH NOTE'
    : '✅ SHIP';

  const dimRowsHtml = dimScores.map((d) => {
    const color = d.score < 0 ? '#7a82a0' : d.score < 2 ? '#e74c3c' : d.score < 2.5 ? '#e67e22' : '#2ecc71';
    const scoreStr = d.score < 0
      ? (d.total > 0 ? '<span title="Run judge stage (auto-invoked with ANTHROPIC_API_KEY set)">⏳ unscored</span>' : '—')
      : d.score.toFixed(1);
    const passStr = d.total > 0 ? `${d.passed}/${d.total}` : '—';
    const passKStr = d.passK !== undefined ? `${d.passK}%` : '—';
    const unscoredNote = d.unscoredCount > 0 ? ` <small style="color:#7a82a0">(${d.unscoredCount} unscored)</small>` : '';
    return `<tr>
      <td><b>${esc(d.dim.toUpperCase())}</b></td>
      <td>${esc(d.label)}${unscoredNote}</td>
      <td style="color:${color};font-weight:700">${scoreStr}${d.score >= 0 ? '/3' : ''}</td>
      <td>${passStr}</td>
      <td>${passKStr}</td>
    </tr>`;
  }).join('');

  const findingRowsHtml = findings.map((f) => {
    const sevColor = f.severity === 'critical' ? '#e74c3c' : f.severity === 'high' ? '#e67e22' : '#3498db';
    const evIcon = f.evidenceType === 'trace' ? '🎯' : f.evidenceType === 'screenshot' ? '📷' : '📄';

    // Compute clickable href relative to playwright-report/diagnostic/index.html
    let evHref = '';
    if (f.evidenceType === 'trace') {
      evHref = './trace/';
    } else if (f.evidenceType === 'screenshot' && f.evidence.includes('/')) {
      // evidence is an absolute path from Playwright attachments
      evHref = './artifacts/';
    } else if (f.evidence.startsWith('lia-agent-system/')) {
      // relative from workspace root; from report dir go 3 levels up
      evHref = `../../../${f.evidence}`;
    } else if (f.evidence.startsWith('playwright-report/diagnostic/')) {
      evHref = `./${f.evidence.replace('playwright-report/diagnostic/', '')}`;
    } else if (f.evidence.startsWith('docs/')) {
      evHref = `../../../${f.evidence}`;
    } else {
      evHref = f.evidence;
    }

    const evLabel = f.evidence.split('/').pop() || f.evidence;
    return `<tr>
      <td><span style="background:${sevColor};color:#fff;padding:2px 7px;border-radius:4px;font-size:11px">${esc(f.severity)}</span></td>
      <td><code>${esc(f.dimension.toUpperCase())}</code></td>
      <td><small>${esc(f.scenarioId)}</small></td>
      <td>${esc(f.title.replace(/^\[.*?\]\s*/, ''))}</td>
      <td>${evIcon} <a href="${esc(evHref)}" style="color:#7a8cc4;text-decoration:none;font-size:11px" title="${esc(f.evidence)}">${esc(evLabel)}</a></td>
    </tr>`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LIA Diagnostic Report — ${esc(TIMESTAMP)}</title>
<style>
:root{--bg:#0f1117;--bg2:#1a1d26;--bg3:#22263a;--border:#2d3148;--text:#e0e4f0;--muted:#7a82a0}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);padding:28px;font-size:13px}
h1{font-size:22px;font-weight:700;margin-bottom:4px}
h2{font-size:15px;font-weight:600;color:var(--muted);margin:28px 0 12px}
.meta{color:var(--muted);font-size:12px;margin-bottom:20px}
.decision{display:inline-block;padding:10px 24px;border-radius:8px;font-size:16px;font-weight:700;color:#fff;background:${decisionColor};margin-bottom:24px}
table{width:100%;border-collapse:collapse;margin-bottom:20px}
th{background:var(--bg3);padding:8px 10px;text-align:left;font-size:11px;color:var(--muted);text-transform:uppercase;border-bottom:2px solid var(--border)}
td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
tr:hover{background:var(--bg2)}
code{background:var(--bg3);padding:1px 5px;border-radius:3px;font-size:11px}
.note{color:var(--muted);font-size:11px;margin-top:28px;line-height:1.8}
</style>
</head>
<body>
<h1>LIA Unified Diagnostic Report</h1>
<div class="meta">Generated ${esc(runDate)} — Run ID: ${esc(TIMESTAMP)}</div>
<div class="decision">${decisionText}</div>

<h2>Stage Summary</h2>
<table style="max-width:400px">
<thead><tr><th></th><th>Stage</th><th>Duration</th></tr></thead>
<tbody>${stageRows}</tbody>
</table>

<h2>Dimension Scores D1–D10</h2>
<p style="color:var(--muted);font-size:11px;margin-bottom:10px">
  Judge runs automatically when <code>ANTHROPIC_API_KEY</code> is set.
  Rerun with <code>npm run diagnostic -- --stage judge</code> to repopulate scores from existing captures.
</p>
<table>
<thead><tr><th>Dim</th><th>Label</th><th>Score (0–3)</th><th>Pass rate</th><th>pass^k (D9)</th></tr></thead>
<tbody>${dimRowsHtml}</tbody>
</table>

<h2>Findings (critical + high, scored failures only)</h2>
${findings.length === 0
  ? '<p style="color:#2ecc71;padding:12px 0">No critical or high scored failures. 🎉</p>'
  : `<table>
<thead><tr><th>Severity</th><th>Dim</th><th>Scenario</th><th>Title</th><th>Evidence</th></tr></thead>
<tbody>${findingRowsHtml}</tbody>
</table>`}

<p class="note">
  <a href="./trace/" style="color:#7a8cc4">🎯 Traces &amp; screenshots</a> — <code>playwright-report/diagnostic/trace/</code><br>
  <a href="../../../lia-agent-system/eval/agentic/runs/" style="color:#7a8cc4">📊 Agentic run JSONs</a> — <code>lia-agent-system/eval/agentic/runs/</code><br>
  <a href="../../../docs/eval/reports/diagnostic-${esc(TIMESTAMP)}.md" style="color:#7a8cc4">📝 Markdown report</a> — <code>docs/eval/reports/diagnostic-${esc(TIMESTAMP)}.md</code><br>
  <a href="../../../docs/eval/tasks/proposed/" style="color:#7a8cc4">📋 Proposed tasks</a> — <code>docs/eval/tasks/proposed/</code><br>
  <a href="./proposed-tasks.json" style="color:#7a8cc4">📄 Tasks JSON</a> — <code>playwright-report/diagnostic/proposed-tasks.json</code>
</p>
</body>
</html>`;
}

// ── Markdown report ───────────────────────────────────────────────────────────

function buildMarkdown(dimScores, findings, stageData) {
  const runDate = new Date().toISOString().slice(0, 19).replace('T', ' ');
  const lines = [
    `# LIA Diagnostic Report — ${TIMESTAMP}`,
    ``,
    `Generated: ${runDate} UTC`,
    ``,
    `## Stage Results`,
    ``,
  ];
  for (const s of stageData) {
    const icon = s.skipped ? '⟳' : (s.ok ? '✅' : '❌');
    lines.push(`- ${icon} **${s.stage}**${s.skipped ? ' (skipped)' : ''}`);
  }

  lines.push(``, `## Dimension Scores (D1–D10)`, ``);
  lines.push('| Dim | Label | Score | Pass rate | pass^k |');
  lines.push('|-----|-------|-------|-----------|--------|');
  for (const d of dimScores) {
    const scoreStr = d.score < 0 ? '⏳' : d.score.toFixed(1);
    const passStr = d.total > 0 ? `${d.passed}/${d.total}` : '—';
    const passKStr = d.passK !== undefined ? `${d.passK}%` : '—';
    lines.push(`| ${d.dim.toUpperCase()} | ${d.label} | ${scoreStr}${d.score >= 0 ? '/3' : ''} | ${passStr} | ${passKStr} |`);
  }

  lines.push(``, `> ⏳ = unscored — judge runs automatically when ANTHROPIC_API_KEY is set.`, ``);
  lines.push(`## Findings (prioritised: severity × dimension)`, ``);
  if (findings.length === 0) {
    lines.push('_No critical or high scored findings. 🎉_');
  } else {
    for (const f of findings) {
      lines.push(`### ${f.title}`, ``);
      lines.push(`**Severity:** ${f.severity}  **Dimension:** ${f.dimension}  **Scenario:** \`${f.scenarioId}\``, ``);
      lines.push(f.description.replace(/\*\*/g, ''), ``);
      lines.push(`**Evidence:** \`${f.evidence}\` (${f.evidenceType || 'artifact'})`, ``);
      lines.push(`**Proposed task:** \`docs/eval/tasks/proposed/${f.hash}.md\``, ``);
    }
  }
  return lines.join('\n');
}

// ── Proposed tasks JSON ───────────────────────────────────────────────────────

function buildProposedTasksJson(findings) {
  return findings
    .filter((f) => f.severity === 'critical' || f.severity === 'high')
    .map((f) => ({
      id: f.id,
      hash: f.hash,
      title: f.title,
      description: f.description,
      evidence: f.evidence,
      evidence_type: f.evidenceType,
      dimension: f.dimension,
      severity: f.severity,
      scenario_id: f.scenarioId,
      stage: f.stage,
      status: 'PROPOSED',
      diagnostic_run: TIMESTAMP,
      markdown_file: `docs/eval/tasks/proposed/${f.hash}.md`,
    }));
}

// ── Main ─────────────────────────────────────────────────────────────────────

function main() {
  console.log(`\nBuilding diagnostic report for run ${TIMESTAMP}…`);

  if (!fs.existsSync(REPORT_DIR)) fs.mkdirSync(REPORT_DIR, { recursive: true });
  if (!fs.existsSync(DOCS_REPORT_DIR)) fs.mkdirSync(DOCS_REPORT_DIR, { recursive: true });

  const agenticResults = loadAgenticResults();
  const passKResults = loadPassKResults();
  const smokeJson = loadPlaywrightJson('smoke-results.json');
  const personaJson = loadPlaywrightJson('persona-results.json');
  const stageData = loadStageResults();

  const dimScores = computeDimensionScores(agenticResults, passKResults);
  const findings = extractFindings(agenticResults, smokeJson, personaJson);

  // Logging what we found
  const judgedCount = agenticResults.filter((r) => r.judgment).length;
  console.log(`  Agentic results: ${agenticResults.length} (${judgedCount} judged)`);
  console.log(`  Pass^k results:  ${passKResults.length}`);
  console.log(`  Persona tests:   ${personaJson ? (personaJson.stats && personaJson.stats.expected > 0 ? personaJson.stats.expected : '?') + ' loaded' : 'not yet run'}`);
  console.log(`  Smoke tests:     ${smokeJson ? 'loaded' : 'not yet run'}`);
  console.log(`  Findings:        ${findings.length} (${findings.filter((f) => f.severity === 'critical').length} critical, ${findings.filter((f) => f.severity === 'high').length} high)`);

  // Build stage rows for HTML
  const stageRowsHtml = stageData.map((s) => {
    const icon = s.skipped ? '⟳' : (s.ok ? '✓' : '✗');
    const color = s.skipped ? '#7a82a0' : (s.ok ? '#2ecc71' : '#e74c3c');
    const dur = s.skipped ? '(skipped)' : `${(s.durationMs / 1000).toFixed(1)}s`;
    return `<tr><td style="color:${color};font-weight:700;font-size:16px">${icon}</td><td>${esc(s.stage)}</td><td style="color:#7a82a0;font-size:11px">${esc(dur)}</td></tr>`;
  }).join('');

  const runDate = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';

  const html = buildHtml(dimScores, findings, stageRowsHtml, runDate);
  const htmlPath = path.join(REPORT_DIR, 'index.html');
  fs.writeFileSync(htmlPath, html, 'utf-8');
  console.log(`  ✓ HTML report: ${htmlPath}`);

  const md = buildMarkdown(dimScores, findings, stageData);
  const mdPath = path.join(DOCS_REPORT_DIR, `diagnostic-${TIMESTAMP}.md`);
  fs.writeFileSync(mdPath, md, 'utf-8');
  console.log(`  ✓ Markdown:    ${mdPath}`);

  const tasks = buildProposedTasksJson(findings);
  const tasksPath = path.join(REPORT_DIR, 'proposed-tasks.json');
  fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2), 'utf-8');
  console.log(`  ✓ Tasks JSON:  ${tasksPath} (${tasks.length} proposed tasks)`);

  const { total, created, updated } = writeTaskMarkdownFiles(findings);
  console.log(`  ✓ Task files:  docs/eval/tasks/proposed/ (${created} new, ${updated} existing of ${total} total)`);

  console.log('\nReport generation complete.\n');
}

main();
