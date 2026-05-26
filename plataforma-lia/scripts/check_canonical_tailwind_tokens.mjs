#!/usr/bin/env node
/**
 * check_canonical_tailwind_tokens.mjs
 *
 * Detecta uso de tokens Tailwind LEGADOS em arquivos .ts/.tsx do frontend.
 * Tokens legados foram aliasados em tailwind.config.ts em 2026-05-25 como fix
 * temporário (canonical-fix no produtor). Código NOVO não deve usá-los.
 *
 * Usage:
 *   node scripts/check_canonical_tailwind_tokens.mjs              # warn-only (exit 0)
 *   node scripts/check_canonical_tailwind_tokens.mjs --blocking   # exit 1 se violations > 0
 *   node scripts/check_canonical_tailwind_tokens.mjs --json       # JSON para CI tooling
 *   node scripts/check_canonical_tailwind_tokens.mjs --max-violations=50 --blocking
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, extname, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const ROOT = join(__dirname, '..');

// Tokens legados: padrão (word boundary no início, não seguido de '-') + token name
// Cada entrada: { pattern, name, canonical, fix }
const LEGACY_TOKENS = [
  {
    // Matches: bg-lia-surface, text-lia-surface, border-lia-surface
    // Does NOT match: lia-surface-something (inexistente, mas defensive)
    pattern: /\blia-surface\b/g,
    name: 'lia-surface',
    canonical: 'lia-bg-elevated (modal/card) ou lia-bg-primary (página)',
    fix: 'bg-lia-bg-elevated | text-lia-bg-elevated | border-lia-bg-elevated',
  },
  {
    // Matches: border-lia-border, bg-lia-border
    // Does NOT match: lia-border-subtle, lia-border-default, lia-border-focus (tokens canônicos)
    pattern: /\blia-border(?![-\w])/g,
    name: 'lia-border',
    canonical: 'lia-border-default (prominent) ou lia-border-subtle (light)',
    fix: 'border-lia-border-default | border-lia-border-subtle | divide-lia-border-default',
  },
  {
    // Matches: text-lia-primary, bg-lia-primary, ring-lia-primary
    // Does NOT match: lia-primary-something (inexistente)
    pattern: /\blia-primary(?![-\w])/g,
    name: 'lia-primary',
    canonical: 'wedo-cyan (sinal IA, cyan #60BED1) ou lia-text-primary (texto)',
    fix: 'text-wedo-cyan | bg-wedo-cyan | border-wedo-cyan | text-lia-text-primary',
  },
  {
    // Matches: bg-lia-muted, text-lia-muted, hover:bg-lia-muted
    // Does NOT match: lia-muted-something (inexistente)
    pattern: /\blia-muted(?![-\w])/g,
    name: 'lia-muted',
    canonical: 'lia-bg-tertiary (hover bg) ou lia-interactive-hover',
    fix: 'bg-lia-bg-tertiary | hover:bg-lia-bg-tertiary | bg-lia-interactive-hover',
  },
];

// Diretórios/arquivos a ignorar
const EXCLUDE_DIRS = new Set(['node_modules', '.next', 'dist', '__tests__', '.impeccable', '.git']);
// O produtor (tailwind.config.ts) define os aliases — não é violation
const EXCLUDE_FILES = new Set(['tailwind.config.ts', 'tailwind.config.js', 'check_canonical_tailwind_tokens.mjs', 'design-tokens.ts']);

function* walkFiles(dir) {
  let entries;
  try { entries = readdirSync(dir); } catch { return; }
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    let stat;
    try { stat = statSync(full); } catch { continue; }
    if (stat.isDirectory()) {
      yield* walkFiles(full);
    } else if (['.ts', '.tsx'].includes(extname(entry)) && !EXCLUDE_FILES.has(entry)) {
      yield full;
    }
  }
}

const args = process.argv.slice(2);
const blocking = args.includes('--blocking');
const jsonOutput = args.includes('--json');
const maxViolationsArg = args.find(a => a.startsWith('--max-violations='));
const maxViolations = maxViolationsArg ? parseInt(maxViolationsArg.split('=')[1], 10) : 0;

const srcDir = join(ROOT, 'src');
const violations = [];

for (const file of walkFiles(srcDir)) {
  let content;
  try { content = readFileSync(file, 'utf8'); } catch { continue; }
  const lines = content.split('\n');

  for (const token of LEGACY_TOKENS) {
    lines.forEach((line, idx) => {
      // Reset lastIndex para cada linha (flag 'g' mantém estado)
      token.pattern.lastIndex = 0;
      let match;
      while ((match = token.pattern.exec(line)) !== null) {
        violations.push({
          file: relative(ROOT, file),
          line: idx + 1,
          col: match.index + 1,
          token: token.name,
          canonical: token.canonical,
          fix: token.fix,
          context: line.trim().slice(0, 120),
        });
      }
    });
  }
}

if (jsonOutput) {
  process.stdout.write(JSON.stringify({ total: violations.length, violations }, null, 2) + '\n');
} else {
  const RESET = '\x1b[0m';
  const YELLOW = '\x1b[33m';
  const RED = '\x1b[31m';
  const GREEN = '\x1b[32m';
  const DIM = '\x1b[2m';

  if (violations.length === 0) {
    console.log(`${GREEN}✓${RESET} check_canonical_tailwind_tokens: 0 violations`);
  } else {
    const icon = blocking ? `${RED}✗${RESET}` : `${YELLOW}⚠${RESET}`;
    console.log(`\n${icon} check_canonical_tailwind_tokens: ${violations.length} violation(s) — tokens legados herdados\n`);

    // Agrupar por arquivo
    const byFile = {};
    for (const v of violations) {
      if (!byFile[v.file]) byFile[v.file] = [];
      byFile[v.file].push(v);
    }

    for (const [file, vs] of Object.entries(byFile)) {
      console.log(`  ${YELLOW}${file}${RESET} (${vs.length})`);
      for (const v of vs) {
        console.log(`    ${DIM}[${v.line}:${v.col}]${RESET} ${RED}${v.token}${RESET}`);
        console.log(`      ${DIM}Canonical:${RESET} ${v.canonical}`);
        console.log(`      ${DIM}Fix:${RESET} ${v.fix}`);
        if (v.context) console.log(`      ${DIM}→ ${v.context}${RESET}`);
      }
      console.log('');
    }

    console.log(`  ${DIM}Total: ${violations.length} violation(s)${RESET}`);
    console.log(`  ${DIM}Esses tokens são LEGACY — aliases temporários em tailwind.config.ts (2026-05-25).${RESET}`);
    console.log(`  ${DIM}NÃO use em código novo. Migre progressivamente para os tokens canônicos.${RESET}`);
  }
}

const shouldFail = blocking && violations.length > maxViolations;
process.exit(shouldFail ? 1 : 0);
