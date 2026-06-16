#!/usr/bin/env node
/**
 * Sensor canonical: DS tokens declared in DESIGN.md frontmatter must be wired
 * in tailwind.config.ts theme.extend.colors. Detects "dead class" risk before
 * sites use tokens that won't generate CSS.
 *
 * - Reads DESIGN.md frontmatter `colors:` block (YAML-ish).
 * - Reads tailwind.config.ts theme.extend.colors keys.
 * - Reports tokens in DESIGN.md but NOT in tailwind config.
 *
 * Exit 0 in warn-only (default). Exit 1 with --blocking when violations > max.
 *
 * Usage:
 *   node scripts/check_ds_tokens_canonical.mjs                # warn-only
 *   node scripts/check_ds_tokens_canonical.mjs --blocking     # exit 1 if any
 *   node scripts/check_ds_tokens_canonical.mjs --json         # JSON output
 *
 * Baseline: 0 violations (post DS canonical wiring Sprint 2026-05-26).
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(new URL(".", import.meta.url).pathname, "..");
const DESIGN_MD = path.join(ROOT, "DESIGN.md");
const TAILWIND = path.join(ROOT, "tailwind.config.ts");

const argv = process.argv.slice(2);
const blocking = argv.includes("--blocking");
const asJson = argv.includes("--json");

function readDesignTokens() {
  const text = fs.readFileSync(DESIGN_MD, "utf8");
  // Extract `colors:` block — lines starting with two-space indent + key: "#HEX"
  const m = text.match(/^colors:\s*$([\s\S]*?)(?=^\S|\Z)/m);
  if (!m) {
    console.error("ERROR: DESIGN.md missing `colors:` frontmatter block");
    process.exit(2);
  }
  const block = m[1];
  const tokens = new Set();
  for (const line of block.split("\n")) {
    const km = line.match(/^\s+([a-z][a-z0-9-]*)\s*:\s*"#[0-9A-Fa-f]{3,8}"/);
    if (km) tokens.add(km[1]);
  }
  return tokens;
}

function readTailwindColors() {
  const text = fs.readFileSync(TAILWIND, "utf8");
  // Naive: find all 'token-name': '#HEX' or 'token-name': 'var(...)' inside colors: { ... }
  // Capture single-quoted keys in theme.extend.colors block.
  const keys = new Set();
  // Match 'kebab-case-name': value
  const re = /'([a-z][a-z0-9-]*)'\s*:/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    keys.add(m[1]);
  }
  return keys;
}

const designTokens = readDesignTokens();
const tailwindKeys = readTailwindColors();

const missing = [];
for (const tok of designTokens) {
  if (!tailwindKeys.has(tok)) missing.push(tok);
}

if (asJson) {
  console.log(JSON.stringify({
    design_tokens: [...designTokens].sort(),
    tailwind_keys_count: tailwindKeys.size,
    missing,
  }, null, 2));
} else {
  console.log(`[ds-tokens] DESIGN.md declara ${designTokens.size} tokens canonical`);
  console.log(`[ds-tokens] tailwind.config.ts tem ${tailwindKeys.size} chaves de cor (inclui aliases lia-*)`);
  if (missing.length === 0) {
    console.log("[ds-tokens] OK: todos os tokens DESIGN.md estao wired no Tailwind ✓");
  } else {
    console.log(`[ds-tokens] WARN: ${missing.length} token(s) declarado(s) em DESIGN.md mas NAO wired em tailwind.config.ts:`);
    for (const t of missing) {
      console.log(`  - ${t}`);
      console.log(`    → Fix: adicionar '${t}': '#HEX' em theme.extend.colors no tailwind.config.ts`);
    }
  }
}

if (blocking && missing.length > 0) {
  process.exit(1);
}
