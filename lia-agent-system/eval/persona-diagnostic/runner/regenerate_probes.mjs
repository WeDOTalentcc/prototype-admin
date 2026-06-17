#!/usr/bin/env node
/**
 * Regenerate ../probes.yaml from the canonical TypeScript list used by the
 * Playwright capture (plataforma-lia/e2e/tests/persona-diagnostic/probes.ts).
 *
 * Run from repo root:
 *   node lia-agent-system/eval/persona-diagnostic/runner/regenerate_probes.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, '../../../../');
const SRC = path.join(REPO, 'plataforma-lia/e2e/tests/persona-diagnostic/probes.ts');
const OUT = path.resolve(__dirname, '../probes.yaml');

const AGENT_CONTEXT = {
  LIA: { scope: 'global',   page: 'home' },
  JOB: { scope: 'Vagas',    page: 'gestao-vagas' },
  SRC: { scope: 'Sourcing', page: 'sourcing' },
  CVS: { scope: 'Pipeline', page: 'pipeline' },
  INT: { scope: 'Pipeline', page: 'interview' },
  WSI: { scope: 'Pipeline', page: 'pipeline' },
  ORC: { scope: 'global',   page: 'home' },
};
const CRIT_NUM = { '★': 1, '★★': 2, '★★★': 3 };

const src = fs.readFileSync(SRC, 'utf-8');
const re = /\{\s*id:\s*'([^']+)',\s*category:\s*'([^']+)',\s*agent:\s*'([^']+)',\s*criticality:\s*'([^']+)',\s*prompt:\s*'((?:[^'\\]|\\.)*)',\s*expected:\s*'((?:[^'\\]|\\.)*)'\s*\}/g;

const probes = [];
let m;
while ((m = re.exec(src)) !== null) {
  const [, id, category, agent, criticality, prompt, expected] = m;
  const u = (s) => s.replace(/\\'/g, "'").replace(/\\"/g, '"').replace(/\\\\/g, '\\');
  probes.push({
    id, category, agent, criticality,
    criticality_num: CRIT_NUM[criticality],
    prompt: u(prompt),
    expected: u(expected),
    context: { ...(AGENT_CONTEXT[agent] || { scope: 'global', page: 'home' }) },
  });
}
if (probes.length !== 120) {
  console.error(`Expected 120 probes, parsed ${probes.length}. Aborting.`);
  process.exit(1);
}

const ys = (s) => JSON.stringify(s);
const lines = [];
lines.push('# Persona Diagnostic — Probe Sheet (auto-generated from probes.ts)');
lines.push('# Source of truth: plataforma-lia/e2e/tests/persona-diagnostic/probes.ts');
lines.push('# Regenerate via: node lia-agent-system/eval/persona-diagnostic/runner/regenerate_probes.mjs');
lines.push('');
lines.push('meta:');
lines.push('  version: "1.0.0"');
lines.push(`  total_probes: ${probes.length}`);
lines.push('  rubric: "scoring-rubric.md"');
lines.push('  baseline: "runs/diagnostico-consolidado-2026-04-19.json"');
lines.push('');
lines.push('agents:');
for (const [k, v] of Object.entries(AGENT_CONTEXT)) {
  lines.push(`  ${k}:`);
  lines.push(`    scope: ${ys(v.scope)}`);
  lines.push(`    page: ${ys(v.page)}`);
}
lines.push('');
lines.push('probes:');
for (const p of probes) {
  lines.push(`  - id: ${ys(p.id)}`);
  lines.push(`    category: ${ys(p.category)}`);
  lines.push(`    agent: ${ys(p.agent)}`);
  lines.push(`    criticality: ${ys(p.criticality)}`);
  lines.push(`    criticality_num: ${p.criticality_num}`);
  lines.push(`    prompt: ${ys(p.prompt)}`);
  lines.push(`    expected: ${ys(p.expected)}`);
  lines.push('    context:');
  lines.push(`      scope: ${ys(p.context.scope)}`);
  lines.push(`      page: ${ys(p.context.page)}`);
}
fs.writeFileSync(OUT, lines.join('\n') + '\n', 'utf-8');
console.log(`Wrote ${probes.length} probes to ${path.relative(REPO, OUT)}`);
