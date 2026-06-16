#!/usr/bin/env node
/**
 * check_no_hardcoded_hex_in_studio.mjs
 *
 * Detecta classes Tailwind com cor HEX CRUA (ex.: bg-[#60BED1], text-[#6B7280])
 * em src/components/pages-agent-studio/. Cor hex hardcoded NÃO é coberta pelo
 * sensor de tokens legados (check_canonical_tailwind_tokens) nem pelo sensor de
 * cyan — foi exatamente assim que o redesign do funil (be3590200) reintroduziu
 * ~120 cores fora do DS, com look "apagado" + dark mode quebrado.
 *
 * Cada hex deve virar token canônico do DS (ver docs/design-system/00-design-system-v4.md):
 *   bg/text/border-[#hex]  →  bg/text/border-lia-* | wedo-green/orange | status-*
 * Cyan (#60BED1/#EBF8FB) é EXCLUSIVA da LIA quando ELA age — em superfícies do
 * agente do CLIENTE use neutros (lia-text-primary, lia-bg-tertiary, ...).
 *
 * Escape hatch: comente `// DS-EXEMPT: <motivo>` na MESMA linha do hex.
 *
 * Usage:
 *   node scripts/check_no_hardcoded_hex_in_studio.mjs            # warn-only (exit 0)
 *   node scripts/check_no_hardcoded_hex_in_studio.mjs --blocking # exit 1 se > max
 *   node scripts/check_no_hardcoded_hex_in_studio.mjs --max-violations=9 --blocking
 *   node scripts/check_no_hardcoded_hex_in_studio.mjs --json
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const ROOT = join(__dirname, '..');
const TARGET_DIR = join(ROOT, 'src', 'components', 'pages-agent-studio');

const EXCLUDE_DIRS = new Set(['__tests__', '__snapshots__', 'node_modules']);
// Classe utilitária Tailwind com cor hex crua. Captura prefixo + hex (+ opacidade).
const HEX_CLASS = /\b(?:bg|text|border|ring|divide|from|to|via|fill|stroke|shadow|outline|decoration)-\[#[0-9A-Fa-f]{3,8}\](?:\/[0-9]+)?/g;

const args = process.argv.slice(2);
const blocking = args.includes('--blocking');
const asJson = args.includes('--json');
const maxArg = args.find(a => a.startsWith('--max-violations='));
const maxViolations = maxArg ? parseInt(maxArg.split('=')[1], 10) : 0;

function* walk(dir) {
  let entries;
  try { entries = readdirSync(dir); } catch { return; }
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) { yield* walk(full); continue; }
    if (!entry.endsWith('.tsx') && !entry.endsWith('.ts')) continue;
    if (entry.endsWith('.test.tsx') || entry.endsWith('.test.ts') || entry.endsWith('.stories.tsx')) continue;
    yield full;
  }
}

const violations = [];
for (const file of walk(TARGET_DIR)) {
  const lines = readFileSync(file, 'utf-8').split('\n');
  lines.forEach((line, i) => {
    if (line.includes('DS-EXEMPT')) return;
    const matches = line.match(HEX_CLASS);
    if (matches) {
      for (const m of matches) {
        violations.push({ file: relative(ROOT, file), line: i + 1, klass: m });
      }
    }
  });
}

if (asJson) {
  console.log(JSON.stringify({ total: violations.length, violations }, null, 2));
} else if (violations.length === 0) {
  console.log('\x1b[32m✓\x1b[0m check_no_hardcoded_hex_in_studio: 0 violations');
} else {
  console.log(`\x1b[33m⚠\x1b[0m check_no_hardcoded_hex_in_studio: ${violations.length} hex cru em pages-agent-studio/`);
  for (const v of violations) {
    console.log(`  [${v.file}:${v.line}] ${v.klass}`);
  }
  console.log('\n→ Fix: troque a cor hex por token canônico do DS (00-design-system-v4.md).');
  console.log('  Cinzas: lia-text-{primary,secondary,tertiary} / lia-bg-{secondary,tertiary,elevated} / lia-border-{subtle,default,medium}');
  console.log('  Status: wedo-green / wedo-orange / status-error.  Botão primário: lia-btn-primary-{bg,text,hover}.');
  console.log('  Cyan (#60BED1) = LIA exclusiva — em superfície do agente do cliente use neutros.');
  console.log('  Exceção justificada: // DS-EXEMPT: <motivo> na mesma linha.');
}

if (blocking && violations.length > maxViolations) {
  console.error(`\n✖ ${violations.length} violations > max ${maxViolations} (--blocking).`);
  process.exit(1);
}
process.exit(0);
