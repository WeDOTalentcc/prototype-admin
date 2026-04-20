#!/usr/bin/env node
/**
 * i18n Missing-Key Guardrail
 * ==========================
 *
 * Usage (via pnpm/npm):
 *   pnpm i18n:check          # run the full check
 *   node scripts/i18n-check.js
 *
 * What it checks:
 *   1. Locale parity — keys present in en.json but absent in pt-BR.json (or vice
 *      versa) are reported as ERRORS. Both files must have the same key set.
 *   2. Code ↔ JSON — static `t('key')` / `t('ns.key')` calls in src/**\/*.{ts,tsx}
 *      are resolved against the JSON files.  Any referenced key that does not
 *      exist in BOTH locales is reported as an ERROR.
 *   3. Unused keys — JSON keys never referenced in source code are reported as
 *      WARNINGs (they may be used dynamically and are NOT treated as errors).
 *
 * Flags:
 *   --verbose    Print every individual unused-key and dynamic-call warning.
 *                By default only the counts are shown to keep output readable.
 *
 * Exit codes:
 *   0  — no errors (warnings are fine)
 *   1  — at least one locale-parity or code-reference error was found
 *
 * Limitations (known):
 *   - Dynamic keys like `t(variable)`, `t('a' + b)`, or `t(\`${prefix}.${suffix}\`)`
 *     are skipped with a WARNING so they don't cause false positives.
 *   - When useTranslations() is called without a namespace argument the literal
 *     passed to t() is used as a fully-qualified key (no prefix prepended).
 *   - Namespace inference is file-local: it reads the nearest
 *     useTranslations/getTranslations call above each t() call. Multiple
 *     namespaces in the same file are handled sequentially.
 *   - Only the two supported locales (en, pt-BR) are checked.
 */

'use strict';

const fs   = require('fs');
const path = require('path');

const VERBOSE = process.argv.includes('--verbose');

// ── paths ────────────────────────────────────────────────────────────────────
const ROOT     = path.resolve(__dirname, '..');
const EN_PATH  = path.join(ROOT, 'messages', 'en.json');
const PT_PATH  = path.join(ROOT, 'messages', 'pt-BR.json');
const SRC_DIR  = path.join(ROOT, 'src');

// ── helpers ──────────────────────────────────────────────────────────────────

/** Recursively flatten a nested object into dotted keys. */
function flattenKeys(obj, prefix = '') {
  const keys = new Set();
  for (const [k, v] of Object.entries(obj)) {
    const full = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      for (const sub of flattenKeys(v, full)) keys.add(sub);
    } else {
      keys.add(full);
    }
  }
  return keys;
}

/** Walk a directory recursively, yield every file matching the extension list. */
function* walkFiles(dir, exts) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkFiles(full, exts);
    } else if (exts.some(e => full.endsWith(e))) {
      yield full;
    }
  }
}

// ── load JSONs ────────────────────────────────────────────────────────────────
let enJson, ptJson;
try {
  enJson = JSON.parse(fs.readFileSync(EN_PATH, 'utf8'));
  ptJson = JSON.parse(fs.readFileSync(PT_PATH, 'utf8'));
} catch (err) {
  console.error(`[i18n-check] FATAL: could not load message files — ${err.message}`);
  process.exit(1);
}

const enKeys = flattenKeys(enJson);
const ptKeys = flattenKeys(ptJson);

// ── (1) locale parity ─────────────────────────────────────────────────────────
const onlyInEn = [...enKeys].filter(k => !ptKeys.has(k));
const onlyInPt = [...ptKeys].filter(k => !enKeys.has(k));

// ── (2) code scanning ────────────────────────────────────────────────────────
//
// Strategy: read each .ts/.tsx file, strip comments, then:
//
// 1. Build a variable-to-namespace map from every line like:
//      const t       = useTranslations('ns')
//      const tStatus = useTranslations('ns.sub')
//      const t       = await getTranslations('ns')
//      const t       = useTranslations()          ← no-arg: namespace = '' (fully-qualified)
//    This handles multiple aliased translation hooks per file.
//
// 2. For each known variable, find calls  varName('key') with a literal key,
//    and resolve to  ns + '.' + key  (or just key when ns is '').
//
// 3. Template literals with ${…}, variable references, and string concatenation
//    are skipped as dynamic (warned but not errored).
//
// Known limitation: chained / conditional namespace assignments are not tracked.

/** Strip single-line and multi-line JS comments from source text. */
function stripComments(src) {
  // Replace /* … */ (non-greedy, dotAll)
  src = src.replace(/\/\*[\s\S]*?\*\//g, (m) => ' '.repeat(m.length));
  // Replace // … to end of line (preserve newline)
  src = src.replace(/\/\/[^\n]*/g, (m) => ' '.repeat(m.length));
  return src;
}

// Matches:  const varName = useTranslations('ns')
//           const varName = await getTranslations('ns')
// Captures: varName (group 1), ns (group 2), index stored separately
const VAR_NS_RE = /(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?(?:useTranslations|getTranslations)\s*\(\s*['"]([^'"]+)['"]\s*\)/g;

// Matches:  const varName = useTranslations()   (no-arg → fully-qualified keys)
//           const varName = await getTranslations()
// Captures: varName (group 1)
const VAR_NS_NOARG_RE = /(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?(?:useTranslations|getTranslations)\s*\(\s*\)/g;

// Matches  varOrT('key')  varOrT("key")  with no quotes inside the key
// Built per-variable-name at runtime
const CALL_SINGLE_RE = (varName) =>
  new RegExp(`\\b${varName}\\s*\\(\\s*'([^']+)'\\s*[,)]`, 'g');
const CALL_DOUBLE_RE = (varName) =>
  new RegExp(`\\b${varName}\\s*\\(\\s*"([^"]+)"\\s*[,)]`, 'g');
const CALL_TMPL_RE   = (varName) =>
  new RegExp(`\\b${varName}\\s*\\(\\s*\`([^\`]*)\`\\s*[,)]`, 'g');

// Matches any t(…) call where the argument is NOT a simple string/template literal:
// e.g. t(variable), t(getSomeKey()), etc.
// We detect this by finding varName( followed by something that is not a quote or backtick.
// Note: string is built with concatenation (not template literal) to avoid backtick escaping issues.
const CALL_DYNAMIC_RE = (varName) =>
  new RegExp('\\b' + varName + '\\s*\\(\\s*(?![\'"`])([^)]+)\\)', 'g');

// Also detect concatenation inside quotes:  t('prefix.' + var)  or  t("pre" + x)
const CALL_CONCAT_RE = (varName) =>
  new RegExp(`\\b${varName}\\s*\\(\\s*['"][^'"]*['"]\\s*\\+`, 'g');

const referencedKeys = new Set();   // full dotted keys found in code
const dynamicWarnings = [];          // files with dynamic t() calls

for (const file of walkFiles(SRC_DIR, ['.ts', '.tsx'])) {
  const rawSrc = fs.readFileSync(file, 'utf8');
  const src    = stripComments(rawSrc);
  const rel    = path.relative(ROOT, file);

  // Collect all namespace assignments with position:
  //   { varName, ns, index }
  // null ns = no-arg (fully-qualified)
  const nsAssignments = [];
  let m;

  VAR_NS_RE.lastIndex = 0;
  while ((m = VAR_NS_RE.exec(src)) !== null) {
    nsAssignments.push({ varName: m[1], ns: m[2], index: m.index });
  }

  VAR_NS_NOARG_RE.lastIndex = 0;
  while ((m = VAR_NS_NOARG_RE.exec(src)) !== null) {
    // ns = '' means the key is already fully-qualified
    nsAssignments.push({ varName: m[1], ns: '', index: m.index });
  }

  // For a given varName and call position, find the closest preceding
  // assignment to that variable (position-sensitive, variable-specific).
  const resolveNs = (varName, callIdx) => {
    let best = undefined;
    for (const a of nsAssignments) {
      if (a.varName === varName && a.index <= callIdx) {
        best = a.ns;
      }
    }
    return best; // undefined = no assignment found; '' = no-arg (fully-qualified)
  };

  // Collect all unique variable names that are ever assigned a namespace
  const varNames = [...new Set(nsAssignments.map(a => a.varName))];

  // For each known variable, scan for literal key calls
  for (const varName of varNames) {
    const seenDynamic = new Set();

    // Helper to record a key for a call at position callIdx
    const record = (raw, callIdx) => {
      const ns = resolveNs(varName, callIdx);
      if (ns === undefined) return; // no namespace context
      const fullKey = ns === '' ? raw : `${ns}.${raw}`;
      referencedKeys.add(fullKey);
    };

    // Helper to record a dynamic warning (deduped per file+snippet)
    const warnDynamic = (snippet, callIdx) => {
      const key = `${rel}:${snippet}`;
      if (seenDynamic.has(key)) return;
      const ns = resolveNs(varName, callIdx);
      if (ns === undefined) return;
      seenDynamic.add(key);
      dynamicWarnings.push({ file: rel, call: snippet });
    };

    // Single-quoted keys
    const reS = CALL_SINGLE_RE(varName);
    reS.lastIndex = 0;
    while ((m = reS.exec(src)) !== null) {
      record(m[1], m.index);
    }

    // Double-quoted keys
    const reD = CALL_DOUBLE_RE(varName);
    reD.lastIndex = 0;
    while ((m = reD.exec(src)) !== null) {
      record(m[1], m.index);
    }

    // Template literals
    const reT = CALL_TMPL_RE(varName);
    reT.lastIndex = 0;
    while ((m = reT.exec(src)) !== null) {
      if (m[1].includes('${')) {
        warnDynamic(`\`${m[1]}\``, m.index);
      } else {
        record(m[1], m.index);
      }
    }

    // String concatenation inside quotes: t('prefix.' + var)
    const reConcat = CALL_CONCAT_RE(varName);
    reConcat.lastIndex = 0;
    while ((m = reConcat.exec(src)) !== null) {
      warnDynamic(src.slice(m.index, m.index + Math.min(60, src.length - m.index)).split('\n')[0].trim(), m.index);
    }

    // Fully dynamic (variable/expression) arguments: t(variable), t(getKey())
    // We scan for varName( not followed by a quote/backtick.
    // We must avoid re-flagging what's already handled above.
    const reDyn = CALL_DYNAMIC_RE(varName);
    reDyn.lastIndex = 0;
    while ((m = reDyn.exec(src)) !== null) {
      const inner = m[1].trim();
      // Skip empty, or things that look like they were already handled as quotes
      if (!inner || inner === ')') continue;
      // Skip if it looks like pure whitespace or numeric
      if (/^\d+$/.test(inner)) continue;
      // Skip JSX prop values like  t({ count: n }) – object-arg calls
      if (inner.startsWith('{')) continue;
      warnDynamic(`${varName}(${inner.slice(0, 40)})`, m.index);
    }
  }
}

// ── missing from JSON (code references key that doesn't exist) ────────────────
const missingInEn = [...referencedKeys].filter(k => !enKeys.has(k));
const missingInPt = [...referencedKeys].filter(k => !ptKeys.has(k));

// union: key is missing in at least one locale
const missingSet = new Set([...missingInEn, ...missingInPt]);
const missingList = [...missingSet].sort();

// ── unused keys (JSON key not referenced in code) — warnings only ─────────────
const unusedInEn = [...enKeys].filter(k => !referencedKeys.has(k));

// ── reporting ────────────────────────────────────────────────────────────────

const RESET  = '\x1b[0m';
const RED    = '\x1b[31m';
const YELLOW = '\x1b[33m';
const GREEN  = '\x1b[32m';
const BOLD   = '\x1b[1m';
const DIM    = '\x1b[2m';

function section(title) {
  console.log(`\n${BOLD}${title}${RESET}`);
  console.log('─'.repeat(60));
}

let hasErrors = false;

// -- Parity errors
section('1. Locale parity (en ↔ pt-BR)');
if (onlyInEn.length === 0 && onlyInPt.length === 0) {
  console.log(`${GREEN}✓ Both locales have identical key sets.${RESET}`);
} else {
  hasErrors = true;
  if (onlyInEn.length) {
    console.log(`${RED}ERROR — ${onlyInEn.length} key(s) in en.json but MISSING in pt-BR.json:${RESET}`);
    onlyInEn.forEach(k => console.log(`  ${RED}✗${RESET} ${k}`));
  }
  if (onlyInPt.length) {
    console.log(`${RED}ERROR — ${onlyInPt.length} key(s) in pt-BR.json but MISSING in en.json:${RESET}`);
    onlyInPt.forEach(k => console.log(`  ${RED}✗${RESET} ${k}`));
  }
}

// -- Code ↔ JSON errors
section('2. Code references → JSON');
if (missingList.length === 0) {
  console.log(`${GREEN}✓ All static t() calls resolve to existing keys.${RESET}`);
} else {
  hasErrors = true;
  console.log(`${RED}ERROR — ${missingList.length} key(s) used in code but MISSING in locale file(s):${RESET}`);
  for (const k of missingList) {
    const inEn = enKeys.has(k);
    const inPt = ptKeys.has(k);
    const where = !inEn && !inPt ? 'both' : !inEn ? 'en.json' : 'pt-BR.json';
    console.log(`  ${RED}✗${RESET} ${k}  ${DIM}(missing in ${where})${RESET}`);
  }
}

// -- Unused keys (warnings)
section('3. Unused keys (warnings — not errors)');
if (unusedInEn.length === 0) {
  console.log(`${GREEN}✓ No unused keys detected.${RESET}`);
} else {
  console.log(`${YELLOW}WARN — ${unusedInEn.length} key(s) in JSON not found in any static t() call.${RESET}`);
  console.log(`${DIM}      (may be used dynamically — not treated as errors)${RESET}`);
  if (VERBOSE) {
    unusedInEn.forEach(k => console.log(`  ${YELLOW}⚠${RESET} ${k}`));
  } else {
    console.log(`${DIM}      Run with --verbose to list all unused keys.${RESET}`);
  }
}

// -- Dynamic call warnings
if (dynamicWarnings.length) {
  section('4. Dynamic / skipped t() calls (informational)');
  console.log(`${YELLOW}WARN — ${dynamicWarnings.length} dynamic t() call(s) skipped (cannot be statically checked):${RESET}`);
  if (VERBOSE) {
    dynamicWarnings.forEach(w => console.log(`  ${YELLOW}~${RESET} ${DIM}${w.file}${RESET}: t(${w.call})`));
  } else {
    const preview = dynamicWarnings.slice(0, 5);
    preview.forEach(w => console.log(`  ${YELLOW}~${RESET} ${DIM}${w.file}${RESET}: t(${w.call})`));
    if (dynamicWarnings.length > 5) {
      console.log(`  ${DIM}... and ${dynamicWarnings.length - 5} more. Run with --verbose to see all.${RESET}`);
    }
  }
}

// -- Summary
section('Summary');
const errorCount  = onlyInEn.length + onlyInPt.length + missingList.length;

console.log(`  Locale-parity errors : ${onlyInEn.length + onlyInPt.length > 0 ? RED : GREEN}${onlyInEn.length + onlyInPt.length}${RESET}`);
console.log(`  Missing-key errors   : ${missingList.length > 0 ? RED : GREEN}${missingList.length}${RESET}`);
console.log(`  Unused-key warnings  : ${YELLOW}${unusedInEn.length}${RESET}`);
console.log(`  Dynamic-call warnings: ${YELLOW}${dynamicWarnings.length}${RESET}`);

if (hasErrors) {
  console.log(`\n${RED}${BOLD}✗ Check FAILED (exit 1)${RESET}\n`);
  process.exit(1);
} else {
  console.log(`\n${GREEN}${BOLD}✓ Check PASSED (exit 0)${RESET}\n`);
  process.exit(0);
}
